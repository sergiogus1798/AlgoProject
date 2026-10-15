"""The fixed-risk mode's own pieces of the judge (encargo 61): the real-loss cap and the no-stop verdict."""

from typing import Any

import pandas as pd

from core.study import blocks
from mt5.verify import firms


def require_cap(th: dict) -> float:
    """The real-loss cap per trade in USD (`mt5verify.loss_cap_usd`), or a loud refusal.

    The owner has not given the figure yet (encargo 61-4c): no default is invented, so the
    risk mode cannot be judged until he writes it in `ledger/thresholds.yaml`.
    """
    cap = th.get("loss_cap_usd")
    if cap is None:
        raise SystemExit(
            "mt5verify.loss_cap_usd no tiene valor: el dueño no ha dado el tope de pérdida "
            "real por operación (encargo 61-4c). Ponlo en ledger/thresholds.yaml; sin él el "
            "modo de riesgo fijo no se juzga"
        )
    return float(cap)


def loss_cap_row(sqx: pd.DataFrame, mt5: pd.DataFrame, th: dict) -> dict[str, Any]:
    """Row 7, fixed-risk mode only: the worst real loss of one trade, USD, against the cap.

    A trade that loses more than `loss_cap_usd` fails the strategy (owner, 2026-10-15, 61-4e);
    the worst of the two sides counts. Refuses while the cap is unset (`require_cap`).
    """
    cap = require_cap(th)
    worst = max(
        -float(sqx["Profit/Loss USD"].min()),
        -float(mt5["Profit/Loss USD"].min()),
        0.0,
    )
    return {
        "row": "7",
        "label": "pérdida real de la peor operación, USD",
        "value": worst,
        "limit": cap,
        "state": "pass" if worst <= cap else "fail",
        "note": "la peor de las dos partes, con el stop real y sus huecos; la estrategia "
        "falla si una operación pierde más que el tope",
    }


def no_stop(firm: str) -> dict[str, Any]:
    """The fixed-risk mode of a strategy with no stop loss: nothing to size from, no verdict.

    Returns:
        A piece with a «none» verdict block and summary, which `ticks.keep_risk` files.
    """
    label = firms.label(firm)
    verdict = blocks.verdict(
        "Sin veredicto",
        "none",
        f"{label} · riesgo fijo — la estrategia no lleva stop loss: no hay SL desde el que "
        "dimensionar el riesgo, el modo no se puede comprobar y, con los dos modos "
        "obligatorios, la estrategia no queda validada.",
    )
    return {
        "verdict": {**verdict, "firm": firm},
        "summary": {"firm": firm, "state": "none"},
    }
