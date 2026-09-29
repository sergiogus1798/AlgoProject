#!/usr/bin/env python3
"""Verify every mechanical rule in CODESTYLE.md and list what breaks them."""

import ast
import re
import shutil
import subprocess
import sys
from pathlib import Path

import depmap
import knowhowmap

ROOT = depmap.ROOT
MAX_LINES = 250
PATHS_MODULE = ROOT / "core" / "paths.py"
DEVELOPER_ONLY = {"tools", "tests"}
ABSOLUTE = re.compile(r"""["'](?:/home/|/root/|~/)""")
PIP_NAME = {"yaml": "PyYAML", "sklearn": "scikit-learn", "PIL": "Pillow",
            "ruamel": "ruamel.yaml"}


def too_long(files: list[Path]) -> list[str]:
    """Files above the 250-line limit.

    Args:
        files: Project Python files.

    Returns:
        One message per offending file.
    """
    out = []
    for f in files:
        n = len(f.read_text(encoding="utf-8").splitlines())
        if n > MAX_LINES:
            out.append(f"{f.relative_to(ROOT)}: {n} lines, split it (max {MAX_LINES})")
    return out


def undocumented(files: list[Path]) -> list[str]:
    """Missing module docstrings, function docstrings and type hints.

    Args:
        files: Project Python files.

    Returns:
        One message per offending definition.
    """
    out = []
    for f in files:
        rel = f.relative_to(ROOT)
        tree = ast.parse(f.read_text(encoding="utf-8"))
        if not ast.get_docstring(tree):
            out.append(f"{rel}: no module docstring")
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            where = f"{rel}:{node.lineno} {node.name}"
            if not ast.get_docstring(node):
                out.append(f"{where}: no docstring")
            if isinstance(node, ast.ClassDef):
                continue
            args = [a for a in node.args.args + node.args.kwonlyargs
                    if a.arg not in ("self", "cls")]
            if any(a.annotation is None for a in args):
                out.append(f"{where}: arguments without type hints")
            if node.returns is None:
                out.append(f"{where}: no return type hint")
    return out


def hardcoded_paths(files: list[Path]) -> list[str]:
    """Absolute or home-relative paths written outside core/paths.py.

    Args:
        files: Project Python files. bin/*.sh is checked alongside them: the shell
            scripts that drive SQX carried one machine's install paths for months
            unseen, because depmap.py_files() only yields .py.

    Returns:
        One message per offending line.
    """
    out = []
    for f in files + sorted((ROOT / "bin").glob("*.sh")):
        if f == PATHS_MODULE:
            continue
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if ABSOLUTE.search(line) and not line.lstrip().startswith("#"):
                out.append(f"{f.relative_to(ROOT)}:{i}: absolute path, use core.paths")
    return out


def missing_requirements(files: list[Path]) -> list[str]:
    """External imports absent from requirements.txt.

    Args:
        files: Project Python files.

    Returns:
        One message per missing library.
    """
    req = ROOT / "requirements.txt"
    listed = {re.split(r"[=<>!\[]", line, 1)[0].strip().lower()
              for line in req.read_text(encoding="utf-8").splitlines()
              if line.strip() and not line.startswith("#")}
    known = depmap.internal_names(files)
    used = set()
    for f in files:
        used |= {n for n in depmap.imports_of(f)
                 if n not in known and n not in depmap.STDLIB}
    return [f"requirements.txt: missing {PIP_NAME.get(n, n)} (imported as {n})"
            for n in sorted(used) if PIP_NAME.get(n, n).lower() not in listed]


def unlisted_in_readme(files: list[Path]) -> list[str]:
    """Python files their folder's README.md does not mention.

    Args:
        files: Project Python files.

    Returns:
        One message per missing README or unlisted file.
    """
    out = []
    for folder in sorted({f.parent for f in files}):
        readme = folder / "README.md"
        if not readme.exists():
            out.append(f"{folder.relative_to(ROOT)}/: no README.md")
            continue
        text = readme.read_text(encoding="utf-8")
        for f in sorted(folder.glob("*.py")):
            if f.name not in text:
                out.append(f"{folder.relative_to(ROOT)}/README.md: {f.name} not listed")
    return out


def no_manual_page(files: list[Path]) -> list[str]:
    """User-facing commands the manual neither documents nor lists as pending.

    Args:
        files: Project Python files.

    Returns:
        One message per command with no page. A command is any file with a __main__ block;
        tools/ and tests/ are developer-only and are deliberately outside the manual. A command
        may be named either by its path or by its dotted `python3 -m` form — the two are a
        bijection, so recognizing both does not weaken the check. The chapters live in
        MANUAL_SRC, out of the repo (the owner reads only the PDFs); on a machine without
        them there is nothing to check against, and the check says so instead of passing.
    """
    sys.path.insert(0, str(ROOT))
    from core.paths import MANUAL_SRC
    if not MANUAL_SRC.is_dir():
        return [f"{MANUAL_SRC}: the manual's sources are missing, commands not checked"]
    written = "".join(p.read_text(encoding="utf-8") for p in MANUAL_SRC.glob("*.md"))
    out = []
    for f in files:
        rel = f.relative_to(ROOT).as_posix()
        dotted = rel[:-3].replace("/", ".")
        if rel.split("/")[0] in DEVELOPER_ONLY or rel in written or dotted in written:
            continue
        if "__main__" in f.read_text(encoding="utf-8"):
            out.append(f"{rel}: no manual chapter — copy _PLANTILLA.md in {MANUAL_SRC}, "
                       f"add it to a family in tools/manual.py and rebuild the PDFs")
    return out


def lint_bugs(files: list[Path]) -> list[str]:
    """Real-bug findings from ruff.toml's rule set, over the whole project.

    Args:
        files: Project Python files, unused: ruff walks the tree itself.

    Returns:
        One message per finding; none when ruff is not installed.
    """
    if not shutil.which("ruff"):
        return []
    result = subprocess.run(
        ["ruff", "check", "--select", "F821,F811,F823,E9", "--no-cache",
         "--output-format", "concise", str(ROOT)],
        capture_output=True, text=True)
    return [line for line in result.stdout.splitlines()
            if line and "Found" not in line and "All checks passed" not in line]


def stale_depmap(files: list[Path]) -> list[str]:
    """Whether docs/DEPENDENCIES.md matches the code as it stands now.

    Args:
        files: Project Python files.

    Returns:
        A single message when the file is missing or out of date.
    """
    if not depmap.OUT.exists():
        return ["docs/DEPENDENCIES.md: missing, run tools/depmap.py"]
    if depmap.OUT.read_text(encoding="utf-8") != depmap.render(files):
        return ["docs/DEPENDENCIES.md: stale, run tools/depmap.py"]
    return []


def workflow_drift(files: list[Path]) -> list[str]:
    """Whether the window's rail and WORKFLOW.md's table name the same steps (plan 24, Q4).

    Args:
        files: Project Python files, unused: the two sources are fixed.

    Returns:
        One message per step whose number or title differs, in either direction. The rail
        stays a list in code (`ui/daemon/workflow/steps.py`, its `doc` field) so that a
        person editing the table cannot break the window; this check makes the drift loud.
    """
    table = ROOT / "docs" / "AgentPDFs" / "WORKFLOW.md"
    doc = re.findall(r"^\|\s*([0-9.]+)\s*\|\s*\*\*(.+?)\*\*", table.read_text(encoding="utf-8"),
                     re.M)
    tree = ast.parse((ROOT / "ui" / "daemon" / "workflow" / "steps.py").read_text(encoding="utf-8"))
    rows = next(ast.literal_eval(n.value) for n in tree.body
                if isinstance(n, ast.Assign) and n.targets[0].id == "S")
    code = [(r[0], r[2]) for r in rows]
    if [n for n, _ in doc] != [n for n, _ in code]:
        return [f"steps.py numbers {[n for n, _ in code]} != WORKFLOW.md {[n for n, _ in doc]}"]
    return [f"step {n}: steps.py says «{c}», WORKFLOW.md says «{d}»"
            for (n, d), (_, c) in zip(doc, code) if d != c]


def main() -> None:
    """Run every check and exit non-zero if anything fails."""
    files = depmap.py_files()
    checks = [("file length", too_long), ("documentation", undocumented),
              ("hardcoded paths", hardcoded_paths), ("requirements", missing_requirements),
              ("folder READMEs", unlisted_in_readme), ("manual pages", no_manual_page),
              ("lint", lint_bugs),
              ("dependency map", stale_depmap), ("knowhow cards", knowhowmap.bad_cards),
              ("knowhow links", knowhowmap.broken_links),
              ("knowhow indexes", knowhowmap.stale_indexes),
              ("workflow table", workflow_drift)]
    total = 0
    for name, check in checks:
        problems = check(files)
        total += len(problems)
        print(f"\n## {name}: {len(problems) or 'ok'}")
        for p in problems:
            print(f"  {p}")
    print(f"\n{len(files)} files checked, {total} problems")
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
