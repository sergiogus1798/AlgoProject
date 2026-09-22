# tests — golden files, not a suite

A handful of tests, only where a silent break would go unnoticed for weeks: the parsers everything
else is built on. Run them with plain Python; there is no test framework to install.

| file | what it protects | run it |
|---|---|---|
| `test_cfx.py` | `core.cfx` still reads a project's tasks, output databanks and conditions the same way | `python3 tests/test_cfx.py` |
| `test_sweep.py` | the window sweep: one block is the free-placement model itself, draw for draw; smaller blocks keep every trade inside its block; no model overlaps its own trades | `python3 tests/test_sweep.py` |
| `test_models.py` | `block_shift` never overlaps its own trades, and one calendar semester is displaced identically in every market — the property the joint null rests on | `python3 tests/test_models.py` |
| `test_surface.py` | `core.surface` on grids whose answer is known by construction: a shuffled surface must read zero shift, zero Cliff and an unchanged plateau while its paired correlation collapses; `n_eff` counts backtests rather than rows; the sentinels never reach a ranking | `python3 tests/test_surface.py` |
| `test_sqxfile.py` | `core.sqxfile` still reads a strategy's identity hash, symbol, parameters and rule tree the same way | `python3 tests/test_sqxfile.py` |
| `test_variants.py` | `sqx.variants` still writes a variant the same way: the values in, the two name fields renamed, the identifier stamped inside, the inherited fingerprint gone, and every other member byte-identical | `python3 tests/test_variants.py` |
| `test_sqxretest.py` | `core.sqxretest` still cuts a Monte Carlo Retest the same way: every simulation's trade count and P/L sum, the original, the eleven confidence levels, and the method settings | `python3 tests/test_sqxretest.py` |

`test_sweep.py` and `test_models.py` are the two tests here that are not golden files: they check
properties on synthetic runs. The first exists because the owner asked for the sweep's full window
to be proven identical to the model it sweeps; the second because the headline model was measured
overlapping 2.8-5.4% of its own trades on 2026-09-17, against a docstring that said it could not.

`fixtures/optimizer.cfx` is a real 2.4 KB project copied from the master. `--bless` rewrites the
golden file: only do that when the change in output is intended, and say in the commit why.

`fixtures/retest.sqx` is `XAUUSD/MCR 5 Params/Strategy 23.16.37` cut down to what the reader touches:
the result XML, the original orders, `lastSettings.xml`, and **five** of its thousand simulations —
35 KB instead of 3 MB. Five is enough because the reader's job is cutting the archive up, not
judging it; calibrating the 30 reconstructed formulas is a separate job that runs on the full
export and is not in this folder yet.

Beside the golden file the test carries **invariants**, and `--bless` refuses to write when one of
them is broken. The load-bearing one is that the original P/L summed off the binary equals the
NetProfit SQX stored in the XML, to within a cent per trade: it ties the two decoders together, so a
flipped byte order, a wrong header width or an off-by-one offset fails even if someone blesses the
golden file over the top. Measured, the invariants catch a little-endian decode, a hole in the
simulation indices, a shifted offset and a lost confidence level. They deliberately **cannot** catch
a dropped *last* simulation — that is indistinguishable from a legitimately truncated run, which 3
of the 40 real runs are — and the golden file catches that one instead.

`test_variants.py` reuses `fixtures/strategy.sqx` rather than adding one: it carries both int and
double parameters, which is what the rewriter can get wrong — `95.0` into an int parameter is not
the same file as `95`. Beside the golden file it carries **invariants**, and the load-bearing one is
that rewriting the parent's own tuple back into the parent reproduces the parent byte for byte apart
from the identifier stamp. That ties the reader and the writer together, so a regex that matched the
wrong block, a number formatted a new way or a lost member fails even if someone blesses the golden
file over the top.

`fixtures/strategy.sqx` is a real strategy from USDCHF/FinalOOS. **Not every `.sqx` is 6 MB**: they
run from 28 KB to 15 MB on this machine, and the smallest carries everything the parser reads — a
`Results/` entry naming symbol and feed, 28 parameters and a full rule tree. `.gitignore` excludes
`*.sqx` and makes `tests/fixtures/` the one exception.
