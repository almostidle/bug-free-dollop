from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.document import Document
from app.services import config_service, plagiarism_service, ai_detection_service
from app.exceptions import AppException


def analyze_document(
    text: str,
    title: str,
    db: Session,
    save_to_corpus: bool = True,
) -> dict:
    min_length = config_service.get_config_int("min_text_length", db)
    if len(text.strip()) < min_length:
        raise AppException(400, f"Text must be at least {min_length} characters long")

    plag_result = plagiarism_service.check_plagiarism(text, None, db)
    ai_result = ai_detection_service.detect_ai_content(text, db)

    if save_to_corpus:
        doc = Document(
            title=title,
            content=text,
            plagiarism_score=plag_result["overall_score"],
            ai_score=ai_result["overall_score"],
            results={"plagiarism": plag_result, "ai_detection": ai_result},
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        doc_id = doc.id
        created_at = doc.created_at
    else:
        doc_id = 0
        created_at = datetime.now(timezone.utc)

    return {
        "id": doc_id,
        "title": title,
        "content": text,
        "saved": save_to_corpus,
        "plagiarism": plag_result,
        "ai_detection": ai_result,
        "created_at": created_at,
    }


def compare_documents(source_text: str, suspect_text: str, db: Session) -> dict:
    min_length = config_service.get_config_int("min_text_length", db)
    if len(source_text.strip()) < min_length or len(suspect_text.strip()) < min_length:
        raise AppException(
            400,
            f"Both texts must be at least {min_length} characters long",
        )
    comparison = plagiarism_service.compare_texts(source_text, suspect_text, db)
    comparison["suspect_text"] = suspect_text
    return comparison


def get_document(doc_id: int, db: Session) -> Document:
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise AppException(404, f"Document {doc_id} not found")
    return doc


def delete_document(doc_id: int, db: Session) -> dict:
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise AppException(404, f"Document {doc_id} not found")
    db.delete(doc)
    db.commit()
    return {"deleted": True, "id": doc_id}


def get_history(db: Session, limit: int = 50, offset: int = 0) -> list[dict]:
    docs = (
        db.query(Document)
        .order_by(Document.created_at.desc(), Document.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": d.id,
            "title": d.title,
            "word_count": len(d.content.split()) if d.content else 0,
            "plagiarism_score": d.plagiarism_score,
            "ai_score": d.ai_score,
            "created_at": d.created_at,
        }
        for d in docs
    ]


def get_corpus_stats(db: Session) -> dict:
    plag_threshold = config_service.get_config_float("plagiarism_threshold", db)
    ai_threshold = config_service.get_config_float("ai_threshold", db)
    docs = db.query(Document).all()
    total = len(docs)
    if total == 0:
        return {
            "total_documents": 0,
            "flagged_plagiarism": 0,
            "flagged_ai": 0,
            "avg_plagiarism_score": 0.0,
            "avg_ai_score": 0.0,
            "plagiarism_threshold": plag_threshold,
            "ai_threshold": ai_threshold,
        }

    plag_scores = [d.plagiarism_score for d in docs if d.plagiarism_score is not None]
    ai_scores = [d.ai_score for d in docs if d.ai_score is not None]

    return {
        "total_documents": total,
        "flagged_plagiarism": sum(1 for s in plag_scores if s >= plag_threshold),
        "flagged_ai": sum(1 for s in ai_scores if s >= ai_threshold),
        "avg_plagiarism_score": round(sum(plag_scores) / len(plag_scores), 4) if plag_scores else 0.0,
        "avg_ai_score": round(sum(ai_scores) / len(ai_scores), 4) if ai_scores else 0.0,
        "plagiarism_threshold": plag_threshold,
        "ai_threshold": ai_threshold,
    }
