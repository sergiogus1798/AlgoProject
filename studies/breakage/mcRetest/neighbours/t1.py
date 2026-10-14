#!/usr/bin/env python3
"""T1 of step 14: how much of a mother's excess her parameter neighbours keep, on build and on oos1."""

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import cast

import numpy as np
import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from core import assetdata, barstore, manifest
from core.paths import export_dir
from engines.market import reprice
from engines.variants import excess as engines_excess
from studies.breakage.mcRetest.model.retention import retention
from studies.breakage.mcRetest.neighbours import excess
from studies.screening.gate import inputs as gate

STORE, FILE = "T1_Neighbours", "neighbours.parquet"
BATCH = (
    "neighbours"  # the tag `sqx.export.export_retest --batch` files the trades under
)
SEGMENTS = ("build", "oos1")  # the fact names are the contract: oos2 is never read
# The measure's parameters are the gate's, not a copy: T1's excess must be step 8's.
GATE = Path(__file__).resolve().parents[3] / "screening" / "gate" / "config.yaml"
COLLISION = r"\(\d+\)$"  # what SQX appends to a duplicate on reload


def summary(rows: pd.DataFrame) -> dict[str, float]:
    """One mother's T1 facts from her per-neighbour table.

    Args:
        rows: Her rows of the stored table: `neighbour` (0 is the mother herself) and, per
            segment, `<segment>_excess`, `_profit` and `_drift`.

    Returns:
        `t1.<segment>.ret_med`, `.ret_p5`, `.f_pos` and `.n` (retention of the EXCESS total),
        `.ret_benef` (median retention of the profit total) and `.beta_share` (the drift the
        mother collected over her profit; NaN when she did not earn), for build and for oos1,
        and `t1.rho_vec`, Spearman's rank correlation between the neighbours' build excess and
        their oos1 excess. A retention is NaN when the mother's own total is not positive.
        Two facts that judge nothing (encargo 65 §3d): `t1.oos1.percentil_madre`, where the
        mother's oos1 excess (net of drift) stands among her neighbours' — 0 to 100, ties
        counting half — and `t1.dd_r_p99`, the 99th percentile of the neighbours' maximum
        drawdown over build and oos1 together, in R (NaN on a table measured before the
        `dd_r` column existed): the dispersion that fixes k.
    """
    mother, runs = (
        rows[rows["neighbour"] == 0].iloc[0],
        cast(pd.DataFrame, rows[rows["neighbour"] > 0]),
    )
    out = {}
    for seg in SEGMENTS:
        profit = float(mother[f"{seg}_profit"])
        kept = retention(
            runs[f"{seg}_excess"].to_numpy(), float(mother[f"{seg}_excess"])
        )
        out |= {f"t1.{seg}.{key}": value for key, value in kept.items()}
        out[f"t1.{seg}.ret_benef"] = retention(
            runs[f"{seg}_profit"].to_numpy(), profit
        )["ret_med"]
        out[f"t1.{seg}.beta_share"] = (
            float(mother[f"{seg}_drift"]) / profit if profit > 0 else float("nan")
        )
    ranks = runs[[f"{seg}_excess" for seg in SEGMENTS]].rank()
    out["t1.rho_vec"] = float(ranks.iloc[:, 0].corr(ranks.iloc[:, 1]))
    here, theirs = float(mother["oos1_excess"]), runs["oos1_excess"].to_numpy()
    out["t1.oos1.percentil_madre"] = 100 * float(
        (theirs < here).mean() + (theirs == here).mean() / 2
    )
    out["t1.dd_r_p99"] = (
        float(np.percentile(runs["dd_r"], 99)) if "dd_r" in runs else float("nan")
    )
    return out


def table(project: str, day: str, strategy: str) -> pd.DataFrame | None:
    """One mother's per-neighbour table, from the newest measure not after `day`.

    Args:
        project: Project name.
        day: YYYY-MM-DD; the study's own day. The batch may have been measured before it.
        strategy: The mother, as the databank names her file or without its «Strategy ».

    Returns:
        One row per retested file of hers — `strategy`, `variant_id`, `neighbour` (0 is the
        mother) and per segment `<segment>_excess`, `_profit`, `_drift`, `_trades` — or None
        when no batch holds her.
    """
    root = export_dir(project, STORE, day).parent
    days = sorted(
        d.name for d in root.glob("*") if d.name <= day and (d / FILE).exists()
    )
    if not days:
        return None
    names = {strategy, strategy.removeprefix("Strategy "), f"Strategy {strategy}"}
    rows = pd.read_parquet(
        root / days[-1] / FILE, filters=[("strategy", "in", sorted(names))]
    )
    return rows.reset_index(drop=True) if len(rows) else None


def facts(project: str, day: str, strategy: str) -> dict[str, float] | None:
    """One mother's T1 facts (`summary`), or None when no neighbour batch exists for her."""
    rows = table(project, day, strategy)
    return None if rows is None else summary(rows)


def measure(project: str, work: Path, symbol: str, timeframe: str, day: str) -> Path:
    """Price a retested batch's exported trades and store the per-neighbour table.

    Args:
        project: Project name; the trades are its newest `--batch neighbours` export of each leg.
        work: The batch directory: `manifest.parquet` and `ran.json`.
        symbol: The asset, as `assets/symbols/` spells it: its card gives costs and windows.
        timeframe: The project's timeframe.
        day: The date the table is stored under.

    Returns:
        The parquet written. A file SQX returned without a trade counts with totals of zero; a
        file a leg never returned is left out of the table, and counted on stdout.

    Raises:
        SystemExit: A mother herself (neighbour 0) missing from a leg: nothing to retain against.
    """
    plan = pd.read_parquet(
        work / "manifest.parquet", columns=["variant_id", "strategy", "neighbour"]
    )
    asset = assetdata.load(symbol)
    feed = asset["sqx_symbol"]
    bars = barstore.read(feed, timeframe)
    drift = yaml.safe_load(GATE.read_text(encoding="utf-8"))["drift"]
    out, paths = plan, []
    for leg in json.loads((work / "ran.json").read_text(encoding="utf-8"))["legs"]:
        seg = leg["segment"]
        folder = sorted(
            export_dir(project, leg["databank"], "x").parent.glob(f"*/{BATCH}")
        )[-1]
        trades = pd.read_parquet(folder / "trades.parquet")
        trades = cast(pd.DataFrame, trades[trades["Symbol"] == feed])
        trades = trades.assign(
            variant_id=trades["strategy"]
            .astype(str)
            .str.replace(COLLISION, "", regex=True)
        )
        back = set(
            pd.read_csv(folder / "identity.csv")["strategy"].str.replace(
                COLLISION, "", regex=True
            )
        )
        span = (str(asset["segments"][seg]["from"]), str(asset["segments"][seg]["to"]))
        per = engines_excess.per_trade(
            trades, bars, reprice.costs(feed, seg), span, drift, feed
        )
        paths.append(
            per.assign(**{"Close time": trades["Close time"]})[
                ["variant_id", "Close time", "profit"]
            ]
        )
        got = excess.summed(per)
        got = got.reindex(
            plan.loc[plan["variant_id"].isin(list(back)), "variant_id"]
        ).fillna(0.0)
        out = out.merge(
            got.add_prefix(f"{seg}_"), left_on="variant_id", right_index=True
        )
    out = out.merge(
        excess.drawdowns(paths, gate.market(feed)["risk"]).rename("dd_r"),
        left_on="variant_id",
        right_index=True,
        how="left",
    ).fillna({"dd_r": 0.0})
    orphans = sorted(
        set(plan["strategy"]) - set(out.loc[out["neighbour"] == 0, "strategy"])
    )
    if orphans:
        raise SystemExit(f"la madre no volvió del retest en algún tramo: {orphans}")
    print(
        f"{len(out)} de {len(plan)} ficheros medidos ({len(plan) - len(out)} no volvieron)"
    )
    path = export_dir(project, STORE, day) / FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(path, compression="zstd", index=False)
    manifest.write(
        path.parent,
        {"project": project, "batch": str(work), "feed": feed},
        "studies.breakage.mcRetest.neighbours.t1",
        {FILE: len(out)},
    )
    return path


def main() -> None:
    """Measure one retested neighbour batch and print each mother's T1 facts."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument(
        "--work",
        required=True,
        type=Path,
        help="the batch directory sqx.variants.neighbourbatch made and retested",
    )
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--timeframe", required=True)
    ap.add_argument("--day", default=date.today().isoformat())
    a = ap.parse_args()
    path = measure(a.project, a.work, a.symbol, a.timeframe, a.day)
    rows = pd.read_parquet(path)
    with pd.option_context("display.width", 200, "display.max_columns", None):
        print(
            pd.DataFrame({name: summary(own) for name, own in rows.groupby("strategy")})
            .round(3)
            .to_string()
        )
    print(f"-> {path}")


if __name__ == "__main__":
    main()
