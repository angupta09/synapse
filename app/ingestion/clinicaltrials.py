"""ClinicalTrials.gov REST API v2 ingestion.

Docs: https://clinicaltrials.gov/data-api/api
Field selection keeps payloads manageable — we only request the modules the
spec asks for (NCT ID, conditions, interventions, phase, status, whyStopped,
enrollment, eligibility text, sponsor, locations).
"""

from collections.abc import Iterator
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

BASE_URL = "https://clinicaltrials.gov/api/v2/studies"

FIELDS = [
    "NCTId",
    "BriefTitle",
    "BriefSummary",
    "Condition",
    "InterventionName",
    "Phase",
    "OverallStatus",
    "WhyStopped",
    "EnrollmentCount",
    "EligibilityCriteria",
    "LeadSponsorName",
    "LocationFacility",
    "LocationCity",
    "LocationState",
    "LocationCountry",
]


@retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=1, max=20))
def _fetch_page(client: httpx.Client, condition_query: str, page_token: str | None, page_size: int) -> dict:
    params: dict[str, Any] = {
        "query.cond": condition_query,
        "fields": "|".join(FIELDS),
        "pageSize": page_size,
        "format": "json",
    }
    if page_token:
        params["pageToken"] = page_token
    resp = client.get(BASE_URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_studies(condition_query: str, max_studies: int = 300, page_size: int = 100) -> Iterator[dict]:
    """Yield raw study JSON objects (protocolSection dict) one at a time."""
    fetched = 0
    page_token = None
    with httpx.Client(headers={"User-Agent": "team-a-data-backend/1.0"}) as client:
        while fetched < max_studies:
            data = _fetch_page(client, condition_query, page_token, page_size)
            studies = data.get("studies", [])
            if not studies:
                break
            for study in studies:
                yield study
                fetched += 1
                if fetched >= max_studies:
                    break
            page_token = data.get("nextPageToken")
            if not page_token:
                break


def extract_fields(study: dict) -> dict:
    """Flatten a raw CT.gov v2 study payload into the columns we store."""
    protocol = study.get("protocolSection", {})
    ident = protocol.get("identificationModule", {})
    desc = protocol.get("descriptionModule", {})
    cond_module = protocol.get("conditionsModule", {})
    design = protocol.get("designModule", {})
    status_module = protocol.get("statusModule", {})
    elig = protocol.get("eligibilityModule", {})
    sponsor_module = protocol.get("sponsorCollaboratorsModule", {})
    contacts = protocol.get("contactsLocationsModule", {})
    arms = protocol.get("armsInterventionsModule", {})

    interventions = [
        i.get("name") for i in arms.get("interventions", []) if i.get("name")
    ]
    locations = []
    for loc in contacts.get("locations", []):
        locations.append(
            {
                "facility": loc.get("facility"),
                "city": loc.get("city"),
                "state": loc.get("state"),
                "country": loc.get("country"),
            }
        )

    phases = design.get("phases", [])

    return {
        "nct_id": ident.get("nctId"),
        "title": ident.get("briefTitle"),
        "brief_summary": desc.get("briefSummary"),
        "condition_text": cond_module.get("conditions", []),
        "intervention_text": interventions,
        "phase": phases[0] if phases else None,
        "status": status_module.get("overallStatus"),
        "why_stopped": status_module.get("whyStopped"),
        "enrollment_count": (design.get("enrollmentInfo") or {}).get("count"),
        "eligibility_text": elig.get("eligibilityCriteria"),
        "sponsor": (sponsor_module.get("leadSponsor") or {}).get("name"),
        "locations": locations,
    }
