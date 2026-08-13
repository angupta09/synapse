from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import DrugLabel, Entity, Trial, TrialCondition, TrialIntervention
from app.provenance import get_provenance
from app.schemas import DrugLabelInternalOut, SimilarTrialOut, TrialInternalOut

router = APIRouter(prefix="/internal", tags=["internal"])


def _trial_to_out(db: Session, trial: Trial) -> TrialInternalOut:
    condition_ids = [db.get(Entity, tc.entity_id).source_id for tc in trial.conditions]
    intervention_ids = [db.get(Entity, ti.entity_id).source_id for ti in trial.interventions]
    return TrialInternalOut(
        nct_id=trial.nct_id,
        title=trial.title,
        condition_text=trial.condition_text,
        condition_ids=condition_ids,
        intervention_text=trial.intervention_text,
        intervention_ids=intervention_ids,
        phase=trial.phase,
        status=trial.status,
        why_stopped=trial.why_stopped,
        enrollment_count=trial.enrollment_count,
        eligibility_text=trial.eligibility_text,
        sponsor=trial.sponsor,
        locations=trial.locations,
        provenance=get_provenance(db, f"trial:{trial.nct_id}"),
    )


@router.get("/trials", response_model=list[TrialInternalOut])
def list_trials(
    condition_id: str | None = Query(default=None, description="MONDO ID, e.g. MONDO:0005148"),
    status: str | None = Query(default=None),
    phase: str | None = Query(default=None),
    limit: int = Query(default=50, le=500),
    db: Session = Depends(get_db),
) -> list[TrialInternalOut]:
    stmt = select(Trial)
    if condition_id:
        stmt = stmt.join(TrialCondition, TrialCondition.trial_nct_id == Trial.nct_id).join(
            Entity, Entity.id == TrialCondition.entity_id
        ).where(Entity.source_id == condition_id)
    if status:
        stmt = stmt.where(Trial.status == status)
    if phase:
        stmt = stmt.where(Trial.phase == phase)
    stmt = stmt.limit(limit)

    trials = db.execute(stmt).unique().scalars().all()
    return [_trial_to_out(db, t) for t in trials]


@router.get("/drug-label", response_model=list[DrugLabelInternalOut])
def get_drug_label(
    drug_id: str = Query(..., description="RxNorm ID"),
    db: Session = Depends(get_db),
) -> list[DrugLabelInternalOut]:
    entity = db.execute(
        select(Entity).where(Entity.source_system == "RXNORM", Entity.source_id == drug_id)
    ).scalar_one_or_none()
    if entity is None:
        return []

    labels = db.execute(select(DrugLabel).where(DrugLabel.drug_id == entity.id)).scalars().all()

    out = []
    for label in labels:
        condition_entity = db.get(Entity, label.condition_id) if label.condition_id else None
        out.append(
            DrugLabelInternalOut(
                id=label.id,
                drug_id=drug_id,
                brand_name=label.brand_name,
                generic_name=label.generic_name,
                condition_id=condition_entity.source_id if condition_entity else None,
                label_text=label.label_text,
                mechanism_text=label.mechanism_text,
                approval_date=label.approval_date,
                provenance=get_provenance(db, f"drug_label:{label.id}"),
            )
        )
    return out


@router.get("/similar-trials", response_model=list[SimilarTrialOut])
def similar_trials(
    trial_id: str = Query(..., description="NCT ID to find similar trials for"),
    k: int = Query(default=5, le=50),
    db: Session = Depends(get_db),
) -> list[SimilarTrialOut]:
    target = db.get(Trial, trial_id)
    if target is None:
        raise HTTPException(status_code=404, detail=f"trial {trial_id} not found")
    if target.embedding is None:
        raise HTTPException(status_code=409, detail=f"trial {trial_id} has not been embedded yet")

    distance = Trial.embedding.cosine_distance(target.embedding)
    stmt = (
        select(Trial, distance.label("distance"))
        .where(Trial.nct_id != trial_id, Trial.embedding.is_not(None))
        .order_by(distance)
        .limit(k)
    )
    rows = db.execute(stmt).all()
    return [
        SimilarTrialOut(nct_id=t.nct_id, title=t.title, similarity=1.0 - float(d))
        for t, d in rows
    ]
