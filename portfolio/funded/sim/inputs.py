"""What a bank run is given: the config with the owner's inputs checked, and the path set."""

import json
from pathlib import Path

import numpy as np

from core.study import config as study_config
from portfolio.funded.sim.bank import ARRAYS

FILE = Path(__file__).parent / "config.yaml"
REBUY = ("same_plan", "none")     # the re-buy policies the kernel knows
OWNER = {
    "eurusd": "el cambio EUR/USD del día del cálculo (dólares por euro)",
    "rebuy": "las políticas de recompra que se comparan: lista de same_plan (recomprar el mismo plan mientras quede caja) y/o none",
    "haircuts": "los recortes h de la curva VE(h), p. ej. [0, 0.25, 0.5, 0.75, 1]",
    "haircut_decides": "el recorte h con el que se ordena la tabla (uno de owner.haircuts)",
    "payout_cushion": "fracción del tamaño que se deja en la cuenta en cada cobro (0 = retirar todo)",
    "tax_rate": "fracción de cada cobro que se va en impuestos (0 sólo si tú dices 0)",
    "payout_fee": "fracción de cada cobro que se va en comisiones de pago y divisa",
    "p_payout_denied": "probabilidad de que la empresa deniegue un cobro",
    "p_firm_closes_year": "probabilidad de que la empresa cierre en un año",
}


def load(overrides: list[str]) -> dict:
    """The module's config with `section.key=value` overrides applied."""
    return study_config.load(FILE, overrides)


def refuse(cfg: dict) -> list[str]:
    """Every owner input still missing or unreadable, one Spanish line each; empty = go."""
    owner = cfg["owner"]
    out = [f"owner.{key} — {what}" for key, what in OWNER.items() if owner[key] is None]
    rebuy = owner["rebuy"]
    if rebuy is not None and not (isinstance(rebuy, list) and rebuy and set(rebuy) <= set(REBUY)
                                  and len(set(rebuy)) == len(rebuy)):
        out.append(f"owner.rebuy = {rebuy!r}: una lista sin repetir de {' y/o '.join(REBUY)}")
    if None not in (owner["haircuts"], owner["haircut_decides"]) \
            and owner["haircut_decides"] not in owner["haircuts"]:
        out.append(f"owner.haircut_decides = {owner['haircut_decides']}: no está en owner.haircuts")
    return out


def paths(file: Path) -> tuple[dict[str, np.ndarray], dict]:
    """A path set from its `.npz`.

    Args:
        file: Arrays `closed`, `float_end`, `low`, `high` (float64 [n_paths, horizon]) and
            `opened` (int32), the server-day table D per draw; scalars `unit_risk` (account
            currency risked per trade at which the arrays are written) and `days_per_year`
            (path days in a year); optional `synthetic` (true = not a look at data: no ledger
            row), `label` and `source` (a JSON string: where `frompool` drew it from).

    Returns:
        The five arrays, C-contiguous, and `unit_risk`, `days_per_year`, `synthetic`, `label`,
        `source` (`None` for a path set that names none).
    """
    with np.load(file) as z:
        arrays = {name: np.ascontiguousarray(z[name], dtype=np.int32 if name == "opened" else np.float64)
                  for name in ARRAYS}
        meta = {"unit_risk": float(z["unit_risk"]), "days_per_year": float(z["days_per_year"]),
                "synthetic": bool(z["synthetic"]) if "synthetic" in z else False,
                "label": str(z["label"]) if "label" in z else file.stem,
                "source": json.loads(str(z["source"])) if "source" in z else None}
    return arrays, meta
