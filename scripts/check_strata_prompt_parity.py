"""Optional model-free oracle: run the pinned HTTP handler up to generation.

No listener is constructed. Fake lifecycle and capture replace only engine/HTTP
effects; the actual handler's normalization and Service.prepare remain intact.
Supply a trusted local counting manifest and JSON list of normalized payloads.
Private assets/requests/results must never enter public CI artifacts.
"""
import hashlib
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace


def main():
    manifest = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    payloads = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
    for path, expected in manifest['files'].items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
            raise ValueError('Oracle assets changed')
    def guard(event, args):
        if event.startswith(('socket.', 'subprocess.', 'os.spawn', 'os.exec')) or event == 'os.system':
            raise AssertionError('Oracle cannot start processes or use a network')
        if event == 'open' and isinstance(args[0], str) and Path(args[0]).suffix.lower() in ('.gguf', '.bin'):
            raise AssertionError('Oracle cannot read model weights')
    sys.addaudithook(guard)
    sys.path[:0] = [manifest['source'], str(Path(manifest['source'])/'tools')]
    from serve import server
    import strata_tokenizer
    def forbidden(*args, **kwargs): raise AssertionError('No engine/listener allowed')
    server.Engine = server.serve = server.popen = forbidden
    path = Path(manifest['tokenizer'])
    vocab = json.loads((path/'vocab.json').read_text(encoding='utf-8'))
    tokens = [None]*len(vocab)
    for text, index in vocab.items(): tokens[index] = text
    tok = strata_tokenizer.Tokenizer(tokens, (path/'merges.txt').read_text(encoding='utf-8').split('\n'),
        json.loads((path/'token_type.json').read_text()))
    svc = server.Service(SimpleNamespace(max_context=16384), tok, server.ChatTemplate(path/'chat_template.jinja'))
    svc.load = lambda: None  # Explicit fake lifecycle; no Engine exists.
    handler = server.make_handler(svc).__new__(server.make_handler(svc))
    handler.headers = {}
    handler._watch_client = lambda cancel: None
    class Captured(Exception): pass
    captured = {}
    def capture(svc, request, ids, thinking, tools, max_new, cancel, **kwargs):
        captured.update(input_tokens=len(ids), output=max_new, thinking=thinking,
            token_ids_sha256=hashlib.sha256(json.dumps(ids, separators=(',', ':')).encode()).hexdigest())
        raise Captured()
    server.openai_chunks = capture
    results = []
    for payload in payloads:
        captured.clear()
        start = time.perf_counter()
        try: handler._openai(payload)
        except Captured: pass
        except ValueError as e: captured.update(rejected=str(e))
        results.append(dict(captured, seconds=time.perf_counter()-start))
    print(json.dumps({'method': 'actual make_handler._openai -> Service.prepare -> captured token IDs; no generation',
        'server_sha256': manifest['server_sha256'], 'results': results, 'network_process_weight_guards': True}))


if __name__ == '__main__': main()
