from sqlalchemy.orm import Session
from app.models.document import Document
from app.services import config_service, plagiarism_service, ai_detection_service
from app.exceptions import AppException


def analyze_document(text: str, title: str, db: Session) -> dict:
    min_length = config_service.get_config_int("min_text_length", db)
    if len(text.strip()) < min_length:
        raise AppException(400, f"Text must be at least {min_length} characters long")

    doc = Document(title=title, content=text)
    db.add(doc)
    db.commit()
    db.refresh(doc)

    plag_result = plagiarism_service.check_plagiarism(text, doc.id, db)
    ai_result = ai_detection_service.detect_ai_content(text, db)

    doc.plagiarism_score = plag_result["overall_score"]
    doc.ai_score = ai_result["overall_score"]
    doc.results = {"plagiarism": plag_result, "ai_detection": ai_result}
    db.commit()
    db.refresh(doc)

    return {
        "id": doc.id,
        "title": doc.title,
        "plagiarism": plag_result,
        "ai_detection": ai_result,
        "created_at": doc.created_at,
    }


def get_document(doc_id: int, db: Session) -> Document:
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise AppException(404, f"Document {doc_id} not found")
    return doc


def get_history(db: Session, limit: int = 50, offset: int = 0) -> list[Document]:
    return (
        db.query(Document)
        .order_by(Document.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
