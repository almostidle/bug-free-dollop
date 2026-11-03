from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine


def jaccard_similarity(shingles_a: set, shingles_b: set) -> float:
    if not shingles_a and not shingles_b:
        return 0.0
    intersection = shingles_a & shingles_b
    union = shingles_a | shingles_b
    return len(intersection) / len(union)


def tfidf_cosine_similarity(text_a: str, text_b: str) -> float:
    vectorizer = TfidfVectorizer()
    try:
        tfidf_matrix = vectorizer.fit_transform([text_a, text_b])
    except ValueError:
        return 0.0
    sim = sklearn_cosine(tfidf_matrix[0:1], tfidf_matrix[1:2])
    return float(sim[0][0])
