"""Whether a quote is a verbatim sentence of the stored source, at the place the entry says."""

import re
import unicodedata

PAGE = re.compile(r"^\[(abstract|page \d+)\]$", re.M)
ABSENT = "not stated in source"


def squeeze(text: str) -> str:
    """A text as it compares: ligatures and accents folded, lower case, no space, no hyphen.

    A PDF's text loses spaces, breaks words at line ends and swaps quote marks; a quote copied
    from it must still be found. Minus signs and significance stars are kept: in a table row
    they are the result.
    """
    signs = text.translate({0x2212: "-", 0x2013: "-", 0x2014: "-", 0x2217: "*"})
    flat = (
        unicodedata.normalize("NFKD", signs).encode("ascii", "ignore").decode().lower()
    )
    # A hyphen before a digit is a minus sign or a range and is kept; any other one is a word
    # broken at a line end, or a compound, and goes.
    return re.sub(r"-(?![0-9.])|[^a-z0-9%.,*-]", "", flat)


def pages(text: str) -> dict[str, str]:
    """A stored source split at its `[abstract]` and `[page N]` marks: place → its text."""
    parts = PAGE.split(text)
    return {
        f"p. {name[5:]}" if name.startswith("page") else name: body
        for name, body in zip(parts[1::2], parts[2::2])
    }


def found(quote: str, where: str, source: dict[str, str]) -> bool:
    """Whether the quote is in the source at that place (`abstract` or `p. N`)."""
    return where in source and squeeze(quote) in squeeze(source[where])


def errors(
    anchor: object,
    value: object,
    name: str,
    source: dict[str, str],
    min_chars: int,
    only: str = "",
) -> list[str]:
    """What is wrong with one field's anchor.

    Args:
        anchor: `{quote, where}`, or ABSENT for a field the source does not state.
        value: The field's value in the entry; ABSENT exactly when the anchor is.
        name: The field, for the message.
        source: What pages() returned.
        min_chars: Shortest quote that counts as a sentence.
        only: When set, the only place a quote may come from (an abstract-only read).

    Returns:
        Messages, empty when the anchor holds.
    """
    if anchor == ABSENT or value == ABSENT:
        return (
            []
            if anchor == value
            else [
                f"{name}: «{ABSENT}» must be both the value and the anchor, or neither"
            ]
        )
    if not isinstance(anchor, dict) or set(anchor) != {"quote", "where"}:
        return [f"{name}: the anchor is {{quote, where}} or «{ABSENT}»"]
    if len(anchor["quote"]) < min_chars:
        return [
            f"{name}: a quote of {len(anchor['quote'])} characters is not a sentence"
        ]
    if only and anchor["where"] != only:
        return [
            f"{name}: read as {only} only, the quote cannot come from {anchor['where']}"
        ]
    if not found(anchor["quote"], anchor["where"], source):
        return [f"{name}: the quote is not in the source at {anchor['where']}"]
    return []
