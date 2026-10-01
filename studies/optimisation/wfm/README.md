# studies/optimisation/wfm — does what optimises well predict what does well after?

SQX's Walk-Forward Matrix re-optimises a strategy over a sliding window and runs each pick forward
on the period that follows, for 30 combinations of *how many steps* and *how much of each step is
out of sample*. The export already existed — `sqx/export/export_wfm.py`, `core/wfmatrix.py`,
`core/wftrades.py`, `docs/manual/09-optimizacion.pdf` (cap. 09-wfm). **This is the analysis that did not.**

It never talks to SQX. The owner runs the cross-check; this reads what came out.

```
config.yaml ─▶ inputs ─▶ model ─▶ measure ─▶ verdict ─▶ many
 every knob    cells,     what the  rho per    predicts/  the report
               steps,     geometry  cell,      blind/
               picks      allows    drift      perverse
```

| folder | the question it answers | read its README before |
|---|---|---|
| `inputs/` | what did SQX actually store, and what is missing? | touching a column name |
| `model/` | what may be pooled with what? | changing the unit of observation |
| `measure/` | what are the numbers? | touching the correlation or the drift |
| `verdict/` | what do they mean? | moving a threshold |

| file | what it does | run it |
|---|---|---|
| `run.py` | One export's whole reading, including the reconstructed pass/fail matrix | imported |
| `many.py` | `one()`: one strategy alone (`run.read(only=…)` correlates, scores and bootstraps only it, the window shapes and the drift's parameter spread kept the export's), the same member the whole run gives it. `run()`: the export as one result — verdicts with each strategy's ρ grid, the window geometry, the drift, the two axes — and each strategy's own | imported — the window reads it |
| `contract.py` | One strategy's pass/fail matrix as SQX paints it — met/active per cell, the conditions on hover, ▣ best rectangle, ◆ recommended cell, checked against SQX's own mark — which condition binds, and the cells' equity with one aggregate table (encargo 37) | imported |
| `objectives.py` | The «Los objetivos» tab: one matrix per condition against its threshold, then stability, score, the WF specials and SQX's parameter stability without one | imported |
| `labels.py` | The Spanish name and one-sentence meaning of every objective | imported |
| `report.py` | The command: `reports/<P>/<D>/<day>/wfm/` with `verdict.csv`, `cell_correlations.csv`, the page and one per strategy. `--strategy` writes only that strategy's `estrategias/` JSON and page (`many.one`), never the population's files | `python3 -m studies.optimisation.wfm.report --project XAUUSD --databank WFM [--strategy "Strategy 1.19.29"]` |
| `tooltips.py` | One sentence per `config.yaml` knob, for the window's configuration drawer | imported |
| `config.yaml` | Every tunable | edited, or `--set section.key=value` |

## The three things this module exists to get right

**The cell is the unit of observation, and it is measured rather than assumed.** 🔬 Within a cell
the run windows are disjoint (0 overlaps in 60 cells); the optimisation windows overlap by 79 %; and
every cell re-splits the same history. Pooling the 660 steps into one correlation would report an
interval several times narrower than the data supports. `model/README.md` carries the figures.

**`Fitness` is zero on every step.** SQX stores it only per cell. A study that reached for the
obvious column would have correlated zeros.

**A third of the steps' honest-looking numbers are computed on data that does not exist.** 60 of
720 steps run past the end of the history — one ends in **2027**. They are dropped, and
`drop_future` exists only so the report can say so.

## What it found, first run (2026-09-21, XAUUSD/WFM 2026-09-10)

| strategy | verdict | rho (95 % over cells) | drift |
|---|---|---|---|
| `Strategy 1.19.29` | **blind** | +0.076 [−0.034, +0.193] | 70 % |
| `Strategy 4.33.46` | **perverse** | −0.505 [−0.683, −0.339] | 78 % |

Neither strategy's in-sample optimisation predicts its own out-of-sample result, and for `4.33.46`
it predicts it **backwards**, on all four metrics read, with 93 % of its cells negative. Meanwhile
the optimiser re-decides 70–78 % of the parameters at every step.

Those two facts are one finding: a surface with no out-of-sample signal has nothing holding the
optimiser in place. Read `POSSIBLE_IMPROVEMENTS.md` before drawing a conclusion wider than this
export supports — two strategies is two strategies.
