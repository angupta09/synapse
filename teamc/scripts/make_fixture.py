#!/usr/bin/env python3
"""Generate a SYNTHETIC CT.gov-shaped cohort for offline testing.

  *** THE NUMBERS THIS PRODUCES ARE FAKE. ***

Its only job is to prove the pipeline runs end to end and that the statistical
guards behave (planted signals get flagged, thin cells do not). Replace it with
scripts/ingest.py before you demo anything. The model file it writes is tagged
so /internal/health reports the model as synthetic.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from teamc.risk import RiskModel  # noqa: E402

random.seed(20260813)

WHY_TEXT = {
    "RECRUITMENT": [
        "Study terminated due to slow accrual; only 4 of 60 planned subjects enrolled.",
        "Terminated: unable to recruit sufficient eligible participants at the site.",
        "Withdrawn prior to enrollment - no eligible patients identified.",
        "Poor enrollment; recruitment did not meet projections over 18 months.",
    ],
    "SAFETY": [
        "Terminated early following a dose-limiting toxicity in cohort 3.",
        "DSMB recommended termination after two serious adverse events.",
        "Study halted due to unfavourable risk-benefit profile observed at interim.",
    ],
    "FUTILITY": [
        "Interim analysis indicated the study was unlikely to meet its primary endpoint.",
        "Terminated for futility; no treatment effect observed at week 24.",
        "Pre-defined efficacy criteria were not met at the interim analysis.",
    ],
    "BUSINESS": [
        "Sponsor's decision; the development programme was discontinued for strategic reasons.",
        "Study terminated due to loss of funding following grant expiry.",
        "Business decision to reprioritise the portfolio.",
    ],
    "OPERATIONAL": [
        "Terminated due to COVID-19 related site closures.",
        "Principal investigator relocated and no replacement was identified.",
        "Study drug supply could not be maintained due to manufacturing issues.",
    ],
    "UNSPECIFIED": ["N/A", "", "Other", "Study terminated"],
}


def study(nct: int, status: str, why: str | None, phase: str, enrollment: int,
          n_sites: int, n_arms: int, masking: str, allocation: str,
          endpoint: str, n_criteria: int, sponsor_class: str) -> dict:
    crit = "Inclusion Criteria:\n\n" + "\n".join(
        f"* Criterion {i + 1} describing an eligibility requirement in prose"
        for i in range(n_criteria)
    )
    return {
        "protocolSection": {
            "identificationModule": {
                "nctId": f"NCT{nct:08d}",
                "briefTitle": f"[SYNTHETIC] Study {nct} in the fixture disease area",
            },
            "statusModule": {
                "overallStatus": status,
                **({"whyStopped": why} if why is not None else {}),
                "startDateStruct": {"date": "2019-05-01", "type": "ACTUAL"},
            },
            "sponsorCollaboratorsModule": {
                "leadSponsor": {"name": "Fixture Sponsor", "class": sponsor_class}
            },
            "conditionsModule": {"conditions": ["Fixture Disease"]},
            "designModule": {
                "studyType": "INTERVENTIONAL",
                "phases": [phase],
                "designInfo": {
                    "allocation": allocation,
                    "interventionModel": "PARALLEL",
                    "primaryPurpose": "TREATMENT",
                    "maskingInfo": {"masking": masking},
                },
                "enrollmentInfo": {"count": enrollment, "type": "ACTUAL"},
            },
            "armsInterventionsModule": {
                "armGroups": [{"label": f"Arm {i}", "type": "EXPERIMENTAL"}
                              for i in range(n_arms)]
            },
            "outcomesModule": {"primaryOutcomes": [{"measure": endpoint}]},
            "eligibilityModule": {
                "eligibilityCriteria": crit, "minimumAge": "18 Years", "sex": "ALL"
            },
            "contactsLocationsModule": {
                "locations": [{"facility": f"Site {i}", "country": "United States"}
                              for i in range(n_sites)]
            },
        }
    }


def main() -> int:
    failed, completed = [], []
    nct = 90000001

    # Planted signal: single-site, high-per-site-target trials fail on recruitment.
    for _ in range(34):
        failed.append(study(nct, "TERMINATED", random.choice(WHY_TEXT["RECRUITMENT"]),
                            "PHASE2", random.choice([60, 80, 120]), 1,
                            2, "DOUBLE", "RANDOMIZED",
                            "Change from baseline in ALSFRS-R total score", 42,
                            "OTHER")); nct += 1
    for _ in range(6):
        completed.append(study(nct, "COMPLETED", None, "PHASE2",
                               random.choice([60, 90]), 1, 2, "DOUBLE", "RANDOMIZED",
                               "Change from baseline in ALSFRS-R total score", 40,
                               "OTHER")); nct += 1

    # Planted signal: large multi-arm phase 3 trials fail on futility.
    for _ in range(19):
        failed.append(study(nct, "TERMINATED", random.choice(WHY_TEXT["FUTILITY"]),
                            "PHASE3", random.choice([400, 600, 900]),
                            random.randint(30, 60), 4, "DOUBLE", "RANDOMIZED",
                            "Overall survival", 30, "INDUSTRY")); nct += 1
    for _ in range(16):
        completed.append(study(nct, "COMPLETED", None, "PHASE3",
                               random.choice([350, 500]), random.randint(25, 55),
                               4, "DOUBLE", "RANDOMIZED", "Overall survival", 28,
                               "INDUSTRY")); nct += 1

    # Background noise across the rest of the design space.
    for _ in range(60):
        mode = random.choice(["SAFETY", "BUSINESS", "OPERATIONAL", "UNSPECIFIED",
                              "RECRUITMENT", "FUTILITY"])
        failed.append(study(
            nct, random.choice(["TERMINATED", "WITHDRAWN"]),
            random.choice(WHY_TEXT[mode]),
            random.choice(["PHASE1", "PHASE2", "PHASE3", "NA"]),
            random.choice([15, 45, 150, 320, 700]), random.randint(1, 40),
            random.randint(1, 4), random.choice(["NONE", "DOUBLE", "QUADRUPLE"]),
            random.choice(["RANDOMIZED", "NON_RANDOMIZED"]),
            random.choice(["Number of participants with adverse events",
                           "Objective response rate per RECIST 1.1",
                           "Pharmacokinetics: area under the curve (AUC)",
                           "Overall survival"]),
            random.randint(8, 55), random.choice(["INDUSTRY", "OTHER", "NIH"]),
        )); nct += 1
    for _ in range(110):
        completed.append(study(
            nct, "COMPLETED", None,
            random.choice(["PHASE1", "PHASE2", "PHASE3", "NA"]),
            random.choice([20, 55, 140, 300, 650]), random.randint(1, 45),
            random.randint(1, 4), random.choice(["NONE", "DOUBLE", "QUADRUPLE"]),
            random.choice(["RANDOMIZED", "NON_RANDOMIZED"]),
            random.choice(["Number of participants with adverse events",
                           "Objective response rate per RECIST 1.1",
                           "Pharmacokinetics: area under the curve (AUC)",
                           "Overall survival"]),
            random.randint(8, 55), random.choice(["INDUSTRY", "OTHER", "NIH"]),
        )); nct += 1

    raw = Path("data/raw-fixture"); raw.mkdir(parents=True, exist_ok=True)
    for name, rows in (("failed", failed), ("completed", completed)):
        with (raw / f"{name}.jsonl").open("w") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")

    model = RiskModel.from_cohorts(
        condition="FIXTURE DISEASE (synthetic — not real data)",
        failed_studies=failed, completed_studies=completed,
        source_note="SYNTHETIC FIXTURE. Numbers are fabricated. "
                    "Run scripts/ingest.py for real data.",
    )
    model.save(Path("data/model.json"))
    print(f"fixture: {len(failed)} failed + {len(completed)} completed "
          f"-> data/model.json")
    print(f"base rates: { {k: round(v, 3) for k, v in model.base_rates.items()} }")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
