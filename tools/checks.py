#!/usr/bin/env python3
"""Verify every mechanical rule in CODESTYLE.md and list what breaks them."""

import ast
import re
import sys
from pathlib import Path

import depmap

ROOT = depmap.ROOT
MAX_LINES = 250
PATHS_MODULE = ROOT / "core" / "paths.py"
ABSOLUTE = re.compile(r"""["'](?:/home/|/root/|~/)""")
PIP_NAME = {"yaml": "PyYAML", "sklearn": "scikit-learn", "PIL": "Pillow"}


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
        files: Project Python files.

    Returns:
        One message per offending line.
    """
    out = []
    for f in files:
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
              for line in req.read_text().splitlines()
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


def main() -> None:
    """Run every check and exit non-zero if anything fails."""
    files = depmap.py_files()
    checks = [("file length", too_long), ("documentation", undocumented),
              ("hardcoded paths", hardcoded_paths), ("requirements", missing_requirements),
              ("folder READMEs", unlisted_in_readme), ("dependency map", stale_depmap)]
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
