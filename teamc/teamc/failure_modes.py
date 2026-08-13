"""Classify the free-text `whyStopped` field into failure modes.

Design note for the judge question "how do you know that's a recruitment
failure": this is a priority-ordered lexicon, and every classification returns
the exact substrings that triggered it. Nothing is classified by vibes, and the
classifier never invents a reason for text it doesn't understand — those go to
UNSPECIFIED and are excluded from the rate math rather than silently bucketed.

An optional LLM adjudication pass (adjudicate.py) can be run over UNSPECIFIED
only; its results are tagged `classifier="llm"` so you can always show which
numbers came from rules and which came from a model.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict

RECRUITMENT = "RECRUITMENT"
SAFETY = "SAFETY"
FUTILITY = "FUTILITY"
BUSINESS = "BUSINESS"
OPERATIONAL = "OPERATIONAL"
REGULATORY = "REGULATORY"
COMPLETED_EARLY = "COMPLETED_EARLY"  # stopped for *success* / interim efficacy
UNSPECIFIED = "UNSPECIFIED"

MODE_LABELS = {
    RECRUITMENT: "Recruitment failure",
    SAFETY: "Safety signal / toxicity",
    FUTILITY: "Futility / lack of efficacy",
    BUSINESS: "Funding, sponsor or business decision",
    OPERATIONAL: "Operational (site, supply, staffing, external events)",
    REGULATORY: "Regulatory or ethics hold",
    COMPLETED_EARLY: "Stopped early for benefit (not a failure)",
    UNSPECIFIED: "No interpretable reason given",
}

# Modes that count as *failures* for the risk model. COMPLETED_EARLY is a
# success and UNSPECIFIED is unknown — including either would bias the rates.
FAILURE_MODES = [RECRUITMENT, SAFETY, FUTILITY, BUSINESS, OPERATIONAL, REGULATORY]

# Priority order matters. A record saying "slow accrual, and the sponsor then
# withdrew funding" is primarily a recruitment failure; funding was downstream.
# Safety outranks everything because a safety stop is never *only* a business
# decision even when it is phrased as one.
RULES: list[tuple[str, list[str]]] = [
    (
        SAFETY,
        [
            r"safety (signal|concern|issue|finding|reason)",
            r"\badverse event",
            r"\bserious adverse",
            r"\bSAE\b",
            r"\btoxicit",
            r"\btoxic\b",
            r"dose.limiting",
            r"\bDLT\b",
            r"unacceptable risk",
            r"risk[- ]benefit",
            r"benefit[- ]risk",
            r"\bdeath(s)?\b",
            r"\bmortalit",
            r"\bDSMB\b.{0,40}(halt|stop|terminat|recommend)",
            r"(data (and )?safety monitoring).{0,60}(halt|stop|terminat)",
            r"\bhepatotox|cardiotox|neurotox|nephrotox",
        ],
    ),
    (
        FUTILITY,
        [
            r"\bfutilit",
            r"\bfutile\b",
            r"lack of (efficacy|effect|benefit|response|clinical benefit)",
            r"(did|does) not (meet|achieve).{0,30}(endpoint|efficacy)",
            r"failed to (meet|demonstrate|show)",
            r"no (significant )?(efficacy|clinical benefit|treatment effect)",
            r"interim analysis.{0,50}(no|lack|insufficient|unlikely)",
            r"unlikely to (meet|demonstrate|achieve)",
            r"negative (results|interim|efficacy)",
            r"insufficient (efficacy|activity|response)",
            r"pre.?defined (efficacy )?(criteria|threshold) (was |were )?not met",
        ],
    ),
    (
        RECRUITMENT,
        [
            r"\brecruit",
            r"\benroll",
            r"\baccrual\b",
            r"\baccrue",
            r"(low|slow|poor|insufficient|inadequate|lack of|limited|difficult).{0,25}"
            r"(subject|participant|patient|particip)",
            r"unable to (identify|find|locate).{0,25}(eligible|suitable)",
            r"no (eligible )?(subjects|patients|participants) (were )?(enrolled|identified|available)",
            r"(few|too few).{0,20}(subject|patient|participant)",
            r"eligible (patient|subject|participant).{0,30}(not|un)available",
        ],
    ),
    (
        REGULATORY,
        [
            r"\bclinical hold",
            r"\bFDA\b.{0,40}(hold|halt|request|require)",
            r"\bIRB\b.{0,40}(withdrew|suspend|terminat|did not approve|non.?approval)",
            r"(ethics|regulatory) (committee|authority).{0,40}(halt|suspend|terminat|reject)",
            r"(EMA|MHRA|Health Canada).{0,40}(hold|halt|suspend)",
            r"(GCP|protocol) (violation|non.?compliance|deviation).{0,40}(terminat|stop)",
        ],
    ),
    (
        BUSINESS,
        [
            r"\bfunding\b",
            r"\bfunded\b",
            r"\bgrant\b.{0,25}(end|expir|not renew|not fund|withdraw)",
            r"(lack|loss|withdraw|cessation) of (financial )?(support|funding|resources)",
            r"\bbudget",
            r"financial (reason|constraint|difficult|issue)",
            r"business (decision|reason|priorit)",
            r"(strategic|portfolio|corporate) (decision|reprioriti|realign|reason)",
            r"sponsor(’s|'s)? decision",
            r"(company|sponsor).{0,30}(discontinu|deprioriti|terminated the (program|development))",
            r"development (of the (drug|compound|program) )?(was )?(discontinu|halted|stopped)",
            r"(acquisition|merger|bankrupt|insolven|ceased operations)",
            r"no longer (commercially|financially) (viable|feasible)",
        ],
    ),
    (
        OPERATIONAL,
        [
            r"\bCOVID",
            r"\bpandemic\b",
            r"(principal )?investigator (left|departed|relocat|no longer|retired|unavailable)",
            r"\bPI\b (left|departed|relocat|no longer)",
            r"(staff|personnel|site).{0,30}(shortage|turnover|closed|closure|unavailable)",
            r"(drug|study drug|product|device|supply).{0,30}(supply|shortage|unavailable|expired|manufactur)",
            r"manufactur\w*.{0,30}(issue|problem|delay|failure)",
            r"(equipment|device) (failure|malfunction)",
            r"(logistic|operational) (issue|problem|difficult|constraint)",
            r"(natural disaster|war|conflict|hurricane|earthquake)",
        ],
    ),
    (
        COMPLETED_EARLY,
        [
            r"(stopped|terminated|halted) early (for|due to) (benefit|efficacy|success|overwhelming)",
            r"(met|achieved) (its |the )?primary endpoint.{0,40}(early|interim)",
            r"interim analysis.{0,40}(superior|efficacy demonstrated|met)",
            r"(demonstrat|show)\w* (clear |significant )?(benefit|efficacy).{0,30}interim",
        ],
    ),
]

# Text that means "no reason given" even though the field is non-empty.
_NULL_REASONS = {
    "", "n/a", "na", "none", "not applicable", "not specified", "unknown",
    "no reason", "no reason given", "not provided", "-", "--", ".",
    "study terminated", "terminated", "withdrawn", "study was terminated",
    "study withdrawn", "see above", "other",
}


@dataclass
class Classification:
    mode: str
    label: str
    evidence: list[str] = field(default_factory=list)
    matched_rules: list[str] = field(default_factory=list)
    secondary_modes: list[str] = field(default_factory=list)
    classifier: str = "rules"
    raw: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def classify_why_stopped(text: str | None) -> Classification:
    """Return the primary failure mode plus the literal spans that justify it."""
    raw = (text or "").strip()
    if raw.lower().strip(" .") in _NULL_REASONS or len(raw) < 3:
        return Classification(UNSPECIFIED, MODE_LABELS[UNSPECIFIED], raw=raw)

    hits: dict[str, tuple[list[str], list[str]]] = {}
    lowered = raw.lower()
    for mode, patterns in RULES:
        spans, rules = [], []
        for pat in patterns:
            for m in re.finditer(pat, lowered, flags=re.IGNORECASE):
                start = max(0, m.start() - 25)
                end = min(len(raw), m.end() + 25)
                spans.append(raw[start:end].strip())
                rules.append(pat)
        if spans:
            hits[mode] = (spans[:4], sorted(set(rules))[:4])

    if not hits:
        return Classification(UNSPECIFIED, MODE_LABELS[UNSPECIFIED], raw=raw)

    # RULES is priority-ordered, so take the first mode that fired.
    for mode, _ in RULES:
        if mode in hits:
            spans, rules = hits[mode]
            return Classification(
                mode=mode,
                label=MODE_LABELS[mode],
                evidence=spans,
                matched_rules=rules,
                secondary_modes=[m for m in hits if m != mode],
                raw=raw,
            )
    return Classification(UNSPECIFIED, MODE_LABELS[UNSPECIFIED], raw=raw)
