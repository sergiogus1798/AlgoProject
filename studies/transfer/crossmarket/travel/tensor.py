"""The tensor of the travel test: every run's P/L in R per market and calendar cell, and the real run's beside it."""

from typing import Any, TypedDict

import numpy as np
import pandas as pd

from engines.market import reprice
from studies.transfer.crossmarket.travel import shift, sizing
from studies.transfer.crossmarket.travel.cells import occupancy

class _Market(TypedDict):
    """What pricing needs of one market: bars, times, cell of each bar, costs, risk, lots, move-on bar, data per cell."""

    bars: pd.DataFrame
    seconds: np.ndarray
    time: np.ndarray
    cell: np.ndarray
    costs: reprice.Costs
    risk: float
    lots: np.ndarray
    next: np.ndarray
    data: np.ndarray


class Market(_Market, total=False):
    """`_Market` plus `share`, the displaced share per cell that `exclude` sets."""

    share: np.ndarray


class Built(TypedDict):
    """One strategy's tensor: markets, real and null R (judged and net), and the trades closed per market and cell."""

    markets: list[str]
    real: np.ndarray
    null: np.ndarray
    real_net: np.ndarray
    null_net: np.ndarray
    trades: np.ndarray


CELLS = 2_000_000      # runs x trades priced at once: 16 MB per array, a dozen arrays alive


def market(bars: pd.DataFrame, costs: reprice.Costs, params: dict[str, Any], cells: pd.DataFrame,
           flat_fraction: float = 0.0) -> Market:
    """What pricing needs of one market, computed once and shared by every strategy.

    Args:
        bars: Its bars on the strategies' timeframe, indexed by bar open time, ALREADY CUT to
            the stretch this market may be read on (`inputs.markets.own_window`): a moved
            trade lands on, and is closed by, any bar given here.
        costs: As `reprice.costs()` returns it.
        params: As `sizing.doctrine()` returns it.
        cells: As `cells.table()` returns it.
        flat_fraction: travel.validity.flat_atr_fraction, see `sizing.usable`.

    Returns:
        The bars, their times, the cell of each bar, the lots a trade opening on each bar
        takes, where an entry on an excluded bar moves to, and `data`: whether the market has
        any bar in each cell.
    """
    seconds = bars.index.to_numpy("datetime64[s]").astype(np.int64)
    start = cells["start"].to_numpy("datetime64[s]").astype(np.int64)
    cell = np.searchsorted(start, seconds, side="right") - 1
    atr_ = sizing.entry_atr(bars, params["ATRPeriod"])
    return Market(bars=bars, seconds=seconds, time=bars.index.to_numpy(), cell=cell,
                  costs=costs, risk=params["Amount"],
                  lots=sizing.lots(atr_, costs["point_value"], params),
                  next=sizing.usable(atr_, flat_fraction),
                  data=np.bincount(cell, minlength=len(cells)) > 0)


PROBE_ENTRIES, PROBE_DRAWS = 20_000, 300     # the validity probe: entries per market, shifts per entry


def displaced_share(mkt: Market, cells: pd.DataFrame, shifts: np.ndarray, step: str) -> np.ndarray:
    """Per cell, the share of uniformly placed entries a shift displaces to a LATER bar.

    A moved stamp with no bar takes the next bar, so after a hole of the data every run piles on
    one bar. The probe puts a fixed sample of entries blind to any strategy (generator seed 0,
    the first PROBE_DRAWS rows of `shifts`) and counts, per cell the entry sits in, how often the
    landing bar is not the stamp's own instant, or is a defective bar that moves on again.

    Args:
        mkt: As market() returns it.
        cells, shifts, step: As build() takes them.

    Returns:
        (cells,) shares in 0..1; NaN where the probe placed no entry (a cell with no bars).
    """
    last = len(mkt["seconds"]) - 1
    pick = np.sort(np.random.default_rng(0).choice(last, min(PROBE_ENTRIES, last), replace=False))
    landed = np.minimum(shift.entries(mkt["seconds"], pick, mkt["cell"][pick], cells,
                                      shifts[:PROBE_DRAWS], step), last)
    unit = shift.WEEK if step == "week" else shift.DAY
    bad = ((mkt["seconds"][landed] - mkt["seconds"][pick][None, :]) % unit != 0) \
        | (mkt["next"][landed] != landed)
    share = pd.Series(bad.mean(0)).groupby(mkt["cell"][pick]).mean()
    return share.reindex(range(len(cells))).to_numpy()


def exclude(mkt: Market, cells: pd.DataFrame, shifts: np.ndarray, step: str, limit: float) -> np.ndarray:
    """Leave out of the tensor every cell of this market whose displaced share exceeds `limit`.

    Sets `mkt["share"]` and clears `mkt["data"]` there, so `build` writes NaN (never 0) for the
    real run, every random run and the count alike. Depends only on the bars and the cells.

    Returns:
        (cells,) bool, True where the cell was excluded.
    """
    mkt["share"] = displaced_share(mkt, cells, shifts, step)
    out = np.nan_to_num(mkt["share"], nan=0.0) > limit
    mkt["data"] = mkt["data"] & ~out
    return out


def _runs(mkt: Market, held: pd.DataFrame, side: np.ndarray, shifts: np.ndarray,
          cells: pd.DataFrame, step: str) -> tuple[np.ndarray, np.ndarray]:
    """(runs, cells) NET and GROSS (net + cost) P/L in R of one market's trades under each row of
    shifts, summed by the cell each trade CLOSES in. Sized by the doctrine at the bar it lands on, priced by the one
    repricer: the real run is the row of zeros through this same code."""
    last = len(mkt["seconds"]) - 1
    entry = held["entry"].to_numpy()
    moved = shift.entries(mkt["seconds"], entry, mkt["cell"][entry], cells, shifts, step)
    moved = mkt["next"][np.minimum(moved, last)]
    leave = np.minimum(moved + held["hold"].to_numpy(), last)
    net, cost = reprice.pnl(reprice.fills(mkt["bars"], moved), reprice.fills(mkt["bars"], leave),
                         mkt["time"][moved], mkt["time"][leave], side, mkt["lots"][moved],
                         mkt["costs"])
    flat = np.arange(len(shifts))[:, None] * len(cells) + mkt["cell"][leave]
    by = lambda x: np.bincount(flat.ravel(), (x / mkt["risk"]).ravel(),
                               len(shifts) * len(cells)).reshape(len(shifts), len(cells))
    return by(net), by(net + cost)


def build(trades: dict[str, pd.DataFrame], markets: dict[str, Market], cells: pd.DataFrame,
          shifts: np.ndarray, step: str, judge: str = "net") -> Built:
    """One strategy's tensor: the real run and every random run, per market and cell.

    Args:
        trades: {market: its trades of this strategy}, SQX's `Open time`, `Close time` and
            `Type` ("Buy"/"Sell"); a market the strategy never traded carries an empty frame.
            SQX's own sizes and P/L are not read.
        markets: {market: what market() returned}; its order is the tensor's.
        cells: As `cells.table()` returns it.
        shifts: (runs, cells), from `shift.draws()`.
        step: travel.shift_step.
        judge: travel.judge_on, "gross" or "net": what `real` and `null` hold.

    Returns:
        `markets` (names), `real` (markets, cells), `null` (runs, markets, cells) and `trades`
        (markets, cells; real trades closed there). `real` and `null` are on the judged quantity;
        `real_net` and `null_net` always on net R (the same arrays when judge is "net"). All in R except `trades`. A cell the market
        has NO BARS in is NaN in all three; a cell it has bars in and no trade closed in is 0.
        Sum them only with `stat.total`, which keeps that difference.
    """
    names = list(markets)
    real = np.full((len(names), len(cells)), np.nan)
    count, null = real.copy(), np.full((len(shifts), *real.shape), np.nan)
    g = judge == "gross"
    real_net, null_net = (real.copy(), null.copy()) if g else (real, null)
    still = np.zeros((1, len(cells)), np.int64)
    for j, name in enumerate(names):
        mkt, mine = markets[name], trades[name]
        held = occupancy(mine, mkt["bars"])
        side = np.where(mine.loc[held.index, "Type"].astype(str) == "Buy", 1.0, -1.0)
        closed = np.bincount(mkt["cell"][held["exit"].to_numpy()], minlength=len(cells))
        count[j] = np.where(mkt["data"], closed, np.nan)
        now = _runs(mkt, held, side, still, cells, step)
        real_net[j] = np.where(mkt["data"], now[0][0], np.nan)
        real[j] = np.where(mkt["data"], now[g][0], np.nan)
        chunk = max(1, CELLS // max(1, len(held)))
        for at in range(0, len(shifts), chunk):
            got = _runs(mkt, held, side, shifts[at:at + chunk], cells, step)
            null_net[at:at + chunk, j] = np.where(mkt["data"], got[0], np.nan)
            null[at:at + chunk, j] = np.where(mkt["data"], got[g], np.nan)
    return Built(markets=names, real=real, null=null, real_net=real_net,
                 null_net=null_net, trades=count)
