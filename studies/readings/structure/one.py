"""One mother's structural reading, returned as the contract's data: what the window paints."""

import time
from pathlib import Path

from core import sqxfile
from core.study import result as envelope
from studies.readings.structure import contract, measure, reading

MODULE = "studies.readings.structure"
GLOSSARY = [
    {"term": "Ablación", "text": "La misma estrategia con una condición de entrada borrada. En "
     "un AND es la condición neutralizada; en un OR, forzada a falso."},
    {"term": "ΔM", "text": "Madre menos ablación, por operación: lo que la condición añade. "
     "Nunca en beneficio total, porque quitar una condición cambia cuántas operaciones hay."},
    {"term": "Recorte al azar", "text": "Tantas operaciones como tiene la madre, sacadas al "
     "azar de la estrategia sin la condición. Si la madre no es mejor que eso, la condición "
     "sólo reduce la muestra (engines/nulls/filter.py)."},
    {"term": "Inversión", "text": "Las mismas entradas con la orden al revés. A precio medio "
     "es el espejo exacto; lo que queda de diferencia son el spread y el swap."},
    {"term": "Precio medio", "text": "La mitad entre compra y venta: el movimiento del "
     "mercado sin el spread, reconstruido de las dos operaciones emparejadas."}]


def legs_of(got: dict, rows: dict, cfg: dict) -> dict:
    """Every measurement for one mother on every leg, with the words each one earns.

    Args:
        got: What `inputs.load` returned.
        rows: The mother's plan rows grouped by kind.
        cfg: The study's config.

    Returns:
        {segment: {"ablations": [...], "inversion": {...}, "identity": [...]}}.
    """
    retained = {(r.leg, r.variant_id): bool(r.ok) for r in got["retained"].itertuples()}
    origin = rows["identity"][0]
    out = {}
    for leg, frames in got["legs"].items():
        mother = frames[origin["variant_id"]]
        ablations = []
        for row in rows.get("ablation", []):
            found = measure.ablation(mother, frames[row["variant_id"]], cfg)
            found |= {"block": row["block"], "signal": row["signal"],
                      "variant_id": row["variant_id"],
                      "retained": retained[(leg, row["variant_id"])]}
            found["label"] = reading.condition(found, found["retained"],
                                               cfg["verdict"]["alpha"])
            ablations.append(found)
        inverted = rows["inversion"][0]["variant_id"]
        inv = measure.inversion(mother, frames[inverted], got["point_value"])
        inv["retained"] = retained[(leg, inverted)]
        inv["label"] = reading.direction(inv, cfg["controls"]["min_paired"])
        out[leg] = {"ablations": ablations, "inversion": inv,
                    "identity": measure.identity(mother, origin["mother"],
                                                 cfg["controls"]["identity_tolerance"]),
                    "identity_retained": retained[(leg, origin["variant_id"])]}
    return out


def run(strategy: str, got: dict, cfg: dict) -> dict:
    """Which condition carries one mother's edge, and whether it lives in the entry's direction.

    Args:
        strategy: The mother's name, as the plan's `strategy` column spells it.
        got: What `inputs.load` returned.
        cfg: What `inputs.config` returned.

    Returns:
        The contract dict: three tabs and no overall verdict. The study describes; removing
        a condition is the owner's decision, logged and revalidated apart (encargo 12 §5).
    """
    started = time.time()
    plan = got["plan"][got["plan"]["strategy"] == strategy]
    rows = {k: g.to_dict("records") for k, g in plan.groupby("kind")}
    found = legs_of(got, rows, cfg)
    summary = {f"{a['block']}@{leg}": a["label"]
               for leg, f in found.items() for a in f["ablations"]}
    summary |= {f"inversion@{leg}": f["inversion"]["label"] for leg, f in found.items()}
    return envelope.envelope(
        MODULE, strategy, sqxfile.identity(Path(rows["identity"][0]["mother"])), cfg, started,
        [contract.conditions_tab(found), contract.inversion_tab(found),
         contract.controls_tab(found)],
        warnings=[{"code": "diagnostico", "state": "info",
                   "text": "Diagnóstico, nunca selección (encargo 12 §5): una ablación que "
                           "mejora no es una estrategia mejor. Quitar la condición es decisión "
                           "del dueño, se anota en el ledger y se revalida aparte."},
                  {"code": "sin_stops", "state": "info",
                   "text": "La inversión es espejo exacto sólo sin stop, target ni trailing; "
                           "la fábrica se niega a invertir una estrategia que los lleve."}],
        glossary=GLOSSARY, summary=summary)
