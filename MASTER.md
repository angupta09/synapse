# Synapse — Master Plan

**Biopharma Hack Day, AWS Builder Loft, San Francisco — Aug 13, 2026**
**Team size: 4** · **Sponsors leveraged: Bright Data, Convoke, AWS**

---

## 0. Product name: Synapse

**Selected.** Synapse — the connection point between neurons — maps onto the product's actual job: connecting patients, trial designers, and researchers to the same underlying evidence spine. Short, one word, biological without being generic ("BioX," "PharmaY"), and easy to say fast in a live demo.

**Naming rationale to reuse in the pitch:** "A synapse is where information crosses from one part of a system to another without getting lost or distorted. That's exactly what this platform does with biopharma data — one evidence spine, faithfully connected across three very different audiences: patients, trial designers, and researchers."

---

## 1. Product summary

A clinical-trial intelligence platform with three audiences sharing one evidence-grounded data spine:

1. **Patient Portal** (committed) — "What are my options?" Approved drugs + open trials, plain-language, safe sources only.
2. **Clinical Trial Design Portal** (committed) — "How do we design a better trial?" Learn from why past trials failed/succeeded.
3. **R&D / Repurposing Portal** (stretch) — "What should we work on next?" Opportunity-mapping across targets, diseases, and competitors.
4. **Simulation Layer** (stretch++, from [IDEA.md](IDEA.md)) — once Portal 3 surfaces a repurposing candidate, optionally run it through the multi-agent Drug×Patient sandbox (real pharmacogenomics via AWS HealthOmics + live evidence via Bright Data) for a deeper "why this might work, what could go wrong" simulation. This feeds directly into Portal 3's "Risk / Gaps / Next Actions" block. Only attempt after 1–3 are demo-solid.

**Build priority is strict:** 1 → 2 → 3 → 4. Do not start 3 until 1 and 2 are demoable end-to-end. Do not start 4 unless 3 is already working.

---

## 2. Architectural review — what the original plan got right, and what it was missing

### What was already right
- Correctly identified ClinicalTrials.gov + openFDA as the structured backbone and Bright Data as the "unstructured context" layer — that's the correct division of labor.
- Correctly identified that Convoke-style speculative reasoning must **never** reach the Patient Portal directly. That instinct is right; it just needed to become an enforced architectural boundary, not just a rule on a page.

### What was missing — the fundamentals that make this work reliably instead of demo-only

**1. Entity normalization (the single most important missing piece).**
ClinicalTrials.gov, openFDA, and Bright Data each refer to the same drug or disease with different free-text strings ("Ozempic" vs "semaglutide" vs "NN9536"). Without a normalization layer, every join between sources ("show approved drugs AND open trials for this condition," "find drugs hitting the same target") silently breaks or under-matches. Fix: map every drug to **RxNorm/DrugBank ID**, every disease to a **MONDO/MeSH ID**, every target/gene to **HGNC ID**, at ingestion time, before anything is stored. This one decision determines whether Portal 3's "similar drugs hitting similar targets" feature actually works or just looks plausible in a rehearsed demo.

**2. Provenance as a first-class data field, not an afterthought.**
Every derived statement (a repurposing hypothesis, a "why trials like this fail" pattern, a plain-language summary) must carry a structured citation back to its source record — not a paragraph that mentions a source, an actual `source_ids: []` field joined to the record it came from. This is what makes the product defensible in front of judges with real pharma backgrounds, and it's cheap to build if designed in from the start (expensive to retrofit the night before demo).

**3. A real safety boundary for the Patient Portal, not just a policy note.**
"Don't expose Convoke reasoning to patients" is correct but needs to be an actual service boundary: the Patient Portal calls a **separate, read-only API** that only touches openFDA + ClinicalTrials.gov + pre-vetted Bright Data summaries. It should physically be unable to call the Convoke/repurposing reasoning path. Put a content-safety pass (Bedrock Guardrails or equivalent) on anything patient-facing that was touched by an LLM, since plain-language rewriting can introduce clinical-sounding claims by accident.

**4. Freshness and caching strategy per source, because they behave differently.**
- ClinicalTrials.gov REST API v2 — supports incremental pulls; poll on a schedule, don't scrape per-request.
- openFDA — near-static reference data; pull once, cache hard.
- Bright Data — expensive and slow per live call; cache with a TTL (hours, not seconds) and pre-fetch for your demo condition/drug before you're on stage. Never make the live demo depend on a cold Bright Data call finishing in real time.

**5. A concrete method for "learning from past trial failures" (Portal 2), not just a description of the goal.**
ClinicalTrials.gov records include structured status (`Terminated`, `Withdrawn`, `Completed`) and — critically — a `whyStopped` free-text field. Concrete approach: pull all terminated/withdrawn trials in the target disease area, cluster `whyStopped` reasons (recruitment failure, safety signal, futility, funding), and compare the new candidate trial's design parameters (sample size, arm count, endpoint type, eligibility criteria complexity, phase) against the design parameters of trials that failed for each reason. Output: "trials shaped like this one failed for X reason Y% of the time — here's what differed in the trials that succeeded." That's a real, demoable analytical result, not a vibe.

**6. Similarity search needs embeddings, not keyword matching.**
"Drugs hitting similar targets," "adjacent diseases with similar biology," "similar past trials" all require semantic similarity over free text (mechanism descriptions, eligibility criteria, trial descriptions) plus structured similarity (shared target ID, shared MoA class). Use a vector index (OpenSearch k-NN or pgvector) alongside the structured joins — structured-only matching will miss the useful, non-obvious hits.

**7. Agent orchestration for Portal 3 needs an explicit pipeline, not one big prompt.**
The Repurposing Opportunity Panel's output ("Drug X may work in Disease Y because...") is only credible if it's built from a traceable multi-step pipeline: candidate generation (structured target/MoA similarity) → evidence retrieval (Bright Data + PubMed for each candidate) → confidence scoring (based on evidence strength/count) → brief generation (LLM writes the summary from the retrieved evidence, not from its own memory). One big "ask an LLM for repurposing ideas" prompt will hallucinate and won't survive a judge asking "where did that come from."

---

## 3. Revised architecture

```
                         ┌────────────────────────────────────────────┐
                         │             INGESTION LAYER                 │
                         │  scheduled pulls, not live-per-request       │
                         ├────────────────┬─────────────┬─────────────┤
                         │ ClinicalTrials  │  openFDA     │  Bright Data │
                         │ .gov REST v2    │  drug label/  │  scrape jobs │
                         │ (daily poll)    │  approval     │  (cached,    │
                         │                 │  (static      │  TTL'd, pre- │
                         │                 │  pull)        │  fetched for │
                         │                 │               │  demo path)  │
                         └────────┬────────┴──────┬───────┴──────┬──────┘
                                  ▼                ▼              ▼
                         ┌────────────────────────────────────────────┐
                         │          NORMALIZATION LAYER                 │
                         │  drug → RxNorm/DrugBank ID                   │
                         │  disease → MONDO/MeSH ID                     │
                         │  target/gene → HGNC ID                       │
                         │  every record gets a canonical entity ID      │
                         └────────────────────┬───────────────────────┘
                                              ▼
                 ┌───────────────────────────────────────────────────────┐
                 │                    STORAGE LAYER                        │
                 │  structured store (Postgres/Aurora): trials, labels,     │
                 │    entities, provenance links                            │
                 │  vector index (pgvector/OpenSearch): embeddings of        │
                 │    trial text, eligibility criteria, MoA descriptions      │
                 │  object store (S3): raw source payloads, cached scrapes    │
                 └───────────────────┬───────────────────┬─────────────────┘
                                     ▼                   ▼
        ┌────────────────────────────────┐   ┌─────────────────────────────────┐
        │   SAFE / PUBLIC API              │   │   INTERNAL REASONING API          │
        │   (Patient Portal only)          │   │   (Portals 2 & 3 only)             │
        │   - openFDA + CT.gov + vetted     │   │   - pattern analysis (Portal 2)     │
        │     Bright Data summaries only     │   │   - Convoke MCP (unmet-needs,        │
        │   - Bedrock Guardrails pass on      │   │     pipeline data)                    │
        │     any LLM-touched text            │   │   - repurposing agent pipeline         │
        │   - CANNOT call Convoke/            │   │     (candidate gen → evidence           │
        │     repurposing path                │   │     retrieval → scoring → brief)         │
        └────────────────┬─────────────────┘   └────────────────┬─────────────────┘
                         ▼                                       ▼
              ┌────────────────────┐                  ┌────────────────────────┐
              │  Portal 1: Patient  │                  │  Portal 2: Trial Design  │
              │  Portal             │                  │  Portal                   │
              └────────────────────┘                  └────────────────────────┘
                                                                    ▼
                                                        ┌────────────────────────┐
                                                        │  Portal 3: R&D /          │
                                                        │  Repurposing Portal        │
                                                        │  (stretch)                  │
                                                        └───────────┬────────────┘
                                                                    ▼ (stretch++)
                                                        ┌────────────────────────┐
                                                        │  Simulation Sandbox        │
                                                        │  (Drug×Patient agents,      │
                                                        │  AWS HealthOmics genomics,    │
                                                        │  see IDEA.md)                  │
                                                        └────────────────────────┘
```

### Tech stack (AWS-native, serverless-first — minimizes ops during a one-day build)

| Layer | Tool |
|---|---|
| Ingestion / scheduled pulls | Lambda + EventBridge schedules |
| Orchestration (multi-step agent pipelines) | Step Functions or a lightweight LangGraph-style orchestrator in a single service |
| Structured storage | Aurora Serverless (Postgres) or RDS Postgres |
| Vector search | pgvector on the same Postgres instance (simplest for one day) — OpenSearch only if time allows |
| Object storage | S3 (raw payloads, cached Bright Data results) |
| LLM / agents | Amazon Bedrock (Claude models), Bedrock Guardrails for the patient-safety pass |
| API layer | API Gateway + Lambda, split explicitly into `/public/*` (Patient Portal) and `/internal/*` (Portals 2/3) |
| Frontend | Next.js (3 route groups, one per portal), deployed via Amplify or a simple static host |
| Genomics (stretch++ only) | AWS HealthOmics + ClinVar/CPIC annotation |

---

## 4. Data sources — locked list

| Source | Used by | Notes |
|---|---|---|
| ClinicalTrials.gov REST API v2 | All portals | Structured backbone. Note `whyStopped`, `phase`, `enrollmentCount`, `eligibilityCriteria` fields — these are the fields Portal 2's pattern analysis runs on. |
| openFDA (drug labels + approvals) | Patient Portal, Portal 2 | Static reference; frame as public-information, not a clinical decision engine (per FDA's own caveat). |
| Bright Data | All portals, differently | Patient Portal: only pre-vetted plain-language summaries. Portal 2: sponsor/investigator/conference/press context. Portal 3: competitive intelligence feed. |
| Convoke MCP | Portals 2 & 3 only, never Patient Portal | Unmet-needs index + pipeline/target data for the repurposing engine. |
| AWS HealthOmics + ClinVar/CPIC | Stretch++ simulation layer only | See IDEA.md. |

---

## 5. Team split (4 people)

| Person | Role | Doc |
|---|---|---|
| A | Data & Backend Infrastructure Engineer | [team-A-data-backend.md](team-A-data-backend.md) |
| B | Enrichment & Bright Data Engineer | [team-B-enrichment-brightdata.md](team-B-enrichment-brightdata.md) |
| C | AI/Agent & Reasoning Engineer | [team-C-ai-reasoning.md](team-C-ai-reasoning.md) |
| D | Frontend & Product Engineer | [team-D-frontend-product.md](team-D-frontend-product.md) |

**Dependency order:** A's normalized data + storage schema unblocks everyone. B's enrichment pipeline feeds C (Portal 3 evidence) and D (Patient Portal summaries, Portal 2 context). C's reasoning outputs feed D's Portal 2/3 UI. D integrates continuously rather than waiting for a "final" handoff — each person should expose a working stub/mock of their API within the first 90 minutes so nobody blocks on anybody past hour 2.

---

## 6. Build timeline (rough, 1-day event)

| Time | Milestone |
|---|---|
| Hour 0–1 | Confirm name, finalize entity schema (A), stub all 4 APIs with mock data so integration isn't blocked later |
| Hour 1–3 | A: ingestion + normalization live for 1 disease area. B: Bright Data pipeline live for the same disease area, cached. D: Patient Portal UI wired to real (or stub) API. |
| Hour 3–5 | C: Portal 2 pattern-analysis pipeline working end-to-end for the same disease area. D: Portal 2 UI wired. |
| Lunch | — |
| Hour 5–7 | Portal 1 + 2 fully demoable end-to-end, real data, no mocks left. This is the "committed" bar — protect it. |
| Hour 7–8.5 | If on schedule: Portal 3 (stretch). Candidate generation + repurposing panel for the chosen disease area only, not general-purpose. |
| Hour 8.5–9.5 | If still ahead: Simulation layer (stretch++) for one hero example only. |
| Final hour | Freeze features. Rehearse demo script against real (not live-fetched) data paths. Prepare fallback screenshots/recording in case of live-demo failure. |

**Hard rule:** never let a stretch goal put the committed goals at risk. If Portal 3 isn't solid by hour 7, drop it and polish Portals 1–2 instead — a flawless 2-portal demo beats a shaky 3-portal one.

---

## 7. Demo script (draft)

1. **Open on the Patient Portal** — pick a real rare-disease example, show approved drugs + open trials + a plain-language popup with a citation. Emotional hook, easy for any judge to understand instantly.
2. **Switch to the Trial Design Portal** — same disease area, show a past trial that failed and why, then show the design-pattern comparison flagging the same risk in a hypothetical new trial design. This is your "we learned something real from data" beat.
3. **(If built) Switch to the R&D Portal** — same disease area, show a repurposing candidate with its confidence score and cited evidence trail.
4. **(If built) Close on the Simulation layer** — the same repurposing candidate, run through the Drug×Patient sandbox, cited risk flag, replayed against a real historical trial outcome for the "would we have caught this" proof.
5. **Close** with the one-line pitch: one evidence-grounded data spine, three audiences, from "what are my options" to "what should we build next" — with every claim traceable to a real source.

Use **one disease area for the entire demo, prepared in advance** — this is the single highest-leverage decision for a smooth demo. Don't let the audience or judges pick a random condition live; pre-select something with clean data in all sources (ClinicalTrials.gov has good coverage, openFDA has an approved drug, Bright Data has real news/investigator content, and — if doing the stretch — has at least one historically failed trial with a documented `whyStopped` reason).

---

## 8. Related documents

- [IDEA.md](IDEA.md) — the multi-agent Drug×Patient simulation sandbox, now scoped as the stretch++ layer feeding Portal 3.
- [team-A-data-backend.md](team-A-data-backend.md)
- [team-B-enrichment-brightdata.md](team-B-enrichment-brightdata.md)
- [team-C-ai-reasoning.md](team-C-ai-reasoning.md)
- [team-D-frontend-product.md](team-D-frontend-product.md)
