# Synapse — Integration Brief

Read this before merging anything. It records what is actually on each branch as
of the Team B push, and the specific collisions a naive merge will hit.

## Branch inventory (verified, not assumed)

| Branch | Owns | Layout | Port |
|---|---|---|---|
| `teama-data-backend` | Data + storage + normalization | **root** `app/`, `sql/`, `scripts/`, `tests/`, `docker-compose.yml` | 8000 (FastAPI default) |
| `feat/team-b-enrichment` | Bright Data enrichment | `enrichment/` | **8100** |
| `teamc-risk-analysis` | Trial risk analysis | `teamc/` | **8100** (collides) |
| `trial-risk-engine` | **Identical to `teamc-risk-analysis`** (same SHA `975f019`) | `teamc/` | — |
| `frontend` | All 3 portal UIs (FastAPI + Jinja templates) | **root** `app/`, `test_boundary.py` | 8080 |

`origin/HEAD` currently points at `teamc-risk-analysis`.

## Collisions to resolve

### 1. Root-path collision (blocking)
`teama-data-backend` and `frontend` **both** put code at root `app/`, and both ship
their own root `requirements.txt`, `README.md`, `.gitignore`. Merging both into one
branch produces direct file-level conflicts.

**Fix:** move each into its own directory before merging — `backend/` for Team A,
`frontend/` for Team D. Team B (`enrichment/`) and Team C (`teamc/`) are already
namespaced and merge cleanly.

Target layout:
```
backend/      <- teama-data-backend, moved from root
enrichment/   <- team B, already correct
teamc/        <- team C, already correct
frontend/     <- frontend branch, moved from root
*.md          <- planning docs (Team B branch)
```

### 2. Port collision (blocking)
Team B and Team C both default to **8100**. Assign:

| Service | Port |
|---|---|
| Team A backend | 8000 |
| Team B enrichment | 8100 |
| Team C risk | 8200 |
| Frontend | 8080 |

### 3. API contract mismatches (blocking — the frontend will 404 on live data)

`frontend/app/backend.py` calls paths that do not exist as written:

| Frontend calls | Reality | Fix |
|---|---|---|
| `GET /public/options?condition=&location=` | Team A has `/public/trials` and `/public/drug-label` | Either add an `/public/options` aggregator to Team A that merges both, or change the frontend to make two calls and merge client-side. **Aggregator on Team A is cleaner.** |
| `GET /internal/trial-risk?disease=&phase=&enrollment=&endpoint=` | Team C has `/internal/trial-risk-analysis` (GET **and** POST) | Rename in the frontend to `/internal/trial-risk-analysis`. |
| `GET /internal/repurposing?q=` | Does not exist anywhere | Stretch scope. Leave on stubs. |

### 4. Team B is not wired into the frontend at all (gap)
`backend.py` has no call to any `/internal/enrichment/*` endpoint. The Patient Portal
detail popup is supposed to show Team B's plain-language summary, and Portal 2 is
supposed to show trial context. Add:

```python
def patient_summary(condition_id, treatment_id, condition_name, treatment_name) -> dict:
    """Portal 1 detail popup: Team B's vetted, safety-gated plain-language summary."""
    ...  # GET {ENRICHMENT_URL}/internal/enrichment/patient-summary

def trial_context(nct_id: str) -> dict:
    """Portal 2: Team B's sponsor/investigator/press context for one trial."""
    ...  # GET {ENRICHMENT_URL}/internal/enrichment/trial-context
```

**Contract rule Team D must honor:** if `safety.passed` is `false`, render nothing.
`content` will be an empty string. Do not fall back to raw text — the gate fails
closed on purpose.

### 5. Single `BACKEND_URL` for three services (blocking)
`frontend/app/backend.py` reads one `BACKEND_URL` env var, but Team A, B, and C are
three separate services on three ports. Split into `BACKEND_URL`, `ENRICHMENT_URL`,
`RISK_URL`, defaulting each to stubs independently so a single service being down
degrades one panel instead of the whole app.

Keep the `PublicClient` / `InternalClient` prefix guard — that boundary enforcement is
good and is exactly what MASTER.md §2.3 asks for. Team B's enrichment service is
internal-only; the Patient Portal reaches its summaries through Team A's `/public/*`
surface or through a dedicated vetted-summary route, never by calling
`/internal/enrichment/*` from a patient-facing view.

### 6. Name drift (cosmetic, fix before demo)
Team C's README still says **"Pharos"**. The product is **Synapse**. Grep for `Pharos`
across all branches after merging.

## Data: do NOT re-scrape or re-ingest

- **Team B:** `enrichment/cache.db` is **committed** with 9 prefetched, pinned entries
  (ALS). Pinned entries never expire. The service answers from cache instantly and
  makes zero network calls for the demo path. Do not run `scripts/prefetch.py` unless
  the disease area changes.
- **Team A / Team C:** both target **ALS**, consistent with Team B's cache. Team C
  ships `scripts/make_fixture.py` for a synthetic cohort if ingestion hasn't been run.
- Team B's `.env` is gitignored. Credentials come from Kenil out of band.

## Verification after merge (all fast, no long-running commands)

```bash
# Team B — offline checks only, ~5s
cd enrichment && python -m scripts.smoke_test
```

Everything else: start each service, hit `/health` or `/docs`, click through the three
portals. Do not run ingestion, prefetch, or any scrape during integration.
