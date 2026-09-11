"""Manual real-inference checks for every explicitly configured role/model."""
import json
from .bridge import Bridge, BridgeError
from .routing import model_status


async def verify_models(config):
    statuses = await model_status(config)
    bridge = Bridge(config)
    reports = []
    for entry in statuses:
        if not entry["installed"]:
            reports.append({**entry, "verified": False})
            continue
        role = entry["role"]
        tool = {"general": "summarize_context", "coding": "analyze_code", "reasoning": "second_opinion"}[role]
        try:
            if config.adaptive.enabled:
                from .models import eligibility
                profile = next(p for p in config.model_registry if p.name==entry['model'])
                cap = bridge.store.compute_cap(config.adaptive.default_cap)
                allowed, reason = eligibility(profile,config.adaptive,cap,bridge.store.model_metrics(profile.name))
                if not profile.enabled or not allowed:
                    raise BridgeError('Exact model verification blocked by disabled model or '+str(reason)+' at '+cap)
            result = await bridge.analyze(tool,
                "math_utils.py:1\ndef add(a, b):\n    return a + b\nThe proposal is to preserve this behavior and test add(-1, 1) == 0.",
                "Assess the helper and suggested test. Be concise.", role=role, with_metadata=True,
                _chosen_model=entry['model'] if config.adaptive.enabled else None)
            request_id = result["_meta"]["request_id"]
            with bridge.store.connect() as db:
                row = db.execute("""SELECT id,model,tool,input_tokens,output_tokens,duration,tokens_per_second,
                    source_bytes,output_bytes,context_compression FROM usage WHERE id=?""", (request_id,)).fetchone()
            reports.append({"role": role, "verified": True, **dict(row)})
        except BridgeError as e:
            reports.append({**entry, "verified": False, "error": str(e)})
    print(json.dumps(reports, indent=2), flush=True)
    return all(row["verified"] for row in reports)
