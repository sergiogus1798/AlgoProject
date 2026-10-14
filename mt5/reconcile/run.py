#!/usr/bin/env python3
"""weeklyReconciler: one ISO week of the live accounts against the SQX backtest of the same strategies."""
import argparse
import time
from pathlib import Path
from typing import Any

import pandas as pd

from core import assetdata, barstore
from core.paths import MT5_ACCOUNTS, MT5_DATA
from core.study import config as study_config
from mt5 import wine
from mt5.reconcile import judge, live, register, report, sqxside, week as weeks
from sqx.inspect import feeds

CONFIG = Path(__file__).resolve().parent / "config.yaml"
RUNS = MT5_DATA / "reconcile"


def required(cfg: dict, key: str, what: str) -> Any:
    """A key the owner has to fill, or the Spanish refusal that says which and how."""
    section, leaf = key.split(".")
    if cfg[section][leaf] in (None, [], ""):
        raise SystemExit(f"falta `{key}` en mt5/reconcile/config.yaml: {what}. Es decisión "
                         f"del dueño y no tiene valor por defecto; también vale --set {key}=…")
    return cfg[section][leaf]


def live_side(cfg: dict, week: str, rows: pd.DataFrame) -> pd.DataFrame:
    """The week's trades of every live account, each with its `firm` and `strategy` (None for
    a magic the register does not name). Opens the terminal on each account — read-only."""
    accounts = required(cfg, "live.accounts", "qué cuentas de mt5_accounts están en real")
    unknown = [a for a in accounts if a not in MT5_ACCOUNTS]
    if unknown:
        raise SystemExit(f"{', '.join(unknown)}: no está en mt5_accounts de config/machine.yaml")
    out = []
    for firm in accounts:
        frame = live.trades(live.fetch(MT5_ACCOUNTS[firm], week, cfg["live"]["spill_days"]))
        split, strays = live.by_strategy(frame, firm, rows)
        out += [t.assign(firm=firm, strategy=name) for name, t in split.items()]
        out.append(strays.assign(firm=firm, strategy=None))
    wine.close_terminal()
    return pd.concat(out, ignore_index=True)


def sqx_side(cfg: dict, week: str, rows: pd.DataFrame, work: Path) -> pd.DataFrame:
    """The week's SQX backtest of every live strategy: a worker job on the conductor."""
    return sqxside.backtest(rows, week, cfg["sqx"], work)


def main() -> None:
    """Read both sides (or their files), pair them per strategy, and write the week's result."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--week", required=True, help="ISO week on the server's clock, YYYY-Www")
    ap.add_argument("--live-trades", type=Path, help="the live side from a parquet "
                    "(`live/trades.parquet` of a week) instead of the terminal")
    ap.add_argument("--sqx-trades", type=Path, help="the SQX side from a parquet "
                    "(`sqx/trades.parquet` of a week) instead of a run on the conductor")
    ap.add_argument("--register", type=Path, help="the register CSV, if not config.yaml's")
    ap.add_argument("--out", type=Path, help="the week's folder, if not AlgoData/mt5/reconcile/<week>")
    ap.add_argument("--set", action="append", default=[], help="section.key=value")
    a = ap.parse_args()
    started = time.time()
    cfg = study_config.load(CONFIG, a.set)
    _, end = weeks.bounds(a.week)
    required(cfg, "pairing.entry_tolerance_bars",
             "a cuántas barras de distancia dos entradas siguen siendo la misma operación")
    rows = register.live_in(register.read(a.register or MT5_DATA / cfg["register"]), end)
    markets = [register.market(Path(p)) for p in rows["sqx"]]
    rows = rows.assign(asset=[m[0] for m in markets], timeframe=[m[1] for m in markets])
    work = a.out or RUNS / a.week
    for side in ("live", "sqx"):
        (work / side).mkdir(parents=True, exist_ok=True)

    if a.live_trades:
        lived = pd.read_parquet(a.live_trades)
    else:
        lived = live_side(cfg, a.week, rows)
        lived.to_parquet(work / "live" / "trades.parquet", index=False)
    if a.sqx_trades:
        tested = pd.read_parquet(a.sqx_trades)
    else:
        tested = sqx_side(cfg, a.week, rows, work / "sqx")
        tested.to_parquet(work / "sqx" / "trades.parquet", index=False)

    pieces, bars, library = {}, {}, barstore.library()
    for r in rows.itertuples():
        data = assetdata.load(r.asset)  # pyright: ignore[reportAttributeAccessIssue]  # pandas stubs: itertuples rows lose their field names
        feed = data["sqx_symbol"]
        if feed not in bars:
            bars[feed] = barstore.source(feed, ["High", "Low"]) if feed in library else None
        mine = lived[(lived["firm"] == r.firm) & (lived["strategy"] == r.strategy)]  # pyright: ignore[reportAttributeAccessIssue]  # pandas stubs: itertuples rows lose their field names
        pieces[(r.firm, r.strategy)] = judge.reconcile(  # pyright: ignore[reportAttributeAccessIssue]  # pandas stubs: itertuples rows lose their field names
            tested[tested["strategy"] == r.strategy], mine, a.week, r.timeframe,  # pyright: ignore[reportArgumentType, reportAttributeAccessIssue]  # pandas stubs: itertuples rows lose their field names; pandas/numpy stubs lose the type through indexing
            data["instrument"], (feeds.timezone(feed), cfg["clock"]["server_zone"]),
            bars[feed], cfg)
    strays = weeks.cut(lived[lived["strategy"].isna()], a.week)  # pyright: ignore[reportArgumentType]  # pandas/numpy stubs lose the type through indexing
    report.finish(work, a.week, cfg, started, pieces, strays)
    print(report.say(a.week, pieces, strays))
    print(f"  resultado: {work / 'result.json'}")


if __name__ == "__main__":
    main()
