"""One WFM export's whole reading: each mother's L1, L2, redundancy, corrected area and drift."""

from pathlib import Path
from typing import Any, TypedDict, cast

import numpy as np
import pandas as pd

from core import metrics
from engines.weekly import flip, panel
from studies.optimisation.wfm.inputs import asset, export
from studies.optimisation.wfm.measure import drift, excess, gaterule, levels
from studies.optimisation.wfm.model import windows
from studies.optimisation.wfm.verdict import call

CELL = "WF: {runs} runs : {oos_pct} % OOS"  # SQX's own name for a cell
OLD = (
    "este export es anterior al 2026-10-01: no guarda las operaciones de la madre ni las "
    "diez condiciones. Vuelve a exportar con sqx.export.export_wfm"
)


def covered(shapes: pd.DataFrame, spans: dict) -> pd.DataFrame:
    """Years of each segment that each cell's out-of-sample runs cover.

    Args:
        shapes: `model.windows.shape` of one strategy: `result`, `covers_from`, `covers_to`.
        spans: `inputs.asset.of`'s `windows`.

    Returns:
        Indexed by cell, one column per segment; zero where the runs do not reach it.
    """
    first, last = (
        shapes["covers_from"].dt.normalize(),
        shapes["covers_to"].dt.normalize(),
    )
    out = {
        name: (
            (
                last.clip(upper=pd.Timestamp(b) + pd.Timedelta(days=1))
                - first.clip(lower=pd.Timestamp(a))
            ).dt.days.clip(lower=0)
            / metrics.YEAR_DAYS
        )
        for name, (a, b) in spans.items()
    }
    return pd.DataFrame(out).set_index(shapes["result"].astype(str).to_numpy())


class Measured(TypedDict):
    """One mother's oos2 measures: the cells' weekly excess, both levels, shape and recharge."""

    cells: pd.DataFrame
    mother: pd.Series
    ref: pd.Series
    per_year: pd.Series
    l1: dict[str, Any]
    l2: dict[str, Any]
    l1_blocks: dict[str, Any] | None
    straddle: float
    skew: float
    effective: float
    positive: float
    segments: Any
    recharged: dict[str, float]
    centre: str


class Found(gaterule.Area):
    """SQX's area rule on corrected scores: the best rectangle plus the cells passing."""

    cells: int


def one(
    trades: pd.DataFrame,
    mother: pd.DataFrame,
    shapes: pd.DataFrame,
    the: asset.Asset,
    cfg: dict,
    seed: np.random.SeedSequence,
) -> Measured:
    """Everything measured on one mother's cells in oos2.

    Args:
        trades: Its cells' walk-forward trades (`sample` OOS), `result` naming the cell.
        mother: Its own trades with fixed parameters (`main.parquet`), `strategy` naming it.
        shapes: Its rows of `model.windows.shape`, in matrix order.
        the: `inputs.asset.of`.
        cfg: The study's config.
        seed: This mother's child of the run's root seed.

    Returns:
        `cells` (weeks x cells), `mother` and `ref` (weekly series), `per_year` (each
        cell's oos2 excess per year), `l1`, `l2`, `l1_blocks` (L1 again in two-week blocks,
        None unless too many trades straddle a weekend), `straddle`, `skew`, `effective`,
        `positive`, `segments` (cell x segment excess per year), `recharged` (trades and
        money re-charged) and `centre`.
    """
    null, window = cfg["null"], the["windows"][asset.CLEAN]
    years = panel.years(window)
    names = shapes["result"].astype(str).tolist()
    per = excess.per_trade(trades, the, "result")
    cells = excess.weekly(per, window, "result", names)
    fixed = excess.per_trade(mother, the, "strategy")
    alone = excess.weekly(
        fixed, window, "strategy", cast(Any, fixed["strategy"].unique())
    )
    signs = flip.signs(seed, null["draws"], len(cells))
    centre = CELL.format(**cfg["centre"])
    ref = levels.reference(cells, cfg["modo_real"], centre)
    clean = cast(pd.DataFrame, per[per["segment"] == asset.CLEAN])
    straddle = panel.straddle(
        cast(pd.Series, clean["open"]), cast(pd.Series, clean["close"])
    )
    per_year = cells.sum() / years
    return {
        "cells": cells,
        "mother": alone.iloc[:, 0],
        "ref": ref,
        "per_year": per_year,
        "l1": levels.l1(cells, signs, years),
        "l2": levels.l2(ref, alone.iloc[:, 0], signs, years),
        "l1_blocks": levels.l1(
            cells, flip.signs(seed, null["draws"], len(cells), 2), years
        )
        if straddle > null["straddle_max"]
        else None,
        "straddle": straddle,
        "skew": levels.skewness(cells),
        "effective": levels.effective(cells),
        "positive": float((per_year > 0).mean()),
        "segments": excess.by_segment(per, "result", covered(shapes, the["windows"])),
        "recharged": {
            "trades": int(len(clean)),
            "money": float(clean["charge"].sum()),
            "mother_money": float(fixed["charge"].sum()),
        },
        "centre": centre,
    }


def area(scored: pd.DataFrame, rule: dict) -> Found:
    """SQX's area rule on one strategy's corrected scores: cells passing, best rectangle."""
    score = scored.pivot(index="runs", columns="oos_pct", values="score_pct").to_numpy()
    passed = score >= rule["threshold_pct"]
    return {
        **gaterule.area(passed, score, rule["rows"], rule["cols"], rule["min_squares"]),
        "cells": int(passed.sum()),
    }


def facts(got: Measured, drifted: float, found: Found, mode: str) -> dict[str, Any]:
    """The numbers the autopilot's rules and step 20 read, named as the plan froze them.

    Args:
        got: one()'s return.
        drifted: The mother's median share of parameters changed per re-optimisation.
        found: area()'s return.
        mode: `fijo` or `reoptimizado`.

    Returns:
        `l1`, `l2`, `centro`, `celdas_efectivas`, `frac_celdas_positivas`, `deriva`, `area`;
        and `reopt` ONLY in `reoptimizado`, so its rules do not exist in `fijo`.
    """

    def tails(level: dict, first: str) -> dict[str, Any]:
        """One level's own number and its place in the null, without the draws."""
        return {k: level[k] for k in (first, "p_mas", "p_menos", "nulo_p5", "nulo_p95")}

    centre = float(got["per_year"][got["centre"]])
    out = {
        "l1": tails(got["l1"], "mediana_exceso"),
        "l2": tails(got["l2"], "delta"),
        "centro": {"exceso_oos2": centre},
        "celdas_efectivas": got["effective"],
        "frac_celdas_positivas": got["positive"],
        "deriva": drifted,
        "area": {"celdas": found["cells"], "pasa": int(found["passed"])},
    }
    if mode == call.REOPT:
        out["reopt"] = {"centro_exceso": centre, "l2_p_menos": got["l2"]["p_menos"]}
    return out


def read(directory: Path, cfg: dict, only: str | None = None) -> dict[str, Any]:
    """Everything the study concludes about one export.

    Args:
        directory: The export's `wfm/` folder.
        cfg: The parsed `config.yaml`.
        only: One strategy's name, to measure that one alone.

    Returns:
        `measured`, `facts`, `verdicts` and `area` per strategy, and what the tabs draw from:
        `the` (the asset), `checked` and `scored` (the corrected conditions), `rules`,
        `sqx_failed`, `objectives`, `drift`, `stability`, `trades`, `original`, `windows`.
        With `only`, that strategy's numbers are the ones the whole export gives it: its
        seed is its position among the export's strategies, and the drift's parameter
        spread stays the export's.
    """
    original, conditions = export.main(directory), export.conditions(directory)
    if original is None or conditions is None:
        raise SystemExit(OLD)
    everything = export.steps(directory, cfg["read"]["drop_future"])
    names = sorted(everything["strategy"].unique())
    seeds = dict(
        zip(names, np.random.SeedSequence(cfg["null"]["seed"]).spawn(len(names)))
    )
    the = asset.of(
        original["Symbol"].iloc[0],
        original["timeframe"].iloc[0],
        cfg["recharge"]["charged"],
    )
    trades = export.trades(directory)
    chosen = export.chosen(directory)
    drifted = drift.summary(drift.per_step(chosen), chosen).set_index("strategy")
    checked = gaterule.oos_only(conditions, export.cells(directory))
    scored, rules = gaterule.score(checked), export.rules(directory)
    shapes = windows.shape(everything).sort_values(["runs", "oos_pct"])
    out = {"measured": {}, "facts": {}, "verdicts": {}, "area": {}}
    for name in [only] if only else names:
        mine = cast(
            pd.DataFrame,
            trades[(trades["strategy"] == name) & (trades["sample"] == "OOS")],
        )
        got = one(
            mine,
            cast(pd.DataFrame, original[original["strategy"] == name]),
            cast(pd.DataFrame, shapes[shapes["strategy"] == name]),
            the,
            cfg,
            seeds[name],
        )
        found = area(
            cast(pd.DataFrame, scored[scored["strategy"] == name]),
            rules.loc[name].to_dict(),
        )
        said = facts(
            got,
            float(drifted.loc[name, "share_changed_median"]),
            found,
            cfg["modo_real"],
        )
        out["measured"][name], out["area"][name], out["facts"][name] = got, found, said
        out["verdicts"][name] = call.call(said, cfg["modo_real"], cfg["null"]["alpha"])
    return out | {
        "source": str(directory),
        "the": the,
        "checked": checked,
        "scored": scored,
        "rules": rules[["threshold_pct", "rows", "cols", "min_squares"]],
        "sqx_failed": rules["sqx_failed"].to_dict(),
        "objectives": export.objectives(directory),
        "drift": drifted.reset_index(),
        "stability": drift.stability(chosen),
        "trades": trades if not only else trades[trades["strategy"] == only],
        "original": original,
        "windows": everything,
    }
