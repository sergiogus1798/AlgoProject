# cscv/inputs — what the study reads

| file | what it does | in → out |
|---|---|---|
| `batch.py` | A variant batch as the CSCV's cells: weekly excess per variant, net and gross, cached beside the batch. | batch folder → cells; metrics, info → kept ids, counts |
| `config.py` | Read this study's config.yaml, its `ledger:` references filled. | overrides → cfg |

The cache lives beside the batch, in the data root. **Must never hold**: a statistic of the panel.
