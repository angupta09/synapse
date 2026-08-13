# Synapse — Team B Enrichment Service

Bright Data enrichment for the Patient, Trial Design, and R&D portals.

## STATUS: LIVE AND WORKING ✅

- **16/16 smoke checks pass** against live Bright Data (both zones verified)
- **9/9 demo entries prefetched and PINNED** — the demo path needs zero live calls
- Verified clean: no bad URLs, no binary content, all safety gates passing

```bash
# start it
cd enrichment && python -m uvicorn app.main:app --port 8100
# docs at http://localhost:8100/docs
```

### One upgrade worth doing: turn on an LLM

Right now summarization runs in **extractive fallback** (verbatim source sentences).
It's safe and it works, but patient-facing prose reads choppy. Adding either of these
to `.env` makes summaries properly plain-language *and* enables a second LLM grounding
check on patient content:

- `ANTHROPIC_API_KEY=sk-...` — if anyone on the team has a key, or
- `USE_BEDROCK=true` — uses the AWS credentials from the event-provided account
  (run `aws configure` first; `boto3` is already installed)

Then re-run `python -m scripts.prefetch`. Nothing else changes.

---

## YOUR TASKS (in order)

> **Steps 1–2 and 4–5 are already DONE.** Credentials are in `.env`, both zones verified,
> demo data prefetched and pinned, server confirmed working. What's left for you:
> **step 3** (confirm the disease area with the team) and **step 6** (hand the API
> contract below to Teams C and D). Everything below is kept for reference / redoing.

### 1. Get Bright Data credentials — DONE ✅

Go straight to **https://brightdata.com/cp/web_access** — the nav item is **"Web Access APIs"**.

> If you're only seeing options to add a *proxy*, you're in the wrong section. Zone creation
> moved out of "Proxies & Scraping" — use the `/cp/web_access` URL above.

1. **Create a Web Unlocker zone.** Add → **Web Unlocker API** → name it (default assumed: `web_unlocker1`) → **Add API**.
2. **Create a SERP API zone.** Add → **SERP API** → name it (default assumed: `serp_api1`) → **Add API**.
3. **Get your API key + exact zone name.** Open each zone → **Overview** tab. Both are shown there.

> **If the button says "Add payment method" instead of "Add API":** that's identity
> verification for personal-email signups. It does not charge you. Complete it to unlock
> zone creation. Zone names cannot be renamed after creation — everything else can be edited.

Then fill in `.env` (already created for you from `.env.example`):

```
BRIGHTDATA_API_TOKEN=your_token_here
BRIGHTDATA_UNLOCKER_ZONE=web_unlocker1
BRIGHTDATA_SERP_ZONE=serp_api1
```

If your zone names differ from the defaults, update them here to match exactly.

**Optional but recommended:** add `ANTHROPIC_API_KEY` to `.env`. With it, summaries are written by Claude and a second LLM grounding check runs on patient content. Without it, the service falls back to extractive summarization (verbatim source sentences) — still works, still safe, just less polished prose.

### 2. Verify it works

```bash
python -m scripts.smoke_test
```

All 9 checks should pass once the token is in. (8/9 pass right now — only the token check fails.)

### 3. Lock the disease area with the team, then edit `demo_targets.json`

It's pre-filled with ALS as a placeholder. Replace with whatever the team locks in — you need the condition/treatment names, NCT IDs, and target names the demo will actually touch.

### 4. Pre-fetch and pin the demo data — DO THIS BEFORE DEMO TIME

```bash
python -m scripts.prefetch
```

This fetches every call the demo will make and **pins** it in cache so it never expires. After this, nothing in the demo path needs a live Bright Data call. This is the single most important thing you do — a live scrape stalling on stage is the most likely way this project visibly breaks.

### 5. Start the service and tell Teams C and D it's up

```bash
python -m uvicorn app.main:app --port 8100 --reload
```

Interactive API docs: http://localhost:8100/docs

### 6. Report any BLOCKED patient summaries to the team

If `prefetch` prints `[BLOCKED]` for a patient summary, the safety gate rejected it. That's the system working — but it means Team D has no content for that treatment. Either pick a different treatment or check whether the sources were too thin.

---

## What's already built (you don't need to touch this)

| File | What it does |
|---|---|
| `app/brightdata.py` | SERP API search + Web Unlocker scrape, HTML→text, `search_and_scrape` workhorse with snippet fallback |
| `app/cache.py` | SQLite cache with TTL + **pinning** (pinned entries never expire — demo safety) |
| `app/summarize.py` | Grounded summarizers for each portal; Claude when keyed, extractive fallback otherwise |
| `app/safety.py` | Patient-facing gate: 8 deterministic rules + optional LLM grounding check. **Fails closed.** |
| `app/enrichment.py` | The three enrichment pipelines |
| `app/main.py` | FastAPI service |
| `scripts/prefetch.py` | Pre-fetch + pin everything the demo touches |
| `scripts/smoke_test.py` | End-to-end verification |

---

## API contract — give this to Teams C and D

Base URL: `http://localhost:8100`

### `GET /internal/enrichment/patient-summary` → Team D (Patient Portal)

```
?condition_id=MONDO:0004976&treatment_id=RXCUI:1092422
&condition_name=Amyotrophic Lateral Sclerosis&treatment_name=Riluzole
```

```json
{
  "content": "plain-language summary, or empty string if blocked",
  "disclaimer": "This is public information...",
  "safety": { "passed": true, "checks_run": ["pattern","llm_grounding"], "violations": [] },
  "sources": [{"url": "...", "title": "..."}],
  "source_url": "...",
  "fetched_at": 1755100000.0,
  "cached": true
}
```

**Team D contract: if `safety.passed` is false, render nothing.** `content` will be empty. Do not fall back to raw text.

### `GET /internal/enrichment/trial-context` → Team C (Portal 2)

```
?nct_id=NCT03127267&trial_title=optional
```

Returns `content`, `has_context`, `sources[]`, `raw_excerpts[]` (excerpts let Team C's pattern analysis read source text directly rather than only the summary).

### `GET /internal/enrichment/competitive-signal` → Team C (Portal 3, stretch)

```
?target_id=HGNC:11179&target_name=SOD1
```

Returns `content`, `signal_count`, `items[]` with per-source excerpts.

### Ops

- `GET /health` — config state + cache stats
- `GET /internal/cache/stats`, `GET /internal/cache/entries?kind=`

---

## Design decisions worth defending to a judge

- **Fails closed on patient safety.** If a summary trips a rule or isn't source-backed, content is withheld — not softened. The Patient Portal shows nothing rather than something unverified.
- **Two-layer safety.** Deterministic regex rules always run (they work offline, can't fail open on a network error); the LLM grounding check is an additional layer, never the only one.
- **Nothing unsourced leaves this service.** Every response carries `source_url` + `fetched_at`. Content with no source URL is rejected by the gate.
- **Extractive fallback is verbatim source text**, so the no-LLM path structurally cannot invent a claim.
- **Pinned cache** means the demo path is guaranteed offline-safe once prefetched.
