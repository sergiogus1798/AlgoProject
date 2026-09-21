# walkForwardMatrix/inputs — what the study is run on

| file | what it does | in → out |
|---|---|---|
| `config.py` | Reads `config.yaml` and locates one WFM export under the data root | project, databank → settings, path |
| `export.py` | Reads the four CSVs of a WFM export: cells, steps, chosen parameters | export folder → frames |

Holds nothing computed.

## Traps in this export

- ⚠️ **`is_Fitness` and `oos_Fitness` are zero on every step.** SQX stores fitness only at cell level
  (`fitness_is` / `fitness_oos` in `cells.csv`). A study reading `Fitness` per step correlates
  zeros and reports a NaN — or worse, silently reports something. `config.yaml` names a real metric
  and says why.
- ⚠️ **The last step of every cell runs past the end of the data.** Measured 2026-09-10: cell 6x20
  of `Strategy 1.19.29` ends with a step running 2025-12-31 to **2027-08-20**, and 60 of the 720
  steps carry `future=True`. `steps()` drops them by default and `drop_future: false` should never
  be set.
- **The two strategies do not share a parameter list**, so the wide frame from `chosen()` carries
  all-NaN columns per strategy. `NaN != 0` is True, so anything comparing steps must drop them
  first or it counts a parameter the strategy does not have as changed at every step.
- **Of the 152 columns per sample, 42 to 46 are constant** across the whole export.
- **What the optimiser rejected is not stored.** Only its pick per step survives, so nothing here
  can say how close the runner-up was, or how flat the surface it chose from was.
