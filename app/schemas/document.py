from datetime import datetime
from pydantic import BaseModel


class MatchResult(BaseModel):
    document_id: int
    document_title: str
    jaccard_score: float
    cosine_score: float
    combined_score: float
    matched_passages: list[str]


class PlagiarismResult(BaseModel):
    overall_score: float
    is_plagiarized: bool
    matches: list[MatchResult]


class MetricDetail(BaseModel):
    score: float
    raw_value: float
    description: str


class AIDetectionResult(BaseModel):
    overall_score: float
    is_ai_generated: bool
    metrics: dict[str, MetricDetail]


class AnalyzeResponse(BaseModel):
    id: int
    title: str
    plagiarism: PlagiarismResult
    ai_detection: AIDetectionResult
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentSummary(BaseModel):
    id: int
    title: str
    plagiarism_score: float | None = None
    ai_score: float | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentDetail(BaseModel):
    id: int
    title: str
    content: str
    plagiarism_score: float | None = None
    ai_score: float | None = None
    results: dict | None = None
    created_at: datetime

    class Config:
        from_attributes = True
