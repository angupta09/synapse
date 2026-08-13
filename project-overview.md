# Hackathon MVP: Clinical Trial Intelligence Platform

## Overview

We are building an MVP for a hackathon with three core goals:

1. Help patients with serious or rare conditions understand their treatment options, including approved drugs and cutting-edge treatments available through clinical trials.
2. Learn from past clinical trial failures to identify patterns and strategies for designing and running better trials.
3. Identify opportunities for repurposing existing drugs for new disease applications, based on the progress of similar drugs hitting similar targets.

Goals 1 and 2 are the committed build. Goal 3 is a stretch goal.

Sponsors: Bright Data and Convoke.

The MVP will have up to three pages/portals:

1. **Patient Portal** — for patients (Goal 1)
2. **Biopharma Clinical Trial Portal** — for trial design teams (Goal 2)
3. **Biopharma R&D Portal** — for research and portfolio teams (Goal 3, stretch)

---

## Architecture

- **ClinicalTrials.gov + openFDA**: authoritative public backbone for trials and approved products. ClinicalTrials.gov offers a REST API, daily weekday refreshes, downloadable records, and study-structure docs. openFDA provides public drug labeling and approval-related datasets.
- **Bright Data**: collects surrounding public web context that official sources don't package neatly (sponsor pipeline pages, investigator/site pages, conference abstracts, press releases, patient community language).
- **Convoke**: organizes and reasons over biotech knowledge for internal pharma users (Portals 2 and 3).

**Important constraint**: Do not expose Convoke-style speculative reasoning directly to patients. The Patient Portal must use only the safer subset of sources:

- Approved therapies from FDA/openFDA label and approval datasets
- Recruiting trials from ClinicalTrials.gov
- Patient-friendly summaries of emerging options

Note: openFDA is publicly available data, but FDA notes not all of it is validated for clinical or production use. It should be framed as a public-information source, not a clinical decision engine.

---

## Portal 1: Patient Portal (Goal 1)

**Purpose**: Help patients understand what treatment options — approved or in trials — exist for their condition.

### Flow

1. Patient selects/searches their condition from a dropdown (or free-text search).
2. Patient adds their location (dropdown or type-ahead).
3. Patient clicks "Find Available Options."

### Results View

Results are shown in a table/columns format:

**Column 1 — Treatment Option**
- Already-approved drugs for the condition
- Clinical trials set up but not yet started
- Currently ongoing clinical trials

**Column 2 — Status label**
- Approved
- Currently accepting patients
- Not started / not accepting patients

**Additional columns**
- Phase
- Study number
- Location

### Detail Popup

Clicking any treatment option opens a popup with:
- Plain-English summary of the scientific research (for patient comprehension)
- Contact options for the study
- Other relevant patient-facing details

### Data Sources
- openFDA (approved drug labels/approvals)
- ClinicalTrials.gov (recruiting/upcoming/ongoing trials)
- Bright Data (patient-friendly context, plain-language summaries of emerging options)

---

## Portal 2: Biopharma Clinical Trial Portal (Goal 2)

**Purpose**: Answer "How should we design or benchmark the trial?" by learning from patterns in past trial failures/successes.

### Data Backbone
- ClinicalTrials.gov as the structured backbone (REST API, daily refresh, downloadable records, study-structure docs)

### Bright Data Enrichment Layer
- Sponsor pipeline pages
- Investigator/site pages
- Conference abstracts or press-release summaries
- Patient community and advocacy-site language around unmet need

### Function
Learn from previous trials to identify patterns and strategies (e.g., why trials fail, design pitfalls, benchmarking against comparable past trials) to inform better trial design going forward.

---

## Portal 3: Biopharma R&D Portal (Goal 3 — Stretch)

**Purpose**: An opportunity-mapping workspace for early research and portfolio teams. Answers: "What should we work on next, and why?"

### Core Users
- Translational research
- Portfolio strategy
- Competitive intelligence
- BD / search-and-evaluation
- Disease-area leads

### Key Questions Answered
- Which targets or mechanisms are heating up in this disease area?
- Which drugs failed, and why?
- Are there adjacent indications worth exploring?
- What are competitors doing around this target/pathway?
- Where are the whitespace opportunities?

### Page Structure (5 blocks)

**1. Search + Opportunity Summary**
- User enters a drug, target, pathway, or disease
- Returns a compact "opportunity brief": target/mechanism, active indications, similar assets, development stage distribution, top repurposing hypotheses, major risks

**2. Target-Indication Landscape**
- Visual map showing: targets linked to diseases, drugs linked to targets, phase status by program, sponsor activity, signal/evidence strength
- Helps users see crowded vs. underexplored areas quickly

**3. Repurposing Opportunity Panel** (strongest feature)
For a selected drug or mechanism, shows:
- Adjacent diseases with similar biology
- Other drugs hitting the same target and where they succeeded
- Rationale for repurposing
- Confidence score
- Evidence used

Example output: "Drug X may have potential in Disease Y because 3 other agents with overlapping mechanism showed Phase 2 efficacy in adjacent inflammatory conditions."

**4. Competitive Intelligence Feed**
Tracks: competitor programs, new trial starts, licensing/acquisition signals, conference mentions, press release activity, investigator/academic activity. This is where Bright Data-style web enrichment is most useful.

**5. Risk / Gaps / Next Actions**
Action-oriented outputs: missing evidence, top scientific risks, biomarker gaps, recommended next analyses, suggested KOLs/papers/assets to review.

---

## Build Priority

| Priority | Portal | Status |
|---|---|---|
| 1 | Patient Portal | Committed |
| 2 | Biopharma Clinical Trial Portal | Committed |
| 3 | Biopharma R&D Portal | Stretch goal |
