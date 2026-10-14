# cloud/inputs — what the map is drawn with

| file | what it does | in → out |
|---|---|---|
| `cloud.py` | The cloud this study reads: each variant's parameters and its excess per year, on build and on oos1. | `manifest.parquet`, `variant_trades.parquet` (legs build and oos1 only), `metrics.parquet` (`variant_id` only) → cloud, counts |
| `config.py` | The study's knobs. | — → settings |

Fits nothing and judges nothing.

**oos2 is never asked for.** The trades are read with a filter on `leg` that pyarrow applies before a
row is loaded, `manifest.parquet` holds no result at all, and of `metrics.parquet` only the
`variant_id` column is read (which variants SQX returned).

**The mother is never dropped.** She is not a control, a floor she fails is not applied, and of a
group of exact duplicates she is the copy kept.
