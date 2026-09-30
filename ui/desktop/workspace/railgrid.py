"""The rail's step cards laid in rows as wide as the rail holds."""

PER_ROW, CARD_W = 10, 175   # cards per row at most; px a card needs for box, ⚙, ▶ and title


def reflow(grid: object, cards: list, width: int, per_row: int) -> int:
    """Lay the step cards in rows as wide as the rail holds, 3 to PER_ROW: ten fixed columns
    ran off the right edge of a narrower window (owner, 2026-09-28).

    Returns:
        The cards per row now; unchanged (and nothing moved) when the width asks the same.
    """
    fit = max(3, min(PER_ROW, width // CARD_W))
    if fit == per_row or not cards:
        return per_row
    for card in cards:
        grid.removeWidget(card)
    for i, card in enumerate(cards):
        grid.addWidget(card, i // fit, i % fit)
    for col in range(PER_ROW):
        grid.setColumnStretch(col, 1 if col < fit else 0)
    return fit
