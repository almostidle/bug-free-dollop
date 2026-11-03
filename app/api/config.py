from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.config import ConfigOut, ConfigUpdate
from app.services import config_service


router = APIRouter(prefix="/api/config", tags=["config"])


@router.get("", response_model=list[ConfigOut])
def get_all(db: Session = Depends(get_db)):
    return config_service.get_all_config(db)


@router.post("/reset", response_model=list[ConfigOut])
def reset_defaults(db: Session = Depends(get_db)):
    return config_service.reset_default_config(db)


@router.put("/{key}", response_model=ConfigOut)
def update(key: str, body: ConfigUpdate, db: Session = Depends(get_db)):
    return config_service.update_config(key, body.value, db)
