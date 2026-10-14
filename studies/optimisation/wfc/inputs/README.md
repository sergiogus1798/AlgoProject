# wfc/inputs — what the study is run on

| file | what it does | in → out |
|---|---|---|
| `batch.py` | A variant batch's trades on the main market as excess, net and gross, trade by trade and leg by leg. | `variant_trades.parquet` → per-trade frames, prints |
| `config.py` | Read this study's config.yaml, beside the batch-reading knobs it shares with the CSCV. | — → settings |

Holds nothing computed beyond that pricing.
