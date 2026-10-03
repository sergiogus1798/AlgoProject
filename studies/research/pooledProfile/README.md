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
| `config.yaml` | Every knob: timeframes, workers, the memory budget in bytes, how assets are grouped, the least assets per test, the FDR, the placebos | edited, or `--set section.key=value` | — |
| `tooltips.py` | One Spanish sentence per knob | imported | — |
| `inputs.py` | **Configuration.** The config with the profile's own under `profile` (clock measures left out); the groups; a group's build bars on their shared instants | imported | group → bars |
| `pooled.py` | **Modelling.** The group statistic: each asset's z against its own draws, summed over the root of the count (Stouffer), on the real series and on every joint draw; the p; the placebo p-values | imported | z, draws → statistic, p |
| `shrink.py` | **Modelling.** Random effects (DerSimonian-Laird): the group's mean, the spread between assets, each asset's effect shrunk by its own error | imported | effects, errors → shrunk |
| `one.py` | **Execution.** One asset of a group: `marketProfile.one.against_null` with a generator seeded by group and timeframe, so every asset draws the same positions; the money and the error of each measure | imported | bars → rows, draws |
| `many.py` | **Inference.** A group's tests; Benjamini-Hochberg over every group test; the profile's other three filters on the shrunk effect; the placebos; the board cells a passing group would bring | imported | cells → tests, assets, board, placebo |
| `store.py` | `AlgoData/research/pooled/`: per asset its rows and null draws, the seed, the tables | imported | — |
| `ledgerrows.py` | One ledger row per group test, contract L1, into the study's own `ledger.jsonl` | imported | tests → ledger rows |
| `contract.py` | The result as the study contract | imported | judged → result dict |
| `report.py` | **The command**: measures the assets not stored yet, judges every group, counts the board cells | `python3 -m studies.research.pooledProfile.report [--judge-only] [--force]` | bars → tables |

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
