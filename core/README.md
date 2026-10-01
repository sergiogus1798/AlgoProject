# core — shared library

Everything that more than one phase needs. Import it as a package from the project root; scripts that
live deeper add the root to `sys.path` in their first lines.

| file | what it does | in → out |
|---|---|---|
| `__init__.py` | Puts stdout/stderr in UTF-8 on import, so Windows' cp1252 console does not crash on this project's own accents and symbols | — |
| `paths.py` | The only module that knows where anything lives. Reads `config/machine.yaml`; `WORKERS` maps a worker role (conductor, custodian) to its install and port | names, roles → `Path` |
| `datapaths.py` | The data root's secondary trees: the template library, `pipeline/`, `strategyPermutations/`, `logs/`, `backups/`, `projectsBackup/`, `cache/` and `spread/`, and the master's tick files. Split out of `paths.py`, which keeps the installs and the primary exports | names → `Path` |
| `sqxfile.py` | Read a `.sqx` without SQX: identity hash, symbol, inner XML, parameters, the corrected `Param Count` mirrored from `<Variables>` (OPEN #17) | `.sqx` → values |
| `optprofile.py` | Read a `.sqx`'s Sys. Param Permutation profile without SQX: run counts, per-metric medians against the original value, the stored histograms, and every permutation's parameters and statistics when SQX kept them | `.sqx` → dicts |
| `sqxstats.py` | Read a `.sqx` result without SQX: decode any `SQStats` blob into its 152 statistics, the stored metrics per sample, and the daily equity curve | `.sqx` → metrics, series |
| `sqxview.py` | The owner's «Export Data View» as SQStats keys (`VIEW`): the metrics export and the cosecha rebuilt from the files with no SQX, equal to the view's export within float32 — except `Param Count (IS)`, always `sqxfile.param_count`, never SQX's frozen `ParameterCount` (OPEN #17) | `.sqx` → metrics table |
| `sqxretest.py` | Read a Monte Carlo Retest result without SQX: every simulation's P/L vector, the original it was perturbed from, the eleven-level confidence table, and the method settings that produced it | `.sqx` → P/L, levels, provenance |
| `wfmobjectives.py` | SQX's per-cell WFM objectives that it never stores — stability, score, the `WF*` specials — and the criterion each strategy carries, recomputed exactly as SQX does (checked equal on 14 columns × 17 strategies) | `.sqx` root → rule, rows per cell and condition |
| `wfmatrix.py` | Read the Walk-Forward Matrix a WFM cross-check leaves in a `.sqx`: the axes, the 30 cells, and every cell's walk-forward steps with their windows, chosen parameters and paired IS/OOS statistics | `.sqx` → dicts |
| `wftrades.py` | Cut a `data=all` export into one block per matrix cell and tag every trade with its walk-forward step, checked against the counts SQX stored | CSV → frames |
| `trades.py` | Read an `orderstocsv` export: times parsed, unfilled orders dropped, one frame per market, cost and MAE/MFE recovered | CSV → frames |
| `bars.py` | Read an OHLC export into a frame indexed by bar open time | CSV → frame |
| `tickfile.py` | Read SQX's own history files without SQX: a tick feed (`*_TICK.dat`, delta-coded ask/bid) folded minute by minute into spread and bid — 650 M gold ticks in 25 s, never held — and an M1 feed (`*_M1.dat`) into bars, for feeds the bar library lacks | `.dat` → frame |
| `barstore.py` | The bar library: M1 is the only bar data stored, every other timeframe is resampled from it on first use and cached under the M1's fingerprint | feed, timeframe → frame |
| `tradestore.py` | The trade library: one typed Parquet per export, carrying only the columns that cannot be derived back, and the guard that decides when `Ticket` still has to be kept | CSVs → Parquet → frames |
| `tradepack.py` | Packs one export's CSVs into that Parquet: parsed across processes, spilled per strategy and written a strategy at a time, so 500 × 9 markets is never one frame | CSVs → Parquet |
| `fanout.py` | Independent tasks across forked processes, the costliest first (LPT), one BLAS thread each, never more processes than physical cores, results as they land | tasks + costs → results |
| `cfx.py` | Read a `project.cfx`: task chain, output databanks, acceptance conditions | project → dicts |
| `worker.py` | Start, stop and command a headless worker over its HTTP API; every call takes the role, conductor by default, and goes through `bin/sqx-worker.sh`'s owner lock (OPEN.md §32). `holding()` reports which PIDs run out of an install, the guard every write to a live install must pass; `lock()` reads who holds the owner lock, read-only | command, role → reply |
| `exportdrv.py` | The three exports SQX offers: trades, databank metrics, bars | request → files |
| `manifest.py` | Write and read the `manifest.json` every export must carry | facts → JSON |
| `assetdata.py` | What `assets/` declares: costs and windows resolved against the shared policy | symbol → dict |
| `assetranges.py` | The MC Retest spread and slippage ranges of one asset in SQX's points: a bound the asset declares as written, a null one as `_policy.yaml`'s default multiple of the cost the backtest runs at, with the source said | asset dict → {spread, slippage: {min, max, source}} |
| `assetoverride.py` | Temporary, one-run overrides of the build doctrine `assetdata.doctrine()` reads — a run-wide precision or MC Retest count for one project, by an env var, never a `_build.yaml` edit | env var → doctrine tree |
| `assetcheck.py` | What is missing or wrong about an asset: undecided values, and windows the data cannot fill | dict → problems |
| `assetyaml.py` | The `assets/` YAML files read and written without losing a comment: the round trip, and every editable value of a file with what the file itself says about it | file → leaves |
| `assetwrite.py` | The only writer of `assets/`: one value, one cost with its `why`, or a whole asset into the library or onto the retired shelf | change → file |
| `assets.py` | The preflight read out loud, with the feed-quality warning the last `studies.data.feedQuality.scan` left for the asset's feeds; `python3 -m core.assets <SYMBOL>` | symbol → report |
| `commission.py` | Converts a broker's own $/lot or % figure into a % of notional at today's price (`commission_pct`), refreshes every asset's confirmed brokers' `pct_now` from the latest close (`python3 -m core.commission --refresh`, weekly), and hands it to step 26 and `weeklyReconciler` (`broker_pct`) — never to an SQX workflow task, which prices at `costs.commission.use` instead | brokers, feed → `pct_now` per broker |
| `significance.py` | Could this edge be zero: Sharpe and its shape, the variance factor both formulas below share, the Probabilistic Sharpe Ratio and the minimum track-record length | returns → probabilities |
| `symbols.py` | `alias(symbol)`: the short market name shown on screen for a full SQX symbol (`USDJPY_M1` → `USDJPY`) — an override in `assets/_aliases.yaml`, else the ticker before the first underscore | symbol → short name |

Three rules specific to this folder:

- **No absolute path may appear anywhere but `paths.py`.** `tools/checks.py` enforces it.
- These modules read and drive SQX, they do not analyse. Maths belongs in a phase folder —
  **with one carve-out, `significance.py`**, taken deliberately on 2026-09-18. `studies/CLAUDE.md`
  says a helper two studies need is copied and promoted here when a third one wants it, and PSR is
  now wanted by three. It was written twice already, and the `1 - skew·SR + (kurt-1)/4·SR²` factor
  appearing in two files is a correctness risk, not a typing one: a fix to one copy leaves the other
  quietly wrong. Nothing else statistical joins it without clearing the same bar — three consumers,
  and a formula whose divergence would be silent.
- **`significance.py` uses `ddof=1` and that is not SQX's convention.** SQX's own `StandardDev` is
  the population deviation, `ddof=0` (measured against its stored level tables, 2026-09-18). The two
  live side by side on purpose: a reconstruction that has to reproduce a number SQX stored uses
  `ddof=0`, and an inference about a sample uses `ddof=1`. Do not harmonise them.
