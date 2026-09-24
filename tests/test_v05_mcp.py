"""Exercise workflow transport and checkpoints through real MCP stdio, with deterministic Ollama HTTP."""
import asyncio
from datetime import timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import sys
import threading

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from test_v05_workflows import ANSWERS


def test_opt_in_workflow_over_real_mcp(tmp_path):
    chats=[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):
            pass
        def send_body(self,payload):
            raw=json.dumps(payload).encode()+b'\n'
            self.send_response(200)
            self.send_header('Content-Length',str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
        def do_GET(self):
            self.send_body({'models':[{'name':'qwen3:4b'}]})
        def do_POST(self):
            body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            chats.append(body)
            self.send_body({'message':{'content':json.dumps(ANSWERS[body['format']['title']])},
                            'done':True,'prompt_eval_count':50,'eval_count':20,'eval_duration':1000000000})
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    root=Path(__file__).resolve().parents[1]
    config=tmp_path/'config.toml'
    text=(root/'config.example.toml').read_text().replace('source_root = "."','')
    config.write_text(text+'\n[agentic]\nenabled=true\n')
    env={k:v for k,v in os.environ.items() if not k.startswith('LAB_')}
    env.update(LAB_CONFIG=str(config),LAB_ENDPOINT=f'http://127.0.0.1:{server.server_port}')
    task={'task_id':'mcp-review','kind':'review_change','objective':'Review helper contract',
          'context':'Negative values are supported','diff':'-return value\n+return abs(value)',
          'test_output':'1 passed','validation_status':'passed'}
    async def run():
        params=StdioServerParameters(command=sys.executable,args=['-m','localagentbridge','server'],env=env)
        async with stdio_client(params) as (reader,writer):
            async with ClientSession(reader,writer,read_timeout_seconds=timedelta(seconds=20)) as client:
                await client.initialize()
                names={t.name for t in (await client.list_tools()).tools}
                assert len(names)==13 and 'review_diff' in names and 'workflow_step' in names
                async def call(name,args):
                    result=await client.call_tool(name,args)
                    assert not result.isError,result
                    assert len(result.content[0].text.encode())<=40000
                    return json.loads(result.content[0].text)
                catalog=await call('workflow_catalog',{})
                assert 'security-reviewer' in catalog['roles']
                plan=await call('workflow_plan',{'task':task})
                assert plan['stages'][-1]['executor']=='codex' and not chats
                state=await call('workflow_start',{'task':task})
                for _ in range(6):
                    state=await call('workflow_step',{'run_id':state['run_id'],'version':state['version'],'task':task})
                    if state['state']=='waiting_for_codex':
                        break
                assert state['state']=='waiting_for_codex' and len(chats)==2
                state=await call('workflow_checkpoint',{'run_id':state['run_id'],'version':state['version'],'task':task,
                    'checkpoint':{'action':'accept','note':'Inspected the actual helper diff and test evidence.'}})
                assert state['state']=='codex_verified'
                queried=await call('workflow_status',{'run_id':state['run_id']})
                assert queried['budget']['attempts']==2 and len(queried['attempts'])==2
    try:
        asyncio.run(run())
    finally:
        server.shutdown()
        server.server_close()
