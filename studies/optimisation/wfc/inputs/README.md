# wfc/inputs — what the study is run on

| file | what it does | in → out |
|---|---|---|
| `config.py` | This study's `config.yaml` over the batch-reading knobs it shares with the CSCV (`engines/variants/config.yaml`), the `ledger:` values filled in | — → settings |
| `batch.py` | The batch's trades priced as step 14's excess, net and gross (`engines/weekly/panel.per_trade`): one row per trade and leg, each variant's trade-list fingerprint over the legs read, and the level's second reading with the drift of bars before oos2; the count of live parameters. Asks `look.admit` before a segment is opened | `variant_trades.parquet` → per-trade frames, prints |

Holds nothing computed beyond that pricing.
