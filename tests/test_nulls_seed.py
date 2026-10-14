#!/usr/bin/env python3
"""Known-answer test for the monkey's seed: one root gives one set of p-values whatever the
order or the process a strategy runs in, another root gives other draws, and a root left out
is drawn fresh and small enough to survive a CSV cell."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import fanout
from engines.nulls import inputs, model, simulate, verdict
from studies.screening.analysis import resample

BARS, TRADES, DRAWS = 20_000, 120, 300
NAMES = [f"Strategy 1.{i}" for i in range(6)]
_CFG: dict = {}


def kept(name: str) -> dict:
    """What simulate.fixed() returns, built by hand on a random walk: no export needed.

    Args:
        name: The strategy; it only picks which trades it holds, the same in every process.
    """
    rng = np.random.default_rng(simulate._stable(name) % 2**32)
    price = 100 + np.cumsum(np.random.default_rng(1).normal(0, 0.1, BARS))
    entry = np.sort(rng.choice(BARS - 100, TRADES, replace=False))
    hold = rng.integers(1, 40, TRADES)
    located = {
        "entry": entry,
        "exit": entry + hold,
        "hold": hold,
        "size": rng.uniform(0.1, 1.0, TRADES),
        "window": (0, BARS - 1),
    }
    return {
        "located": located,
        "value": 100.0,
        "cost": np.full(TRADES, 0.5),
        "levels": {},
        "bars": {"enter_px": price, "leave_px": price, "low": price, "high": price},
    }


def pvalues(name: str) -> dict:
    """Every rung's p on every statistic for one strategy, as the monkey's panel holds them."""
    held = kept(name)
    seen = simulate.real(held, _CFG["statistics"]["report"])
    return {
        f"{rung}_{stat}": verdict.pvalue(seen[stat], drawn[stat], stat)
        for rung in model.RUNGS
        for drawn in [simulate.nulls(held, rung, _CFG, name)]
        for stat in seen
    }


def panel(seed: int, names: list[str], workers: int) -> dict:
    """One run of the population under one root, serial or forked."""
    _CFG.clear()
    _CFG.update(inputs.config([f"nulls.draws={DRAWS}"] + inputs.seeded(seed)))
    if workers == 1:
        return {name: pvalues(name) for name in names}
    return dict(fanout.run(pvalues, {name: 1 for name in names}, workers))


def main() -> None:
    """Fail loudly on the first property that does not hold."""
    failures = []
    serial = panel(7, NAMES, 1)
    if panel(7, NAMES[::-1], 4) != serial:
        failures.append("misma semilla, otro orden y 4 procesos: los p cambian")
    if panel(7, NAMES[:2], 1) != {n: serial[n] for n in NAMES[:2]}:
        failures.append("misma semilla, menos estrategias en el lote: los p cambian")
    if panel(8, NAMES, 1) == serial:
        failures.append("otra semilla dio los mismos p")
    held = kept(NAMES[0])
    a, b, c = (
        simulate.nulls(
            held,
            "free",
            inputs.config([f"nulls.draws={DRAWS}", f"nulls.seed={s}"]),
            NAMES[0],
        )["net"]
        for s in (7, 7, 8)
    )
    if not np.array_equal(a, b) or np.array_equal(a, c):
        failures.append("los monos de una estrategia no dependen sólo de la semilla")
    if np.array_equal(a, simulate.nulls(held, "free", _CFG, NAMES[1])["net"]):
        failures.append("dos estrategias sacaron los mismos monos")
    # The four rungs share one stream (N12 B, 2026-10-13): handed the same model, they draw the same.
    spare, model.RUNGS["free"] = model.RUNGS["free"], model.RUNGS["timing"]
    if not np.array_equal(
        simulate.nulls(held, "free", _CFG, NAMES[0])["net"],
        simulate.nulls(held, "timing", _CFG, NAMES[0])["net"],
    ):
        failures.append(
            "dos peldaños con el mismo modelo no comparten el flujo aleatorio"
        )
    model.RUNGS["free"] = spare
    # Restored from the flipped assertion: different models do give different monkeys, and
    # level 3c's stream is not the stream of 3a/b (numpy pads [s, k] to [s, k, 0]).
    if np.array_equal(
        simulate.nulls(held, "free", _CFG, NAMES[0])["net"],
        simulate.nulls(held, "timing", _CFG, NAMES[0])["net"],
    ):
        failures.append("dos peldaños con modelos distintos sacaron los mismos monos")
    if np.array_equal(
        resample.stream(5, "k").random(4), resample.stream(5, "k|mono").random(4)
    ):
        failures.append("el flujo de 3c es el de 3a/b")
    if np.array_equal(
        np.random.default_rng([5, simulate._stable("k"), simulate.TAG, 0]).random(4),
        resample.stream(5, "k").random(4),
    ):
        failures.append("el flujo de los monos es el de remuestreo")
    fresh = [inputs.config([])["nulls"]["seed"] for _ in range(2)]
    if fresh[0] == fresh[1] or max(fresh) >= 2**32:
        failures.append(f"semilla fresca: {fresh} (iguales, o no caben en 32 bits)")
    if inputs.config(inputs.seeded(20261002))["nulls"][
        "seed"
    ] != 20261002 or inputs.seeded(None):
        failures.append("--seed no llega a nulls.seed")
    print("\n".join(failures) or "ok: una semilla, unos p; otra semilla, otros monos")
    sys.exit(bool(failures))


if __name__ == "__main__":
    main()
