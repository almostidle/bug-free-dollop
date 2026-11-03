from app.utils.text_normalizer import tokenize_with_spans


def create_shingles(words: list[str], size: int) -> set[tuple[str, ...]]:
    if size <= 0 or len(words) < size:
        return set()
    return {tuple(words[i:i + size]) for i in range(len(words) - size + 1)}


def create_shingles_with_positions(words: list[str], size: int) -> dict[tuple[str, ...], list[int]]:
    if size <= 0 or len(words) < size:
        return {}
    positions: dict[tuple[str, ...], list[int]] = {}
    for i in range(len(words) - size + 1):
        shingle = tuple(words[i:i + size])
        if shingle not in positions:
            positions[shingle] = []
        positions[shingle].append(i)
    return positions


def find_matched_intervals(words_a: list[str], words_b: list[str], shingle_size: int) -> list[tuple[int, int]]:
    """Return merged (word_start, word_end) intervals in words_a that match shingles in words_b."""
    if shingle_size <= 0 or len(words_a) < shingle_size or len(words_b) < shingle_size:
        return []

    shingles_a = create_shingles_with_positions(words_a, shingle_size)
    shingles_b = create_shingles(words_b, shingle_size)

    matched_positions = sorted(set(
        pos
        for shingle, positions in shingles_a.items()
        if shingle in shingles_b
        for pos in positions
    ))

    if not matched_positions:
        return []

    intervals: list[tuple[int, int]] = []
    start = matched_positions[0]
    end = matched_positions[0] + shingle_size

    for pos in matched_positions[1:]:
        if pos <= end:
            end = max(end, pos + shingle_size)
        else:
            intervals.append((start, end))
            start = pos
            end = pos + shingle_size

    intervals.append((start, end))
    return intervals


def find_matched_passages(words_a: list[str], words_b: list[str], shingle_size: int) -> list[str]:
    intervals = find_matched_intervals(words_a, words_b, shingle_size)
    return [" ".join(words_a[start:end]) for start, end in intervals]


def find_original_spans(
    text_a: str,
    tokens_a: list[tuple[str, int, int]],
    words_b: list[str],
    shingle_size: int,
) -> list[dict]:
    """Return matched intervals mapped to character offsets and original excerpts in text_a."""
    words_a = [w for w, _, _ in tokens_a]
    intervals = find_matched_intervals(words_a, words_b, shingle_size)
    spans = []
    for word_start, word_end in intervals:
        char_start = tokens_a[word_start][1]
        char_end = tokens_a[word_end - 1][2]
        spans.append({
            "start": char_start,
            "end": char_end,
            "word_count": word_end - word_start,
            "text": text_a[char_start:char_end],
        })
    return spans
