import re
import math
from collections import Counter
from sqlalchemy.orm import Session
from app.services import config_service


_ABBREV_PATTERN = re.compile(
    r"\b(Dr|Mr|Mrs|Ms|Prof|Sr|Jr|vs|etc|Fig|Eq|Ref|al|Inc|Ltd|Co|No|Vol|pp)\.",
    re.IGNORECASE,
)
_MULTI_ABBREV_PATTERN = re.compile(r"\b(e\.g|i\.e|U\.S|U\.K)\.", re.IGNORECASE)
_DECIMAL_PATTERN = re.compile(r"(?<=\d)\.(?=\d)")


def detect_ai_content(text: str, db: Session) -> dict:
    w_burst = config_service.get_config_float("weight_burstiness", db)
    w_lex = config_service.get_config_float("weight_lexical_diversity", db)
    w_ngram = config_service.get_config_float("weight_repeated_ngrams", db)
    w_avg = config_service.get_config_float("weight_avg_sentence_length", db)
    w_punct = config_service.get_config_float("weight_punctuation_patterns", db)
    ngram_size = config_service.get_config_int("ngram_size", db)
    ai_threshold = config_service.get_config_float("ai_threshold", db)

    sentences = _split_sentences(text)
    words = _extract_words(text)

    burst_score, burst_raw = _burstiness(sentences)
    lex_score, lex_raw = _lexical_diversity(words)
    ngram_score, ngram_raw = _repeated_ngrams(words, ngram_size)
    avg_score, avg_raw = _avg_sentence_length(sentences)
    punct_score, punct_raw = _punctuation_patterns(text)

    weight_sum = w_burst + w_lex + w_ngram + w_avg + w_punct
    weighted = (
        w_burst * burst_score +
        w_lex * lex_score +
        w_ngram * ngram_score +
        w_avg * avg_score +
        w_punct * punct_score
    )
    if weight_sum > 0 and abs(weight_sum - 1.0) > 1e-6:
        weighted = weighted / weight_sum
    overall = round(min(1.0, max(0.0, weighted)), 4)

    sentence_lengths = [len(_extract_words(s)) for s in sentences]
    mean_len = (sum(sentence_lengths) / len(sentence_lengths)) if sentence_lengths else 0.0
    sentence_breakdown = [
        {
            "index": idx + 1,
            "text": s[:220] + ("..." if len(s) > 220 else ""),
            "word_count": wc,
            "deviation": round(abs(wc - mean_len), 2),
        }
        for idx, (s, wc) in enumerate(zip(sentences[:25], sentence_lengths[:25]))
    ]

    return {
        "overall_score": overall,
        "is_ai_generated": overall >= ai_threshold,
        "word_count": len(words),
        "sentence_count": len(sentences),
        "metrics": {
            "burstiness": {
                "score": round(burst_score, 4),
                "raw_value": round(burst_raw, 4),
                "description": "Sentence length coefficient of variation (CV). Low variance suggests uniform AI cadence.",
            },
            "lexical_diversity": {
                "score": round(lex_score, 4),
                "raw_value": round(lex_raw, 4),
                "description": "Moving-Average Type-Token Ratio (50-word window). Lower local diversity indicates repetitive AI phrasing.",
            },
            "repeated_ngrams": {
                "score": round(ngram_score, 4),
                "raw_value": round(ngram_raw, 4),
                "description": f"Proportion of repeated {ngram_size}-grams across stripped tokens. Higher repetition suggests AI templates.",
            },
            "avg_sentence_length": {
                "score": round(avg_score, 4),
                "raw_value": round(avg_raw, 2),
                "description": "Mean words per sentence. LLM prose often clusters tightly around 16–22 words.",
            },
            "punctuation_patterns": {
                "score": round(punct_score, 4),
                "raw_value": round(punct_raw, 4),
                "description": "Share of basic punctuation (.,:) vs expressive marks (—;!?()). AI relies heavily on periods and commas.",
            },
        },
        "sentences": sentence_breakdown,
    }


def _extract_words(text: str) -> list[str]:
    return re.findall(r"[a-z]+(?:'[a-z]+)?", text.lower())


def _split_sentences(text: str) -> list[str]:
    protected = _MULTI_ABBREV_PATTERN.sub(lambda m: m.group(0).replace(".", "\x00"), text)
    protected = _ABBREV_PATTERN.sub(lambda m: m.group(1) + "\x00", protected)
    protected = _DECIMAL_PATTERN.sub("\x00", protected)
    parts = re.split(r"[.!?]+(?:\s+|$)", protected)
    restored = [p.replace("\x00", ".").strip() for p in parts]
    return [s for s in restored if s]


def _burstiness(sentences: list[str]) -> tuple[float, float]:
    if len(sentences) < 2:
        return 0.5, 0.0
    lengths = [len(_extract_words(s)) for s in sentences]
    lengths = [l for l in lengths if l > 0]
    if len(lengths) < 2:
        return 0.5, 0.0
    mean = sum(lengths) / len(lengths)
    if mean == 0:
        return 0.5, 0.0
    variance = sum((l - mean) ** 2 for l in lengths) / len(lengths)
    stdev = math.sqrt(variance)
    cv = stdev / mean
    # Low coefficient of variation = uniform sentence length = more AI-like
    score = max(0.0, min(1.0, 1.0 - (cv / 0.6)))
    return score, cv


def _lexical_diversity(words: list[str], window_size: int = 50) -> tuple[float, float]:
    if not words:
        return 0.5, 0.0
    if len(words) <= window_size:
        mattr = len(set(words)) / len(words)
    else:
        windows = [
            len(set(words[i:i + window_size])) / window_size
            for i in range(len(words) - window_size + 1)
        ]
        mattr = sum(windows) / len(windows)
    # Lower MATTR = more repetitive local vocabulary = more AI-like
    score = max(0.0, min(1.0, (0.93 - mattr) / 0.18))
    return score, mattr


def _repeated_ngrams(words: list[str], n: int) -> tuple[float, float]:
    if n <= 0 or len(words) < n:
        return 0.0, 0.0
    ngrams = [tuple(words[i:i + n]) for i in range(len(words) - n + 1)]
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
    lengths = [len(_extract_words(s)) for s in sentences]
    lengths = [l for l in lengths if l > 0]
    if not lengths:
        return 0.5, 0.0
    avg = sum(lengths) / len(lengths)
    # AI tends to cluster around 15-22 words per sentence
    score = max(0.0, 1.0 - abs(avg - 18) / 14)
    return score, avg


def _punctuation_patterns(text: str) -> tuple[float, float]:
    all_punct = re.findall(r"[^\w\s]", text)
    if not all_punct:
        return 0.6, 0.0
    basic = sum(1 for p in all_punct if p in ".,:")
    basic_ratio = basic / len(all_punct)
    # If almost all punctuation is periods/commas/colons, looks AI-generated
    score = max(0.0, min(1.0, (basic_ratio - 0.5) / 0.45))
    return score, basic_ratio
