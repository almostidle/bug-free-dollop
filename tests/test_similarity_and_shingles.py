from app.utils.text_normalizer import normalize_text, tokenize_with_spans
from app.utils.shingles import create_shingles, find_matched_intervals, find_original_spans
from app.utils.similarity import (
    jaccard_similarity,
    tfidf_cosine_similarity,
    corpus_tfidf_similarities,
)


def test_tokenize_with_spans_matches_normalize_text():
    raw = "Transformers—introduced in 2017!—rely on self-attention, keys, & values."
    norm_words = normalize_text(raw).split()
    tokens = tokenize_with_spans(raw)

    assert [w for w, _, _ in tokens] == norm_words
    for _, start, end in tokens:
        assert 0 <= start < end <= len(raw)


def test_find_original_spans_preserves_exact_slices():
    source = (
        "The Transformer architecture dispenses entirely with recurrence and convolutions, "
        "relying instead on scaled dot-product self-attention mechanisms."
    )
    suspect = (
        "Introductory context here. Specifically, the Transformer architecture dispenses "
        "entirely with recurrence and convolutions, relying instead on scaled dot-product "
        "self-attention mechanisms! Closing remark."
    )

    suspect_tokens = tokenize_with_spans(suspect)
    source_words = normalize_text(source).split()
    spans = find_original_spans(suspect, suspect_tokens, source_words, shingle_size=5)

    assert len(spans) == 1
    span = spans[0]
    assert suspect[span["start"]:span["end"]] == span["text"]
    assert "Transformer architecture dispenses entirely with recurrence" in span["text"]


def test_shingles_and_intervals_edge_cases():
    assert create_shingles(["a", "b"], 5) == set()
    assert create_shingles(["a", "b", "c"], 0) == set()
    assert find_matched_intervals(["a", "b"], ["a", "b"], 5) == []


def test_jaccard_and_tfidf_similarity_bounds():
    s1 = create_shingles(["alpha", "beta", "gamma", "delta", "epsilon"], 3)
    s2 = create_shingles(["alpha", "beta", "gamma", "delta", "epsilon"], 3)
    s3 = create_shingles(["one", "two", "three", "four", "five"], 3)

    assert jaccard_similarity(s1, s2) == 1.0
    assert jaccard_similarity(s1, s3) == 0.0
    assert jaccard_similarity(set(), set()) == 0.0

    same_cos = tfidf_cosine_similarity("distributed consensus raft log", "distributed consensus raft log")
    diff_cos = tfidf_cosine_similarity("distributed consensus raft log", "photosynthesis chlorophyll leaf sunlight")
    assert same_cos > 0.99
    assert diff_cos == 0.0


def test_corpus_tfidf_ranks_relevant_document_highest():
    query = "B+Tree index pages maintain sorted keys for fast range scans in databases"
    corpus = [
        "Gradient descent optimizes neural network weights using mini batches",
        "Relational databases use B+Tree index pages with sorted keys for range scans",
        "Operating systems schedule threads across multiple processor cores",
    ]
    scores = corpus_tfidf_similarities(query, corpus)
    assert len(scores) == 3
    assert scores[1] > scores[0]
    assert scores[1] > scores[2]
