"""Extract comparable design parameters from a ClinicalTrials.gov v2 record.

Everything here is a *binned categorical* on purpose. Binning is what lets you
say "trials shaped like this one" and point at the specific past trials in the
same bin. Continuous regression coefficients would be harder to cite and, at the
sample sizes available for a single disease area, less honest.

Field paths verified against live v2 payloads (2026-08-13).
"""
from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------- bin helpers

ENROLLMENT_BINS = [(0, 24, "<25"), (25, 99, "25-99"), (100, 299, "100-299"),
                   (300, 999, "300-999"), (1000, 10**9, "1000+")]
SITE_BINS = [(1, 1, "1 site"), (2, 5, "2-5 sites"), (6, 20, "6-20 sites"),
             (21, 10**9, "21+ sites")]
PER_SITE_BINS = [(0, 4.999, "<5 per site"), (5, 19.999, "5-20 per site"),
                 (20, 49.999, "20-50 per site"), (50, 10**9, "50+ per site")]
ARM_BINS = [(1, 1, "1 arm"), (2, 2, "2 arms"), (3, 3, "3 arms"), (4, 10**9, "4+ arms")]
CRITERIA_BINS = [(0, 9, "<10 criteria"), (10, 24, "10-24 criteria"),
                 (25, 49, "25-49 criteria"), (50, 10**9, "50+ criteria")]


def _bin(value: float | None, bins: list[tuple[float, float, str]]) -> str | None:
    if value is None:
        return None
    for lo, hi, label in bins:
        if lo <= value <= hi:
            return label
    return None


# ------------------------------------------------------- endpoint typing

_ENDPOINT_RULES = [
    ("survival", [r"overall survival", r"\bOS\b", r"progression.free survival",
                  r"\bPFS\b", r"disease.free survival", r"event.free survival",
                  r"time to (death|progression|event)", r"\bmortalit"]),
    ("safety_tolerability", [r"adverse event", r"\bAE\b", r"\bSAE\b", r"toxicit",
                             r"dose.limiting", r"\bDLT\b", r"tolerabilit",
                             r"maximum tolerated dose", r"\bMTD\b", r"safety"]),
    ("pk_pd_biomarker", [r"pharmacokinetic", r"\bAUC\b", r"\bCmax\b", r"\bCtrough\b",
                         r"plasma concentration", r"biomarker", r"pharmacodynamic",
                         r"receptor occupancy", r"antibod(y|ies) (titer|response)"]),
    ("tumor_response", [r"objective response", r"\bORR\b", r"\bRECIST\b",
                        r"response rate", r"complete response", r"disease control rate"]),
    ("clinical_scale", [r"\bscore\b", r"\bscale\b", r"questionnaire", r"\bALSFRS",
                        r"\bMMSE\b", r"\bEDSS\b", r"\bUPDRS\b", r"\bHAM-?D\b",
                        r"quality of life", r"\bQoL\b", r"patient.reported",
                        r"change from baseline in .*(score|scale|index)"]),
    ("function_lab", [r"forced vital capacity", r"\bFVC\b", r"\bFEV1\b",
                      r"6.minute walk", r"\b6MWD?\b", r"muscle strength",
                      r"serum level", r"\bHbA1c\b", r"ejection fraction"]),
]


def classify_endpoint(measure_text: str) -> str:
    t = measure_text or ""
    for label, pats in _ENDPOINT_RULES:
        for p in pats:
            if re.search(p, t, flags=re.IGNORECASE):
                return label
    return "other"


# ------------------------------------------------------- criteria counting

def count_eligibility_criteria(text: str | None) -> int | None:
    """Count discrete criteria bullets in the free-text eligibility blob.

    CT.gov returns one prose blob; bullets are '* ' or '1. ' or newline-separated
    clauses. This deliberately undercounts run-on prose rather than inflating it.
    """
    if not text:
        return None
    lines = [ln.strip() for ln in text.split("\n")]
    bullets = [
        ln for ln in lines
        if re.match(r"^([*\-\u2022]|\d+[.)]|[a-z][.)])\s+", ln) and len(ln) > 12
    ]
    if bullets:
        return len(bullets)
    sentences = [s for s in re.split(r"[.;]\s+", text) if len(s.strip()) > 20]
    return len(sentences) or None


# ------------------------------------------------------- main extractor

def extract_design(study: dict) -> dict[str, Any]:
    """Flatten a v2 study record into the design features the model scores on."""
    ps = study.get("protocolSection", {}) or {}
    ident = ps.get("identificationModule", {}) or {}
    status = ps.get("statusModule", {}) or {}
    design = ps.get("designModule", {}) or {}
    design_info = design.get("designInfo", {}) or {}
    arms_mod = ps.get("armsInterventionsModule", {}) or {}
    outcomes = ps.get("outcomesModule", {}) or {}
    elig = ps.get("eligibilityModule", {}) or {}
    locs_mod = ps.get("contactsLocationsModule", {}) or {}
    sponsor_mod = ps.get("sponsorCollaboratorsModule", {}) or {}

    enrollment = (design.get("enrollmentInfo", {}) or {}).get("count")
    enrollment_type = (design.get("enrollmentInfo", {}) or {}).get("type")
    arm_groups = arms_mod.get("armGroups") or []
    n_arms = len(arm_groups) or None
    locations = locs_mod.get("locations") or []
    n_sites = len(locations) or None
    countries = sorted({l.get("country") for l in locations if l.get("country")})

    phases = design.get("phases") or []
    phase = "|".join(phases) if phases else "NA"

    primaries = outcomes.get("primaryOutcomes") or []
    primary_text = primaries[0].get("measure", "") if primaries else ""
    endpoint_type = classify_endpoint(primary_text) if primary_text else None

    criteria_n = count_eligibility_criteria(elig.get("eligibilityCriteria"))

    per_site = None
    if enrollment and n_sites:
        per_site = enrollment / n_sites

    min_age = elig.get("minimumAge")
    max_age = elig.get("maximumAge")

    return {
        "nct_id": ident.get("nctId"),
        "title": ident.get("briefTitle"),
        "overall_status": status.get("overallStatus"),
        "why_stopped": status.get("whyStopped"),
        "start_date": (status.get("startDateStruct") or {}).get("date"),
        "lead_sponsor": (sponsor_mod.get("leadSponsor") or {}).get("name"),
        "conditions": (ps.get("conditionsModule", {}) or {}).get("conditions") or [],
        # ---- raw values (shown in the UI, not scored directly)
        "enrollment": enrollment,
        "enrollment_type": enrollment_type,
        "n_arms": n_arms,
        "n_sites": n_sites,
        "n_countries": len(countries) or None,
        "n_criteria": criteria_n,
        "primary_endpoint_text": primary_text,
        "n_primary_endpoints": len(primaries) or None,
        # ---- scored features (binned categoricals)
        "features": {
            k: v for k, v in {
                "phase": phase,
                "enrollment_bin": _bin(enrollment, ENROLLMENT_BINS),
                "site_bin": _bin(n_sites, SITE_BINS),
                "per_site_bin": _bin(per_site, PER_SITE_BINS),
                "arm_bin": _bin(n_arms, ARM_BINS),
                "criteria_bin": _bin(criteria_n, CRITERIA_BINS),
                "endpoint_type": endpoint_type,
                "masking": (design_info.get("maskingInfo") or {}).get("masking"),
                "allocation": design_info.get("allocation"),
                "sponsor_class": (sponsor_mod.get("leadSponsor") or {}).get("class"),
                "multi_country": ("multi-country" if len(countries) > 1
                                  else "single-country" if countries else None),
                "age_restricted": ("age-restricted"
                                   if (min_age and min_age != "18 Years") or max_age
                                   else "no-age-restriction"),
            }.items() if v
        },
    }


# Human-readable names for the feature keys, used in explanations.
FEATURE_LABELS = {
    "phase": "phase",
    "enrollment_bin": "target enrollment",
    "site_bin": "number of sites",
    "per_site_bin": "enrollment per site",
    "arm_bin": "number of arms",
    "criteria_bin": "eligibility criteria count",
    "endpoint_type": "primary endpoint type",
    "masking": "masking",
    "allocation": "allocation",
    "sponsor_class": "sponsor class",
    "multi_country": "geographic spread",
    "age_restricted": "age restriction",
}
