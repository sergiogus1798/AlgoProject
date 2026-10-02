"""The board as one page of Spanish text: what the director and the owner read."""

HEAD = ("#", "celda", "puntos", "prior", "evidencia", "señal", "hueco", "pasado", "freno",
        "op/año", "entra por", "avisos")
SEEN = {"naked": "pasa desnuda", "plateau": "barrido en meseta", "weak": "significativa, <2x",
        "none": "sin evidencia", "against": "MEDIDO EN CONTRA"}


def marks(cell: dict) -> str:
    """The warnings of one cell: measured against, a pullback idea, provisional costs; or none."""
    said = [text for text, on in (("«medido en contra»", cell["evidence"] == "against"),
                                  ("pullback: contexto de tendencia + disparo de reversión",
                                   cell["pullback"]),
                                  ("costes provisionales", cell["provisional_costs"])) if on]
    return "; ".join(said) or "-"


def row(cell: dict) -> tuple:
    """One cell as the page's columns: each factor's raw value and, in brackets, its 0-1."""
    f, p = cell["factors"], cell["past"]
    paid = f"{cell['multiple']:.1f}x coste" if cell["trades_per_year"] is not None else "sin medir"
    return (str(cell["rank"]),
            f"{cell['symbol']} {cell['timeframe']} {cell['direction']} {cell['family']}",
            f"{cell['points']:.1f}",
            f"{cell['prior'] or 'ninguna'} ({f['prior']:.2f})",
            f"{SEEN[cell['evidence']]} ({f['evidence']:.2f})"
            + (f" [{cell['variant']}]" if cell["variant"] else ""),
            f"{paid} ({f['signal']:.2f})",
            f"{cell['attempts']} intentos ({f['gap']:.2f})",
            f"{p['with_survivors']}/{p['closed']} cerradas, {p['rate']:.2f} "
            f"[{p['low']:.2f}-{p['high']:.2f}]",
            f"{cell['ideas_spent']} ideas (x{f['brake']:.2f})",
            f"{cell['trades_per_year']:.1f}" if cell["trades_per_year"] is not None else "sin medir",
            "+".join(cell["entered_by"]), marks(cell))


def text(board: dict) -> str:
    """The whole page.

    Args:
        board: `many.run`'s dict.

    Returns:
        Header, the first `rows` cells of the ordered table, and the legend that says how
        each column is computed.
    """
    w, e = board["weights"], board["evidence_values"]
    shown = board["cells"][:board["rows"]]
    rows = [HEAD] + [row(c) for c in shown]
    width = [max(len(r[i]) for r in rows) for i in range(len(HEAD))]
    table = ["  ".join(v.ljust(n) for v, n in zip(r, width)).rstrip() for r in rows]
    by = {k: sum(k in c["entered_by"] for c in board["cells"]) for k in ("prior", "desnudo", "barrido")}
    flat = (" Ninguna familia tiene corridas cerradas: el factor «pasado» es plano (0.50 en todas)."
            if not board["closed_runs"] else "")
    return "\n".join([
        f"TABLERO DE INVESTIGACIÓN · {board['generated']}",
        f"{len(board['cells'])} celdas-familia entran de {board['cell_families']} medidas "
        f"(las otras {board['gated_out']} no): {by['prior']} porque la prior las da por Alta, "
        f"{by['desnudo']} porque pasan los cuatro filtros del perfil, {by['barrido']} porque una "
        "variante del barrido pasa en meseta. Ninguna familia de reloj entra. "
        f"Se imprimen las {len(shown)} primeras; todas están en board.json.",
        "", *table, "",
        f"puntos = 100 × freno × ({w['prior']:.2f}·prior + {w['evidence']:.2f}·evidencia + "
        f"{w['signal']:.2f}·señal + {w['gap']:.2f}·hueco + {w['past']:.2f}·pasado); entre "
        f"paréntesis, cada factor de 0 a 1. «Medido en contra» multiplica además por "
        f"{board['against_brake']:.2f}.",
        "prior     lo que dice el documento de familias por activo del dueño para esa celda: Alta "
        "1, Media 0,5, ninguna o Baja 0. Donde la prior dice «(largo)», el corto no la lleva. "
        f"El «pullback» de la prior va bajo `{board['pullback_as']}`: disparo de reversión con "
        "contexto de tendencia en D1.",
        f"evidencia lo medido, graduado: pasa los cuatro filtros desnuda {e['naked']:.2f} > una "
        f"variante del barrido pasa en meseta {e['plateau']:.2f} > significativa y estable pero "
        f"paga menos de 2× {e['weak']:.2f} > sin evidencia {e['none']:.2f} > medido en contra "
        f"{e['against']:.2f}. La estadística suma sobre la prior; no es requisito para entrar.",
        f"señal     efecto medio por operación de lo que la admite (medida líder o variante del "
        f"barrido), en múltiplos del coste; {board['signal_cap']:.0f}x o más cuenta como 1. Una "
        "celda que entra sólo por la prior no tiene efecto medido: «sin medir».",
        "hueco     1/(1 + intentos de esa familia en esa celda): sin probar vale 1.",
        f"pasado    tasa de supervivencia de la familia en esa clase de activo, con su intervalo "
        f"del {board['interval']:.0%}; una familia sin probar no baja.{flat}",
        f"freno     1/(1 + ideas ya gastadas en la celda / {board['brake_half']}).",
        "op/año    operaciones al año de lo que la admite; «sin medir» si entra sólo por la prior "
        "(no se inventa una frecuencia).",
        "Una variante del barrido es una hipótesis elegida dentro de muestra, no un hallazgo."])
