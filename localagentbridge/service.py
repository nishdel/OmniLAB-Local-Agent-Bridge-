"""Bounded orchestration: one request, or an explicit fixed set of opinions."""
import asyncio
import uuid
import httpx
from .bridge import Bridge, BridgeError
from .context import scan_repository, candidate_prompt, evidence_result, fit_evidence
from .files import read_selected
from .routing import canonical, inventory, install_command
from .schemas import compact
from .telemetry import Recorder


class Service:
    def __init__(self, config, transport=None):
        self.config = config
        self.bridge = Bridge(config, transport)

    def content(self, text="", files=None, file_paths=None):
        parts = [text]
        if files:
            parts.append(compact([f.model_dump() if hasattr(f, "model_dump") else f for f in files]))
        if file_paths:
            parts.append(read_selected(self.config, file_paths))
        return "\n".join(p for p in parts if p)

    async def analyze(self, tool, text="", task="", *, files=None, file_paths=None, role=None, routing=None):
        return await self.bridge.analyze(tool, self.content(text, files, file_paths), task, role=role,
                                         with_metadata=bool(self.config.roles) or tool == "analyze_code", routing=routing)

    async def find_context(self, task, scope="", use_model=True, routing=None):
        cfg = self.config
        async with self.bridge.exclusive():
            candidates, coverage = await asyncio.to_thread(scan_repository, cfg, task, scope)
            selected = candidate_prompt(cfg, candidates, task)
            coverage["candidates_ranked"] = len(selected)
            warnings = ["Lexical search can miss indirect or differently named dependencies."]
            if coverage["limit_reached"]:
                warnings.append("Scan limits were reached; narrow scope or refine the query.")
            if use_model and selected:
                def project(result, budget):
                    result["uncertainties"] = (warnings + result["uncertainties"])[:4]
                    return fit_evidence(evidence_result(selected, coverage, result, cfg.search.max_results), budget)
                return await self.bridge.analyze("find_relevant_context", compact(selected), task,
                                                 with_metadata=True, projection=project, _held=True, routing=routing)
            if candidates and not selected:
                raise BridgeError("The input budget cannot fit search candidates; increase max_input_chars or narrow the query.")
            record = Recorder(self.bridge.store, "find_relevant_context", "repository-search", 0,
                              source_bytes=len(compact(selected).encode()) if selected else None)
            status, output_bytes = "error", 0
            try:
                result = evidence_result(selected, coverage, {"candidate_ids": list(range(len(selected))),
                    "uncertainties": warnings + (["No matching evidence found; refine the query."] if not selected else [])}, cfg.search.max_results)
                result = fit_evidence(result, cfg.max_output_bytes - 180)
                result["_meta"] = {"request_id": record.id, "model": "repository-search", "method": "lexical", "model_called": False}
                output_bytes = len(compact(result).encode())
                if output_bytes > cfg.max_output_bytes:
                    raise BridgeError("Search result cannot fit the output budget.")
                status = "ok"
                return result
            finally:
                record.finish({"prompt_eval_count": 0, "eval_count": 0}, output_bytes, status)

    def delegation(self, context_chars, file_count, risk, confidence="high", *,
                   complexity="simple", ambiguous=False, capability="analysis", failed_local_attempts=0):
        policy = self.config.delegation
        if risk not in ("low", "medium", "high") or confidence not in ("low", "medium", "high"):
            raise ValueError("Invalid risk or confidence")
        if complexity not in ("simple", "moderate", "complex") or capability not in ("analysis", "implementation", "architecture", "orchestration", "disagreement", "execution"):
            raise ValueError("Invalid complexity or capability")
        if min(context_chars, file_count, failed_local_attempts) < 0:
            raise ValueError("Scope and failed-attempt counts cannot be negative")
        if ambiguous:
            return "codex", "Clarify ambiguous requirements with Codex before delegating a bounded task."
        if complexity == "complex":
            return "codex", "Complex reasoning or tightly coupled multi-file changes require Codex orchestration."
        if risk == "high":
            return "codex", "Important decisions and high-risk work stay with Codex."
        if capability not in ("analysis", "implementation"):
            return "codex", "This capability requires Codex: local models only analyze or propose bounded code changes."
        if failed_local_attempts >= policy.max_failed_local_attempts:
            return "codex", "The failed-local-attempt limit was reached; stop retrying and inspect the evidence."
        levels = {"low": 0, "medium": 1, "high": 2}
        if levels[confidence] < levels[policy.min_confidence]:
            return "codex", "Local confidence is below the configured threshold."
        if file_count > policy.max_files_for_local_analysis or context_chars > self.config.max_input_chars:
            return "find_relevant_context_first", "Narrow the evidence set before local analysis; include the objective in the input budget."
        if context_chars < policy.min_context_chars and file_count < policy.min_file_count:
            if not policy.local_first:
                return "codex_direct", "The input is below the optional minimum-delegation thresholds."
            return "delegate_analysis", "Use the matching local tool directly; a separate model triage call is unnecessary."
        return "delegate_analysis", "Prefer local analysis or implementation suggestions; Codex verifies consequential findings and owns changes."

    async def triage(self, task="", context_chars=0, file_count=0, risk="low", feedback=None, *,
                     confidence="high", complexity="simple", ambiguous=False, capability="analysis", failed_local_attempts=0):
        reports = [f.model_dump() if hasattr(f, "model_dump") else f for f in (feedback or [])]
        recorded = self.bridge.store.report(reports) if reports else 0
        if not task.strip():
            if recorded:
                return {"feedback_recorded": recorded, "model_called": False}
            raise BridgeError("Supply a task or explicit feedback records.")
        hints = dict(complexity=complexity, ambiguous=ambiguous, capability=capability, failed_local_attempts=failed_local_attempts)
        delegation, reason = self.delegation(context_chars, file_count, risk, confidence, **hints)
        small = context_chars < self.config.delegation.min_context_chars and file_count < self.config.delegation.min_file_count
        if delegation != "delegate_analysis" or (small and complexity == "simple" and risk == "low"):
            self.bridge.store.decision(delegation, context_chars=context_chars, file_count=file_count, risk=risk, confidence=confidence, **hints)
            return {"delegation": delegation, "reason": reason, "feedback_recorded": recorded, "model_called": False}
        def project(result, budget):
            levels = {"low": 0, "medium": 1, "high": 2}
            chosen_risk = max((risk, result["risk"]), key=levels.get)
            chosen_confidence = min((confidence, result["confidence"]), key=levels.get)
            result["delegation"], result["reason"] = self.delegation(context_chars, file_count, chosen_risk, chosen_confidence, **hints)
            result["feedback_recorded"] = recorded
            return result
        result = await self.bridge.analyze("triage_task", task,
                                         f"Scope: {file_count} files, {context_chars} characters; risk={risk}, complexity={complexity}, capability={capability}, failed attempts={failed_local_attempts}. Keep uncertain or complex decisions with Codex.",
                                         with_metadata=True, projection=project, routing=dict(complexity=complexity))
        if result.get('_routing',{}).get('handoff_to_codex'):
            result['delegation'] = 'codex'
        self.bridge.store.decision(result["delegation"], request_id=result.get('_meta',{}).get('request_id'),
            context_chars=context_chars, file_count=file_count, risk=risk, confidence=confidence, **hints)
        return result

    async def second_opinion(self, question, context="", file_paths=None, consensus=False, roles=None, routing=None):
        content = self.content(context, file_paths=file_paths) or question
        if not consensus:
            if roles:
                raise BridgeError("roles is only used with consensus=true; single opinions use the configured route.")
            return await self.bridge.analyze("second_opinion", content, question, with_metadata=True, routing=routing)
        cfg = self.config
        selected = roles or cfg.consensus_roles
        if not 2 <= len(selected) <= 3 or len(set(selected)) != len(selected):
            raise BridgeError("Consensus requires two or three distinct configured roles.")
        models = [cfg.resolve_model("second_opinion", role)[1] for role in selected]
        if cfg.adaptive.enabled:
            from .models import eligibility
            if routing:
                raise BridgeError('Consensus is a fixed comparison; routing hints apply to single opinions only.')
            profiles = {p.name:p for p in cfg.model_registry}
            cap = self.bridge.store.compute_cap(cfg.adaptive.default_cap)
            for model in models:
                if model not in profiles or not profiles[model].enabled or not eligibility(profiles[model],cfg.adaptive,cap,self.bridge.store.model_metrics(model))[0]:
                    raise BridgeError('Consensus exceeds the compute/resource cap or uses a disabled model; return to Codex.')
        if len({canonical(model) for model in models}) != len(models):
            raise BridgeError("Consensus requires distinct models. Configure [roles]; no substitutes will be chosen.")
        if cfg.max_output_bytes < 1500:
            raise BridgeError("Consensus requires max_output_bytes >= 1500.")
        async with self.bridge.exclusive():
            try:
                installed = await inventory(cfg, self.bridge.transport)
            except (httpx.HTTPError, ValueError):
                raise BridgeError("Ollama model inventory is unavailable. Start Ollama and check /api/tags.") from None
            missing = [model for model in models if canonical(model) not in installed]
            if missing:
                raise BridgeError("Consensus models are missing. " + "; ".join(install_command(m) for m in missing) + ". No models were substituted or called.")
            group = str(uuid.uuid4())
            opinions = []
            budget = (cfg.max_output_bytes - 300) // len(selected)
            for role in selected:
                if cfg.adaptive.enabled:
                    cap = self.bridge.store.compute_cap(cfg.adaptive.default_cap)
                    model = cfg.resolve_model('second_opinion', role)[1]
                    if not eligibility(profiles[model],cfg.adaptive,cap,self.bridge.store.model_metrics(model))[0]:
                        self.bridge.store.route_event(group, opinions[-1]['_meta']['model'] if opinions else None,
                                                     'Codex', 'consensus_cap_changed', cap)
                        return {'opinions': opinions, 'codex_decides': True, 'stopped': 'consensus_cap_changed', 'cap':cap}
                opinions.append(await self.bridge.analyze("second_opinion", content, question, role=role,
                                with_metadata=True, max_bytes=budget, group_id=group, _held=True,
                                _chosen_model=cfg.resolve_model('second_opinion',role)[1] if cfg.adaptive.enabled else None))
            votes = {v: sum(o["verdict"] == v for o in opinions) for v in ("support", "concern", "uncertain")}
            result = {"opinions": opinions, "verdict_counts": votes,
                      "agreement": "unanimous" if len({o["verdict"] for o in opinions}) == 1 else "mixed",
                      "codex_decides": True}
            if len(compact(result).encode()) > cfg.max_output_bytes:
                raise BridgeError("Consensus result exceeded the output budget.")
            return result
