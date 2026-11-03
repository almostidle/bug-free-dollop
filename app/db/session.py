from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class Settings(BaseSettings):
    database_url: str = "sqlite:///./plagiarism_detector.db"
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    import app.models  # noqa: F401 - register ORM models
    from app.db.base import Base
    from app.services.config_service import ensure_default_config

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        ensure_default_config(db)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
