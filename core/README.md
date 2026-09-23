# core — shared library

Everything that more than one phase needs. Import it as a package from the project root; scripts that
live deeper add the root to `sys.path` in their first lines.

| file | what it does | in → out |
|---|---|---|
| `__init__.py` | Puts stdout/stderr in UTF-8 on import, so Windows' cp1252 console does not crash on this project's own accents and symbols | — |
| `paths.py` | The only module that knows where anything lives. Reads `config/machine.yaml`; `WORKERS` maps a worker role (conductor, custodian) to its install and port | names, roles → `Path` |
| `templatepaths.py` | Where the strategy-template library lives under the data root: one folder per template, `registry.csv`, `runs.csv` and the dated vocabulary snapshots. Split out of `paths.py` for its line limit | names → `Path` |
| `sqxfile.py` | Read a `.sqx` without SQX: identity hash, symbol, inner XML, parameters | `.sqx` → values |
| `optprofile.py` | Read a `.sqx`'s Sys. Param Permutation profile without SQX: run counts, per-metric medians against the original value, the stored histograms, and every permutation's parameters and statistics when SQX kept them | `.sqx` → dicts |
| `sqxstats.py` | Read a `.sqx` result without SQX: decode any `SQStats` blob into its 152 statistics, the stored metrics per sample, and the daily equity curve | `.sqx` → metrics, series |
| `sqxretest.py` | Read a Monte Carlo Retest result without SQX: every simulation's P/L vector, the original it was perturbed from, the eleven-level confidence table, and the method settings that produced it | `.sqx` → P/L, levels, provenance |
| `wfmatrix.py` | Read the Walk-Forward Matrix a WFM cross-check leaves in a `.sqx`: the axes, the 30 cells, and every cell's walk-forward steps with their windows, chosen parameters and paired IS/OOS statistics | `.sqx` → dicts |
| `wftrades.py` | Cut a `data=all` export into one block per matrix cell and tag every trade with its walk-forward step, checked against the counts SQX stored | CSV → frames |
| `trades.py` | Read an `orderstocsv` export: times parsed, unfilled orders dropped, one frame per market, cost and MAE/MFE recovered | CSV → frames |
| `bars.py` | Read an OHLC export into a frame indexed by bar open time | CSV → frame |
| `barstore.py` | The bar library: M1 is the only bar data stored, every other timeframe is resampled from it on first use and cached under the M1's fingerprint | feed, timeframe → frame |
| `tradestore.py` | The trade library: one typed Parquet per export, carrying only the columns that cannot be derived back, and the guard that decides when `Ticket` still has to be kept | CSVs → Parquet → frames |
| `cfx.py` | Read a `project.cfx`: task chain, output databanks, acceptance conditions | project → dicts |
| `worker.py` | Start, stop and command a headless worker over its HTTP API; every call takes the role, conductor by default. `holding()` reports which PIDs run out of an install, the guard every write to a live install must pass | command, role → reply |
| `exportdrv.py` | The three exports SQX offers: trades, databank metrics, bars | request → files |
| `manifest.py` | Write and read the `manifest.json` every export must carry | facts → JSON |
| `assetdata.py` | What `assets/` declares: costs and windows resolved against the shared policy | symbol → dict |
| `assetcheck.py` | What is missing or wrong about an asset: undecided values, and windows the data cannot fill | dict → problems |
| `assets.py` | The preflight read out loud; `python3 -m core.assets <SYMBOL>` | symbol → report |
| `significance.py` | Could this edge be zero: Sharpe and its shape, the variance factor both formulas below share, the Probabilistic Sharpe Ratio and the minimum track-record length | returns → probabilities |

Three rules specific to this folder:

- **No absolute path may appear anywhere but `paths.py`.** `tools/checks.py` enforces it.
- These modules read and drive SQX, they do not analyse. Maths belongs in a phase folder —
  **with one carve-out, `significance.py`**, taken deliberately on 2026-09-18. `strategies/CLAUDE.md`
  says a helper two studies need is copied and promoted here when a third one wants it, and PSR is
  now wanted by three. It was written twice already, and the `1 - skew·SR + (kurt-1)/4·SR²` factor
  appearing in two files is a correctness risk, not a typing one: a fix to one copy leaves the other
  quietly wrong. Nothing else statistical joins it without clearing the same bar — three consumers,
  and a formula whose divergence would be silent.
- **`significance.py` uses `ddof=1` and that is not SQX's convention.** SQX's own `StandardDev` is
  the population deviation, `ddof=0` (measured against its stored level tables, 2026-09-18). The two
  live side by side on purpose: a reconstruction that has to reproduce a number SQX stored uses
  `ddof=0`, and an inference about a sample uses `ddof=1`. Do not harmonise them.
