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
| `analytic.py` | The normal approximation of the profile's power: what a t statistic can see, from its error. | imported | measure rows → error, power, mde |
| `contract.py` | The power study as the study contract: what the window and the page draw. | imported | tables → result dict |
| `inputs.py` | What the power study is run on: its config, the profile's, the cut-off, and a cell's bars. | imported | cell → bars, cost |
| `ledgerrows.py` | The power study's looks at the data, as rows of the ledger's contract L1. | imported | rows → ledger rows |
| `many.py` | The replications judged: detection per planted effect, and the minimum detectable effect. | imported | rows → curve, mde |
| `one.py` | One replication: a directionless copy of a cell, an edge planted in it, the profile's test. | imported | key + bars → one row |
| `plant.py` | The planted edge: which bars carry it, and the series with it added. | imported | series + trades → series |
| `report.py` | The command: how small an edge the market profile can see — planted, tested, and widened. | `python3 -m studies.research.profilePower.report [--set run.cells=[USOIL/H1]] [--judge-only] [--force]` | bars + the map → tables |
| `store.py` | Where the power study lives on disk: the replications, and the judged tables. | imported | — |
| `tooltips.py` | One sentence per config.yaml knob, for the window's configuration drawer. | imported | — |
| `config.yaml` | Every knob: the cells, the plant (how, effects, replications, measures), the judge (cut, chunk, single level, power) and the memory budget in bytes | edited, or `--set section.key=value` | — |

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
