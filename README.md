# Team A — Data & Backend Infrastructure

Builds from `team-A-data-backend.md`: ClinicalTrials.gov + openFDA ingestion,
drug/disease/target normalization, Postgres + pgvector storage, and the
`/internal/*` / `/public/*` API surface the rest of the team reads from.

Disease area locked for the demo: **type 2 diabetes** (`app/config.py` /
`.env` — change `DISEASE_AREA` / `CLINICALTRIALS_CONDITION_QUERY` /
`OPENFDA_CONDITION_QUERY` if the team picks something else).

## 1. Setup

```bash
cp .env.example .env
python -m venv .venv
.venv/Scripts/activate   # or `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
docker compose up -d
```

`docker compose up -d` starts Postgres with the `pgvector` extension and
applies `sql/schema.sql` automatically on first boot.

### If Docker Hub is unreachable (WSL fallback)

This machine could not pull images — Docker Hub's CDN intermittently fails
TLS here, so no image completes. The working alternative is Postgres +
pgvector installed directly in WSL, which uses a different network path:

```bash
wsl --install Ubuntu-24.04 --no-launch
wsl -d Ubuntu-24.04 -u root -- bash -c "apt-get update && apt-get install -y postgresql postgresql-contrib postgresql-16-pgvector"
wsl -d Ubuntu-24.04 -u root -- bash /mnt/c/Users/anshu/Downloads/team-a-data-backend/scripts/setup_wsl_postgres.sh
```

`scripts/setup_wsl_postgres.sh` configures TCP access, creates the `teama`
role and `team_a` database, and applies `sql/schema.sql`.

Two host-side settings make this reachable from Windows without admin
rights, both already applied on this machine:

- `~/.wslconfig` sets `networkingMode=mirrored`. Without it the Hyper-V
  firewall blocks inbound TCP to WSL (ICMP still works, which makes it look
  like a Postgres problem rather than a firewall one), and adding a firewall
  rule requires admin.
- `/etc/wsl.conf` inside the distro sets `systemd=true` so Postgres starts
  automatically on boot rather than needing a manual start each time.

Either way the connection string stays `localhost:5432`, so `.env` needs no
change.

## 2. Ingest real data (hour 1)

```bash
python -m app.ingestion.run_ingest --max-trials 300 --max-labels 200
```

Raw payloads land in `raw_data/clinicaltrials/` and `raw_data/openfda/`
before anything is transformed, so this step (or normalization) can be
re-run without re-fetching. Set `RAW_STORAGE_BACKEND=s3` + `S3_BUCKET` in
`.env` to write to S3 instead.

## 3. Normalize + embed

```bash
python -m app.ingestion.backfill_normalize
python -m app.ingestion.backfill_embeddings
```

`backfill_normalize` calls `normalize_drug` / `normalize_disease` (RxNorm,
MONDO via EBI OLS) on every ingested trial/label and links them via
`trial_conditions` / `trial_interventions`. `backfill_embeddings` embeds
trial titles + eligibility text and drug label + mechanism text with a
local `sentence-transformers` model (no API key needed) for the pgvector
similarity index.

## 4. Run the API

```bash
uvicorn app.main:app --reload --port 8000
```

- `GET /internal/trials?condition_id=MONDO:...&status=RECRUITING&phase=PHASE3`
- `GET /internal/drug-label?drug_id=<RxNorm ID>`
- `GET /internal/similar-trials?trial_id=NCT.......&k=5`
- `POST /internal/normalize` — `{"type": "drug", "text": "Ozempic"}`
- `GET /public/trials?condition_id=MONDO:...&status=recruiting` — safe subset for the Patient Portal
- `GET /public/drug-label?condition_id=MONDO:...`

Every response includes a `provenance` block (`source_record_type` +
`source_record_ids`) tracing it back to the raw ClinicalTrials.gov/openFDA
payload, per the provenance requirement in the spec.

## 5. Smoke test

```bash
pytest
```

`tests/test_public_boundary.py` explicitly asserts `/public/*` cannot
return anything derived from Convoke (target/gene) data — both by
statically checking the router source never references target/HGNC
concepts, and by checking the public response schemas exclude
internal-only fields. `tests/test_provenance.py` and
`tests/test_normalize.py` need a running Postgres (`docker compose up -d`)
and are skipped otherwise.

To confirm the end-to-end slice works against real data:

```bash
curl "http://localhost:8000/public/trials?status=recruiting&limit=3"
curl "http://localhost:8000/internal/trials?status=RECRUITING&limit=3"
```

Both should return real ClinicalTrials.gov records for the locked disease
area with a non-empty `provenance.source_record_ids`.

## Project layout

```
app/
  config.py, db.py, models.py    # settings, SQLAlchemy session, ORM models
  normalize.py                    # normalize_drug / normalize_disease / normalize_target
  embeddings.py                   # local sentence-transformers embedding
  provenance.py                   # derived_claim_id -> source_record_id[] lookup
  ingestion/
    clinicaltrials.py, openfda.py # API pulls
    storage.py                    # raw payload persistence (local disk or S3)
    run_ingest.py                 # CLI: fetch + store + load
    backfill_normalize.py         # CLI: link normalized entities
    backfill_embeddings.py        # CLI: populate pgvector columns
  routers/
    internal.py, public.py, normalize.py
sql/schema.sql                    # trials, drug_labels, entities, provenance, pgvector
tests/
```

## Normalization quality

Free-text conditions are matched against MONDO via EBI OLS, scoring each
candidate against its label **and its synonyms** (ontology labels are often
formal names while trials use common ones — "adult onset diabetes" resolves
to `MONDO:0005148` at 1.0 only because synonyms are scored).

Two guards keep bad matches out of the join tables, because downstream teams
join on these IDs and a wrong link is worse than a missing one:

- Matches below `MIN_LINK_CONFIDENCE` (0.72, in `backfill_normalize.py`) are
  cached but never linked. This is what rejects real observed junk like
  "fall" → *fallopian tube neoplasm* and "oxidative stress" → *carnitine
  palmitoyl transferase II deficiency*.
- `NON_DISEASE_TERMS` in `normalize.py` drops control-arm values ("healthy",
  "normal", "controls") that have no MONDO equivalent and otherwise
  fuzzy-match to nonsense.

On a 60-trial type 2 diabetes pull this links 55/60 trials, 52 of them to
`MONDO:0005148`. Raising recall on the remaining 5 is the obvious next
tuning step — inspect them with:

```sql
SELECT nct_id, condition_text FROM trials WHERE nct_id NOT IN (SELECT trial_nct_id FROM trial_conditions);
```

## Known gaps / next pass

- Target/gene (HGNC) normalization is implemented and exposed via
  `POST /internal/normalize`, but no trial/label is linked to a target
  entity yet — that join lands once Team C's Convoke data arrives, and
  `tests/test_public_boundary.py` is the guardrail that it never leaks
  into `/public/*`.
- Approval date isn't populated from the openFDA label endpoint (it doesn't
  carry one); would need a second pull against the openFDA NDC or Orange
  Book dataset if that field is needed.
- `drug_labels.condition_id` is set from the disease area the pull was
  scoped to, not parsed per-label from the indications text. That's accurate
  for a single-disease demo but would need real per-label extraction if you
  ingest several disease areas into one database.
