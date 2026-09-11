"""At most a configured number of sequential attempts, never an agent loop."""
import uuid
from .models import task_eligibility
from .schemas import compact


class AdaptiveRouter:
    def __init__(self, config, store):
        self.config, self.store = config, store

    def candidates(self, role, tool, cap, minimum=1, excluded=()):
        eligible, blocked = [], []
        cfg = self.config
        for profile in cfg.model_registry:
            if not profile.enabled or role not in profile.roles or profile.name in excluded or profile.strength < minimum:
                continue
            metrics = self.store.model_metrics(profile.name, tool)
            allowed, reason = task_eligibility(profile, cfg.adaptive, cap, metrics, tool)
            if not allowed:
                blocked.append(reason)
                continue
            eligible.append(profile)
        # Strength represents reviewed task capability, not total MoE parameters.
        eligible.sort(key=lambda p: (p.strength, p.active_parameters_b or p.total_parameters_b, p.weight_gb, p.name))
        return eligible, blocked

    def selection(self, choices, tool, cap, input_chars, hints, retry=False):
        """Preference changes ordering only; resource, role and quality gates still apply."""
        policy = self.config.adaptive
        if not policy.preferred_model:
            return choices, 'lowest strength eligible candidate'
        light = next(p for p in self.config.model_registry if p.name == policy.lightweight_model)
        threshold = policy.maximum_trivial_max_chars if cap == 'Maximum' else policy.trivial_max_chars
        trivial = (not retry and not hints.get('stronger') and not hints.get('reason') and
                   hints.get('complexity', 'simple') == 'simple' and
                   tool in ('find_relevant_context', 'summarize_context') and (cap == 'Light' or input_chars <= threshold))
        if trivial:
            return [p for p in choices if p.name == light.name], 'bounded extraction/compression: lightweight only'
        choices = [p for p in choices if p.strength > light.strength]
        preferred = next((p for p in choices if p.name == policy.preferred_model), None)
        if preferred:
            return [preferred] + [p for p in choices if p != preferred], 'substantive work: configured quality preference'
        profile = next(p for p in self.config.model_registry if p.name == policy.preferred_model)
        _, block = task_eligibility(profile, policy, cap, self.store.model_metrics(profile.name, tool), tool)
        return choices, f'quality preference unavailable ({block or "role/strength gate"}); lowest eligible substantive fallback'

    async def run(self, bridge, tool, content, objective, *, hints=None, role=None, **kwargs):
        from .bridge import BridgeError
        cfg, store = self.config, self.store
        hints = hints.model_dump() if hasattr(hints, 'model_dump') else (hints or {})
        role = role or cfg.routes[tool]
        cfg.resolve_model(tool, role)  # validate explicit role before selecting candidates
        cap = store.compute_cap(cfg.adaptive.default_cap)
        logical, previous, count = str(uuid.uuid4()), None, 0
        minimum = 2 if hints.get('complexity') == 'moderate' else 1
        reason = 'task_complexity' if minimum > 1 else 'smallest_capable'
        if cfg.adaptive.preferred_model and minimum == 1:
            reason = 'task_profile'
        attempts, result = [], None
        requested_bytes = kwargs.pop('max_bytes', None) or cfg.max_output_bytes
        profiles = {p.name:p for p in cfg.model_registry}
        prior = hints.get('previous_request_id')
        if prior:
            with store.connect() as db:
                row = db.execute("SELECT * FROM usage WHERE id=? AND source='local' AND tool=?", (prior,tool)).fetchone()
                if not row or row['model'] not in profiles:
                    raise BridgeError('previous_request_id must identify a registered local request for the same tool.')
                previous = row['model']
                logical = row['logical_id'] or row['id']
                count = db.execute('SELECT COUNT(*) FROM usage WHERE logical_id=? OR id=?', (logical,logical)).fetchone()[0]
                minimum = profiles[previous].strength + 1
                reason = hints.get('reason') or 'previous_attempt_failed'
        elif hints.get('stronger') or hints.get('reason'):
            base = profiles.get(cfg.adaptive.lightweight_model or cfg.resolve_model(tool, role)[1])
            minimum = (base.strength if base else 1) + 1
            reason = hints.get('reason') or 'explicit_stronger'

        def finish(handoff, why):
            output = result if result is not None else {}
            output['_routing'] = dict(logical_id=logical, cap=cap, attempts=attempts, handoff_to_codex=handoff, reason=why)
            if handoff:
                store.route_event(logical, previous, 'Codex', why, cap)
            if '_meta' in output:
                output['_meta']['codex_review_recommended'] = True
                for _ in range(3):
                    output['_meta']['compression_estimate'] = round(1-len(compact(output).encode())/len(content.encode()),4)
            size = len(compact(output).encode())
            if size > cfg.max_output_bytes:
                raise BridgeError('Routing result exceeds output budget; narrow the request.')
            store.route_result(logical, len(content.encode()), size, handoff, why)
            return output

        if hints.get('complexity') == 'complex':
            return finish(True, 'complex_work_requires_codex')
        for _ in range(max(0, cfg.adaptive.max_attempts-count)):
            # Re-read persisted cap between attempts, including another process's edits.
            cap = store.compute_cap(cfg.adaptive.default_cap)
            choices, blocked = self.candidates(role, tool, cap, minimum, [a['model'] for a in attempts])
            choices, selection = self.selection(choices, tool, cap, len(content)+len(objective), hints, bool(previous))
            if not choices:
                why = '; '.join(dict.fromkeys(blocked)) if blocked else 'no_enabled_capable_model'
                return finish(True, why)
            selected = choices[0]
            measured = store.model_metrics(selected.name, tool)
            quality = measured if measured.get('reviewed_cases') else selected.reliability.get(tool, {})
            reviewed = quality.get('reviewed_cases', 0)
            quality_fact = (f"quality gate passed: {reviewed} reviewed, {quality['accepted_rate']:.0%} accepted, {quality['rejected_rate']:.0%} rejected"
                            if reviewed >= cfg.adaptive.min_reviewed_cases else
                            f"insufficient quality evidence: {reviewed}/{cfg.adaptive.min_reviewed_cases} reviewed; permitted by configuration")
            facts = f"Role: {role}; complexity: {hints.get('complexity', 'simple')}; cap: {cap}; {reason}; {selection} ({selected.strength}); {quality_fact}."
            store.route_event(logical, previous, selected.name, reason, cap, tool=tool, role=role, selection_reason=facts)
            try:
                result = await bridge.analyze(tool, content, objective, role=role, with_metadata=True,
                    _held=True, _chosen_model=selected.name, _route=dict(logical_id=logical,
                    escalated_from=previous, escalation_reason=reason if previous or reason!='smallest_capable' else None,
                    route_cap=cap, selection_reason=facts),
                    max_bytes=min(requested_bytes, cfg.max_output_bytes-900), **kwargs)
                attempts.append(dict(model=selected.name,request_id=result['_meta']['request_id'],status='ok',reason=reason))
                if result.get('confidence') == 'low' or result.get('verdict') == 'uncertain':
                    reason = 'low_confidence'
                elif result.get('truncated'):
                    reason = 'truncated_result'
                else:
                    return finish(False, 'local_result_requires_verification')
            except BridgeError as error:
                with store.connect() as db:
                    row = db.execute('SELECT id FROM usage WHERE logical_id=? ORDER BY started DESC LIMIT 1',(logical,)).fetchone()
                attempts.append(dict(model=selected.name,request_id=row[0] if row else None,status='error',reason=reason))
                result = None
                if any(word in str(error) for word in ('structured JSON','output token limit','before final')):
                    reason = 'invalid_result'
                else:
                    return finish(True, str(error)[:220])
            previous, minimum = selected.name, selected.strength + 1
            if not hints.get('auto_escalate', True):
                return finish(True, reason)
        return finish(True, 'attempt_limit: '+reason)
