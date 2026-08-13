"""Synapse — clinical trial intelligence platform (Team D frontend).

Three portals, one FastAPI app. See MASTER.md for architecture,
team-D-frontend-product.md for this role's scope.
"""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import backend

HERE = Path(__file__).parent

app = FastAPI(title="Synapse")
app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")
templates = Jinja2Templates(directory=HERE / "templates")
templates.env.globals["live"] = backend.is_live


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/patient", response_class=HTMLResponse)
def patient(request: Request, condition: str = "", location: str = ""):
    # Patient Portal: safe sources only. backend.patient_options is the only
    # call allowed here — see MASTER.md §2.3 and test_boundary.py.
    rows = backend.patient_options(condition, location) if condition else []
    return templates.TemplateResponse(
        request,
        "patient.html",
        {"rows": rows, "condition": condition, "location": location},
    )


@app.get("/trial-design", response_class=HTMLResponse)
def trial_design(
    request: Request,
    disease: str = "",
    phase: str = "Phase 3",
    enrollment: int = 150,
    endpoint: str = "Functional rating scale",
):
    result = backend.trial_risk(disease, phase, enrollment, endpoint) if disease else None
    return templates.TemplateResponse(
        request,
        "trial_design.html",
        {
            "result": result,
            "disease": disease,
            "phase": phase,
            "enrollment": enrollment,
            "endpoint": endpoint,
        },
    )


@app.get("/rd", response_class=HTMLResponse)
def rd(request: Request, q: str = ""):
    brief = backend.repurposing_brief(q) if q else None
    return templates.TemplateResponse(request, "rd.html", {"brief": brief, "q": q})
