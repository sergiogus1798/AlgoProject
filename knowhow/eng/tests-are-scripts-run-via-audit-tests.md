---
q: How are the tests run, and why might a new test_ function never execute?
kw: tests script main, pytest no __main__, audit_tests prints nothing, test function never runs
tag: 🔬  date: 2026-10-04
---
# Tests are scripts; a new `test_*` in a script file runs only if `main()` calls it
Run one with `python3 tests/<file>.py`. A file without `__main__` runs under pytest. Whole suite: `tools/audit_tests.py` — call `run_all()` then `report()` from Python; running the script directly prints nothing. A `test_*` added to a script-style file is never executed unless its `main()` calls it.

## Evidence
2026-10-04 cleanup (`INFRA_REVIEW.md`, deleted 2026-10-06).
