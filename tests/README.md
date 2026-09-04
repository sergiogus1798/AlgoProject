# tests — golden files, not a suite

A handful of tests, only where a silent break would go unnoticed for weeks: the parsers everything
else is built on. Run them with plain Python; there is no test framework to install.

| file | what it protects | run it |
|---|---|---|
| `test_cfx.py` | `core.cfx` still reads a project's tasks, output databanks and conditions the same way | `python3 tests/test_cfx.py` |
| `test_sqxfile.py` | `core.sqxfile` still reads a strategy's identity hash, symbol, parameters and rule tree the same way | `python3 tests/test_sqxfile.py` |

`fixtures/optimizer.cfx` is a real 2.4 KB project copied from the master. `--bless` rewrites the
golden file: only do that when the change in output is intended, and say in the commit why.

`fixtures/strategy.sqx` is a real strategy from USDCHF/FinalOOS. **Not every `.sqx` is 6 MB**: they
run from 28 KB to 15 MB on this machine, and the smallest carries everything the parser reads — a
`Results/` entry naming symbol and feed, 28 parameters and a full rule tree. `.gitignore` excludes
`*.sqx` and makes `tests/fixtures/` the one exception.
