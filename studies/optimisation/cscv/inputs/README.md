# cscv/inputs — what the study reads

| file | what it does | in → out |
|---|---|---|
| `config.py` | The study's `config.yaml` with the ledger's thresholds filled in and `--set` applied | overrides → cfg |
| `batch.py` | The batch's `variant_trades.parquet` priced into weekly net and gross excess (cached as `cscv_weekly.parquet`, keyed by the trades file, costs, drift and window), each variant's trade count and fingerprint, and the screen that decides who enters | batch folder → cells; metrics, info → kept ids, counts |

The cache lives beside the batch, in the data root. **Must never hold**: a statistic of the panel.
