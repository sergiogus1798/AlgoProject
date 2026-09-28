"""A study result drawn as a self-contained HTML page, from the result dict and nothing else."""

from html import escape
from pathlib import Path

from core.study.render import figures, grids, tables

TEMPLATE = Path(__file__).with_name("page.html")
DRAW = {"distribution": figures.distribution, "cone": figures.cone, "lines": figures.lines,
        "bars": figures.bars, "grid": grids.grid, "scatter": grids.scatter,
        "table": tables.table, "verdict": tables.verdict}


def shell(title: str, sections: list[str]) -> str:
    """Put assembled sections inside the page shell.

    Args:
        title: Browser title.
        sections: HTML blocks, in reading order.

    Returns:
        A page with no scripts, no fonts and no network: it has to open from a USB stick in
        five years.
    """
    return (TEMPLATE.read_text(encoding="utf-8")
            .replace("__TITLE__", escape(title)).replace("__BODY__", "\n".join(sections)))


def block(b: dict) -> str:
    """One block, drawn by its kind; a block from a selector combination says which, and a
    grid's marked cell and shared colour extent are written under it."""
    where = b.get("select")
    head = ("<p class='select'>" + " · ".join(f"{escape(k)}: {escape(str(v))}"
                                             for k, v in where.items()) + "</p>") if where else ""
    foot = []
    if b["kind"] == "grid" and b.get("mark"):
        m = b["mark"]
        foot.append(f"{escape(m['label'])}: fila {escape(m['row'])}, columna {escape(m['col'])}")
    if b["kind"] == "grid" and b.get("scale_range"):
        foot.append("escala común a varias rejillas: {} a {}".format(*b["scale_range"]))
    tail = f"<p class='select'>{' · '.join(foot)}</p>" if foot else ""
    return head + DRAW[b["kind"]](b) + tail


def shown(tab: dict) -> list[dict]:
    """The blocks a static page draws: under selectors, only the default combination.

    Args:
        tab: One tab of a result.

    Returns:
        Its blocks, or, when it has selectors, those whose "select" agrees with every
        default. The window redraws any other combination from the same result; a page that
        drew all of them was 1.9 MB per strategy, three times the old report.
    """
    defaults = {s["key"]: s["default"] for s in tab["selectors"]}
    return [b for b in tab["blocks"]
            if all(defaults.get(k) == v for k, v in b.get("select", {}).items())]


def body(result: dict, level: int = 2) -> list[str]:
    """Every part of one result, in reading order: verdict, warnings, tabs, glossary.

    Args:
        result: A validated study result.
        level: Heading level for the tabs, 2 on its own page and 3 inside a batch page.

    Returns:
        HTML sections.
    """
    out = [tables.verdict(result["verdict"])] if result["verdict"] else []
    out += [f'<div class="warn st-{w["state"]}"><b>{escape(w["code"])}</b> '
            f'{escape(w["text"])}</div>' for w in result["warnings"]]
    for tab in result["tabs"]:
        out.append(f'<h{level} id="{escape(tab["name"])}">{escape(tab["title"])}</h{level}>')
        if tab["note"]:
            out.append(f'<p class="lede">{escape(tab["note"])}</p>')
        if tab["selectors"]:
            out.append('<p class="lede">Aquí se ve la combinación por defecto de '
                       + ", ".join(f"{escape(s['label'])} ({escape(str(s['default']))})"
                                   for s in tab["selectors"])
                       + ". Las demás están en el resultado JSON y en la ventana.</p>")
        out += [block(b) for b in shown(tab)]
    if result["glossary"]:
        out.append(f"<h{level}>Glosario</h{level}><dl class='glossary'>"
                   + "".join(f"<dt>{escape(g['term'])}</dt><dd>{escape(g['text'])}</dd>"
                             for g in result["glossary"]) + "</dl>")
    return out


def page(result: dict, title: str, lede: str = "") -> str:
    """One strategy's (or one population's) result as a whole page.

    Args:
        result: A validated study result.
        title: The page's heading.
        lede: One paragraph under it.

    Returns:
        The HTML, with a tab index at the top and the provenance in the footer.
    """
    nav = "".join(f'<a href="#{escape(t["name"])}">{escape(t["title"])}</a>'
                  for t in result["tabs"])
    head = [f"<h1>{escape(title)}</h1>"] + ([f'<p class="lede">{escape(lede)}</p>']
                                            if lede else [])
    foot = (f"<footer>{escape(result['module'])} · configuración {result['config_hash']} · "
            f"{result['computed_at']} · {result['wall_s']} s</footer>")
    return shell(title, head + [f'<nav class="tabs">{nav}</nav>'] + body(result) + [foot])
