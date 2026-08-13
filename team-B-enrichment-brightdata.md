# Team B — Enrichment & Bright Data Engineer

See [MASTER.md](MASTER.md) for full architecture and context.

## Your mission

You own everything the official sources (ClinicalTrials.gov, openFDA) don't package neatly: sponsor pipeline pages, investigator/site pages, conference abstracts, press releases, patient-community language, and competitive signal. You turn messy public web content into clean, cited, cached artifacts that the other three portals can safely consume — "safely" being the operative word for anything that reaches the Patient Portal.

## Why this matters (don't skip this)

Bright Data calls are slow and rate-limited relative to a live demo's needs. If your pipeline isn't cached and pre-fetched before the team is on stage, a live scrape stalling for 20 seconds during the demo is the single most likely way this project visibly breaks in front of judges. Build for "pre-fetched and cached," not "fetched live on click," from the start.

## Responsibilities

1. **Enrichment pipeline (general)**
   - For the team's chosen disease area/drugs, run Bright Data searches/scrapes for: sponsor pipeline pages, investigator/site pages, conference abstracts, press releases, and (for Patient Portal use) patient-advocacy or community language describing emerging options in plain terms.
   - Cache every result (S3 or a simple table) with a fetch timestamp and TTL. Re-fetching should be explicit and rare, not automatic per request.
   - Every cached artifact must carry: source URL, fetch timestamp, and the entity/entities it relates to (join against Team A's normalized IDs).

2. **Patient Portal feed (safety-critical — read this twice)**
   - The Patient Portal may only receive **pre-vetted, plain-language summaries**, never raw scraped speculative content. You are the human/process gate before content reaches the safe API.
   - Concretely: run your scraped content through a summarization pass, then a Bedrock Guardrails (or manual) check for clinical-sounding claims that aren't sourced, before it's allowed into the `/public/*` route Team A exposes. If in doubt, cut the claim rather than soften it.

3. **Trial Design Portal feed (Portal 2)**
   - Package sponsor/investigator/conference/press context tied to specific trials (by NCT ID) so Team C's pattern-analysis pipeline can pull "surrounding context" for a trial, not just its structured fields.

4. **R&D Portal feed (Portal 3, stretch)**
   - Competitive intelligence: competitor programs, new trial starts, licensing/acquisition signals, conference mentions, press activity, investigator/academic activity — tied to target/mechanism IDs so Team C's repurposing engine can cite it as evidence.

## API surface you expose to the rest of the team

- `GET /internal/enrichment/patient-summary?condition_id=&treatment_id=` — vetted plain-language summary + source citation, for Patient Portal
- `GET /internal/enrichment/trial-context?nct_id=` — sponsor/investigator/press context for a specific trial, for Portal 2
- `GET /internal/enrichment/competitive-signal?target_id=` — competitive intelligence items, for Portal 3
- All responses include `{content, source_url, fetched_at}` at minimum — no unsourced text leaves your service.

## Task checklist (priority order)

- [ ] Confirm the disease area/drugs with the team (same as Team A — this must be locked together, first)
- [ ] Get Bright Data MCP connection working, run one end-to-end test scrape/search against a real target
- [ ] Build the cache layer (S3 or table) with TTL and source metadata
- [ ] Pull sponsor/investigator/press/conference content for the chosen disease area, cache it
- [ ] Build the summarization + safety-check pass for anything destined for the Patient Portal
- [ ] Expose `/internal/enrichment/patient-summary`, wire to Team A's `/public/*` route
- [ ] Expose `/internal/enrichment/trial-context`, hand off to Team C
- [ ] (Stretch) Expose `/internal/enrichment/competitive-signal` for Portal 3
- [ ] Pre-fetch and lock the exact set of demo queries you'll need on stage — cache them explicitly so nothing live-fetches during the actual demo

## Dependencies

- You need Team A's normalized entity IDs to tag your cached content correctly — coordinate the disease-area/entity list together at hour 0, don't wait for their full pipeline.
- Team C (Portal 3 repurposing) and Team D (Patient Portal, Portal 2 UI) both consume your output — get a minimal real response flowing to them within the first 2–3 hours, even if the content set is small.

## Definition of done (committed scope)

- Patient-facing summaries are real, cited, cached, and have passed a safety check for unsourced clinical claims.
- Trial-context enrichment is available for at least the trials used in the live demo, pre-cached (not dependent on a live scrape during the demo).
- Every piece of enrichment content is traceable to a real source URL — no generated-sounding, uncited text anywhere in the pipeline.
