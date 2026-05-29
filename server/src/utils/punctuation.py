"""Punctuation restoration for ASR word timestamps."""

try:
    from ..engines.base import WordTimestamp
except ImportError:
    from engines.base import WordTimestamp


_PUNCT = set('，。、！？；：""''《》【】（）,.!?;:\'"()[]{}·…—~')


def restore_punctuation(words: list[WordTimestamp], full_text: str) -> list[WordTimestamp]:
    """Restore punctuation from full text into word timestamps.

    Uses substring matching to handle multi-char timestamp entries (e.g. "OpenCL").
    Finds each timestamp text in the full text sequentially, and attaches
    any intervening punctuation/spaces to the preceding word.

    Args:
        words: List of WordTimestamp objects (without punctuation).
        full_text: The original transcribed text with punctuation.

    Returns:
        New list of WordTimestamp objects with punctuation attached.
    """
    if not words or not full_text:
        return words

    result = [WordTimestamp(w.text, w.start_time, w.end_time) for w in words]
    pos = 0  # current position in full_text

    for wi in range(len(result)):
        expected = result[wi].text
        remaining = full_text[pos:]

        # Find this timestamp's text in the remaining full text
        idx = remaining.find(expected)
        if idx < 0:
            # Can't find it - skip this timestamp
            continue

        # Attach any chars before the match (punctuation only) to previous word
        if wi > 0:
            for ch in remaining[:idx]:
                if ch in _PUNCT:
                    result[wi - 1] = WordTimestamp(
                        result[wi - 1].text + ch,
                        result[wi - 1].start_time,
                        result[wi - 1].end_time,
                    )

        # Advance position past the matched text
        pos += idx + len(expected)

        # Attach trailing punctuation/spaces to this word
        while pos < len(full_text) and full_text[pos] in _PUNCT:
            result[wi] = WordTimestamp(
                result[wi].text + full_text[pos],
                result[wi].start_time,
                result[wi].end_time,
            )
            pos += 1

    return result
