import re
import math
from collections import Counter
from sqlalchemy.orm import Session
from app.services import config_service


def detect_ai_content(text: str, db: Session) -> dict:
    w_burst = config_service.get_config_float("weight_burstiness", db)
    w_lex = config_service.get_config_float("weight_lexical_diversity", db)
    w_ngram = config_service.get_config_float("weight_repeated_ngrams", db)
    w_avg = config_service.get_config_float("weight_avg_sentence_length", db)
    w_punct = config_service.get_config_float("weight_punctuation_patterns", db)
    ngram_size = config_service.get_config_int("ngram_size", db)
    ai_threshold = config_service.get_config_float("ai_threshold", db)

    sentences = _split_sentences(text)
    words = text.lower().split()

    burst_score, burst_raw = _burstiness(sentences)
    lex_score, lex_raw = _lexical_diversity(words)
    ngram_score, ngram_raw = _repeated_ngrams(words, ngram_size)
    avg_score, avg_raw = _avg_sentence_length(sentences)
    punct_score, punct_raw = _punctuation_patterns(text)

    overall = (
        w_burst * burst_score +
        w_lex * lex_score +
        w_ngram * ngram_score +
        w_avg * avg_score +
        w_punct * punct_score
    )
    overall = round(min(1.0, max(0.0, overall)), 4)

    return {
        "overall_score": overall,
        "is_ai_generated": overall >= ai_threshold,
        "metrics": {
            "burstiness": {
                "score": round(burst_score, 4),
                "raw_value": round(burst_raw, 4),
                "description": "Sentence length variance. Low variance suggests AI-generated text.",
            },
            "lexical_diversity": {
                "score": round(lex_score, 4),
                "raw_value": round(lex_raw, 4),
                "description": "Type-token ratio. Lower diversity can indicate repetitive AI patterns.",
            },
            "repeated_ngrams": {
                "score": round(ngram_score, 4),
                "raw_value": round(ngram_raw, 4),
                "description": "Ratio of repeated n-grams. Higher repetition suggests AI content.",
            },
            "avg_sentence_length": {
                "score": round(avg_score, 4),
                "raw_value": round(avg_raw, 4),
                "description": "Average words per sentence. AI tends toward uniform medium-length sentences.",
            },
            "punctuation_patterns": {
                "score": round(punct_score, 4),
                "raw_value": round(punct_raw, 4),
                "description": "Punctuation diversity. AI text often relies mostly on periods and commas.",
            },
        },
    }


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r'[.!?]+', text)
    return [s.strip() for s in parts if s.strip()]


def _burstiness(sentences: list[str]) -> tuple[float, float]:
    if len(sentences) < 2:
        return 0.5, 0.0
    lengths = [len(s.split()) for s in sentences]
    mean = sum(lengths) / len(lengths)
    if mean == 0:
        return 0.5, 0.0
    variance = sum((l - mean) ** 2 for l in lengths) / len(lengths)
    stdev = math.sqrt(variance)
    cv = stdev / mean
    # low coefficient of variation = uniform sentence length = more AI-like
    score = max(0.0, min(1.0, 1.0 - (cv / 0.6)))
    return score, cv


def _lexical_diversity(words: list[str]) -> tuple[float, float]:
    if not words:
        return 0.5, 0.0
    clean = [w for w in words if w.isalpha()]
    if not clean:
        return 0.5, 0.0
    ttr = len(set(clean)) / len(clean)
    # lower TTR = more repetitive = more AI-like
    score = max(0.0, min(1.0, (0.72 - ttr) / 0.4))
    return score, ttr


def _repeated_ngrams(words: list[str], n: int) -> tuple[float, float]:
    clean = [w for w in words if w.isalpha()]
    if len(clean) < n:
        return 0.0, 0.0
    ngrams = [tuple(clean[i:i + n]) for i in range(len(clean) - n + 1)]
    counts = Counter(ngrams)
    total = len(counts)
    if total == 0:
        return 0.0, 0.0
    repeated = sum(1 for c in counts.values() if c > 1)
    ratio = repeated / total
    score = min(1.0, ratio * 2.5)
    return score, ratio


def _avg_sentence_length(sentences: list[str]) -> tuple[float, float]:
    if not sentences:
        return 0.5, 0.0
    lengths = [len(s.split()) for s in sentences]
    avg = sum(lengths) / len(lengths)
    # AI tends to cluster around 15-22 words per sentence
    score = max(0.0, 1.0 - abs(avg - 18) / 14)
    return score, avg


def _punctuation_patterns(text: str) -> tuple[float, float]:
    all_punct = re.findall(r'[^\w\s]', text)
    if not all_punct:
        return 0.6, 0.0
    basic = sum(1 for p in all_punct if p in '.,:')
    basic_ratio = basic / len(all_punct)
    # if almost all punctuation is periods/commas/colons, looks AI-generated
    score = max(0.0, min(1.0, (basic_ratio - 0.5) / 0.45))
    return score, basic_ratio
