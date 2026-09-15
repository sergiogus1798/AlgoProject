# tests — golden files, not a suite

A handful of tests, only where a silent break would go unnoticed for weeks: the parsers everything
else is built on. Run them with plain Python; there is no test framework to install.

| file | what it protects | run it |
|---|---|---|
| `test_cfx.py` | `core.cfx` still reads a project's tasks, output databanks and conditions the same way | `python3 tests/test_cfx.py` |
| `test_sweep.py` | the window sweep: one block is the free-placement model itself, draw for draw; smaller blocks keep every trade inside its block; no model overlaps its own trades | `python3 tests/test_sweep.py` |
| `test_sqxfile.py` | `core.sqxfile` still reads a strategy's identity hash, symbol, parameters and rule tree the same way | `python3 tests/test_sqxfile.py` |

`test_sweep.py` is the one test here that is not a golden file: it checks properties on synthetic runs, and it is there because the owner asked for the sweep's full window to be proven identical to the model it sweeps.

`fixtures/optimizer.cfx` is a real 2.4 KB project copied from the master. `--bless` rewrites the
golden file: only do that when the change in output is intended, and say in the commit why.

`fixtures/strategy.sqx` is a real strategy from USDCHF/FinalOOS. **Not every `.sqx` is 6 MB**: they
run from 28 KB to 15 MB on this machine, and the smallest carries everything the parser reads — a
`Results/` entry naming symbol and feed, 28 parameters and a full rule tree. `.gitignore` excludes
`*.sqx` and makes `tests/fixtures/` the one exception.
