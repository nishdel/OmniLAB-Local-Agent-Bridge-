import asyncio
import io
import json
import tarfile

import pytest

from localagentbridge.sandbox import DockerSandbox, bundle, unpack, tree_hash
from localagentbridge.selective import execute, make_candidate, verify
from localagentbridge.task_store import TaskStore
from test_selective_contracts import contract, setup, finish_candidate


def secure_row():
    return {'Image':'sha256:'+'a'*64,'Mounts':[],'State':{'Status':'created','Running':False},
      'Config':{'User':'10001:10001','Labels':{'org.omnilab.owner':'owner'}},
      'HostConfig':{'NetworkMode':'none','CapDrop':['ALL'],'SecurityOpt':['no-new-privileges:true'],
       'Memory':2147483648,'MemorySwap':2147483648,'PidsLimit':128,'StorageOpt':{'size':'2G'}}}


@pytest.mark.parametrize('section,key,value',[('HostConfig','NetworkMode','host'),
    ('HostConfig','Privileged',True),('HostConfig','Binds',['/:/host']),
    ('HostConfig','CapAdd',['SYS_ADMIN']),('HostConfig','StorageOpt',{}),
    ('HostConfig','MemorySwap',-1),('Config','User','root')])
def test_sandbox_rejects_unsafe_configuration(section,key,value):
    row=secure_row(); row[section][key]=value
    sandbox=DockerSandbox({'image':'sha256:'+'a'*64},lambda *a,**k:json.dumps([row]).encode())
    with pytest.raises(ValueError,match='security'): sandbox.inspect('name','owner')


def test_missing_image_or_runtime_never_uses_host():
    with pytest.raises(ValueError,match='image'): DockerSandbox({'image':'latest'})
    def missing(*a,**k): raise FileNotFoundError('docker')
    sandbox=DockerSandbox({'image':'sha256:'+'a'*64},missing)
    with pytest.raises(FileNotFoundError): sandbox.preflight()


def test_snapshot_permissions_and_symlink_rejection(tmp_path):
    c=contract(tmp_path)
    raw=bundle({'subject.py':b'x=1\n','check.py':b'assert True\n'},c)
    with tarfile.open(fileobj=io.BytesIO(raw)) as tar:
        assert tar.getmember('workspace/subject.py').uid==10001
        assert tar.getmember('workspace/check.py').uid==0
        assert tar.getmember('workspace').mode==0o555
    out=io.BytesIO()
    with tarfile.open(fileobj=out,mode='w') as tar:
        item=tarfile.TarInfo('evil'); item.type=tarfile.SYMTYPE; item.linkname='/home/user'
        tar.addfile(item)
    with pytest.raises(ValueError,match='link'): unpack(out.getvalue(),10000)


def test_owned_container_cancellation_checks_identity():
    row=secure_row(); row['Config']['Labels']['org.omnilab.owner']='other'
    calls=[]
    def run(argv,**kwargs): calls.append(argv); return json.dumps([row]).encode()
    sandbox=DockerSandbox({'image':'sha256:'+'a'*64},run)
    with pytest.raises(ValueError): sandbox.stop('name','owner')
    assert len(calls)==1 and calls[0][1]=='inspect'


class VerifySandbox:
    def __init__(self, checks):
        self.checks=checks; self.created=0; self.exists=False
    def inspect(self,*args):
        if not self.exists: raise RuntimeError('No such container')
        return {'State':{'Running':False,'Status':'exited','ExitCode':0}}
    def create(self,*args): self.created+=1; self.exists=True
    def put(self,*args): pass
    def start(self,*args): pass
    def read(self,*args): return {'checks':self.checks}


def test_independent_checks_detect_skips_and_restart_without_duplicate_dispatch(tmp_path):
    c=contract(tmp_path)
    store,run,jid=setup(tmp_path,c)
    job=store.claim_job({})
    result={'id':'check','argv':['python','check.py'],'covers':['a'],'exit_code':0,
            'timed_out':False,'output':'1 skipped','output_truncated':False}
    sandbox=VerifySandbox([result])
    checks=asyncio.run(verify(store,job,sandbox,c,{'subject.py':b'x=2\n'},'verify'))
    assert checks[0]['skip_detected']
    asyncio.run(verify(store,job,sandbox,c,{'subject.py':b'x=2\n'},'verify'))
    assert sandbox.created==1


def test_successful_execution_failed_verification_cannot_be_accepted(tmp_path):
    store,run,jid=setup(tmp_path)
    job=store.claim_job({})
    event,h=finish_candidate(store,job,{'changes':{}})
    TaskStore(store).update(job,verification_status='verification_failed')
    with pytest.raises(ValueError,match='verification'):
        store.decide(event,'accepted','looks good',local=True,candidate_hash=h,coverage={'a':'claim'})


def test_cancellation_stops_active_owned_verifier(tmp_path):
    c=contract(tmp_path)
    store,_,_=setup(tmp_path,c)
    job=store.claim_job({})
    class Running(VerifySandbox):
        def __init__(self):
            super().__init__([])
            self.stopped=[]
            self.exists=True
        def inspect(self,*args):
            return {'State':{'Running':True,'Status':'running'}}
        def stop(self,name,owner):
            self.stopped.append((name,owner))
            return True
    sandbox=Running()
    async def cancel():
        task=asyncio.create_task(verify(store,job,sandbox,c,{},'verify'))
        await asyncio.sleep(.02)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    asyncio.run(cancel())
    assert sandbox.stopped==[('lab-'+job['attempt_id']+'-verify',job['attempt_id'])]


def test_containerd_storage_option_is_not_enforcement():
    info={'OSType':'linux','Driver':'overlayfs','DriverStatus':[['driver-type','io.containerd.snapshotter.v1']]}
    sandbox=DockerSandbox({'image':'sha256:'+'a'*64},lambda *args,**kwargs:json.dumps(info).encode())
    with pytest.raises(ValueError,match='quota is unqualified'):
        sandbox.preflight()



def test_controller_artifact_aggregate_and_partial_write_budget(tmp_path, monkeypatch):
    import localagentbridge.selective as selective
    monkeypatch.setattr(selective, 'ARTIFACT_BUDGET', 12)
    directory = tmp_path/'artifacts'/'job'
    directory.mkdir(parents=True)
    selective.atomic_bytes(directory/'one.json', b'12345678')
    (directory/'crashed.tmp').write_bytes(b'123')
    with pytest.raises(ValueError, match='Aggregate'):
        selective.atomic_bytes(directory/'two.json', b'12')
    assert not (directory/'two.json').exists()
    with pytest.raises(ValueError, match='Aggregate'):
        selective.atomic_bytes(directory/'one.json', b'12345678')
    assert (directory/'one.json').read_bytes() == b'12345678'


def readonly_row():
    from localagentbridge.sandbox import TMPFS_MIB
    row = secure_row()
    row['HostConfig'].update(ReadonlyRootfs=True, StorageOpt={}, ShmSize=8*1024*1024,
        LogConfig={'Type':'none'}, NanoCpus=2*10**9,
        Tmpfs={p:f'rw,nosuid,nodev,size={m*1024*1024}' for p,m in TMPFS_MIB.items()})
    return row


@pytest.mark.parametrize('key,value', [('ReadonlyRootfs',False),('ShmSize',64*1024*1024),
    ('LogConfig',{'Type':'json-file'}),('NanoCpus',0),('Tmpfs',{})])
def test_readonly_profile_fails_closed_on_storage_or_resource_drift(key,value):
    row = readonly_row(); row['HostConfig'][key] = value
    sandbox = DockerSandbox({'image':'sha256:'+'a'*64,'storage_profile':'readonly_tmpfs_v1'},
        lambda *a,**k:json.dumps([row]).encode())
    with pytest.raises(ValueError, match='security'):
        sandbox.inspect('name','owner')


def test_stopped_tmpfs_is_never_restarted_or_read_as_a_result():
    row = readonly_row(); row['State'].update(Status='exited',Running=False)
    calls = []
    def command(argv,**kwargs):
        calls.append(argv)
        return json.dumps([row]).encode()
    sandbox = DockerSandbox({'image':'sha256:'+'a'*64,'storage_profile':'readonly_tmpfs_v1'},command)
    for operation in (lambda:sandbox.start('name','owner'),
                      lambda:sandbox.read('name','owner','/workspace/.'),
                      lambda:sandbox.completion('name','owner')):
        with pytest.raises(ValueError, match='tmpfs'):
            operation()
    assert all(c[1]=='inspect' for c in calls)



def test_readonly_verification_recovery_separates_integration_attempt(tmp_path):
    import uuid
    c = contract(tmp_path)
    store,_,_ = setup(tmp_path,c)
    job = store.claim_job({})
    class Collected:
        readonly = True
        image = 'sha256:'+'a'*64
        def __init__(self): self.rows = {}; self.created = []
        def inspect(self,name,owner):
            if name not in self.rows: raise RuntimeError('No such container')
            return {'State':self.rows[name]}
        def create(self,name,owner,c,mode):
            self.rows[name] = {'Running':True,'Status':'running','ExitCode':0}
            self.created.append(name)
        def put(self,*args): pass
        def start(self,*args): pass
        def completion(self,*args): return {'ExitCode':0}
        def read(self,*args):
            return {'checks':[{'id':'check','argv':['python','check.py'],'covers':['a'],
                'exit_code':0,'timed_out':False,'output':'passed','output_truncated':False}]}
        def stop(self,name,owner): self.rows[name]['Running'] = False; return True
    sandbox = Collected()
    files = {'subject.py':b'x=2\n'}
    initial = asyncio.run(verify(store,job,sandbox,c,files,'verify'))
    assert asyncio.run(verify(store,job,sandbox,c,files,'verify')) == initial
    integration = dict(job,attempt_id=str(uuid.uuid4()))
    asyncio.run(verify(store,integration,sandbox,c,files,'verify'))
    assert len(sandbox.created) == 2
    with pytest.raises(ValueError,match='binding changed'):
        asyncio.run(verify(store,job,sandbox,c,{'subject.py':b'x=3\n'},'verify'))
