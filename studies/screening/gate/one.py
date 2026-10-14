"""One strategy through the gate, as the contract's data: where it fell, and every fact of every level."""

import time
from typing import Any

import pandas as pd

from core.study import blocks, result as envelope
from studies.screening.gate.levels import LEVELS

MODULE = "gate"


def run(identity: str, scores: pd.DataFrame, cfg: dict) -> dict[str, Any]:
    """What every level measured on one strategy, read off the scorecard.

    Args:
        identity: The strategy's identity, the scorecard's index.
        scores: What cascade.run() returned.
        cfg: What inputs.config() returned.

    Returns:
        The contract dict. The verdict is the one the judge will give from these facts:
        DESCARTAR with the level and the rule it fell at, LIMBO with the rules that leave it
        there, or MANTENER; and one row per fact. A level after the one it fell at was not
        run on it.
    """
    started = time.time()
    r = scores.loc[identity]
    doubt = r["limbo"] if isinstance(r["limbo"], str) else ""
    if not r["survives"]:
        said = blocks.verdict(
            "DESCARTAR",
            "fail",
            f"Cayó en el nivel {r['cayo_nivel']}: {r['cayo_regla']}",
        )
    elif doubt:
        said = blocks.verdict("LIMBO", "watch", f"Sigue, en limbo por: {doubt}")
    else:
        said = blocks.verdict("MANTENER", "pass", "Pasa todas las reglas del paso 8.")
    table = blocks.table(
        "Cada hecho",
        pd.DataFrame(
            [
                [fact, level, None if pd.isna(r[fact]) else float(r[fact])]
                for level, module in LEVELS
                for fact in module.FACTS
            ],
            columns=pd.Index(["hecho", "nivel", "valor"]),
        ),
        "Un hecho sin valor es de un nivel al que la estrategia no llegó, o no se pudo medir.",
    )
    name = r["strategy"] if isinstance(r["strategy"], str) else r["strategy_build"]
    return envelope.envelope(
        MODULE,
        name,
        identity,
        cfg,
        started,
        [envelope.tab("levels", "Los niveles, hecho a hecho", [table])],
        said,
        summary={"survives": bool(r["survives"]), "cayo_nivel": r["cayo_nivel"] or ""},
    )
