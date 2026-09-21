"""One strategy's whole cross-market analysis: every market, then the base asset's OOS stretch."""

from collections.abc import Callable

import pandas as pd

from core import trades as tradeio
from strategies.crossmarket import views
from strategies.crossmarket.explorer import market_run, oos_run
from strategies.crossmarket.mechanics import curves, envelope
from strategies.crossmarket.simulate import backtest, correlation, portfolio
from strategies.crossmarket.verdict import breadth, inference


def analyse_strategy(setup: dict, cfg: dict, name: str, only: str | None,
                     step: Callable[[str, float], None]) -> dict:
    """The whole cross-market analysis of one strategy.

    Args:
        setup: What serve.main() assembled: universe, bars per feed, trades folder.
        cfg: What config.load() returned.
        name: Strategy name, the CSV's stem.
        only: One market feed to run on its own, or None for all of them.
        step: Called with (what is running, share done) for the progress bar.

    Returns:
        The record the session holds: the per-market rows, every model's full result, the
        markets this strategy produced no trades on at all, the strategy's summary, every
        market's equity curve, the combined portfolio account, the correlation matrix, the
        base asset's own row — the reference case, never evidence — and `oos`, the same
        random-entry test run on the base asset's declared out-of-sample stretch alone. The
        base asset is in the portfolio and in the equity overlay because the question there
        is what the combination does, and the combination the owner would trade has gold in
        it. `oos` is in neither, and in no per-market view: see oos_run.py.
    """
    universe = setup["universe"]
    main = universe["main"]
    base_trades = tradeio.read(setup["trades"] / main / f"{name}.csv")
    base_bars = envelope.window(base_trades, setup["bars"][main])
    # The base asset carries its own bars: the fingerprint compares every market's
    # distributions against it, and that needs its ATR as well as its trades.
    base = {**backtest.setting(base_trades, base_bars, cfg), "bars": base_bars}
    weekly = {main: correlation.weekly_equity(base, base_bars)}
    equity = {main: curves.series(base, cfg)}
    streams = {main: portfolio.priced(base, main)}

    wanted = [m for m in universe["markets"] if only is None or m["feed"] == only]
    # The OOS stretch is one more unit of work when the whole strategy is run; a single-market
    # re-run leaves it alone and work.merged() carries the one already in the session.
    units = len(wanted) + (only is None)
    rows, runs, missing = [], {}, []
    for i, market in enumerate(wanted):
        feed = market["feed"]
        trades = setup["trades"] / feed / f"{name}.csv"
        # The export writes a market's file only when that strategy traded there, so a
        # strategy that never fired on one market simply has no file.
        if not trades.exists():
            missing.append(feed)
            continue
        row, got, extra = market_run.analyse_market(
            cfg, market, trades, setup["bars"][feed], base,
            lambda what, share, i=i: step(what, (i + share) / units))
        rows.append(row)
        runs[feed] = got
        weekly[feed], equity[feed] = extra["weekly"], extra["curve"]
        streams[feed] = extra["stream"]

    oos = (oos_run.run(setup, cfg, name, setup["asset"],
                       lambda what, share: step(what, (len(wanted) + share) / units))
           if only is None else None)
    per_market = pd.DataFrame(rows)
    return {"rows": per_market.to_dict("records"), "runs": runs, "missing": missing,
            "summary": {"family": inference.family(per_market), "missing": len(missing),
                        **breadth.summary(per_market, cfg["diagnostics"]["alpha"])},
            "base": {"feed": main, **market_run.tests(base, base_bars, cfg, main),
                     "trades": len(base["held"])},
            "oos": oos, "equity": equity, "weekly": weekly, "streams": streams,
            **views.build(weekly, streams, runs, cfg)}
