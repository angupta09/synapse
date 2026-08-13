# Synapse

Clinical trial intelligence for three audiences on one evidence-grounded data spine.
Built for Biopharma Hack Day (AWS Builder Loft, San Francisco — Aug 13 2026).

Every claim the UI makes is traceable to a source record. Every patient-facing byte
comes from a read-only public API that is structurally incapable of reaching the
speculative reasoning layer.

This repository is the **frontend and product surface** — FastAPI + Jinja2, no JS
framework, no build step, no CDN. It runs against stub data out of the box and
switches to the real backend with one environment variable.

---

## The three portals

| Route | Portal | Question it answers | Data it may touch |
|---|---|---|---|
| `/patient` | Patient Portal | "What are my options?" | `/public/*` only — openFDA labels, ClinicalTrials.gov, pre-vetted plain-language summaries |
| `/trial-design` | Trial Design Portal | "Why did trials shaped like mine fail?" | `/internal/*` — failure-pattern analysis over `whyStopped` |
| `/rd` | R&D / Repurposing Portal | "What should we work on next?" | `/internal/*` — target/mechanism similarity, repurposing candidates |

`/` is the index that routes between them.

### Patient Portal

Condition (+ optional location) in, a table out: **Treatment Option / Status / Phase /
Study number / Location**. Three status values only — `Approved`,
`Currently accepting patients`, `Not started / not accepting patients`. Each row opens a
native `<dialog>` with a plain-English summary written at reading level, a contact route,
and a **Sources** block. A "not medical advice" disclaimer is on the page and asserted by
a test.

An unrecognised condition returns an empty state, not an error — that is the honest
answer when the registry has nothing.

### Trial Design Portal

Takes a proposed design (disease, phase, enrollment, primary endpoint) and compares it
against comparable studies that stopped early or read out negative. Output is a verdict
(`Comparable to trials that completed` → `High risk`), a headline, matched failure
patterns with a percentage and per-pattern citations, and **comparable successes** —
studies of the same shape that worked, with an explicit `differed_by` note.

The `whyStopped` free-text field from each cited ClinicalTrials.gov record is rendered
inline. That field is the credibility feature; a test fails if it disappears from the page.

### R&D / Repurposing Portal (stretch)

A mechanism summary for a queried drug or target, plus ranked repurposing candidates —
each with a confidence score, a written rationale, and an evidence trail of study IDs and
target annotations. Deliberately scoped to the candidate panel; the landscape,
competitive-intel, and next-actions blocks were planned cuts, not gaps.

---

## Run it

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt          # Linux/macOS: .venv/bin/pip
.venv/Scripts/python -m uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000>. No API keys, no network, no backend needed — stub data
carries the whole UI.

### Checks

```bash
.venv/Scripts/python test_boundary.py     # safety boundary + every portal renders
.venv/Scripts/python -m app.stubs         # stub data self-check
```

Both are plain `assert` scripts with a `__main__` block — no pytest required, though
`pytest test_boundary.py` works too.

---

## Layout

| Path | What |
|---|---|
| `app/main.py` | Four routes. Reads query params, calls `backend`, renders a template. No logic. |
| `app/backend.py` | **The only module that talks to another team's API.** Boundary enforcement lives here. |
| `app/stubs.py` | Placeholder data shaped exactly like the real API responses. |
| `app/templates/` | Jinja2 — `base.html` (shell, nav, stub banner) plus one per portal. |
| `app/static/app.css` | 205 lines, hand-written, light default with `prefers-color-scheme: dark`. |
| `test_boundary.py` | The five checks worth keeping. |

Nothing calls an API from a route or a template. If you need data, add a function to
`backend.py`.

---

## The safety boundary

Speculative reasoning must never reach a patient. That is a policy statement everywhere
else in the plan; here it is a type.

```python
class _Client:
    prefix = ""
    def get(self, path, **params):
        if not path.startswith(self.prefix):
            raise BoundaryViolation(...)

class PublicClient(_Client):    prefix = "/public/"     # Patient Portal
class InternalClient(_Client):  prefix = "/internal/"   # Portals 2 and 3
```

`backend.public` can only ever construct a `/public/*` URL. A patient-facing route cannot
reach the Convoke-touched reasoning path even by typo, refactor, or copy-paste. The
symmetric rule holds too — `InternalClient` refuses `/public/` paths, so the layers stay
legible rather than merely one-directional.

`test_boundary.py` asserts both directions against a list of near-miss paths
(`/internal/trial-risk`, `/public-ish/x`, `/`). Do not relax it.

---

## Going live

Set one variable. Nothing else changes.

```bash
BACKEND_URL=https://<backend-host> .venv/Scripts/python -m uvicorn app.main:app
```

Unset → every call falls through to `stubs.py` and a stub banner appears at the top of
every page. Set → real HTTP, banner gone. `backend.is_live()` is exposed to templates as
`live()`, so the banner cannot be left on by accident.

### API contract

| Endpoint | Returns |
|---|---|
| `GET /public/options?condition=&location=` | `[{name, kind, status, phase, study_id, location, summary, contact, sources[]}]` |
| `GET /internal/trial-risk?disease=&phase=&enrollment=&endpoint=` | `{design, verdict, headline, patterns[], comparable_successes[]}` |
| `GET /internal/repurposing?q=` | `{query, mechanism, candidates[]}` |

`sources[]` and `evidence[]` entries are `{label, url}` (plus `study_id`, and
`why_stopped` on trial-risk citations).

**The dict shapes in `app/stubs.py` are the specification.** Match them and the frontend
needs no changes. Add rows freely; renaming or dropping a key is a contract change and
needs agreement on both sides.

---

## Stub honesty

Stub data is labelled at three levels so nothing fabricated can reach a judge unmarked:

1. Drug and approval facts are **real** (riluzole, edaravone, tofersen for ALS; the CFTR
   modulators; the DMD and HD agents).
2. Study identifiers are **invented**, kept in an obvious `NCT0000XXXX` form. Percentages
   in the failure patterns are invented too.
3. The stub banner names both facts on every page while `BACKEND_URL` is unset.

Four conditions are stubbed — ALS, Duchenne muscular dystrophy, Huntington's, cystic
fibrosis — so the portals can be exercised beyond a single rehearsed path.

---

## Demo notes

- **Locked disease area: ALS.** Deep ClinicalTrials.gov coverage, three approved drugs in
  openFDA, and a well-documented recent failure (AMX0035/Relyvrio, withdrawn after
  PHOENIX) for the trial-design story. Do not let the audience pick a condition live.
- Suggested run: Patient Portal (emotional hook, citations visible) → Trial Design (the
  "we learned something real from data" beat) → R&D if it is solid.
- Pre-fetch anything slow before going on stage. Never make the demo depend on a cold
  live call finishing in real time.
- **Outstanding:** the fallback walkthrough recording has not been made. Do it before
  the demo, not during it.

---

## Design decisions worth not re-litigating

- **No CDN, no build step, no JS framework.** The demo has to render with the Wi-Fi off.
  This rules out webfonts loaded from Google Fonts — self-host a `woff2` or skip it.
- **Light mode is the default**, dark follows the OS. This gets read at a desk, in a
  clinic, and off a projector in a lit room — not the scene dark UI is for.
- **Accent is split** into `--accent` (5.6:1, safe for text and fills) and `--accent-soft`
  (3.7:1, non-text only) so contrast can't silently regress.
- Known gaps: no media queries anywhere, no `:focus-visible` styling, `<th>` missing
  `scope="col"`, nav `.on` is visual without `aria-current`. Accessibility and responsive
  work is the first thing to do if the schedule loosens.

---

## Conventions

- All backend calls go through `app/backend.py`.
- Patient Portal touches `/public/*` only — enforced, not agreed.
- Every derived or AI-generated claim shows a visible source citation. If you can't cite
  it, don't render it.
- Deliberate simplifications carry a `ponytail:` comment naming the ceiling and the
  upgrade path.
- Planning documents (master plan, per-team briefs, todos) are local-only and
  git-ignored — this README is the tracked source of truth for the repo.
