from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine


def jaccard_similarity(shingles_a: set, shingles_b: set) -> float:
    if not shingles_a and not shingles_b:
        return 0.0
    intersection = shingles_a & shingles_b
    union = shingles_a | shingles_b
    if not union:
        return 0.0
    return len(intersection) / len(union)


def tfidf_cosine_similarity(text_a: str, text_b: str) -> float:
    if not text_a.strip() or not text_b.strip():
        return 0.0
    for stop in ("english", None):
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, stop_words=stop)
        try:
            tfidf_matrix = vectorizer.fit_transform([text_a, text_b])
            sim = sklearn_cosine(tfidf_matrix[0:1], tfidf_matrix[1:2])
            return float(sim[0][0])
        except ValueError:
            continue
    return 0.0


def corpus_tfidf_similarities(query_text: str, corpus_texts: list[str]) -> list[float]:
    """Compute TF-IDF cosine similarities of query_text against all corpus_texts in a single corpus fit."""
    if not corpus_texts:
        return []
    if not query_text.strip():
        return [0.0] * len(corpus_texts)

    for stop in ("english", None):
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, stop_words=stop)
        try:
            tfidf_matrix = vectorizer.fit_transform([query_text, *corpus_texts])
            sims = sklearn_cosine(tfidf_matrix[0:1], tfidf_matrix[1:])[0]
            return [float(s) for s in sims]
        except ValueError:
            continue

    return [0.0] * len(corpus_texts)
