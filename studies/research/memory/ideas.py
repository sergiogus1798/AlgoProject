"""The ideas index: every idea the ideaExpert proposed, chosen or not, and what finding it cost."""

import re

from core.researchpaths import ideas_dir
from studies.research.memory import sources

COLUMNS = ["idea", "symbol", "timeframe", "direction", "date", "rank", "hypotheses_measured",
           "origin", "from_book", "chosen", "attempts", "file"]
HEADING = re.compile(r"^### Idea (\d+)[^—\n]*— `(\w+)` · (M15|M30|H1|H4|D1)\b(.*)$", re.M)
HYPOTHESES = re.compile(r"Hip[oó]tesis medidas:?\s*\**\s*(\d+)")
ORIGIN = re.compile(r"^\W*Origen:?\W*\s*(.+)$", re.M | re.I)


def direction(tail: str) -> str:
    """'short' or 'long' from the rest of an idea's heading, '' when it says neither."""
    return "short" if "corto" in tail else "long" if "largo" in tail else ""


def parse(text: str, symbol: str, name: str) -> list[dict]:
    """The ideas of one ideaExpert file.

    Args:
        text: The file's markdown.
        symbol: Folder it lives in.
        name: File name, `<date>-<slug>.md`.

    Returns:
        One row per `### Idea N — `name` · TF · direction` heading. `hypotheses_measured` is
        the file's own count (its «Hipótesis medidas: N» line, shared by its ideas) or ''.
        `origin` is the text of an `Origen:` line inside the idea's section, '' when the file
        gives none; `from_book` is yes/no only when that line exists, else unknown — a book idea
        carries its author's trials, so unknown is not a no.
    """
    counted = HYPOTHESES.search(text)
    marks = list(HEADING.finditer(text))
    rows = []
    for i, m in enumerate(marks):
        section = text[m.end():marks[i + 1].start() if i + 1 < len(marks) else len(text)]
        origin = ORIGIN.search(section)
        rows.append({"idea": m[2], "symbol": symbol, "timeframe": m[3],
                     "direction": direction(m[4]), "date": name[:10], "rank": int(m[1]),
                     "hypotheses_measured": int(counted[1]) if counted else "",
                     "origin": origin[1].strip() if origin else "",
                     "from_book": ("yes" if "libro" in origin[1].lower() else "no")
                     if origin else "unknown", "file": f"{symbol}/{name}"})
    return rows


def index(attempts: list[dict] = ()) -> list[dict]:
    """Every idea ever proposed, oldest first, with whether a template of that name exists.

    Args:
        attempts: The attempts table; `chosen` is yes when a template carries the idea's name,
            and `attempts` counts the projects it was run in.
    """
    made = sources.templates()
    rows = []
    for path in sorted(ideas_dir().glob("*/*.md")):
        rows += parse(path.read_text(encoding="utf-8"), path.parent.name, path.name)
    for r in rows:
        r["chosen"] = "yes" if r["idea"] in made else "no"
        r["attempts"] = sum(a["template"] == r["idea"] for a in attempts)
    return sorted(rows, key=lambda r: (r["date"], r["rank"]))
