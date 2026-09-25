"""Run the null study over every strategy of one export and say what survives chance."""

import argparse
import json
from datetime import date
from pathlib import Path

import pandas as pd

from core.manifest import write as write_manifest
from core.paths import DATA, report_dir
from nulls import inputs, model, simulate, verdict


def newest(project: str, databank: str) -> Path:
    """The most recent dated trade export of one databank.

    Args:
        project: Project name.
        databank: Databank name as SQX shows it.

    Returns:
        Its `trades.parquet`. Exports are dated and immutable, so the newest is the one
        with the most strategies in it, never a partially refreshed older one.
    """
    folder = DATA / "raw" / project / databank.replace(" ", "_")
    return sorted(folder.glob("*/trades.parquet"))[-1]


def one(trades: pd.DataFrame, frame: pd.DataFrame, cfg: dict) -> dict:
    """Every rung, every statistic and every warning for one strategy.

    Args:
        trades: That strategy's trades on the chosen sample.
        frame: The bars they were priced on.
        cfg: What inputs.config() returned.

    Returns:
        One row: the real statistics, the p of each statistic under each rung, the
        attribution of the headline statistic, and the reasons to distrust all of it.
    """
    kept = simulate.fixed(trades, frame, cfg)
    names = cfg["statistics"]["report"]
    seen = simulate.real(kept, names)
    per_rung = {rung: simulate.nulls(kept, rung, cfg) for rung in cfg["nulls"]["rungs"]}
    head = cfg["nulls"]["headline"]
    found = {name: verdict.pvalue(seen[name], per_rung[head][name], name) for name in names}
    row = {"n": len(trades), "reconcile": kept["checks"]["corr"]}
    row |= {f"real_{name}": seen[name] for name in names}
    row |= {f"p_{rung}_{name}": verdict.pvalue(seen[name], values[name], name)
            for rung, values in per_rung.items() for name in names}
    row |= {f"edge_{key}": value
            for key, value in verdict.attribute(seen, per_rung, names[0]).items()}
    row["distrust"] = " | ".join(verdict.distrust(kept, found, len(trades), cfg))
    return row


def main() -> None:
    """Run every strategy of one export through every rung and write the panel."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True)
    ap.add_argument("--feed", required=True, help="SQX feed name, e.g. XAUUSD_DukasM1_Infinox")
    ap.add_argument("--timeframe", default="M30")
    ap.add_argument("--sample", default="OOS1", help="IST in sample, OOS1 out of it")
    ap.add_argument("--limit", type=int, default=0, help="first N strategies only, for a trial")
    ap.add_argument("--set", action="append", default=[], help="section.key=value")
    a = ap.parse_args()

    cfg = inputs.config(a.set)
    cfg["feed"] = a.feed
    packed = newest(a.project, a.databank)
    frame = inputs.bars(a.feed, a.timeframe)
    every = pd.read_parquet(packed, columns=["strategy", "Sample type"])
    names = sorted(every[every["Sample type"] == a.sample]["strategy"].unique())
    names = names[:a.limit] if a.limit else names

    rows = {}
    for i, name in enumerate(names, 1):
        trades = inputs.sample(packed, name, a.sample)
        if len(trades) < cfg["verdict"]["min_trades"]:
            continue
        rows[name] = one(trades, frame, cfg)
        print(f"PROGRESS {100 * i // len(names)} {i}/{len(names)} {name}", flush=True)

    panel = pd.DataFrame(rows).T.rename_axis("strategy")
    out = report_dir(a.project, a.databank, date.today().isoformat()) / "nulls"
    out.mkdir(parents=True, exist_ok=True)
    panel.to_csv(out / "nulls.csv")
    (out / "rungs.json").write_text(json.dumps(model.RANDOMISES, indent=2), encoding="utf-8")
    write_manifest(out,
                   {"project": a.project, "databank": a.databank, "sample": a.sample,
                    "feed": a.feed, "timeframe": a.timeframe, "trades": str(packed),
                    "draws": cfg["nulls"]["draws"], "rungs": cfg["nulls"]["rungs"]},
                   " ".join(["python3 -m nulls.report", "--project", a.project,
                             "--databank", a.databank, "--feed", a.feed,
                             "--timeframe", a.timeframe, "--sample", a.sample]),
                   {"nulls.csv": len(panel)})
    print(f"\n{len(panel)} estrategias -> {out}")


if __name__ == "__main__":
    main()
