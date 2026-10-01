"""Grids that differ only in their market, laid side by side (2-3 chosen), with the consensus grid under them."""

from collections.abc import Callable

from PySide6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from core.symbols import alias
from ui.desktop.blocks.card import text
from ui.desktop.blocks.kinds import draw
from ui.desktop.blocks.pick import picked, selectors, shown
from ui.text.glossary import label
from ui.desktop.theme import T

KEY = "market"          # the selector a study tags per-market surfaces with (marketSurfaces, E4)
MOST = 3                # the owner's 22 §6.2: two or three at a time, never more
CHOSEN = "_markets"     # where the tab's memory keeps the markets on screen


def grouped(tab: dict) -> bool:
    """Whether a tab holds grids that differ only in their market.

    Args:
        tab: One contract tab.

    Returns:
        True when a `market` selector exists and at least one grid is tagged with it.
    """
    return (any(s["key"] == KEY for s in selectors(tab))
            and any(b["kind"] == "grid" and KEY in (b.get("select") or {}) for b in tab["blocks"]))


def first(tab: dict) -> list[str]:
    """The markets on screen before the reader picks: the selector's default and the next ones."""
    s = next(s for s in selectors(tab) if s["key"] == KEY)
    options = [str(o) for o in s["options"]]
    return ([str(s["default"])] + [o for o in options if o != str(s["default"])])[:MOST]


def split(tab: dict, chosen: dict, pool: list[dict]) -> tuple[list[dict], list[dict], dict | None]:
    """What a grouped tab draws: its other blocks, one grid per chosen market, the consensus.

    Args:
        tab: A grouped tab.
        chosen: Its selector values, with the markets on screen under `CHOSEN`.
        pool: Every block of the whole result, where the consensus grid is looked for — it
            lives in a tab of its own, tagged like these grids minus the market.

    Returns:
        (the blocks drawn as usual for the first market, the market grids in the chosen
        order, the consensus grid of the same other selections or None). Nothing is
        recomputed: every combination is already in the result (CONTRACT §1).
    """
    markets = chosen.get(CHOSEN) or first(tab)
    plain = [b for b in shown(tab, {**chosen, KEY: markets[0]})
             if not (b["kind"] == "grid" and KEY in (b.get("select") or {}))]
    grids = [b for m in markets for b in shown(tab, {**chosen, KEY: m})
             if b["kind"] == "grid" and str((b.get("select") or {}).get(KEY)) == m]
    rest = {k: v for k, v in picked(tab, chosen).items() if k != KEY}
    consensus = next((b for b in pool if b["kind"] == "grid" and b.get("select")
                      and KEY not in b["select"]
                      and {k: str(v) for k, v in b["select"].items()} == rest), None)
    return plain, grids, consensus


def row(grids: list[dict], consensus: dict | None) -> QWidget:
    """The market grids in one row, the consensus under the first at the same width.

    Args:
        grids: One grid block per market on screen.
        consensus: The consensus grid, or None when the result carries none.

    Returns:
        The laid-out widget.
    """
    box = QWidget()
    lay = QVBoxLayout(box)
    lay.setContentsMargins(0, 0, 0, 0)
    across = QHBoxLayout()
    for g in grids:
        across.addWidget(draw(g), 1)
    lay.addLayout(across)
    if consensus is not None:
        under = QHBoxLayout()
        lay.addWidget(text(label("markets.consensus").upper(), T["text"], 11, True))
        under.addWidget(draw(consensus), 1)
        for _ in grids[1:]:
            under.addWidget(QWidget(), 1)
        lay.addLayout(under)
    return box


def picker(tab: dict, on: list[str], changed: Callable[[list[str]], None]) -> QWidget:
    """One toggle per market: pressing a fourth lets go of the oldest, so 2-3 stay on screen.

    Args:
        tab: A grouped tab.
        on: The markets on screen now.
        changed: Called with the new list after every press.

    Returns:
        The row of toggles, with its caption.
    """
    s = next(s for s in selectors(tab) if s["key"] == KEY)
    box = QWidget()
    lay = QHBoxLayout(box)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.addWidget(text(label("markets.pick"), T["muted"], 12))
    keep = list(on)
    buttons: dict[str, QPushButton] = {}

    def press(market: str, down: bool) -> None:
        """Add or drop one market, never below one nor above MOST."""
        if down == (market in keep):       # the echo of a toggle this function made itself
            return
        if down:
            keep.append(market)
            if len(keep) > MOST:
                buttons[keep.pop(0)].setChecked(False)
        elif len(keep) == 1:
            buttons[market].setChecked(True)
            return
        else:
            keep.remove(market)
        changed(list(keep))

    for o in [str(o) for o in s["options"]]:
        b = QPushButton(alias(o))
        b.setCheckable(True)
        b.setChecked(o in keep)
        b.setStyleSheet(f"QPushButton:checked {{ background: {T['accent']}; color: {T['bg']}; "
                        "font-weight: 700; }")
        b.setToolTip("Enseña u oculta la superficie de este mercado. Hasta tres a la vez, todas "
                     "con la misma escala de color. No recalcula nada.")
        b.toggled.connect(lambda down, o=o: press(o, down))
        buttons[o] = b
        lay.addWidget(b)
    lay.addStretch(1)
    return box
