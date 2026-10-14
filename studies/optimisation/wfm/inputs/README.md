# wfm/inputs — what the study is run on

| file | what it does | in → out |
|---|---|---|
| `asset.py` | The asset a WFM export traded: its bars, its three segments, the two cost cards and the drift term. | feed, timeframe, charged segment → dict |
| `config.py` | Read config.yaml and find the WFM export on disk. | project, databank → settings, path |
| `export.py` | Read a WFM export: the 30 cells, their steps, and the parameters the optimiser chose. | export folder → frames |

Holds nothing computed.

## Traps in this export

- ⚠️ **The task is charged at ONE segment's costs throughout** (`wfm.costs_segment` in
  `assets/_build.yaml`, oos1). `recharge.charged` must say the same; verify on a new export by
  repricing the mother's build trades before trusting it.
- ⚠️ **Cells end with `EndTest` trades closed off the bar grid** (103 in the reference export):
  `engines.market.reprice.real` refuses them.
- ⚠️ **`is_Fitness` and `oos_Fitness` are zero on every step.** SQX stores fitness only per cell.
- ⚠️ **The last step of a cell can run past the end of the data** (`future=True`). `steps()` drops
  them and `drop_future: false` should never be set.
- **Mothers do not share a parameter list**, so `chosen()` carries all-NaN columns per mother;
  `oos_pct` and `runs` in `params.parquet` are the cell's coordinates, not parameters, and are left out.
- **`all_<metric>` is the first optimisation window plus the out-of-sample**, and SQX's `score`
  condition is built on it (`measure/gaterule.oos_only` undoes that).
- **What the optimiser rejected is not stored.** Only its pick per step survives.
- An export older than 2026-10-01 has no `main.parquet` nor `conditions.parquet`: `run.read` refuses it.
