---
q: How are the tests run, and why might a new test_ function never execute?
kw: tests script main, pytest no __main__, audit_tests prints nothing, test function never runs, exit 124 test_portfolio_verdict, from tests.x import _helper ImportError after split
tag: 🔬  date: 2026-10-14
---
# Tests are scripts; a new `test_*` in a script file runs only if `main()` calls it
Run one with `python3 tests/<file>.py`. A file without `__main__` runs under pytest. Whole suite: `tools/audit_tests.py` — call `run_all()` then `report()` from Python; running the script directly prints nothing. A `test_*` added to a script-style file is never executed unless its `main()` calls it.

- `tests/test_portfolio_verdict.py` takes 276-455 s; under load it hits `audit_tests`' 300 s per-test cap (exit 124) while passing alone. Rerun it alone before calling it a failure.
- Splitting a test file: other tests may import its private helpers (`_csv` moved to `test_perf66_algobank_pack` broke liveexport/membank/retest). `grep 'from tests.<module> import'` before moving one.

## Evidence
2026-10-04 cleanup (`INFRA_REVIEW.md`, deleted 2026-10-06).
