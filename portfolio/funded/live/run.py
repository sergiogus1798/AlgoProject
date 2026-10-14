"""THE COMMAND: stage A and the funded account's SPRT for one strategy, ending in a decision line."""

import argparse
from datetime import date

import pandas as pd

from core import assetdata, assetwrite
from core.assetyaml import safe_load
from core.paths import ROOT
from ledger import thresholds
from mt5 import compare
from portfolio.funded.live import sprt, stage_a
from portfolio.funded.live.real import from_fleet, r_values
from portfolio.funded.live.stage_a import StageA
from sqx.inspect import feeds

CONFIG = ROOT / "portfolio" / "funded" / "live" / "config.yaml"
VERIFY = safe_load(
    (ROOT / "mt5" / "verify" / "config.yaml").read_text(encoding="utf-8")
)
TIMES = ["Open time", "Close time"]


def trades(path: str) -> pd.DataFrame:
    """A trades CSV in SQX's export shape, times parsed."""
    return pd.read_csv(path, parse_dates=TIMES)


def say_stage_a(res: StageA) -> str:
    """Stage A's rows as Spanish lines and its one-line reading."""
    lines = [f"ETAPA A — {res['n']} operaciones reales"]
    for r in res["rows"]:
        v = "—" if r["value"] is None else f"{r['value']:.3f}"
        lines.append(
            f"  fila {r['row']:>2}  {v}  (límite {r['limit']})  {r['state']}  {r['label']}"
        )
    lines.append(f"  reloj: SQX movido {res['hours']:+d} h")
    if res["warning"]:
        lines.append(
            "  aviso: emparejadas por debajo del límite (la fila 1 no saca a la estrategia)"
        )
    return "\n".join(lines)


def prepare(
    sqx: pd.DataFrame, real: pd.DataFrame, asset: str
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Both sides as step 26 reads them: SQX moved to the server's zone, both P&L in points."""
    data = assetdata.load(asset)
    zones = (feeds.timezone(data["sqx_symbol"]), VERIFY["clock"]["server_zone"])
    return compare.in_points(
        compare.to_zone(sqx, *zones), data["instrument"]
    ), compare.in_points(real, data["instrument"])


def main() -> None:
    """Read the inputs, print both readings and the decision."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--asset", required=True, help="the asset's card (assets/symbols)")
    ap.add_argument("--strategy", required=True, help="its name in the live register")
    ap.add_argument(
        "--sqx",
        required=True,
        help="CSV of the SQX backtest trades, SQX's export shape",
    )
    ap.add_argument(
        "--deposit", type=float, required=True, help="account both sides start from"
    )
    ap.add_argument(
        "--firm", help="the register's key: read the trades from the fleet's history"
    )
    ap.add_argument(
        "--real", help="CSV of the real trades instead of the fleet (needs --timeframe)"
    )
    ap.add_argument("--timeframe", help="M1..D1, with --real")
    ap.add_argument(
        "--r", help="CSV with a column R instead of the real trades' own R (SPRT)"
    )
    ap.add_argument(
        "--anotar",
        action="store_true",
        help="write the failed rows on the asset's card",
    )
    a = ap.parse_args()
    cfg = thresholds.fill(safe_load(CONFIG.read_text(encoding="utf-8")))
    cfg["stage_a"]["max_offset_h"] = VERIFY["clock"]["max_offset_h"]
    if a.real:
        real, timeframe = trades(a.real), a.timeframe
    else:
        real, _, timeframe = from_fleet(a.strategy, a.firm)
    sqx, real = prepare(trades(a.sqx), real, a.asset)
    res = stage_a.run(sqx, real, timeframe, a.deposit, cfg["stage_a"])
    print(say_stage_a(res))
    if not res["ready"]:
        decisions = [
            f"etapa A sin veredicto: {res['n']} de {cfg['stage_a']['trades']} operaciones"
        ]
    elif res["out"]:
        decisions = ["SACAR a la estrategia: falla la fila " + ", ".join(res["failed"])]
        if a.anotar:
            for row in res["rows"]:
                if row["row"] in res["failed"]:
                    assetwrite.add_live_failure(
                        a.asset, date.today(), a.strategy, row["row"], row["value"]
                    )
            decisions[0] += " (anotado en la ficha del activo)"
    else:
        decisions = ["etapa A superada"]
    rs = pd.read_csv(a.r)["R"].tolist() if a.r else r_values(real, sqx)
    out = sprt.run(rs, cfg["sprt"])
    print(
        f"SPRT — {out['n']} operaciones, S_n − {out['drift']:.2f}·n = {out['stat']:+.2f} R, "
        f"fronteras {out['lower']:+.1f} / {out['upper']:+.1f} R"
    )
    decisions.append(
        {
            "raise": "SUBIR k al 1,5 %",
            "retire": "RETIRAR y sustituir por otra medoide de la celda",
            "continue": "SPRT: seguir operando",
        }[out["verdict"]]
    )
    print("DECISIÓN: " + "; ".join(decisions))


if __name__ == "__main__":
    main()
