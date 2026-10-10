"""Explicit SDK tool-roundtrip probe, confined to a generated disposable fixture."""
import hashlib
import json
import re
from pathlib import Path
import uuid

from .companion import git_identity
from .inference import ChatProvider
from .sandbox import DockerSandbox, tree_hash
from .selective import prepare, policy_for, artifact_dir, atomic_json, save_tree
from .selective_resources import memory_admission
from .task_contract import Contract, TaskLimits
from .task_store import TaskStore


async def start(store, config, backend, model, activate=False, context_tokens=16384, *, fixture_seed=None, limits=None, execution_guidance=""):
    if fixture_seed is not None and not re.fullmatch(r'[0-9a-f]{32}', fixture_seed):
        raise ValueError('Fixture seed must be exactly 32 lowercase hexadecimal characters')
    limits = TaskLimits.model_validate(limits or {'context_tokens': context_tokens})
    context_tokens = limits.context_tokens
    policy=policy_for(config)
    if not activate or not all(policy.get(k) for k in ('enabled','implementation_enabled')):
        raise ValueError('SDK qualification requires explicit activation and an isolated enabled implementation configuration')
    provider=ChatProvider(backend,policy['providers'][backend])
    capability=await provider.inspect(model)
    if not capability.get('ready') or not capability.get('identity_verified'):
        raise ValueError('Qualification requires a ready, verified exact local model')
    if capability.get('context_tokens', 0) < context_tokens or not capability.get('tools_advertised'):
        raise ValueError('Qualification requires sufficient context and advertised tool support')
    sandbox=DockerSandbox(policy['sandbox'])
    sandbox.preflight()
    token=fixture_seed or uuid.uuid4().hex
    root=store.directory/'qualification-fixtures'/uuid.uuid4().hex
    root.mkdir(parents=True,exist_ok=False)
    (root/'subject.py').write_text('def value():\n    return None\n')
    (root/'seed.txt').write_text(token+'\n')
    (root/'acceptance.py').write_text('from subject import value\nassert value() == '+repr(token)+'\n')
    repository,revision=git_identity(config.source_root)
    c=Contract(task_id='sdk-qualification-'+token,objective='Read seed.txt with the terminal tool, then use the file_editor tool to make subject.value() return the exact seed. Run python acceptance.py.',
       requirement_ref='Built-in SDK full tool-roundtrip qualification fixture',
       acceptance={'fixture':'python acceptance.py passes using the exact seed'},context=execution_guidance,repository=repository,
       base_revision=revision,permitted_files=['subject.py'],context_files=['subject.py','seed.txt','acceptance.py'],
       acceptance_files=['acceptance.py','seed.txt'],operations=['read','edit','test'],skills=['implementation-proposal'],
       requested_lane='local_implementation',backend=backend,model=model,exact_identity=capability['identity'],
       risk='low',ambiguity=False,coherent_scope=True,reversible=True,category='sdk-qualification',
       supervisor_approved=True,limits=limits,checks=[{'id':'fixture','argv':['python','acceptance.py'],'covers':['fixture']}])
    allowed,reason=memory_admission(c,policy)
    if not allowed:
        raise ValueError(reason)
    req=(await prepare(config,[c]))[0]
    # This exception is confined to the fixed generated probe. It does not qualify
    # user tasks or bypass model identity, memory, tool/sandbox boundaries or review.
    req['routing'].update(effective_lane='local_implementation',
                          reason='Explicit generated SDK qualification probe; compatibility remains unverified',
                          return_to_supervisor=False)
    req['qualification_fixture']=True
    run=store.create_run(repository,revision)
    jid=TaskStore(store).submit_many(run,[req])[0]
    # Trusted generated inputs bind to their exact bytes without creating a Git
    # commit or changing the repository. Only this fixed probe gets this bootstrap.
    job=store.job(jid)
    files={p.name:p.read_bytes() for p in root.iterdir()}
    save_tree(artifact_dir(store,job)/'base.json',files)
    TaskStore(store).update(job,evidence={'base_tree_hash':tree_hash(files),
        'baseline_origin':'Supervisor-activated generated SDK compatibility fixture',
        'repository_base_revision':revision})
    return {'run_id':run,'job_id':jid,'qualification':'pending; start the existing companion worker and review the candidate'}


def record(store, job_id):
    job=store.job(job_id)
    state=TaskStore(store).get(job_id)
    if (not job['request'].get('qualification_fixture') or state['verification_status']!='passed'
            or state['review_status']!='accepted' or state['accepted_hash']!=state['candidate_hash']):
        raise ValueError('The generated qualification fixture must pass independent checks and supervisor review')
    receipts=[json.loads(p.read_text()) for p in artifact_dir(store,job).glob('inference-*.json')]
    names=sorted({name for r in receipts for name in r.get('tools_called',[])})
    tool_messages=sum(r.get('tool_result_messages',0) for r in receipts)
    if not {'terminal','file_editor'}<=set(names) or not tool_messages:
        raise ValueError('No complete required SDK tool-call/result round trip was observed')
    c=job['request']['contract']
    value={'kind':'openhands_roundtrip','backend':c['backend'],'identity':c['exact_identity'],
           'context_tokens':c['limits']['context_tokens'],'image':job['request']['policy']['sandbox']['image'],
           'sdk_version':'1.53.0','verification_status':'passed','candidate_hash':state['candidate_hash'],
           'tools_called':names,'tool_result_messages':tool_messages,'job_id':job_id,
           'limitations':['One synthetic compatibility probe; task-category and quality pilot qualification remains separate.']}
    path=artifact_dir(store,job)/'qualification.json'
    atomic_json(path,value)
    return {k:value[k] for k in ('backend','identity','context_tokens','image','sdk_version')} | {
        'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'supervisor_accepted':True}
