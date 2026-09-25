"""The random-entry study run on the out-of-sample stretch of the main backtest alone.

The cross-market test asks whether the timing survives on markets the strategy was never
fitted to. This asks the same question of the **same** market over the stretch the builder
optimised nothing on: `assets/_markets.yaml`'s declared `out_of_sample` range, the project's own
<OutOfSample>. It is deliberately kept out of `record["rows"]` and `record["runs"]` — the
joint null, the breadth count, the portfolio and the correlation matrix are all statements
about *other* markets, and gold-2018 is neither another market nor independent of the silver
and Brent draws over the same dates. It gets its own record key and its own tab."""

from collections.abc import Callable

from core import tradestore
from strategies.crossmarket.orchestrate import market as market_run
from strategies.crossmarket.inputs import markets
from strategies.crossmarket.mechanics import envelope
from strategies.crossmarket.simulate import backtest, realrun, stress
from strategies.crossmarket.verdict import inference

# The stretch entered selection twice — inside every sampleType=127 acceptance condition,
# since the full period contains it, and explicitly through the walk-forward matrix's OOS
# net profit — so a p computed here is a statement about this window's mechanics and not
# about unseen data. Measured 2026-09-17 on Build-Task3.xml; knowhow/conditions/selection-window.md.
SELECTED = "selected_window"


def label(feed: str, span: dict[str, str]) -> str:
    """How the stretch is named everywhere it is shown.

    Args:
        feed: The base asset's SQX symbol.
        span: What markets.out_of_sample() returned.

    Returns:
        A display key, e.g. "XAUUSD_DukasM1_Infinox · OOS 2018-2022". It is never a key into
        `setup["bars"]` or into the export: the data always comes from `feed` itself.
    """
    return f'{feed} · OOS {span["from"][:4]}-{span["to"][:4]}'


def run(setup: dict, cfg: dict, name: str, asset: str,
        step: Callable[[str, float], None]) -> dict | None:
    """The same random-entry test, on the main backtest's out-of-sample stretch only.

    Args:
        setup: What load.load() assembled.
        cfg: What config.load() returned.
        name: Strategy name, the CSV's stem.
        asset: Base asset, for the declared range.
        step: Called with (what is running, share done) for the progress bar.

    Returns:
        {"row", "runs", "span", "feed"} — the flat row with its warnings, one full result per
        null model, and the stretch it ran on — or None where the base asset declares no
        out-of-sample range. There is **no window sweep** here: the sweep cuts the run into
        3-year, 1-year and 6-month blocks, and a five-year stretch holding a few hundred
        trades leaves every block under `sweep.min_trades`, so every point would be withheld.
        The cost-and-execution stress is run, because it needs no such room.
    """
    span = markets.out_of_sample(asset)
    if span is None:
        return None
    feed = setup["universe"]["main"]
    whole = tradestore.market(setup["trades"], name, feed)
    real = envelope.segment(whole, span)
    # The bars are sliced to this stretch's own first entry and last exit, exactly as a
    # market is: a null that may place a trade in 2010 is not testing the out-of-sample
    # window, it is testing the whole backtest with fewer trades.
    bars = envelope.window(real, setup["bars"][feed])
    fixed = backtest.setting(real, bars, cfg)
    shown = label(feed, span)
    models = cfg["nulls"]["models"]
    units = len(models) + 1
    model_row, runs = market_run.nulls(fixed, bars, cfg, models, lambda m, share: step(
        f"{shown} · {m}", share * len(models) / units))
    row = {"feed": shown, "category": "tramo OOS del backtest principal",
           "data_from": span["from"], **model_row}
    step(f"{shown} · coste y ejecución", (units - 1) / units)
    row.update(market_run.tests(fixed, bars, cfg, feed))
    row["exits"] = realrun.exits(fixed)
    row["reproducible_pnl"] = sum(e["gross_share"] for e in row["exits"] if e["reproducible"])
    runs["stress"] = stress.simulate(fixed, bars, cfg, row["stress_settings"])
    # SELECTED is appended rather than checked: nothing in the row can reveal that this
    # window was read by the acceptance conditions. It is a fact about the project, and it
    # is the single most important thing to say about the number beside it.
    row["warnings"] = inference.warnings(row, cfg) + [SELECTED]
    return {"row": row, "runs": runs, "span": span, "feed": feed,
            "kept": len(real), "of": len(whole)}

