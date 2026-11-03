def create_shingles(words: list[str], size: int) -> set[tuple[str, ...]]:
    if len(words) < size:
        return set()
    return {tuple(words[i:i + size]) for i in range(len(words) - size + 1)}


def create_shingles_with_positions(words: list[str], size: int) -> dict[tuple[str, ...], list[int]]:
    positions = {}
    for i in range(len(words) - size + 1):
        shingle = tuple(words[i:i + size])
        if shingle not in positions:
            positions[shingle] = []
        positions[shingle].append(i)
    return positions


def find_matched_passages(words_a: list[str], words_b: list[str], shingle_size: int) -> list[str]:
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

    # merge consecutive/overlapping positions into passages
    passages = []
    start = matched_positions[0]
    end = matched_positions[0] + shingle_size

    for pos in matched_positions[1:]:
        if pos <= end:
            end = pos + shingle_size
        else:
            passages.append(" ".join(words_a[start:end]))
            start = pos
            end = pos + shingle_size

    passages.append(" ".join(words_a[start:end]))
    return passages
