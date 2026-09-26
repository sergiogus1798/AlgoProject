#!/usr/bin/env python3
"""The study's whole search, read back: the funnel, what was spent, and what it costs the Sharpe."""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from core.surface import plateau
from ledger import gate, record, spend, study as studymod, thresholds, trials

YEAR = 252      # trading days a year, for converting SQX's annualised Sharpes


def returns_of(equity: Path, identity: str) -> np.ndarray:
    """One strategy's per-day returns, from a gate harvest.

    Args:
        equity: The harvest's `equity.parquet` -- long, with `day`, `identity`, `equity`.
        identity: Which strategy, by the hash the harvest is keyed on.

    Returns:
        Day-to-day change in its cumulative equity. Per day, so anything compared against
        it must also be per day -- see the conversion in `main`.
    """
    frame = pd.read_parquet(equity)
    one = frame[frame["identity"] == identity].sort_values("day")
    return np.diff(one["equity"].to_numpy(float))


def main() -> None:
    """Read one study's ledger and print what its whole search adds up to."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--study", help="study id, as ledger/study.py builds it")
    ap.add_argument("--check-thresholds", action="store_true", dest="check",
                    help="say, per declared threshold, whether its module reads it from the ledger "
                         "or from a copy, and whether the copy still matches")
    ap.add_argument("--equity", type=Path, help="a harvest equity.parquet, to deflate a Sharpe")
    ap.add_argument("--identity", help="which strategy in it")
    a = ap.parse_args()

    if a.check:
        table = thresholds.divergences()
        print(table.to_string(index=False))
        off = table[~table["coincide"]]
        read = int((table["lee_de"] == "ledger").sum())
        print(f"\n{len(off)} divergencia(s)" if len(off) else
              f"\n{len(table)} umbrales declarados: {read} los lee su módulo del ledger y "
              f"{len(table) - read} son copias que coinciden")
        raise SystemExit(1 if len(off) else 0)
    if not a.study:
        raise SystemExit("ledger: hace falta --study, o --check-thresholds")

    frame = studymod.read(a.study)
    if not len(frame):
        print(f"{a.study}: sin búsquedas registradas todavía")
        return
    symbol = frame["symbol"].iloc[0]
    print(f"{a.study} · {len(frame)} búsquedas · {studymod.path(a.study)}")

    print("\n-- el embudo, paso a paso")
    print(record.funnel(frame).to_string(index=False))
    print(f"de {int(frame['n_in'].iloc[0])} entraron a "
          f"{int(frame['n_out'].iloc[-1])} supervivientes")

    print("\n-- qué historia se ha gastado")
    print(spend.spent(frame).to_string(index=False))
    for name, block in spend.virgin(frame, symbol).items():
        mark = "RESERVADO para " + ", ".join(block["reserved_for"]) if block["reserved_for"] else ""
        print(f"  {name:<6} {block['from']} → {block['to']}  leído {block['reads']}x  {mark}")

    print("\n-- la puerta ciega del paso 20")
    state = gate.done(frame)
    print("  " + " · ".join(f"{s} {'hecho' if ran else 'pendiente'}" for s, ran in state.items()))
    try:
        gate.allow_read(frame)
        print("  los tres están: el paso 20 puede leerse")
    except PermissionError as refusal:
        print(f"  {refusal}")

    counted = trials.accumulated(frame)
    if not counted["n"]:
        print("\n-- ninguna búsqueda registró la distribución de sus candidatos")
        return
    print(f"\n-- lo que se ha probado en total: N = {counted['n']} candidatos sobre "
          f"{counted['searches']} búsqueda(s), sigma = {counted['sigma']:.4f} "
          f"({counted['unit']})")

    last = frame[frame["n_scored"].notna()].iloc[-1]
    local = int(last["n_scored"])
    sigma = counted["sigma"] / np.sqrt(YEAR) if counted["unit"] == "annualised" \
        else counted["sigma"]
    for label, n in (("la última búsqueda", local), ("el estudio entero", counted["n"])):
        print(f"  benchmark con N de {label:<18} ({n:>5}): "
              f"{plateau.expected_max_sharpe(sigma, n):.4f} (por día)")
    if local == counted["n"]:
        print("  los dos coinciden: este estudio sólo tiene una búsqueda con distribución "
              "registrada, así que no hay nada acumulado todavía que mover")

    if a.equity and a.identity:
        returns = returns_of(a.equity, a.identity)
        print(f"\n-- el Sharpe desinflado de {a.identity[:12]}… sobre {len(returns)} días")
        for label, n in (("la última búsqueda", local), ("el estudio entero", counted["n"])):
            found = trials.deflated(returns, sigma, n)
            print(f"  N de {label:<18}: sharpe {found['sharpe']:.4f} contra benchmark "
                  f"{found['benchmark']:.4f} -> DSR {found['dsr']:.4f}")


if __name__ == "__main__":
    main()
