# parameterCloud/inputs — what the study is run on

| file | what it does | in → out |
|---|---|---|
| `config.py` | Reads the module's `config.yaml`, the single place every knob lives | — → settings |
| `cloud.py` | The metric panel narrowed to what may be described, and the per-day curves | `metrics.parquet`, `equity.parquet` → cloud, curves |

Holds nothing computed.

**The canaries are dropped and the origin never is.** The four known-result canaries were placed at
the extremes of the grid on purpose, to make a broken chain obvious; a study that leaves them in
reads a rougher surface and a better origin rank than the design actually produced. The origin
survives every filter including `min_trades`, because where it sits is the question.

**Fewer curves than panel rows is normal.** 962 of 2,000 on `Strategy 17.9.39`: a batch is
fabricated larger than what comes back off the custodian, and `equity.parquet` only holds what came
back. Every per-period reading says how many columns it actually had.
