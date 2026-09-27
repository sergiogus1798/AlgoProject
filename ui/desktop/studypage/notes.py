"""What the page says about a study around its result: its role, where it was looked for, what was passed over."""

from ui.desktop.blocks.states import colour
from ui.desktop.theme import T

FAMILY = {"screening": "Cribado", "transfer": "Transferencia", "breakage": "Rotura",
          "optimisation": "Optimización", "closing": "Cierre", "readings": "Lecturas",
          "data": "Datos"}


# ⛔ and 👁 are in no font installed here (fc-list, 2026-09-26): they drew as empty boxes.
def headline(entry: dict) -> str:
    """The line under the study tabs: title, step, whether it eliminates, what it runs over.

    Args:
        entry: The study's catalogue entry.

    Returns:
        Rich text.
    """
    role = (f'<b style="color:{colour("fail")}">⊘ elimina</b> — su verdict.csv quita '
            f"estrategias vía /curate" if entry["role"] == "gate" else
            f'<b style="color:{colour("info")}">◉ describe</b> — no quita a nadie')
    step = f"paso {entry['step']}" if entry["step"] else "fuera de la secuencia"
    scope = " y ".join(s for s, ok in (("una estrategia", entry["one"]),
                                       ("la población", entry["many"])) if ok) or "—"
    # `one`/`many` are the runner's scopes when the study runs from here (catalogue.entry).
    verb = "se corre sobre" if entry["runnable"] else "juzga"
    return (f'<span style="font-size:17px; font-weight:700">{entry["title"]}</span>'
            f' <span style="color:{T["faint"]}">{entry["key"]}</span> · {step} · {role}'
            f" · {verb} {scope}")


def context(where: dict, strategy_page: bool) -> str:
    """The breadcrumb: project › databank › strategy (identity).

    Args:
        where: project, databank, strategy, identity, asset.
        strategy_page: False on the population page.

    Returns:
        Rich text.
    """
    tail = ""
    if strategy_page:
        who = where.get("strategy") or "— ninguna estrategia elegida —"
        ident = where.get("identity") or ""
        tail = f" › <b>{who}</b>" + (f' <span style="color:{T["faint"]}">({ident[:12]})</span>'
                                    if ident else "")
    else:
        tail = " › <b>población</b>"
    return (f"{where.get('project') or '—'} › {where.get('databank') or '—'}{tail}"
            f' <span style="color:{T["faint"]}">· activo {where.get("asset") or "?"}</span>')


def absent(entry: dict, strategy_page: bool) -> str:
    """Why there is no result on screen, in the study's own terms.

    Args:
        entry: The study's catalogue entry.
        strategy_page: False on the population page.

    Returns:
        One Spanish sentence.
    """
    if entry["source"] == "batch":
        return ("Este estudio escribe en el lote de variantes de la madre (estudios/), no en "
                "reports/: se lee desde el lote de variantes — aún no conectado.")
    if strategy_page and not entry["one"] and entry["many"]:
        return ("Este estudio juzga la población y no dejó ficha de esta estrategia aquí: "
                "su resultado está en la página de Población.")
    return ("Sin resultado de este estudio en este databank. No se toma el de otro databank: "
            "allí una estrategia con el mismo nombre tiene otra identidad.")


def skipped(rows: list[dict]) -> str:
    """The newer runs passed over before the one shown, with their reasons.

    Args:
        rows: `meta.skipped`, `[{day, reason}]`.

    Returns:
        Rich text, "" when none was passed over.
    """
    if not rows:
        return ""
    body = "<br>".join(f"{r['day']}: {r['reason']}" for r in rows)
    return (f'<span style="color:{colour("watch")}"><b>Corridas más nuevas que no se '
            f"muestran:</b><br>{body}</span>")


def shown(day: str, chosen: bool, strategy_page: bool) -> str:
    """Which run is on screen and why that one.

    Args:
        day: Its day.
        chosen: True when picked in the history, False when it is the newest.
        strategy_page: False on the population page.

    Returns:
        One Spanish sentence.
    """
    if chosen:
        return f"Corrida del {day}, elegida en el historial."
    whose = "de esta estrategia (por identidad)" if strategy_page else "de la población"
    return f"Corrida del {day}: la más nueva {whose} en este databank."
