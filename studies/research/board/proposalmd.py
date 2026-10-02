"""A proposal as the Markdown the owner reads."""


def idea(n: int, i: dict) -> list[str]:
    """One idea's section."""
    families = [f"| {f['family']} | {f['weight']} | {f['reason']} |"
                for f in i["palette"].get("families", [])]
    blocks = ", ".join(f"{k} ({w})" for k, w in i["palette"].get("blocks", {}).items())
    custom = [f"- `{b['name']}`: {b['what']}" for b in i["custom_blocks"]] or ["- ninguno"]
    questions = []
    for q in i["questions"]:
        questions += [f"- **{q['question']}**"] + [f"  - {r}" for r in q["readings"]] \
            + [f"  - Respuesta: {q['answer']}" if q.get("answer") else
               "  - SIN CONTESTAR: esta idea no se lanza hasta que contestes."]
    quarry = i["quarry"] + (f" ({i['source']})" if i.get("source") else "")
    return [f"## Idea {n}: {i['name']}" + (" — VETADA" if i.get("vetoed") else ""), "",
            f"**Regla exacta.** {i['rule']}", "", f"**Mecanismo.** {i['mechanism']}", "",
            f"**Dirección.** {i['direction']} · **Cantera.** {quarry} · "
            f"**Custodio.** unas {i['custodian_hours']} h", "",
            f"**El hueco libre.** {i['palette'].get('role', '')}", "",
            "| familia de bloques | peso | por qué |", "|---|---|---|", *families, "",
            f"Bloques: {blocks or 'los de esas familias, sin excepciones'}", "",
            "**Bloques custom a crear.**", *custom, "",
            f"**Cómo puede fallar.** {i['failure']}", "",
            *(["**Preguntas abiertas (regla 11).**", *questions, ""] if questions else [])]


def text(p: dict) -> str:
    """The whole proposal: diagnosis, the three ideas, and what the owner must know first.

    Args:
        p: A stamped proposal (`proposal.stamp`).
    """
    c, b = p["cell"], p["board"]
    measures = [f"| {m['measure']} | {m['reading']} | {m['explanation']} |" for m in p["measures"]]
    warn = (["> **Costes provisionales.** Los costes de este activo siguen sin cerrar: el filtro "
             "«paga el doble del coste» se ha medido contra un coste que puede cambiar.", ""]
            if p["provisional_costs"] else [])
    lines = [
        f"# Propuesta de investigación · {c['symbol']} {c['timeframe']} {c['direction']} · "
        f"{c['family']}", "", f"*{p['created']} · id `{p['id']}`*", "",
        "## Diagnóstico", "", p["diagnosis"], "",
        f"En el tablero: puesto {b['rank']}, {b['points']} puntos (prior {b.get('prior') or 'ninguna'}, "
        f"entra por {'+'.join(b.get('entered_by', ['desnudo']))}, señal {b['multiple']}x el coste, "
        f"{b['attempts']} intentos previos, "
        f"{'sin medir' if b['trades_per_year'] is None else b['trades_per_year']} op/año).",
        *(["**Aviso: lo medido en esta celda va en contra de la prior («medido en contra»).**"]
          if b.get("evidence") == "against" else []),
        *([f"**Se aparta del orden del tablero:** {p['departs']}"] if p.get("departs") else []),
        "", "| medida | lectura | qué quiere decir |", "|---|---|---|", *measures, "", *warn,
        "## Antes de lanzar", "",
        f"- En {c['symbol']} {c['timeframe']} {c['direction']} ya van **{p['ideas_spent']} ideas** "
        "antes de estas tres.", *[f"- {s}" for s in p["standing_costs"]], ""]
    for n, i in enumerate(p["ideas"], 1):
        lines += idea(n, i)
    return "\n".join(lines) + "\n"
