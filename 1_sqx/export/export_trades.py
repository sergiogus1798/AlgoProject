#!/usr/bin/env python3
"""Export one databank's trades, and the bars those trades were taken on, into the data root."""

import argparse
import shutil
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core import exportdrv, manifest, sqxfile
from core.paths import MASTER, databank_dir, export_dir


def stage(project: str, databank: str, dest: Path) -> dict[str, str]:
    """Copy a databank's strategies aside and read each one's timeframe.

    Args:
        project: Project name on the master.
        databank: Databank name on the master.
        dest: Directory to copy the .sqx files into.

    Returns:
        Strategy name to timeframe, e.g. {"Strategy 1.2.3": "M30"}. Copies rather than
        exporting in place so SQX never opens the live files.
    """
    dest.mkdir(parents=True, exist_ok=True)
    timeframes = {}
    for f in sorted(databank_dir(project, databank, MASTER).glob("*.sqx")):
        shutil.copy(f, dest / f.name)
        timeframes[f.stem] = sqxfile.symbol(f)[1].rsplit("_", 1)[-1]
    return timeframes


def main() -> None:
    """Stage a databank, export its trades and the bars for every timeframe it uses."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True)
    ap.add_argument("--symbol", required=True, help="SQX symbol without the timeframe suffix")
    ap.add_argument("--from", dest="date_from", default="2007.01.01")
    ap.add_argument("--to", dest="date_to", default="2026.01.01")
    a = ap.parse_args()

    out = export_dir(a.project, a.databank, date.today().isoformat())
    timeframes = stage(a.project, a.databank, out / "strategies")
    (out / "timeframes.csv").write_text(
        "strategy,timeframe\n" + "".join(f"{k},{v}\n" for k, v in timeframes.items()))
    print(f"staged {len(timeframes)} strategies from {a.project}/{a.databank}")

    exportdrv.trades(out / "strategies", out / "trades")
    for tf in sorted(set(timeframes.values())):
        exportdrv.bars(a.symbol, tf, out / "bars", a.date_from, a.date_to)

    manifest.write(out,
                   {"install": str(MASTER), "project": a.project, "databank": a.databank,
                    "symbol": a.symbol, "window": [a.date_from, a.date_to]},
                   f"export_trades.py --project {a.project} --databank {a.databank} "
                   f"--symbol {a.symbol}",
                   {"strategies": len(timeframes),
                    "trade_csvs": len(list((out / "trades").glob("*.csv"))),
                    "timeframes": sorted(set(timeframes.values()))})
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
