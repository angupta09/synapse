from app.models import Provenance, RawPayload
from app.provenance import get_provenance


def test_provenance_traces_derived_claim_to_raw_source(db_session):
    raw = RawPayload(
        source="clinicaltrials",
        source_record_id="NCT99999999",
        storage_backend="local",
        storage_path="/tmp/does-not-matter.json",
        checksum="deadbeef",
    )
    db_session.add(raw)
    db_session.flush()

    db_session.add(
        Provenance(
            derived_claim_id="trial:NCT99999999",
            source_record_type="clinicaltrials",
            source_record_id="NCT99999999",
            raw_payload_id=raw.id,
        )
    )
    db_session.flush()

    result = get_provenance(db_session, "trial:NCT99999999")
    assert result["source_record_type"] == "clinicaltrials"
    assert result["source_record_ids"] == ["NCT99999999"]


def test_provenance_missing_claim_returns_empty(db_session):
    result = get_provenance(db_session, "trial:DOES_NOT_EXIST")
    assert result["source_record_ids"] == []
