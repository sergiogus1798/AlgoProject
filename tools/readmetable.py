"""Generate the «file» and «what it does» columns of every code folder's README table from the modules' docstrings."""
import ast
import re
from pathlib import Path

import depmap

ROOT = depmap.ROOT
CELL = re.compile(r"(?<!\\)\|")
PY_ROW = re.compile(r"^\|\s*`(\w+\.py)`\s*\|")


def first_line(py: Path) -> str:
    """The first paragraph of a module's docstring on one line, escaped for a markdown table cell.

    Args:
        py: A Python file.

    Returns:
        The line with `|` escaped; «—» when the module has no docstring.
    """
    doc = ast.get_docstring(ast.parse(py.read_text(encoding="utf-8")))
    line = " ".join((doc or "").strip().split("\n\n")[0].split())     # a sentence may wrap onto line 2
    return line.replace("|", "\\|") or "—"


def render(readme: Path) -> str:
    """The README text with its file table regenerated from the folder's modules.

    The table is the one whose header is `| file | what ...`. Its `.py` rows are rewritten in sorted
    order: «what it does» from the docstring's first paragraph, every other column kept byte for byte (a new row gets
    `—`); a row whose file is gone disappears. Any other row (subfolder, data file, nested path) keeps
    its text and follows the `.py` rows in its own order. Nothing outside the table changes.

    Args:
        readme: A folder's README.md.

    Returns:
        The new text; equal to the old one when the table is already right.
    """
    lines = readme.read_text(encoding="utf-8").split("\n")
    head = next((i for i, ln in enumerate(lines)
                 if re.match(r"^\|\s*file\s*\|\s*what", ln)), None)
    if head is None:
        return "\n".join(lines)
    end = head + 2
    while end < len(lines) and lines[end].startswith("|"):
        end += 1
    hand_n = len(CELL.split(lines[head].strip()[1:-1])) - 2     # columns after «what it does»
    old, others = {}, []
    for ln in lines[head + 2:end]:
        m = PY_ROW.match(ln)
        if m:
            cells = CELL.split(ln.strip()[1:-1])
            old[m.group(1)] = cells[len(cells) - hand_n:]      # the hand columns, from the right
        else:
            others.append(ln)
    rows = []
    for f in sorted(readme.parent.glob("*.py")):
        hand = old.get(f.name, [" — "] * hand_n)
        rows.append("|".join(["", f" `{f.name}` ", f" {first_line(f)} ", *hand]) + "|")
    return "\n".join(lines[:head + 2] + rows + others + lines[end:])


def readmes(files: list[Path]) -> list[Path]:
    """The README.md of every folder with Python files (a folder documented by SKILL.md is skipped).

    Args:
        files: Project Python files.

    Returns:
        Existing README paths.
    """
    return [r for r in (d / "README.md" for d in sorted({f.parent for f in files}))
            if r.exists() and not (r.parent / "SKILL.md").exists()]


def stale(files: list[Path]) -> list[str]:
    """README tables that differ from what the docstrings say.

    Args:
        files: Project Python files.

    Returns:
        One message per README whose text is not `render(readme)`.
    """
    return [f"{r.relative_to(ROOT)}: stale table, run tools/readmetable.py"
            for r in readmes(files) if r.read_text(encoding="utf-8") != render(r)]


def main() -> None:
    """Rewrite every stale code README in place."""
    for r in readmes(depmap.py_files()):
        new = render(r)
        if new != r.read_text(encoding="utf-8"):
            r.write_text(new, encoding="utf-8")


if __name__ == "__main__":
    main()
