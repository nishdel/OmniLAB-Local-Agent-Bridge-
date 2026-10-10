import asyncio
from datetime import timedelta
import json
import os
from pathlib import Path
import sys
import time

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from localagentbridge.companion_store import CompanionStore
from localagentbridge.task_store import TaskStore
from localagentbridge.companion import ensure_worker
from test_selective_contracts import contract
from test_selective_integration import repo


def test_real_mcp_contract_reuses_worker_store_and_preserves_review(tmp_path):
    repository, revision = repo(tmp_path/'repo')
    data = tmp_path/'data'
    cfg = tmp_path/'isolated.toml'
    cfg.write_text('source_root = '+json.dumps(repository)+'\ndata_dir = '+json.dumps(str(data))+
                   '\n[selective]\nenabled = true\n', encoding='utf-8')
    store = CompanionStore(data/'companion')
    run = store.create_run(repository, revision)
    c = contract(Path(repository), base_revision=revision, requested_lane='codex_direct')
    async def run_mcp():
        params = StdioServerParameters(command=sys.executable,
            args=['-m','localagentbridge','--config',str(cfg),'server'],env=dict(os.environ))
        async with stdio_client(params) as (reader,writer):
            async with ClientSession(reader,writer,read_timeout_seconds=timedelta(seconds=30)) as client:
                await client.initialize()
                names = {t.name for t in (await client.list_tools()).tools}
                assert {'companion_contract_submit','companion_contract_status'} <= names
                assert not any('integrate' in n or 'contract_review' in n for n in names)
                args = {'run_id':run, 'contracts':[c.model_dump()]}
                response = await client.call_tool('companion_contract_submit',args)
                assert not response.isError
                payload = json.loads(response.content[0].text)
                jid = payload['job_ids'][0]
                assert payload['dispatch']=='controller_not_running'
                assert store.job(jid)['state']=='queued'
                again = await client.call_tool('companion_contract_submit',args)
                assert json.loads(again.content[0].text)['job_ids']==[jid]
                wrong = c.model_copy(update={'base_revision':'b'*40})
                bad = await client.call_tool('companion_contract_submit',{'run_id':run,'contracts':[wrong.model_dump()]})
                assert bad.isError
                assert len(store.snapshot()['jobs'])==1
                assert TaskStore(store).get(jid)['accepted_hash'] is None
                return jid
    jid = asyncio.run(run_mcp())
    # The MCP server has closed. A trusted process outside its Windows job
    # starts the existing worker; there are no breakaway/host-boundary flags.
    assert store.job(jid)['state']=='queued'
    process = ensure_worker(store)
    assert process is not None
    process.wait(timeout=20)
    assert process.returncode==0
    value = store.job(jid)
    assert value['state']=='succeeded'
    assert TaskStore(store).get(jid)['review_status']=='awaiting_review'
    assert value['result']['answer']['return_to_supervisor']
    async def status_after_restart():
        async with stdio_client(StdioServerParameters(command=sys.executable,
                args=['-m','localagentbridge','--config',str(cfg),'server'],env=dict(os.environ))) as (reader,writer):
            async with ClientSession(reader,writer) as client:
                await client.initialize()
                result=await client.call_tool('companion_contract_status',{'job_id':jid})
                assert json.loads(result.content[0].text)['attempt_id']==value['attempt_id']
    asyncio.run(status_after_restart())

