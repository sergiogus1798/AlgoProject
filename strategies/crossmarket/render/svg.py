"""The drawing primitives every figure shares: the canvas, the axes, the number and the legend."""

W, H = 760, 300                       # one figure, wide enough for 60 bins at 2px apart
WIDE, NARROW = 820, 620               # the equity/histogram pair, side by side
PAD = {"l": 56, "r": 20, "t": 28, "b": 46}
NAMES = 150                           # room for a model name; "resampled_holds" must not clip
NULL, REAL, GRID, INK = "var(--null)", "var(--real)", "var(--grid)", "var(--ink-2)"
SERIES = ("var(--s1)", "var(--s2)", "var(--s3)")   # one colour per model when several
                                                  # share an axis; --real stays the reference
# One colour per market, fixed for the whole panel: the same market is the same colour in the
# equity overlay, in the correlation heatmap and in every histogram. Six of them, because the
# owner expects to retest on four markets plus the base and one unclassified feed.
MARKETS = ("var(--s1)", "var(--s2)", "var(--s3)", "var(--s4)", "var(--s5)", "var(--s6)")
GAP = 2                               # surface gap between adjacent bars


def palette(feeds: list[str], base: str) -> dict[str, str]:
    """A fixed colour per market, the base asset always the same one.

    Args:
        feeds: Every market on the page, the base asset included.
        base: The base asset's feed.

    Returns:
        {feed: CSS colour}. The base asset takes --real, the colour that means "the reference"
        everywhere else on the page; the rest take MARKETS in the order the universe lists
        them, so a market does not change colour when another one is re-run on its own.
    """
    rest = [f for f in feeds if f != base]
    return {base: REAL, **{f: MARKETS[i % len(MARKETS)] for i, f in enumerate(rest)}}


def xpos(value: float, lo: float, hi: float, left: int = PAD["l"], width: int = W) -> float:
    """Position a data value on the horizontal axis.

    Args:
        value: The value to place.
        lo, hi: Axis extent in data units.
        left: Left margin, wider when the rows carry names rather than ticks.
        width: Total figure width; the pair of figures beside each other are not W wide.

    Returns:
        A pixel coordinate inside the plot area.
    """
    span = hi - lo or 1.0
    return left + (value - lo) / span * (width - left - PAD["r"])


def tickvals(lo: float, hi: float, count: int = 5) -> list[float]:
    """Evenly spaced axis values.

    Args:
        lo, hi: Axis extent.
        count: How many ticks.

    Returns:
        The tick values, ends included. Named tickvals and not ticks because `ticks` is
        already a local holding rendered markup in two of the modules that import this.
    """
    return [lo + (hi - lo) * i / (count - 1) for i in range(count)]


def num(value: float) -> str:
    """One axis or mark number, in the shape a reader expects for its size.

    Args:
        value: The number.

    Returns:
        Thousands separated above 1,000, two decimals down to 1, four significant figures
        below it. The general-purpose format turns 46,191 into 4.619e+04, which is correct
        and unreadable.
    """
    if abs(value) >= 1000:
        return f"{value:,.0f}"
    return f"{value:,.2f}" if abs(value) >= 1 else f"{value:.4g}"


def legend(items: list[tuple[str, str]]) -> str:
    """A row of colour-coded chips under a figure, instead of a caption to decode.

    Args:
        items: (swatch style, label) pairs, the style matching what the figure drew.

    Returns:
        One HTML block, script-free so it renders the same in the panel and anywhere else.
    """
    chips = "".join(f'<span class="chip"><i style="{style}"></i>{label}</span>'
                    for style, label in items)
    return f'<div class="legend">{chips}</div>'
