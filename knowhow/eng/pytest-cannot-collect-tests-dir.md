---
q: Why does `pytest tests` die with INTERNALERROR, and how do I run the tests?
kw: pytest INTERNALERROR, collection error sys.exit at import, pytest tests, ModuleNotFoundError standalone, PYTHONPATH
tag: 🔬  date: 2026-10-12  see: eng/tests-are-scripts-run-via-audit-tests
---
# `pytest tests` cannot collect: several `tests/test_*.py` are scripts that call `sys.exit` at import
Run files one by one. Script-style files with `python3 tests/<f>.py`; standalone runs need `PYTHONPATH=.`. Whole suite: `tools/audit_tests.py`.

## Evidence
- 🔬 2026-10-12: `tests/test_oracle_draws.py` and `tests/test_mt5_start_check.py` exit at import and kill collection with INTERNALERROR.
