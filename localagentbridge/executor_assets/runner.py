"""Container-only SDK runner. LAB owns scheduling; SDK owns the agent loop."""
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import threading
import time
import uuid

from bounded import run_bounded, terminal_executor, CommandPolicy

ROOT = Path('/exchange')


def write(name, value):
    path = ROOT / name
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value), encoding='utf-8')
    temporary.replace(path)


def sealed_editor_executor(contract):
    """Keep SDK editing/encoding/history with exact-file writes in sealed directories.

    SDK 1.53.0 normally replaces a sibling temporary file. Here the disposable
    file is updated in place; a crash may leave it partial, which must be discarded
    or independently verified. No directory write permission or host access is added.
    """
    import stat
    from openhands.tools.file_editor.editor import FileEditor
    from openhands.tools.file_editor.impl import FileEditorExecutor
    allowed = {Path('/workspace')/name for name in contract['permitted_files']}
    cap = contract['limits']['snapshot_bytes']

    class SealedEditor(FileEditor):
        def _atomic_write(self, path, file_text, encoding):
            # This pinned SDK extension point is intentionally non-atomic only
            # inside the disposable snapshot; original/acceptance files stay sealed.
            path = Path(path)
            if path not in allowed or path.resolve() != path:
                raise ValueError('Editor target is outside the exact permitted files')
            try:
                data = file_text.encode(encoding)
            except UnicodeEncodeError:
                data = file_text.encode('utf-8')
            if len(data) > cap:
                raise ValueError('Editor content exceeds the snapshot budget')
            fd = os.open(path, os.O_WRONLY | os.O_NOFOLLOW)
            try:
                info = os.fstat(fd)
                if not stat.S_ISREG(info.st_mode) or info.st_uid != 10001 or info.st_nlink != 1:
                    raise ValueError('Editor target is not an owned regular snapshot file')
                with os.fdopen(fd, 'wb', closefd=False) as output:
                    output.write(data)
                    output.truncate()
                    output.flush()
                    os.fsync(fd)
            finally:
                os.close(fd)

    class ScopedEditor(FileEditorExecutor):
        def __call__(self, action, conversation=None):
            from openhands.tools.file_editor.definition import FileEditorObservation
            try:
                CommandPolicy(contract).path(action.path)
                if action.command not in ('view', 'str_replace', 'insert', 'undo_edit'):
                    raise ValueError('Editor operation is outside this qualification contract')
                if action.command != 'view' and 'edit' not in contract['operations']:
                    raise ValueError('Editing is not authorized')
            except ValueError as error:
                return FileEditorObservation.from_text(text=str(error), command=action.command, is_error=True)
            return super().__call__(action, conversation)

    executor = ScopedEditor(workspace_root='/workspace',
                                  allowed_edits_files=[str(p) for p in allowed])
    # Empty scope must deny edits; SDK treats an empty constructor list as None.
    executor.allowed_edits_files = allowed
    executor.editor = SealedEditor(workspace_root='/workspace')
    return executor


def main(mode):
    if os.name != 'posix' or os.getuid() != 10001:
        raise RuntimeError('Runner requires the restricted nonroot Linux sandbox')
    if os.getenv('LAB_HOLD_FOR_COLLECTION') == '1':
        while not (ROOT/'ready').exists():
            time.sleep(.1)
    contract = json.loads((ROOT / 'task.json').read_text())
    if mode in ('verify', 'baseline'):
        results = []
        for check in contract['checks']:
            result = run_bounded(check['argv'], cwd='/workspace',
                seconds=contract['limits']['test_seconds'], output_bytes=contract['limits']['output_bytes'])
            results.append(dict(id=check['id'], covers=check['covers'], **result))
        write('result.json', {'checks': results})
        return
    if mode != 'agent':
        raise RuntimeError('Unknown sandbox mode')
    for package in ('openhands-sdk', 'openhands-tools'):
        if importlib.metadata.version(package) != '1.53.0':
            raise RuntimeError('SDK version differs from qualified API')
    # A loopback-only proxy INSIDE --network=none has no path to the host/network.
    # The controller relays only allowed inference requests through the mailbox.
    class Relay(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_POST(self):
            size = int(self.headers.get('Content-Length', '0'))
            if self.path != '/v1/chat/completions' or not 0 < size <= 1000000:
                self.send_error(400)
                return
            body = json.loads(self.rfile.read(size))
            request_id = str(uuid.uuid4())
            write('request.json', {'id': request_id, 'body': body})
            response_file = ROOT / 'response.json'
            while True:
                if response_file.exists():
                    response = json.loads(response_file.read_text())
                    if response['id'] == request_id:
                        break
                time.sleep(.1)  # Independent runtime, never a waiting Codex session.
            data = json.dumps(response['body']).encode()
            self.send_response(response.get('status', 200))
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
    server = HTTPServer(('127.0.0.1', 8765), Relay)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    from pydantic import SecretStr
    from openhands.sdk import LLM, Agent, Conversation, Tool
    from openhands.tools.file_editor import FileEditorTool
    from openhands.tools.terminal import TerminalTool
    from openhands.sdk.tool import register_tool

    class ScopedFileEditorTool(FileEditorTool):
        @classmethod
        def create(cls, conv_state):
            definitions = FileEditorTool.create(conv_state)
            return [definition.model_copy(update={'executor': sealed_editor_executor(contract)})
                    for definition in definitions]

    commands = []
    class ScopedTerminalTool(TerminalTool):
        @classmethod
        def create(cls, conv_state):
            definitions = TerminalTool.create(conv_state, executor=terminal_executor(contract, commands))
            return [definition.model_copy(update={'description':
                'Run a single bounded command without a shell. Allowed: cat followed by exact listed workspace files, '
                'or one exact acceptance command from the contract. No command chaining, interactive input, '
                'redirection, arbitrary scripts or resets. The controller enforces time and output caps.'}) for definition in definitions]

    register_tool(TerminalTool.name, ScopedTerminalTool)
    register_tool(FileEditorTool.name, ScopedFileEditorTool)
    class MailboxLLM(LLM):
        # Pinned SDK 1.53.0 recognizes reasoning_content but its model-name
        # allowlist omits local Qwen. Preserve the actual field without aliases
        # or a patched SDK; the controller translates the provider wire name.
        def _to_chat_dicts(self, messages):
            values = super()._to_chat_dicts(messages)
            if len(values) != len(messages):
                raise ValueError('SDK message serialization changed')
            for message, value in zip(messages, values):
                if message.reasoning_content is not None:
                    value['reasoning_content'] = message.reasoning_content
            return values

    llm = MailboxLLM(model='openai/' + contract['model'], api_key=SecretStr('sandbox-placeholder'),
              base_url='http://127.0.0.1:8765/v1', max_output_tokens=contract['limits']['output_tokens'],
              num_retries=0, stream=False, timeout=contract['limits']['inference_deadline_seconds'],
              stream_idle_timeout=None,
              # Above every admissible whole-prompt budget: SDK shortening cannot
              # turn oversized requirements/failures into an admitted request.
              max_message_chars=1000000)
    agent = Agent(llm=llm, tools=[Tool(name=TerminalTool.name), Tool(name=FileEditorTool.name)])
    # No task/subagent tool, browser, MCP servers, credentials, plugins or shared memory.
    conversation = Conversation(agent=agent, workspace='/workspace',
                                conversation_id=uuid.UUID(os.environ['LAB_CONVERSATION_ID']),
                                persistence_dir='/state/conversations',
                                max_iteration_per_run=contract['limits']['steps'])
    prompt = json.dumps({'execution_authority': (
                        'This is the supervisor-authorized isolated implementation lane. '
                        'The contract permits only its listed operations and files. '
                        'Selected advisory skill text supplies planning guidance; its '
                        'proposal-mode no-edit/no-execute clause does not override this '
                        'explicit scoped execution permission. No commit, expansion of '
                        'scope or self-acceptance is authorized.'), 'objective': contract['objective'], 'requirements': contract['acceptance'],
                        'non_goals': contract['non_goals'], 'context': contract['context'],
                        'permitted_files': contract['permitted_files'], 'operations': contract['operations'],
                        'checks': contract['checks'],
                        'skills': json.loads((ROOT/'skills.json').read_text())})
    conversation.send_message(prompt)
    conversation.run()
    write('result.json', {'sdk_version': '1.53.0', 'execution_finished': True, 'commands': commands})
    server.shutdown()


if __name__ == '__main__':
    if os.getenv('LAB_HOLD_FOR_COLLECTION') == '1':
        status = 0
        try:
            main(sys.argv[1])
        except Exception as error:
            status = 1
            write('result.json', {'error': type(error).__name__ + ': ' + str(error)[:2000]})
        write('completion.json', {'ExitCode': status})
        # The controller must durably collect before stopping this owned process.
        # An exited container has lost tmpfs and must never be restarted as recovery.
        while True:
            time.sleep(1)
    else:
        main(sys.argv[1])
