import datetime as dt

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    ARRAY,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

EMBEDDING_DIM = 384


class RawPayload(Base):
    __tablename__ = "raw_payloads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String, nullable=False)
    source_record_id: Mapped[str] = mapped_column(String, nullable=False)
    fetched_at: Mapped[dt.datetime] = mapped_column(default=dt.datetime.utcnow)
    storage_backend: Mapped[str] = mapped_column(String, nullable=False)
    storage_path: Mapped[str] = mapped_column(String, nullable=False)
    checksum: Mapped[str] = mapped_column(String, nullable=False)


class Entity(Base):
    __tablename__ = "entities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_type: Mapped[str] = mapped_column(String, nullable=False)
    source_system: Mapped[str] = mapped_column(String, nullable=False)
    source_id: Mapped[str] = mapped_column(String, nullable=False)
    canonical_name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(default=dt.datetime.utcnow)


class EntityAlias(Base):
    __tablename__ = "entity_aliases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_type: Mapped[str] = mapped_column(String, nullable=False)
    alias_text: Mapped[str] = mapped_column(String, nullable=False)
    entity_id: Mapped[int | None] = mapped_column(ForeignKey("entities.id"))
    confidence: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False)
    resolved_at: Mapped[dt.datetime] = mapped_column(default=dt.datetime.utcnow)


class Trial(Base):
    __tablename__ = "trials"

    nct_id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str | None] = mapped_column(Text)
    condition_text: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    intervention_text: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    phase: Mapped[str | None] = mapped_column(String)
    status: Mapped[str | None] = mapped_column(String)
    why_stopped: Mapped[str | None] = mapped_column(Text)
    enrollment_count: Mapped[int | None] = mapped_column(Integer)
    eligibility_text: Mapped[str | None] = mapped_column(Text)
    sponsor: Mapped[str | None] = mapped_column(String)
    locations: Mapped[list] = mapped_column(JSONB, default=list)
    embedding = mapped_column(Vector(EMBEDDING_DIM), nullable=True)
    raw_payload_id: Mapped[int | None] = mapped_column(ForeignKey("raw_payloads.id"))
    created_at: Mapped[dt.datetime] = mapped_column(default=dt.datetime.utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(default=dt.datetime.utcnow)

    conditions: Mapped[list["TrialCondition"]] = relationship(
        back_populates="trial", cascade="all, delete-orphan"
    )
    interventions: Mapped[list["TrialIntervention"]] = relationship(
        back_populates="trial", cascade="all, delete-orphan"
    )


class TrialCondition(Base):
    __tablename__ = "trial_conditions"

    trial_nct_id: Mapped[str] = mapped_column(
        ForeignKey("trials.nct_id", ondelete="CASCADE"), primary_key=True
    )
    entity_id: Mapped[int] = mapped_column(ForeignKey("entities.id"), primary_key=True)

    trial: Mapped[Trial] = relationship(back_populates="conditions")
    entity: Mapped[Entity] = relationship()


class TrialIntervention(Base):
    __tablename__ = "trial_interventions"

    trial_nct_id: Mapped[str] = mapped_column(
        ForeignKey("trials.nct_id", ondelete="CASCADE"), primary_key=True
    )
    entity_id: Mapped[int] = mapped_column(ForeignKey("entities.id"), primary_key=True)

    trial: Mapped[Trial] = relationship(back_populates="interventions")
    entity: Mapped[Entity] = relationship()


class DrugLabel(Base):
    __tablename__ = "drug_labels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    drug_id: Mapped[int | None] = mapped_column(ForeignKey("entities.id"))
    brand_name: Mapped[str | None] = mapped_column(String)
    generic_name: Mapped[str | None] = mapped_column(String)
    condition_id: Mapped[int | None] = mapped_column(ForeignKey("entities.id"))
    label_text: Mapped[str | None] = mapped_column(Text)
    mechanism_text: Mapped[str | None] = mapped_column(Text)
    approval_date: Mapped[dt.date | None] = mapped_column(Date)
    embedding = mapped_column(Vector(EMBEDDING_DIM), nullable=True)
    raw_payload_id: Mapped[int | None] = mapped_column(ForeignKey("raw_payloads.id"))
    created_at: Mapped[dt.datetime] = mapped_column(default=dt.datetime.utcnow)


class Provenance(Base):
    __tablename__ = "provenance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    derived_claim_id: Mapped[str] = mapped_column(String, nullable=False)
    source_record_type: Mapped[str] = mapped_column(String, nullable=False)
    source_record_id: Mapped[str] = mapped_column(String, nullable=False)
    raw_payload_id: Mapped[int | None] = mapped_column(ForeignKey("raw_payloads.id"))
    created_at: Mapped[dt.datetime] = mapped_column(default=dt.datetime.utcnow)
