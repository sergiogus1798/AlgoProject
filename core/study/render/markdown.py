"""A study result written as Markdown, for the .md report and for reading in a terminal."""

from core.study.render.svg import num


def _table(columns: list[str], rows: list[list]) -> list[str]:
    """A Markdown table; cells through the same number format as the page."""
    def cell(v: object) -> str:
        """One cell."""
        return num(v) if isinstance(v, (int, float)) and not isinstance(v, bool) or v is None \
            else str(v).replace("|", "/")

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
    elif kind == "distribution":
        p = "" if b["p"] is None else f" · p {b['p']:.4f}"
        body = [f"real {num(b['real'])} · mediana {num(b['median'])} · banda "
                f"{num(b['band'][0])} a {num(b['band'][1])}{p}"]
    elif kind == "grid":
        body = _table([""] + [str(c) for c in b["cols"]],
                      [[r] + v for r, v in zip(b["rows"], b["values"])])
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
        for b in tab["blocks"]:
            out += block(b)
    out += ["", f"_{result['module']} · configuración {result['config_hash']} · "
                f"{result['computed_at']}_", ""]
    return "\n".join(out)
