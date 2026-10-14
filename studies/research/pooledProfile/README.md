# pooledProfile — the profile's measures judged per group of assets, jointly resampled

The profile (`../marketProfile/`) judges every measure on one asset; a rule that makes 3-12
trades a year there cannot be seen (`../profilePower/`). This study asks the same measures of a
**group** — asset class × timeframe × direction × measure: one combined statistic against a null
that resamples the group's assets **jointly in time**, and each asset's effect shrunk towards its
group's mean. The measures, the null, the block, the draws and the four filters are the
profile's own, read from its config.

**It reads only the `build` segment**: every asset enters through `marketProfile.inputs.cut`, and
a group is judged on the bar times all its assets share (`inputs.shared`);
`tests/test_pooledprofile.py` poisons the bars after the build end.

| file | what it does | run it | in → out |
|---|---|---|---|
| `contract.py` | The pooled profile as the study contract: what the window and the page draw. | imported | judged → result dict |
| `inputs.py` | What the pooled profile is run on: its config, the groups, and each group's shared bars. | imported | group → bars |
| `ledgerrows.py` | The pooled profile's looks at the data, as rows of the ledger's contract L1. | imported | tests → ledger rows |
| `many.py` | Every group judged together: the correction, the shrunk effects, the placebos, the board. | imported | cells → tests, assets, board, placebo |
| `one.py` | One asset of a group: every measure on its bars and on the group's joint null draws. | imported | bars → rows, draws |
| `pooled.py` | The group statistic: every asset's standardised measure added up, real and under the null. | imported | z, draws → statistic, p |
| `report.py` | The command: the market profile's measures judged per group of assets, jointly resampled. | `python3 -m studies.research.pooledProfile.report [--judge-only] [--force]` | bars → tables |
| `shrink.py` | Random effects: each asset's effect pulled towards its group's mean by how noisy it is. | imported | effects, errors → shrunk |
| `store.py` | Where the pooled profile lives on disk: one file pair per asset of a group, and the tables. | imported | — |
| `tooltips.py` | One sentence per config.yaml knob, for the window's configuration drawer. | imported | — |
| `config.yaml` | Every knob: timeframes, workers, the memory budget in bytes, how assets are grouped, the least assets per test, the FDR, the placebos | edited, or `--set section.key=value` | — |

Manual page, in Spanish: chapter `92-perfil-agrupado` of `AlgoData/manual-fuentes/`.

## The owner's readings (2026-10-02)

- **Groups**: the four asset classes of `../memory/config.yaml` (forex 10, index 5, metal 2,
  energy 2). Finer groups are proposed only if the heterogeneity (`tau`, `i2`) asks for them.
- **Direction is the instrument's**: long USDCHF and long EURUSD are in the same group test.
- **The board's gate is not touched.** `board.csv` counts the cell-families a passing group
  would bring by two routes — every tested asset of the group (loose), or only those whose
  shrunk effect pays, is stable and is frequent (strict) — and which are not on the board today.

## What it writes — `AlgoData/research/pooled/`

| file | one row per | columns |
|---|---|---|
| `cells/<group>_<tf>_<symbol>.parquet`, `.npy` | measure × direction of one asset; its null statistics (draws × tests, float32) | the profile's row plus `se`, `tested`, the shared window |
| `tests.csv` | group × timeframe × direction × measure | `assets`, `stat`, `p`, `q`, `significant`, `mean_excess`, `tau`, `i2`, `trade` |
| `assets.csv` | the same × asset | `z`, `p` (alone), `multiple`, `excess`, `se`, `shrunk_excess`, `shrunk_multiple`, `significant_alone`, `pays`, `pays_shrunk`, `stable`, `frequent`, `strict` |
| `board.csv` | cell-family an asset of a passing group test would bring | `measures`, `strict`, `alone`, `best_shrunk_multiple`, `new` |
| `pooled.json`, `.html`, `.md` | the study contract | — |
| `seed.json`, `ledger.jsonl`, `run.json` | the root of the joint draws; the looks at the data; the last run | — |

## The decisions the code takes

- **Joint resampling is a shared seed on a shared clock.** Each asset is cut to the bar times
  every asset of its group has, so the group's assets have the same number of bars; the
  generator is seeded by group and timeframe, so `against_null` draws the same positions for
  each. Bar k is the same instant everywhere and one draw moves the whole group together.
- **The group's window is the overlap of its assets' build windows** (index: 2013-09 → 2020,
  76-95 % of each asset's bars; forex and metal 99 %).
- **The effect that is shrunk is the excess over the null**, in round-trip costs: z × the error
  of the mean gain per trade, widened by the null's spread. `shrunk_multiple` adds back what the
  null's drift already gave, so it compares with the profile's `multiple`.
- **Clock measures are left out**: they never reach the board.
- **Placebos**: the first `judge.placebos` null draws are judged as if they were the real series,
  against all the draws; the share of them in which anything is named is the false-alarm rate
  of the whole procedure with the assets' real cross-correlation.

Alternatives and limits: `POSSIBLE_IMPROVEMENTS.md`. Findings:
`knowhow/market-profile/market-profile-pooled.md`.
