"""What a monkey strategy is: one real strategy's footprint, its entries handed to chance."""

import numpy as np
import pandas as pd

from engines.nulls import barrier, model, simulate

SAMPLES = ("IS", "OOS")     # the gate's names: the asset's `build` segment and its `oos1`


def atr_sized(kept: dict, enter: np.ndarray) -> np.ndarray:
    """Each drawn trade sized by the volatility of the bar it landed on.

    Args:
        kept: What simulate.fixed() returned for the donor.
        enter: Entry bar of every drawn trade.

    Returns:
        `c / ATR(entry)`, `c` the donor's median size x ATR at its own entries. The donor's
        own size carries the ATR of the REAL entry: moved to a bar twice as volatile it risks
        twice the money, which no sizing rule would have allowed (🔬 2026-10-04, 300 XAUUSD
        H1 donors: 79 % of `timing` monkeys showed a trade 5R under water against 1 % of the
        real ones). The ATR period is the engine's, not the strategy's, which is not fitted.
    """
    located, atr = kept["located"], kept["atr"]
    return np.median(located["size"] * atr[located["entry"]]) / atr[enter]


SIZING = {"donor": lambda kept, enter, sizes: sizes,
          "atr": lambda kept, enter, sizes: atr_sized(kept, enter)}


def monkeys(donor: pd.DataFrame, frame: pd.DataFrame, nullcfg: dict, knobs: dict,
            key: str) -> tuple[pd.DataFrame, float]:
    """`draws` monkey strategies with one real strategy's footprint, as trade lists.

    Args:
        donor: One real strategy's trades on both samples (`sample` IS/OOS), as harvested.
        frame: The bars it was priced on.
        nullcfg: What engines.nulls.inputs.config() returned; `nulls.seed` is the root.
        knobs: `monkeys` of config.yaml: `rung`, a key of engines.nulls.model.RUNGS (what
            the monkey keeps of the donor); `sizing`, a key of SIZING (`donor`: the sizes
            the rung drew, `atr`: re-sized at its own entry); `per_donor`, how many.
        key: The donor's identity. It enters the seed and names the monkeys `<key>#<j>`.

    Returns:
        The trades in the gate's shape (`identity`, `sample`, times, `Type`, `Size`, prices,
        `Profit/Loss`, `MAE ($)`), and the worse of the two samples' reconciliations of the
        donor's own P/L: below `verdict.RECONCILE_FLOOR` the monkeys are priced by arithmetic
        that did not reproduce SQX and must not be read. Each sample is drawn inside the
        window the donor occupied in it, priced by `barrier.pnl` at the donor's measured
        point value and per-trade cost — the engine's own lines, so a monkey here is the run
        `simulate.nulls` measures, kept trade by trade. `MAE ($)` is the worst bar extreme
        between entry and exit against the entry price: SQX reads it on M1, this on the
        strategy's bars, so it is never deeper than SQX's would be.
    """
    parts, corr, rung, draws = [], 1.0, knobs["rung"], knobs["per_donor"]
    for i, sample in enumerate(SAMPLES):
        own = donor[donor["sample"] == sample].sort_values("Open time").reset_index(drop=True)
        kept = simulate.fixed(own, frame, nullcfg)
        corr = min(corr, kept["checks"]["corr"])
        rng = np.random.default_rng([nullcfg["nulls"]["seed"], simulate._stable(key),
                                     model.RUNG_ID[rung], i])
        drawn = {k: np.ascontiguousarray(v).ravel()
                 for k, v in model.RUNGS[rung](kept["located"], draws, rng).items()}
        bars, enter = kept["bars"], drawn["entries"]
        drawn["sizes"] = SIZING[knobs["sizing"]](kept, enter, drawn["sizes"])
        leave, price = barrier.exits(enter, drawn["holds"], bars, {}, "pessimistic")
        pnl = barrier.pnl(enter, leave, price, drawn["sizes"], bars["enter_px"],
                          np.tile(kept["cost"], draws), kept["value"])
        # Worst price while held: the low for a long, the high for a short (value < 0). In
        # entry order, so the stretches reduceat scans between two trades stay short.
        order = np.argsort(enter, kind="stable")
        worst = np.empty(len(enter))
        worst[order] = (np.minimum if kept["value"] > 0 else np.maximum).reduceat(
            bars["low" if kept["value"] > 0 else "high"],
            np.column_stack([enter[order], leave[order]]).ravel())[::2]
        mae = np.minimum(kept["value"] * drawn["sizes"] * (worst - bars["enter_px"][enter]), 0.0)
        parts.append(pd.DataFrame({
            "identity": np.repeat([f"{key}#{j:04d}" for j in range(draws)], len(own)),
            "sample": sample, "Open time": frame.index[enter], "Close time": frame.index[leave],
            "Type": str(own["Type"].iloc[0]), "Size": drawn["sizes"],
            "Open price": bars["enter_px"][enter], "Close price": price,
            "Profit/Loss": pnl, "MAE ($)": mae}))
    return pd.concat(parts, ignore_index=True), corr


def curve(trades: pd.DataFrame, first: str, end: str) -> pd.DataFrame:
    """The daily cumulative P&L the gate's curve screens read, from trade lists.

    Args:
        trades: What monkeys() returned, any number of strategies.
        first: First day of the build window.
        end: Last day of the out-of-sample one.

    Returns:
        Days x identity, each trade's P/L booked on the day it closed, over every business
        day of the window. SQX's own curve is each day's LOWEST equity, floating included
        (OPEN.md #88); this one is closed P&L only, so a monkey's drawdown and worst day
        read milder than a real strategy's would.
    """
    booked = trades.pivot_table(index=trades["Close time"].dt.normalize(), columns="identity",
                                values="Profit/Loss", aggfunc="sum")
    days = pd.bdate_range(first, end).union(booked.index)
    return booked.reindex(days).fillna(0.0).cumsum()
