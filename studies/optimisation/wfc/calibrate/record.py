"""The register that opens the blind block, or does not: the two reference rates against their caps."""

from typing import Any, cast
import json
from datetime import date
from pathlib import Path

import pandas as pd
import yaml

from core.study.config import fingerprint
from ledger import gate
from studies.optimisation.wfc.calibrate import families
from studies.optimisation.wfc.calibrate.rehearsal import Rehearsal

STEP = "17"


def comma(value: float) -> str:
    """A rate as the report writes it: two decimals, decimal comma."""
    return f"{value:.2f}".replace(".", ",")


def decide(table: pd.DataFrame, cfg: dict) -> dict[str, Any]:
    """Whether the criterion stays under the two caps at the reference cells.

    Args:
        table: What `rates.table` returned.
        cfg: The calibration's config: `reference`, `max_false_pass`, `max_false_fail`.

    Returns:
        `falso_pasa` (PASA with no edge and no cost) and `falso_no_pasa` (NO PASA with the
        reference edge, the worse of with and without order), both at the reference length,
        with the same two of the criterion without a null on the level (`_sin`); `abre`,
        true when neither exceeds its cap; and `motivo`, in Spanish.
    """
    ref = cfg["reference"]
    at = cast(
        pd.DataFrame,
        table[
            (table["bloque"] == "rejilla") & (table["anos_fuera"] == ref["years_out"])
        ],
    )
    none = cast(pd.DataFrame, at[(at["tipo"] == families.NONE) & (at["sharpe"] == 0)])
    edge = cast(
        pd.DataFrame, at[(at["tipo"] != families.NONE) & (at["sharpe"] == ref["edge"])]
    )
    got = {
        "falso_pasa": float(none["pasa"].iloc[0]),
        "falso_no_pasa": float(edge["no_pasa"].max()),
        "falso_pasa_sin": float(none["pasa_sin"].iloc[0]),
        "falso_no_pasa_sin": float(edge["no_pasa_sin"].max()),
    }
    over = [
        f"falso PASA sin ventaja {comma(got['falso_pasa'])} > tope "
        f"{comma(cfg['max_false_pass'])}"
    ] * (got["falso_pasa"] > cfg["max_false_pass"]) + [
        f"falso NO PASA con Sharpe {str(ref['edge']).replace('.', ',')} "
        f"{comma(got['falso_no_pasa'])} > tope {comma(cfg['max_false_fail'])}"
    ] * (got["falso_no_pasa"] > cfg["max_false_fail"])
    return got | {
        "abre": not over,
        "motivo": "; ".join(over) or "las dos tasas de referencia están bajo su tope",
    }


def build(
    decision: dict, table: pd.DataFrame, rehearsed: Rehearsal, cfg: dict, wfc: dict
) -> dict[str, Any]:
    """The register as `ledger.gate.seal` reads it.

    Returns:
        `fecha`, `criteria_sha256` (today's entry "17" of criteria.yaml), `abre`, and
        `tasas`: the synthetic table and the rehearsal; plus the reason, the caps, the
        reference and the two configs' fingerprints.
    """
    entry = yaml.safe_load(gate.CRITERIA.read_text(encoding="utf-8"))["steps"][STEP]
    return {
        "fecha": date.today().isoformat(),
        "criteria_sha256": gate.criteria_hash(entry),
        "abre": decision["abre"],
        "motivo": decision["motivo"],
        **{k: v for k, v in decision.items() if k.startswith("falso_")},
        "topes": {
            "falso_pasa": cfg["max_false_pass"],
            "falso_no_pasa": cfg["max_false_fail"],
        },
        "referencia": cfg["reference"],
        "criterio": "con nulo de volteo semanal en el nivel (mediana neta del top > 0 y "
        "p ≤ wfc.level_alpha); orden en bruto (dueño, 2026-10-08)",
        "comparacion": "sin sufijo: el criterio; `_sin`: sin nulo en el nivel",
        "config": {"calibrate": fingerprint(cfg), "wfc": fingerprint(wfc)},
        "tasas": {
            "sinteticas": table.to_dict("records"),
            "ensayo_build_oos1": rehearsed,
        },
    }


def write(path: Path, register: dict) -> None:
    """Leave the register where the seal looks for it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(register, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
