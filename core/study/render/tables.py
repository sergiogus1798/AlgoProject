"""The two blocks that are not drawings: the table and the verdict with its meaning."""

from html import escape

from core.study.render import svg


def _cell(v: object) -> str:
    """One cell as text: numbers through svg.num, the rest escaped."""
    if isinstance(v, bool):
        return "sí" if v else "no"
    if isinstance(v, (int, float)) or v is None:
        return svg.num(v)
    return escape(str(v))


def table(b: dict) -> str:
    """A scrollable table with its title above and its note below."""
    cls = ['' if a == "left" else ' class="n"' for a in b["align"]]
    head = "".join(f"<th{c}>{escape(h)}</th>" for h, c in zip(b["columns"], cls))
    body = "".join("<tr>" + "".join(f"<td{c}>{_cell(v)}</td>" for v, c in zip(r, cls))
                   + "</tr>" for r in b["rows"])
    note = f'<p class="lede">{escape(b["note"])}</p>' if b["note"] else ""
    return (f'<h3>{escape(b["title"])}</h3><div class="scroll"><table><tr>{head}</tr>{body}'
            f"</table></div>{note}")


def callout(b: dict) -> str:
    """One sentence the study wants seen, not read past — a coloured banner."""
    return f'<div class="verdict st-{b.get("state") or "info"}"><p>{escape(b["text"])}</p></div>'


def lst(b: dict) -> str:
    """Title in bold, a short description under it, one item after another."""
    items = "".join(f'<li><b>{escape(i["title"])}</b> — {escape(i["text"])}</li>'
                    for i in b["items"])
    title = f'<h3>{escape(b["title"])}</h3>' if b.get("title") else ""
    note = f'<p class="lede">{escape(b["note"])}</p>' if b.get("note") else ""
    return f"{title}{note}<ul>{items}</ul>"


def verdict(b: dict) -> str:
    """The call, its score, the sentence that explains it, and the parts that made it."""
    score = "" if b["score"] is None else f' <span class="score">{svg.num(b["score"])}</span>'
    parts = "".join(f'<li class="st-{p["state"]}"><b>{escape(p["label"])}</b> '
                    f'{svg.num(p.get("value")) if p.get("value") is not None else ""} '
                    f'<span>{escape(p.get("note", ""))}</span></li>' for p in b["parts"])
    return (f'<div class="verdict st-{b["state"]}"><div class="call">{escape(b["label"])}'
            f'{score}</div><p>{escape(b["meaning"])}</p>'
            f'{"<ul>" + parts + "</ul>" if parts else ""}</div>')
