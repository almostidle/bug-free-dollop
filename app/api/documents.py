from fastapi import APIRouter, Depends, Form, File, UploadFile
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.document import AnalyzeResponse, DocumentDetail, DocumentSummary
from app.services import document_service
from app.exceptions import AppException


router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    text: str | None = Form(None),
    title: str | None = Form(None),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    if file and file.filename:
        if not file.filename.endswith(".txt"):
            raise AppException(400, "Only .txt files are supported")
        raw = await file.read()
        content = raw.decode("utf-8", errors="replace")
        doc_title = title or file.filename
    elif text:
        content = text
        doc_title = title or "Untitled"
    else:
        raise AppException(400, "Provide either text or a .txt file")

    result = document_service.analyze_document(content, doc_title, db)
    return result


@router.get("/history", response_model=list[DocumentSummary])
def history(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    return document_service.get_history(db, limit=limit, offset=offset)


@router.get("/{doc_id}", response_model=DocumentDetail)
def get_document(doc_id: int, db: Session = Depends(get_db)):
    return document_service.get_document(doc_id, db)
