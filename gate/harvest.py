#!/usr/bin/env python3
"""Two databanks in, one joined cosecha out: the build window and the retest window."""

import argparse
import random
from datetime import date

import pandas as pd

from core import manifest, sqxfile
from core.paths import MASTER, databank_dir, harvest_dir, worker_dir
from gate import collect, pairing

SAMPLE_SEED = 20260923      # a subset harvest is a sample, and a sample has to reproduce


def main() -> None:
    """Match the two databanks on identity, take both, and write the joined tables."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True, help="the build databank, in sample")
    ap.add_argument("--oos-databank", required=True, help="the retest databank, out of sample")
    ap.add_argument("--role", help="worker role holding the project; the master if absent")
    ap.add_argument("--view", default="Export Data View", help="databank view on the master")
    ap.add_argument("--limit", type=int, default=0, help="a random sample of N pairs, for a trial")
    a = ap.parse_args()

    install = worker_dir(a.role) if a.role else MASTER
    build = collect.index(databank_dir(a.project, a.databank, install))
    after = collect.index(databank_dir(a.project, a.oos_databank, install))
    # SQX drops a strategy from a retest databank when one of its own red flags fires there.
    # Those are decided, not missing: the gate carries them to the verdict as rejects.
    pairs, alias, missing = pairing.pair(build, after)
    matched = sorted(pairs)
    print(f"{a.databank}: {len(build)} · {a.oos_databank}: {len(after)} · "
          f"emparejadas {len(matched)} ({len(alias)} por nombre) · sin OOS {len(missing)} · "
          f"solo en OOS {len(set(after) - set(build) - set(alias))}")
    if a.limit and a.limit < len(matched):
        matched = sorted(random.Random(SAMPLE_SEED).sample(matched, a.limit))

    out = harvest_dir(a.project, a.databank, date.today().isoformat())
    out.mkdir(parents=True, exist_ok=True)
    sides = collect.tables({side: [pairs[i][n] for i in matched]
                            for n, side in enumerate(("IS", "OOS"))}, out / "_work", a.view)
    # A pair the names rescued carries two different identities, so the retest side is
    # re-keyed to the build's before anything is joined on it.
    if alias:
        sides["OOS"]["metrics"] = sides["OOS"]["metrics"].rename(index=alias)
        for frame in ("trades", "equity"):
            sides["OOS"][frame]["identity"] = sides["OOS"][frame]["identity"].replace(alias)

    metrics = sides["IS"]["metrics"].add_suffix(" [IS]").join(
        sides["OOS"]["metrics"].add_suffix(" [OOS]"))
    metrics = metrics.rename(columns={"Strategy Name [IS]": "strategy_build",
                                      "Strategy Name [OOS]": "strategy"})
    # The logic each strategy IS, with its parameter values ignored, so the redundancy
    # screen can ask whether N survivors are N ideas. Read from the files, not derived
    # from the numbers: 0.2 ms each.
    # Aligned on the index, never positionally: `metrics` comes back in SQX's own export
    # order and `matched` is sorted, so a list here would attach each shape to the wrong
    # strategy without anything failing.
    metrics["structure"] = pd.Series({i: sqxfile.structure(pairs[i][1]) for i in matched})
    metrics.to_parquet(out / "metrics.parquet", compression="zstd")
    trades = pd.concat([f["trades"].assign(sample=side) for side, f in sides.items()])
    trades.to_parquet(out / "trades.parquet", compression="zstd", index=False)
    equity = pd.concat([f["equity"].assign(sample=side) for side, f in sides.items()])
    equity.to_parquet(out / "equity.parquet", compression="zstd", index=False)
    pd.DataFrame({"identity": missing,
                  "strategy_build": [build[i].stem for i in missing]}).to_csv(
        out / "missing_oos.csv", index=False)

    blocks = {side: f["sample"] for side, f in sides.items()}
    print(f"bloque con datos: build={blocks['IS']} · retesteo={blocks['OOS']}")
    manifest.write(out,
                   {"install": str(install), "project": a.project, "databank": a.databank,
                    "oos_databank": a.oos_databank, "view": a.view, "role": a.role or "master",
                    "join": "identity (sha256 of strategy_Portfolio.xml), file name as fallback",
                    "sample_blocks": blocks},
                   f"python3 -m gate.harvest --project {a.project} --databank "
                   f"'{a.databank}' --oos-databank '{a.oos_databank}'",
                   {"build": len(build), "oos": len(after), "matched": len(matched),
                    "missing_oos": len(missing), "trades": len(trades),
                    "equity_days": len(equity), "metrics_columns": len(metrics.columns)})
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
