"""One strategy's stop read from its MAE — every X side by side, never one chosen — as the contract's data."""

import time

import pandas as pd

from core.study import blocks, result as envelope
from studies.closing.atrCalculator import (grid, mae, noreturn, stability, sqxview, threshold,
                                           transfer, view)

MODULE = "studies.closing.atrCalculator"
OOS = ("oos1", "oos2")


def reading(trades: pd.DataFrame, inputs: dict, cfg: dict) -> dict:
    """§2 on one strategy's trades without a stop: every X, its zone, their transfer.

    Args:
        trades: The reference trades of one strategy, every segment.
        inputs: What load.load() returned.
        cfg: What `inputs.config` returned.

    Returns:
        `measured` (per-trade MAE and result in ATR), `xs` (one row per percentile with its
        interval, zone and effective percentile in each OOS window), `curve` (the point of
        no return), `shapes` (IS against each OOS window) and `winners` (MAE in ATR of the
        winners per segment).
    """
    measured = mae.measure(trades, inputs["bars_index"], inputs["atr"], inputs["point_value"])
    winners = {s: measured.loc[(measured["segment"] == s) & measured["winner"], "mae_atr"]
               .to_numpy() for s in ("build",) + OOS}
    xs = threshold.x_values(winners["build"], cfg)
    curve = noreturn.curve(measured[measured["segment"] == "build"], cfg)
    xs["zone"] = [noreturn.zone_of(x, curve) for x in xs["x"]]
    shapes = {}
    for s in OOS:
        eff = transfer.effective(xs, winners[s], cfg)
        xs[f"effective_{s}"] = eff["effective"].to_numpy()
        xs[f"transfers_{s}"] = eff["transfers"].to_numpy()
        shapes[s] = transfer.shape(winners["build"], winners[s]) if len(winners[s]) else None
    return {"measured": measured, "xs": xs, "curve": curve, "shapes": shapes,
            "winners": winners}


def summary(found: dict) -> dict:
    """The flat row this strategy adds to the population table and verdict.csv."""
    row = {f"n_winners_{s}": len(v) for s, v in found["winners"].items()}
    for r in found["xs"].itertuples():
        p = r.percentile
        row |= {f"x_p{p}": r.x, f"low_p{p}": r.low, f"high_p{p}": r.high,
                f"unreliable_p{p}": r.unreliable, f"zone_p{p}": r.zone,
                f"effective_oos1_p{p}": r.effective_oos1, f"effective_oos2_p{p}": r.effective_oos2}
    return row


def run(strategy: str, inputs: dict, cfg: dict) -> dict:
    """What stop each percentile gives this strategy, and — with a retested batch — what it costs.

    Args:
        strategy: The mother's name.
        inputs: What load.load() returned.
        cfg: What `inputs.config` returned.

    Returns:
        The contract dict. Verdict `info`: the study describes and the owner decides. Its
        `summary` carries the flat row, and `grid` the stability rows for `stopgrid.csv`.
    """
    started = time.time()
    trades = inputs["trades"]
    found = reading(trades[trades["strategy"] == inputs["reference"][strategy]], inputs, cfg)
    tabs = view.tabs(found, cfg)
    warnings = [{"code": f"unreliable_p{r.percentile}", "state": "watch",
                 "text": f"La X del p{r.percentile} ({r.x:.2f}) tiene un intervalo de "
                         f"{r.low:.2f} a {r.high:.2f}: otro puñado de ganadoras daría otra X."}
                for r in found["xs"].itertuples() if r.unreliable]
    row = summary(found)
    if inputs["batch"] is not None:
        measured = stability.measure(strategy, inputs, cfg)
        tabs += sqxview.tabs(measured, cfg)
        row |= stability.summary(measured)
    said = blocks.verdict(
        f"{len(cfg['stop']['percentiles'])} X, sin elegir", "info",
        "El estudio lee X del MAE de las ganadoras del IS con una regla fijada antes de mirar "
        "(un percentil) y no elige: todos los percentiles van lado a lado y decide el dueño.",
        None, [{"label": f"p{r.percentile}: X", "state":
                "watch" if r.unreliable else "info", "value": r.x,
                "note": f"intervalo {r.low:.2f}–{r.high:.2f}, zona {r.zone}"}
               for r in found["xs"].itertuples()])
    out = envelope.envelope(MODULE, strategy, inputs["identity"].get(strategy), cfg, started,
                            tabs, said, warnings, view.GLOSSARY, row)
    out["grid"] = grid.rows(strategy, found["xs"], cfg)
    return out
