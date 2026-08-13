"""Patient-facing safety gate.

Team B is the last checkpoint before content reaches the Patient Portal. Per the
architecture, patient-facing text must be plain-language, sourced, and free of
clinical-sounding claims the source never made.

Two layers: deterministic pattern rules (always run, never fail open) and an
optional LLM adjudication pass (only when a key is configured).
"""

from typing import Optional

from .config import HAS_LLM
from .rules import check_patterns  # noqa: F401  (re-exported for callers/tests)
from .summarize import _complete

_LLM_JUDGE_SYSTEM = """You are a safety reviewer for patient-facing medical content.

You will be given SOURCE TEXT and a DRAFT SUMMARY written from it.

Reject the draft if ANY of these are true:
1. It states a medical fact that is NOT supported by the source text.
2. It gives dosing or administration instructions.
3. It claims or implies a cure, a guarantee, or a predicted outcome for the reader.
4. It tells the reader to start, stop, or change a treatment.
5. It presents itself as a substitute for professional medical advice.

Reply with exactly one line:
PASS
or
FAIL: <short reason>"""


def check_llm(draft: str, source_text: str) -> Optional[dict]:
    """LLM grounding adjudication. Returns None when no LLM is configured."""
    if not HAS_LLM:
        return None
    verdict = _complete(
        _LLM_JUDGE_SYSTEM,
        f"SOURCE TEXT:\n{source_text[:6000]}\n\n---\n\nDRAFT SUMMARY:\n{draft}",
        max_tokens=150,
    )
    if not verdict:
        return None
    if verdict.strip().upper().startswith("PASS"):
        return {"passed": True, "reason": None}
    return {"passed": False, "reason": verdict.split(":", 1)[-1].strip()[:200]}


DISCLAIMER = (
    "This is public information to help you have a better conversation with your "
    "care team. It is not medical advice and not a recommendation."
)


def gate(draft: str, source_docs: list[dict], require_source: bool = True) -> dict:
    """Full patient-facing gate.

    Returns {passed, content, violations, checks_run, disclaimer}.
    Fails CLOSED: if anything is wrong, content is withheld rather than softened.
    """
    checks_run = ["pattern"]
    violations: list[dict] = []

    if require_source and not any(d.get("url") for d in source_docs):
        violations.append(
            {"rule": "no_source", "reason": "No source URL attached to this content", "matched": ""}
        )

    if not draft or len(draft.strip()) < 40:
        violations.append(
            {"rule": "empty", "reason": "Summary too short to be useful", "matched": ""}
        )

    violations.extend(check_patterns(draft))

    source_text = "\n\n".join(d.get("text", "") for d in source_docs)
    llm_result = check_llm(draft, source_text) if not violations else None
    if llm_result is not None:
        checks_run.append("llm_grounding")
        if not llm_result["passed"]:
            violations.append(
                {
                    "rule": "llm_grounding",
                    "reason": llm_result["reason"] or "Not supported by source text",
                    "matched": "",
                }
            )

    passed = not violations
    return {
        "passed": passed,
        "content": draft if passed else "",
        "violations": violations,
        "checks_run": checks_run,
        "disclaimer": DISCLAIMER if passed else None,
    }
