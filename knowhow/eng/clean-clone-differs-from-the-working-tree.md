---
q: Why does code pass on leaseWeb but fail on a fresh clone (gorilla), and what do I fix?
kw: gorilla clean clone fails; 'perf' is not a package; perf.cpython-312 linux-tools namespace package; gitignore *.csv *.parquet *.sqx hid skeletons symbols.csv fixtures; test_condition_count test_builder_feedswap; PyYAML 6.0.1; test_marketsurfaces chunked null last bit BLAS; 51 failing tests uncommitted
tag: 📓  date: 2026-10-11  see: sqx-drive/second-server-gorilla
---
# A clone on gorilla fails where the leaseWeb working tree passes: shadowed modules, ignored files, uncommitted fixes, BLAS bits
Trap: green on leaseWeb means nothing for GitHub's master. Run `bin/remote.sh gorilla python3 tools/checks.py` before trusting a push.
| cause | fix |
|---|---|
| Ubuntu linux-tools puts `/usr/lib/linux-tools/<kernel>/lib/perf.cpython-312-*.so` on `sys.path`; `perf/` had no `__init__.py` (namespace package) and lost: `import perf.…` died «'perf' is not a package» (pipeline.stages.gates, pipeline.cleanup, window catalogue, 4 ui tests) | `perf/__init__.py`. Rule: a top-level folder whose name can collide with a system module needs an `__init__.py` (`perf` was the only one shadowed) |
| `.gitignore` blanket `*.csv`, `*.parquet`, `*.sqx` hid needed files: 17 skeletons `tools/sqx-lab/plugins/sqx-lab/skills/sqx-strategy-template/engine/skeletons/*.sqx` (read by `sqx/templates/build.py`, `holes.py`, `ui/daemon/interview.py`), `mt5/symbols.csv` (`mt5/verify/firms.py`), `tests/fixtures/fleet/**`. Symptom: `test_condition_count`, `test_builder_feedswap` fail; authoring a template there fails | `!` exceptions in `.gitignore` |
| Sessions leave test fixes or knowhow cards uncommitted: gorilla showed 7 `checks.py` problems and 51 failing tests (8 here) | commit them (owner decides) |
| `tests/test_marketsurfaces.py` compared a chunked null exactly across chunk sizes; the 7950X's BLAS rounds the last bit differently (-0.6231758175072347 vs …346) 🔬 | compare to 9 digits, `blocks.plain(x, 9)` |

## Evidence
Of gorilla's 43 extra failures: ~30 are tests pinned to leaseWeb-only data (`Test_USDJPY_donchianUpperCrossUp_M30` exports, `AlgoData/mt5/verify`, funding DB, archive) — not errors; 5 were uncommitted test fixes; the rest the rows above.
📓 2026-10-11 gorilla runs. Versions: gorilla Ubuntu 24.04, Python 3.12.3, PyYAML 6.0.1, no ruff; leaseWeb Python 3.10.12, PyYAML 5.4.1; other key packages identical.
Reproduce the shadow: `python3 -c "import perf; print(perf)"` on gorilla before the fix.
