# wfm/inputs — what the study is run on

| file | what it does | in → out |
|---|---|---|
| `config.py` | Reads `config.yaml`, fills its `ledger:` references and locates one WFM export under the data root | project, databank → settings, path |
| `export.py` | Reads a WFM export: cells, steps, chosen parameters, every trade tagged by cell and sample, each cell against each condition, the mother's own trades (`main.parquet`), the objectives, and the area rule each strategy ran with | export folder → frames |
| `asset.py` | The asset behind the export's feed: bars, the three segments' days, the costs the export was charged with and oos2's, and the gate's drift block | feed, timeframe, charged segment → dict |

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
