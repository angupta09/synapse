# Synapse

Spec: [MASTER.md](MASTER.md) (architecture, team split, timeline) and
[project-overview.md](project-overview.md) (product goals). This repo's role is
[team-D-frontend-product.md](team-D-frontend-product.md) — **frontend & product**.

## Stack

Python + FastAPI + Jinja2 templates + hand-written CSS. No JS framework, no build
step, no CDN — the demo must render offline.

## Rules

- All backend calls go through `app/backend.py`. Never call an API from a route or template.
- Patient Portal touches `/public/*` only — enforced by `BoundaryViolation`, tested in
  `test_boundary.py`. This is a product requirement, not just a backend one.
- Every derived or AI-generated claim in the UI shows a visible source citation.
- Stubs in `app/stubs.py` are the API contract with Teams A/C. Change them only by agreement.
- Locked demo disease area: ALS.
