import hashlib
import json
from pathlib import Path


def test_preserved_v02_code_and_inputs_have_not_changed():
    root=Path(__file__).resolve().parents[1]/'benchmarks'/'v02'
    if root.exists():  # Private historical archive is deliberately absent from a public checkout.
        for name,digest in json.loads((root/'sha256.json').read_text()).items():
            assert hashlib.sha256((root/Path(name.replace('\\','/'))).read_bytes()).hexdigest()==digest
    public=Path(__file__).parent/'fixtures'/'paired_requests.json'
    if root.exists():
        assert public.read_bytes()==(root/'requests.json').read_bytes()
    fixtures=json.loads(public.read_text())
    assert len(fixtures)==11
    for fixture in fixtures:
        body=fixture['body']
        assert hashlib.sha256(json.dumps(body['messages'],sort_keys=True).encode()).hexdigest()==fixture['sha256']
        assert body['options']=={'temperature':0,'num_predict':600,'num_ctx':8192}
        assert body['think'] is False and body['keep_alive']==0
