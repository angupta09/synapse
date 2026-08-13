"""Public, read-only routes for the Patient Portal (Team D).

Safety boundary: this is a genuinely separate router/service from
/internal/*, not a filtered parameter on the same code path. It must never
be able to return anything derived from Convoke (target/gene, HGNC) data —
these queries only ever touch trials and drug_labels, and never join
against target-type entities. See tests/test_public_boundary.py, which
asserts this explicitly rather than assuming it.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import DrugLabel, Entity, Trial, TrialCondition
from app.provenance import get_provenance
from app.schemas import DrugLabelPublicOut, TrialPublicOut

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/trials", response_model=list[TrialPublicOut])
def list_public_trials(
    condition_id: str | None = Query(default=None, description="MONDO ID"),
    status: str = Query(default="recruiting"),
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
) -> list[TrialPublicOut]:
    status_filter = "RECRUITING" if status.lower() == "recruiting" else status

    stmt = select(Trial).where(Trial.status == status_filter)
    if condition_id:
        stmt = stmt.join(TrialCondition, TrialCondition.trial_nct_id == Trial.nct_id).join(
            Entity, Entity.id == TrialCondition.entity_id
        ).where(Entity.source_id == condition_id)
    stmt = stmt.limit(limit)

    trials = db.execute(stmt).unique().scalars().all()
    return [
        TrialPublicOut(
            nct_id=t.nct_id,
            title=t.title,
            condition_text=t.condition_text,
            intervention_text=t.intervention_text,
            phase=t.phase,
            status=t.status,
            locations=t.locations,
            provenance=get_provenance(db, f"trial:{t.nct_id}"),
        )
        for t in trials
    ]


@router.get("/drug-label", response_model=list[DrugLabelPublicOut])
def list_public_drug_labels(
    condition_id: str = Query(..., description="MONDO ID"),
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
) -> list[DrugLabelPublicOut]:
    entity = db.execute(
        select(Entity).where(Entity.source_system == "MONDO", Entity.source_id == condition_id)
    ).scalar_one_or_none()
    if entity is None:
        return []

    labels = (
        db.execute(select(DrugLabel).where(DrugLabel.condition_id == entity.id).limit(limit))
        .scalars()
        .all()
    )
    return [
        DrugLabelPublicOut(
            id=label.id,
            brand_name=label.brand_name,
            generic_name=label.generic_name,
            label_text=label.label_text,
            provenance=get_provenance(db, f"drug_label:{label.id}"),
        )
        for label in labels
    ]
