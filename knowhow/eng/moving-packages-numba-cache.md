---
q: moved renamed package folder git mv, ModuleNotFoundError old module name after refactor, numba cache=True .nbi .nbc __pycache__ stale, bulk rewrite of paths touched dated audit reports, mass rename imports
tag: 🔬  date: 2026-09-25  see: eng/moving-module-into-layer, perf/numba-division
---
# Moving whole packages: clear `__pycache__`, and never let a bulk rewrite touch dated records
1. `git mv` of a directory moves the untracked `__pycache__` with it. Numba's `cache=True` files there (`.nbi`/`.nbc`) pickle the **old** module path, so the first call of a cached kernel imports a package that no longer exists. After any package move: `find . -name __pycache__ -prune -exec rm -rf {} +`.
2. A path rewrite across the repo must skip what is a dated record — `audit/` reports and dated `docs/AgentPDFs/*-AAAA-MM-DD.md` — or history starts saying things that were not true on its date. Rewrite live docs; point old names to `docs/MAPA-DE-CARPETAS.md`.

## Evidence
Refactor `strategies/`, `tasks/`, `nulls/`, `gate/` → `studies/`, `engines/`, `portfolio/common/monteCarlo` (2026-09-25).
- After phase 2 (`nulls.kernel` → `engines.nulls.kernel`) the regression failed with `ModuleNotFoundError: No module named 'nulls.kernel'` from inside numba's cache loader; deleting every `__pycache__` fixed it, no code change.
- The AST+text mover rewrote module paths inside `audit/` daily reports; restored with `git checkout <pre-move commit> -- audit`.
