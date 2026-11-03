from fastapi import APIRouter, Depends, Form, File, UploadFile
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.document import (
    AnalyzeResponse,
    CompareRequest,
    CompareResponse,
    CorpusStats,
    DocumentDetail,
    DocumentSummary,
)
from app.services import document_service
from app.exceptions import AppException


router = APIRouter(prefix="/api/documents", tags=["documents"])

_ALLOWED_EXTENSIONS = (".txt", ".md")


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    text: str | None = Form(None),
    title: str | None = Form(None),
    save_to_corpus: bool = Form(True),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    if file and file.filename:
        if not file.filename.lower().endswith(_ALLOWED_EXTENSIONS):
            raise AppException(400, "Only .txt and .md files are supported")
        raw = await file.read()
        content = raw.decode("utf-8", errors="replace")
        doc_title = (title or "").strip() or file.filename
    elif text:
        content = text
        doc_title = (title or "").strip() or "Untitled Submission"
    else:
        raise AppException(400, "Provide either text or a .txt/.md file")

    return document_service.analyze_document(
        content,
        doc_title,
        db,
        save_to_corpus=save_to_corpus,
    )


@router.post("/compare", response_model=CompareResponse)
def compare(body: CompareRequest, db: Session = Depends(get_db)):
    return document_service.compare_documents(body.source_text, body.suspect_text, db)


@router.get("/stats", response_model=CorpusStats)
def stats(db: Session = Depends(get_db)):
    return document_service.get_corpus_stats(db)


@router.get("/history", response_model=list[DocumentSummary])
def history(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    return document_service.get_history(db, limit=limit, offset=offset)


@router.get("/{doc_id}", response_model=DocumentDetail)
def get_document(doc_id: int, db: Session = Depends(get_db)):
    return document_service.get_document(doc_id, db)


@router.delete("/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    return document_service.delete_document(doc_id, db)
