from sqlalchemy import Column, Integer, String, Text
from app.db.base import Base


class DetectorConfig(Base):
    __tablename__ = "detector_config"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
