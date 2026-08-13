from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Provenance


def get_provenance(db: Session, derived_claim_id: str) -> dict:
    rows = db.execute(
        select(Provenance).where(Provenance.derived_claim_id == derived_claim_id)
    ).scalars().all()
    if not rows:
        return {"source_record_type": "", "source_record_ids": []}
    return {
        "source_record_type": rows[0].source_record_type,
        "source_record_ids": [r.source_record_id for r in rows],
    }
