"""One explicit real MCP probe. Follow-ups require separately reviewed request IDs."""
import argparse
import asyncio
from datetime import timedelta
import json
import os
from pathlib import Path
import sys
import time
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from localagentbridge.config import load_config
from localagentbridge.models import TIERS
from localagentbridge.telemetry import Store
from localagentbridge.schemas import compact
from validate_local_first import CASES


async def run(args):
    output=Path(args.output)
    if output.exists():
        raise ValueError('Choose a new output file; evidence is never overwritten')
    cfg=load_config(args.config)
    store=Store(cfg.data_dir)
    if args.cap:
        store.compute_cap(value=args.cap)  # explicit operator test control, never available to a model
    category,tool,arguments=next(case for case in CASES if case[0]==args.case)
    arguments=dict(arguments)
    if args.arguments:
        arguments.update(json.loads(args.arguments))
    if args.single:
        arguments.pop('consensus',None)
    if args.routing:
        arguments['routing']=json.loads(args.routing)
    if args.feedback:
        tool='triage_task'
        arguments={'feedback':json.loads(args.feedback)}
    params=StdioServerParameters(command=sys.executable,args=['-m','localagentbridge','--config',str(Path(args.config).resolve()),'server'],env=dict(os.environ))
    started=time.time()
    async with stdio_client(params) as (read,write):
        async with ClientSession(read,write,read_timeout_seconds=timedelta(seconds=1850)) as session:
            await session.initialize()
            reply=await session.call_tool(tool,arguments)
            result=json.loads(reply.content[0].text)
    with store.connect() as db:
        usage=[dict(r) for r in db.execute("SELECT * FROM usage WHERE source='local' AND started>=? ORDER BY started",(started,))]
        routes=[dict(r) for r in db.execute('SELECT * FROM route_events WHERE created>=? ORDER BY created',(started,))]
    record=dict(case=category,tool=tool,arguments=arguments,started=started,finished=time.time(),
                config=str(Path(args.config).resolve()),cap=store.compute_cap(cfg.adaptive.default_cap),
                error=bool(reply.isError),result=result,returned_bytes=len(compact(result).encode()),usage=usage,routes=routes)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(record,indent=2),encoding='utf-8')
    print(json.dumps(dict(case=category,models=[r['model'] for r in usage],result=result),indent=2),flush=True)
    if reply.isError:
        raise SystemExit(1)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',default='config.toml')
    parser.add_argument('--case',choices=[c[0] for c in CASES],default='repository_discovery')
    parser.add_argument('--routing',help='Explicit routing-hints JSON; no inferred failure or acceptance')
    parser.add_argument('--arguments',help='Explicit tool argument overrides for a focused follow-up')
    parser.add_argument('--single',action='store_true',help='Evaluate the consensus question as one routed opinion')
    parser.add_argument('--feedback',help='Explicit reviewed feedback JSON')
    parser.add_argument('--cap',choices=TIERS)
    parser.add_argument('--output',required=True)
    asyncio.run(run(parser.parse_args()))
