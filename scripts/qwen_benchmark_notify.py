"""Optional operational ntfy delivery. Never receives prompts or generated model text."""
import os
from pathlib import Path
import re
import threading
import time
from urllib.parse import urlsplit

import httpx

from qwen_benchmark_io import Lock, atomic, read

KINDS = {'launched', 'case-completed', 'terminal', 'review-ready', 'review-failed', 'progress'}


class Notifier:
    def __init__(self, job, config=None, transport=None):
        self.job, self.config, self.transport = Path(job), config if isinstance(config,dict) else {}, transport
        self.stop = threading.Event()
        self.thread = None

    def valid(self):
        try:
            return self._valid()
        except (TypeError,ValueError):
            return False

    def _valid(self):
        c = self.config
        if not all(isinstance(c.get(key),str) for key in ('server_url','topic','token_env')):
            return False
        url = urlsplit(c.get('server_url') or '')
        return bool(c.get('enabled') is True and c.get('private_destination_verified') is True
                    and url.scheme == 'https' and url.hostname and not url.username and not url.password
                    and not url.query and not url.fragment and url.path in ('', '/')
                    and re.fullmatch(r'[A-Za-z0-9_-]{1,128}', c.get('topic') or '')
                    and c.get('token_env') and os.environ.get(c['token_env']))

    def health(self, state):
        try:
            atomic(self.job/'notification-state.json', {'state':state, 'time':time.time(),
                'phone_receipt':'unverified', 'hourly_progress':bool(self.config.get('hourly_progress'))})
        except OSError:
            pass  # Optional notification storage cannot cancel inference.

    def emit(self, kind, *, case=None):
        if kind not in KINDS:
            raise ValueError('Unknown operational notification')
        try:
            state = read(self.job/'state.json')
            execution = state.get('execution_id', state['job_id'])
            suffix = str(int(time.time() // 3600)) if kind=='progress' else (case or '')
            # Case IDs come only from the frozen queue; never from model output.
            if case and case not in {c['id'] for c in state['cases']}:
                raise ValueError('Unknown case')
            import hashlib
            key = hashlib.sha256((execution+'|'+kind+'|'+suffix).encode()).hexdigest()
            directory = self.job/'notifications'
            directory.mkdir(exist_ok=True)
            path = directory/(key+'.json')
            with Lock(directory/'queue.lock'):
                if path.exists():
                    return
                counts = {s:sum(c['state']==s for c in state['cases'])
                          for s in ('completed','running','queued','failed','interrupted','safety-stopped')}
                inherited = sum(bool(c.get('inherited_from')) for c in state['cases'])
                message = (f"{state['job_id']}: {kind}; state={state['state']}; "
                           f"new completed={counts['completed']-inherited}; inherited={inherited}; "
                           f"running={counts['running']}; queued={counts['queued']}; failed={counts['failed']}")
                if case:
                    message += '; case='+case
                atomic(path, {'event_id':key, 'kind':kind, 'created_at':time.time(), 'message':message,
                              'delivery':'pending' if self.valid() else 'disabled'})
        except Exception:
            self.health('notification-record-error')

    def drain(self):
        directory = self.job/'notifications'
        if not directory.exists():
            return
        with Lock(directory/'delivery.lock'):
            for path in sorted(directory.glob('*.json')):
                event = read(path)
                if event['delivery']=='sending':
                    event.update(delivery='ambiguous', reason='Sender interrupted; not automatically resent')
                    atomic(path, event)
                if event['delivery']!='pending':
                    continue
                if not self.valid():
                    event['delivery']='disabled'
                    atomic(path,event)
                    continue
                event.update(delivery='sending', started_at=time.time())
                atomic(path,event)  # Durable claim before network operation.
                try:
                    c = self.config
                    with httpx.Client(timeout=httpx.Timeout(5,connect=2), trust_env=False,
                                      follow_redirects=False, transport=self.transport) as client:
                        with client.stream('POST',c['server_url'].rstrip('/')+'/'+c['topic'],
                            content=event['message'].encode(), headers={
                                'Authorization':'Bearer '+os.environ[c['token_env']],
                                'Title':'LocalAgentBridge benchmark'}) as response:
                            # Status is sufficient; do not read an unbounded response body.
                            event.update(delivery='server-accepted' if 200<=response.status_code<300 else 'failed',
                                         status_code=response.status_code)
                except Exception as error:
                    # Exception text/response bodies can contain destinations or credentials.
                    event.update(delivery='ambiguous' if isinstance(error,httpx.TimeoutException) else 'failed',
                                 error_type=type(error).__name__)
                event['ended_at']=time.time()
                atomic(path,event)

    def start(self):
        self.health('configured' if self.valid() else 'disabled')
        if not self.valid():
            return
        def loop():
            while not self.stop.is_set():
                try:
                    self.drain()
                except Exception:
                    self.health('delivery-error')
                self.stop.wait(1)
        self.thread = threading.Thread(target=loop, name='benchmark-notifier', daemon=True)
        try:
            self.thread.start()
        except RuntimeError:
            self.thread = None
            self.health('delivery-thread-unavailable')

    def close(self):
        self.stop.set()
        if self.thread:
            self.thread.join(timeout=8)
        try:
            self.drain()
        except Exception:
            self.health('delivery-error')
