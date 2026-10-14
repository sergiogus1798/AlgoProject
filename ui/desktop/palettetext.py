"""The line under the palette bar: what the open palette is, and whether it does anything."""

from ui.desktop import names
from ui.desktop.theme import C, chip


def describe(p: dict, s: dict, blocks: int) -> str:
    """The line under the bar saying what the open palette is, and whether it does anything.

    Args:
        p: The open palette.
        s: Its summary.
        blocks: How many blocks the palette lists.

    Returns:
        Rich text. A palette whose every decision still comes from the unlabelled
        default is doing nothing, and saying so is the difference between a view that
        looks broken and one that is honest about being empty.
    """
    bits = [chip(names.family(p["family"]), C["accent"]), chip(p["origin"], C["muted"])]
    if p["based_on"]:
        bits.append(chip(f"de {p['based_on']}", C["muted"]))
    head = " ".join(bits) + f'  <span style="color:{C["muted"]}">{p["note"]}</span>'
    if not s["conditions_ok"]:
        head += (
            f'<br><span style="color:{C["dead"]}">⚠️ {s["signal"]["on"]} condiciones: '
            "fuera del 90–170 que pide el dueño. "
            + (
                "Faltan bloques por elegir."
                if s["signal"]["on"] < 90
                else "Sobran: esta paleta no está estrechando lo suficiente."
            )
            + "</span>"
        )
    if s["overridden"] == 0 and s["unlabelled"] == blocks:
        head += (
            f'<br><span style="color:{C["weak"]}">⚠️ Esta paleta no elige nada '
            f"todavía: sus {s['unlabelled']} bloques salen del valor por defecto, "
            "así que deja pasar todo el vocabulario. Elige bloques en la columna "
            "Peso, o etiqueta la familia en taxonomy.yaml.</span>"
        )
    return head
