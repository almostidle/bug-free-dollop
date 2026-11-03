import time
from sqlalchemy.orm import Session
from app.models.config import DetectorConfig
from app.exceptions import AppException


_cache: dict[str, str] = {}
_cache_time: float = 0
_CACHE_TTL = 300


def _refresh_cache(db: Session):
    global _cache, _cache_time
    rows = db.query(DetectorConfig).all()
    _cache = {row.key: row.value for row in rows}
    _cache_time = time.time()


def get_all_config(db: Session) -> list[DetectorConfig]:
    return db.query(DetectorConfig).order_by(DetectorConfig.key).all()


def get_config_value(key: str, db: Session) -> str:
    global _cache, _cache_time
    if not _cache or (time.time() - _cache_time) > _CACHE_TTL:
        _refresh_cache(db)
    if key not in _cache:
        raise AppException(404, f"Config key '{key}' not found")
    return _cache[key]


def get_config_float(key: str, db: Session) -> float:
    return float(get_config_value(key, db))


def get_config_int(key: str, db: Session) -> int:
    return int(get_config_value(key, db))


def update_config(key: str, value: str, db: Session) -> DetectorConfig:
    row = db.query(DetectorConfig).filter(DetectorConfig.key == key).first()
    if not row:
        raise AppException(404, f"Config key '{key}' not found")
    row.value = value
    db.commit()
    db.refresh(row)
    _invalidate_cache()
    return row


def _invalidate_cache():
    global _cache, _cache_time
    _cache = {}
    _cache_time = 0
