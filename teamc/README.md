# Pharos — Team C reasoning layer

Portal 2 (Trial Design) risk analysis, plus the patient-safe-rewrite guardrail
Team D needs for Portal 1. Committed scope from `team-C-ai-reasoning.md`.

**The one thing this repo is for:** when a judge points at a risk flag and asks
"where did that come from," the answer is a list of NCT IDs and the arithmetic
that used them. Not "the LLM said so." There is no LLM anywhere in the Portal 2
scoring path — it is all counting, and the counting is auditable.

---

## Run it in 60 seconds

```bash
pip install -r requirements.txt

# Real data. Do this before you demo anything.
python scripts/ingest.py --condition "amyotrophic lateral sclerosis"

uvicorn teamc.api:app --reload --port 8100
open http://localhost:8100/docs
```

If you have no network yet and Team D needs a live endpoint *now*:

```bash
python scripts/make_fixture.py     # synthetic cohort, fake numbers, real shape
```

The fixture exists so Team D can integrate against a live API in hour 1 instead
of waiting on you. `/internal/health` reports the condition name, which for the
fixture reads `FIXTURE DISEASE (synthetic — not real data)` — if that string is
on screen during the demo, something has gone wrong.

Tests: `python tests/test_pipeline.py` (or `pytest -q`; needs `httpx`).

---

## What Team D consumes

Base: `http://localhost:8100`. Everything under `/internal/*`. CORS is open for
local dev — lock it down before anything is publicly routable.

### `GET /internal/failure-landscape`
Portal 2's landing panel. How this disease area fails, overall.

```jsonc
{
  "condition": "amyotrophic lateral sclerosis",
  "trials_modelled": 234,
  "unclassifiable_terminations": 11,     // show this number, don't hide it
  "modes": [{
    "mode": "RECRUITMENT",
    "label": "Recruitment failure",
    "count": 49,
    "share_of_cohort": 0.209,
    "wilson_95": [0.161, 0.267],
    "example_trials": [{"nct_id": "NCT…", "why_stopped": "…", "evidence": ["slow accrual"]}]
  }]
}
```

### `POST /internal/trial-risk-analysis`
The main event. Body is a partial trial design; every field optional.

```jsonc
// request
{ "phase": "PHASE2", "enrollment": 120, "n_sites": 1, "n_arms": 2,
  "n_criteria": 42, "primary_endpoint": "Change from baseline in ALSFRS-R total score",
  "masking": "DOUBLE", "allocation": "RANDOMIZED" }
```

```jsonc
// response (abridged)
{
  "matched_features": { "phase": "PHASE2", "site_bin": "1 site", … },
  "cohort": { "trials_modelled": 234, "failed_with_known_reason": 102,
              "completed": 132, "excluded_unspecified_reason": 11 },
  "flags": [{
    "mode": "RECRUITMENT",
    "mode_label": "Recruitment failure",
    "base_rate": 0.209,
    "estimated_rate": 0.705,
    "relative_risk": 3.37,
    "severity": "high",                      // high | moderate | watch
    "drivers": [{
      "feature_label": "number of sites",
      "value": "1 site",
      "cohort_size": 41, "failed_this_way": 34,
      "observed_rate": 0.829, "lift": 3.45,
      "wilson_95": [0.68, 0.92],
      "novel_evidence_share": 1.0,           // see "the overlap discount" below
      "cited_trials": ["NCT…", "NCT…"],
      "explanation": "34 of 41 trials with number of sites = '1 site' ended in …"
    }]
  }],
  "recommendations": [{                       // "what the successful trials did"
    "feature_label": "number of sites",
    "current_value": "1 site", "suggested_value": "6-20 sites",
    "statement": "Trials in this disease area with … ended in recruitment failure 4/67 …",
    "completed_trials_using_suggested_value": ["NCT…"],
    "failed_trials_using_current_value": ["NCT…"],
    "caveat": "Observational contrast …, not a causal estimate"
  }],
  "evidence": [{ "nct_id": "NCT…", "title": "…", "why_stopped": "…",
                 "classifier_evidence": ["slow accrual at all sites"],
                 "url": "https://clinicaltrials.gov/study/NCT…" }],
  "method": { "summary": "…", "min_support": 8, "min_lift": 1.4 }
}
```

`evidence` is pre-joined for every cited NCT ID, so rendering an evidence panel
needs no second round trip. Render `explanation` verbatim — it is written to be
read aloud.

`GET /internal/trial-risk-analysis?trial_design=<url-encoded JSON>` exists too,
matching the spec in the team doc. Prefer the POST.

### `GET /internal/trials/{nct_id}`
Full record for one cited trial, including the exact `whyStopped` text and the
substrings the classifier matched on.

### `POST /internal/patient-safe-rewrite`
Support role for Portal 1.

```jsonc
{ "source_text": "…", "plain_text": "<candidate rewrite>", "source_ids": ["NCT…"] }
→ { "pass": false,
    "plain_text": null,                       // withheld on failure, by design
    "violations": [{ "check": "assertion-introduction",
                     "reason": "asserts a cure", "span": "cures" }] }
```

`plain_text` comes back `null` when the check fails, so a UI that renders the
response without checking `pass` fails closed rather than shipping the bad copy.

---

## How the score works

Four sentences, in the order a skeptic will ask them.

1. **Buckets, not regression.** Every design parameter is binned into a
   categorical (`1 site`, `2-5 sites`, `6-20 sites`, `21+ sites`). That is what
   makes "trials shaped like this one" a set you can point at.
2. **Rate versus base rate.** For each bucket and each failure mode, compare the
   mode's rate among trials in that bucket against its rate across the whole
   disease area.
3. **Three guards before anything is flagged.** At least `MIN_SUPPORT` (8)
   trials in the bucket; a shrunk lift of at least `MIN_LIFT` (1.4×); and a
   Wilson 95% lower bound still above the base rate. Small-sample rates are
   pulled toward the base rate by a Beta prior worth 10 pseudo-trials, so 3-for-3
   does not become "100% failure."
4. **Combine with an overlap discount.** Surviving features are summed in log-odds
   and capped, but each successive feature is weighted by the share of failing
   trials it flags that stronger features *did not already flag*. A single-site
   academic phase 2 is also a small double-blind phase 2; naive summing would
   count those same trials four times.

### The denominators, explicitly
- Failure cohort: `TERMINATED` + `WITHDRAWN`. `SUSPENDED` is excluded — not terminal.
- Comparison cohort: `COMPLETED`.
- Terminations whose `whyStopped` is unreadable (`"N/A"`, `"Other"`, blank) are
  **excluded from the denominator entirely**, not bucketed into a mode. The count
  is surfaced as `excluded_unspecified_reason`. Bucketing them would make every
  chart look better and every number wrong.
- Stopped-early-for-benefit is detected and *not* counted as a failure.

### Failure-mode classification
Priority-ordered lexicon over `whyStopped`, returning the literal matched spans.
Priority resolves the common ambiguities: safety outranks everything (a safety
stop phrased as a sponsor decision is still a safety stop); recruitment outranks
funding (funding withdrawn *because* accrual stalled is a recruitment failure).
Text it does not understand becomes `UNSPECIFIED` rather than a guess.

Optional: run an LLM adjudication pass over `UNSPECIFIED` only. Anything it
labels is tagged `classifier: "llm"`, so you can always show a judge which share
of the chart is rules and which is model. Not wired up — rules-only is the
stronger demo.

---

## Judge Q&A crib sheet

**"How did you compute that?"**
Trials in this disease area sharing that design parameter failed this way N of M
times, against a base rate of X% — here are the NCT IDs, and here is the
`whyStopped` text for each one.

**"Isn't n=3 meaningless?"**
Yes, which is why nothing under 8 supporting trials can raise a flag, and why
small samples are shrunk toward the base rate. Point at
`method.min_support` in the response.

**"Aren't those features correlated?"**
Yes. Each feature is weighted by the fraction of failing trials it flags that
the stronger features didn't — visible per driver as `novel_evidence_share`.
In practice one feature carries the flag and the rest collapse toward zero.

**"Is this causal?"**
No, and we don't claim it is. Every recommendation ships with that caveat in the
payload. It is a historical contrast that tells you which design choices have
been associated with which failure modes, and which trials to go read.

**"What did the LLM do here?"**
Nothing in this path. Classification is a published lexicon, scoring is counting.
The only LLM in Team C's committed scope is the patient rewrite, and that one is
wrapped in a guardrail that fails closed.

**"What's your biggest weakness?"** (ask this of yourselves before they do)
`whyStopped` is self-reported and sponsors under-report unflattering reasons —
futility and business decisions are almost certainly undercounted relative to
recruitment, which is the least embarrassing thing to admit. The
`excluded_unspecified_reason` count is the visible edge of that problem.

---

## Wiring notes

- **Convoke boundary.** Nothing in this package imports or reads Convoke data.
  When you add the MCP connection for Portal 3, keep it in a separate module and
  do not import it from `safety.py` or `api.py`'s rewrite route. The rewrite
  endpoint reads only the text passed to it — that property is what makes the
  boundary checkable rather than a promise. Verify with Team A that the
  public/patient route cannot reach this service at all.
- **Nothing fetches at request time.** `ingest.py` writes `data/model.json`; the
  API only reads it. A cold ClinicalTrials.gov call can never stall the demo.
- **Team B's enrichment** slots into the evidence panel: key each item by NCT ID
  and merge into the `evidence` array. The risk math does not depend on it, so a
  late or partial Bright Data feed degrades the colour commentary, not the flags.

## Layout

```
teamc/ctgov.py         CT.gov v2 client, cursor pagination, cohort pull
teamc/failure_modes.py whyStopped → failure mode, with evidence spans
teamc/features.py      design-parameter extraction and binning
teamc/stats.py         Wilson intervals, empirical-Bayes shrinkage
teamc/risk.py          the model: cells, scoring, counterfactuals
teamc/safety.py        patient-rewrite guardrail (deterministic, fails closed)
teamc/api.py           FastAPI, /internal/*
scripts/ingest.py      real data → data/model.json      ← run this
scripts/make_fixture.py synthetic cohort for offline integration
tests/test_pipeline.py 20 tests over the claims we make out loud
```

## Checklist status

- [x] Failure clustering + design-parameter comparison, end to end
- [x] `/internal/trial-risk-analysis` exposed, evidence pre-joined for Team D
- [x] `/internal/patient-safe-rewrite` guardrail, fails closed
- [ ] **Confirm the disease area with Teams A/B and run `ingest.py` against it**
- [ ] Convoke MCP connection (Portal 3, stretch)
- [ ] 4-step repurposing pipeline (Portal 3, stretch)
