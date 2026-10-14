# marketSurfaces/inputs — what the study is run on

| file | what it does | in → out |
|---|---|---|
| `batch.py` | A variant batch's trades on every market as weekly excess, gross and net, one leg at a time. | `metrics.parquet`, `variant_trades.parquet`, `segments.parquet`, bars → panels |
| `config.py` | Read this study's config.yaml, beside the panel floors it shares with the WFC and the CSCV. | — → settings |
| `markets.py` | The markets `assets/_markets.yaml` declares for an asset: category, first date, group and weight. | `assets/` → table |

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
