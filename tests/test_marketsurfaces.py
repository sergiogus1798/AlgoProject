#!/usr/bin/env python3
"""Known-answer test for the market surfaces: rho and J on panels whose answer is fixed by construction."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.optimisation.marketSurfaces.contract import density, grids
from studies.optimisation.marketSurfaces.measure import pairs
from studies.optimisation.marketSurfaces.verdict import call

N, SEED, SEEDS = 2000, 20260926, 200
SHARE, QUANTILE, FLOOR = 0.10, 0.975, 0.30


def panel(seed: int) -> pd.DataFrame:
    """Five markets over the same variants, each related to `main` in a way decided in advance.

    Args:
        seed: Fixes every draw.

    Returns:
        `variant_id` down, market across. `same` is `main` itself, `shared` is a monotone
        transform of it plus a little noise (the same region, another scale), `unrelated`
        is drawn independently, `inverted` is `main` reversed, and `bottom` agrees with
        `main` below its median and is reversed above it — a rho carried by the bad half,
        with its best variants sitting just above `main`'s median and not at its top.
    """
    rng = np.random.default_rng(seed)
    main = rng.normal(0, 1, N)
    bottom = np.where(main < np.median(main), main, 10 - main)
    return pd.DataFrame({"main": main, "same": main,
                         "shared": np.exp(main) * 300 + rng.normal(0, 30, N),
                         "unrelated": rng.normal(0, 1, N), "inverted": -main,
                         "bottom": bottom},
                        index=pd.Index([f"P{i:05d}" for i in range(N)], name="variant_id"))


def check(failures: list, ok: bool, said: str) -> None:
    """Record one property and say how it went."""
    print(f"  {'ok  ' if ok else 'FALLA'} {said}")
    if not ok:
        failures.append(said)


def main() -> None:
    """Fail loudly on any property that does not hold."""
    failures = []
    print("## el azar exacto")
    j0, _ = pairs.chance(1000, 100, QUANTILE)
    check(failures, abs(j0 - 10 / 190) < 1e-12, f"J de dos deciles independientes = 10/190 ({j0:.5f})")

    print("\n## un panel")
    flat = panel(SEED)
    found = pairs.matrix(flat, flat * 0 + 20.0, SHARE, QUANTILE).set_index(["a", "b"])
    for market in ("main", "shared", "unrelated"):
        row = found.loc[(market, market)]
        check(failures, row["rho"] == 1.0 and row["j"] == 1.0, f"{market} consigo mismo: rho 1, J 1")
    same = found.loc[("main", "same")]
    check(failures, same["rho"] == 1.0 and same["j"] == 1.0 and same["n_eff"] == N,
          "una copia exacta del principal: rho 1, J 1, y cada variante cuenta una vez")
    shared = found.loc[("main", "shared")]
    check(failures, shared["rho"] > 0.9 and shared["j"] > 0.7,
          f"la misma región a otra escala: rho {shared['rho']:.3f}, J {shared['j']:.3f}")
    inverted = found.loc[("main", "inverted")]
    check(failures, inverted["rho"] == -1.0 and inverted["j"] == 0.0,
          "el principal invertido: rho -1, J 0")
    bottom = found.loc[("main", "bottom")]
    check(failures, bottom["rho"] > FLOOR and call.pair_state(bottom, FLOOR) != "pass",
          f"rho {bottom['rho']:.2f} llevado por la esquina mala no pasa: los deciles "
          f"superiores no se comparten (J {bottom['j']:.3f})")
    check(failures, np.allclose(found["rho_neutral"], found["rho"]),
          "con la exposición constante, rho_neutral es rho")
    check(failures, call.pair_state(shared, FLOOR) == "pass"
          and call.pair_state(inverted, FLOOR) == "fail", "estados: shared pasa, inverted falla")

    print("\n## duplicados")
    doubled = pd.concat([panel(SEED)[["main", "unrelated"]]] * 3)
    twice = pairs.pair(doubled["main"].reset_index(drop=True),
                       doubled["unrelated"].reset_index(drop=True), SHARE, QUANTILE,
                       doubled["main"].reset_index(drop=True) * 0,
                       doubled["main"].reset_index(drop=True) * 0)
    once = found.loc[("main", "unrelated")]
    check(failures, twice["n_eff"] == N and abs(twice["rho"] - once["rho"]) < 1e-12,
          "el mismo backtest tres veces cuenta una: n_eff y rho iguales al panel sin copiar")

    print(f"\n## el nulo, sobre {SEEDS} paneles independientes")
    reads = pd.DataFrame([pairs.pair(p["main"], p["unrelated"], SHARE, QUANTILE,
                                     p["main"] * 0, p["main"] * 0)
                          for p in map(panel, range(SEEDS))])
    above = float((reads["j"] > reads["j_hi"]).mean())
    check(failures, abs(reads["j"].mean() - reads["j0"].mean()) < 0.005,
          f"J medio de órdenes independientes {reads['j'].mean():.4f} = azar {reads['j0'].mean():.4f}")
    check(failures, above < 0.06, f"J por encima de la banda en {above:.1%} de los paneles (≤ 2,5 %: la banda es discreta y conservadora)")
    check(failures, abs(reads["rho"].mean()) < 0.01 and (reads["rho_lo"] > 0).mean() < 0.06,
          f"rho medio {reads['rho'].mean():+.4f}; intervalo entero sobre 0 en "
          f"{(reads['rho_lo'] > 0).mean():.1%}")

    print("\n## la exposición por la deriva")
    rng = np.random.default_rng(SEED)
    time_in = pd.Series(rng.uniform(5, 40, N))
    up = time_in * 100 + rng.normal(0, 300, N)
    down = -time_in * 100 + rng.normal(0, 300, N)
    drift = pairs.pair(up, down, SHARE, QUANTILE, time_in, time_in)
    check(failures, drift["rho"] < -0.7 and abs(drift["rho_neutral"]) < 0.08,
          f"dos mercados que sólo premian estar dentro con derivas opuestas: rho "
          f"{drift['rho']:+.2f} en bruto, {drift['rho_neutral']:+.2f} sin la exposición")
    same_drift = time_in * 100 + rng.normal(0, 300, N)
    same_drift2 = time_in * 100 + rng.normal(0, 300, N)
    shared_exposure = pairs.pair(same_drift, same_drift2, SHARE, QUANTILE, time_in, time_in)
    check(failures, shared_exposure["rho_lo"] > FLOOR
          and call.pair_state(shared_exposure, FLOOR) != "pass",
          f"dos mercados que sólo comparten la MISMA deriva: rho en bruto "
          f"{shared_exposure['rho']:+.2f} (intervalo sobre el suelo) pero rho_neutral "
          f"{shared_exposure['rho_neutral']:+.2f} decide, y no pasa por exposición sola")
    silent = pairs.pair(time_in, time_in * float("nan"), SHARE, QUANTILE, time_in, time_in)
    check(failures, silent["n_eff"] == 0 and call.pair_state(silent, FLOOR) != "pass",
          "un mercado sin ninguna variante usable no comparte nada: sin lectura, y no pasa")

    print("\n## la llamada de la madre")
    rows = pd.DataFrame({"segment": ["build"] * 4 + ["oos1"] * 4,
                         "state": ["pass"] * 2 + ["fail"] * 2 + ["pass"] * 3 + ["fail"]})
    check(failures, call.mother(rows, 4, 0.5)["state"] == "pass", "2/4 y 3/4 con 0.5 -> pass")
    check(failures, call.mother(rows, 9, 0.5)["state"] == "fail",
          "los mismos contra 9 declarados -> fail: el que falta cuenta como no superado")

    print("\n## las densidades y la escala de las rejillas")
    edges = np.linspace(-5, 5, 241)
    dens = np.array(density.kde(np.random.default_rng(1).normal(1, 0.5, 400), edges))
    check(failures, abs((dens * np.diff(edges)).sum() - 1) < 1e-9, "la densidad suma área 1")
    check(failures, abs((edges[1:] + edges[:-1])[dens.argmax()] / 2 - 1) < 0.15,
          "la moda de la densidad cae donde la muestra (1)")
    flat = np.array(density.kde(np.full(20, 3.0), edges))
    check(failures, np.isfinite(flat).all() and flat.argmax() == np.abs(edges[:-1] - 3).argmin(),
          "una muestra constante no rompe el ancho de banda")
    cells = pd.DataFrame({"variant_id": ["a", "b", "a", "b"], "market": ["M1", "M1", "M2", "M2"],
                          "segment": "build", "value": [0.8, 1.9, 1.2, 1.1], "x": [1, 2, 1, 2],
                          "y": [1, 1, 1, 1]})
    theta = pd.Series({"x": 1, "y": 1})
    made = grids.markets(cells, "build", "x", "y", {"x": [1, 2], "y": [1]}, ["M1", "M2"], theta, 1,
                         "Profit Factor")
    lo, hi = made[0]["scale_range"]
    check(failures, made[0]["scale"] == "diverging" and abs((lo + hi) / 2 - 1.0) < 1e-12,
          "la escala del Profit Factor está centrada en 1: rojo es perder, verde ganar")

    print()
    if failures:
        sys.exit(f"{len(failures)} propiedades rotas: {failures}")
    print("todas las propiedades se cumplen")


if __name__ == "__main__":
    main()
