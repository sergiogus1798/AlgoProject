#!/usr/bin/env python3
"""Read every installed skill and rewrite docs/SKILLS.md: what exists, what it costs, where."""

import re
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "SKILLS.md"
MARK = "<!-- generado por tools/skillmap.py — no editar debajo de esta linea -->"
SCOPES = {"proyecto": ROOT / ".claude" / "skills",
          "global": Path.home() / ".claude" / "skills"}


def front_matter(skill: Path) -> dict[str, str]:
    """The name and description a skill declares.

    Args:
        skill: Path of a SKILL.md.

    Returns:
        Its frontmatter fields. Only name and description are read: they are the only two
        the harness itself uses, and the description is what routes a request here.
    """
    head = skill.read_text(encoding="utf-8").split("---")[1]
    return {m.group(1): m.group(2).strip()
            for m in re.finditer(r"^(\w+):\s*(.+?)(?=\n\w+:|\Z)", head, re.S | re.M)}


def skills(scope: Path) -> list[dict]:
    """Every skill under one skills directory.

    Args:
        scope: A .claude/skills folder.

    Returns:
        One row per skill: name, description, the whole folder's size in bytes, an
        approximate token cost of the body, and the date it last changed. Size is the
        folder and not just SKILL.md, because a skill's reference files are part of what
        it can pull into context.
    """
    if not scope.exists():
        return []
    rows = []
    for md in sorted(scope.glob("*/SKILL.md")):
        fm = front_matter(md)
        files = [f for f in md.parent.rglob("*") if f.is_file()]
        rows.append({"name": fm.get("name", md.parent.name),
                     "description": fm.get("description", "").replace("\n", " "),
                     "body": md.stat().st_size,
                     "folder": sum(f.stat().st_size for f in files),
                     "files": len(files),
                     "changed": datetime.fromtimestamp(max(f.stat().st_mtime for f in files))})
    return rows


def table(rows: list[dict]) -> str:
    """One scope's skills as a Markdown table.

    Args:
        rows: Output of skills().

    Returns:
        The table, heaviest first — the cost of a skill is what makes it worth
        questioning, so the ones worth auditing sort to the top.
    """
    out = ["| skill | ~tokens al invocar | ficheros | último cambio | para qué |",
           "|---|---:|---:|---|---|"]
    for r in sorted(rows, key=lambda r: -r["body"]):
        purpose = r["description"].split(". Use when")[0].split(" Use when")[0]
        out.append(f"| `{r['name']}` | {r['body'] // 4:,} | {r['files']} | "
                   f"{r['changed']:%Y-%m-%d} | {purpose} |")
    return "\n".join(out)


def main() -> None:
    """Rewrite the generated half of docs/SKILLS.md, keeping whatever is above the marker."""
    kept = OUT.read_text(encoding="utf-8").split(MARK)[0] if OUT.exists() else ""
    parts = [kept.rstrip(), "", MARK, "", f"Regenerado {date.today().isoformat()} con "
             "`python3 tools/skillmap.py`. El coste en tokens es el cuerpo del `SKILL.md`, "
             "que solo se carga al invocarla; la descripcion (~90 tokens) esta siempre en "
             "contexto.", ""]
    for scope, path in SCOPES.items():
        rows = skills(path)
        parts += [f"## Skills de {scope} — `{path}`", "",
                  table(rows) if rows else "_ninguna_", ""]
        if rows:
            parts += [f"{len(rows)} skills, {sum(r['body'] for r in rows) // 4:,} tokens "
                      f"de cuerpo en total, {sum(r['folder'] for r in rows) // 1024:,} KB en disco.",
                      ""]
    OUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"{OUT.relative_to(ROOT)}: "
          + ", ".join(f"{len(skills(p))} de {s}" for s, p in SCOPES.items()))


if __name__ == "__main__":
    main()
