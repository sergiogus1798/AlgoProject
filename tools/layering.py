"""Layering check: which project package may import which, with today's violations as debt."""

import ast
from pathlib import Path

import depmap

ROOT = depmap.ROOT
# importer package -> the only packages it may import (its own is always allowed).
MAY_IMPORT = {"core": set(), "engines": {"core", "ledger"}, "sqx": {"core"}}
# imported package -> the only packages allowed to import it.
ONLY_FROM = {"ui": {"tests", "tools"}, "tools": {"tests"}, "tests": set()}
# DEBT, not a licence: every pair is a violation that existed on 2026-10-03. Shrink this set when
# one is fixed; the check fails on any pair that is NOT in it, so a new violation cannot join.
ALLOW: set[tuple[str, str]] = {
    (".claude/skills/dossier-pdf/render.py", "tools"),
    ("core/archive/manifest.py", "ledger"),
    ("core/archive/view.py", "ui.daemon"),
    ("core/archive/write.py", "ui.daemon"),
    ("mt5/reconcile/sqxside.py", "ui.daemon"),
    ("mt5/verify/autopilot.py", "ui.daemon"),
    ("mt5/verify/run.py", "ui.daemon"),
    ("mt5/verify/sqxside.py", "ui.daemon"),
    ("perf/inputs/workloads.py", "ui.daemon"),
    ("pipeline/autopilot/blind.py", "ui.daemon"),
    ("pipeline/autopilot/call.py", "ui.daemon"),
    ("pipeline/autopilot/closing.py", "ui.daemon"),
    ("pipeline/autopilot/facts.py", "ui.daemon"),
    ("pipeline/autopilot/judge.py", "ui.daemon"),
    ("pipeline/autopilot/plan.py", "ui.daemon"),
    ("pipeline/autopilot/run.py", "ui.daemon"),
    ("pipeline/autopilot/survivors.py", "ui.daemon"),
    ("ui/desktop/launch.py", "ui.daemon"),
}


def unit(parts: tuple[str, ...]) -> str:
    """The layer of a dotted module: its top package, except `ui`, split in daemon and desktop."""
    return ".".join(parts[:2]) if parts[0] == "ui" and len(parts) > 1 else parts[0]


def edges(files: list[Path]) -> set[tuple[str, str, str]]:
    """Every (importer file, importer unit, imported unit) between project packages, lazy imports too."""
    tops = {f.relative_to(ROOT).parts[0] for f in files if len(f.relative_to(ROOT).parts) > 1}
    out = set()
    for f in files:
        rel = f.relative_to(ROOT)
        if len(rel.parts) < 2:
            continue
        mine = unit(rel.parts)
        for node in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            mods = ([a.name for a in node.names] if isinstance(node, ast.Import) else
                    [node.module] + [f"{node.module}.{a.name}" for a in node.names]
                    if isinstance(node, ast.ImportFrom) and node.module and not node.level else [])
            for m in mods:
                if m.split(".")[0] in tops:
                    out.add((rel.as_posix(), mine, unit(tuple(m.split(".")))))
    return out


def bad_layering(files: list[Path]) -> list[str]:
    """Imports that cross a layer in the wrong direction and are not in ALLOW."""
    out = []
    for path, mine, theirs in sorted(edges(files)):
        top, other = mine.split(".")[0], theirs.split(".")[0]
        wrong = ((top != other and other in ONLY_FROM and top not in ONLY_FROM[other])
                 or (top != other and top in MAY_IMPORT and other not in MAY_IMPORT[top])
                 or (mine, theirs) == ("ui.desktop", "ui.daemon"))
        if wrong and (path, theirs) not in ALLOW:
            out.append(f"{path}: imports {theirs}, against the layering in CODESTYLE.md "
                       f"(a violation that predates the rule goes in ALLOW, a new one is fixed)")
    return out
