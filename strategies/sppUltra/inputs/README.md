# sppUltra/inputs — what the study is run on

| file | what it does | in → out |
|---|---|---|
| `config.py` | Reads `config.yaml` and locates one SPP export under the data root | project, databank → settings, path |
| `export.py` | Turns the five CSVs of an SPP export into one grid: parameters wide, statistics beside them | export folder → frame, names, original tuple |

Holds nothing computed. Every number in this study comes from `model/` or `verdict/`.

## Traps in this export

- **The original strategy is permutation `-1`** in `permutation_params.csv` and has **no row** in
  `permutations.csv`. `grid()` inner-joins, so it drops out; `original()` reads it on its own. It is
  the anchor the whole design is checked against, so it must never be assumed to be in the grid.
- **`runs.csv` lists the parameters the SPP permuted, not the strategy's parameters.** Anything
  absent was frozen by the SPP settings — which says nothing about whether it matters. The 12-step
  run permuted only Periods, Constants and ExitParamsUsed and froze every shift by configuration,
  and one of those shifts turned out to be the most important parameter out of sample.
- **42 of the 152 statistics are constant** across the whole grid (measured 2026-09-20). `varying()`
  drops them, because a constant column in an eta-squared table is a row of zeros pretending to be a
  measurement.
- Several dates coexist under `raw/<project>/<databank>/` on purpose — those exports are immutable.
  Which one was read is printed in the report and stored in the brief.
