"""What Ctrl+K lists and in which order: the fuzzy match, the aliases and the recent choices."""

import json
import unicodedata

from PySide6.QtCore import QSettings

# Recent choices: the per-viewer QSettings of the app (organisation, application), never AlgoData.
RECENT_KEY, RECENT_MAX, SHOWN = "cmdpalette/recent", 10, 60
STORE = ("AlgoProject", "AlgoProject")
TAG = {"zone": "zona", "project": "proyecto", "databank": "databank", "strategy": "estrategia",
       "study": "estudio"}
ORDER = list(TAG)
# Other words a zone answers to: the owner still says «ledger» for the search log (22 §9).
ALIASES = {"Registro de búsquedas": ("ledger",), "En marcha": ("custodio", "generación"),
           "Portfolios": ("carteras",)}


def fold(s: str) -> str:
    """Lower case without accents, so «busquedas» finds «búsquedas»."""
    return "".join(c for c in unicodedata.normalize("NFD", s.lower())
                   if unicodedata.category(c) != "Mn")


def match(query: str, label: str) -> int | None:
    """Fuzzy subsequence score of a query against a label.

    Args:
        query: What the owner typed.
        label: The candidate's name.

    Returns:
        None when the query's letters do not appear in order; otherwise the letters skipped
        between the first and last hit plus where the first hit sits (lower is better).
    """
    q, s = fold(query).replace(" ", ""), fold(label)
    at, first, gaps = -1, None, 0
    for ch in q:
        nxt = s.find(ch, at + 1)
        if nxt < 0:
            return None
        if first is None:
            first = nxt
        else:
            gaps += nxt - at - 1
        at = nxt
    return gaps * 2 + (first or 0)


def best(query: str, item: dict) -> int | None:
    """The best score of a query against an item's label and its aliases, or None."""
    scores = [s for s in (match(query, w) for w in (item["label"], *item.get("also", ())))
              if s is not None]
    return min(scores) if scores else None


def ident(item: dict) -> tuple:
    """What makes two items the same choice, for the recent list."""
    return item["kind"], item["label"], item.get("project"), item.get("databank")


def rank(query: str, items: list[dict], recent: list[dict]) -> list[dict]:
    """The items to list for a query: recent matches first, newest on top, then by score and kind.

    Args:
        query: What the owner typed; "" lists everything.
        items: Every candidate.
        recent: The last choices, newest first.

    Returns:
        The matching items, a recent one carrying `recent: True`.
    """
    seen = {ident(r) for r in recent}
    pool = [{**r, "recent": True} for r in recent] + [i for i in items if ident(i) not in seen]
    kept = [(s, i) for s, i in ((best(query, i), i) for i in pool) if s is not None]
    return [i for _, i in sorted(kept, key=lambda p: (0, 0, 0) if p[1].get("recent") else
                                 (1, p[0], ORDER.index(p[1]["kind"])))]


def load_recent() -> list[dict]:
    """The last choices, newest first; a broken store reads as none."""
    try:
        got = json.loads(QSettings(*STORE).value(RECENT_KEY, "[]") or "[]")
        return [r for r in got if r.get("kind") in TAG and r.get("label")][:RECENT_MAX]
    except Exception:  # noqa: BLE001 — a per-viewer convenience must never break the window
        return []


def save_recent(item: dict) -> None:
    """Put one choice at the head of the recent list; a store that refuses is ignored.

    A project is remembered by its name only: its gallery row is read fresh when opened.
    """
    clean = {k: v for k, v in item.items() if k not in ("recent", "row", "also")}
    rest = [r for r in load_recent() if ident(r) != ident(clean)]
    try:
        QSettings(*STORE).setValue(RECENT_KEY, json.dumps([clean, *rest][:RECENT_MAX]))
    except Exception:  # noqa: BLE001 — same as above
        pass
