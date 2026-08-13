"""Entity normalization service.

Maps free text to a canonical ID:
    normalize_drug(text)    -> RxNorm ID
    normalize_disease(text) -> MONDO ID
    normalize_target(text)  -> HGNC ID (gene/target, for Team C's Convoke data)

Each call returns {"id": str, "canonical_name": str, "confidence": float,
"source_system": str} or None if nothing could be resolved.

Results are cached in entity_aliases so repeated lookups of the same free
text (very common — "Ozempic" will be typed thousands of times) don't re-hit
the external ontology APIs. Team C and D should call these functions
directly for any user-entered free text rather than re-implementing
matching logic inline.
"""

import difflib
from typing import TypedDict

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session
from tenacity import retry, stop_after_attempt, wait_exponential

from app.db import SessionLocal
from app.models import Entity, EntityAlias

RXNORM_APPROX_URL = "https://rxnav.nlm.nih.gov/REST/approximateTerm.json"
RXNORM_EXACT_URL = "https://rxnav.nlm.nih.gov/REST/rxcui.json"
RXNORM_PROPERTY_URL = "https://rxnav.nlm.nih.gov/REST/rxcui/{rxcui}/property.json"
OLS_SEARCH_URL = "https://www.ebi.ac.uk/ols4/api/search"
HGNC_SEARCH_URL = "https://rest.genenames.org/search/{query}"


class NormalizeResult(TypedDict):
    id: str
    canonical_name: str
    confidence: float
    source_system: str


def _norm_key(text: str) -> str:
    return text.strip().lower()


def _text_similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a.strip().lower(), b.strip().lower()).ratio()


def _cache_lookup(db: Session, entity_type: str, text: str) -> NormalizeResult | None:
    alias = db.execute(
        select(EntityAlias).where(
            EntityAlias.entity_type == entity_type,
            EntityAlias.alias_text == _norm_key(text),
        )
    ).scalar_one_or_none()
    if alias is None or alias.entity_id is None:
        return None
    entity = db.get(Entity, alias.entity_id)
    if entity is None:
        return None
    return {
        "id": entity.source_id,
        "canonical_name": entity.canonical_name,
        "confidence": float(alias.confidence),
        "source_system": entity.source_system,
    }


def _cache_store(
    db: Session, entity_type: str, text: str, source_system: str, source_id: str, canonical_name: str, confidence: float
) -> None:
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

    existing_alias = db.execute(
        select(EntityAlias).where(
            EntityAlias.entity_type == entity_type,
            EntityAlias.alias_text == _norm_key(text),
        )
    ).scalar_one_or_none()
    if existing_alias is None:
        db.add(
            EntityAlias(
                entity_type=entity_type,
                alias_text=_norm_key(text),
                entity_id=entity.id,
                confidence=confidence,
            )
        )
    db.commit()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def _rxnorm_lookup(text: str) -> tuple[str, str, float] | None:
    with httpx.Client(timeout=10) as client:
        exact = client.get(RXNORM_EXACT_URL, params={"name": text}).json()
        rxcui_list = (exact.get("idGroup") or {}).get("rxnormId") or []
        if rxcui_list:
            rxcui = rxcui_list[0]
            confidence = 1.0
        else:
            approx = client.get(
                RXNORM_APPROX_URL, params={"term": text, "maxEntries": 1}
            ).json()
            candidates = (approx.get("approximateGroup") or {}).get("candidate") or []
            if not candidates:
                return None
            rxcui = candidates[0].get("rxcui")
            score = candidates[0].get("score")
            confidence = min(float(score) / 100.0, 1.0) if score else 0.5
            if not rxcui:
                return None

        prop = client.get(
            RXNORM_PROPERTY_URL.format(rxcui=rxcui), params={"propName": "RxNorm Name"}
        ).json()
        props = (prop.get("propConceptGroup") or {}).get("propConcept") or []
        name = props[0]["propValue"] if props else text
        return rxcui, name, confidence


# ClinicalTrials.gov condition fields routinely carry non-disease values for
# control arms. These have no MONDO equivalent, and letting OLS fuzzy-match
# them produces confident nonsense (e.g. "healthy" -> "immunodeficiency 32B").
NON_DISEASE_TERMS = {
    "healthy",
    "healthy volunteer",
    "healthy volunteers",
    "healthy subjects",
    "healthy adults",
    "healthy participants",
    "normal",
    "none",
    "control",
    "controls",
    "no known condition",
}


def _best_ols_candidate(text: str, docs: list[dict]) -> tuple[str, str, float] | None:
    """Score each candidate against its label *and* its synonyms, keeping the
    best. Ontology labels are often the formal name while the trial uses a
    common synonym ("diabetes mellitus, type 2" vs "type 2 diabetes mellitus"),
    so label-only scoring badly understates real matches."""
    best: tuple[str, str, float] | None = None
    for doc in docs:
        obo_id = doc.get("obo_id")
        label = doc.get("label")
        if not obo_id or not label:
            continue
        # OLS returns cross-referenced terms from other ontologies (HP:, NCIT:)
        # even when scoped to MONDO. Storing those under source_system='MONDO'
        # would hand downstream teams IDs that aren't MONDO at all.
        if not obo_id.startswith("MONDO:"):
            continue
        names = [label, *(doc.get("synonym") or [])]
        score = max(_text_similarity(text, n) for n in names)
        if best is None or score > best[2]:
            best = (obo_id, label, score)
    return best


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def _mondo_lookup(text: str) -> tuple[str, str, float] | None:
    if _norm_key(text) in NON_DISEASE_TERMS:
        return None

    params = {"ontology": "mondo", "fieldList": "obo_id,label,synonym", "rows": 5}
    with httpx.Client(timeout=10) as client:
        # Prefer an exact label/synonym match before falling back to fuzzy search.
        exact = client.get(OLS_SEARCH_URL, params={**params, "q": text, "exact": "true"}).json()
        best = _best_ols_candidate(text, (exact.get("response") or {}).get("docs") or [])
        if best is not None and best[2] >= 0.9:
            return best

        fuzzy = client.get(OLS_SEARCH_URL, params={**params, "q": text}).json()
        fuzzy_best = _best_ols_candidate(text, (fuzzy.get("response") or {}).get("docs") or [])
        candidates = [c for c in (best, fuzzy_best) if c is not None]
        return max(candidates, key=lambda c: c[2]) if candidates else None


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def _hgnc_lookup(text: str) -> tuple[str, str, float] | None:
    with httpx.Client(timeout=10, headers={"Accept": "application/json"}) as client:
        resp = client.get(HGNC_SEARCH_URL.format(query=text)).json()
        docs = (resp.get("response") or {}).get("docs") or []
        if not docs:
            return None
        doc = docs[0]
        hgnc_id = doc.get("hgnc_id")
        symbol = doc.get("symbol") or text
        if not hgnc_id:
            return None
        confidence = 1.0 if symbol.strip().lower() == text.strip().lower() else _text_similarity(text, symbol)
        return hgnc_id, symbol, confidence


def _normalize(
    entity_type: str,
    text: str,
    source_system: str,
    lookup_fn,
    db: Session | None = None,
) -> NormalizeResult | None:
    owns_session = db is None
    db = db or SessionLocal()
    try:
        cached = _cache_lookup(db, entity_type, text)
        if cached is not None:
            return cached

        result = lookup_fn(text)
        if result is None:
            return None
        source_id, canonical_name, confidence = result
        _cache_store(db, entity_type, text, source_system, source_id, canonical_name, confidence)
        return {
            "id": source_id,
            "canonical_name": canonical_name,
            "confidence": confidence,
            "source_system": source_system,
        }
    finally:
        if owns_session:
            db.close()


def normalize_drug(text: str, db: Session | None = None) -> NormalizeResult | None:
    """Map a drug mention (brand or generic) to its RxNorm ID."""
    return _normalize("drug", text, "RXNORM", _rxnorm_lookup, db)


def normalize_disease(text: str, db: Session | None = None) -> NormalizeResult | None:
    """Map a disease/condition mention to its MONDO ID."""
    return _normalize("disease", text, "MONDO", _mondo_lookup, db)


def normalize_target(text: str, db: Session | None = None) -> NormalizeResult | None:
    """Map a target/gene mention to its HGNC ID."""
    return _normalize("target", text, "HGNC", _hgnc_lookup, db)
