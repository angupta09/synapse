"""Run with: python -m pytest tests/ -q   (or: python tests/test_pipeline.py)

These test the claims we make out loud to a judge. If one of them fails, the
corresponding sentence in the demo script has stopped being true.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from teamc.failure_modes import (BUSINESS, FUTILITY, RECRUITMENT, SAFETY,
                                 UNSPECIFIED, classify_why_stopped)
from teamc.features import classify_endpoint, count_eligibility_criteria, extract_design
from teamc.risk import MIN_LIFT, MIN_SUPPORT, RiskModel
from teamc.safety import check_patient_safe
from teamc.stats import shrink, wilson_interval


# --------------------------------------------------------- classifier

def test_classifier_basic_modes():
    assert classify_why_stopped("Slow accrual; only 3 subjects enrolled").mode == RECRUITMENT
    assert classify_why_stopped("Terminated after two serious adverse events").mode == SAFETY
    assert classify_why_stopped("Interim analysis showed futility").mode == FUTILITY
    assert classify_why_stopped("Loss of funding").mode == BUSINESS


def test_classifier_returns_evidence_spans():
    c = classify_why_stopped("Study stopped early due to slow accrual at all sites.")
    assert c.mode == RECRUITMENT
    assert c.evidence, "every classification must cite the text that triggered it"
    assert any("accrual" in e.lower() for e in c.evidence)


def test_classifier_refuses_to_guess():
    for junk in ["N/A", "", "Other", "terminated", "  .  ", None]:
        assert classify_why_stopped(junk).mode == UNSPECIFIED


def test_safety_outranks_business():
    # A safety stop dressed up as a sponsor decision is still a safety stop.
    c = classify_why_stopped(
        "Sponsor's decision to terminate following a serious adverse event."
    )
    assert c.mode == SAFETY
    assert BUSINESS in c.secondary_modes


def test_recruitment_outranks_downstream_funding():
    c = classify_why_stopped("Poor enrollment led the sponsor to withdraw funding.")
    assert c.mode == RECRUITMENT


# --------------------------------------------------------- features

def test_endpoint_classification():
    assert classify_endpoint("Overall survival") == "survival"
    assert classify_endpoint("Change from baseline in ALSFRS-R score") == "clinical_scale"
    assert classify_endpoint("Number of participants with adverse events") == "safety_tolerability"
    assert classify_endpoint("Area under the curve (AUC)") == "pk_pd_biomarker"


def test_criteria_counting():
    text = "Inclusion Criteria:\n\n* First requirement here\n* Second requirement here\n"
    assert count_eligibility_criteria(text) == 2
    assert count_eligibility_criteria(None) is None


def test_extract_design_survives_sparse_records():
    # Real CT.gov records omit modules freely; extraction must not raise.
    d = extract_design({"protocolSection": {"identificationModule": {"nctId": "NCT1"}}})
    assert d["nct_id"] == "NCT1"
    assert isinstance(d["features"], dict)


# --------------------------------------------------------- statistics

def test_wilson_is_conservative_at_small_n():
    lo, hi = wilson_interval(2, 2)
    assert lo < 0.6, "2/2 must not be treated as a 100% rate"
    assert hi == 1.0


def test_shrinkage_pulls_small_samples_to_base():
    base = 0.20
    assert abs(shrink(3, 3, base) - base) < 0.30   # n=3 stays near base
    assert shrink(40, 40, base) > 0.75             # n=40 dominates the prior


# --------------------------------------------------------- model guards

def _model() -> RiskModel:
    path = Path(__file__).resolve().parents[1] / "data" / "model.json"
    assert path.exists(), "run scripts/make_fixture.py or scripts/ingest.py first"
    return RiskModel.load(path)


def test_no_flag_without_minimum_support():
    m = _model()
    for (fkey, fval, mode), cell in m.cells.items():
        if cell["qualifies"]:
            assert cell["n"] >= MIN_SUPPORT, f"{fkey}={fval} flagged on n={cell['n']}"
            assert cell["lift"] >= MIN_LIFT
            assert cell["wilson_low"] > cell["base_rate"]


def test_every_driver_cites_real_trials():
    m = _model()
    known = {r.nct_id for r in m.records}
    r = m.score({"phase": "PHASE2", "enrollment": 120, "n_sites": 1, "n_arms": 2})
    assert r["flags"], "fixture has a planted signal; it must be detected"
    for flag in r["flags"]:
        for driver in flag["drivers"]:
            assert driver["cited_trials"], "a flag with no citations is not shippable"
            for nid in driver["cited_trials"]:
                assert nid in known


def test_unspecified_excluded_from_denominator():
    m = _model()
    r = m.score({"phase": "PHASE2", "enrollment": 120, "n_sites": 1})
    c = r["cohort"]
    assert c["excluded_unspecified_reason"] > 0
    assert c["trials_modelled"] == c["failed_with_known_reason"] + c["completed"]


def test_overlap_discount_applies():
    m = _model()
    r = m.score({"phase": "PHASE2", "enrollment": 120, "n_sites": 1, "n_arms": 2,
                 "masking": "DOUBLE", "allocation": "RANDOMIZED", "n_criteria": 42,
                 "primary_endpoint": "Change from baseline in ALSFRS-R total score"})
    drivers = [d for f in r["flags"] for d in f["drivers"]]
    assert any(d["novel_evidence_share"] < 0.5 for d in drivers), (
        "correlated design features must be discounted, not summed"
    )
    for d in drivers:
        assert abs(d["logit_contribution"]) <= abs(d["logit_contribution_undiscounted"]) + 1e-9


def test_estimate_is_capped():
    m = _model()
    r = m.score({"phase": "PHASE2", "enrollment": 120, "n_sites": 1, "n_arms": 2,
                 "masking": "DOUBLE", "allocation": "RANDOMIZED", "n_criteria": 42,
                 "primary_endpoint": "Change from baseline in ALSFRS-R total score"})
    for f in r["flags"]:
        assert 0.0 < f["estimated_rate"] < 1.0


# --------------------------------------------------------- safety guardrail

def test_guardrail_blocks_invented_efficacy():
    v = check_patient_safe(
        source_text="Drug X is being studied in a phase 2 trial for this condition.",
        candidate="Drug X treats this condition and is safe for you.",
    )
    assert not v.passed
    assert any(x["check"] == "assertion-introduction" for x in v.violations)


def test_guardrail_blocks_dropped_hedges():
    v = check_patient_safe(
        source_text="This investigational therapy may slow disease progression.",
        candidate="This therapy slows disease progression.",
    )
    assert not v.passed


def test_guardrail_blocks_invented_numbers():
    v = check_patient_safe(
        source_text="The trial enrolled participants across several centres.",
        candidate="The trial enrolled 240 participants across 12 centres.",
    )
    assert not v.passed
    assert any(x["check"] == "numeric-grounding" for x in v.violations)


def test_guardrail_blocks_negation_flip():
    v = check_patient_safe(
        source_text="This drug is not approved for this use.",
        candidate="This drug is approved for this use.",
    )
    assert not v.passed


def test_guardrail_passes_faithful_rewrite():
    v = check_patient_safe(
        source_text="Riluzole is approved to treat ALS. It may extend survival by "
                    "a few months. Side effects can include nausea.",
        candidate="Riluzole is approved to treat ALS. It may help people live a "
                  "few months longer. Some people feel sick to their stomach.",
    )
    assert v.passed, v.violations


if __name__ == "__main__":
    import traceback
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"  pass  {fn.__name__}")
        except Exception:
            failed += 1
            print(f"  FAIL  {fn.__name__}")
            traceback.print_exc()
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    raise SystemExit(1 if failed else 0)
