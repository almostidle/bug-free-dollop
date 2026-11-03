import math
import time
from sqlalchemy.orm import Session
from app.models.config import DetectorConfig
from app.exceptions import AppException


DEFAULT_CONFIGS: list[tuple[str, str, str]] = [
    ("shingle_size", "5", "Number of words per shingle for plagiarism detection"),
    ("plagiarism_threshold", "0.3", "Minimum combined score to flag as plagiarized"),
    ("ai_threshold", "0.5", "Minimum AI score to flag as AI-generated"),
    ("min_text_length", "50", "Minimum character count required for analysis"),
    ("jaccard_weight", "0.5", "Weight of Jaccard similarity in combined plagiarism score"),
    ("tfidf_weight", "0.5", "Weight of TF-IDF cosine similarity in combined plagiarism score"),
    ("weight_burstiness", "0.25", "Weight for sentence length variance metric in AI detection"),
    ("weight_lexical_diversity", "0.25", "Weight for type-token ratio metric in AI detection"),
    ("weight_repeated_ngrams", "0.25", "Weight for repeated n-gram ratio metric in AI detection"),
    ("weight_avg_sentence_length", "0.15", "Weight for average sentence length metric in AI detection"),
    ("weight_punctuation_patterns", "0.10", "Weight for punctuation diversity metric in AI detection"),
    ("ngram_size", "3", "N-gram size for the repeated n-gram analysis"),
]

_INT_BOUNDS: dict[str, tuple[int, int]] = {
    "shingle_size": (2, 20),
    "min_text_length": (10, 10000),
    "ngram_size": (2, 10),
}

_FLOAT_BOUNDS: dict[str, tuple[float, float]] = {
    "plagiarism_threshold": (0.01, 1.0),
    "ai_threshold": (0.01, 1.0),
    "jaccard_weight": (0.0, 1.0),
    "tfidf_weight": (0.0, 1.0),
    "weight_burstiness": (0.0, 1.0),
    "weight_lexical_diversity": (0.0, 1.0),
    "weight_repeated_ngrams": (0.0, 1.0),
    "weight_avg_sentence_length": (0.0, 1.0),
    "weight_punctuation_patterns": (0.0, 1.0),
}

_cache: dict[str, str] = {}
_cache_time: float = 0
_CACHE_TTL = 300


def ensure_default_config(db: Session) -> None:
    existing = {row.key for row in db.query(DetectorConfig.key).all()}
    added = False
    for key, value, description in DEFAULT_CONFIGS:
        if key not in existing:
            db.add(DetectorConfig(key=key, value=value, description=description))
            added = True
    if added:
        db.commit()
        _invalidate_cache()


def _validate_config_value(key: str, value: str) -> str:
    cleaned = value.strip()
    if key in _INT_BOUNDS:
        low, high = _INT_BOUNDS[key]
        try:
            parsed = int(cleaned)
        except ValueError:
            raise AppException(400, f"Config '{key}' must be an integer between {low} and {high}")
        if not (low <= parsed <= high):
            raise AppException(400, f"Config '{key}' must be between {low} and {high}")
        return str(parsed)

    if key in _FLOAT_BOUNDS:
        low, high = _FLOAT_BOUNDS[key]
        try:
            parsed = float(cleaned)
        except ValueError:
            raise AppException(400, f"Config '{key}' must be a number between {low} and {high}")
        if math.isnan(parsed) or math.isinf(parsed) or not (low <= parsed <= high):
            raise AppException(400, f"Config '{key}' must be between {low} and {high}")
        return str(round(parsed, 4))

    return cleaned


def _refresh_cache(db: Session):
    global _cache, _cache_time
    rows = db.query(DetectorConfig).all()
    if not rows:
        ensure_default_config(db)
        rows = db.query(DetectorConfig).all()
    _cache = {row.key: row.value for row in rows}
    _cache_time = time.time()


def get_all_config(db: Session) -> list[DetectorConfig]:
    ensure_default_config(db)
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
    ensure_default_config(db)
    row = db.query(DetectorConfig).filter(DetectorConfig.key == key).first()
    if not row:
        raise AppException(404, f"Config key '{key}' not found")
    validated = _validate_config_value(key, value)
    row.value = validated
    db.commit()
    db.refresh(row)
    _invalidate_cache()
    return row


def reset_default_config(db: Session) -> list[DetectorConfig]:
    ensure_default_config(db)
    defaults_map = {k: (v, d) for k, v, d in DEFAULT_CONFIGS}
    rows = db.query(DetectorConfig).all()
    for row in rows:
        if row.key in defaults_map:
            row.value, row.description = defaults_map[row.key]
    db.commit()
    _invalidate_cache()
    return get_all_config(db)


def _invalidate_cache():
    global _cache, _cache_time
    _cache = {}
    _cache_time = 0
