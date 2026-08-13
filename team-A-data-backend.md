# Team A — Data & Backend Infrastructure Engineer

See [MASTER.md](MASTER.md) for full architecture and context.

## Your mission

You own the foundation everyone else builds on: pulling ClinicalTrials.gov and openFDA data, normalizing every drug/disease/target to a canonical ID, and standing up the storage layer (structured + vector) that Portals 1, 2, and 3 all read from. If your normalization layer is weak, every other team's "smart" feature quietly breaks or fakes it. This is the highest-leverage, least-glamorous role — treat it that way.

## Why this matters (don't skip this)

The original plan's biggest hidden risk was assuming drug/disease names would "just match" across sources. They won't — "Ozempic," "semaglutide," and a trial's free-text condition field are three different strings for overlapping concepts. Every feature downstream (repurposing matches, "similar trials," Patient Portal joins) depends on you resolving this once, correctly, up front.

## Responsibilities

1. **Ingestion**
   - ClinicalTrials.gov REST API v2 — pull studies for your team's chosen disease area(s). Use the API's field selection to keep payloads manageable; you need at minimum: NCT ID, condition(s), intervention(s), phase, status, `whyStopped`, enrollment count, eligibility criteria text, sponsor, locations.
   - openFDA — pull drug label + approval data relevant to the same disease area(s). This is close to static; one clean pull is enough.
   - Store every raw payload in S3 (or local disk if S3 setup is too slow to justify) before transforming anything — you want to be able to re-run normalization without re-fetching.

2. **Entity normalization**
   - Map every drug mention to a canonical ID (RxNorm or DrugBank ID — pick one and be consistent).
   - Map every disease/condition mention to a canonical ID (MONDO or MeSH ID).
   - Map every target/gene mention (from Convoke data, once Team C has it) to HGNC ID.
   - Build this as a small, testable function/service: `normalize_drug(text) -> {id, canonical_name, confidence}`, not inline scattered logic. Team C and D will call this directly for any user-entered free text.

3. **Storage layer**
   - Structured store (Postgres/Aurora): trials table, drug-label table, entity table, and a `provenance` join table (`derived_claim_id -> source_record_id[]`) — this provenance table is what makes every other team's outputs citable. Build it early; it's cheap now and expensive to retrofit at hour 7.
   - Vector index (pgvector is fine for one day): embed trial descriptions + eligibility criteria + drug mechanism text, so Team C can do semantic similarity search instead of keyword matching.

4. **API surface you expose to the rest of the team**
   - `GET /internal/trials?condition_id=&status=&phase=` — structured trial query
   - `GET /internal/drug-label?drug_id=` — approval/label data
   - `GET /internal/similar-trials?trial_id=&k=` — vector similarity lookup
   - `POST /internal/normalize` — `{type: "drug"|"disease"|"target", text}` → canonical ID
   - `GET /public/trials?condition_id=&status=recruiting` and `GET /public/drug-label?condition_id=` — the **safe, read-only subset** for the Patient Portal. This must be a genuinely separate route/service from the internal ones, not just a filtered parameter, per the architecture's safety boundary.

## Task checklist (priority order)

- [ ] Pick and lock the disease area(s) for the demo (coordinate with the whole team — do this first, together, before anyone writes code)
- [ ] Stand up Postgres (Aurora Serverless or local for dev) with the trials/labels/entities/provenance schema
- [ ] Write the ClinicalTrials.gov ingestion pull for the chosen disease area(s)
- [ ] Write the openFDA ingestion pull for the same disease area(s)
- [ ] Build `normalize_drug` / `normalize_disease` / `normalize_target` functions and expose as an internal service
- [ ] Backfill normalized IDs onto every ingested record
- [ ] Stand up pgvector, embed trial text + eligibility criteria
- [ ] Expose the `/internal/*` and `/public/*` API routes (stub with real data as soon as possible — don't leave the team on mocks past hour 2)
- [ ] Write the provenance table and make sure every query response includes source record IDs, not just derived text
- [ ] Smoke-test: can Team D's Patient Portal query actually return real, correct data end-to-end?

## Dependencies

- **You block everyone.** Get a minimal end-to-end slice (one disease area, real ClinicalTrials.gov + openFDA data, normalized, queryable) working within the first 2–3 hours, even if incomplete, so B/C/D aren't stuck on mocks.
- You depend on Team C for target/gene IDs once Convoke data comes in — coordinate on the HGNC mapping together rather than blocking.

## Definition of done (committed scope)

- Real ClinicalTrials.gov + openFDA data for the chosen disease area, normalized, stored, and queryable via both the internal and public API routes.
- Provenance is queryable: given any trial or label record returned, you can trace it back to its raw source payload.
- The public API route cannot return anything derived from Convoke data — verify this explicitly, don't just assume it.
