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
| `test_atrcalculator.py` | the ATR stop study's inference on samples built to have one answer: X of 1..100 at numpy's linear percentile and inside its own interval; 20 winners marked unreliable and 2,000 not; trades that never come back past 2 ATR read «sin retorno» there and «ruido» below; the same distribution transfers and one needing 1.5x the air does not; the ±20 % grid | `python3 tests/test_atrcalculator.py` |
| `test_atr.py` | `engines.market.atr.sqx` still is SQX's ATR: five bars worked out by hand (running-mean start, Wilder after, a gap), and a constant true range converging on itself | `python3 tests/test_atr.py` |
| `test_stoploss.py` | the stop-loss graft still writes exactly the `ATRBasedValue` block SQX writes for `SL = X·ATR(20)`, touches only the stop (never the profit target), declares X so the factory can move it, refuses a second graft, and undoing it returns the original byte for byte. Golden over `fixtures/nostop_portfolio.xml` (XAUUSD Strategy 19.8.78) | `python3 tests/test_stoploss.py` |
| `test_variants.py` | `sqx.variants` still writes a variant the same way: the values in, the two name fields renamed, the identifier stamped inside, the inherited fingerprint gone, and every other member byte-identical | `python3 tests/test_variants.py` |
| `test_structural.py` | `sqx.structural` still rewrites a strategy's rules the same way: the golden hashes are the XML SQX ran on 2026-09-26; an ablation deletes exactly one direct child of the entry AND (nested operands untouched) and keeps every variable; the last condition is never ablated; inverting twice returns the mother; a strategy with a stop is never inverted; the factory's read-back matches its plan. Fixtures keep SQX's CRLF | `python3 tests/test_structural.py` |
| `test_cscv.py` | the CSCV maths on panels whose answer is known by construction: pure noise and a block-shuffled surface must both read a PBO of 0.5, one real edge must read 0, the carry-over slope must read zero without an edge, and the plateau rule must refuse an isolated spike | `python3 tests/test_cscv.py` |
| `test_wfc.py` | the WFC's composition of the split: only the owner's four pass (`build` always in sample), each reads a union `sqx.variants.collect` writes, the door lets 17 and 18 read `oos2` and refuses 8, a look writes one ledger row per segment, and `ledger.blind` does not rebuild it | `python3 tests/test_wfc.py` |
| `test_studycontract.py` | the study contract of `core/study`: the eight kinds build, validate, survive JSON and all draw; a ninth kind, a sixth state word and a block missing a key are refused; an override keeps the type of the knob it replaces | `python3 tests/test_studycontract.py` |
| `test_ui_screen.py` | the window's F5 drawings: «Informe de lo que ves» keeps exactly the blocks drawn and the static page and the markdown draw every one of them (E3 isOos: 4 of 4; a grouped surfaces tab: 3 markets + consensus); `markets.split` picks the chosen markets and the consensus of the same segment, the picker drops the oldest at a fourth and never goes below one; `store.load` carries the crossmarket re-run beside the stored result and `fuse.merge` swaps only that market, verdict kept; a partial's header says the verdict comes from the whole analysis | `python3 tests/test_ui_screen.py` |
| `test_ui_labels.py` | no raw key and no scientific number on screen (encargo 24, F15): the rail's one-line config reads as labelled knobs with numbers in full, every kind of filterable column (SQX metric, study field, distribution) has words and the ledger criterion writes no `:g` number, and every knob of every study's config carries its tooltip sentence | `python3 tests/test_ui_labels.py` |
| `test_conditionalmap.py` | the conditional map's tercile edges are measured on the build segment alone and never move when data outside it does; a trade outside the build segment is still classified against those same frozen edges; and a cell under `engines/nulls`'s own minimum trade count never reaches the grid while one at it does | `python3 tests/test_conditionalmap.py` |
| `test_sqxretest.py` | `core.sqxretest` still cuts a Monte Carlo Retest the same way: every simulation's trade count and P/L sum, the original, the eleven confidence levels, and the method settings | `python3 tests/test_sqxretest.py` |

`test_sweep.py`, `test_models.py` and `test_cscv.py` are the tests here that are not golden files:
they check properties on synthetic runs. The first exists because the owner asked for the sweep's full window
to be proven identical to the model it sweeps; the second because the headline model was measured
overlapping 2.8-5.4% of its own trades on 2026-09-17, against a docstring that said it could not.

| `test_tradeshape.py` | the trade-level statistics on series built to have one answer: one outlier must own the whole profit and the trimmed expectancy must go negative; blocks of five identical outcomes must read as clustered on both the runs test and the streak while an i.i.d. sequence does not; the CUSUM must reject a mean that flips halfway and locate it, and must not reject a constant one; the e-ratio must separate a rising path from a symmetric one | `python3 tests/test_tradeshape.py` |

| `test_feedquality.py` | the feed-quality detector on a synthetic feed built to have one answer: a 2K close spike that comes back reads spike-and-revert and a 0.5K one reads nothing; a wick of 2K marks the wick column only; a jump that stays reads «extremo»; 10 identical bars are a frozen run and 9 are not, 12 inside the rollover are counted apart; a 5-minute hole is a gap and 4 is not. The alarm reads chance as quiet and the best 30 trades as an alarm; the calendar tells an outage, a partial close and a holiday apart; the stable year's floor. Then the owner's injection grid, a fifth of it, on a copy of the gold feed: every acceptance criterion but «zero new marks», and those under 0.1 % of the real count (~40 s) | `python3 tests/test_feedquality.py` |
| `test_ledger.py` | the global ledger's two guarantees: the one-way door refuses step 8 on the reserved segment and refuses to serve 17/18/19 until all three have run; the pooled sigma reproduces the union of two searches exactly; two score units are never averaged; and widening N from one search to the whole study raises the deflated Sharpe's benchmark and lowers the DSR | `python3 tests/test_ledger.py` |
| `test_edgecost.py` | `studies.readings.edgeCost`'s gross reconstruction and edge maths on three trades of varying `Size` worked out by hand, against a stubbed (never a real `AlgoData/bars/*`) measured spread: the gross, `cost_today` kept separate from the measured cost, the mean/median edge and `c*`, an exact reconciliation, the reconciliation tab rendering before the headline, the issue-26 warning on a `no_forex` asset, `action: drop` writing DESCARTAR below the bar, and `spread_share.measure()` refusing on a feed with no bars or a segment under 30 trades | `python3 tests/test_edgecost.py` |

| `test_thresholds.py` | a migrated module reads each threshold from `ledger/thresholds.yaml` and from nowhere else: every declared value is swapped for a sentinel and the module's own `config()` must return it; a key missing or declared twice must make the read fail | `python3 tests/test_thresholds.py` |

| `test_snooping.py` | SPA and StepM on panels whose answer is known: over 20 seeds of fat-tailed, correlated noise the StepM names someone no more often than its FWER allows; one planted edge among the noise is named every time; and at equal risk a positive mean excess is exactly a Sharpe above buy and hold's | `python3 tests/test_snooping.py` |

| `test_blindjoint.py` | step 20 on mothers whose answer is known: over 20 seeds of noise the StepM names a mother no more often than its FWER allows (and 6 of 100 more); one planted edge is named every time, yet a piece in `fail` vetoes it under `unanimidad` and `sin_fallo`; a mother missing a piece is never read; without oos2 no reading is decided; and the blind door refuses a study without 17, 18 and 19 | `python3 tests/test_blindjoint.py` |

| `test_marketsurfaces.py` | the market surfaces' rho and J on panels built to have one answer: a market against itself and an exact copy read 1 and 1, the same region on another scale passes, the inverse reads −1 and 0, a rho carried by the bad half with unshared tops does not pass, a triplicated backtest counts once, independent rankings read J ≈ 10/190 and sit above the band ≤ 2.5 % of the time, exposure-times-drift reads −0.9 raw and ≈ 0 neutral, and a missing declared market counts as not passing | `python3 tests/test_marketsurfaces.py` |

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

The window's tests (`ui/`), all offscreen (`QT_QPA_PLATFORM=offscreen`) over the daemon's routes in-process through `fastapi.testclient` — never port 8765, never `bin/algoui`, never an SQX install. Grabs land in `scratch/ui-plan/shots/`.

| file | what it protects | run it |
|---|---|---|
| `test_ui_blocks.py` | every block kind draws: every population result and three strategy results per study under `AlgoData/reports/` go through `ResultView` without an exception; selectors filter without recomputing; compare puts each block beside its counterpart (~3 s) | `python3 tests/test_ui_blocks.py` |
| `test_ui_results.py` | the results routes: the catalogue in family order with its roles, a result paired by identity and never borrowed from a same-named strategy, the history, the matrix, older reports skipped with a reason, the config drawer's hash equal to what the study signs | `python3 tests/test_ui_results.py` |
| `test_ui_runner.py` | the run side on `Test_USDJPY_donchianUpperCrossUp_M30`: the python queue (two at once, the rest queued), cancel killing the whole tree, the `only` options, and each refusal sentence with `jobs.start` swapped for a recorder (a wrongly accepted case never starts a real study); `--run` adds one real `edgeCost` run end to end, which writes a report of the day | `python3 tests/test_ui_runner.py [--run]` |
| `test_ui_workflow.py` | the workflow rail on `Test_USDJPY_donchianUpperCrossUp_M30`: every step in WORKFLOW order, 17 sealed and 20 blocked while the ledger's door is shut, an unknown project refused, and Proyecto's rail (`workspace.rail.Rail`) drawn offscreen | `python3 tests/test_ui_workflow.py` |
| `test_ui_ops.py` | `/api/pulse`, `/api/ops/sqx` and `/api/ledger` read-only — `runs` silent unless a project runs, the pulse's task-only count for an outside run (no ETA), `durations.share` — and the jobs strip (with its SQX chip), pulse and ledger widgets offscreen | `python3 tests/test_ui_ops.py` |
| `test_ui_studypage.py` | the study tabs Estrategia embeds: result, drawer overrides, history, compare two days and two strategies, a refused study said and refused, scope many on the same databank; `--run` adds one real `edgeCost` run reloading the page (it writes a report of the day) | `python3 tests/test_ui_studypage.py [--run]` |
| `test_ui_shell.py` | the whole window over the whole daemon (`ui.daemon.app.APP`): every sidebar zone opens and marks only its button; SELECTION fills Proyecto's databank panel and a double click opens Estrategia on that strategy (crumb, title, study tabs), a row whose databank left every install included; each crumb opens its PROYECTO zone; PORTFOLIOS' «Importar» shows the archived version without touching SELECTION; one grab per zone | `python3 tests/test_ui_shell.py` |
| `test_ui_tearsheet.py` | the Ficha: `/api/tearsheet` and `/exits` on the Donchian USDJPY harvest of 2026-09-27 (the deepest IS drawdown episode well formed — the hand-checked one belonged to the retired fixture, re-measure one before asserting it again —, monthly cells summing to the final equity to the cent, exit rows summing to the totals, refusal of any sample but IS/OOS) drawn offscreen; «Lote» shown only for a mother with a batch folder | `python3 tests/test_ui_tearsheet.py` |
| `test_ui_tearmarket.py` | the Ficha's market routes on the Donchian USDJPY harvest: the month 2×2 cells plus flat plus no-market summing to the months, quantile picks deterministic, a seed redrawing the same five, refusals (the project whose name holds no asset only when its harvest exists; it says so otherwise), no bar past oos1; gallery drawn offscreen | `python3 tests/test_ui_tearmarket.py` |
| `test_ui_cmdpalette.py` | Ctrl+K over the whole daemon in-process: matching and ranking (`cmdrank`), «ledger» finding Registro de búsquedas by its alias, nothing read at start, Enter to a zone, a strategy (its ficha) and a study (on the ficha; a population-only study not listed), recents capped at ten, a broken QSettings store, a focused text field keeping Ctrl+K | `python3 tests/test_ui_cmdpalette.py` |
| `test_ui_batch.py` | `/api/batch` never lets an oos2/ALL key or label out (real and synthetic parquet); a batch folder without metrics.parquet said; «Lote» offscreen on the Donchian mother's 150 variants | `python3 tests/test_ui_batch.py` |
| `test_ui_loader.py` | the databank loader: a build databank pairs with OOS and sends only trades and cosecha to the conductor, a cross-market one exports with data=all, a failed load is never queued again alone and ↻ requeues it, nothing is read while SQX writes the project, one conductor job at a time. The four tests that read a live build + OOS + cross-market databank skip with a sentence when no install holds the Donchian project's (only its WFM was on the custodian on 2026-09-28) | `python3 tests/test_ui_loader.py` |
| `test_ui_strategy.py` | the Estrategia routes in-process on `Test_USDJPY_donchianUpperCrossUp_M30`: `/api/strategy/meta` reads the exported .sqx under the databank's name (direction, costs, the build task), `/stats` gives IS with its excess kurtosis in USD per lot, and OOS2 answers «reservado…» both there and in `/api/tearsheet?sample=OOS2` | `python3 tests/test_ui_strategy.py` |

| `test_spread.py` | `core.tickfile` on a `*_TICK.dat` written by hand in SQX's 4.2 format: the header, a magic chain crossed at 1,000 ticks, deltas of 1, 2 and 4 bytes both ways, each minute's opening, time-weighted, min and max spread and bid; then `studies.data.spread.reprice` — a long pays the spread at its entry, a short at its exit, P/L adjusted by hand | `python3 tests/test_spread.py` |
| `test_strategymeta.py` | `sqx.inspect.strategymeta` still reads a strategy's fields the same way, over a template-built short with SL/PT/trailing, a generic build whose AND holds bare items and exit signals, and a XAUUSD OOS strategy with its project's task and an inactive twin; the direction agrees with `logic.direction`, the entries with `logic.conditions` where that regex applies, a grafted stop reads `ATRBasedValue`, and the asset card hash is today's file | `python3 tests/test_strategymeta.py` |
| `test_archive.py` | the strategy archive on a real strategy: two versions, the same stamp refused, sealed read-only, refused while SQX writes the project, `load()` equal to the live daemon, and no `studies.*`/`ui.*` import nor subprocess in `load()` | `python3 tests/test_archive.py` |
| `test_identity.py` | identity resolution on a retired project: the cosecha (build and OOS side), the .sqx an export kept, a cosecha newer than the export refused, a retest copy `(1)` left unsigned rather than guessed, and — on a scratch folder, nothing exported — `export_trades.sign` (with export_retest's `<i>__` prefix and without) leaving the `identity.csv` that signs the export | `python3 tests/test_identity.py` |

| `test_advance.py` | «Continuar workflow» on a scratch install, every SQX call faked: the master refused before any other check, a worker whose port answers refused and never stopped, another project touched within 24 h refused; the happy path (with an earlier finished run in today's log) copies the two discarded `.sqx` and a `verdict.csv` with their identities, then calls curate → ledger → stage (only `OOS`) → start → `action=start` → only `action=status` → stop, in that order, and leaves a `cut` line that empties F6's live discards | `python3 tests/test_advance.py` |
| `test_advance_edges.py` | «Continuar workflow» going wrong: `action=start` refused, the start never logged within the bound, `worker.start` failing half-way — each fails the job AND stops the worker; a run started before midnight and finished after it is followed across both log files, and an earlier finish does not count; no template skips the ledger; a second «Continuar» queued is refused and starts nothing; duplicate files are named in the confirmation | `python3 tests/test_advance_edges.py` |
