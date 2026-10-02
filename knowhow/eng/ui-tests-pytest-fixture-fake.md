---
q: pytest fixture not found app shell http port real; test_ui_*.py errors at setup; bare pytest tests/ INTERNALERROR SystemExit; sys.exit at module level crashes pytest collection
tag: 📓  date: 2026-09-30  see: -
---
# `tests/test_ui_*.py`: a plain parameter looks like a pytest fixture, and isn't one

Every `test_ui_*.py` passed its `QApplication`/`Shell`/`TestClient` into each `test_*` as an
ordinary parameter, filled only by its own `main()`. A bare `python3 -m pytest` reads
`app`/`shell`/`http`/`data`/`port` as fixtures it never defined, and every test errors at setup.
Fixed by building them once at import as a module constant, same singleton pattern the rest of
the suite uses; a return-value-fed test got a small recomputing helper instead. Same night, two
files crashed a whole `pytest tests/` with a bare `sys.exit()` at module scope — guarded under
`__main__`; `test_ui_loader.py`'s `held()` skip-guard only ever ran from `__main__`.

## Evidence
- 🔬 `python3 -m pytest tests/test_ui_shell.py -q` before: 4 of 5 `ERROR` at setup (`fixture 'app'
  not found`). After: `5 passed`. Same shape fixed in `test_ui_cmdpalette.py` (8 passed),
  `test_ui_helpmark.py` (5 passed, 1 skipped — `test_coverage` needs `--port`, a live scratch
  daemon, now `pytest.mark.skip`), `test_ui_batch.py` (5 passed), `test_ui_workflow.py` (7 passed).
- 🔬 `python3 -m pytest tests/` before: `INTERNALERROR` (`SystemExit: 0` importing
  `test_funded_rules.py`) — the whole run reported zero tests. After: collects clean.
- 🔬 `test_ui_loader.py`: 4 tests read a live custodian databank; absent tonight (project
  retired), they failed with a bare `KeyError` instead of the skip `held()` already existed for.
  Wired as `pytest.mark.skipif(not held(), ...)`: `2 passed, 4 skipped`, matching `__main__`.
- 🔬 `test_ui_cmdpalette.py`'s pinned `STRATEGY`/probed study were stale from a nightly re-run
  (data drift, not a fixture bug) — same fix pattern as `test_ui_runner.py`: read off the newest
  export; the study probed switched to one confirmed present for that identity.
- 🔬 The fixed files still cross-contaminate when run **together** in one pytest invocation (shared
  `client.get/post`, `SELECTION` singletons) — each passes **alone**, the suite's only documented
  invocation (`tests/README.md`); this pre-existing lack of module isolation was not this fix's job.
