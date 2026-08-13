"""CLI entrypoint: pull ClinicalTrials.gov + openFDA for the locked disease
area, store raw payloads, and load trials/drug_labels + provenance.

Usage:
    python -m app.ingestion.run_ingest --max-trials 300 --max-labels 200
"""

import argparse
import logging

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.config import settings
from app.db import SessionLocal
from app.ingestion import clinicaltrials, openfda
from app.ingestion.storage import save_raw
from app.models import DrugLabel, Entity, Provenance, RawPayload, Trial
from app.normalize import normalize_disease, normalize_drug

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("ingest")


def _record_raw_payload(db, source: str, source_record_id: str, payload: dict) -> RawPayload:
    path, checksum, backend = save_raw(source, source_record_id, payload)
    existing = db.execute(
        select(RawPayload).where(
            RawPayload.source == source,
            RawPayload.source_record_id == source_record_id,
            RawPayload.checksum == checksum,
        )
    ).scalar_one_or_none()
    if existing:
        return existing
    raw = RawPayload(
        source=source,
        source_record_id=source_record_id,
        storage_backend=backend,
        storage_path=path,
        checksum=checksum,
    )
    db.add(raw)
    db.flush()
    return raw


def _add_provenance(db, derived_claim_id: str, source_record_type: str, source_record_id: str, raw_payload_id: int):
    db.add(
        Provenance(
            derived_claim_id=derived_claim_id,
            source_record_type=source_record_type,
            source_record_id=source_record_id,
            raw_payload_id=raw_payload_id,
        )
    )


def ingest_trials(condition_query: str, max_trials: int):
    db = SessionLocal()
    count = 0
    try:
        for study in clinicaltrials.fetch_studies(condition_query, max_studies=max_trials):
            fields = clinicaltrials.extract_fields(study)
            nct_id = fields.pop("nct_id", None)
            if not nct_id:
                continue

            raw = _record_raw_payload(db, "clinicaltrials", nct_id, study)

            stmt = (
                pg_insert(Trial)
                .values(
                    nct_id=nct_id,
                    title=fields["title"],
                    condition_text=fields["condition_text"],
                    intervention_text=fields["intervention_text"],
                    phase=fields["phase"],
                    status=fields["status"],
                    why_stopped=fields["why_stopped"],
                    enrollment_count=fields["enrollment_count"],
                    eligibility_text=fields["eligibility_text"],
                    sponsor=fields["sponsor"],
                    locations=fields["locations"],
                    raw_payload_id=raw.id,
                )
                .on_conflict_do_update(
                    index_elements=[Trial.nct_id],
                    set_={
                        "title": fields["title"],
                        "condition_text": fields["condition_text"],
                        "intervention_text": fields["intervention_text"],
                        "phase": fields["phase"],
                        "status": fields["status"],
                        "why_stopped": fields["why_stopped"],
                        "enrollment_count": fields["enrollment_count"],
                        "eligibility_text": fields["eligibility_text"],
                        "sponsor": fields["sponsor"],
                        "locations": fields["locations"],
                        "raw_payload_id": raw.id,
                    },
                )
            )
            db.execute(stmt)
            _add_provenance(db, f"trial:{nct_id}", "clinicaltrials", nct_id, raw.id)
            count += 1
            if count % 25 == 0:
                db.commit()
                log.info("ingested %d trials", count)
        db.commit()
        log.info("done: %d trials ingested for %r", count, condition_query)
    finally:
        db.close()


def _entity_id(db, source_system: str, source_id: str) -> int | None:
    entity = db.execute(
        select(Entity).where(Entity.source_system == source_system, Entity.source_id == source_id)
    ).scalar_one_or_none()
    return entity.id if entity else None


def _get_or_create_entity(db, entity_type: str, source_system: str, source_id: str, canonical_name: str) -> int:
    entity = db.execute(
        select(Entity).where(
            Entity.entity_type == entity_type,
            Entity.source_system == source_system,
            Entity.source_id == source_id,
        )
    ).scalar_one_or_none()
    if entity is None:
        entity = Entity(
            entity_type=entity_type,
            source_system=source_system,
            source_id=source_id,
            canonical_name=canonical_name,
        )
        db.add(entity)
        db.flush()
    return entity.id


def _resolve_condition_entity_id(db) -> int | None:
    """Labels are pulled by searching indications for the locked disease area,
    so every ingested label is attributable to that condition."""
    result = normalize_disease(settings.disease_area, db)
    if result is None:
        log.warning("could not normalize disease area %r — condition_id will be NULL", settings.disease_area)
        return None
    return _entity_id(db, result["source_system"], result["id"])


def ingest_drug_labels(condition_query: str, max_labels: int):
    db = SessionLocal()
    count = 0
    try:
        condition_entity_id = _resolve_condition_entity_id(db)

        for label in openfda.fetch_labels(condition_query, max_labels=max_labels):
            fields = openfda.extract_fields(label)
            openfda_id = fields.pop("openfda_id")

            raw = _record_raw_payload(db, "openfda", openfda_id, label)

            existing = db.execute(
                select(DrugLabel).where(DrugLabel.raw_payload_id == raw.id)
            ).scalar_one_or_none()
            if existing:
                continue

            drug_entity_id = None
            name = fields["generic_name"] or fields["brand_name"]
            if fields["rxcui"] and name:
                # openFDA carries the RxNorm ID directly when the SPL record has
                # an openfda block — trust it rather than round-tripping to RxNav.
                drug_entity_id = _get_or_create_entity(
                    db, "drug", "RXNORM", fields["rxcui"], name
                )
            elif name:
                # Empty openfda block: fall back to resolving the product name.
                result = normalize_drug(name, db)
                if result:
                    drug_entity_id = _entity_id(db, result["source_system"], result["id"])

            drug_label = DrugLabel(
                drug_id=drug_entity_id,
                condition_id=condition_entity_id,
                brand_name=fields["brand_name"],
                generic_name=fields["generic_name"],
                label_text=fields["label_text"],
                mechanism_text=fields["mechanism_text"],
                approval_date=fields["approval_date"],
                raw_payload_id=raw.id,
            )
            db.add(drug_label)
            db.flush()
            _add_provenance(db, f"drug_label:{drug_label.id}", "openfda", openfda_id, raw.id)
            count += 1
            if count % 25 == 0:
                db.commit()
                log.info("ingested %d drug labels", count)
        db.commit()
        log.info("done: %d drug labels ingested for %r", count, condition_query)
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-trials", type=int, default=300)
    parser.add_argument("--max-labels", type=int, default=200)
    parser.add_argument("--skip-trials", action="store_true")
    parser.add_argument("--skip-labels", action="store_true")
    args = parser.parse_args()

    if not args.skip_trials:
        log.info("ingesting ClinicalTrials.gov studies for %r", settings.clinicaltrials_condition_query)
        ingest_trials(settings.clinicaltrials_condition_query, args.max_trials)

    if not args.skip_labels:
        log.info("ingesting openFDA drug labels for %r", settings.openfda_condition_query)
        ingest_drug_labels(settings.openfda_condition_query, args.max_labels)


if __name__ == "__main__":
    main()
