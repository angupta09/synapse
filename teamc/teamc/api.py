"""Team C internal API — the surface Team D consumes for Portal 2.

Routes are all under /internal/*. Nothing here is mounted on the public path,
and nothing here is safe to expose to the Patient Portal except
/internal/patient-safe-rewrite, which is deliberately built to touch only the
text handed to it (no Convoke, no repurposing, no model memory).
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .risk import RiskModel
from .safety import SafetyVerdict, check_patient_safe

MODEL_PATH = Path(os.environ.get("PHAROS_MODEL", "data/model.json"))

app = FastAPI(
    title="Pharos — Team C internal reasoning API",
    version="0.1.0",
    description="Portal 2 trial-risk analysis. Every number cites its trials.",
)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

_model: RiskModel | None = None


def model() -> RiskModel:
    global _model
    if _model is None:
        if not MODEL_PATH.exists():
            raise HTTPException(
                503,
                f"model not built: {MODEL_PATH} missing. "
                "Run `python scripts/ingest.py --condition '<disease>'` first.",
            )
        _model = RiskModel.load(MODEL_PATH)
    return _model


# --------------------------------------------------------------- schemas


class TrialDesign(BaseModel):
    """A candidate/hypothetical trial design. All fields optional — the model
    scores whatever it is given and tells you which features it matched on."""

    phase: str | None = Field(None, examples=["PHASE2"])
    enrollment: int | None = Field(None, examples=[120])
    n_sites: int | None = Field(None, examples=[4])
    n_arms: int | None = Field(None, examples=[3])
    n_criteria: int | None = Field(None, examples=[38])
    primary_endpoint: str | None = Field(
        None, examples=["Change from baseline in ALSFRS-R total score at 24 weeks"]
    )
    endpoint_type: str | None = None
    masking: str | None = Field(None, examples=["DOUBLE"])
    allocation: str | None = Field(None, examples=["RANDOMIZED"])
    sponsor_class: str | None = Field(None, examples=["INDUSTRY"])
    multi_country: str | None = Field(None, examples=["single-country"])
    age_restricted: str | None = None


class RewriteRequest(BaseModel):
    source_text: str
    source_ids: list[str] = Field(default_factory=list)
    plain_text: str | None = Field(
        None, description="Candidate rewrite to check. If omitted, only the "
                          "source is validated and no rewrite is returned."
    )


# --------------------------------------------------------------- routes


@app.get("/internal/health")
def health() -> dict:
    ok = MODEL_PATH.exists()
    return {
        "status": "ok" if ok else "model-missing",
        "model_path": str(MODEL_PATH),
        "condition": model().condition if ok else None,
    }


@app.get("/internal/failure-landscape")
def failure_landscape() -> dict:
    """Portal 2 landing panel: how trials in this disease area actually fail."""
    return model().failure_summary()


@app.get("/internal/trial-risk-analysis")
def trial_risk_analysis_get(
    trial_design: str = Query(
        ...,
        description="JSON-encoded TrialDesign, e.g. "
                    '{"phase":"PHASE2","enrollment":120,"n_sites":3}',
    )
) -> dict:
    try:
        payload = json.loads(trial_design)
    except json.JSONDecodeError as exc:
        raise HTTPException(422, f"trial_design must be valid JSON: {exc}")
    return _analyse(payload)


@app.post("/internal/trial-risk-analysis")
def trial_risk_analysis_post(design: TrialDesign = Body(...)) -> dict:
    """Same as the GET, with a real body. Prefer this from the frontend."""
    return _analyse(design.model_dump(exclude_none=True))


def _analyse(payload: dict[str, Any]) -> dict:
    m = model()
    result = m.score(payload)
    if not result["matched_features"]:
        raise HTTPException(
            422,
            "no scorable design features supplied — provide at least phase, "
            "enrollment, n_sites or n_arms",
        )
    # Attach the full record for every cited trial so the UI never has to
    # make a second round trip to render an evidence panel.
    cited = sorted({
        nid
        for flag in result["flags"]
        for d in flag["drivers"]
        for nid in d["cited_trials"]
    })
    result["evidence"] = m.cited_trials(cited)
    return result


@app.get("/internal/trials/{nct_id}")
def trial_detail(nct_id: str) -> dict:
    rows = model().cited_trials([nct_id.upper()])
    if not rows:
        raise HTTPException(404, f"{nct_id} not in the modelled cohort")
    return rows[0]


@app.post("/internal/patient-safe-rewrite")
def patient_safe_rewrite(req: RewriteRequest = Body(...)) -> dict:
    """Guardrail pass for Team D's Patient Portal (support role).

    This endpoint is intentionally isolated: it reads only `source_text`. It has
    no access to the risk model, Convoke, or any repurposing output, so there is
    no code path by which speculative content can reach a patient-facing screen.
    """
    verdict: SafetyVerdict = check_patient_safe(
        source_text=req.source_text, candidate=req.plain_text
    )
    return {
        "pass": verdict.passed,
        "plain_text": req.plain_text if verdict.passed else None,
        "violations": verdict.violations,
        "checks_run": verdict.checks_run,
        "source_ids": req.source_ids,
        "boundary": "convoke-free: this endpoint reads no reasoning-layer data",
    }
