"""Short, bounded schemas shared by the prompt and response validator."""
import json
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field

Short = Annotated[str, Field(max_length=240)]
Items = Annotated[list[Short], Field(max_length=4)]
Confidence = Literal["low", "medium", "high"]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SourceFile(Strict):
    path: Annotated[str, Field(min_length=1, max_length=240)]
    content: Annotated[str, Field(max_length=24000)]


class Summary(Strict):
    relevant_components_files: Items
    important_findings: Items
    uncertainties: Items
    recommended_next_actions: Items


class TestAnalysis(Strict):
    failing_tests_errors: Items
    likely_cause: Short
    likely_affected_components: Items
    confidence: Confidence
    recommended_investigation: Items


class DiffReview(Strict):
    possible_bugs: Items
    regressions: Items
    suspicious_logic: Items
    missing_tests: Items
    confidence: Confidence


class CodeAnalysis(Strict):
    behavior: Short
    findings: Items
    uncertainties: Items
    recommended_tests: Items
    confidence: Confidence


class ContextSelection(Strict):
    candidate_ids: Annotated[list[Annotated[int, Field(ge=0, le=19)]], Field(max_length=8)]
    uncertainties: Items


class Triage(Strict):
    task_type: Literal["lookup", "summary", "coding", "test_failure", "review", "decision"]
    risk: Literal["low", "medium", "high"]
    local_steps: Items
    codex_decisions: Items
    confidence: Confidence


class Opinion(Strict):
    verdict: Literal["support", "concern", "uncertain"]
    reasons: Items
    checks: Items
    confidence: Confidence


class Feedback(Strict):
    request_id: Annotated[str, Field(pattern=r"^[a-f0-9-]{36}$")]
    outcome: Literal["accepted", "corrected", "rejected"]


class RoutingHints(Strict):
    complexity: Literal['simple','moderate','complex'] = 'simple'
    stronger: bool = False
    previous_request_id: Annotated[str, Field(pattern=r'^[a-f0-9-]{36}$')] | None = None
    reason: Literal['previous_attempt_failed','contradictory_evidence','unsupported_capability','explicit_stronger'] | None = None
    auto_escalate: bool = True


SCHEMAS = {"summarize_context": Summary, "analyze_test_output": TestAnalysis, "review_diff": DiffReview}
SCHEMAS.update(find_relevant_context=ContextSelection, analyze_code=CodeAnalysis, triage_task=Triage, second_opinion=Opinion)
OBJECTIVES = {
    "summarize_context": "Cover each topic in the objective using supplied evidence. Preserve method/file references and concrete limits. State uncertainty only for missing evidence.",
    "analyze_test_output": "Identify actual failures, likely root causes and specific next investigations.",
    "review_diff": "First-pass review against intended behavior. Find bugs, regressions, suspicious logic and tests preserving the stated contract. Avoid style advice.",
    "find_relevant_context": "Select at most 3 candidate IDs that implement the objective. Prefer matching definitions and paths over imports or example query text. Never invent evidence; uncertainties describe missing evidence only.",
    "analyze_code": "Analyze code against the objective. Identify defects with references. When asked, put a concise fix or code suggestion in findings. Recommend targeted tests.",
    "triage_task": "Classify task/risk. Prefer local discovery, diagnosis, fixes and test suggestions. Reserve complex architecture, ambiguous requirements, high-risk changes, disagreement and orchestration for Codex. Codex applies changes.",
    "second_opinion": "Judge the proposal exactly as written, not a safer alternative. support means consistent with all given facts; concern means it violates a given constraint; uncertain means missing evidence. Check concrete consequences. Give brief reasons and checks.",
}


def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def bounded_result(tool, raw, limit):
    """Never expose unvalidated raw model output or broken/truncated JSON."""
    result = SCHEMAS[tool].model_validate_json(raw).model_dump()
    result["truncated"] = False
    while len(compact(result).encode("utf-8")) > limit:
        result["truncated"] = True
        candidates = [(len(v.encode("utf-8")), key, None) for key, v in result.items()
                      if isinstance(v, str) and key != "confidence" and v]
        candidates += [(len(item.encode("utf-8")), key, i) for key, v in result.items()
                       if isinstance(v, list) for i, item in enumerate(v)]
        if not candidates:
            raise ValueError("Response envelope exceeds output limit")
        _, key, index = max(candidates)
        if index is None:
            result[key] = result[key][:len(result[key]) // 2]
        elif len(result[key][index]) > 40:
            result[key][index] = result[key][index][:len(result[key][index]) // 2]
        else:
            result[key].pop(index)
    return result
