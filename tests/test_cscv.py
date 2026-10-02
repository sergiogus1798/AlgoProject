#!/usr/bin/env python3
"""Property test for the CSCV on panels whose answer is known by construction — above all
the block-shuffled one, where a surface with real dispersion must still read as luck."""

import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.surface import trials as counting
from engines.variants import panel as variants
from studies.optimisation.cscv.measure import cscv, rules
from studies.optimisation.cscv.verdict import summary, trials

N, T, BLOCKS, SEED = 60, 400, 10, 20260922
# One panel proves nothing about the null: measured 2026-09-22, the PBO of pure noise has
# a standard deviation of 0.21 across seeds at this width, because the 252 partitions
# overlap heavily and are nothing like 252 independent observations. The properties below
# are therefore checked on the average over many panels, which is what has an expectation.
SEEDS = 12


def dates(periods: int) -> pd.DatetimeIndex:
    """A weekly index of the right length.

    Args:
        periods: How many rows.

    Returns:
        Weekly timestamps, which is the period the study aggregates to.
    """
    return pd.date_range("2008-01-06", periods=periods, freq="W")


def panels(seed: int = SEED) -> dict[str, pd.DataFrame]:
    """Three panels whose probability of backtest overfitting is decided in advance.

    Args:
        seed: Fixes every draw.

    Returns:
        Name to a periods-by-variants frame.

        `noise` has no edge anywhere, so choosing the in-sample best must be worth
        nothing. `edge` has one column that genuinely earns, so choosing must be worth
        everything. `shuffled` is the one that matters: every block ranks the variants
        independently, so the surface has real dispersion in every window and none of it
        carries -- the failure a single in-sample/out-of-sample split cannot see.
    """
    rng = np.random.default_rng(seed)
    noise = rng.normal(0, 1, (T, N))

    edge = rng.normal(0, 1, (T, N))
    edge[:, 7] = rng.normal(0.9, 1, T)

    shuffled = np.empty((T, N))
    for rows in np.array_split(np.arange(T), BLOCKS):
        shuffled[rows] = rng.normal(rng.normal(0, 0.6, N), 1, (len(rows), N))

    return {name: pd.DataFrame(v, index=dates(T),
                               columns=[f"P{i:05d}" for i in range(N)])
            for name, v in {"noise": noise, "edge": edge, "shuffled": shuffled}.items()}


def spiky() -> tuple[np.ndarray, pd.DataFrame]:
    """A surface with a broad good region and one isolated better point.

    Returns:
        (score, grid) over an 11 by 11 parameter grid. The lone spike scores highest, and
        a five-by-five plateau scores well everywhere. Which of the two a rule takes is
        the entire difference between the rules.
    """
    a, b = np.meshgrid(np.arange(11), np.arange(11), indexing="ij")
    a, b = a.ravel(), b.ravel()
    score = np.zeros(a.size)
    score[(abs(a - 3) <= 2) & (abs(b - 3) <= 2)] = 1.0
    score[(a == 9) & (b == 9)] = 2.0
    return score, pd.DataFrame({"param_x": a, "param_y": b})


def by_rows(wide: pd.DataFrame, blocks: int, rule: Callable, grid: pd.DataFrame,
            rng: np.random.Generator, score: str) -> pd.DataFrame:
    """The CSCV as it was computed before 2026-10-01: rows concatenated, one partition at a time.

    Args:
        wide, blocks, rule, grid, rng: As `cscv.run`.
        score: A key of `cscv.SCORES`.

    Returns:
        The same frame `cscv.run` returns, off the plain per-row score -- the reference the
        block-sum version must reproduce.
    """
    measure = cscv.SCORES[score]
    pieces = np.array_split(np.arange(len(wide)), blocks)
    values, n = wide.to_numpy(), wide.shape[1]
    rows = []
    for inside in cscv.partitions(blocks):
        outside = [b for b in range(blocks) if b not in inside]
        train = measure(values[np.concatenate([pieces[b] for b in inside])])
        held = values[np.concatenate([pieces[b] for b in outside])]
        test = measure(held)
        pick = rule(train, grid, rng)
        omega = (int((test < test[pick]).sum()) + 1) / (n + 1)
        slope, intercept = np.polyfit(train, test, 1)
        rows.append({"pick": pick, "omega": omega, "lam": float(np.log(omega / (1 - omega))),
                     "is_score": float(train[pick]), "oos_score": float(test[pick]),
                     "oos_median": float(np.median(test)), "slope": float(slope),
                     "r2": float(np.corrcoef(train, test)[0, 1] ** 2),
                     "oos_pnl": float(held[:, pick].sum())})
    return pd.DataFrame(rows)


def daily_panel() -> tuple[pd.DataFrame, pd.DataFrame]:
    """A joined equity file with two overlapping legs, and the panel it must read as.

    Returns:
        (what `engines.variants.panel.panel(work, "D")` read off it, the expected frame):
        the overlapping date summed, the weekend never filled, the last day dropped.
    """
    leg1 = pd.DataFrame({"P0": [1.0, 0.0, 2.0], "P1": [0.0, 0.0, -1.0]},
                        index=pd.to_datetime(["2020-01-02", "2020-01-03", "2020-01-06"]))
    leg2 = pd.DataFrame({"P0": [0.5, 3.0, 4.0], "P1": [0.0, 1.0, 9.0]},
                        index=pd.to_datetime(["2020-01-06", "2020-01-07", "2020-01-08"]))
    with tempfile.TemporaryDirectory() as tmp:
        pd.concat([leg1, leg2]).sort_index().to_parquet(Path(tmp) / "equity.parquet")
        got = variants.panel(Path(tmp), "D")
    want = pd.DataFrame({"P0": [1.0, 0.0, 2.5, 3.0], "P1": [0.0, 0.0, -1.0, 1.0]},
                        index=pd.to_datetime(["2020-01-02", "2020-01-03", "2020-01-06",
                                              "2020-01-07"]))
    return got, want


def check(failures: list, ok: bool, said: str) -> None:
    """Record one property and say how it went.

    Args:
        failures: Collected failures, appended to when `ok` is false.
        ok: Whether the property held.
        said: What was being checked.
    """
    print(f"  {'ok  ' if ok else 'FALLA'} {said}")
    if not ok:
        failures.append(said)


def main() -> None:
    """Fail loudly on the first property that does not hold."""
    failures = []
    rng = np.random.default_rng(SEED)
    grids = panels()

    print("## las particiones")
    parts = cscv.partitions(BLOCKS)
    check(failures, len(parts) == 252, f"C(10,5) = 252 particiones, hay {len(parts)}")
    check(failures, all(len(p) == BLOCKS // 2 for p in parts),
          "cada mitad de entrenamiento tiene 5 bloques")
    check(failures, len(set(parts)) == len(parts), "ninguna particion se repite")

    print(f"\n## el PBO sobre paneles de respuesta conocida, {SEEDS} paneles de cada uno")
    grid = pd.DataFrame({"param_i": range(N)})
    runs = {name: [] for name in grids}
    for seed in range(SEEDS):
        for name, panel in panels(seed).items():
            runs[name].append(summary.everything(
                cscv.run(panel, BLOCKS, rules.argmax, grid, np.random.default_rng(seed))))
    found = {name: pd.DataFrame(rows) for name, rows in runs.items()}
    for name, rows in found.items():
        print(f"     {name:9s} PBO medio {rows['pbo'].mean():.2f} "
              f"(desv {rows['pbo'].std():.2f})  pendiente media {rows['slope'].mean():+.2f}")
    check(failures, abs(found["noise"]["pbo"].mean() - 0.5) < 0.1,
          "ruido puro: el PBO medio ronda 0,5, elegir no compra nada")
    check(failures, found["edge"]["pbo"].mean() < 0.05,
          "una columna con ventaja real: el PBO se va a cero")
    check(failures, (found["edge"]["dominance"] == "primer_orden").all(),
          "y elegir domina a quedarse con la mediana, en todos los paneles")
    check(failures, abs(found["shuffled"]["pbo"].mean() - 0.5) < 0.1,
          "barajado por bloques: dispersion real en cada ventana y PBO en 0,5 igual")
    check(failures, abs(found["noise"]["slope"].mean()) < 0.1,
          "sin ventaja, el arrastre entre todas las variantes es cero")
    check(failures, found["edge"]["slope"].mean() > 0.3,
          "con una ventaja real, el arrastre es claramente positivo")
    check(failures, abs(found["shuffled"]["slope"].mean()) < 0.1,
          "barajado por bloques: dispersion real y arrastre cero, que es el caso ciego")

    print("\n## la matriz diaria y las sumas por bloque")
    got, want = daily_panel()
    check(failures, got.equals(want), "el panel D suma la fecha que dos tramos comparten, no "
          "rellena el fin de semana y descarta el último día")
    wide = panels(SEED)["edge"].iloc[:, :25]
    wide.iloc[:40, 3] = 0.0
    wide.iloc[:, 5] = wide.iloc[:, 5].abs()  # never loses: Sortino places it on top
    small = pd.DataFrame({"param_i": range(wide.shape[1])})
    for score in cscv.SCORES:
        for name, rule in rules.RULES.items():
            fast = cscv.run(wide, BLOCKS, rule, small, np.random.default_rng(1), score)
            slow = by_rows(wide, BLOCKS, rule, small, np.random.default_rng(1), score)
            same = (fast["pick"].equals(slow["pick"])
                    and np.allclose(fast.drop(columns="pick"), slow.drop(columns="pick"),
                                rtol=1e-9, atol=1e-9))
            check(failures, same, f"{score} {name}: las sumas por bloque dan lo mismo que "
                  "concatenar filas, partición a partición")

    print("\n## el signo de lambda")
    records = cscv.run(grids["edge"], BLOCKS, rules.argmax,
                       pd.DataFrame({"param_i": range(N)}), rng)
    agree = ((records["omega"] > 0.5) == (records["lam"] > 0)).all()
    check(failures, bool(agree), "lambda es positiva exactamente cuando omega pasa de 0,5")

    print("\n## las reglas de seleccion")
    score, grid = spiky()
    picked = rules.argmax(score, grid, rng)
    centred = rules.plateau_centre(score, grid, rng)
    check(failures, grid.loc[picked, "param_x"] == 9,
          "argmax se queda con el pico aislado")
    check(failures, abs(grid.loc[centred, "param_x"] - 3) <= 1
          and abs(grid.loc[centred, "param_y"] - 3) <= 1,
          "el centro de meseta se queda dentro de la meseta")

    print("\n## cuantas pruebas independientes hay")
    base = rng.normal(0, 1, (T, 3))
    family = pd.DataFrame(
        {f"g{g}_{i}": base[:, g] + rng.normal(0, 0.15, T) for g in range(3) for i in range(20)},
        index=dates(T))
    counted = counting.independent(family, 20)
    print(f"     tres familias correlacionadas -> {counted}")
    check(failures, counted["n_clusters"] == 3,
          "tres grupos de variantes correlacionadas cuentan como tres pruebas")

    print()
    if failures:
        sys.exit(f"{len(failures)} propiedades rotas: {failures}")
    print("todas las propiedades se cumplen")


if __name__ == "__main__":
    main()
