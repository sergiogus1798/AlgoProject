"""One strategy's whole cross-market analysis: every market, then the base asset's OOS stretch."""

from collections.abc import Callable

import pandas as pd

from core import fanout, tradestore
from studies.transfer.crossmarket.mechanics import curves, envelope
from studies.transfer.crossmarket.orchestrate import (market as market_run, stretch as oos_run,
                                                      views)
from studies.transfer.crossmarket.simulate import backtest, correlation
from studies.transfer.crossmarket.verdict import breadth, inference

# What the workers read — the export, every feed's bars, the base asset's setting — set before
# the pool is built so `fork` hands every worker the same pages instead of pickling them.
_SHARED: dict = {}
OOS = "__oos__"   # the task key of the base asset's out-of-sample stretch


def _unit(key: str) -> tuple:
    """One unit of a strategy's analysis in a worker: a market, or the OOS stretch.

    Args:
        key: A market feed, or `OOS`.

    Returns:
        The market's (row, runs, extra), or the stretch's record. Every model and test
        seeds its own generator from `nulls.seed`, so the order the units run in moves nothing.
    """
    got = _SHARED
    quiet = lambda what, share: None      # the parent reports units as they land
    if key == OOS:
        return oos_run.run(got["setup"], got["cfg"], got["name"], got["setup"]["asset"], quiet)
    market = got["markets"][key]
    return market_run.analyse_market(got["cfg"], market, got["trades"][key],
                                     got["setup"]["bars"][key], quiet)


def analyse_strategy(setup: dict, cfg: dict, name: str, only: str | None,
                     step: Callable[[str, float], None]) -> dict:
    """The whole cross-market analysis of one strategy.

    Args:
        setup: What load.load() assembled: universe, bars per feed, the packed trades.
        cfg: What config.load() returned.
        name: Strategy name, the CSV's stem.
        only: One market feed to run on its own, or None for all of them.
        step: Called with (what is running, share done) for the progress bar.

    Returns:
        The record the session holds: the per-market rows, every model's full result, the
        markets this strategy produced no trades on at all, the strategy's summary, every
        market's equity curve, the correlation matrix, the base asset's own row — the
        reference case, never evidence — and `oos`, the same random-entry test run on the
        base asset's declared out-of-sample stretch alone. The base asset is in the equity
        overlay and the correlation matrix. `oos` is in neither, and in no per-market view:
        see oos_run.py.
    """
    universe = setup["universe"]
    main = universe["main"]
    base_trades = tradestore.market(setup["trades"], name, main)
    base_bars = envelope.window(base_trades, setup["bars"][main])
    base = {**backtest.setting(base_trades, base_bars, cfg), "bars": base_bars}
    weekly = {main: correlation.weekly_equity(base, base_bars)}
    equity = {main: curves.series(base, cfg)}

    wanted = [m for m in universe["markets"] if only is None or m["feed"] == only]
    # The OOS stretch is one more unit of work when the whole strategy is run; a single-market
    # re-run leaves it alone and work.merged() carries the one already in the session.
    trades = {m["feed"]: tradestore.market(setup["trades"], name, m["feed"]) for m in wanted}
    # The export carries a market's rows only when that strategy traded there, so a
    # strategy that never fired on one market simply has none.
    missing = [f for f, t in trades.items() if t.empty]
    # 🔬 2026-09-27: run one after another these took one core for ~15 min on nine markets;
    # every market and the OOS stretch are independent, so each is a task of its own, costed
    # by its trade count (knowhow/perf/python-parallelism.md: the unit of cost is the trade).
    costs = {f: len(t) for f, t in trades.items() if not t.empty}
    if only is None:
        costs[OOS] = len(base_trades)
    _SHARED.update(setup=setup, cfg=cfg, name=name, base=base, trades=trades,
                   markets={m["feed"]: m for m in wanted})
    done, oos = {}, None
    for n, (key, got) in enumerate(fanout.run(_unit, costs, len(costs)), 1):
        if key == OOS:
            oos = got
        else:
            done[key] = got
        step(f"{n} de {len(costs)} hechos · {key if key != OOS else 'tramo OOS'}", n / len(costs))
    rows, runs = [], {}
    for feed in (m["feed"] for m in wanted if m["feed"] in done):   # the universe's order
        row, got, extra = done[feed]
        rows.append(row)
        runs[feed] = got
        weekly[feed], equity[feed] = extra["weekly"], extra["curve"]
    per_market = pd.DataFrame(rows)
    return {"rows": per_market.to_dict("records"), "runs": runs, "missing": missing,
            "summary": {"family": inference.family(per_market), "missing": len(missing),
                        **breadth.summary(per_market, cfg["diagnostics"]["alpha"])},
            "base": {"feed": main, **market_run.tests(base, base_bars, cfg, main),
                     "trades": len(base["held"])},
            "oos": oos, "equity": equity, "weekly": weekly,
            **views.build(weekly, runs, cfg)}
