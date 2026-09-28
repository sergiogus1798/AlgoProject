"""What one archived version holds, in words: its studies by databank, what it left out, its provenance."""

from ui.text.numbers import num
from ui.desktop.theme import T

FAMILY = {"screening": "Cribado", "transfer": "Transferencia", "breakage": "Rotura",
          "optimisation": "Optimización", "closing": "Cierre", "readings": "Lecturas",
          "data": "Datos"}


def when(stamp: str) -> str:
    """`2026-09-27T20:39:17` → «2026-09-27 20:39»."""
    return stamp.replace("T", " ")[:16]


def trials(held: dict) -> str:
    """N as the list prints it: «—» when the ledger has searches but none scored candidates."""
    return "—" if held["n"] == 0 and held["searches"] > 0 else num(held["n"])


def ledger(held: dict) -> str:
    """The ledger count frozen that day, as one line."""
    sigma = f" · σ del Sharpe {num(held['sigma'])}" if held["sigma"] is not None else ""
    return (f"N = {trials(held)} candidatas puntuadas en todas las búsquedas del estudio · "
            f"{num(held['searches'])} filas del Ledger"
            f"{sigma} (estudio del Ledger {held['study']})")


def page(shown: dict) -> str:
    """The detail beside the list, as rich text.

    Args:
        shown: What `/api/archive/show` answered for one version.

    Returns:
        HTML for a QLabel: head facts, the studies held per databank, what was not
        archived and why, and the provenance. No identity, no file path.
    """
    dim = f'style="color:{T["faint"]}"'
    rows = [f"<b>{shown['strategy']}</b> · {shown['symbol']} {shown['timeframe'] or ''} · "
            f"paso {shown['step']} · versión {shown['version']}",
            f"<span {dim}>archivada el {when(shown['archived_at'])} · desde {shown['databank']} "
            f"· proyecto {shown['project']}</span>"]
    if shown["note"]:
        rows.append(f"«{shown['note']}»")
    rows += ["", "<b>Lo que trae</b> (se ve al importar, sin recalcular nada):"]
    for databank, studies in shown["held"].items():
        names = ", ".join(f"{s['title']} <span {dim}>({FAMILY.get(s['family'], s['family'])}"
                          f"{', paso ' + s['step'] if s['step'] else ''})</span>" for s in studies)
        rows.append(f"· {databank}: {names or '—'}")
    rows.append("· la ficha de backtest (IS/OOS, salidas), las dos curvas y los metadatos del .sqx")
    if shown["skipped"]:
        rows += ["", "<b>Lo que no se archivó</b> y por qué:"]
        rows += [f"· {s['path']}: <span {dim}>{s['reason']}</span>" for s in shown["skipped"]]
    elif shown["skipped"] is None:
        rows += ["", f"<span {dim}>Versión anterior a la lista de lo no archivado: no dice qué "
                     "dejó fuera.</span>"]
    rows += ["", "<b>Procedencia</b>", ledger(shown["ledger"]),
             f"ficha de costes de {shown['asset']['symbol']} congelada ese día · código "
             f"{shown['code_version']}",
             "el .sqx se copió de un export (no del install)" if shown["sqx"]["by_hand"]
             else "el .sqx se copió del databank del install"]
    return "<br>".join(rows)
