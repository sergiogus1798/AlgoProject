# core — shared library

Everything that more than one phase needs. Import it as a package from the project root; scripts that
live deeper add the root to `sys.path` in their first lines.

| file | what it does | in → out |
|---|---|---|
| `paths.py` | The only module that knows where anything lives. Reads `config/machine.yaml` | names → `Path` |
| `sqxfile.py` | Read a `.sqx` without SQX: identity hash, symbol, inner XML, parameters | `.sqx` → values |
| `optprofile.py` | Read a `.sqx`'s Sys. Param Permutation profile without SQX: run counts, per-metric medians against the original value, the stored histograms, and every permutation's parameters and statistics when SQX kept them | `.sqx` → dicts |
| `sqxstats.py` | Read a `.sqx` result without SQX: decode any `SQStats` blob into its 152 statistics, the stored metrics per sample, and the daily equity curve | `.sqx` → metrics, series |
| `wfmatrix.py` | Read the Walk-Forward Matrix a WFM cross-check leaves in a `.sqx`: the axes, the 30 cells, and every cell's walk-forward steps with their windows, chosen parameters and paired IS/OOS statistics | `.sqx` → dicts |
| `wftrades.py` | Cut a `data=all` export into one block per matrix cell and tag every trade with its walk-forward step, checked against the counts SQX stored | CSV → frames |
| `trades.py` | Read an `orderstocsv` export: times parsed, unfilled orders dropped, one frame per market, cost and MAE/MFE recovered | CSV → frames |
| `bars.py` | Read an OHLC export into a frame indexed by bar open time | CSV → frame |
| `cfx.py` | Read a `project.cfx`: task chain, output databanks, acceptance conditions | project → dicts |
| `worker.py` | Start, stop and command the headless worker over its HTTP API | command → reply |
| `exportdrv.py` | The three exports SQX offers: trades, databank metrics, bars | request → files |
| `manifest.py` | Write and read the `manifest.json` every export must carry | facts → JSON |
| `assets.py` | Load per-asset overrides; `python3 -m core.assets <SYMBOL>` is the preflight | symbol → report |

Two rules specific to this folder:

- **No absolute path may appear anywhere but `paths.py`.** `tools/checks.py` enforces it.
- These modules read and drive SQX, they do not analyse. Maths belongs in a phase folder.
