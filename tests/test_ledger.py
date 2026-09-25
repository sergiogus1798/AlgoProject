#!/usr/bin/env python3
"""The ledger's two guarantees: the door refuses, and pooling widens what the DSR must clear."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.surface import plateau
from ledger import gate, record, trials

SEED = 3


def rows(units: str = "per_period") -> pd.DataFrame:
    """Two searches of one study, with known moments.

    Args:
        units: What `score_unit` both rows carry.

    Returns:
        A frame shaped like `study.read`'s, built without touching the data root.
    """
    rng = np.random.default_rng(SEED)
    first, second = rng.normal(0.02, 0.05, 400), rng.normal(-0.01, 0.06, 1600)
    made = []
    for step, scores in ((8, first), (16, second)):
        row = record.search("T", {"step": step, "launched_by": "test", "symbol": "XAUUSD",
                                  "timeframe": "M30", "segment": "oos1", "n_in": 10,
                                  "n_out": 5, "criterion": "x", "score_unit": units},
                            scores)
        made.append(row)
    return pd.DataFrame(made), np.concatenate([first, second])


def main() -> None:
    """Check the door, the pooling and what the pooling does to the benchmark."""
    failures = []

    # The one-way door, on the real policy: step 8 may not read what is reserved for 17/19.
    try:
        gate.allow(8, "oos2", "XAUUSD")
        failures.append("gate: el paso 8 pudo mirar oos2")
    except PermissionError:
        pass
    gate.allow(17, "oos2", "XAUUSD")
    gate.allow(8, "oos1", "XAUUSD")

    # Step 20 stays blind until all three have run.
    frame, pooled = rows()
    try:
        gate.allow_read(frame)
        failures.append("gate: dejo leer 17/18/19 sin que estuvieran los tres")
    except PermissionError:
        pass
    done = pd.DataFrame([{"step": s} for s in (17, 18, 19)])
    gate.allow_read(done)

    # Pooling the stored moments must equal the moments of the union, exactly.
    counted = trials.accumulated(frame)
    if counted["n"] != pooled.size:
        failures.append(f"accumulated: N {counted['n']} contra {pooled.size}")
    if abs(counted["sigma"] - pooled.std(ddof=1)) > 1e-9:
        failures.append(f"accumulated: sigma {counted['sigma']:.9f} contra "
                        f"{pooled.std(ddof=1):.9f} de la union")

    # Two units are never averaged together.
    mixed = frame.copy()
    mixed.loc[mixed.index[0], "score_unit"] = "annualised"
    try:
        trials.accumulated(mixed)
        failures.append("accumulated: agrupo un Sharpe anualizado con uno por observacion")
    except ValueError:
        pass

    # The point of the module: a wider N raises the bar the Sharpe has to clear.
    local = int(frame["n_scored"].iloc[-1])
    near = plateau.expected_max_sharpe(counted["sigma"], local)
    whole = plateau.expected_max_sharpe(counted["sigma"], counted["n"])
    if not whole > near:
        failures.append(f"el benchmark no sube al acumular: {near:.4f} -> {whole:.4f}")
    returns = np.random.default_rng(SEED).normal(0.16, 1.0, 500)
    one = trials.deflated(returns, counted["sigma"], local)
    both = trials.deflated(returns, counted["sigma"], counted["n"])
    if not both["dsr"] < one["dsr"]:
        failures.append(f"el DSR no baja al acumular: {one['dsr']:.4f} -> {both['dsr']:.4f}")

    print("\n".join(failures) or
          f"ok: la puerta rechaza el paso 8 sobre oos2 y el 20 sin los tres; la sigma "
          f"agrupada reproduce la union exactamente; y al pasar de N={local} a "
          f"N={counted['n']} el benchmark sube {near:.4f} -> {whole:.4f} y el DSR baja "
          f"{one['dsr']:.4f} -> {both['dsr']:.4f}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
