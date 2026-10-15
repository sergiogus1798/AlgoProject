"""«Entradas del dueño» (encargo 54, A): the inputs the funding modules refuse without, written from the window.

The one writer is `set_field`: it puts one typed value in the owner's local layer
(`config/owner.yaml`, not in git — owner 2026-10-14, decision 14) and nothing else. A value the
owner did not type is never written: a blank box removes the line and the base file's value
(`null` for the open ones) comes back.
"""

from datetime import date
from typing import Any

from core import assetyaml
from core.study import config as study_config
from ledger import thresholds
from portfolio.common.construct.inputs import config as construct_config
from portfolio.funded.sim import inputs as sim_inputs

HEADER = (
    "# Written by the window's «Entradas del dueño» (encargo 54, A). Local to this machine, not in git.\n"
    "# Laid over portfolio/funded/sim/config.yaml (sim) and portfolio/common/construct/config.yaml\n"
    "# (construct) before any --set; delete a line to go back to the file's value.\n"
)
FRACTION, POSITIVE, DAYS, CHOICE = "fraction", "positive", "days", "choice"
STAYS = ("stays", "initial")
# (module, section, key, kind, options, label, what it is, what it blocks)
FIELDS = (
    (
        "sim",
        "owner",
        "eurusd",
        POSITIVE,
        (),
        "Cambio EUR/USD",
        "dólares por euro el día del cálculo; se escribe junto al resultado, nunca se busca en la red",
        "la caja del banco",
    ),
    (
        "sim",
        "owner",
        "budget_eur",
        POSITIVE,
        (),
        "Caja en euros",
        "lo que hay en la cuenta bancaria; tope duro de las recompras",
        "la caja del banco",
    ),
    (
        "sim",
        "owner",
        "payout_cushion",
        FRACTION,
        (),
        "Colchón de retiro",
        "fracción del tamaño que se deja en la cuenta en cada cobro; 0 = retirar todo",
        "la caja del banco",
    ),
    (
        "sim",
        "owner",
        "tax_rate",
        FRACTION,
        (),
        "Impuestos",
        "opcional; vacío = apagado (no se calcula ni se muestra nada de impuestos). Con una fracción, se muestra al lado del dinero, nunca entra en un cálculo",
        "la caja del banco",
    ),
    (
        "sim",
        "owner",
        "payout_fee",
        FRACTION,
        (),
        "Comisión de cobro",
        "fracción de cada cobro que se va en comisiones de pago y divisa",
        "la caja del banco",
    ),
    (
        "sim",
        "owner",
        "p_payout_denied",
        FRACTION,
        (),
        "Cobro denegado",
        "probabilidad de que la empresa deniegue una petición de cobro",
        "la caja del banco",
    ),
    (
        "sim",
        "owner",
        "p_firm_closes_year",
        FRACTION,
        (),
        "Cierre de la empresa",
        "probabilidad de que la empresa cierre dentro de un año",
        "la caja del banco",
    ),
    (
        "sim",
        "gaps",
        "hantec_fee_refund",
        CHOICE,
        ("true", "false"),
        "Hantec devuelve la cuota",
        "si la cuota vuelve con el primer cobro",
        "la caja, sólo si la ficha del catálogo no lo dice",
    ),
    (
        "sim",
        "gaps",
        "hantec_endurance_payout_days",
        DAYS,
        (),
        "Endurance: días entre cobros",
        "días naturales entre cobros de una Endurance fondeada",
        "la caja con planes Endurance",
    ),
    (
        "sim",
        "gaps",
        "hantec_express_floor_after_payout",
        CHOICE,
        STAYS,
        "Express: suelo tras un cobro",
        "stays = el suelo sigue donde lo dejó el máximo; initial = se fija en el saldo inicial desde el primer cobro",
        "la caja con planes Express",
    ),
    (
        "sim",
        "gaps",
        "ftmo_1step_floor_after_payout",
        CHOICE,
        STAYS,
        "FTMO 1-step: suelo tras un cobro",
        "stays = el suelo sigue donde lo dejó el máximo; initial = se fija en el saldo inicial desde el primer cobro",
        "la caja con planes FTMO 1-step",
    ),
    (
        "construct",
        "funded",
        "open_risk_cap",
        FRACTION,
        (),
        "Riesgo abierto máximo",
        "qué fracción de la pérdida diaria máxima del plan puede estar en riesgo a la vez",
        "la etapa A y la B del fondeo",
    ),
    (
        "construct",
        "stageb",
        "t1_gap",
        CHOICE,
        ("close_to_open_blocks",),
        "Huecos del Monte Carlo T1",
        "el modelo de huecos de la etapa B (el único construido es close_to_open_blocks)",
        "la etapa B del fondeo",
    ),
)
LOADERS = {"sim": sim_inputs.load, "construct": construct_config.load}


def _base(module: str, section: str, key: str) -> Any:
    """What the repo's file holds, the layer left out (ledger placeholders filled, as the loader does)."""
    file = sim_inputs.FILE if module == "sim" else construct_config.FILE
    return thresholds.fill(study_config.load(file, []))[section][key]


def read() -> list[dict[str, Any]]:
    """Every field with the value in force, the file's value under it, and what it blocks."""
    rows = []
    for module, section, key, kind, options, label, what, blocks in FIELDS:
        now = LOADERS[module]([])[section][key]
        rows.append(
            {
                "id": f"{module}.{section}.{key}",
                "label": label,
                "help": what,
                "blocks": blocks,
                "kind": kind,
                "options": list(options),
                "value": None
                if now is None
                else str(now).lower()
                if kind == CHOICE
                else now,
                "from_layer": key in (study_config.layer(module).get(section) or {}),
                "where": "portfolio/funded/sim/config.yaml"
                if module == "sim"
                else "portfolio/common/construct/config.yaml",
            }
        )
    return rows


def _coerce(kind: str, options: tuple, label: str, typed: object) -> object:
    """What was typed as the value it means, or ValueError with the sentence to show."""
    text = str(typed).strip().replace(",", ".")
    if kind == CHOICE:
        if text not in options:
            raise ValueError(f"{label}: elige una de {', '.join(options)}.")
        return {"true": True, "false": False}.get(text, text)
    try:
        number = float(text)
    except ValueError:
        raise ValueError(f"{label}: «{typed}» no es un número.") from None
    if kind == DAYS:
        if number < 1 or not number.is_integer():
            raise ValueError(f"{label}: son días enteros, 1 o más.")
        return int(number)
    if kind == FRACTION and not 0 <= number <= 1:
        raise ValueError(f"{label}: una fracción entre 0 y 1 (5 % = 0,05).")
    if kind == POSITIVE and number <= 0:
        raise ValueError(f"{label}: mayor que 0.")
    return number


def set_field(field: str, value: object) -> dict[str, Any]:
    """Write one typed value to the local layer; a blank value removes the line.

    Args:
        field: A row's `id` from `read()`.
        value: What the box held.

    Returns:
        `{id, value, where}`. Raises ValueError (Spanish) for an unknown field or a value out of range.
    """
    found = next((f for f in FIELDS if ".".join(f[:3]) == field), None)
    if found is None:
        raise ValueError(f"{field} no es una entrada que esta zona escriba.")
    module, section, key, kind, options, label = found[:6]
    path = study_config.LAYER
    doc = (assetyaml.read(path) if path.exists() else None) or {}
    mod = doc.setdefault(module, {})
    if str(value).strip() == "":
        mod.get(section, {}).pop(key, None)
        if section in mod and not mod[section]:
            del mod[section]
        new = None
    else:
        new = _coerce(kind, options, label, value)
        base = _base(module, section, key)
        if isinstance(base, float) and isinstance(new, int):
            new = float(new)
        if (
            isinstance(base, int)
            and not isinstance(base, bool)
            and isinstance(new, float)
            and new.is_integer()
        ):
            new = int(new)
        if base is not None and type(new) is not type(base):
            raise ValueError(f"{label}: no es del tipo que el fichero espera.")
        mod.setdefault(section, {})[key] = new
    doc[module] = mod
    assetyaml.write(path, doc)
    if not path.read_text(encoding="utf-8").startswith(
        HEADER
    ):  # a new file has no header yet
        path.write_text(HEADER + path.read_text(encoding="utf-8"), encoding="utf-8")
    return {
        "id": field,
        "value": new,
        "where": f"config/owner.yaml ({date.today().isoformat()})",
    }
