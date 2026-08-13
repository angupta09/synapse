"""Unit tests for the normalize_* service. External ontology lookups are
monkeypatched so these run without network access; the cache read/write
path is exercised against the real DB.
"""

import uuid

import pytest
from sqlalchemy import text

from app import normalize


@pytest.fixture()
def novel_term(db_session):
    """A term guaranteed not to be in the alias cache already, so the test
    exercises the real write-then-read path instead of colliding with
    whatever a previous ingestion run cached."""
    term = f"zz-test-drug-{uuid.uuid4().hex[:8]}"
    yield term
    db_session.execute(
        text("DELETE FROM entity_aliases WHERE alias_text = :t"), {"t": term}
    )
    db_session.commit()


def test_normalize_drug_caches_result(db_session, novel_term, monkeypatch):
    calls = {"n": 0}

    def fake_lookup(text):
        calls["n"] += 1
        return ("161", "Metformin", 1.0)

    monkeypatch.setattr(normalize, "_rxnorm_lookup", fake_lookup)

    first = normalize.normalize_drug(novel_term, db_session)
    second = normalize.normalize_drug(novel_term, db_session)

    assert first == {"id": "161", "canonical_name": "Metformin", "confidence": 1.0, "source_system": "RXNORM"}
    assert second == first
    assert calls["n"] == 1  # second call hit the cache, not the network


def test_normalize_disease_returns_none_when_unresolved(db_session, monkeypatch):
    monkeypatch.setattr(normalize, "_mondo_lookup", lambda text: None)
    result = normalize.normalize_disease("not a real disease xyzzy", db_session)
    assert result is None


def test_normalize_target_dispatch(db_session, monkeypatch):
    monkeypatch.setattr(normalize, "_hgnc_lookup", lambda text: ("HGNC:3236", "EGFR", 1.0))
    result = normalize.normalize_target("EGFR", db_session)
    assert result["id"] == "HGNC:3236"
    assert result["source_system"] == "HGNC"
