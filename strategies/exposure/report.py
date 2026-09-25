"""Every strategy of one export against buy and hold, priced in the market time it spent."""

import argparse
import json
from datetime import date

import numpy as np
import pandas as pd

from core.manifest import write as write_manifest
from core.paths import report_dir
from strategies.exposure import benchmark, compare, inputs, occupancy, verdict

PANEL = """
{name} · {project}/{databank} · muestra {sample} · {start} a {end}

  EN EL MERCADO      {share:>10.2%} de las barras, {hours:.1f} h de las 168 de la semana
                     {notional:>10.1f} % de la cuenta comprometido de media mientras opera
  LA ESTRATEGIA      {net:>10,.0f} $   {ret:.2f} %   CAGR {cagr:.2f} %   DD {dd:.2f} %
  BUY AND HOLD       {bnet:>10,.0f} $   {bret:.2f} %   CAGR {bcagr:.2f} %   DD {bdd:.2f} %
       ({conv}, {lots:.3f} lotes)

  POR HORA EXPUESTA  {per:>10.2f} %   ->  {eff:.2f}x lo que rinde el buy and hold
  EN TOTAL           {ratio:>10.2f}x lo que rinde el buy and hold
  RIESGO             {ddr:>10.2f}x su drawdown, y {off:.0f} h a la semana fuera del mercado

  ESTUVO PRESENTE    en el {cap:.1%} del movimiento del mercado, alineado con el {ali:.1%}

  VEREDICTO          {verdict}
{reasons}"""


def row(trades: pd.DataFrame, bars: pd.DataFrame, point_value: float, cfg: dict) -> dict:
    """Everything this study measures about one strategy.

    Args:
        trades: That strategy's trades on the chosen sample.
        bars: The window's bars, indexed by open time.
        point_value: Account currency per 1.0 of price and 1.0 of lot.
        cfg: What `inputs.config` returned.

    Returns:
        One flat row: occupancy, the strategy's own statistics, the benchmark's under each
        convention, the trade-off, where the market moved while it was holding, and the
        verdict with its reasons.
    """
    equity = compare.equity_start(trades)
    moves = benchmark.moves(bars)
    mine = benchmark.daily(trades, moves.index)
    exposure = occupancy.measure(trades, bars, point_value, equity)
    held = occupancy.held(trades, bars.index)["signed"]
    closes = bars["Close"].to_numpy()
    presence = occupancy.presence(held, np.diff(closes, append=closes[-1]))

    strategy = compare.stats(mine, equity)
    lots = {name: benchmark.CONVENTIONS[name](trades, moves, mine, point_value)
            for name in cfg["benchmark"]["report"]}
    bench = {name: compare.stats(benchmark.profit(size, moves, point_value), equity)
             for name, size in lots.items()}
    head = cfg["benchmark"]["headline"]
    trade_off = compare.dichotomy(strategy, bench[head], exposure)
    days = (moves.index[-1] - moves.index[0]).days
    said = verdict.judge(strategy, bench[head], exposure, trade_off, presence,
                         len(trades), days, cfg)

    out = {"n": len(trades), "days": days, "equity_start": equity}
    out |= {f"exp_{key}": value for key, value in exposure.items()}
    out |= {f"strat_{key}": value for key, value in strategy.items()}
    out |= {f"bench_{name}_{key}": value
            for name, found in bench.items() for key, value in found.items()}
    out |= {f"lots_{name}": size for name, size in lots.items()}
    out |= trade_off | presence
    out |= {"verdict": said["verdict"], "reasons": " | ".join(said["reasons"])}
    return out


def panel(found: dict, name: str, project: str, databank: str, cfg: dict,
          span: tuple) -> str:
    """One strategy's answer, written for someone who is not going to open the CSV.

    Args:
        found: What `row` returned.
        name: The strategy's name.
        project: Project name.
        databank: Databank name.
        cfg: What `inputs.config` returned.
        span: The window, as `inputs.window` returned it.

    Returns:
        The text panel, ready to print.
    """
    head = cfg["benchmark"]["headline"]
    lines = "\n".join(f"                     - {reason}" for reason in
                      found["reasons"].split(" | ") if reason)
    return PANEL.format(
        name=name, project=project, databank=databank, sample=cfg["study"]["sample"],
        start=span[0].date(), end=span[1].date(),
        share=found["exp_share"], hours=found["exp_hours_per_week"],
        notional=found["exp_notional_when_in_pct"],
        net=found["strat_net"], ret=found["strat_return_pct"],
        cagr=found["strat_cagr_pct"], dd=found["strat_maxdd_pct"],
        bnet=found[f"bench_{head}_net"], bret=found[f"bench_{head}_return_pct"],
        bcagr=found[f"bench_{head}_cagr_pct"], bdd=found[f"bench_{head}_maxdd_pct"],
        conv=head, lots=found[f"lots_{head}"],
        per=found["return_per_exposure_pct"], eff=found["efficiency"],
        ratio=found["return_ratio"], ddr=found["dd_ratio"], off=found["hours_off"],
        cap=found["captured"], ali=found["aligned"],
        verdict=found["verdict"], reasons=lines)


def main() -> None:
    """Measure one strategy, or every strategy of one export, against buy and hold."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True)
    ap.add_argument("--feed", required=True, help="SQX feed name, e.g. XAUUSD_DukasM1_Infinox")
    ap.add_argument("--symbol", required=True, help="asset file name, e.g. XAUUSD")
    ap.add_argument("--strategy", default="", help="one strategy; every one when omitted")
    ap.add_argument("--set", action="append", default=[], metavar="section.key=value")
    args = ap.parse_args()

    cfg = inputs.config(args.set)
    span = inputs.window(args.symbol, cfg["study"]["segment"])
    bars = inputs.bars(args.feed, cfg["study"]["timeframe"], span)
    point_value = inputs.point_value(args.symbol)
    packed = inputs.newest(args.project, args.databank)
    frame = inputs.sample(packed, cfg["study"]["sample"])

    wanted = [args.strategy] if args.strategy else list(frame["strategy"].unique())
    rows = {name: row(frame[frame["strategy"] == name], bars, point_value, cfg)
            for name in wanted}
    if args.strategy:
        print(panel(rows[args.strategy], args.strategy, args.project, args.databank,
                    cfg, span))

    out = report_dir(args.project, args.databank, date.today().isoformat())
    out.mkdir(parents=True, exist_ok=True)
    panel_frame = pd.DataFrame(rows).T.rename_axis("strategy").reset_index()
    # One strategy writes its own pair of files: a single-strategy look must never
    # overwrite the table of the whole population that ran the same day.
    stem = "exposure" if not args.strategy else \
        "exposure_" + args.strategy.replace(" ", "_").replace(".", "-")
    panel_frame.to_csv(out / f"{stem}.csv", index=False)
    (out / f"{stem}.json").write_text(json.dumps(
        {"config": cfg, "feed": args.feed, "symbol": args.symbol,
         "window": [str(span[0]), str(span[1])],
         "worth_it": int((panel_frame["verdict"] == "worth_it").sum()),
         "strategies": len(panel_frame)}, indent=2), encoding="utf-8")
    write_manifest(out, {"project": args.project, "databank": args.databank,
                         "trades": str(packed), "feed": args.feed},
                   "python3 -m strategies.exposure.report",
                   {f"{stem}.csv": len(panel_frame)})
    plural = "estrategia" if len(panel_frame) == 1 else "estrategias"
    print(f"\n{len(panel_frame)} {plural} -> {out}/{stem}.csv")


if __name__ == "__main__":
    main()
