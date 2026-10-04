---
q: Can the graphify graph list dead functions?
kw: dead code, unreferenced nodes, graphify orphan, projectmap dead section, FastAPI route unused, Qt callback
tag: 🔬  date: 2026-10-04
---
# Graphify cannot list dead functions — grep per symbol
"Nodes nothing refers to" was 89 % false positives: FastAPI routes, Qt callbacks and `__main__` entry points are called by frameworks, not by code. That section was removed from `tools/projectmap.py`. Confirm dead code with `grep -rn '<symbol>'` per symbol.

## Evidence
2026-10-04 cleanup; `scratch/cleanup/*.md`.
