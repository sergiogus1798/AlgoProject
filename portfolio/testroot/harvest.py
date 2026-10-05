"""The traded (stop) versions' cosecha for the test root, keyed by the grafted file's own identity."""

import argparse
import json
from datetime import date
from pathlib import Path

import pandas as pd

from core import assetdata, barstore, sqxfile
from core.manifest import write as write_manifest
from core.paths import harvest_dir
from engines.market import calibrate
from portfolio.common.construct.equity import days, paths, reconcile, sqxcurve, stopexit, universe
from portfolio.testroot import build
from sqx.inspect import feeds

STAND_IN = ("equity.parquet NO es la curva de SQX: es la reconstrucción M1 del propio motor "
            "(el paso 24 no guarda la curva diaria de la versión con stop). La conciliación "
            "daily-low contra ella es circular; la licencia MAE/MFE sí se mide contra SQX.")


def curve(trades: pd.DataFrame, bars: pd.DataFrame, symbol: str, timeframe: str, clock: str) -> pd.DataFrame:
    """One strategy's daily lowest equity per leg, rebuilt exactly as the universe rebuilds it.

    Args:
        trades: Its trades of both samples (schema T, plus `sample`).
        bars: The feed's M1 High, Low, Close.
        symbol: The asset, for its commission and its segment windows.
        timeframe: The strategies' grid, e.g. "M30".
        clock: The feed's zone.

    Returns:
        `day`, `equity`, `sample` — the shape of a cosecha's `equity.parquet`, each leg from
        its own 0. A stand-in for SQX's curve, which nothing on disk holds for a stop version.
    """
    trades = stopexit.retime(trades, bars, timeframe)
    same_day = trades[trades["Open time"].dt.normalize() == trades["Close time"].dt.normalize()]
    member = {"symbol": symbol, "trades": trades, "point_value": calibrate.point_value(same_day)}
    path = paths.minute_path(trades, bars, member["point_value"], universe._commission(member))
    low = reconcile.low_equity(days.server_days(path, clock, clock))
    data, parts, before = assetdata.load(symbol), [], 0.0
    for sample, segment in sqxcurve.SAMPLE_TO_SEGMENT.items():
        lo, hi = (pd.Timestamp(ms, unit="ms") for ms in assetdata.window(data, segment))
        leg = low[(low.index >= lo) & (low.index < hi)] - before
        parts.append(pd.DataFrame({"day": leg.index, "equity": leg.to_numpy(), "sample": sample}))
        before += float(trades.loc[trades["sample"] == sample, "Profit/Loss"].sum())
    return pd.concat(parts, ignore_index=True)


def harvest(project: str, databank: str) -> list[dict]:
    """Rewrite the real cosecha of the traded versions under the test root, by grafted identity.

    The real one (`pipeline.autopilot.traded.harvest`) keys each row by the MOTHER's identity
    and carries no curve, so the archive — which checks the `.sqx` against the identity it
    freezes — cannot take a stop version from it.

    Args:
        project: The project whose step 24 ran.
        databank: The cosecha's name, e.g. "Stop_p90".

    Returns:
        One dict per strategy: `strategy`, `identity` (the grafted file's) and `sqx`.
    """
    build.required()
    real = sorted((build.REAL / "harvest" / project / databank).glob("*/trades.parquet"))[-1].parent
    source = json.loads((real / "manifest.json").read_text(encoding="utf-8"))["source"]
    metrics = pd.read_parquet(real / "metrics.parquet").reset_index()
    files = {row.identity: Path(source["batch"]) / "sqx" / f"{source['variants'][row.strategy]}.sqx"
             for row in metrics.itertuples()}
    grafted = {mother: sqxfile.identity(sqx) for mother, sqx in files.items()}
    trades = pd.read_parquet(real / "trades.parquet")
    bars = barstore.source(source["feed"], ["High", "Low", "Close"])
    clock = feeds.timezone(source["feed"])
    curves = []
    for mother, rows in trades.groupby("identity", sort=False):
        symbol, timeframed = sqxfile.symbol(files[mother])
        curves.append(curve(rows, bars, symbol, timeframed.split("_LOM_")[-1], clock)
                      .assign(identity=grafted[mother]))
    out = harvest_dir(project, databank, date.today().isoformat())
    out.mkdir(parents=True)
    trades.assign(identity=trades["identity"].map(grafted)).to_parquet(out / "trades.parquet", index=False)
    metrics.assign(identity=metrics["identity"].map(grafted)).set_index("identity").to_parquet(
        out / "metrics.parquet")
    pd.concat(curves, ignore_index=True).to_parquet(out / "equity.parquet", index=False)
    write_manifest(out, {**source, "from": str(real), "equity": STAND_IN},
                   "portfolio.testroot.harvest", {"trades": len(trades), "strategies": len(files)})
    return [{"strategy": row.strategy, "identity": grafted[row.identity], "sqx": str(files[row.identity])}
            for row in metrics.itertuples()]


def main() -> None:
    """Write the test cosecha and print, per strategy, the command that archives it."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--databank", required=True)
    parser.add_argument("--family", required=True, help="la familia de plantilla del estudio del ledger")
    args = parser.parse_args()
    print(f"AVISO: {STAND_IN}")
    try:
        rows = harvest(args.project, args.databank)
    except FileExistsError as exists:
        raise SystemExit(f"la cosecha de prueba de hoy ya existe, bórrala para rehacerla: {exists.filename}")
    for row in rows:
        print(f"python3 -m core.archive archive --project {args.project} --databank {args.databank} "
              f"--identity {row['identity']} --step 24 --family {args.family} --sqx {row['sqx']}"
              f"   # {row['strategy']}")


if __name__ == "__main__":
    main()
