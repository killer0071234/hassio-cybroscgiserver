def split_at_index(sequence: list[int], index: int):
    """Split `sequence` into left and right part.

    Args:
        sequence (list[int])
        index: Place at which to make the split.

    Returns:
        Tuple with left and right part.
    """

    return sequence[:index], sequence[index:]


def chunk(sequence: bytes, size: int):
    """Break `sequence` into chunks which are at most `size` long.

    Returns:
        None

    Yields:
        Chunks in the order they are being made.
    """

    s = sequence
    while len(s) != 0:
        yield s[:size]
        s = s[size:]
