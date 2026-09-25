# walkForwardCorrelation

Two questions about one parameter grid, and they are not the same question.

**Does in-sample performance predict out-of-sample performance?** One point per parameter
combination, in-sample net profit against out-of-sample net profit. A cloud that fills all four
quadrants means optimising in-sample buys nothing out of sample; a cloud on the rising diagonal
means the surface carries information and the in-sample ranking is worth trusting.

**And is the way I pick parameters prone to overfitting at all?** That one is not about this
history. It splits the history 924 ways, picks by each half in turn, and counts how often the
winner came back below average — the CSCV of Bailey, Borwein, López de Prado and Zhu. It is run
once per selection rule, so the answer is not "this strategy decays" but **"choosing by plateau
centre instead of by maximum takes the PBO from 30 % to 4 %"**.

Reads contract **C3** (`metrics.parquet`, from `sqx.variants.collect`) and, for the CSCV,
`equity.parquet` (from `sqx.variants.equity`). Writes `wfc.json` and `cscv.json` beside them —
the pipeline reads their scalars, so they do not change shape — and the result the window paints
into the batch's `estudios/` folder: `wfc.*` and `cscv.*`, each `.json`, `.html` and `.md`.

```
config.yaml ─▶ inputs ─▶ measure ─▶ verdict ─▶ contract
 every knob    the panel,  rho, the    PBO, DSR,   estudios/
               the split   rules,      what each   cscv.html
                           the CSCV    rule cost
```

| folder | the question it answers | read its README before |
|---|---|---|
| `inputs/` | what is the study run on, and where does the history split? | touching the panel or the boundary |
| `measure/` | what are the numbers? | touching the rho, a selection rule or the partitions |
| `verdict/` | what do they mean? | moving a threshold or a cluster count |
| `contract/` | how is it read? — the call, the cloud and the λ per rule as the contract's blocks | adding a figure or a table |

| file | what it does | run it |
|---|---|---|
| `report.py` | The correlation | `python3 -m strategies.walkForwardCorrelation.report --work <dir>` |
| `pbo.py` | The CSCV, once per selection rule | `python3 -m strategies.walkForwardCorrelation.pbo --work <dir>` |
| `config.yaml` | The trade floor, the rho floor, and every knob of the CSCV | edited, or `--set section.key=value` |
| `tooltips.py` | One sentence per `config.yaml` knob, for the window's configuration drawer | imported |

**Twelve blocks, C(12,6) = 924 partitions, ranked by per-period Sharpe.** Those are López de
Prado's own numbers and the owner's decision of 2026-09-23; `pbo.py --blocks N` overrides the count
per run, and `cscv.score` takes `sortino` as well. What it will never take is Ret/DD — a score has
to be a rate per period to be comparable across windows, and Ret/DD grows with elapsed time.
`POSSIBLE_IMPROVEMENTS.md` §2 and §3 carry both arguments and what each choice cost.

**The interval is the point, not the coefficient.** With a dozen tuples the sampling error on a
correlation is enormous, so the study reports a band and will say `indeciso` rather than pretend.
`indeciso` means fabricate more points, not lower the threshold.

## Three traps measured here, and the code is shaped around all three

**The PBO of pure noise has a standard deviation of 0.21.** Measured 2026-09-22 over twelve
synthetic panels at 252 partitions: individual draws ran from 0.25 to 0.92 with a mean of 0.52. The
partitions overlap heavily and are nothing like as many independent observations. A grid at 0.45
and a grid at 0.55 are not distinguishable, so the 50 % gate is a coarse filter and
`tests/test_cscv.py` checks the *average* over panels, never one.

**Regressing the chosen variant's out-of-sample Sharpe on its in-sample Sharpe measures a
seesaw, not decay.** The two halves are complementary, so a partition whose winner looked unusually
good inside has less left over outside. On pure noise that slope reads −0.57, and on a panel with
one genuinely good column it reads −0.99 — *more* negative where the edge is real. `cscv.carry`
fits across **every** variant instead, which reads 0.00 on noise and +0.75 on a real edge.

**Left alone, the cluster count that deflates the Sharpe picks the most flattering answer.** With a
median correlation of 0.80 between variants this really is one blob with an outlier, and the
silhouette prefers splitting it 478 against 1 — which counts as two trials and barely deflates
anything. `trials.independent` refuses any split where one cluster holds half the variants: here
that is the difference between reporting 2 independent trials and reporting 21, and between a
deflated Sharpe of 0.91 and one of 0.66.

## What it does not tell you

The CSCV **breaks chronology on purpose**. It judges the selection procedure, not this history, so
it cannot say whether the strategy will work going forward. That is the holdout's question and
`walkForwardMatrix`'s. Read `POSSIBLE_IMPROVEMENTS.md` before changing a modelling choice.
