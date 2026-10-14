#!/usr/bin/env python3
"""Generate docs/DEPENDENCIES.md from the imports actually present in the project's Python files."""

import ast
import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "DEPENDENCIES.md"
SKIP_DIRS = {".venv", "__pycache__", ".git", "scratch", "sqx-lab", "snapshots"}
STDLIB = sys.stdlib_module_names


def py_files() -> list[Path]:
    """Every project Python file worth mapping.

    Returns:
        Absolute paths, sorted, excluding vendored, scratch and cache directories.
    """
    return sorted(
        p for p in ROOT.rglob("*.py") if not SKIP_DIRS & set(p.relative_to(ROOT).parts)
    )


def internal_names(files: list[Path]) -> set[str]:
    """Top-level names an import can refer to inside this project.

    Args:
        files: Project Python files.

    Returns:
        Package directory names (any depth: a folder with no `__init__.py` is still imported
        relatively) plus every module stem, e.g. {"core", "plots"}.
    """
    names = {p.stem for p in files} | {p.parent.name for p in files}
    names |= {
        p.relative_to(ROOT).parts[0]
        for p in files
        if len(p.relative_to(ROOT).parts) > 1
    }
    return names


@lru_cache(maxsize=None)
def tree(path: Path) -> ast.Module:
    """The parsed file, once per process: depmap, checks and layering all read the same 1,500."""
    return ast.parse(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def nodes(path: Path) -> tuple[ast.AST, ...]:
    """Every node of the file's tree, walked once: the four checks that scan it share this."""
    return tuple(ast.walk(tree(path)))


def imports_of(path: Path) -> set[str]:
    """Top-level module names imported by one file.

    Args:
        path: A Python source file.

    Returns:
        First segment of every import, e.g. "numpy" for "import numpy.linalg".
        Relative imports are reported as the bare name they import.
    """
    found = set()
    for node in nodes(path):
        if isinstance(node, ast.Import):
            found |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module.split(".")[0])
    return found


def dotted_names(path: Path) -> set[str]:
    """Every dotted module name one file may be importing (`from a import b` gives `a` and `a.b`)."""
    pkg = list(path.relative_to(ROOT).parent.parts)
    out = set()
    for node in nodes(path):
        if isinstance(node, ast.Import):
            out |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            base = (
                ".".join(pkg[: len(pkg) - node.level + 1] + [node.module or ""]).strip(
                    "."
                )
                if node.level
                else node.module
            )
            out |= {base} | {f"{base}.{a.name}" if base else a.name for a in node.names}
    return out - {None, ""}


def file_graph() -> dict[Path, set[Path]]:
    """File-level import graph: each project file -> the project files it imports.

    `imports_of` stops at the first segment ("core"), too coarse to say which test a change reaches.
    This resolves the full dotted name (and `from pkg import mod`, relative imports, and a module
    imported by bare name after a sys.path insert) to the file, plus the `__init__.py` of its parents.

    Returns:
        {importer: {imported files}}, absolute paths, project files only.
    """
    files = py_files()
    by_dotted = {}
    for p in files:
        parts = list(p.relative_to(ROOT).with_suffix("").parts)
        by_dotted[".".join(parts[:-1] if parts[-1] == "__init__" else parts)] = p
    stems = [p.stem for p in files]
    by_stem = {p.stem: p for p in files if stems.count(p.stem) == 1}
    graph = {}
    for p in files:
        found = set()
        for dotted in dotted_names(p):
            head = dotted.split(".")[0]
            if head not in by_dotted and head in by_stem:
                dotted = ".".join(by_stem[head].relative_to(ROOT).with_suffix("").parts)
            parts = dotted.split(".")
            found |= {
                by_dotted[".".join(parts[:i])]
                for i in range(1, len(parts) + 1)
                if ".".join(parts[:i]) in by_dotted
            }
        graph[p] = found - {p}
    return graph


def summary(path: Path) -> str:
    """The module docstring's first line, or a marker when there is none.

    Args:
        path: A Python source file.

    Returns:
        One line of prose describing the module.
    """
    doc = ast.get_docstring(tree(path))
    return doc.splitlines()[0] if doc else "— no module docstring —"


def render(files: list[Path]) -> str:
    """Build the whole DEPENDENCIES.md text.

    Args:
        files: Project Python files.

    Returns:
        Markdown. Carries no timestamp, so regenerating an unchanged tree is a no-op.
    """
    known = internal_names(files)
    rows, reverse, external = [], {}, {}
    for f in files:
        # as_posix, not str: the map is committed, and a Windows run must not rewrite
        # every path in it with backslashes.
        rel = f.relative_to(ROOT).as_posix()
        used = imports_of(f)
        inside = sorted(n for n in used if n in known)
        outside = sorted(n for n in used if n not in known and n not in STDLIB)
        rows.append(
            (
                rel,
                summary(f),
                inside,
                outside,
                len(f.read_text(encoding="utf-8").splitlines()),
            )
        )
        for name in inside:
            reverse.setdefault(name, []).append(rel)
        for name in outside:
            external.setdefault(name, []).append(rel)

    out = [
        "# DEPENDENCIES — generated",
        "",
        "Generated by `python3 tools/depmap.py`. **Never edit by hand.**",
        "Regenerate after touching code; `tools/checks.py` fails when this file is stale.",
        "",
        "## Modules",
        "",
        "| file | lines | what it is | imports from project | external |",
        "|---|---|---|---|---|",
    ]
    for rel, doc, inside, outside, n in rows:
        out.append(
            f"| `{rel}` | {n} | {doc} | {', '.join(inside) or '—'} | "
            f"{', '.join(outside) or '—'} |"
        )

    out += [
        "",
        "## Who depends on what",
        "",
        "| project module | imported by |",
        "|---|---|",
    ]
    for name in sorted(reverse):
        out.append(
            f"| `{name}` | {', '.join(f'`{p}`' for p in sorted(reverse[name]))} |"
        )

    out += ["", "## External libraries", "", "| library | used in |", "|---|---|"]
    for name in sorted(external):
        out.append(
            f"| `{name}` | {', '.join(f'`{p}`' for p in sorted(external[name]))} |"
        )
    return "\n".join(out) + "\n"


def main() -> None:
    """Write docs/DEPENDENCIES.md and report how many files were mapped."""
    files = py_files()
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(render(files), encoding="utf-8")
    print(f"mapped {len(files)} files -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
