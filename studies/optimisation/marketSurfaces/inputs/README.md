# marketSurfaces/inputs — what the study is run on

| file | what it does | in → out |
|---|---|---|
| `config.py` | Reads `config.yaml` and the trade floor shared with the WFC and the CSCV | — → settings |
| `surfaces.py` | The main feed and timeframe off the batch, the markets `_markets.yaml` declared, whether each one's costs are provisional, every (variant, market, segment) cell of the segments asked for, and each variant's `param_*` values (the axes of the pair grids) | `segments.parquet`, `metrics.parquet`, `assets/` → cells, surfaces |

Holds nothing computed.

**The segment filter is pushed into the Parquet read.** A reserved segment's rows are never
materialised, not read and dropped — and `report.py` asks `ledger.gate.allow` before this runs.

**The variants are the WFC's**: the rows of `metrics.parquet`, which already passed the hard floor
of 50 trades on the main market. The per-segment floor of `engines/variants/config.yaml` is then
applied per market: a cell below it is NaN for that market, never a zero.

**The markets come from `_markets.yaml`, never from the batch.** A declared market the batch lacks is
reported absent and counts as not passing; the batch's markets are only what was retested.
