"""The q: rule of a knowhow card: one question, at most 120 characters, ending in '?'.

Cards not yet rewritten are listed in tools/knowhow_pending_q.txt (one `domain/slug` per line).
A listed card is tolerated while it still violates the rule and fails once it complies, so the
list can only shrink and must end empty.
"""

import re
from pathlib import Path

MAX_Q = 120
PENDING = Path(__file__).resolve().parent / "knowhow_pending_q.txt"


def pending() -> set[str]:
    """The `domain/slug` entries still waiting for a rewritten q:."""
    if not PENDING.exists():
        return set()
    return {ln.strip() for ln in PENDING.read_text(encoding="utf-8").splitlines() if ln.strip()}


def q_of(card: Path) -> str:
    """The q: line of a card, without its key."""
    m = re.search(r"^q:[ \t]*(.*)$", card.read_text(encoding="utf-8"), re.M)
    return m.group(1).strip() if m else ""


def question_problems(card: Path) -> list[str]:
    """Messages for a card whose q: breaks the rule, or whose pending entry is stale.

    Args:
        card: Path of a card, knowhow/<domain>/<slug>.md.

    Returns:
        Empty when the card complies and is not listed, or fails and is listed.
    """
    q, name = q_of(card), f"{card.parent.name}/{card.stem}"
    bad = not q.endswith("?") or len(q) > MAX_Q
    listed = name in pending()
    if bad and not listed:
        return [f"{name}: q: must be one question ending in '?', at most {MAX_Q} chars ({len(q)})"]
    if listed and not bad:
        return [f"{name}: q: complies now, delete it from tools/knowhow_pending_q.txt"]
    return []
