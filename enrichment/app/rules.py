"""Patient-safety pattern rules.

Lives in its own module so both `safety` (the gate) and `summarize` (which
pre-filters unsafe source sentences) can use it without a circular import.
"""

import re

# Each rule: (id, human-readable reason, compiled pattern)
RULES = [
    ("dosing", "Contains dosing or administration instructions", re.compile(
        r"\b(take|inject|administer|swallow|apply)\b[^.]{0,40}\b(\d+\s*(mg|mcg|ml|g|units?|tablets?|capsules?|doses?))",
        re.I)),
    ("dosing_freq", "Contains a dosing schedule", re.compile(
        r"\b\d+\s*(mg|mcg|ml|g|units?)\b[^.]{0,30}\b(daily|twice|once|per day|every \d+|weekly)\b", re.I)),
    # Patient-facing copy should describe what a treatment IS, never its strength
    # or amount — that is prescribing territory and belongs with their clinician.
    ("dose_amount", "Mentions a specific drug amount or strength", re.compile(
        r"\b\d+(\.\d+)?\s*(mg|mcg|µg|ug|ml|mL|units?)\b", re.I)),
    ("cure_claim", "Claims a cure", re.compile(
        r"\b(cures?|cured|curing)\b(?!\s*(rate|for cancer research))", re.I)),
    ("guarantee", "Guarantees an outcome", re.compile(
        r"\b(guarantee[sd]?|guaranteed|always works|100% effective|no side effects|completely safe)\b", re.I)),
    ("directive", "Directs the reader to start or stop a treatment", re.compile(
        r"\b(you should (take|start|stop|switch|discontinue)|stop taking|start taking|discontinue your)\b", re.I)),
    ("prognosis", "Predicts the individual reader's outcome", re.compile(
        r"\b(you will (recover|improve|be cured|respond|survive)|your (cancer|disease|condition) will)\b", re.I)),
    ("miracle", "Uses sensational framing", re.compile(
        r"\b(miracle|breakthrough cure|game-?changer that cures|revolutionary cure)\b", re.I)),
    ("replace_doctor", "Positions the content as a substitute for medical advice", re.compile(
        r"\b(no need to (see|consult) (a|your) doctor|instead of (seeing|consulting) (a|your) doctor)\b", re.I)),
]


def check_patterns(text: str) -> list[dict]:
    """Deterministic rule pass. Returns a list of violations (empty == clean)."""
    violations = []
    for rule_id, reason, pattern in RULES:
        m = pattern.search(text)
        if m:
            violations.append({"rule": rule_id, "reason": reason, "matched": m.group(0)[:80]})
    return violations


def is_clean(text: str) -> bool:
    return not check_patterns(text)
