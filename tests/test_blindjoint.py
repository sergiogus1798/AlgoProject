#!/usr/bin/env python3
"""Step 20 on mothers whose answer is known: noise names nobody, a planted edge is named, the pieces veto."""

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ledger import gate
from studies.closing.blindJoint import inputs, many, measure, one, readings
from studies.closing.blindJoint.pieces import PIECES

DAYS, K, SEEDS = 1250, 5, 20
CFG = inputs.config(["bootstrap.reps=500"])


def mothers(states: dict[str, list[str]], missing: dict[str, list[str]] = None) -> pd.DataFrame:
    """A population as pieces.population returns it, with each piece's state given.

    Args:
        states: {mother: four state words, in PIECES order}.
        missing: {mother: pieces it lacks}; such a mother is incomplete and never read.

    Returns:
        The frame.
    """
    missing = missing or {}
    rows = []
    for m, words in states.items():
        lacks = missing.get(m, [])
        rows.append({"mother": m, "batch": None, "identity": None, "complete": not lacks,
                     "missing": lacks, **{p: None if lacks else
                                          {"label": w, "state": w, "score": None,
                                           "meaning": "", "summary": {}}
                                          for p, w in zip(PIECES, words)}})
    return pd.DataFrame(rows).set_index("mother")


def market(seed: int, edge: str | None) -> dict:
    """Mothers of fat-tailed noise sharing a factor, the asset's moves, one edge planted or none.

    Args:
        seed: Seed of the draw.
        edge: The mother given a true daily Sharpe of 0.25 (about 0.18 once buy and hold
            at equal risk is subtracted), or None.

    Returns:
        `panel`, `moves` and `point_value`, as report.py hands them to measure.run.
    """
    rng = np.random.default_rng(seed)
    names = [f"m{i}" for i in range(K)]
    panel = pd.DataFrame(0.4 * rng.standard_t(4, (DAYS + 1, 1)) +
                         rng.standard_t(4, (DAYS + 1, K)), columns=names)
    if edge:
        panel[edge] += 0.25 * panel[edge].std()
    moves = pd.Series(np.r_[np.nan, rng.normal(0.0, 1.0, DAYS)], index=panel.index)
    return {"panel": panel, "moves": moves, "point_value": 100.0}


def main() -> None:
    """Run the controls and exit non-zero on any failure."""
    failures = []
    passing = mothers({f"m{i}": ["pass"] * 4 for i in range(K)})
    everyone = readings.label(("ninguna", "entrantes"))

    false = sum(bool(measure.run({"population": passing, **market(s, None)}, CFG)
                     ["named"][everyone]) for s in range(SEEDS))
    # Binomial(20, 0.05): four or more false families happens 1.6 % of the time.
    if false > 3:
        failures.append(f"ruido: el StepM nombra a alguna madre en {false} de {SEEDS} semillas")

    hits = 0
    vetoed = mothers({"m0": ["pass"] * 4, "m1": ["pass", "pass", "fail", "watch"],
                      **{f"m{i}": ["pass"] * 4 for i in range(2, K)}})
    for s in range(SEEDS):
        got = measure.run({"population": vetoed, **market(s, "m1")}, CFG)
        hits += "m1" in got["named"][everyone]
        calls = got["calls"].loc["m1"]
        if calls["unanimidad+entrantes"] != "fail" or calls["sin_fallo+supervivientes"] != "fail":
            failures.append(f"semilla {s}: una pieza en fail no veta a m1 ({calls.to_dict()})")
        if calls[everyone] != "pass":
            failures.append(f"semilla {s}: con las piezas de contexto m1 no pasa")
    if hits < SEEDS:
        failures.append(f"edge plantado: el StepM lo nombra en {hits} de {SEEDS}")

    states = measure.states(vetoed)
    if readings.kept(states, "sin_fallo") != ["m0", "m2", "m3", "m4"] or \
            readings.kept(states, "unanimidad") != ["m0", "m2", "m3", "m4"]:
        failures.append("readings: fail no descarta")
    watch = measure.states(mothers({"a": ["pass", "watch", "pass", "pass"]}))
    if readings.kept(watch, "sin_fallo") != ["a"] or readings.kept(watch, "unanimidad"):
        failures.append("readings: watch debe pasar sin_fallo y no unanimidad")

    blind = mothers({"a": ["pass"] * 4, "b": ["pass"] * 4}, {"b": ["wfc", "cscv"]})
    refused = {"population": blind, "refused": "política", "source": "test"}
    got = many.run(refused, CFG)
    member = {m["strategy"]: m for m in got["members"]}
    if member["b"]["verdict"]["label"] != "INCOMPLETA" or "b" in got["measured"]["states"].index:
        failures.append("una madre incompleta se ha leído")
    if set(got["measured"]["calls"].loc["a"]) != {"none"}:
        failures.append("sin oos2 la llamada de una madre que pasa las piezas debe quedar sin leer")
    if one.chosen(CFG) is not None or got["population"]["verdict"]["label"] != "SIN REGLA":
        failures.append("sin regla del dueño el paso 20 ha elegido una lectura")

    inputs.blind_door("TEST_M1_nunca_corrido")          # a human is never refused
    os.environ[gate.AUTONOMOUS] = "1"                    # an autonomous agent is
    try:
        inputs.blind_door("TEST_M1_nunca_corrido")
        failures.append("la puerta ciega dejó leer a un agente autónomo un estudio sin 17, 18 ni 19")
    except PermissionError:
        pass
    os.environ.pop(gate.AUTONOMOUS)

    print("\n".join(failures) or
          f"ok: sobre ruido el StepM nombra alguna madre en {false} de {SEEDS} semillas; el "
          f"edge plantado sale nombrado en {hits} de {SEEDS} y aun así una pieza en fail lo "
          f"veta bajo unanimidad y sin_fallo; una madre incompleta no se lee; sin oos2 no se "
          f"decide; y la puerta ciega se niega sin 17, 18 y 19")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
