turns fragmented public clinical trial and drug data into three focused tools: one for patients, one for trial designers, and one for R&D teams hunting for the next opportunity.

Built with Bright Data and Convoke.

The Problem
Patients with serious or rare conditions struggle to find out what treatments — approved or experimental — are actually available to them.
Most drugs fail in clinical trials, and those lessons rarely make it back into how the next trial is designed.
Drugs that hit similar biological targets could work for other diseases too, but nobody has time to test every drug-disease pair.
What We're Building
Portal	Audience	Status
Patient Portal	Patients searching for treatment options	Core
Clinical Trial Portal	Biopharma trial design teams	Core
R&D Portal	Portfolio strategy / competitive intel / BD teams	Stretch goal
1. Patient Portal

Patients pick a condition and location, then see their options laid out clearly: approved drugs, trials not yet started, and trials currently recruiting — each tagged with phase, study number, and location. Clicking an option opens a plain-English explainer and study contact info.

Only uses vetted public sources (openFDA, ClinicalTrials.gov, patient-friendly summaries) — no speculative reasoning is surfaced to patients.

2. Clinical Trial Portal

Helps trial teams answer "how should we design or benchmark this trial?" by mining patterns from past trials — what worked, what failed, and why — using ClinicalTrials.gov as the backbone and Bright Data for sponsor, investigator, and conference-level context.

3. R&D Portal (stretch)

An opportunity-mapping workspace for research and portfolio teams. Search a drug, target, or pathway and get an opportunity brief, a target-indication landscape map, drug repurposing hypotheses with confidence scores, a competitive intelligence feed, and a list of key risks and gaps.

Data Sources
ClinicalTrials.gov — authoritative trial data (REST API, daily refresh)
openFDA — approved drug labeling and approval data
Bright Data — public web context not packaged by official sources (sponsor pages, investigator sites, conference abstracts, press releases)
Convoke — biotech knowledge reasoning for internal pharma users (Portals 2 & 3 only)
