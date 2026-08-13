# Team C — AI / Agent & Reasoning Engineer

**Project: Synapse** · See [MASTER.md](MASTER.md) for full architecture and context.

## Your mission

You turn Team A's normalized data and Team B's enrichment content into the two things this product is actually selling: (1) a credible answer to "why do trials like this fail, and what should we watch for," and (2) — stretch — a credible, cited repurposing hypothesis. "Credible" means every output is traceable to specific source records, built through an explicit multi-step pipeline, never a single freeform prompt asking an LLM to "be smart."

## Why this matters (don't skip this)

A judge with real pharma background will ask "where did that come from" about any interesting claim you show. If the honest answer is "the LLM said so," the product loses credibility instantly — this is the difference between a toy and a real tool. Every pipeline you build must keep evidence attached to its output, not just produce fluent-sounding text.

## Responsibilities

### 1. Trial Design Portal — pattern analysis (Portal 2, committed)

- Pull terminated/withdrawn trials in the chosen disease area from Team A's API, read the `whyStopped` field.
- Cluster/bucket failure reasons (recruitment failure, safety signal, futility, funding, other) — a simple rule-based or LLM-assisted classification is fine; don't over-engineer this.
- For each failure cluster, extract the design parameters that correlate with it (sample size, arm count, endpoint type, eligibility criteria complexity, phase) — compare against design parameters of trials in the same area that succeeded.
- Build a scoring function: given a new/hypothetical trial design, flag which historical failure pattern(s) it resembles and why, citing the specific past trials (by NCT ID) that inform the flag.
- Use Team B's trial-context enrichment (sponsor/investigator/press content) to add color/explanation beyond the bare structured fields where it strengthens the "why."

### 2. R&D Portal — repurposing engine (Portal 3, stretch)

Build this as an explicit pipeline, not one prompt:

1. **Candidate generation** — structured similarity: find drugs sharing a target/mechanism with the drug in question (via Team A's normalized target IDs), plus semantic similarity over mechanism-of-action text (via Team A's vector index).
2. **Evidence retrieval** — for each candidate, pull supporting evidence: Convoke's unmet-needs/pipeline data (does the target disease have low pipeline activity and high burden?), Team B's competitive-signal enrichment, and literature/evidence via Bright Data.
3. **Confidence scoring** — score each candidate based on evidence strength/count (e.g., number of independent corroborating sources, phase reached by analogous drugs on the same target). Don't hide the scoring logic — surface it, it's part of the credibility story.
4. **Brief generation** — only at this final step does an LLM write the human-readable summary, and it must write strictly from the retrieved evidence passed into its context, not from its own training-data memory. Every sentence in the brief should be attributable to a specific retrieved item.

### 3. Convoke MCP integration

- You own the Convoke MCP connection. Pull the unmet-needs index (disease burden, prevalence, pipeline activity, treatment burden) and pipeline/target data for the chosen disease area.
- This data feeds your repurposing pipeline (step 1–2 above) and is explicitly restricted to Portals 2/3 — never let it reach the Patient Portal's data path (Team A enforces the route separation; you enforce it by simply never wiring Convoke data into anything Team D marks as patient-facing).

### 4. Patient-facing safety pass (support role)

- If Team D needs an LLM to rewrite Team A/B content into plain language for the Patient Portal, you own or co-own that rewriting step and its guardrail check (Bedrock Guardrails or an equivalent prompt-based check) — the rewrite must not introduce claims beyond what the source content says.

## API surface you expose to the rest of the team

- `GET /internal/trial-risk-analysis?trial_design=` — returns flagged risk patterns with cited historical trial IDs and rationale
- `GET /internal/repurposing-candidates?drug_id=` or `?disease_id=` — returns ranked candidates with confidence scores and evidence citations (stretch)
- `POST /internal/patient-safe-rewrite` — takes source content, returns plain-language text + pass/fail from the safety guardrail (support role for Team D)

## Task checklist (priority order)

- [ ] Confirm disease area with the team (same as A/B)
- [ ] Get read access to Team A's trial data (including `whyStopped`) as early as possible
- [ ] Build the failure-clustering + design-parameter comparison for Portal 2, get one real, correct example working end-to-end
- [ ] Expose `/internal/trial-risk-analysis`, hand to Team D
- [ ] Set up Convoke MCP connection, pull unmet-needs + pipeline data for the disease area
- [ ] (Stretch) Build the 4-step repurposing pipeline, get one real candidate with real citations working end-to-end before generalizing
- [ ] (Stretch) Expose `/internal/repurposing-candidates`, hand to Team D
- [ ] Support Team D on the patient-safe-rewrite guardrail pass

## Dependencies

- You are blocked on Team A's normalized data and Team B's enrichment feeds — coordinate early to get a minimal real slice from each within the first 2–3 hours rather than waiting for their "finished" versions.
- Team D consumes your output directly for Portal 2 (committed) and Portal 3 (stretch) — get something real flowing to them well before the final hours so UI integration isn't rushed.

## Definition of done (committed scope)

- Portal 2's risk-analysis output, for the chosen disease area, is built from real historical trial data, cites specific past trials by ID, and the correlation logic is explainable in one sentence if a judge asks "how did you compute that."
- No Convoke-derived content has any path into the Patient Portal — verify this explicitly with Team A.
