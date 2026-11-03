from sqlalchemy.orm import Session
from app.models.document import Document
from app.utils.text_normalizer import normalize_text
from app.utils.shingles import create_shingles, find_matched_passages
from app.utils.similarity import jaccard_similarity, tfidf_cosine_similarity
from app.services import config_service


def check_plagiarism(text: str, current_doc_id: int, db: Session) -> dict:
    shingle_size = config_service.get_config_int("shingle_size", db)
    threshold = config_service.get_config_float("plagiarism_threshold", db)
    jaccard_weight = config_service.get_config_float("jaccard_weight", db)
    tfidf_weight = config_service.get_config_float("tfidf_weight", db)

    normalized = normalize_text(text)
    words = normalized.split()
    shingles = create_shingles(words, shingle_size)

    other_docs = db.query(Document).filter(Document.id != current_doc_id).all()

    matches = []
    best_score = 0.0

    for doc in other_docs:
        doc_normalized = normalize_text(doc.content)
        doc_words = doc_normalized.split()
        doc_shingles = create_shingles(doc_words, shingle_size)

        j_score = jaccard_similarity(shingles, doc_shingles)
        c_score = tfidf_cosine_similarity(normalized, doc_normalized)
        combined = (jaccard_weight * j_score) + (tfidf_weight * c_score)

        if combined > 0.01:
            passages = find_matched_passages(words, doc_words, shingle_size)
            matches.append({
                "document_id": doc.id,
                "document_title": doc.title,
                "jaccard_score": round(j_score, 4),
                "cosine_score": round(c_score, 4),
                "combined_score": round(combined, 4),
                "matched_passages": passages[:10],
            })
            if combined > best_score:
                best_score = combined

    matches.sort(key=lambda m: m["combined_score"], reverse=True)

    return {
        "overall_score": round(best_score, 4),
        "is_plagiarized": best_score >= threshold,
        "matches": matches[:20],
    }
