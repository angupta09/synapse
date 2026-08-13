"""ClinicalTrials.gov REST API v2 client.

Deliberately dumb: pull whole study records, cache to disk, never call at request
time. The demo must never depend on a live fetch (MASTER.md §2.4).
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Iterator

import urllib.parse
import urllib.request

BASE = "https://clinicaltrials.gov/api/v2/studies"

# Statuses we care about. TERMINATED/WITHDRAWN = the failure cohort,
# COMPLETED = the comparison cohort. SUSPENDED is excluded: it is not a
# terminal state and folding it in inflates the failure base rate.
FAILURE_STATUSES = ["TERMINATED", "WITHDRAWN"]
SUCCESS_STATUSES = ["COMPLETED"]


def _get(params: dict[str, Any], timeout: int = 45) -> dict:
    url = f"{BASE}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "pharos-teamc/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_studies(
    condition: str,
    statuses: list[str],
    page_size: int = 200,
    max_pages: int = 40,
    study_type: str | None = "INTERVENTIONAL",
) -> Iterator[dict]:
    """Yield raw study records for a condition + status filter.

    Pagination in v2 is cursor-based via nextPageToken, not offsets.
    """
    params: dict[str, Any] = {
        "query.cond": condition,
        "filter.overallStatus": "|".join(statuses),
        "pageSize": page_size,
        "format": "json",
        "countTotal": "true",
    }
    if study_type:
        # advanced filter syntax; keeps observational registries out of the cohort
        params["filter.advanced"] = f"AREA[StudyType]{study_type}"

    token = None
    for page in range(max_pages):
        if token:
            params["pageToken"] = token
        payload = _get(params)
        studies = payload.get("studies", [])
        if page == 0 and "totalCount" in payload:
            print(f"    total matching studies: {payload['totalCount']}")
        for s in studies:
            yield s
        token = payload.get("nextPageToken")
        if not token or not studies:
            break
        time.sleep(0.34)  # be polite; NLM has no published hard limit but don't hammer


def pull_cohort(condition: str, out_dir: Path) -> dict[str, Path]:
    """Pull failure + success cohorts and write them to disk as JSONL."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written = {}
    for label, statuses in (("failed", FAILURE_STATUSES), ("completed", SUCCESS_STATUSES)):
        path = out_dir / f"{label}.jsonl"
        n = 0
        print(f"  fetching {label} ({'|'.join(statuses)}) ...")
        with path.open("w") as fh:
            for study in fetch_studies(condition, statuses):
                fh.write(json.dumps(study) + "\n")
                n += 1
        print(f"    wrote {n} records -> {path}")
        written[label] = path
    (out_dir / "manifest.json").write_text(
        json.dumps(
            {
                "condition": condition,
                "pulled_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "source": "ClinicalTrials.gov REST API v2",
                "failure_statuses": FAILURE_STATUSES,
                "success_statuses": SUCCESS_STATUSES,
            },
            indent=2,
        )
    )
    return written


def load_jsonl(path: Path) -> list[dict]:
    with Path(path).open() as fh:
        return [json.loads(line) for line in fh if line.strip()]
