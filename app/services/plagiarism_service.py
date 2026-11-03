from sqlalchemy.orm import Session
from app.models.document import Document
from app.utils.text_normalizer import normalize_text, tokenize_with_spans
from app.utils.shingles import create_shingles, find_matched_intervals, find_original_spans
from app.utils.similarity import (
    jaccard_similarity,
    tfidf_cosine_similarity,
    corpus_tfidf_similarities,
)
from app.services import config_service


def _merge_char_spans(spans: list[dict]) -> list[dict]:
    if not spans:
        return []
    ordered = sorted(spans, key=lambda s: (s["start"], -s["end"]))
    merged = [dict(ordered[0])]
    for current in ordered[1:]:
        prev = merged[-1]
        if current["start"] <= prev["end"]:
            if current["end"] > prev["end"]:
                prev["end"] = current["end"]
            if current.get("score", 0) > prev.get("score", 0):
                prev["source_id"] = current.get("source_id")
                prev["source_title"] = current.get("source_title")
                prev["score"] = current.get("score")
        else:
            merged.append(dict(current))
    return merged


def check_plagiarism(text: str, current_doc_id: int | None, db: Session) -> dict:
    shingle_size = config_service.get_config_int("shingle_size", db)
    threshold = config_service.get_config_float("plagiarism_threshold", db)
    jaccard_weight = config_service.get_config_float("jaccard_weight", db)
    tfidf_weight = config_service.get_config_float("tfidf_weight", db)

    tokens = tokenize_with_spans(text)
    words = [w for w, _, _ in tokens]
    normalized = " ".join(words)
    shingles = create_shingles(words, shingle_size)

    query = db.query(Document)
    if current_doc_id is not None:
        query = query.filter(Document.id != current_doc_id)
    other_docs = query.all()

    if not other_docs:
        return {
            "overall_score": 0.0,
            "is_plagiarized": False,
            "coverage_ratio": 0.0,
            "matches": [],
            "highlight_spans": [],
        }

    corpus_words_list = []
    corpus_normalized = []
    for doc in other_docs:
        doc_norm = normalize_text(doc.content)
        corpus_normalized.append(doc_norm)
        corpus_words_list.append(doc_norm.split())

    cosine_scores = corpus_tfidf_similarities(normalized, corpus_normalized)

    matches = []
    all_char_spans = []
    covered_word_indices: set[int] = set()
    best_score = 0.0

    for doc, doc_words, c_score in zip(other_docs, corpus_words_list, cosine_scores):
        doc_shingles = create_shingles(doc_words, shingle_size)
        j_score = jaccard_similarity(shingles, doc_shingles)
        combined = (jaccard_weight * j_score) + (tfidf_weight * c_score)

        if combined > best_score:
            best_score = combined

        if combined >= 0.06:
            intervals = find_matched_intervals(words, doc_words, shingle_size)
            for w_start, w_end in intervals:
                covered_word_indices.update(range(w_start, w_end))

            orig_spans = find_original_spans(text, tokens, doc_words, shingle_size)
            passages = [s["text"] for s in orig_spans]

            doc_highlights = []
            for s in orig_spans:
                span_entry = {
                    "start": s["start"],
                    "end": s["end"],
                    "source_id": doc.id,
                    "source_title": doc.title,
                    "score": round(combined, 4),
                }
                doc_highlights.append(span_entry)
                all_char_spans.append(span_entry)

            matches.append({
                "document_id": doc.id,
                "document_title": doc.title,
                "jaccard_score": round(j_score, 4),
                "cosine_score": round(c_score, 4),
                "combined_score": round(combined, 4),
                "matched_passages": passages[:10],
                "highlight_spans": doc_highlights[:20],
            })

    matches.sort(key=lambda m: m["combined_score"], reverse=True)
    coverage_ratio = round(len(covered_word_indices) / len(words), 4) if words else 0.0
    merged_spans = _merge_char_spans(all_char_spans)

    return {
        "overall_score": round(best_score, 4),
        "is_plagiarized": best_score >= threshold,
        "coverage_ratio": coverage_ratio,
        "matches": matches[:20],
        "highlight_spans": merged_spans,
    }


def compare_texts(source_text: str, suspect_text: str, db: Session) -> dict:
    shingle_size = config_service.get_config_int("shingle_size", db)
    threshold = config_service.get_config_float("plagiarism_threshold", db)
    jaccard_weight = config_service.get_config_float("jaccard_weight", db)
    tfidf_weight = config_service.get_config_float("tfidf_weight", db)

    suspect_tokens = tokenize_with_spans(suspect_text)
    suspect_words = [w for w, _, _ in suspect_tokens]
    suspect_norm = " ".join(suspect_words)

    source_norm = normalize_text(source_text)
    source_words = source_norm.split()

    j_score = jaccard_similarity(
        create_shingles(suspect_words, shingle_size),
        create_shingles(source_words, shingle_size),
    )
    c_score = tfidf_cosine_similarity(suspect_norm, source_norm)
    combined = (jaccard_weight * j_score) + (tfidf_weight * c_score)

    intervals = find_matched_intervals(suspect_words, source_words, shingle_size)
    covered: set[int] = set()
    for w_start, w_end in intervals:
        covered.update(range(w_start, w_end))

    orig_spans = find_original_spans(suspect_text, suspect_tokens, source_words, shingle_size)
    coverage_ratio = round(len(covered) / len(suspect_words), 4) if suspect_words else 0.0

    return {
        "jaccard_score": round(j_score, 4),
        "cosine_score": round(c_score, 4),
        "combined_score": round(combined, 4),
        "is_plagiarized": combined >= threshold,
        "coverage_ratio": coverage_ratio,
        "matched_passages": [s["text"] for s in orig_spans[:15]],
        "highlight_spans": [
            {
                "start": s["start"],
                "end": s["end"],
                "source_id": 0,
                "source_title": "Reference Text",
                "score": round(combined, 4),
            }
            for s in orig_spans
        ],
    }
