# Team D — Frontend & Product Engineer

See [MASTER.md](MASTER.md) for full architecture and context.

## Your mission

You build all three portals' UI, own the overall product feel, and own the demo itself — script, rehearsal, and the fallback plan if something breaks live. You're also the team's product conscience: if a feature is technically impressive but confusing to a judge in 15 seconds, it's your job to simplify it or cut it.

## Why this matters (don't skip this)

Judges see the UI, not the architecture doc. A technically excellent backend with a confusing or slow-feeling frontend loses to a simpler product that's obviously polished. Your job is to make Team A/B/C's real, cited, hard-won data feel effortless and trustworthy at a glance.

## Responsibilities

### 1. Patient Portal (Goal 1, committed)

- **Search flow:** condition dropdown/free-text + location → "Find Available Options" button.
- **Results table:** columns for Treatment Option (approved drug / not-yet-started trial / ongoing trial), Status label (Approved / Currently accepting / Not started), Phase, Study number, Location.
- **Detail popup:** plain-English summary (from Team B's vetted content), contact options for the study, other patient-facing details.
- Data comes exclusively from Team A's `/public/*` routes and Team B's `patient-summary` enrichment — never call an internal/Convoke-touched endpoint from this portal, even for convenience. This boundary is a product requirement, not just a backend one.
- Tone matters here: plain language, no unexplained jargon, calm and clear — this is the portal a real patient or caregiver might actually read.

### 2. Trial Design Portal (Goal 2, committed)

- Input: a disease area or a hypothetical trial design (sample size, phase, endpoint type, eligibility criteria).
- Output: Team C's risk-analysis result — flagged failure patterns, cited historical trials, and the "trials shaped like this failed for X reason Y% of the time" framing from MASTER.md section 2.5.
- Make the citations clickable/visible — this is the credibility feature, don't bury it in a tooltip.

### 3. R&D Portal (Goal 3, stretch)

Five blocks, in priority order if time is short (build 1 and 3 first — they're the highest-impact, most demoable blocks; 2, 4, 5 are enhancements):

1. **Search + Opportunity Summary** — enter a drug/target/pathway/disease, get a compact brief.
2. Target-Indication Landscape (visual map) — nice-to-have, cut first if time is short.
3. **Repurposing Opportunity Panel** — the strongest, most demoable feature. Show the candidate, confidence score, and evidence trail from Team C clearly.
4. Competitive Intelligence Feed — nice-to-have.
5. Risk / Gaps / Next Actions — nice-to-have; if the stretch++ simulation layer (see IDEA.md) gets built, its output slots in here.

### 4. Demo assembly

- Own the demo script (draft in MASTER.md section 7) — refine it with the team once real data is flowing.
- **Lock one disease area for the entire demo, in advance.** Never let judges pick a random condition live.
- Prepare a fallback: screenshots or a screen recording of the working flow, in case live network/API calls fail on stage. This is not pessimism, it's standard hackathon practice — the team that can't demo live because Wi-Fi died loses to the team with a 30-second backup video.

## Task checklist (priority order)

- [ ] Confirm disease area with the team
- [ ] Scaffold the Next.js app with 3 route groups (patient / trial-design / rd), shared design system/components
- [ ] Build Patient Portal UI against Team A's stub API (don't wait for final data)
- [ ] Build Trial Design Portal UI against Team C's stub output
- [ ] Swap stubs for real data as Teams A/B/C land their pieces (continuous integration, not a big-bang merge at the end)
- [ ] Verify the Patient Portal literally cannot reach any Convoke/internal-only data path
- [ ] (Stretch) Build the Repurposing Opportunity Panel first, other Portal 3 blocks only if time allows
- [ ] Write and rehearse the demo script with the team
- [ ] Record a fallback video/screenshot walkthrough of the full working flow
- [ ] Final visual pass: make sure citations/sources are visibly surfaced everywhere, not hidden — that's the product's actual differentiator

## Dependencies

- You depend on all three other roles, but should never be blocked by them: insist on a stubbed/mocked API contract from each within the first hour so you can build UI in parallel and swap in real data as it lands.
- You own the final go/no-go call on cutting Portal 3 or the simulation layer if the committed portals (1 and 2) aren't rock-solid by hour 7 — protect the committed scope over the stretch scope.

## Definition of done (committed scope)

- Patient Portal and Trial Design Portal both work end-to-end on real (not mocked) data, for the chosen disease area, live, without needing a network call to complete during the demo (pre-fetch/cache anything slow).
- A fallback recording exists in case live demo fails.
- Every piece of derived/AI-generated content visible in the UI has a visible source citation next to it.
