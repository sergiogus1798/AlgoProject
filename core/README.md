# core — shared library

Everything that more than one phase needs. Import it as a package from the project root; scripts that
live deeper add the root to `sys.path` in their first lines.

| file | what it does | in → out |
|---|---|---|
| `__init__.py` | Runs before anything else here: makes stdout/stderr able to print this project's own text. | — |
| `assetcheck.py` | What is missing or wrong about an asset: undecided values, and windows the data cannot fill. | dict → problems |
| `assetdata.py` | What assets/ declares: costs resolved against the shared policy, checked against the class. | symbol → dict |
| `assetmarkets.py` | The retest universe `assets/_markets.yaml` declares, and the cross-asset notes in `assets/special/`. | symbol → dict |
| `assetoverride.py` | Temporary, one-run overrides of the build doctrine — never a `_build.yaml` edit. | env var → doctrine tree |
| `assetranges.py` | The MC Retest spread and slippage ranges of one asset, in the points SQX takes. | asset dict → {spread, slippage: {min, max, source}} |
| `assets.py` | The preflight every project needs: one asset read out loud, and the index of all of them. | symbol → report |
| `assetyaml.py` | The assets/ YAML files read and written without losing a comment — the only round-trip here. | file → leaves |
| `bankfile.py` | Read an `.abk`: one databank as the AlgoBank snippet wrote it from SQX's memory. | `.abk` → dict, frame |
| `bankframes.py` | An `.abk` loaded by `core.bankfile`, as the strategies' XML, statistics and daily equity. | dict → frame |
| `barstore.py` | The bar library: M1 is the only bar data stored, every other timeframe is resampled from it. | feed, timeframe → frame |
| `buildfilters.py` | The Build's acceptance filters for one asset and timeframe, resolved from assets/_study.yaml. | asset dict + timeframe + mode → the conditions to write |
| `cfx.py` | Read a project.cfx without SQX. It is a ZIP holding config.xml plus one XML per task. | project → dicts |
| `commission.py` | Each broker's own commission as a %, refreshed weekly from the latest close. | brokers, feed → `pct_now` per broker |
| `datapaths.py` | The data root's secondary trees: template library, pipeline, permutations, logs, backups, caches, spread. | names → `Path` |
| `exportdrv.py` | What leaves SQX through the worker: trades, and the symbol list (metrics are read off the .sqx). | request → files |
| `fanout.py` | Independent tasks across processes, the costliest first, each result handed back as it lands. | tasks + costs → results |
| `fleetpaths.py` | Where the live MT5 fleet's files are, and each account's plan from machine.yaml. | → `Path`, dict |
| `fsio.py` | The one atomic writer: a file is whole or it is not there, whoever reads it meanwhile. | — |
| `identities.py` | `sqxfile.identity` of many files across processes, the hashes kept in this process's cache. | files → identities |
| `manifest.py` | Every export writes one of these. Without it an export cannot be reproduced or trusted. | facts → JSON |
| `metrics.py` | The one definition of Sharpe, drawdown, profit factor and years that every step, the window and MT5 share. | returns, P&L, curves → Sharpe, drawdown, PF, years |
| `optprofile.py` | Read the Sys. Param Permutation profile SQX stores inside a .sqx, without SQX running. | `.sqx` → dicts |
| `paths.py` | Every path and port in the project. The only module allowed to know where things live. | names, roles → `Path` |
| `phases.py` | Wall clock of a named sub-phase, appended to the CSV `ALGO_PHASES` names; nothing without it. | a block → one CSV row |
| `researchpaths.py` | Where the research director's pieces live under the data root. | names → `Path` |
| `significance.py` | Could this edge be zero? The Sharpe-based tests three studies now share. | returns → probabilities |
| `sqxfile.py` | Read a .sqx strategy without SQX. It is a ZIP; everything useful is in its inner XML. | `.sqx` → values |
| `sqxretest.py` | Read a Monte Carlo Retest result out of a .sqx: its simulation P/L vectors and its level table. | `.sqx` → P/L, levels, provenance |
| `sqxstats.py` | Read a .sqx result without SQX: its stored metrics and its daily equity curve. | `.sqx` → metrics, series |
| `sqxview.py` | The owner's «Export Data View» as SQStats keys: a databank's metrics with no SQX running. | `.sqx` → metrics table |
| `symbols.py` | The short name a market is called by on screen, from its SQX symbol or feed name. | symbol → short name |
| `tickfile.py` | Read SQX's own history files without SQX: a tick feed into one row per minute of spread, an M1 feed into bars. | `.dat` → frame |
| `tickparallel.py` | `tickfile.read` in parallel: a walk over the record headers finds where each block starts, and jobs of whole blocks are decoded at once. | `.dat` → minute table |
| `tradepack.py` | Pack one export's CSVs into the trade library: parsed in parallel, written a few dozen strategies at a time. | CSVs → Parquet |
| `trades.py` | Read a trade list exported by SQX's orderstocsv, and the per-trade quantities derived from it. | CSV → frames |
| `tradestore.py` | The trade library: one Parquet per export, holding only what cannot be derived back. | CSVs → Parquet → frames |
| `uitoken.py` | The ui daemon's session token: minted by `ui.daemon.serve`, kept in a 0600 file under the data root, read by every client. | port → token |
| `wfmatrix.py` | Read the Walk-Forward Matrix a WFM cross-check leaves inside a .sqx, without SQX running. | `.sqx` → dicts |
| `wfmobjectives.py` | SQX's Walk-Forward Matrix objectives per cell — stability, score, the WF specials — and its rule. | `.sqx` root → rule, rows per cell and condition |
| `wftrades.py` | Assign the trades of a data=all export to the Walk-Forward cell and period that produced them. | CSV → frames |
| `worker.py` | Drive the headless worker install. The master's CLI is dead while its GUI is up. | command, role → reply |
| `xmlget.py` | Typed reads of an XML tree whose layout is known: the element, attribute or text is there or the read fails. | — |
| `assetwrite/` | The only writer of `assets/`: one value, one cost with its `why`, or a whole asset into the library or onto the retired shelf | change → file |
| `archive/` · `store/` · `study/` · `surface/` | Subpackages, each with its own `README.md`: the strategy archive (frozen `.sqx`, cosecha rows and study results) · the strategy store (a strategy that passed the gate saved the moment it passes) · the contract every study speaks (`CONTRACT.md`) · the maths of a parameter grid | see each README |

Three rules specific to this folder:

- **No absolute path may appear anywhere but `paths.py`.** `tools/checks.py` enforces it.
- These modules read and drive SQX, they do not analyse. Maths belongs in a phase folder —
  **with two carve-outs, `significance.py`** (2026-09-18) **and `metrics.py`** (2026-10-16, encargo 75: thirteen copies of Sharpe, drawdown and PF had drifted apart in the flat and no-loss cases; it sits in `core/` because `significance.py` and `sqx/variants/united.py` call it and neither may import `engines/`). `studies/CLAUDE.md`
  says a helper two studies need is copied and promoted here when a third one wants it, and PSR is
  now wanted by three. It was written twice already, and the `1 - skew·SR + (kurt-1)/4·SR²` factor
  appearing in two files is a correctness risk, not a typing one: a fix to one copy leaves the other
  quietly wrong. Nothing else statistical joins it without clearing the same bar — three consumers,
  and a formula whose divergence would be silent.
- **`significance.py` uses `ddof=1` and that is not SQX's convention.** SQX's own `StandardDev` is
  the population deviation, `ddof=0` (measured against its stored level tables, 2026-09-18). The two
  live side by side on purpose: a reconstruction that has to reproduce a number SQX stored uses
  `ddof=0`, and an inference about a sample uses `ddof=1`. Do not harmonise them.
