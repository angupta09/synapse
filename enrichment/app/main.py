"""Synapse — Team B Enrichment Service (Bright Data).

Exposes the three enrichment endpoints the other three tracks consume.
Every response carries {content, source_url, fetched_at} at minimum; nothing
unsourced leaves this service.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import brightdata, cache, enrichment
from .config import HAS_BRIGHTDATA, HAS_LLM

app = FastAPI(
    title="Synapse — Enrichment Service (Team B)",
    description="Bright Data enrichment for the Patient, Trial Design, and R&D portals.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    cache.init()


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "brightdata_configured": HAS_BRIGHTDATA,
        "llm_configured": HAS_LLM,
        "summarization_mode": "llm" if HAS_LLM else "extractive",
        "cache": cache.stats(),
    }


# --- Patient Portal (safety-gated) ---------------------------------------


@app.get("/internal/enrichment/patient-summary")
async def get_patient_summary(
    condition_id: str = Query(..., description="Canonical condition ID from Team A"),
    treatment_id: str = Query(..., description="Canonical drug/trial ID from Team A"),
    condition_name: str = Query(..., description="Human-readable condition name"),
    treatment_name: str = Query(..., description="Human-readable treatment name"),
    refresh: bool = Query(False, description="Bypass cache and re-fetch"),
) -> dict:
    """Plain-language, safety-gated summary. Safe for the Patient Portal.

    If `safety.passed` is false, `content` is empty by design — fail closed.
    Team D must not render content when `safety.passed` is false.
    """
    try:
        return await enrichment.patient_summary(
            condition_id, treatment_id, condition_name, treatment_name, refresh
        )
    except brightdata.BrightDataError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


# --- Trial Design Portal --------------------------------------------------


@app.get("/internal/enrichment/trial-context")
async def get_trial_context(
    nct_id: str = Query(..., description="ClinicalTrials.gov NCT ID"),
    trial_title: str = Query("", description="Optional trial title for better search recall"),
    refresh: bool = Query(False),
) -> dict:
    """Sponsor/investigator/press context for one trial. Internal use only."""
    try:
        return await enrichment.trial_context(nct_id, trial_title, refresh)
    except brightdata.BrightDataError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


# --- R&D Portal -----------------------------------------------------------


@app.get("/internal/enrichment/competitive-signal")
async def get_competitive_signal(
    target_id: str = Query(..., description="Canonical target/gene ID (HGNC) from Team A"),
    target_name: str = Query("", description="Human-readable target/mechanism name"),
    refresh: bool = Query(False),
) -> dict:
    """Competitive-intelligence feed for a target/mechanism. Internal use only."""
    try:
        return await enrichment.competitive_signal(target_id, target_name, refresh)
    except brightdata.BrightDataError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


# --- Cache ops (demo safety) ---------------------------------------------


@app.get("/internal/cache/stats")
def cache_stats() -> dict:
    return cache.stats()


@app.get("/internal/cache/entries")
def cache_entries(kind: str = Query(None)) -> dict:
    return {"entries": cache.entries(kind)}


@app.post("/internal/cache/pin")
def cache_pin(kind: str, key_json: str) -> dict:
    """Pin an entry so it never expires during the demo."""
    import json

    ok = cache.pin(kind, json.loads(key_json))
    return {"pinned": ok}
