# tests — golden files, not a suite

A handful of tests, only where a silent break would go unnoticed for weeks: the parsers everything
else is built on. Run them with plain Python; there is no test framework to install.

| file | what it protects | run it |
|---|---|---|
| `test_cfx.py` | `core.cfx` still reads a project's tasks, output databanks and conditions the same way | `python3 tests/test_cfx.py` |
| `test_sweep.py` | the window sweep: one block is the free-placement model itself, draw for draw; smaller blocks keep every trade inside its block; no model overlaps its own trades | `python3 tests/test_sweep.py` |
| `test_models.py` | `block_shift` never overlaps its own trades, and one calendar semester is displaced identically in every market — the property the joint null rests on | `python3 tests/test_models.py` |
| `test_surface.py` | `core.surface` on grids whose answer is known by construction: a shuffled surface must read zero shift, zero Cliff and an unchanged plateau while its paired correlation collapses; `n_eff` counts backtests rather than rows; the sentinels never reach a ranking; and A1 reads a lone spike as rank 1 with no company while a broad plateau reads the reverse, on a negative metric included | `python3 tests/test_surface.py` |
| `test_sqxfile.py` | `core.sqxfile` still reads a strategy's identity hash, symbol, parameters and rule tree the same way. ⚠️ Rebendecido el 2026-09-23: `identity()` pasó a hashear el XML **normalizado**, así que el hash del golden cambió a propósito. Sólo cambió ese campo — comprobado antes de rebendecir | `python3 tests/test_sqxfile.py` |
| `test_variants.py` | `sqx.variants` still writes a variant the same way: the values in, the two name fields renamed, the identifier stamped inside, the inherited fingerprint gone, and every other member byte-identical | `python3 tests/test_variants.py` |
| `test_cscv.py` | the CSCV maths on panels whose answer is known by construction: pure noise and a block-shuffled surface must both read a PBO of 0.5, one real edge must read 0, the carry-over slope must read zero without an edge, and the plateau rule must refuse an isolated spike | `python3 tests/test_cscv.py` |
| `test_studycontract.py` | the study contract of `core/study`: the eight kinds build, validate, survive JSON and all draw; a ninth kind, a sixth state word and a block missing a key are refused; an override keeps the type of the knob it replaces | `python3 tests/test_studycontract.py` |
| `test_sqxretest.py` | `core.sqxretest` still cuts a Monte Carlo Retest the same way: every simulation's trade count and P/L sum, the original, the eleven confidence levels, and the method settings | `python3 tests/test_sqxretest.py` |

`test_sweep.py`, `test_models.py` and `test_cscv.py` are the tests here that are not golden files:
they check properties on synthetic runs. The first exists because the owner asked for the sweep's full window
to be proven identical to the model it sweeps; the second because the headline model was measured
overlapping 2.8-5.4% of its own trades on 2026-09-17, against a docstring that said it could not.

| `test_tradeshape.py` | the trade-level statistics on series built to have one answer: one outlier must own the whole profit and the trimmed expectancy must go negative; blocks of five identical outcomes must read as clustered on both the runs test and the streak while an i.i.d. sequence does not; the CUSUM must reject a mean that flips halfway and locate it, and must not reject a constant one; the e-ratio must separate a rising path from a symmetric one | `python3 tests/test_tradeshape.py` |

| `test_ledger.py` | the global ledger's two guarantees: the one-way door refuses step 8 on the reserved segment and refuses to serve 17/18/19 until all three have run; the pooled sigma reproduces the union of two searches exactly; two score units are never averaged; and widening N from one search to the whole study raises the deflated Sharpe's benchmark and lowers the DSR | `python3 tests/test_ledger.py` |
| `test_edgecost.py` | `studies.readings.edgeCost`'s gross reconstruction and edge maths on three trades of varying `Size` worked out by hand, against a stubbed (never a real `AlgoData/bars/*`) measured spread: the gross, `cost_today` kept separate from the measured cost, the mean/median edge and `c*`, an exact reconciliation, the reconciliation tab rendering before the headline, the issue-26 warning on a `no_forex` asset, `action: drop` writing DESCARTAR below the bar, and `spread_share.measure()` refusing on a feed with no bars or a segment under 30 trades | `python3 tests/test_edgecost.py` |

| `test_thresholds.py` | a migrated module reads each threshold from `ledger/thresholds.yaml` and from nowhere else: every declared value is swapped for a sentinel and the module's own `config()` must return it; a key missing or declared twice must make the read fail | `python3 tests/test_thresholds.py` |

| `test_snooping.py` | SPA and StepM on panels whose answer is known: over 20 seeds of fat-tailed, correlated noise the StepM names someone no more often than its FWER allows; one planted edge among the noise is named every time; and at equal risk a positive mean excess is exactly a Sharpe above buy and hold's | `python3 tests/test_snooping.py` |

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

`test_cscv.py` checks every PBO property on the **average of twelve panels**, never on one. Measured
2026-09-22, the PBO of a single pure-noise panel has a standard deviation of 0.21 and individual
draws ran from 0.25 to 0.92: the 252 partitions overlap heavily and are nothing like 252
independent observations. A single-panel assertion would have passed or failed on the seed. That
same spread is why the pipeline's 50 % gate on the PBO is documented as a coarse filter.
