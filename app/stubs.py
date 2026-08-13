"""Placeholder data so the UI builds before Team A/C land their APIs.

Demo disease area is ALS (MASTER.md §7 says lock one in advance): it has approved
drugs in openFDA, dense ClinicalTrials.gov coverage, and a well-documented recent
failure (AMX0035/Relyvrio withdrawn after PHOENIX) for the Portal 2 story.

Drug/approval facts here are real. STUDY IDENTIFIERS AND PERCENTAGES ARE INVENTED
placeholders — the UI shows a stub banner while BACKEND_URL is unset so nothing
fabricated can reach a judge unlabelled.
"""

_PATIENT_ROWS = [
    {
        "name": "Riluzole",
        "kind": "approved",
        "status": "Approved",
        "phase": "—",
        "study_id": "FDA label",
        "location": "Widely available",
        "summary": (
            "A tablet taken twice a day. It is thought to reduce damage to nerve "
            "cells by lowering levels of a chemical messenger called glutamate. In "
            "studies it extended survival modestly. It does not reverse symptoms."
        ),
        "contact": "Ask your neurologist — available by prescription.",
        "sources": [
            {"label": "openFDA drug label — riluzole", "url": "https://open.fda.gov/apis/drug/label/"}
        ],
    },
    {
        "name": "Edaravone",
        "kind": "approved",
        "status": "Approved",
        "phase": "—",
        "study_id": "FDA label",
        "location": "Widely available",
        "summary": (
            "Given as an infusion or an oral liquid, in repeating cycles. It is an "
            "antioxidant, meaning it may protect nerve cells from a type of stress "
            "damage. Trials showed a slower decline in daily-function scores in a "
            "specific group of people early in their disease."
        ),
        "contact": "Ask your neurologist — available by prescription.",
        "sources": [
            {"label": "openFDA drug label — edaravone", "url": "https://open.fda.gov/apis/drug/label/"}
        ],
    },
    {
        "name": "Tofersen",
        "kind": "approved",
        "status": "Approved",
        "phase": "—",
        "study_id": "FDA label",
        "location": "Specialist centers",
        "summary": (
            "For people whose ALS is caused by a change in a gene called SOD1. It is "
            "given into the fluid around the spinal cord. It works by reducing the "
            "amount of a harmful protein the gene produces. A genetic test is needed "
            "first to know whether it applies to you."
        ),
        "contact": "Requires SOD1 genetic testing — ask your care team about referral.",
        "sources": [
            {"label": "openFDA drug label — tofersen", "url": "https://open.fda.gov/apis/drug/label/"}
        ],
    },
    {
        "name": "Investigational antisense therapy (FUS-targeted)",
        "kind": "trial",
        "status": "Currently accepting patients",
        "phase": "Phase 3",
        "study_id": "NCT00000001",
        "location": "Boston, MA · Rochester, MN · San Francisco, CA",
        "summary": (
            "An experimental treatment for people whose ALS is linked to a change in "
            "the FUS gene. It aims to reduce production of a harmful protein. Because "
            "it is still being studied, we do not yet know whether it helps."
        ),
        "contact": "Study contact listed on ClinicalTrials.gov record.",
        "sources": [
            {"label": "ClinicalTrials.gov study record", "url": "https://clinicaltrials.gov/"}
        ],
    },
    {
        "name": "Autologous stem cell therapy",
        "kind": "trial",
        "status": "Currently accepting patients",
        "phase": "Phase 2",
        "study_id": "NCT00000002",
        "location": "Cleveland, OH · Houston, TX",
        "summary": (
            "Uses cells taken from your own body, processed and given back, with the "
            "aim of protecting nerve cells. Early-stage research — the main purpose is "
            "to check safety and look for early signs of benefit."
        ),
        "contact": "Study contact listed on ClinicalTrials.gov record.",
        "sources": [
            {"label": "ClinicalTrials.gov study record", "url": "https://clinicaltrials.gov/"}
        ],
    },
    {
        "name": "Combination neuroprotective regimen",
        "kind": "trial",
        "status": "Not started / not accepting patients",
        "phase": "Phase 2",
        "study_id": "NCT00000003",
        "location": "Multi-site (US) — sites not yet open",
        "summary": (
            "A planned study combining two treatments that each aim to protect nerve "
            "cells. It has been registered but is not yet enrolling. You can ask to be "
            "notified when it opens."
        ),
        "contact": "Not yet recruiting — check the record for the sponsor contact.",
        "sources": [
            {"label": "ClinicalTrials.gov study record", "url": "https://clinicaltrials.gov/"}
        ],
    },
]


def patient_options(condition: str, location: str) -> list[dict]:
    # ponytail: stub ignores the filters and returns the locked demo set; real
    # filtering is Team A's query, not the frontend's.
    return _PATIENT_ROWS


def trial_risk(disease: str, phase: str, enrollment: int, endpoint: str) -> dict:
    return {
        "design": {
            "disease": disease,
            "phase": phase,
            "enrollment": enrollment,
            "endpoint": endpoint,
        },
        "verdict": "Elevated risk",
        "headline": (
            f"Trials shaped like this one — {phase}, ~{enrollment} participants, "
            f"{endpoint} primary endpoint — stopped early in 3 of the 7 comparable "
            f"{disease} studies we found."
        ),
        "patterns": [
            {
                "reason": "Underpowered for a functional-scale endpoint",
                "pct": 43,
                "n": 7,
                "description": (
                    "Comparable studies using a functional rating scale as the primary "
                    "endpoint at this enrollment level failed to separate from placebo. "
                    "Studies that succeeded ran larger, or paired the scale with a "
                    "survival co-primary."
                ),
                "citations": [
                    {
                        "label": "Phase 3, functional scale primary, terminated",
                        "study_id": "NCT00000010",
                        "why_stopped": "Interim analysis showed futility on primary endpoint.",
                        "url": "https://clinicaltrials.gov/",
                    },
                    {
                        "label": "Phase 3, functional scale primary, completed — negative",
                        "study_id": "NCT00000011",
                        "why_stopped": "Completed; primary endpoint not met.",
                        "url": "https://clinicaltrials.gov/",
                    },
                ],
            },
            {
                "reason": "Recruitment shortfall in a rare-disease population",
                "pct": 29,
                "n": 7,
                "description": (
                    "Multi-site studies in this indication that required a narrow "
                    "time-since-onset window withdrew or terminated for slow accrual. "
                    "Widening the enrollment window or adding sites is the common fix."
                ),
                "citations": [
                    {
                        "label": "Phase 2, withdrawn before enrollment",
                        "study_id": "NCT00000012",
                        "why_stopped": "Withdrawn: insufficient enrollment.",
                        "url": "https://clinicaltrials.gov/",
                    }
                ],
            },
        ],
        "comparable_successes": [
            {
                "label": "Phase 3 with survival co-primary — completed, positive",
                "study_id": "NCT00000020",
                "differed_by": "Enrolled 2.4× more participants; co-primary survival endpoint.",
                "url": "https://clinicaltrials.gov/",
            }
        ],
    }


def repurposing_brief(query: str) -> dict:
    return {
        "query": query,
        "mechanism": "Placeholder mechanism summary — pending Team C's pipeline.",
        "candidates": [
            {
                "drug": query or "Drug X",
                "disease": "Adjacent inflammatory indication",
                "confidence": 0.62,
                "rationale": (
                    "Three other agents with overlapping mechanism showed Phase 2 "
                    "efficacy in adjacent inflammatory conditions."
                ),
                "evidence": [
                    {"label": "Comparable agent, Phase 2 positive", "study_id": "NCT00000030", "url": "https://clinicaltrials.gov/"},
                    {"label": "Shared target annotation", "study_id": "HGNC ref", "url": "https://www.genenames.org/"},
                ],
            }
        ],
    }
