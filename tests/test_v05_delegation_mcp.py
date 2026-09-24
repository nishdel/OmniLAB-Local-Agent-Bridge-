"""Adaptive task fields round-trip through the existing MCP workflow tools."""
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


def test_adaptive_gate_over_mcp_without_new_tools(tmp_path):
    chats=[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):
            pass
        def body(self,value):
            raw=json.dumps(value).encode()+b'\n'
            self.send_response(200)
            self.send_header('Content-Length',str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
        def do_GET(self):
            self.body({'models':[{'name':'qwen3:4b'}]})
        def do_POST(self):
            value=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            chats.append(value)
            self.body({'message':{'content':json.dumps(ANSWERS[value['format']['title']])},
                'done':True,'prompt_eval_count':60,'eval_count':25,'eval_duration':1000000000})
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    root=Path(__file__).resolve().parents[1]
    config=tmp_path/'config.toml'
    config.write_text((root/'config.example.toml').read_text().replace('source_root = "."','')+
                      '\n[agentic]\nenabled=true\n')
    env={k:v for k,v in os.environ.items() if not k.startswith('LAB_')}
    env.update(LAB_CONFIG=str(config),LAB_ENDPOINT=f'http://127.0.0.1:{server.server_port}')
    task={'task_id':'adaptive-mcp','kind':'bug_analysis','objective':'Analyze an exact-limit rejection.',
        'context':'Length equal to the configured maximum must be accepted.','diff':'-if n > maximum\n+if n >= maximum',
        'delegation':{},'validation_status':'passed','test_output':'Boundary test confirms the defect.'}
    async def run():
        params=StdioServerParameters(command=sys.executable,args=['-m','localagentbridge','server'],env=env)
        async with stdio_client(params) as (reader,writer):
            async with ClientSession(reader,writer,read_timeout_seconds=timedelta(seconds=20)) as client:
                await client.initialize()
                assert len((await client.list_tools()).tools)==13
                async def call(name,args):
                    response=await client.call_tool(name,args)
                    assert not response.isError,response
                    return json.loads(response.content[0].text)
                plan=await call('workflow_plan',{'task':task})
                assert plan['delegation']['path']=='direct' and not chats
                state=await call('workflow_start',{'task':task})
                state=await call('workflow_step',{'run_id':state['run_id'],'version':state['version'],'task':task})
                assert len(chats)==1 and state['next_stage']=='decide'
                assert state['stages'][0]['execution']=='direct'
                state=await call('workflow_step',{'run_id':state['run_id'],'version':state['version'],'task':task})
                state=await call('workflow_checkpoint',{'run_id':state['run_id'],'version':state['version'],'task':task,
                    'checkpoint':{'action':'reject','note':'Codex rejected the boundary regression.'}})
                assert state['state']=='rejected' and state['delegation']['path']=='direct'
    try:
        asyncio.run(run())
    finally:
        server.shutdown()
        server.server_close()
