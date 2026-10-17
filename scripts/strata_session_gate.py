"""Qualification-only observation gate; NOT a machine-wide inference lock.

The isolated supervisor supplies fresh process/provider/store observations before
startup, before every dispatch, and from its existing monitor. On rejection it
uses the existing owned-runtime cleanup and reservation reconciliation. This
module never starts/stops a process or changes a store. Provider access is limited
to read-only resident-model metadata; it never requests inference.
"""
import argparse
import json
import math
from pathlib import Path, PureWindowsPath
import sqlite3
import time


ENGINE_NAMES = frozenset({'strata.exe', 'strata', 'llama-server.exe', 'llama-server',
                          'ollama_llama_server'})


def observe(store_paths, endpoint):
    """Read-only observations of the declared stores and known engine families.

    The operator must inventory other clients too: this is not universal process
    classification. Provider /api/ps alone misses runners still loading a model.
    """
    import httpx
    import psutil
    from localagentbridge.inference import local_origin
    result = dict(time=time.time(), diagnostics_complete=False, engines=[], stores={},
                  resident_models=None, errors=[])
    try:
        for process in psutil.process_iter(['pid', 'name']):
            if (process.info['name'] or '').casefold() in ENGINE_NAMES:
                try:
                    row = dict(pid=process.pid, created=process.create_time(), exe=process.exe())
                    identity(row)
                    result['engines'].append(row)
                except psutil.NoSuchProcess:
                    continue
        with httpx.Client(trust_env=False, follow_redirects=False, timeout=3) as client:
            response = client.get(local_origin(endpoint) + '/api/ps')
            response.raise_for_status()
            models = response.json()['models']
            if not isinstance(models, list):
                raise ValueError('Invalid provider model inventory')
            result['resident_models'] = models
        for label, path in store_paths.items():
            with sqlite3.connect(Path(path).resolve(strict=True).as_uri()+'?mode=ro', uri=True) as db:
                db.row_factory = sqlite3.Row
                paused = db.execute("SELECT value FROM settings WHERE key='paused'").fetchone()
                reservation = db.execute('SELECT * FROM inference_reservation').fetchall()
                if len(reservation) > 1:
                    raise ValueError('Invalid store reservation inventory')
                result['stores'][label] = dict(paused=json.loads(paused[0]) if paused else False,
                    pending_jobs=[dict(r) for r in db.execute(
                        "SELECT id,attempt_id FROM jobs WHERE state IN ('queued','running')")],
                    reservation=dict(reservation[0]) if reservation else None)
        result['diagnostics_complete'] = True
    except Exception as error:
        result['errors'].append(type(error).__name__ + ': ' + str(error))
    return result


def identity(row):
    if (type(row.get('pid')) is not int or row['pid'] <= 0
            or type(row.get('created')) not in (int, float) or row['created'] <= 0
            or not math.isfinite(row['created'])
            or not isinstance(row.get('exe'), str) or not row['exe']):
        raise ValueError('Incomplete process identity')
    return row['pid'], row['created'], str(PureWindowsPath(row['exe'])).casefold()


class SessionGate:
    def __init__(self, halt_file, expected_stores, clock=time.time):
        self.halt_file = Path(halt_file)
        self.expected_stores = set(expected_stores)
        if not self.expected_stores:
            raise ValueError('Explicit participating stores are required')
        self.clock = clock

    def check(self, snapshot, *, owned_engines=(), owned_attempt=None):
        """owned_attempt is (store label, job id, attempt id), never just a PID.

        A halt is sticky across supervisor/worker processes. Observations do not
        prevent a nonparticipant from starting immediately after this check.
        """
        if self.halt_file.exists():
            raise ValueError('Session halted; no subsequent dispatch or automatic reset')
        try:
            if snapshot.get('diagnostics_complete') is not True:
                raise ValueError('Missing process/provider/store diagnostics')
            age = self.clock() - snapshot['time']
            if not 0 <= age <= 5:
                raise ValueError('Stale or future observation')
            if snapshot['resident_models'] != []:
                raise ValueError('Competing provider model is resident')
            owned = {identity(row) for row in owned_engines}
            seen = set()
            for row in snapshot['engines']:
                key = identity(row)
                if key not in owned:
                    raise ValueError('Unowned engine is loading or running')
                seen.add(key)
            if seen != owned:
                raise ValueError('Owned engine disappeared or its PID was reused')
            stores = snapshot['stores']
            if set(stores) != self.expected_stores:
                raise ValueError('Participating store inventory changed')
            for label, state in stores.items():
                mine = owned_attempt if owned_attempt and label == owned_attempt[0] else None
                if state['paused'] is not True and mine is None:
                    raise ValueError('Other admissions are not paused by the operator')
                for job in state['pending_jobs']:
                    if mine is None or (job['id'], job['attempt_id']) != mine[1:]:
                        raise ValueError('Other queued/running work remains')
                reservation = state['reservation']
                if reservation is not None:
                    if (mine is None or reservation['state'] != 'active'
                            or (reservation['job_id'], reservation['attempt_id']) != mine[1:]):
                        raise ValueError('Other or uncertain inference reservation remains')
        except Exception as error:
            self.halt_file.parent.mkdir(parents=True, exist_ok=True)
            try:
                with self.halt_file.open('x', encoding='utf-8') as stream:
                    json.dump({'time': self.clock(), 'reason': str(error),
                               'action': 'Block dispatch; reconcile only owned work'}, stream)
            except FileExistsError:
                pass
            raise ValueError('Qualification session blocked: ' + str(error)) from error
        # Another participant may have latched the halt during observation.
        if self.halt_file.exists():
            raise ValueError('Session halted during observation')


def install_dispatch_guard(gate, snapshot, ownership):
    """Explicit hook for the isolated qualification worker process only.

    Returns a restoration callback. No installation/global mutation; the trusted
    supervisor supplies ownership from its verified serving binding and durable
    job. The existing owner monitor must call the same gate independently while
    a request is in flight, and use existing owned cleanup if it rejects.
    """
    from localagentbridge.inference import ChatProvider
    original = ChatProvider.chat

    async def checked(provider, *args, **kwargs):
        gate.check(snapshot(), **ownership())
        return await original(provider, *args, **kwargs)

    ChatProvider.chat = checked

    def restore():
        if ChatProvider.chat is not checked:
            raise ValueError('Qualification dispatch hook changed unexpectedly')
        ChatProvider.chat = original

    return restore


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--snapshot', type=Path)
    source.add_argument('--store-db', action='append', help='Read-only LABEL=DATABASE; repeat for each store')
    parser.add_argument('--endpoint', help='Exact loopback Ollama origin; metadata only')
    parser.add_argument('--halt-file', type=Path, required=True)
    parser.add_argument('--store', action='append', help='Expected label when checking a saved snapshot')
    args = parser.parse_args()
    if args.snapshot:
        if not args.store:
            parser.error('--snapshot requires the expected --store labels')
        labels, observed = args.store, json.loads(args.snapshot.read_text(encoding='utf-8'))
    else:
        if not args.endpoint or args.store:
            parser.error('--store-db requires --endpoint and supplies the store labels itself')
        pairs = [item.split('=', 1) for item in args.store_db]
        if any(len(pair) != 2 or not all(pair) for pair in pairs):
            parser.error('Each --store-db must be LABEL=DATABASE')
        paths = dict(pairs)
        if len(paths) != len(pairs):
            parser.error('Duplicate store labels')
        labels, observed = paths, observe(paths, args.endpoint)
    SessionGate(args.halt_file, labels).check(observed)
    print('Observation passed; this is not startup authorization or exclusive ownership')
