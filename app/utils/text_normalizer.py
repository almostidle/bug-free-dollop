import re
import unicodedata


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize_with_spans(text: str) -> list[tuple[str, int, int]]:
    """Return (normalized_word, char_start, char_end) aligned 1-to-1 with normalize_text(text).split()."""
    tokens: list[tuple[str, int, int]] = []
    for match in re.finditer(r"\S+", text):
        raw_token = match.group(0)
        normalized = unicodedata.normalize("NFKD", raw_token).lower()
        normalized = re.sub(r"[^a-z0-9\s]", "", normalized)
        for part in normalized.split():
            if part:
                tokens.append((part, match.start(), match.end()))
    return tokens
