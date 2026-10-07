"""The monkey drawn inside calendar windows, sized at its own bar and priced by the common repricer.

A third family beside the ladder and placement, and separate on purpose: the ladder
(`simulate.nulls`) draws over the whole sample, keeps the donor's lots and charges the residual
cost `calibrate.charged` measures, which holds no spread and no slippage
(knowhow/research/monkey-reprice-audit.md). Nothing of the ladder is touched here, so every
number it gave before this file existed is the number it gives now."""

import numpy as np
import pandas as pd

from engines.market import calibrate, reprice

# What each rung of model.RUNGS hands to chance here, beside the entry bar: (the hold is
# redrawn from the strategy's own, the sizing by volatility is stripped).
REDRAWS = {"timing": (False, False), "timing_holds": (True, False),
           "timing_sizing": (False, True), "free": (True, True)}

# Trade valuations priced per reprice.pnl call. Memory and cache only: a draw consumes the
# same random numbers whatever the block, so changing this moves no monkey.
BLOCK = 200_000


def atr_sized(atr: np.ndarray, entry: np.ndarray, size: np.ndarray,
              enter: np.ndarray) -> np.ndarray:
    """The lots a sizing rule that normalises by volatility would have given a drawn trade.

    Args:
        atr: One value per bar, the volatility the rule reads at that bar.
        entry: Entry bar of every real trade.
        size: Lots of every real trade.
        enter: Entry bar of every drawn trade, any shape.

    Returns:
        `c / atr[enter]`, `c` the real trades' median size x ATR at their own entries. The
        real size carries the ATR of the REAL entry: moved to a bar twice as volatile it risks
        twice the money, which no sizing rule would have allowed
        (knowhow/research/monkey-size-carries-donor-volatility.md). Lifted from
        `studies/screening/falsePositives/model.py`; the ATR period is the engine's, not the
        strategy's, and the lots are not rounded to the broker's step.
    """
    return np.median(size * atr[entry]) / atr[enter]


def grid(bars: pd.DataFrame, inside: np.ndarray, labels: np.ndarray) -> dict:
    """What every strategy of a run shares: the bars, their windows and where a draw may land.

    Args:
        bars: The strategies' own timeframe, the whole file, indexed by open time.
        inside: Positions of the bars of the sample (oos1), ascending.
        labels: The calendar window of each of those bars, same length.

    Returns:
        `bars`; `time`, their stamps; `atr`, the ATR known at each bar's open (the previous
        bar's — the one a rule that sizes at the entry can read, and the weight R3's blind
        trade uses); `eligible`, the positions of `inside` with a usable ATR; `bounds`, each
        window's first and last position; `last`, the last position of the sample.
    """
    atr = np.r_[np.nan, calibrate.atr(bars)[:-1]]
    usable = np.isfinite(atr[inside]) & (atr[inside] > 0)
    edges = pd.Series(inside).groupby(np.asarray(labels)).agg(["min", "max"])
    return {"bars": bars, "time": bars.index.to_numpy(), "atr": atr, "eligible": inside[usable],
            "bounds": {label: (int(lo), int(hi)) for label, lo, hi in edges.itertuples()},
            "last": int(inside[-1])}


def located(shared: dict, entry: np.ndarray, leave: np.ndarray, size: np.ndarray,
            side: np.ndarray, window: np.ndarray) -> dict:
    """One strategy's real trades on the grid, each with the window its monkeys are drawn in.

    Args:
        shared: What grid() returned.
        entry, leave: Bar position of every trade's open and close.
        size: Lots.
        side: +1 long, -1 short.
        window: The calendar window each trade opened in, a key of `shared["bounds"]`.

    Returns:
        `entry`, `hold` (bars), `size`, `side`, and `lo` / `hi`, the first and last bar of
        each trade's window.
    """
    lo, hi = np.array([shared["bounds"][label] for label in window]).T
    return {"entry": np.asarray(entry), "hold": np.asarray(leave) - np.asarray(entry),
            "size": np.asarray(size, float), "side": np.asarray(side, float), "lo": lo, "hi": hi}


def draw(shared: dict, mine: dict, rung: str, draws: int, rng: np.random.Generator) -> dict:
    """Monkeys of one strategy: every trade re-entered at a uniform bar of its own window.

    Args:
        shared: What grid() returned.
        mine: What located() returned.
        rung: A key of REDRAWS (the names of model.RUNGS).
        draws: How many monkeys.
        rng: Seeded generator.

    Returns:
        `entries`, `holds`, `sizes`, each (draws, trades). The entry is uniform over the
        eligible bars of the trade's window that leave its hold room before the sample ends;
        the exit may cross into the next window, as a real trade's does, and never leaves the
        sample (a redrawn hold too long for the last window is cut to fit). Sizes are
        atr_sized() at the drawn bar, or the strategy's mean lots on the rungs that strip the
        sizing. Monkeys may overlap, as on the ladder (model.py).
    """
    redraw, flat = REDRAWS[rung]
    n, ok = mine["entry"].size, shared["eligible"]
    u = rng.random((draws, 1 + redraw, n))
    holds = (mine["hold"][(u[:, 1] * n).astype(np.int64)] if redraw
             else np.broadcast_to(mine["hold"], (draws, n)))
    holds = np.minimum(holds, shared["last"] - mine["lo"])
    first = np.searchsorted(ok, mine["lo"])
    room = np.searchsorted(ok, np.minimum(mine["hi"], shared["last"] - holds),
                           side="right") - first
    entries = ok[first + (u[:, 0] * np.maximum(room, 1)).astype(np.int64)]
    holds = np.minimum(entries + holds, shared["last"]) - entries
    sizes = (np.broadcast_to(mine["size"].mean(), entries.shape) if flat
             else atr_sized(shared["atr"], mine["entry"], mine["size"], entries))
    return {"entries": entries, "holds": holds, "sizes": sizes}


def price(shared: dict, mine: dict, drawn: dict,
          costs: reprice.Costs) -> tuple[np.ndarray, np.ndarray]:
    """Every drawn trade's money P/L at the declared costs, in one reprice.pnl call.

    Args:
        shared: What grid() returned.
        mine: What located() returned; gives each column its side.
        drawn: What draw() returned.
        costs: reprice.costs() of the feed and segment.

    Returns:
        (pnl, cost), each (draws, trades): raw bar opens in, so the spread and the slippage
        are charged here, to every draw, exactly as to the real run.
    """
    enter, leave = drawn["entries"], drawn["entries"] + drawn["holds"]
    return reprice.pnl(reprice.fills(shared["bars"], enter), reprice.fills(shared["bars"], leave),
                       shared["time"][enter], shared["time"][leave], mine["side"],
                       drawn["sizes"], costs)


def means(shared: dict, mine: dict, costs: reprice.Costs, rung: str, draws: int,
          rng: np.random.Generator) -> np.ndarray:
    """The mean P/L per trade of every monkey of one strategy under one rung.

    Args:
        shared: What grid() returned.
        mine: What located() returned.
        costs: reprice.costs() of the feed and segment.
        rung: A key of REDRAWS.
        draws: How many monkeys.
        rng: Seeded generator; the result depends on it and on nothing else.

    Returns:
        One mean per monkey, length `draws`, priced in blocks of BLOCK trade valuations.
    """
    block = max(1, BLOCK // mine["entry"].size)
    out = np.empty(draws)
    for done in range(0, draws, block):
        batch = min(block, draws - done)
        out[done:done + batch] = price(shared, mine, draw(shared, mine, rung, batch, rng),
                                       costs)[0].mean(axis=1)
    return out


def z(seen: float, drawn: np.ndarray) -> float:
    """Where the real run sits among its monkeys, in their own standard deviations.

    Args:
        seen: The real run's statistic.
        drawn: The same statistic over every monkey.

    Returns:
        (seen - mean of the monkeys) / their standard deviation; NaN when they do not vary.
        Unlike the empirical p it has no floor at 1 / (draws + 1), and it reads on the scale
        of a t.
    """
    spread = drawn.std(ddof=1)
    return float((seen - drawn.mean()) / spread) if spread > 0 else float("nan")
