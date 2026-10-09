# marketSurfaces/inputs — what the study is run on

| file | what it does | in → out |
|---|---|---|
| `config.py` | Reads `config.yaml`, fills the `ledger:` thresholds and adds the trade floors shared with the WFC and the CSCV (`panel`) | — → settings |
| `markets.py` | The markets `assets/_markets.yaml` declares for the asset — feed, category, `data_from`, `near_identical` group — and whether a market's cost card is provisional | `assets/` → table |
| `batch.py` | The batch's design (`variants`), each market's trades repriced into weekly gross and net excess per leg (`one`, fanned out by `read`), the legs' bounds and lengths, and consecutive legs as one panel (`stacked`) | `metrics.parquet`, `variant_trades.parquet`, `segments.parquet`, bars → panels |

Holds nothing computed beyond the repricing, which is `engines.weekly.panel`'s.

**A leg that is not named is never opened.** The leg and market filters are pushed into the Parquet
read, and `report.py` asks `engines.variants.look.admit` before this runs.

**The markets come from `_markets.yaml`, never from the batch.** A declared market the batch lacks
has no common variant, stays out of the mean and is reported absent.

**`near_identical`** is an optional key of an asset's block, beside `categories`: a list of lists of
feeds that are nearly the same market. Its members share one weight (`measure/order.weights`). Every
other reader of the file takes `categories` only.

**The drift is the gate's** (`studies/screening/gate/config.yaml`, `drift`), read from its file: a
path, not an import of that study.
