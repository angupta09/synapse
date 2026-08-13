"""Backfill normalized entity IDs onto every ingested trial and drug label.

Usage:
    python -m app.ingestion.backfill_normalize
"""

import logging

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db import SessionLocal
from app.models import DrugLabel, Entity, Trial, TrialCondition, TrialIntervention
from app.normalize import normalize_disease, normalize_drug

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("backfill")

# Below this, a match is more likely to be ontology noise than a real mapping.
# Downstream teams join on these IDs, so a wrong link is worse than no link.
MIN_LINK_CONFIDENCE = 0.72


def _link(db, table, trial: Trial, entity_id: int) -> None:
    """Several free-text conditions on one trial routinely collapse to the same
    canonical ID ("Diabetes" and "Type 2 Diabetes"), so the link may already be
    pending in this transaction — where a SELECT check can't see it."""
    db.execute(
        pg_insert(table)
        .values(trial_nct_id=trial.nct_id, entity_id=entity_id)
        .on_conflict_do_nothing()
    )


def _entity_id_for(db, source_system: str, source_id: str) -> int | None:
    entity = db.execute(
        select(Entity).where(Entity.source_system == source_system, Entity.source_id == source_id)
    ).scalar_one_or_none()
    return entity.id if entity else None


def backfill_trials():
    db = SessionLocal()
    count = 0
    try:
        trials = db.execute(select(Trial)).scalars().all()
        for trial in trials:
            for cond_text in trial.condition_text:
                result = normalize_disease(cond_text, db)
                if result and result["confidence"] >= MIN_LINK_CONFIDENCE:
                    entity_id = _entity_id_for(db, result["source_system"], result["id"])
                    if entity_id:
                        _link(db, TrialCondition, trial, entity_id)
                elif result:
                    log.debug(
                        "skipped low-confidence condition %r -> %s (%.2f)",
                        cond_text, result["canonical_name"], result["confidence"],
                    )
            for drug_text in trial.intervention_text:
                result = normalize_drug(drug_text, db)
                if result and result["confidence"] >= MIN_LINK_CONFIDENCE:
                    entity_id = _entity_id_for(db, result["source_system"], result["id"])
                    if entity_id:
                        _link(db, TrialIntervention, trial, entity_id)
            count += 1
            if count % 25 == 0:
                db.commit()
                log.info("backfilled %d trials", count)
        db.commit()
        log.info("done: %d trials normalized", count)
    finally:
        db.close()


def backfill_drug_labels():
    db = SessionLocal()
    count = 0
    try:
        labels = db.execute(select(DrugLabel).where(DrugLabel.drug_id.is_(None))).scalars().all()
        for label in labels:
            text = label.generic_name or label.brand_name
            if not text:
                continue
            result = normalize_drug(text, db)
            if result and result["confidence"] >= MIN_LINK_CONFIDENCE:
                entity_id = _entity_id_for(db, result["source_system"], result["id"])
                if entity_id:
                    label.drug_id = entity_id
            count += 1
            if count % 25 == 0:
                db.commit()
                log.info("backfilled %d drug labels", count)
        db.commit()
        log.info("done: %d drug labels normalized", count)
    finally:
        db.close()


def main():
    log.info("backfilling trial condition/intervention normalization")
    backfill_trials()
    log.info("backfilling drug label normalization")
    backfill_drug_labels()


if __name__ == "__main__":
    main()
