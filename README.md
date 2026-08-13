# Synapse

Clinical trial intelligence platform — Biopharma Hack Day, Aug 13 2026.
One evidence-grounded data spine, three portals. See [MASTER.md](MASTER.md).

## Run

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt      # Linux/mac: .venv/bin/pip
.venv/Scripts/python -m uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000

```bash
.venv/Scripts/python test_boundary.py             # checks the patient safety boundary
```

## Layout

| Path | What |
|---|---|
| `app/main.py` | Routes: `/` `/patient` `/trial-design` `/rd` |
| `app/backend.py` | The only place that talks to Team A/C. Stubs until `BACKEND_URL` is set. |
| `app/stubs.py` | Placeholder data so the UI builds in parallel |
| `app/templates/` | Jinja2 pages |
| `app/static/app.css` | Hand-written CSS — no build step, no CDN, renders offline |

## Going live

Set one env var; nothing else changes.

```bash
BACKEND_URL=https://<team-a-api> .venv/Scripts/python -m uvicorn app.main:app
```

Expected contract:

- `GET /public/options?condition=&location=` → list of rows
  (`name, kind, status, phase, study_id, location, summary, contact, sources[]`)
- `GET /internal/trial-risk?disease=&phase=&enrollment=&endpoint=` → `verdict, headline, patterns[], comparable_successes[]`
- `GET /internal/repurposing?q=` → `mechanism, candidates[]`

Stub shapes in `app/stubs.py` are the spec — match them and the UI needs no changes.

## Safety boundary

The Patient Portal may only touch `/public/*`. `backend.PublicClient` raises
`BoundaryViolation` on anything else, so a Convoke-touched path can't reach a patient
even by accident. `test_boundary.py` enforces it.

## Demo notes

- Locked disease area: **ALS**. Don't let judges pick one live.
- Stub banner shows whenever `BACKEND_URL` is unset — it disappears on real data.
- TODO before demo: record the fallback walkthrough video.
