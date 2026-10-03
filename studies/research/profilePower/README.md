# profilePower — how small an edge the market profile can see (positive controls)

The profile (`../marketProfile/`) says how many cells pass; nothing said how many cells **with**
an edge it would miss. This study plants an edge of known size and runs the profile's own test
on it — `marketProfile.one.against_null`, the same null, block and draws — judged at the raw p
the full map's Benjamini-Hochberg imposes today. Idea 2 of
`docs/AgentPDFs/ideas-de-edge-2026-09-26.md`; owner's readings of 2026-10-02 below.

**It reads only the `build` segment**: bars enter through `marketProfile.inputs.cut`
(`inputs.bars`); `tests/test_profilepower.py` poisons the bars after the build end.

| file | what it does | run it | in → out |
|---|---|---|---|
| `config.yaml` | Every knob: the cells, the plant (how, effects, replications, measures), the judge (cut, chunk, single level, power) and the memory budget in bytes | edited, or `--set section.key=value` | — |
| `tooltips.py` | One Spanish sentence per knob | imported | — |
| `inputs.py` | **Configuration.** The config with the profile's own under `profile`; the cut-off read from the map on disk; a cell's build bars; the round-trip cost as a log return | imported | cell → bars, cost |
| `plant.py` | **Modelling.** `PLANTS`: where the edge goes (`condition`: the bars the measure's trades hold; `random`: as many bars anywhere — the control); the planted series | imported | series + trades → series |
| `analytic.py` | **Modelling.** The normal approximation of the same test: a measure's error in costs from its t and its null spread, the power at an effect, the minimum detectable effect; applied to every trade measure of the map | imported | measure rows → error, power, mde |
| `one.py` | **Execution.** One replication: a sign-flipped copy of the cell, the edge planted in the measure's own trades, the profile's test in chunks until the cut is out of reach, and what the trades earned | imported | key + bars → one row |
| `many.py` | **Inference.** Each replication's verdicts (significant at the cut, the profile's other three filters, the single uncorrected test), the power curve, the minimum detectable effect | imported | rows → curve, mde |
| `store.py` | `AlgoData/research/power/`: the replications (kept per cut and draws, so a run resumes), the tables | imported | — |
| `ledgerrows.py` | One ledger row per cell, measure and direction, contract L1, into the study's own `ledger.jsonl` | imported | rows → ledger rows |
| `contract.py` | The result as the study contract | imported | tables → result dict |
| `report.py` | **The command**: runs the replications not stored yet, judges all, widens to the whole map with the approximation | `python3 -m studies.research.profilePower.report [--set run.cells=[USOIL/H1]] [--judge-only] [--force]` | bars + the map → tables |

Manual page, in Spanish: chapter `91-potencia-del-perfil` of `AlgoData/manual-fuentes/`.

## The owner's readings (2026-10-02)

- **Where the edge is planted**: in the returns that follow the measure's own condition (this
  tests the measure). The random-bars variant is the control, run once (`--set plant.how=random`).
- **Unit**: multiples of the cell's round-trip cost, gross; the ATR equivalent beside it.
- **Detected**: two curves — `significant` (the headline) and `passes` (all four filters) — and
  `single`, the rule judged alone at 5 % on the first chunk of draws.
- One measure per family carries the plant, plus a sparse one where the family has both kinds.

## What it writes — `AlgoData/research/power/`

| file | one row per | columns |
|---|---|---|
| `runs.parquet` | replication | the key (`symbol`, `timeframe`, `measure`, `direction`, `effect_planted`, `rep`, `how`), `exceed`, `drawn`, `draws`, `p_first`, `stat`, `null_mean`, `null_sd`, the trades' money, `cut`, `seed`, `wall_s` |
| `curve.csv`, `curve_class.csv` | family (or asset class) × measure × timeframe × effect | `runs`, the rates `significant`, `passes`, `single`, `frequent`, mean realised `multiple`, `trades_per_year` |
| `mde.csv`, `mde_class.csv` | the same without the effect | `mde_significant`, `mde_passes`, `mde_single` (costs; empty = beyond the largest effect), `alarm_*` (detection with nothing planted), `top_*` (at the largest effect) |
| `calibration.csv` | measure × timeframe × effect | simulated `detected` beside the approximation's `predicted` |
| `widened.csv` | trade measure of the map (no clock) | the map's row plus `asset_class`, `mde` (costs), `mde_atr` |
| `reach.csv`, `reach_class.csv` | family (or class) × timeframe | `tests`, `mde_median`, `mde_atr_median`, `sees_1x`, `sees_2x`, `sees_5x`: share of the map's tests that could have named an edge that size |
| `power.json`, `.html`, `.md` | the study contract | — |
| `ledger.jsonl`, `run.json` | the looks at the data; the last run | — |

## The decisions the code takes

- **The base is the cell's bars with every bar's sign tossed** (`marketProfile.series.flipped`,
  the yardstick `blocklen.py` used): the real volatility bar by bar, no direction, no drift. The
  same copies carry every measure and every effect.
- **A trade gains `effect` costs on average**: every held bar's close moves by effect × cost ÷
  mean holding time, once, however many trades overlap on it.
- **The measure is read again on the planted series**, so its entries can move; the realised
  `multiple` is stored beside the planted effect.
- **A replication stops at the first chunk after which the cut cannot be reached** — more null
  draws at or above the statistic than the cut allows at the full count. Exact, not approximate.
- **Widening is by the approximation**, calibrated against the simulation: simulating the 76
  cells would cost thousands of core-hours (a replication is 0.05-3 minutes at H1).

Alternatives and limits: `POSSIBLE_IMPROVEMENTS.md`. Findings:
`knowhow/market-profile/market-profile-power.md`.
