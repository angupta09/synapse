"""openFDA drug label ingestion.

Docs: https://open.fda.gov/apis/drug/label/
This dataset is close to static — one clean pull per disease area is enough.
"""

from collections.abc import Iterator

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

BASE_URL = "https://api.fda.gov/drug/label.json"
MAX_SKIP = 1000  # openFDA hard limit on skip + limit


@retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, min=1, max=20))
def _fetch_page(client: httpx.Client, condition_query: str, skip: int, limit: int) -> dict:
    search = f'indications_and_usage:"{condition_query}"'
    params = {"search": search, "limit": limit, "skip": skip}
    resp = client.get(BASE_URL, params=params, timeout=30)
    if resp.status_code == 404:
        return {"results": []}
    resp.raise_for_status()
    return resp.json()


def fetch_labels(condition_query: str, max_labels: int = 200, page_size: int = 100) -> Iterator[dict]:
    """Yield raw openFDA drug label result objects one at a time."""
    fetched = 0
    skip = 0
    with httpx.Client(headers={"User-Agent": "team-a-data-backend/1.0"}) as client:
        while fetched < max_labels and skip < MAX_SKIP:
            limit = min(page_size, max_labels - fetched)
            data = _fetch_page(client, condition_query, skip, limit)
            results = data.get("results", [])
            if not results:
                break
            for result in results:
                yield result
                fetched += 1
                if fetched >= max_labels:
                    break
            skip += limit


def record_id(label: dict) -> str:
    return label.get("id") or (label.get("openfda", {}) or {}).get("spl_id", ["unknown"])[0]


def _spl_product_name(label: dict) -> str | None:
    """Many SPL records have an empty `openfda` block. Their product name is
    still recoverable from the first token of spl_product_data_elements,
    which is enough for RxNorm approximate matching."""
    elements = label.get("spl_product_data_elements") or []
    if not elements:
        return None
    tokens = str(elements[0]).split()
    return tokens[0] if tokens else None


def extract_fields(label: dict) -> dict:
    openfda = label.get("openfda", {}) or {}

    def first(key: str) -> str | None:
        vals = openfda.get(key)
        return vals[0] if vals else None

    fallback_name = _spl_product_name(label)
    label_text = " ".join(label.get("indications_and_usage", []) or [])
    mechanism_text = " ".join(
        label.get("mechanism_of_action", []) or label.get("clinical_pharmacology", []) or []
    )

    return {
        "openfda_id": record_id(label),
        "brand_name": first("brand_name") or fallback_name,
        "generic_name": first("generic_name") or first("substance_name") or fallback_name,
        "rxcui": first("rxcui"),
        "label_text": label_text,
        "mechanism_text": mechanism_text,
        "approval_date": None,  # openFDA label endpoint doesn't carry approval date directly
    }
