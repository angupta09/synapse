import datetime as dt

from pydantic import BaseModel


class ProvenanceOut(BaseModel):
    source_record_type: str
    source_record_ids: list[str]


class TrialInternalOut(BaseModel):
    nct_id: str
    title: str | None
    condition_text: list[str]
    condition_ids: list[str]
    intervention_text: list[str]
    intervention_ids: list[str]
    phase: str | None
    status: str | None
    why_stopped: str | None
    enrollment_count: int | None
    eligibility_text: str | None
    sponsor: str | None
    locations: list[dict]
    provenance: ProvenanceOut


class TrialPublicOut(BaseModel):
    """The safe, read-only subset for the Patient Portal.

    Deliberately excludes: why_stopped, sponsor, eligibility_text (may contain
    operationally-sensitive detail) and any target/gene (Convoke-derived)
    linkage. Only fields a patient-facing trial finder needs.
    """

    nct_id: str
    title: str | None
    condition_text: list[str]
    intervention_text: list[str]
    phase: str | None
    status: str | None
    locations: list[dict]
    provenance: ProvenanceOut


class DrugLabelInternalOut(BaseModel):
    id: int
    drug_id: str | None
    brand_name: str | None
    generic_name: str | None
    condition_id: str | None
    label_text: str | None
    mechanism_text: str | None
    approval_date: dt.date | None
    provenance: ProvenanceOut


class DrugLabelPublicOut(BaseModel):
    id: int
    brand_name: str | None
    generic_name: str | None
    label_text: str | None
    provenance: ProvenanceOut


class SimilarTrialOut(BaseModel):
    nct_id: str
    title: str | None
    similarity: float


class NormalizeRequest(BaseModel):
    type: str  # "drug" | "disease" | "target"
    text: str


class NormalizeResponse(BaseModel):
    id: str | None
    canonical_name: str | None
    confidence: float | None
    source_system: str | None
    resolved: bool
