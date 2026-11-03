from datetime import datetime
from pydantic import BaseModel, ConfigDict


class HighlightSpan(BaseModel):
    start: int
    end: int
    source_id: int | None = None
    source_title: str | None = None
    score: float | None = None


class MatchResult(BaseModel):
    document_id: int
    document_title: str
    jaccard_score: float
    cosine_score: float
    combined_score: float
    matched_passages: list[str]
    highlight_spans: list[HighlightSpan] = []


class PlagiarismResult(BaseModel):
    overall_score: float
    is_plagiarized: bool
    coverage_ratio: float = 0.0
    matches: list[MatchResult]
    highlight_spans: list[HighlightSpan] = []


class MetricDetail(BaseModel):
    score: float
    raw_value: float
    description: str


class SentenceItem(BaseModel):
    index: int
    text: str
    word_count: int
    deviation: float


class AIDetectionResult(BaseModel):
    overall_score: float
    is_ai_generated: bool
    word_count: int = 0
    sentence_count: int = 0
    metrics: dict[str, MetricDetail]
    sentences: list[SentenceItem] = []


class AnalyzeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    saved: bool = True
    plagiarism: PlagiarismResult
    ai_detection: AIDetectionResult
    created_at: datetime


class CompareRequest(BaseModel):
    source_text: str
    suspect_text: str


class CompareResponse(BaseModel):
    jaccard_score: float
    cosine_score: float
    combined_score: float
    is_plagiarized: bool
    coverage_ratio: float
    matched_passages: list[str]
    highlight_spans: list[HighlightSpan]
    suspect_text: str


class CorpusStats(BaseModel):
    total_documents: int
    flagged_plagiarism: int
    flagged_ai: int
    avg_plagiarism_score: float
    avg_ai_score: float
    plagiarism_threshold: float
    ai_threshold: float


class DocumentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    word_count: int = 0
    plagiarism_score: float | None = None
    ai_score: float | None = None
    created_at: datetime


class DocumentDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    plagiarism_score: float | None = None
    ai_score: float | None = None
    results: dict | None = None
    created_at: datetime
