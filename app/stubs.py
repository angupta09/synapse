"""Placeholder data so the UI builds before Team A/C land their APIs.

Demo disease area is ALS (MASTER.md §7 says lock one in advance): it has approved
drugs in openFDA, dense ClinicalTrials.gov coverage, and a well-documented recent
failure (AMX0035/Relyvrio withdrawn after PHOENIX) for the Portal 2 story. Three
further conditions are stubbed so the portals can be exercised beyond the one
happy path — an unrecognised condition returns nothing, which is the real empty
state, not an error.

Drug/approval facts here are real. STUDY IDENTIFIERS AND PERCENTAGES ARE INVENTED
placeholders — kept in an obvious NCT0000XXXX form — and the UI shows a stub
banner while BACKEND_URL is unset so nothing fabricated can reach a judge
unlabelled.

Dict shapes are the API contract with Teams A/C (CLAUDE.md). Add rows freely;
do not rename or drop keys.
"""

# --- Portal 1: patient-facing options -------------------------------------

_ALS_ROWS = [
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
    {
        "name": "Expanded access programme — investigational neurofilament-guided dosing",
        "kind": "trial",
        "status": "Currently accepting patients",
        "phase": "Phase 1/2",
        "study_id": "NCT00000004",
        "location": (
            "Baltimore, MD · Ann Arbor, MI · Portland, OR · Miami, FL · "
            "Philadelphia, PA · Salt Lake City, UT"
        ),
        "summary": (
            "An early study that adjusts the dose based on a blood marker linked to "
            "nerve damage. Studies at this stage are mainly checking safety and how "
            "the body handles the treatment, not whether it works."
        ),
        "contact": "Referral from a treating neurologist is usually required.",
        "sources": [
            {"label": "ClinicalTrials.gov study record", "url": "https://clinicaltrials.gov/"}
        ],
    },
]

_DMD_ROWS = [
    {
        "name": "Deflazacort",
        "kind": "approved",
        "status": "Approved",
        "phase": "—",
        "study_id": "FDA label",
        "location": "Widely available",
        "summary": (
            "A corticosteroid taken by mouth. It is used to slow the loss of muscle "
            "strength. Like other steroids it has side effects that need monitoring, "
            "so your care team will weigh the benefit against them with you."
        ),
        "contact": "Ask your neuromuscular specialist — available by prescription.",
        "sources": [
            {"label": "openFDA drug label — deflazacort", "url": "https://open.fda.gov/apis/drug/label/"}
        ],
    },
    {
        "name": "Eteplirsen",
        "kind": "approved",
        "status": "Approved",
        "phase": "—",
        "study_id": "FDA label",
        "location": "Specialist centers",
        "summary": (
            "A weekly infusion for people whose Duchenne is caused by specific changes "
            "in the dystrophin gene that can be 'skipped over'. Genetic testing is "
            "needed to know whether it applies. It was approved on a measure of "
            "protein production rather than a direct measure of strength."
        ),
        "contact": "Requires genetic confirmation of an amenable mutation.",
        "sources": [
            {"label": "openFDA drug label — eteplirsen", "url": "https://open.fda.gov/apis/drug/label/"}
        ],
    },
    {
        "name": "Investigational gene transfer therapy",
        "kind": "trial",
        "status": "Currently accepting patients",
        "phase": "Phase 3",
        "study_id": "NCT00000005",
        "location": "Columbus, OH · Dallas, TX · Los Angeles, CA",
        "summary": (
            "A one-time infusion designed to deliver a shortened version of a missing "
            "gene. It is still being studied, so both how well it works and its "
            "long-term safety are unknown."
        ),
        "contact": "Study contact listed on ClinicalTrials.gov record.",
        "sources": [
            {"label": "ClinicalTrials.gov study record", "url": "https://clinicaltrials.gov/"}
        ],
    },
    {
        "name": "Anti-fibrotic add-on therapy",
        "kind": "trial",
        "status": "Not started / not accepting patients",
        "phase": "Phase 2",
        "study_id": "NCT00000006",
        "location": "Multi-site (EU) — sites not yet open",
        "summary": (
            "A planned study of a treatment aimed at reducing scarring in muscle "
            "tissue, taken alongside standard care. Registered but not yet enrolling."
        ),
        "contact": "Not yet recruiting — check the record for the sponsor contact.",
        "sources": [
            {"label": "ClinicalTrials.gov study record", "url": "https://clinicaltrials.gov/"}
        ],
    },
]

_HD_ROWS = [
    {
        "name": "Tetrabenazine",
        "kind": "approved",
        "status": "Approved",
        "phase": "—",
        "study_id": "FDA label",
        "location": "Widely available",
        "summary": (
            "A tablet used to reduce the involuntary movements (chorea) that come with "
            "Huntington's disease. It treats that symptom — it does not slow the "
            "disease itself. Mood changes are a known side effect to watch for."
        ),
        "contact": "Ask your neurologist — available by prescription.",
        "sources": [
            {"label": "openFDA drug label — tetrabenazine", "url": "https://open.fda.gov/apis/drug/label/"}
        ],
    },
    {
        "name": "Deutetrabenazine",
        "kind": "approved",
        "status": "Approved",
        "phase": "—",
        "study_id": "FDA label",
        "location": "Widely available",
        "summary": (
            "A related tablet for the same involuntary movements, taken twice a day. "
            "It is designed to stay in the body longer than tetrabenazine, which "
            "changes the dosing schedule."
        ),
        "contact": "Ask your neurologist — available by prescription.",
        "sources": [
            {"label": "openFDA drug label — deutetrabenazine", "url": "https://open.fda.gov/apis/drug/label/"}
        ],
    },
    {
        "name": "Investigational huntingtin-lowering therapy",
        "kind": "trial",
        "status": "Currently accepting patients",
        "phase": "Phase 2",
        "study_id": "NCT00000007",
        "location": "New York, NY · Chicago, IL · Toronto, ON",
        "summary": (
            "An experimental treatment that aims to reduce production of the protein "
            "that causes the disease. Earlier attempts in this class have had mixed "
            "results, so this study is testing a different dose and schedule."
        ),
        "contact": "Study contact listed on ClinicalTrials.gov record.",
        "sources": [
            {"label": "ClinicalTrials.gov study record", "url": "https://clinicaltrials.gov/"}
        ],
    },
]

_CF_ROWS = [
    {
        "name": "Ivacaftor",
        "kind": "approved",
        "status": "Approved",
        "phase": "—",
        "study_id": "FDA label",
        "location": "Widely available",
        "summary": (
            "A tablet that helps a faulty protein channel work better, for people with "
            "specific changes in the CFTR gene. A genetic test tells you whether your "
            "particular change is one it works on."
        ),
        "contact": "Ask your CF care team — depends on your CFTR mutation.",
        "sources": [
            {"label": "openFDA drug label — ivacaftor", "url": "https://open.fda.gov/apis/drug/label/"}
        ],
    },
    {
        "name": "Elexacaftor / tezacaftor / ivacaftor",
        "kind": "approved",
        "status": "Approved",
        "phase": "—",
        "study_id": "FDA label",
        "location": "Widely available",
        "summary": (
            "A combination of three medicines in one regimen that helps the faulty "
            "protein both fold correctly and work better. It applies to a much wider "
            "range of CFTR gene changes than earlier options."
        ),
        "contact": "Ask your CF care team — depends on your CFTR mutation.",
        "sources": [
            {"label": "openFDA drug label — elexacaftor", "url": "https://open.fda.gov/apis/drug/label/"}
        ],
    },
    {
        "name": "Inhaled anti-infective for chronic colonisation",
        "kind": "trial",
        "status": "Currently accepting patients",
        "phase": "Phase 3",
        "study_id": "NCT00000008",
        "location": "Seattle, WA · Denver, CO · Atlanta, GA",
        "summary": (
            "An experimental inhaled treatment aimed at long-standing lung infection. "
            "It is being compared against the current standard inhaled option."
        ),
        "contact": "Study contact listed on ClinicalTrials.gov record.",
        "sources": [
            {"label": "ClinicalTrials.gov study record", "url": "https://clinicaltrials.gov/"}
        ],
    },
    {
        "name": "mRNA-based CFTR restoration therapy",
        "kind": "trial",
        "status": "Not started / not accepting patients",
        "phase": "Phase 1",
        "study_id": "NCT00000009",
        "location": "Multi-site (US) — sites not yet open",
        "summary": (
            "A first-in-human study of an inhaled therapy that aims to supply "
            "instructions for a working version of the protein. Registered but not yet "
            "enrolling; the main purpose will be to check safety."
        ),
        "contact": "Not yet recruiting — check the record for the sponsor contact.",
        "sources": [
            {"label": "ClinicalTrials.gov study record", "url": "https://clinicaltrials.gov/"}
        ],
    },
]

# Substring keys, checked against the lowercased query. First hit wins.
_CONDITIONS = [
    ("amyotrophic", _ALS_ROWS),
    ("als", _ALS_ROWS),
    ("lou gehrig", _ALS_ROWS),
    ("duchenne", _DMD_ROWS),
    ("dmd", _DMD_ROWS),
    ("muscular dystrophy", _DMD_ROWS),
    ("huntington", _HD_ROWS),
    ("cystic fibrosis", _CF_ROWS),
    ("cftr", _CF_ROWS),
]


def _matches_location(row: dict, location: str) -> bool:
    """Approved drugs are available anywhere; trials are tied to their sites."""
    if row["kind"] == "approved":
        return True
    return location in row["location"].lower()


def patient_options(condition: str, location: str) -> list[dict]:
    # ponytail: substring match over a handful of stubbed conditions. Real
    # matching is Team A's query against ClinicalTrials.gov, not the frontend's.
    text = (condition or "").lower()
    rows = next((rows for key, rows in _CONDITIONS if key in text), [])

    place = (location or "").strip().lower()
    if place:
        rows = [r for r in rows if _matches_location(r, place)]
    return rows


# --- Portal 2: trial design risk ------------------------------------------

_ENDPOINT_PATTERNS = {
    "Functional rating scale": {
        "reason": "Underpowered for a functional-scale endpoint",
        "pct": 43,
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
    "Overall survival": {
        "reason": "Follow-up too short to observe the survival difference",
        "pct": 38,
        "description": (
            "Studies powered on overall survival in this indication needed longer "
            "follow-up than planned before the curves separated. Those that read out "
            "positive had either a longer minimum follow-up or an event-driven "
            "analysis rather than a fixed time point."
        ),
        "citations": [
            {
                "label": "Phase 3, survival primary, terminated at interim",
                "study_id": "NCT00000013",
                "why_stopped": "Terminated: conditional power below futility threshold.",
                "url": "https://clinicaltrials.gov/",
            },
            {
                "label": "Phase 2/3, survival primary, completed — negative",
                "study_id": "NCT00000014",
                "why_stopped": "Completed; no significant difference in overall survival.",
                "url": "https://clinicaltrials.gov/",
            },
        ],
    },
    "Biomarker change": {
        "reason": "Surrogate endpoint not accepted as evidence of benefit",
        "pct": 51,
        "description": (
            "Comparable studies hit their biomarker endpoint but could not show a "
            "matching change in how patients felt or functioned, and the result did "
            "not support approval. Programs that carried a biomarker forward paired "
            "it with a clinical co-primary in the same study."
        ),
        "citations": [
            {
                "label": "Phase 2, biomarker primary met, program discontinued",
                "study_id": "NCT00000015",
                "why_stopped": "Sponsor decision; biomarker change not accompanied by clinical benefit.",
                "url": "https://clinicaltrials.gov/",
            },
            {
                "label": "Phase 3, biomarker co-primary, completed — mixed",
                "study_id": "NCT00000016",
                "why_stopped": "Completed; biomarker endpoint met, clinical endpoint not met.",
                "url": "https://clinicaltrials.gov/",
            },
        ],
    },
    "Composite": {
        "reason": "Composite driven by its least meaningful component",
        "pct": 34,
        "description": (
            "In comparable studies the composite endpoint moved mainly on its softest "
            "component, and regulators discounted the result. Studies that held up "
            "pre-specified the component hierarchy and reported each part separately."
        ),
        "citations": [
            {
                "label": "Phase 3, composite primary, completed — contested",
                "study_id": "NCT00000017",
                "why_stopped": "Completed; effect concentrated in one non-fatal component.",
                "url": "https://clinicaltrials.gov/",
            }
        ],
    },
}

_UNDERPOWERED = {
    "reason": "Enrollment below the level comparable studies needed",
    "pct": 46,
    "description": (
        "Studies in this indication that enrolled at this level were unable to detect "
        "an effect of the size seen in earlier-phase data. The comparable studies that "
        "read out positive enrolled substantially more participants."
    ),
    "citations": [
        {
            "label": "Phase 2, small cohort, completed — inconclusive",
            "study_id": "NCT00000018",
            "why_stopped": "Completed; effect estimate too imprecise to interpret.",
            "url": "https://clinicaltrials.gov/",
        }
    ],
}

_RECRUITMENT = {
    "reason": "Recruitment shortfall in a rare-disease population",
    "pct": 29,
    "description": (
        "Multi-site studies in this indication that required a narrow time-since-onset "
        "window withdrew or terminated for slow accrual. Widening the enrollment "
        "window or adding sites is the common fix."
    ),
    "citations": [
        {
            "label": "Phase 2, withdrawn before enrollment",
            "study_id": "NCT00000012",
            "why_stopped": "Withdrawn: insufficient enrollment.",
            "url": "https://clinicaltrials.gov/",
        }
    ],
}

_SUCCESSES = {
    "Functional rating scale": {
        "label": "Phase 3 with survival co-primary — completed, positive",
        "study_id": "NCT00000020",
        "differed_by": "Enrolled 2.4× more participants; co-primary survival endpoint.",
        "url": "https://clinicaltrials.gov/",
    },
    "Overall survival": {
        "label": "Phase 3, event-driven survival analysis — completed, positive",
        "study_id": "NCT00000021",
        "differed_by": "Analysis triggered by event count rather than a fixed date; 18 months longer follow-up.",
        "url": "https://clinicaltrials.gov/",
    },
    "Biomarker change": {
        "label": "Phase 3, biomarker plus clinical co-primary — completed, positive",
        "study_id": "NCT00000022",
        "differed_by": "Carried a clinical co-primary in the same study rather than deferring it.",
        "url": "https://clinicaltrials.gov/",
    },
    "Composite": {
        "label": "Phase 3, hierarchical composite — completed, positive",
        "study_id": "NCT00000023",
        "differed_by": "Pre-specified component hierarchy and reported each component separately.",
        "url": "https://clinicaltrials.gov/",
    },
}

_ENRICHED_SITES = {
    "label": "Phase 3, enrichment by biomarker-defined subgroup — completed, positive",
    "study_id": "NCT00000024",
    "differed_by": "Enrolled from 62 sites across 9 countries and restricted to a defined subgroup.",
    "url": "https://clinicaltrials.gov/",
}

_VERDICTS = {0: "Comparable to trials that completed", 1: "Moderate risk", 2: "Elevated risk", 3: "High risk"}


def trial_risk(disease: str, phase: str, enrollment: int, endpoint: str) -> dict:
    # ponytail: pattern selection is a lookup plus two enrollment thresholds, so
    # the portal visibly reacts to the form. Team C's model replaces this whole
    # function; only the returned shape is load-bearing.
    patterns = []

    endpoint_pattern = _ENDPOINT_PATTERNS.get(endpoint)
    if endpoint_pattern:
        patterns.append(endpoint_pattern)
    if enrollment < 120:
        patterns.append(_UNDERPOWERED)
    if enrollment >= 250:
        patterns.append(_RECRUITMENT)

    verdict = _VERDICTS[min(len(patterns), 3)]
    reviewed = 7

    if patterns:
        headline = (
            f"Trials shaped like this one — {phase}, ~{enrollment} participants, "
            f"{endpoint} primary endpoint — stopped early or read out negative in "
            f"{len(patterns) + 1} of the {reviewed} comparable {disease} studies we found."
        )
    else:
        headline = (
            f"No matching failure pattern. Across {reviewed} comparable {disease} "
            f"studies, {phase} designs at ~{enrollment} participants with a "
            f"{endpoint} primary endpoint completed as planned."
        )

    successes = [_SUCCESSES.get(endpoint, _SUCCESSES["Functional rating scale"])]
    if enrollment >= 250:
        successes.append(_ENRICHED_SITES)

    return {
        "design": {
            "disease": disease,
            "phase": phase,
            "enrollment": enrollment,
            "endpoint": endpoint,
        },
        "verdict": verdict,
        "headline": headline,
        "patterns": [dict(p, n=reviewed) for p in patterns],
        "comparable_successes": successes,
    }


# --- Portal 3: repurposing brief ------------------------------------------

_CTG = "https://clinicaltrials.gov/"
_HGNC = "https://www.genenames.org/"

_BRIEFS = {
    "sod1": {
        "mechanism": (
            "SOD1 encodes an enzyme that clears a reactive by-product of normal cell "
            "metabolism. Variants associated with familial ALS are thought to act "
            "through a toxic gain of function rather than loss of the enzyme's normal "
            "activity, which is why lowering the protein — rather than replacing it — "
            "is the strategy carried into the clinic."
        ),
        "candidates": [
            {
                "drug": "Antisense oligonucleotide (protein-lowering)",
                "disease": "SOD1-associated ALS",
                "confidence": 0.71,
                "rationale": (
                    "Direct match to the target mechanism, with an approved agent in "
                    "the same modality and indication establishing the regulatory path."
                ),
                "evidence": [
                    {"label": "Approved agent, same target and modality", "study_id": "openFDA label", "url": "https://open.fda.gov/apis/drug/label/"},
                    {"label": "Target annotation — SOD1", "study_id": "HGNC:11179", "url": _HGNC},
                ],
            },
            {
                "drug": "Metal-chaperone small molecule",
                "disease": "SOD1-associated ALS",
                "confidence": 0.44,
                "rationale": (
                    "Acts on protein misfolding upstream of the same pathway. Two "
                    "comparable agents reached Phase 2 in this indication; neither has "
                    "reported a positive Phase 3."
                ),
                "evidence": [
                    {"label": "Comparable agent, Phase 2 completed", "study_id": "NCT00000030", "url": _CTG},
                    {"label": "Comparable agent, Phase 2 terminated", "study_id": "NCT00000031", "url": _CTG},
                ],
            },
            {
                "drug": "Oxidative-stress modulator (approved, other indication)",
                "disease": "Sporadic ALS",
                "confidence": 0.27,
                "rationale": (
                    "Mechanistically adjacent and already approved elsewhere, so the "
                    "safety package exists. Evidence in this indication is limited to "
                    "one small open-label study."
                ),
                "evidence": [
                    {"label": "Small open-label study, single centre", "study_id": "NCT00000032", "url": _CTG},
                ],
            },
        ],
    },
    "riluzole": {
        "mechanism": (
            "Riluzole reduces glutamatergic signalling, which is implicated in "
            "excitotoxic injury to motor neurons. The same excitotoxicity mechanism is "
            "proposed in several other neurodegenerative and mood conditions, which is "
            "where its repurposing literature sits."
        ),
        "candidates": [
            {
                "drug": "Riluzole",
                "disease": "Spinocerebellar ataxia",
                "confidence": 0.53,
                "rationale": (
                    "Shared excitotoxicity rationale, with two small randomised studies "
                    "reporting improvement on an ataxia rating scale. Neither was "
                    "powered for a confirmatory claim."
                ),
                "evidence": [
                    {"label": "Randomised, small cohort, positive on rating scale", "study_id": "NCT00000033", "url": _CTG},
                    {"label": "Randomised, small cohort, positive on rating scale", "study_id": "NCT00000034", "url": _CTG},
                ],
            },
            {
                "drug": "Riluzole",
                "disease": "Treatment-resistant depression",
                "confidence": 0.31,
                "rationale": (
                    "Glutamate modulation overlaps with the mechanism of other agents "
                    "active in this indication. Adjunct studies have been mixed and the "
                    "largest reported no separation from placebo."
                ),
                "evidence": [
                    {"label": "Adjunct study, completed — negative", "study_id": "NCT00000035", "url": _CTG},
                ],
            },
        ],
    },
    "cftr": {
        "mechanism": (
            "CFTR encodes a chloride channel at the cell surface. Different classes of "
            "variant break it in different ways — some prevent it reaching the surface, "
            "others leave it there but barely open — so modulator strategies are "
            "matched to variant class rather than to the disease as a whole."
        ),
        "candidates": [
            {
                "drug": "Potentiator + corrector combination",
                "disease": "CFTR-related metabolic syndrome",
                "confidence": 0.48,
                "rationale": (
                    "Same channel defect in a milder phenotype outside the classic "
                    "diagnosis. Case series only; no registered interventional study "
                    "in this population yet."
                ),
                "evidence": [
                    {"label": "Target annotation — CFTR", "study_id": "HGNC:1884", "url": _HGNC},
                    {"label": "Observational registry record", "study_id": "NCT00000036", "url": _CTG},
                ],
            },
            {
                "drug": "Potentiator monotherapy",
                "disease": "Chronic rhinosinusitis with CFTR carrier status",
                "confidence": 0.22,
                "rationale": (
                    "Mechanistically plausible in carriers, but the single registered "
                    "study withdrew before enrolling and there is no controlled data."
                ),
                "evidence": [
                    {"label": "Phase 2, withdrawn before enrollment", "study_id": "NCT00000037", "url": _CTG},
                ],
            },
        ],
    },
}

_GENERIC_BRIEF = {
    "mechanism": (
        "No stubbed mechanism summary for this query. In the live pipeline this "
        "paragraph is Team C's synthesis over target annotations and the trial "
        "registry; the candidates below show the shape it returns."
    ),
    "candidates": [
        {
            "disease": "Adjacent inflammatory indication",
            "confidence": 0.62,
            "rationale": (
                "Three other agents with overlapping mechanism showed Phase 2 "
                "efficacy in adjacent inflammatory conditions."
            ),
            "evidence": [
                {"label": "Comparable agent, Phase 2 positive", "study_id": "NCT00000030", "url": _CTG},
                {"label": "Shared target annotation", "study_id": "HGNC ref", "url": _HGNC},
            ],
        },
        {
            "disease": "Adjacent fibrotic indication",
            "confidence": 0.35,
            "rationale": (
                "Downstream pathway overlap only. One registered study exists and it "
                "terminated for reasons unrelated to efficacy."
            ),
            "evidence": [
                {"label": "Phase 2, terminated — sponsor decision", "study_id": "NCT00000038", "url": _CTG},
            ],
        },
    ],
}


def repurposing_brief(query: str) -> dict:
    # ponytail: substring lookup with a generic fallback that echoes the query,
    # so the panel is never empty while Team C's pipeline is pending.
    text = (query or "").lower()
    brief = next((b for key, b in _BRIEFS.items() if key in text), None)

    if brief is None:
        candidates = [dict(c, drug=query or "Drug X") for c in _GENERIC_BRIEF["candidates"]]
        return {"query": query, "mechanism": _GENERIC_BRIEF["mechanism"], "candidates": candidates}

    return {"query": query, "mechanism": brief["mechanism"], "candidates": brief["candidates"]}


if __name__ == "__main__":
    assert patient_options("ALS", "")[0]["name"] == "Riluzole"
    assert patient_options("Cystic fibrosis", "")[0]["name"] == "Ivacaftor"
    assert patient_options("diabetes", "") == [], "unknown condition must hit the empty state"

    boston = patient_options("ALS", "Boston")
    assert all(r["kind"] == "approved" or "boston" in r["location"].lower() for r in boston)
    assert any(r["kind"] == "trial" for r in boston), "Boston has an ALS trial site"
    assert not any(r["kind"] == "trial" for r in patient_options("ALS", "Nowhere"))

    safe = trial_risk("ALS", "Phase 3", 400, "Overall survival")
    assert safe["patterns"], "large survival trial still matches the endpoint pattern"
    assert all(p["n"] == 7 for p in safe["patterns"])
    assert len(safe["comparable_successes"]) == 2, "big enrollment adds the multi-site success"

    small = trial_risk("ALS", "Phase 2", 60, "Functional rating scale")
    assert small["verdict"] == "Elevated risk", small["verdict"]

    clean = trial_risk("ALS", "Phase 3", 150, "Time to event")
    assert clean["patterns"] == [] and clean["verdict"] == "Comparable to trials that completed"

    assert repurposing_brief("SOD1")["candidates"][0]["confidence"] == 0.71
    assert repurposing_brief("zzz")["candidates"][0]["drug"] == "zzz"
    assert all("evidence" in c for c in repurposing_brief("riluzole")["candidates"])

    print("stubs ok")
