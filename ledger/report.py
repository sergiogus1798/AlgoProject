#!/usr/bin/env python3
"""The study's whole search, read back: the funnel, what was spent, and what it costs the Sharpe."""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from core.surface import plateau
from ledger import gate, record, spend, study as studymod, thresholds, trials, tried
from studies.research.memory import ideas, sources, trials as research


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
    one = pd.DataFrame(frame[frame["identity"] == identity]).sort_values("day")
    return np.diff(one["equity"].to_numpy(float))


def main() -> None:
    """Read one study's ledger and print what its whole search adds up to."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--study", help="study id, as ledger/study.py builds it")
    ap.add_argument(
        "--check-thresholds",
        action="store_true",
        dest="check",
        help="say, per declared threshold, whether its module reads it from the ledger "
        "or from a copy, and whether the copy still matches",
    )
    ap.add_argument(
        "--equity", type=Path, help="a harvest equity.parquet, to deflate a Sharpe"
    )
    ap.add_argument("--identity", help="which strategy in it")
    a = ap.parse_args()

    if a.check:
        table = thresholds.divergences()
        print(table.to_string(index=False))
        off = table[~table["coincide"]]
        read = int((table["lee_de"] == "ledger").sum())
        print(
            f"\n{len(off)} divergencia(s)"
            if len(off)
            else f"\n{len(table)} umbrales declarados: {read} los lee su módulo del ledger y "
            f"{len(table) - read} son copias que coinciden"
        )
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
    print(
        f"de {int(frame['n_in'].iloc[0])} entraron a "
        f"{int(frame['n_out'].iloc[-1])} supervivientes"
    )

    print("\n-- qué historia se ha gastado")
    print(spend.spent(frame).to_string(index=False))
    for name, block in spend.virgin(frame, symbol).items():
        mark = (
            "RESERVADO para " + ", ".join(block["reserved_for"])
            if block["reserved_for"] and gate.enforced()
            else ""
        )
        print(
            f"  {name:<6} {block['from']} → {block['to']}  leído {block['reads']}x  {mark}"
        )

    print("\n-- la puerta ciega del paso 20")
    state = gate.done(frame)
    print(
        "  "
        + " · ".join(
            f"{s} {'hecho' if ran else 'pendiente'}" for s, ran in state.items()
        )
    )
    try:
        gate.allow_read(frame)
        print(
            "  los tres están: el paso 20 puede leerse"
            if all(state.values())
            else "  abierta: la puerta ciega sólo se cierra a un agente autónomo (ALGO_AUTONOMOUS=1)"
        )
    except PermissionError as refusal:
        print(f"  {refusal}")

    swept = tried.summary(a.study)
    if len(swept):
        print("\n-- lo probado en barridos (L2): probados K, elegido 1")
        print(swept.to_string(index=False))
        print(
            f"  {int(swept['cuenta'].sum())} pruebas cuentan para N (un barrido sin elegido no cuenta)"
        )

    timeframe = frame["timeframe"].iloc[0]
    family = a.study.removeprefix(studymod.study_id(symbol, timeframe, "") + "_")
    spent = research.spent(
        ideas.index(), sources.templates(), symbol, timeframe, family
    )
    counted = trials.accumulated(tried.with_sweeps(frame, a.study), spent["hypotheses"])
    if not counted["n"]:
        print("\n-- ninguna búsqueda registró la distribución de sus candidatos")
        return
    print(
        f"\n-- lo que se ha probado en total: N = {counted['n']} = {counted.get('searched')} "
        f"candidatos de {counted['searches']} búsqueda(s) + {spent['hypotheses']} hipótesis "
        f"medidas en {spent['ideas']} idea(s) ({' y '.join(spent['directions'])}), "
        f"sigma = {counted['sigma']:.4f} ({counted.get('unit')})"
    )
    print(
        f"  aparte, sin sumar: {research.profile_looks(symbol, timeframe, spent['directions'])}"
        " medidas del perfil de mercado y su barrido, corregidas entre sí"
    )

    every = trials.overall(
        [tried.with_sweeps(studymod.read(s), s) for s in studymod.studies()]
    )
    print(
        f"  N global entre {every['studies']} estudios: {every['n']} (el de este estudio: "
        f"{counted['n']}, con sus hipótesis medidas)"
    )

    last = frame[frame["n_scored"].notna()].iloc[-1]
    local = int(last["n_scored"])
    sigma = counted["sigma"]
    widths = (
        ("la última búsqueda", local),
        ("todas las búsquedas", counted.get("searched", 0)),
        ("búsquedas + ideas", counted["n"]),
    )
    for label, n in widths:
        print(
            f"  benchmark con N de {label:<19} ({n:>5}): "
            f"{plateau.expected_max_sharpe(sigma, n):.6f} (por día)"
        )
    if local == counted["n"]:
        print(
            "  los dos coinciden: este estudio sólo tiene una búsqueda con distribución "
            "registrada, así que no hay nada acumulado todavía que mover"
        )

    if a.equity and a.identity:
        returns = returns_of(a.equity, a.identity)
        print(
            f"\n-- el Sharpe desinflado de {a.identity[:12]}… sobre {len(returns)} días"
        )
        for label, n in widths:
            found = trials.deflated(returns, sigma, n)
            print(
                f"  N de {label:<19}: sharpe {found['sharpe']:.4f} contra benchmark "
                f"{found['benchmark']:.4f} -> DSR {found['dsr']:.6f}"
            )


if __name__ == "__main__":
    main()
