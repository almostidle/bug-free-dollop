from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services import demo_service


router = APIRouter(prefix="/api/demo", tags=["demo"])


@router.get("/samples")
def list_samples():
    return demo_service.get_sample_presets()


@router.post("/seed")
def seed_corpus(
    reset: bool = Query(False, description="Clear existing documents and restore clean reference corpus"),
    db: Session = Depends(get_db),
):
    return demo_service.seed_reference_corpus(db, reset=reset)
