"""What a monkey strategy is: one real strategy's footprint, its entries handed to chance."""

import numpy as np
import pandas as pd

from engines.nulls import barrier, simulate, windowed

SAMPLES = ("IS", "OOS")     # the gate's names: the asset's `build` segment and its `oos1`


def atr_sized(kept: dict, enter: np.ndarray) -> np.ndarray:
    """Each drawn trade sized by the volatility known when it opens, as the gate's monkey is.

    Args:
        kept: What simulate.fixed() returned for the donor.
        enter: Entry bar of every drawn trade.

    Returns:
        `windowed.atr_sized` on the ATR of the bar BEFORE each entry: the bar's own would be
        looking ahead (owner, 2026-10-07). The ATR period is the engine's, not the strategy's.
    """
    located, known = kept["located"], np.r_[np.nan, kept["atr"][:-1]]
    return windowed.atr_sized(known, located["entry"], located["size"], enter)


def donor_sized(kept: dict, enter: np.ndarray, flat: bool) -> np.ndarray:
    """The donor's lots on every drawn trade (`enter` is the raveled draws x trades), or their mean
    when the rung strips the sizing."""
    size = kept["located"]["size"]
    return np.full(enter.shape, size.mean()) if flat else np.tile(size, enter.size // size.size)


SIZING = {"donor": donor_sized, "atr": lambda kept, enter, flat: atr_sized(kept, enter)}


def monkeys(donor: pd.DataFrame, frame: pd.DataFrame, nullcfg: dict, knobs: dict,
            key: str) -> tuple[pd.DataFrame, float]:
    """`draws` monkey strategies with one real strategy's footprint, as trade lists.

    Args:
        donor: One real strategy's trades on both samples (`sample` IS/OOS), as harvested.
        frame: The bars it was priced on.
        nullcfg: What engines.nulls.inputs.config() returned; `nulls.seed` is the root.
        knobs: `monkeys` of config.yaml: `rung`, a key of engines.nulls.model.RUNGS (what
            the monkey keeps of the donor); `sizing`, a key of SIZING (`donor`: the sizes
            the donor's, or their mean on a rung that strips the sizing;
            `atr`: re-sized at its own entry); `per_donor`, how many.
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
        rng = np.random.default_rng([nullcfg["nulls"]["seed"], simulate._stable(key), i])
        # The hours null (owner, 2026-10-12, encargo 65 §5.2): each monkey trade re-enters at a
        # uniform bar of the donor's window AND at the clock hour of the trade it replaces.
        at = kept["located"]
        span = np.arange(at["window"][0], at["window"][1] + 1)
        shared = windowed.grid(frame, span, np.zeros(span.size, int))
        mine = windowed.located(shared, at["entry"], at["exit"], at["size"],
                                np.where(own["Type"].astype(object) == "Buy", 1.0, -1.0),
                                np.zeros(at["entry"].size, int))
        drawn = {k: np.ascontiguousarray(v).ravel()
                 for k, v in windowed.draw(shared, mine, rung, draws, rng).items()}
        bars, enter = kept["bars"], drawn["entries"]
        drawn["sizes"] = SIZING[knobs["sizing"]](kept, enter, windowed.REDRAWS[rung][1])
        assert np.isfinite(drawn["sizes"]).all(), f"{key}: a {sample} trade has no ATR to size by"
        leave, price = barrier.vertical(enter, drawn["holds"], bars["leave_px"])
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


def planted(oos: pd.DataFrame, edge: float) -> tuple[pd.DataFrame, pd.Series]:
    """The gate's per-trade table of oos1 with an edge of known size, NET of costs, planted.

    Args:
        oos: Level 1a's table: `identity`, `pnl`, `cost` and `excess`.
        edge: The planted Sharpe per trade, net of the costs the gate charges.

    Returns:
        The table with one constant per strategy added to the `pnl` and the `excess` of each
        of its trades, and that constant per identity: `edge x sd(its excess)` plus its mean
        `cost` per trade (owner, 2026-10-07). `excess` is the series R3 judges — the
        repricer's P/L after the declared costs, minus the drift term — and its sd does not
        move, so the monkey's cost is paid back on average and what is left is its luck
        around `edge x sd`: an expected net Sharpe of `edge`, and a plain t that rises by
        (edge + mean cost / sd) x sqrt(n) exactly. The null population is not planted and
        keeps paying.
    """
    by = oos.groupby("identity", sort=False)
    add = edge * by["excess"].transform("std") + by["cost"].transform("mean")
    return (oos.assign(pnl=oos["pnl"] + add, excess=oos["excess"] + add),
            add.groupby(oos["identity"], sort=False).first())
