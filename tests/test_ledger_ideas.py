#!/usr/bin/env python3
"""Known answer: the hypotheses the research memory counts raise the ledger's N and lower the DSR."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ledger import trials  # noqa: E402
from studies.research.memory import trials as research  # noqa: E402

SEED = 7
TEMPLATES = {
    "breakLong": {"archetype": "breakout", "shape": "market_long"},
    "breakShort": {"archetype": "breakout", "shape": "market_short"},
    "trendLong": {"archetype": "trendFollowing", "shape": "market_long"},
    "ideaBreak": {"archetype": "breakout", "shape": "market_long"},
}


def idea(
    name: str, direction: str, file: str, measured: int, timeframe: str = "H4"
) -> dict:
    """One row of the ideas index."""
    return {
        "idea": name,
        "symbol": "XAUUSD",
        "timeframe": timeframe,
        "direction": direction,
        "file": file,
        "hypotheses_measured": measured,
    }


def main() -> None:
    """Build a synthetic ledger and a synthetic memory and check the count and the DSR."""
    failures = []
    rng = np.random.default_rng(SEED)
    scores = [rng.normal(0.0, 0.02, n) for n in (30, 20)]
    frame = pd.DataFrame(
        [
            {
                "n_scored": s.size,
                "sharpe_mean": s.mean(),
                "sharpe_std": s.std(ddof=1),
                "score_unit": "per_period",
            }
            for s in scores
        ]
    )
    ideas = [
        idea("ideaBreak", "long", "a.md", 24),
        idea("loose", "long", "a.md", 24),
        idea("looseShort", "short", "a.md", 24),
        idea("other", "long", "b.md", 5),
        idea("elsewhere", "long", "c.md", 9, "H1"),
    ]

    def spent(family: str) -> dict:
        """What the synthetic memory spent on the XAUUSD H4 study of that family."""
        return research.spent(ideas, TEMPLATES, "XAUUSD", "H4", family)

    # Each file once; a long study never counts the short idea; no family counts everywhere.
    for family, hypotheses, n_ideas in (
        ("breakLong", 29, 3),
        ("trendLong", 29, 2),
        ("breakShort", 24, 1),
        ("mt5verify", 29, 4),
    ):
        got = spent(family)
        if (got["hypotheses"], got["ideas"]) != (hypotheses, n_ideas):
            failures.append(
                f"{family}: {got['hypotheses']} hipótesis de {got['ideas']} ideas, "
                f"esperaba {hypotheses} de {n_ideas}"
            )
    if research.spent([], TEMPLATES, "XAUUSD", "H4", "breakLong")["hypotheses"]:
        failures.append("una memoria vacía cuenta hipótesis")

    # K = 0 changes nothing; K > 0 raises N, leaves sigma alone and lowers the DSR strictly.
    plain, zero = trials.accumulated(frame), trials.accumulated(frame, 0)
    more = trials.accumulated(frame, spent("breakLong")["hypotheses"])
    if (more["n"], more["searched"], more["extra"]) != (79, 50, 29):
        failures.append(
            f"accumulated: N {more['n']} = {more['searched']} + {more['extra']}"
        )
    if more["sigma"] != plain["sigma"]:
        failures.append("las hipótesis movieron la sigma")
    returns = rng.normal(0.16, 1.0, 500)
    dsr = [
        trials.deflated(returns, c["sigma"], c["n"])["dsr"] for c in (plain, zero, more)
    ]
    if dsr[0] != dsr[1]:
        failures.append(f"K = 0 cambia el DSR: {dsr[0]} -> {dsr[1]}")
    if not dsr[2] < dsr[0]:
        failures.append(f"el DSR no baja con K = 29: {dsr[0]:.6f} -> {dsr[2]:.6f}")

    print(
        "\n".join(failures)
        or f"ok: cada fichero cuenta una vez y sólo en su dirección; con K = 0 el DSR es idéntico "
        f"({dsr[0]:.6f}) y con K = 29 sobre N = 50 baja a {dsr[2]:.6f}"
    )
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
