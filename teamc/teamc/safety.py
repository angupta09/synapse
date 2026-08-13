"""Guardrail for patient-facing plain-language rewrites.

The failure mode we are defending against is specific and real: an LLM asked to
"simplify this trial description" will smooth a hedge into a promise. "Is being
studied for" becomes "treats". "May reduce" becomes "reduces". A 2% response
rate becomes "effective for some patients."

These checks are deterministic and run *before* any model-based check, so the
guardrail still holds when Bedrock is slow, rate-limited, or down mid-demo.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class SafetyVerdict:
    passed: bool
    violations: list[dict] = field(default_factory=list)
    checks_run: list[str] = field(default_factory=list)


# Phrases that assert efficacy, safety or instruction, which a rewrite must
# never introduce on its own authority.
_ASSERTION_PATTERNS = [
    (r"\b(cures?|cured|curing)\b", "asserts a cure"),
    (r"\b(will|does|do) (treat|cure|stop|reverse|prevent|fix)\b", "asserts an outcome"),
    (r"\bproven to\b", "asserts proof"),
    (r"\bguarantee", "guarantees an outcome"),
    (r"\b(safe|effective|works) for (you|patients|everyone|most people)\b",
     "asserts general efficacy or safety"),
    (r"\byou should (take|start|stop|switch|try)\b", "gives treatment instruction"),
    (r"\bstop taking\b", "gives treatment instruction"),
    (r"\b(recommended|best) (treatment|option|choice) for you\b",
     "gives personalised recommendation"),
    (r"\bno (side effects|risks)\b", "asserts absence of harm"),
    (r"\bbetter than\b", "asserts comparative superiority"),
]

# Hedges in the source that must survive into the rewrite if present.
_HEDGES = [
    r"\bmay\b", r"\bmight\b", r"\bcould\b", r"\bis being (studied|tested|investigated)\b",
    r"\bunder investigation\b", r"\bnot (yet )?approved\b", r"\binvestigational\b",
    r"\bin (a )?(clinical )?trial\b", r"\bpreliminary\b", r"\bsuggests?\b",
]

_NUMBER = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)\s*(%|percent|mg|mcg|patients|"
                     r"participants|weeks?|months?|years?|days?)?", re.IGNORECASE)


def _numbers(text: str) -> set[str]:
    out = set()
    for m in _NUMBER.finditer(text or ""):
        unit = (m.group(2) or "").lower().rstrip("s")
        unit = "percent" if unit in {"%", "percent"} else unit
        out.add(f"{float(m.group(1)):g}{('|' + unit) if unit else ''}")
    return out


def check_patient_safe(source_text: str, candidate: str | None) -> SafetyVerdict:
    """Verify a rewrite introduces no claim absent from its source."""
    checks: list[str] = []
    violations: list[dict] = []

    if candidate is None:
        return SafetyVerdict(True, [], ["no-candidate-supplied"])

    src = source_text or ""
    cand = candidate

    # 1. No new asserted claims that the source does not itself make.
    checks.append("assertion-introduction")
    for pat, why in _ASSERTION_PATTERNS:
        in_cand = re.search(pat, cand, re.IGNORECASE)
        in_src = re.search(pat, src, re.IGNORECASE)
        if in_cand and not in_src:
            violations.append({
                "check": "assertion-introduction",
                "reason": why,
                "span": in_cand.group(0),
            })

    # 2. Hedges present in the source must not be dropped wholesale.
    checks.append("hedge-preservation")
    src_hedges = [h for h in _HEDGES if re.search(h, src, re.IGNORECASE)]
    if src_hedges and not any(re.search(h, cand, re.IGNORECASE) for h in _HEDGES):
        violations.append({
            "check": "hedge-preservation",
            "reason": "source hedges its claims but the rewrite states them flatly",
            "span": src_hedges[0],
        })

    # 3. Every number in the rewrite must appear in the source.
    checks.append("numeric-grounding")
    new_numbers = _numbers(cand) - _numbers(src)
    for n in sorted(new_numbers):
        violations.append({
            "check": "numeric-grounding",
            "reason": "figure does not appear in the source content",
            "span": n.replace("|", " "),
        })

    # 4. Negation flips ("not approved" -> "approved").
    checks.append("negation-flip")
    for phrase in ["approved", "eligible", "available", "recommended"]:
        neg_src = re.search(rf"\bnot (yet )?{phrase}\b", src, re.IGNORECASE)
        pos_cand = re.search(rf"(?<!not )(?<!not yet )\b(is|are) {phrase}\b",
                             cand, re.IGNORECASE)
        if neg_src and pos_cand:
            violations.append({
                "check": "negation-flip",
                "reason": f"source says not {phrase}; rewrite says {phrase}",
                "span": pos_cand.group(0),
            })

    return SafetyVerdict(passed=not violations, violations=violations, checks_run=checks)
