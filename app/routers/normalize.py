from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.normalize import normalize_disease, normalize_drug, normalize_target
from app.schemas import NormalizeRequest, NormalizeResponse

router = APIRouter(prefix="/internal", tags=["normalize"])

_DISPATCH = {
    "drug": normalize_drug,
    "disease": normalize_disease,
    "target": normalize_target,
}


@router.post("/normalize", response_model=NormalizeResponse)
def normalize(body: NormalizeRequest, db: Session = Depends(get_db)) -> NormalizeResponse:
    fn = _DISPATCH.get(body.type)
    if fn is None:
        raise HTTPException(status_code=400, detail="type must be one of: drug, disease, target")

    result = fn(body.text, db)
    if result is None:
        return NormalizeResponse(id=None, canonical_name=None, confidence=None, source_system=None, resolved=False)
    return NormalizeResponse(
        id=result["id"],
        canonical_name=result["canonical_name"],
        confidence=result["confidence"],
        source_system=result["source_system"],
        resolved=True,
    )
