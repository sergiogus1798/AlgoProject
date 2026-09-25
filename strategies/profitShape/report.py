#!/usr/bin/env python3
"""The panel: how few trades, how few periods and which stretch the whole result rests on."""

import argparse
from pathlib import Path

import numpy as np

from strategies.profitShape import breaks, concentration, dependence, inputs, verdict


def read(packed: Path, strategy: str, cfg: dict) -> dict:
    """Every measurement for one strategy, with nothing judged and nothing printed.

    Args:
        packed: The `trades.parquet` an export wrote.
        strategy: Its name exactly as the export spells it.
        cfg: What `inputs.config` returned.

    Returns:
        The three families of numbers, keyed `concentration`, `dependence` and `breaks`.
    """
    run, dep, brk = cfg["run"], cfg["dependence"], cfg["breaks"]
    data = inputs.stream(packed, strategy, run["sample"])
    pnl, wins = data["pnl"], data["wins"]

    conc = concentration.time_concentration(data["trades"], pnl, run["best_months"])
    conc.update({"top1": concentration.top_share(pnl, 0.01),
                 "top5": concentration.top_share(pnl, 0.05),
                 "mean": float(pnl.mean()), "median": float(np.median(pnl)),
                 "trimmed": concentration.trimmed(pnl, run["trim"])})

    dependent = {"runs": dependence.runs(wins),
                 "trades": dependence.ljung_box(pnl, dep["lags"]),
                 "daily": dependence.ljung_box(data["daily"].to_numpy(), dep["lags"]),
                 "streak": dependence.streak(wins, dep["draws"], dep["seed"])}

    found = breaks.cusum(pnl) if pnl.size >= brk["min_trades"] else None
    structure = {"cusum": found, "n": pnl.size}
    if found:
        structure["sides"] = breaks.either_side(pnl, found["at"])
        structure["rolling"] = breaks.rolling(pnl, brk["window"])
        structure["date"] = data["trades"].loc[found["at"], "Open time"]
    return {"data": data, "concentration": conc, "dependence": dependent,
            "breaks": structure}


def main() -> None:
    """Read one strategy's trade list and print what its result rests on."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--export", required=True, type=Path, help="a trades.parquet")
    ap.add_argument("--strategy", required=True, help="its name as the export spells it")
    ap.add_argument("--set", dest="overrides", action="append", default=[])
    a = ap.parse_args()

    cfg = inputs.config(a.overrides)
    found = read(a.export, a.strategy, cfg)
    v = cfg["verdict"]
    conc, dep, brk = found["concentration"], found["dependence"], found["breaks"]

    print(f"{a.strategy} · muestra {cfg['run']['sample']} · "
          f"{found['data']['pnl'].size} operaciones")

    print("\n-- 1 · concentración del beneficio")
    print(f"mejor 1 % de las operaciones {conc['top1']:.1%} del total · "
          f"mejor 5 % {conc['top5']:.1%}")
    print(f"media por operación {conc['mean']:.2f} · mediana {conc['median']:.2f}")
    print(conc["trimmed"].round(3).to_string())
    print(f"mejores {cfg['run']['best_months']} meses {conc['best_months']:.1%} · "
          f"mejor año {conc['best_year']} {conc['best_year_share']:.1%} · sin él, "
          f"esperanza {conc['without_best_year']['expectancy']:.2f} "
          f"sobre {conc['n_without']} operaciones")
    label = verdict.concentration(conc, v)
    print(f"-> {label}: {verdict.MEANS[label]}")

    print("\n-- 2 · independencia de las operaciones")
    print(f"rachas {dep['runs']['runs']} contra {dep['runs']['expected']:.1f} esperadas, "
          f"z {dep['runs']['z']:+.2f} (p {dep['runs']['p']:.3f})")
    print(f"Ljung-Box sobre operaciones p {dep['trades']['p']:.3f} · sobre P&L diario "
          f"p {dep['daily']['p']:.3f} · último retardo con autocorrelación "
          f"{dep['daily']['last_significant']}")
    print(f"racha perdedora {dep['streak']['observed']} contra mediana "
          f"{dep['streak']['median']:.0f} y p95 {dep['streak']['p95']:.0f} barajando "
          f"(p {dep['streak']['p']:.3f})")
    label = verdict.dependence(dep["runs"], dep["daily"], dep["streak"], v)
    print(f"-> {label}: {verdict.MEANS[label]}")

    print("\n-- 7 · ¿cambió la media dentro de la muestra?")
    if not brk["cusum"]:
        print(f"{brk['n']} operaciones, por debajo del mínimo: no se lee")
        return
    print(f"CUSUM sup {brk['cusum']['sup']:.2f} contra el crítico {breaks.CRITICAL} · "
          f"candidato en la operación {brk['cusum']['at']} "
          f"({brk['cusum']['share']:.0%} de la muestra, {brk['date']:%Y-%m-%d})")
    print(brk["sides"].round(3).to_string())
    label = verdict.structure(brk["cusum"])
    print(f"-> {label}: {verdict.MEANS[label]}")
    print("\nDescriptivo, no una puerta: con siete diagnósticos, alguno falla por azar "
          "incluso en una estrategia buena. Un filtro nuevo sacado de aquí es una "
          "búsqueda nueva y se anota como tal.")


if __name__ == "__main__":
    main()
