"""A study result written as Markdown, for the .md report and for reading in a terminal."""

from core.study.render.page import shown
from core.study.render.svg import num


def _table(columns: list[str], rows: list[list]) -> list[str]:
    """A Markdown table; cells through the same number format as the page."""
    def cell(v: object) -> str:
        """One cell."""
        if isinstance(v, bool):
            return "sí" if v else "no"
        if isinstance(v, (int, float)) or v is None:
            return num(v)
        return str(v).replace("|", "/")

    return (["| " + " | ".join(columns) + " |", "|" + "---|" * len(columns)]
            + ["| " + " | ".join(cell(v) for v in r) + " |" for r in rows])


def block(b: dict) -> list[str]:
    """One block as Markdown lines: tables and bars in full, the drawings by their numbers."""
    title = b.get("title") or b.get("label", "")
    where = b.get("select")
    head = [f"**{title}**" + (" — " + ", ".join(f"{k} {v}" for k, v in where.items())
                              if where else ""), ""]
    kind = b["kind"]
    if kind == "table":
        body = _table(b["columns"], b["rows"])
    elif kind == "bars":
        body = _table(["", "valor", "estado"],
                      [[i["label"], i["value"], i.get("state", "")] for i in b["items"]])
    elif kind == "verdict":
        head = []
        body = [f"**{b['label']}**" + ("" if b["score"] is None else f" ({num(b['score'])})")
                + f" — {b['meaning']}", ""]
        body += [f"- {p['label']}: {num(p.get('value'))} {p.get('note', '')}" for p in b["parts"]]
    elif kind == "distribution" and b.get("series"):
        body = _table(["muestra", "n", "mediana", "real"],
                      [[s["label"], s["n"], s["median"], s.get("real")] for s in b["series"]])
        if b.get("shift"):
            p = "—" if b["shift"]["ks_p"] is None else f"{b['shift']['ks_p']:.4f}"
            body += ["", f"desplazamiento de la mediana ({b['series'][-1]['label']} − "
                         f"{b['series'][0]['label']}) {num(b['shift']['median'])} · KS p {p}"]
    elif kind == "distribution":
        p = "" if b["p"] is None else f" · p {b['p']:.4f}"
        body = [f"real {num(b['real'])} · mediana {num(b['median'])} · banda "
                f"{num(b['band'][0])} a {num(b['band'][1])}{p}"]
    elif kind == "grid":
        m = b.get("mark") or {}
        body = _table([""] + [str(c) for c in b["cols"]],
                      [[r] + [f"**[{num(x)}]**" if (r, c) == (m.get("row"), m.get("col"))
                              else x for c, x in zip(b["cols"], v)]
                       for r, v in zip(b["rows"], b["values"])])
        if m:
            body += ["", f"{m['label']}: fila {m['row']}, columna {m['col']} (entre corchetes)"]
        if b.get("scale_range"):
            body += ["", "escala común a varias rejillas: {} a {}".format(
                *(num(v) for v in b["scale_range"]))]
    elif kind == "callout":
        head = []
        body = [f"> **{b['text']}**", ""]
    elif kind == "list":
        body = [f"- **{i['title']}** — {i['text']}" for i in b["items"]]
    else:
        body = [f"({kind}: se ve en la página HTML)"]
    note = [b["note"]] if b.get("note") else []
    return head + body + [""] + note + ([""] if note else [])


def render(result: dict, title: str) -> str:
    """The whole result, tab by tab.

    Args:
        result: A validated study result.
        title: The document's heading.

    Returns:
        Markdown text.
    """
    out = [f"# {title}", ""]
    if result["verdict"]:
        out += block(result["verdict"])
    out += [f"- ⚠️ **{w['code']}** {w['text']}" for w in result["warnings"]]
    for tab in result["tabs"]:
        out += ["", f"## {tab['title']}", ""] + ([tab["note"], ""] if tab["note"] else [])
        if tab["selectors"]:
            out += ["Combinación por defecto: " + ", ".join(
                f"{s['label']} {s['default']}" for s in tab["selectors"]) + ".", ""]
        for b in shown(tab):
            out += block(b)
    out += ["", f"_{result['module']} · configuración {result['config_hash']} · "
                f"{result['computed_at']}_", ""]
    return "\n".join(out)
