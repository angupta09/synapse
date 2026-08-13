"""Embed trial descriptions + eligibility criteria and drug mechanism text
into pgvector columns for semantic similarity search (Team C).

Usage:
    python -m app.ingestion.backfill_embeddings
"""

import logging

from sqlalchemy import select

from app.db import SessionLocal
from app.embeddings import embed_text
from app.models import DrugLabel, Trial

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("embed")


def embed_trials():
    db = SessionLocal()
    count = 0
    try:
        trials = db.execute(select(Trial).where(Trial.embedding.is_(None))).scalars().all()
        for trial in trials:
            text = " ".join(filter(None, [trial.title, trial.eligibility_text]))
            trial.embedding = embed_text(text)
            count += 1
            if count % 25 == 0:
                db.commit()
                log.info("embedded %d trials", count)
        db.commit()
        log.info("done: %d trials embedded", count)
    finally:
        db.close()


def embed_drug_labels():
    db = SessionLocal()
    count = 0
    try:
        labels = db.execute(select(DrugLabel).where(DrugLabel.embedding.is_(None))).scalars().all()
        for label in labels:
            text = " ".join(filter(None, [label.label_text, label.mechanism_text]))
            label.embedding = embed_text(text)
            count += 1
            if count % 25 == 0:
                db.commit()
                log.info("embedded %d drug labels", count)
        db.commit()
        log.info("done: %d drug labels embedded", count)
    finally:
        db.close()


def main():
    log.info("embedding trial text")
    embed_trials()
    log.info("embedding drug label text")
    embed_drug_labels()


if __name__ == "__main__":
    main()
