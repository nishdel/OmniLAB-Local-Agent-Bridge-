import asyncio
import json
from pathlib import Path
import uuid

import pytest

from localagentbridge.companion import git_identity
from localagentbridge.companion_store import CompanionStore
from localagentbridge.integration import integrate
from localagentbridge.sandbox import command
from localagentbridge.selective import execute
from localagentbridge.task_store import TaskStore
from test_selective_contracts import contract, request
from test_selective_flows import FakeSandbox, transport


class IntegrationSandbox(FakeSandbox):
    def read(self,name,owner,path,*args):
        if path=='/exchange/result.json':
            row=self.containers[name]
            return {'checks':[dict(id=c.id,argv=c.argv,covers=c.covers,exit_code=1 if self.wrong else 0,
                timed_out=False,output='AssertionError' if self.wrong else 'passed',output_truncated=False)
                for c in row['c'].checks]}
        return super().read(name,owner,path,*args)


def repo(path):
    path.mkdir()
    (path/'subject.py').write_text('x=1\n')
    (path/'check.py').write_text('from subject import x\nassert x==2\n')
    command(['git','init','--quiet',str(path)])
    command(['git','-C',str(path),'add','.'])
    command(['git','-C',str(path),'-c','user.name=Test','-c','user.email=test@localhost','commit','--quiet','-m','fixture'])
    return git_identity(path)


def candidate(tmp_path):
    root,revision=repo(tmp_path/'repo')
    c=contract(Path(root),base_revision=revision)
    req=request(c)
    req['policy'].update(providers={'ollama':{'endpoint':'http://127.0.0.1:11434'}},sandbox={},
        memory_plan={'supervisor_verified':True,'os_and_apps_mb':1,'lab_mb':1,'runtime_mb':1,
                     'context_cache_mb':1,'headroom_mb':1})
    store=CompanionStore(tmp_path/'state'); run=store.create_run(root,revision)
    jid=TaskStore(store).submit_many(run,[req])[0]; job=store.claim_job({})
    asyncio.run(execute(store,job,transport(),lambda _:FakeSandbox()))
    state=TaskStore(store).get(jid)
    assert state['verification_status']=='passed',store.job(jid)['error']
    event=store.snapshot()['events'][0]['id']
    store.decide(event,'accepted','inspected exact patch',local=True,candidate_hash=state['candidate_hash'],coverage={'a':'source and checks'})
    return store,job,state['candidate_hash'],Path(root)


def test_supervisor_integration_exact_candidate_and_idempotent_retry(tmp_path):
    store,job,h,root=candidate(tmp_path)
    sandbox=IntegrationSandbox()
    result=asyncio.run(integrate(store,job['id'],h,lambda _:sandbox))
    assert result['integrated'] and not result['committed']
    assert (root/'subject.py').read_text()=='x=2\n'
    assert git_identity(root)[1]==job['request']['contract']['base_revision']
    assert len(sandbox.creates)==1
    again=asyncio.run(integrate(store,job['id'],h,lambda _:sandbox))
    assert again['tree_hash']==result['tree_hash'] and len(sandbox.creates)==1
    assert TaskStore(store).get(job['id'])['integration_status']=='integrated'


def test_failed_combined_checks_leave_source_untouched(tmp_path):
    store,job,h,root=candidate(tmp_path)
    with pytest.raises(ValueError,match='Combined'):
        asyncio.run(integrate(store,job['id'],h,lambda _:IntegrationSandbox(wrong=True)))
    assert (root/'subject.py').read_text()=='x=1\n'
    assert TaskStore(store).get(job['id'])['integration_status']=='candidate'


def test_unrelated_changes_block_integration(tmp_path):
    store,job,h,root=candidate(tmp_path)
    (root/'check.py').write_text('print("unrelated work")\n')
    with pytest.raises(ValueError,match='Unrelated'):
        asyncio.run(integrate(store,job['id'],h,lambda _:IntegrationSandbox()))
    assert (root/'subject.py').read_text()=='x=1\n'


def test_review_is_idempotent_and_required_profile_review_cannot_disappear(tmp_path):
    store,job,h,root=candidate(tmp_path)
    event=store.snapshot()['events'][0]['id']
    store.decide(event,'accepted','inspected exact patch',local=True,candidate_hash=h,coverage={'a':'source and checks'})
    with store.db() as db:
        assert db.execute("SELECT count(*) FROM contract_audit WHERE kind='supervisor_review'").fetchone()[0]==1
    with pytest.raises(ValueError,match='coverage'):
        store.decide(event,'accepted','inspected exact patch',local=True,candidate_hash=h,coverage={'a':'different'})


def test_interrupted_atomic_integration_resumes_only_reviewed_bytes(tmp_path,monkeypatch):
    import os
    store,job,h,root=candidate(tmp_path)
    sandbox=IntegrationSandbox()
    original=os.replace
    def crash(source,target):
        if str(source).endswith('.tmp') and '.lab-' in str(source):
            raise OSError('simulated interruption')
        return original(source,target)
    with monkeypatch.context() as patch:
        patch.setattr(os,'replace',crash)
        with pytest.raises(OSError,match='simulated'):
            asyncio.run(integrate(store,job['id'],h,lambda _:sandbox))
    assert TaskStore(store).get(job['id'])['integration_status']=='integrating'
    assert (root/'subject.py').read_bytes()!=b'x=2\n'
    assert list(root.glob('*.lab-*.tmp'))
    result=asyncio.run(integrate(store,job['id'],h,lambda _:sandbox))
    assert result['integrated'] and (root/'subject.py').read_bytes()==b'x=2\n'
    assert len(sandbox.creates)==1 and not list(root.glob('*.lab-*.tmp'))


def test_interrupted_integration_rejects_changed_temporary(tmp_path,monkeypatch):
    import os
    store,job,h,root=candidate(tmp_path)
    def crash(source,target):
        if '.lab-' in str(source):
            raise OSError('simulated')
        return original(source,target)
    original=os.replace
    sandbox=IntegrationSandbox()
    with monkeypatch.context() as patch:
        patch.setattr(os,'replace',crash)
        with pytest.raises(OSError):
            asyncio.run(integrate(store,job['id'],h,lambda _:sandbox))
    next(root.glob('*.lab-*.tmp')).write_text('unreviewed')
    with pytest.raises(ValueError,match='temporary'):
        asyncio.run(integrate(store,job['id'],h,lambda _:sandbox))
    assert (root/'subject.py').read_text()=='x=1\n'
