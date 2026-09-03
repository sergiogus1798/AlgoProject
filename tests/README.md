# tests — golden files, not a suite

A handful of tests, only where a silent break would go unnoticed for weeks: the parsers everything
else is built on. Run them with plain Python; there is no test framework to install.

| file | what it protects | run it |
|---|---|---|
| `test_cfx.py` | `core.cfx` still reads a project's tasks, output databanks and conditions the same way | `python3 tests/test_cfx.py` |

`fixtures/optimizer.cfx` is a real 2.4 KB project copied from the master. `--bless` rewrites the
golden file: only do that when the change in output is intended, and say in the commit why.

**Still missing a fixture:** `core.sqxfile` has no golden test, because a `.sqx` is about 6 MB and
this repository ignores them. Either commit one small strategy as an exception, or point the test at
a path in `config/machine.yaml`. Until then the `.sqx` parser is unprotected — `OPEN.md` tracks it.
