# Trial Sandbox — Stretch++ Layer for Synapse

**Biopharma Hack Day, AWS Builder Loft, San Francisco — Aug 13, 2026**
**Status: stretch++, feeds Synapse's R&D Portal (Portal 3) — see [MASTER.md](MASTER.md)**

---

## 1. The idea, in one paragraph

An **AI-agent sandbox that simulates how a drug and a patient interact before a real trial ever runs.**
You spin up a "Drug Agent" (built from real pharmacology data) and a "Patient Agent" (built from a real, non-identifying genetic profile). They interact inside the sandbox while a "Safety Agent" watches, reasons out loud, and flags risks or benefits — every claim backed by a live-pulled real source, never a guess. Run it against a disease with few existing treatments, and it also tells you *which existing drug might newly work there*. Run it against a real historical trial that already failed, and it retroactively tells you *whether it would have caught the problem in advance*.

It's not a replacement for real clinical trials. It's a fast, honest, explainable screening tool — a flight simulator for drug-patient interactions, not a real airplane.

---

## 2. In plain English (layman's version)

Imagine two characters in a video game: one is "the Drug," the other is "the Patient." The Drug character knows everything real about that medicine — how the body breaks it down, what it's supposed to do, what it's known to clash with. The Patient character isn't a made-up person — their genes come from a real (anonymous, public) genetic sample, run through Amazon's genetics tools, so we actually know things like "this simulated patient's body processes drugs slowly," which is a real, medically recognized fact about some people.

We let the two characters "meet" inside the sandbox. A third character, a "Safety Doctor" AI, watches what happens and explains, in plain language, whether this looks risky or promising — and for every warning it gives, it goes and finds a real medical article, report, or past case on the internet to back itself up, so it's never just making things up.

On top of that: there are diseases that barely have any treatments being worked on, even though they're common and serious. Our system can also scan for existing drugs that might secretly work on those neglected diseases, using a private industry database most people don't have access to. And to prove the whole system actually works, we run it against real drug trials from the past that we already know failed — and show, live, that our sandbox would have caught the same problem before it happened.

It's like a flight simulator for testing a drug on a patient — useful for catching problems early and generating good ideas, not a substitute for the real, regulated clinical trial process.

---

## 3. Why this, and why now — the market gap

### Gap A — Two worlds that have never been merged
- **World 1 (real, trusted, rigid):** Tools like Certara's Simcyp are the actual industry standard — used in 110+ FDA drug approvals — but they're closed, mechanistic simulators built over 20 years. You can't quickly improvise a new "what if" scenario with them.
- **World 2 (flexible, new, ungrounded):** In 2026, the first research papers appeared describing LLM agents that role-play as "drug" and "patient" to reason about interactions. This is brand new, genuinely promising — and currently pure academic research, with no product, and no connection to real-world evidence (it can hallucinate).
- **Nobody has combined them.** That's the opening: real pharmacology + real genomics + agentic reasoning + live evidence-grounding, in one interactive tool.

### Gap B — No one benchmarks the agents themselves
Existing pharma "benchmarks" (Therapeutics Data Commons, WelQrate, etc.) score whether a model can predict a molecule's property in isolation — not whether an AI reasoning system can predict what actually happens when a real drug meets a real patient population. That end-to-end question is unaddressed. We answer it as a side effect of the sandbox: replay real historical trial outcomes through it and show it agreeing (or disagreeing) with what really happened.

### Gap C — Repurposing is manual and slow
Finding a new use for an existing, already-safety-tested drug is one of the fastest, cheapest ways to help patients with neglected diseases — but today it relies on individual scientists' intuition and personal knowledge of the literature, not systematic search across the full landscape of diseases and drugs. A proprietary dataset (Convoke's unmet-needs index + pipeline database) makes this searchable and rankable, which nobody outside their paying customers currently has access to.

### Why this is the right hackathon build, specifically
- It directly prototypes **Convoke's own publicly stated long-term mission** — "autonomously guide new drugs from an idea through testing" — as a small, working, one-day proof, not a slide.
- It uses **AWS HealthOmics** for exactly what AWS built a dedicated workshop to teach at this event: real genomic variant annotation, not a decorative Bedrock call.
- It uses **BrightData** as a live grounding layer the way their own roadmap describes their agentic use case: real-time evidence retrieval for AI agents, not one throwaway scrape.
- It stays honest about its limits (screening tool, not a regulatory-grade simulator), which is a credibility signal, not a weakness — judges with real pharma background will notice the difference between a team that oversells and a team that knows exactly where the line is.

---

## 4. Architecture

```
                         ┌─────────────────────────────┐
                         │   1. HYPOTHESIS ENGINE       │
                         │   (Convoke MCP)               │
                         │  Unmet-needs index ×          │
                         │  pipeline/target data          │
                         │  → ranked drug↔disease         │
                         │    repurposing candidates      │
                         └──────────────┬───────────────┘
                                        │  candidate drug + target disease
                                        ▼
        ┌───────────────────────────────────────────────────────────┐
        │                     2. THE SANDBOX                         │
        │                                                             │
        │   ┌───────────────┐        ┌────────────────────────────┐  │
        │   │  DRUG AGENT   │        │      PATIENT AGENT          │  │
        │   │  mechanism,   │◄──────►│  built from a real (public, │  │
        │   │  metabolism,  │  react │  synthetic-labeled) VCF      │  │
        │   │  known        │        │  genomic file → processed   │  │
        │   │  interactions │        │  via AWS HealthOmics →      │  │
        │   │  (DrugBank /  │        │  annotated vs ClinVar/CPIC  │  │
        │   │  openFDA/     │        │  → real metabolizer status, │  │
        │   │  DDInter)     │        │  comorbidity profile        │  │
        │   └───────┬───────┘        └───────────────┬────────────┘  │
        │           │                                 │               │
        │           └───────────────┬─────────────────┘               │
        │                           ▼                                 │
        │                ┌─────────────────────┐                      │
        │                │   SAFETY / MODERATOR │                      │
        │                │   AGENT               │                      │
        │                │  reasons over the      │                      │
        │                │  interaction, flags     │                      │
        │                │  risks/benefits          │                      │
        │                └──────────┬─────────────┘                      │
        │                           │ claim needing evidence               │
        │                           ▼                                     │
        │                ┌─────────────────────┐                      │
        │                │  3. GROUNDING LAYER   │                      │
        │                │  (BrightData MCP)      │                      │
        │                │  live-pulled PubMed,    │                      │
        │                │  FDA adverse events,     │                      │
        │                │  case reports, news       │                      │
        │                └──────────┬─────────────┘                      │
        └───────────────────────────┼──────────────────────────────────┘
                                     ▼
                     ┌─────────────────────────────────┐
                     │  4. OUTPUT REPORT                 │
                     │  - risk/efficacy plausibility      │
                     │  - every claim cited to a source    │
                     │  - "trial design" recommendations    │
                     └────────────────┬────────────────┘
                                      ▼
                     ┌─────────────────────────────────┐
                     │  5. RETROSPECTIVE BENCHMARK        │
                     │  Replay real past trials             │
                     │  (ClinicalTrials.gov / AACT,          │
                     │  known outcome) through the            │
                     │  sandbox → "would we have caught        │
                     │  this failure in advance?"               │
                     └─────────────────────────────────┘
```

### Component detail

| Component | Sponsor tool | Real data source | What it proves |
|---|---|---|---|
| Hypothesis Engine | Convoke MCP | Unmet-needs index, pipeline/target data | Finds drug-disease repurposing candidates nobody's tested |
| Drug Agent | — | DrugBank, openFDA, DDInter | Grounded pharmacology, not invented |
| Patient Agent | AWS HealthOmics | Public/synthetic VCF + ClinVar + CPIC | Real pharmacogenomic metabolizer status |
| Safety/Moderator Agent | Bedrock agent orchestration | — | Explainable reasoning trace |
| Grounding Layer | BrightData MCP | PubMed, openFDA adverse events, case reports | Every claim cited, not hallucinated |
| Retrospective Benchmark | — | ClinicalTrials.gov / AACT historical outcomes | Proof the system isn't just plausible-sounding — it's checked against reality |

---

## 5. Build plan (single day, team split into 3 tracks)

**Track A — Data & Hypothesis Engine (Convoke)**
1. Connect to Convoke MCP, pull unmet-needs index + pipeline data.
2. Build the scoring/ranking logic for drug↔disease repurposing candidates.
3. Output: a short ranked list with a chosen candidate for the live demo.

**Track B — Sandbox Core (Drug Agent + Patient Agent + Safety Agent)**
1. Drug Agent: pull structured pharmacology data for the chosen candidate drug (DrugBank/openFDA/DDInter).
2. Patient Agent: pick a public sample VCF (e.g., 1000 Genomes or similar open dataset), run through AWS HealthOmics, annotate against ClinVar/CPIC for pharmacogenomic markers relevant to the drug's metabolism pathway.
3. Build the multi-agent reasoning loop (Bedrock agents or equivalent orchestration) — Drug Agent + Patient Agent "interact," Safety Agent reasons and flags.
4. Output: structured risk/efficacy report with reasoning trace.

**Track C — Grounding + Benchmark + Demo**
1. Wire BrightData MCP into the Safety Agent so every flagged claim triggers a live evidence search, and results get attached as citations.
2. Pull 1-2 real historical trials with known negative outcomes (ClinicalTrials.gov/AACT) that match the demo's drug class or mechanism.
3. Replay them through the sandbox; prepare the "would we have caught it" comparison as the closing beat of the live demo.
4. Assemble demo script: Hypothesis → Sandbox interaction (live) → cited risk report → historical replay proof.

**Data & rules reminder:** no real patient/PHI data anywhere — only public, synthetic-labeled genomic samples and synthesized/de-identified inputs, per the event's stated data policy.

---

## 6. Why this wins

| Prize angle | Why this product earns it |
|---|---|
| Best overall | Only team with a working, explainable, evidence-grounded multi-agent system spanning hypothesis generation → simulation → validation |
| Best use of Convoke | Repurposing engine is structurally impossible without their proprietary unmet-needs/pipeline data |
| Best use of BrightData | Live, cited, multi-source evidence grounding is core to the product, not a bolt-on |
| Best use of AWS | Direct, substantive use of AWS HealthOmics — the exact service AWS built a dedicated workshop for at this event — plus Bedrock agent orchestration |
| Technical / impact | Honest positioning (screening tool, not a regulatory replacement) reads as credible to judges with real pharma background, not overhyped |
