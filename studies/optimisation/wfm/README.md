# studies/optimisation/wfm — re-optimised, does it win on the stretch nobody looked at?

SQX's Walk-Forward Matrix re-optimises a mother over a sliding window and runs each pick forward,
for 30 cells of *how many runs* x *what % of the optimisation window is out of sample*. Its window
is `build..oos2`, so 67–79 % of each cell's out-of-sample is data the build and step 8 already
used. **This study judges on the trades that CLOSE in `oos2` only**, re-charged at `oos2`'s costs
(specification: the owner's «criterios paso 19», 2026-10-07). It never talks to SQX.

```
config.yaml ─▶ inputs ─▶ measure ─────────────────▶ verdict ─▶ tabs, many ─▶ report
 every knob    export,    net excess per trade,     pasa /     the result,
               asset,     weekly oos2 panel, L1,    limbo /    `facts` for
               costs      L2, redundancy, area      no_pasa    the autopilot
```

| folder | the question it answers | read its README before |
|---|---|---|
| `inputs/` | what did SQX store, at whose costs, and what is missing? | touching a column name |
| `model/` | when does each cell's out-of-sample run? | touching the windows |
| `measure/` | what are the numbers? | touching the excess, the null or the area |
| `verdict/` | what do they mean? | moving a rule |

| file | what it does | run it |
|---|---|---|
| `run.py` | One export's whole reading: per mother `one()` (weekly panel, L1, L2, redundancy, per-segment excess, what was re-charged), `area()` (SQX's rule on the corrected score), `facts()` (the frozen fact names) and `read()` | imported |
| `many.py` | `one()`: one mother alone, the same member the whole run gives it (its seed is its place among the export's names). `run()`: the export as one result and each mother's own. A member carries `facts` beside the contract's keys | imported — the window reads it |
| `tabs.py` | The tabs of one mother: L1 against its null band with the cells' heat map and the annotations, L2, the drift, the per-segment table | imported |
| `contract.py` | SQX's pass/fail matrix on the corrected score with the fixed «67–79 % seen» warning, the cells' equity, and one chart per cell against the original (`celda` selector) | imported |
| `objectives.py` | The «Los objetivos» tab: one matrix per condition against its threshold, then stability, the WF specials and SQX's parameter stability | imported |
| `labels.py` | The Spanish name and one-sentence meaning of every objective | imported |
| `report.py` | The command: `reports/<P>/<D>/<day>/wfm/` with `verdict.csv`, `cell_excess.csv`, `distribuciones.parquet` (the L1 and L2 nulls; a `--strategy` run merges its mother's rows in), the page and one per mother. `--strategy` writes only that mother's `estrategias/` files | `python3 -m studies.optimisation.wfm.report --project <P> --databank WFM [--strategy "Strategy 1.19.29"]` |
| `tooltips.py` | One sentence per `config.yaml` knob, for the window's configuration drawer | imported |
| `config.yaml` | Every tunable; the thresholds are `ledger:` rows under `wfm.` | edited, or `--set section.key=value` |

## What decides, and what is only written down

- **L1 decides.** Median over the 30 cells of net excess per year in oos2, against a weekly
  shared-sign flip null (`engines.weekly.flip`, B per mother, one sign per week for all cells).
  `no_pasa` when p− <= alpha; `limbo` when the median is <= 0 without that; else `pasa`
  («reoptimizar gana» when p+ <= alpha, «no descarta» otherwise).
- **`modo_real: reoptimizado`** adds two rules that can only give `limbo` — the centre cell's excess
  <= 0, L2's p− <= alpha — and the facts `reopt.*`. In `fijo` (default) they do not exist.
- **Annotated, never judges:** L2, share of cells positive, effective cells, SQX's area on the
  corrected score, parameter drift, each cell's excess per segment, the weekly skewness.

## What a reader must know about the numbers

- **Re-charge.** 🔬 The reference export reprices at **oos1**'s costs on build and on oos1 to 0.21
  USD a trade, so the whole task was charged at oos1 (`recharge.charged`). Trades closing in oos2
  pay on top lots x point value x (Δspread + 2 Δslippage) + Δcommission. First order: no stop or
  target is moved, no tick rounding. build and oos1 in the per-segment table are NOT re-charged.
- **Excess** = SQX's P/L − re-charge − `tradelevel.drift_term` under the gate's drift block (read
  from `studies/screening/gate/config.yaml`). Not `engines.weekly.panel.per_trade`: `reprice.real`
  refuses the cells' `EndTest` trades, closed off the bar grid.
- **L2's reference in `fijo` is the weekly cross-cell median series**; its sum is not the median of
  the cells' sums that L1 reads, so L1 − mother != L2's delta.
- **Effective cells** read ~25, not 30, for truly independent cells on 143 weeks.
- **`Fitness` is zero on every step**, and steps running past the end of the data are dropped
  (`read.drop_future`).

## Open questions for the owner (`POSSIBLE_IMPROVEMENTS.md`)

L2's reference; the null's lower tail on skewed weeks (`null.skew_warn` is provisional); the drift
definition inside the excess; re-charging without moving stops.

## What it found (2026-10-07, Trade_NIKKEI225_M30_volatilidadL, 10 mothers, modo fijo)

4 pasa (all «no descarta»), 5 limbo, 1 no_pasa (`Strategy 18.5.355`, L1 −6,505 USD/year, p− 0.004).
Effective cells 1.4–4.1 of 30. Corrected area: 89 of 300 cells pass, 2 mothers find the 4x4.
3 s per mother.
