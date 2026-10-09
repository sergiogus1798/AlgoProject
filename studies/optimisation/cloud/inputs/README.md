# cloud/inputs — what the map is drawn with

| file | what it does | in → out |
|---|---|---|
| `config.py` | The module's `config.yaml` with its ledger numbers, plus the WFC's inside trade floor | — → settings |
| `cloud.py` | `measured`: every returned variant with its parameters and its excess per year, profit and trades on build and on oos1. `screen`: controls out, the inside floor, exact duplicates out, each counted | `manifest.parquet`, `variant_trades.parquet` (legs build and oos1 only), `metrics.parquet` (`variant_id` only) → cloud, counts |

Fits nothing and judges nothing.

**oos2 is never asked for.** The trades are read with a filter on `leg` that pyarrow applies before a
row is loaded, `manifest.parquet` holds no result at all, and of `metrics.parquet` only the
`variant_id` column is read (which variants SQX returned).

**The mother is never dropped.** She is not a control, a floor she fails is not applied, and of a
group of exact duplicates she is the copy kept.
