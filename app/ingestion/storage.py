"""Raw payload storage: every fetched record is written here, unchanged,
before any transformation — so normalization/backfill can be re-run without
re-fetching from ClinicalTrials.gov / openFDA.
"""

import hashlib
import json
import re
from pathlib import Path

from app.config import settings

_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


def _safe_filename(record_id: str) -> str:
    return _SAFE_NAME.sub("_", record_id)


def _checksum(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def save_raw(source: str, source_record_id: str, payload: dict) -> tuple[str, str, str]:
    """Persist a raw payload before any transformation.

    Returns (storage_path, checksum, backend).
    """
    checksum = _checksum(payload)
    filename = f"{_safe_filename(source_record_id)}_{checksum[:12]}.json"
    body = json.dumps(payload, indent=2)

    if settings.raw_storage_backend == "s3":
        import boto3

        key = f"{source}/{filename}"
        s3 = boto3.client("s3", region_name=settings.aws_region)
        s3.put_object(Bucket=settings.s3_bucket, Key=key, Body=body.encode("utf-8"))
        return key, checksum, "s3"

    out_dir = Path(settings.raw_storage_dir) / source
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / filename
    out_path.write_text(body, encoding="utf-8")
    return str(out_path), checksum, "local"
