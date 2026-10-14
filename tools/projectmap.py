#!/usr/bin/env python3
"""Generate PROJECT_MAP.md from Graphify's graph: modules, who talks to whom, infra vs calculation, hot spots."""

import ast
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import TypedDict

ROOT = Path(__file__).resolve().parent.parent
GRAPH = ROOT / "graphify-out" / "graph.json"
OUT = ROOT / "PROJECT_MAP.md"
SKIP = ("tools/sqx-lab/", "scratch/")
USES = {"calls", "imports", "imports_from", "references", "uses", "inherits", "indirect_call"}
# A module that imports from NUMERIC computes; one that imports from OUTSIDE talks to something.
NUMERIC = {"numpy", "scipy", "numba", "statsmodels", "sklearn"}
OUTSIDE = {"subprocess", "requests", "urllib", "http", "socket", "fastapi", "uvicorn", "pyside6", "httpx", "shutil"}
# The layout's own split (CLAUDE.md, «Layout»): these compute, everything else is plumbing.
CALC_ROOTS = ("engines", "studies/", "portfolio/", "ledger", "core/study", "core/surface")
TOOLING = ("tests", "tools", "perf", ".claude/")
COMMON = {"main()", "run()", "render()", "load()", "report()", "rows()", "build()", "read()", "write()"}
NEAR_LIMIT = 480


def module_of(path: str) -> str:
    """The module a file belongs to: its first two folders, or the first when it sits right under it."""
    parts = path.split("/")
    return "/".join(parts[:2]) if len(parts) > 2 else parts[0] if len(parts) > 1 else "(root)"


def load() -> tuple[dict, list]:
    """The graph's code nodes by id (plus external concepts) and its edges."""
    graph = json.loads(GRAPH.read_text(encoding="utf-8"))
    nodes = {n["id"]: n for n in graph["nodes"]
             if n["file_type"] in ("code", "concept") and not n["source_file"].startswith(SKIP)}
    return nodes, [e for e in graph["links"] if e["source"] in nodes and e["target"] in nodes]


def describe(module: str) -> str:
    """One line of what a module is: its README's first prose line, else its package docstring."""
    folder = ROOT / module
    for readme in (folder / "README.md", folder.parent / "README.md"):
        if readme.exists() and readme.parent != ROOT:
            for line in readme.read_text(encoding="utf-8").splitlines():
                if line.strip() and not line.startswith(("#", "|", "<", "```", "---")):
                    return line.strip()[:140]
    init = folder / "__init__.py"
    doc = ast.get_docstring(ast.parse(init.read_text(encoding="utf-8"))) if init.exists() else None
    return doc.splitlines()[0] if doc else "—"


def kind(module: str, libs: set[str]) -> str:
    """Infrastructure, pure calculation or mixed: the layout says which, the imports say whether it is pure."""
    if module.startswith(TOOLING):
        return "INFRA"
    if module.startswith(CALC_ROOTS):
        return "MIXED" if libs & OUTSIDE else "CALC"
    return "MIXED" if libs & NUMERIC else "INFRA"


class Survey(TypedDict):
    """What `survey` gathers: lines per file, libraries and dependencies per module, exposed symbols."""

    lines: dict[str, int]
    libs: defaultdict[str, set[str]]
    deps: defaultdict[str, Counter[str]]
    exposed: defaultdict[str, Counter[str]]


def survey(nodes: dict, edges: list) -> Survey:
    """Everything the map prints, gathered in one pass over the graph.

    Returns:
        files (path -> lines), libs and deps per module, and the symbols other modules use.
    """
    files = {n["source_file"] for n in nodes.values() if n["source_file"].endswith(".py")}
    lines = {f: len((ROOT / f).read_text(encoding="utf-8").splitlines()) for f in files if (ROOT / f).exists()}
    libs: defaultdict[str, set[str]] = defaultdict(set)
    deps: defaultdict[str, Counter[str]] = defaultdict(Counter)
    exposed: defaultdict[str, Counter[str]] = defaultdict(Counter)
    for e in edges:
        if e["relation"] not in USES:
            continue
        src, dst = nodes[e["source"]], nodes[e["target"]]
        mod = module_of(src["source_file"])
        if not dst["source_file"]:
            libs[mod].add(dst["label"].lower().replace(".", "_").split("_")[0])
            continue
        other = module_of(dst["source_file"])
        if other != mod:
            deps[mod][other] += 1
            if dst.get("_callable") and not dst["label"].endswith(".py"):
                exposed[other][dst["label"]] += 1
    return {"lines": lines, "libs": libs, "deps": deps, "exposed": exposed}


def repeated(nodes: dict) -> list[tuple[str, list[str]]]:
    """Function names defined in three or more modules — the same helper written again."""
    where = defaultdict(set)
    for n in nodes.values():
        if n.get("_callable") and n["label"].endswith("()") and n["label"] not in COMMON \
                and not n["label"].startswith(".") and not n["source_file"].startswith("tests/"):
            where[n["label"]].add(module_of(n["source_file"]))
    return sorted(((k, sorted(v)) for k, v in where.items() if len(v) >= 3), key=lambda r: -len(r[1]))


def render(nodes: dict, s: Survey) -> str:
    """Build the whole PROJECT_MAP.md text; no timestamp, so an unchanged tree regenerates identically."""
    per = defaultdict(list)
    for f, n in s["lines"].items():
        per[module_of(f)].append(n)
    fan_in = Counter()
    for targets in s["deps"].values():
        for other in targets:
            fan_in[other] += 1
    out = ["# PROJECT_MAP — generated", "",
           "Generated by `python3 tools/projectmap.py` from Graphify's graph (`graphify-out/graph.json`). "
           "**Never edit by hand.**",
           "Class: CALC is a module of the computing folders (engines, studies, portfolio, ledger, core/study, "
           "core/surface); INFRA is everything else. MIXED is a CALC module that also imports "
           f"{'/'.join(sorted(OUTSIDE))}, or an INFRA module that also imports {'/'.join(sorted(NUMERIC))}.", "",
           "## Modules", "", "| module | class | files | lines | what it is |", "|---|---|---|---|---|"]
    for mod in sorted(per):
        out.append(f"| `{mod}` | {kind(mod, s['libs'][mod])} | {len(per[mod])} | {sum(per[mod])} | {describe(mod)} |")

    out += ["", "## Dependencies and interfaces", "",
            "| module | uses (references) | used by | what others take from it (callers) |", "|---|---|---|---|"]
    for mod in sorted(per):
        uses = ", ".join(f"{m} ({c})" for m, c in s["deps"][mod].most_common(8)) or "—"
        api = ", ".join(f"`{k}` ({c})" for k, c in s["exposed"][mod].most_common(8)) or "—"
        out.append(f"| `{mod}` | {uses} | {fan_in[mod]} | {api} |")

    big = sorted(((n, f) for f, n in s["lines"].items() if n >= NEAR_LIMIT), reverse=True)
    out += ["", "## Hot spots", "", f"### Files pressed against the 500-line limit, {NEAR_LIMIT}+ ({len(big)})", ""]
    out += [f"- `{f}` — {n}" for n, f in big[:40]]
    out += ["", "### Most coupled modules (modules used + modules using it)", ""]
    coupled = sorted(per, key=lambda m: -(len(s["deps"][m]) + fan_in[m]))[:15]
    out += [f"- `{m}` — uses {len(s['deps'][m])}, used by {fan_in[m]}" for m in coupled]
    out += ["", "### Function names defined in three or more modules", ""]
    out += [f"- `{name}` — {', '.join(mods)}" for name, mods in repeated(nodes)[:40]]
    return "\n".join(out) + "\n"


def main() -> None:
    """Write PROJECT_MAP.md and report how many modules were mapped."""
    nodes, edges = load()
    text = render(nodes, survey(nodes, edges))
    OUT.write_text(text, encoding="utf-8")
    print(f"mapped {text.count(chr(10) + '| `') // 2} modules -> {OUT.name}")


if __name__ == "__main__":
    main()
