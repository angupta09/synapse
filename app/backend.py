"""Single swap point between stub data and Team A/C's real APIs.

Set BACKEND_URL to switch the whole frontend over to live data. Until then every
call falls through to stubs.py so the UI can be built in parallel (MASTER.md §5).

The Patient Portal safety boundary from MASTER.md §2.3 is enforced here, not by
convention: PublicClient can only ever build /public/* URLs, so no patient-facing
route can reach a Convoke-touched path even by mistake.
"""

import os

import httpx

from . import stubs

BACKEND_URL = os.getenv("BACKEND_URL", "").rstrip("/")
TIMEOUT = 10.0


class BoundaryViolation(RuntimeError):
    """Raised when a client is asked for a path outside its own namespace."""


class _Client:
    prefix = ""

    def get(self, path: str, **params):
        if not path.startswith(self.prefix):
            raise BoundaryViolation(
                f"{type(self).__name__} may only call {self.prefix}*, got {path!r}"
            )
        r = httpx.get(f"{BACKEND_URL}{path}", params=params, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()


class PublicClient(_Client):
    """Patient Portal only. openFDA + ClinicalTrials.gov + vetted summaries."""

    prefix = "/public/"


class InternalClient(_Client):
    """Portals 2 and 3 only. Pattern analysis, Convoke, repurposing pipeline."""

    prefix = "/internal/"


public = PublicClient()
internal = InternalClient()


def patient_options(condition: str, location: str) -> list[dict]:
    """Portal 1: approved drugs + trials for a condition. Safe sources only."""
    if not BACKEND_URL:
        return stubs.patient_options(condition, location)
    return public.get("/public/options", condition=condition, location=location)


def trial_risk(disease: str, phase: str, enrollment: int, endpoint: str) -> dict:
    """Portal 2: Team C's failure-pattern analysis for a proposed design."""
    if not BACKEND_URL:
        return stubs.trial_risk(disease, phase, enrollment, endpoint)
    return internal.get(
        "/internal/trial-risk",
        disease=disease,
        phase=phase,
        enrollment=enrollment,
        endpoint=endpoint,
    )


def repurposing_brief(query: str) -> dict:
    """Portal 3 (stretch): opportunity summary + repurposing candidates."""
    if not BACKEND_URL:
        return stubs.repurposing_brief(query)
    return internal.get("/internal/repurposing", q=query)


def is_live() -> bool:
    return bool(BACKEND_URL)
