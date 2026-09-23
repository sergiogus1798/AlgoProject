# walkForwardCorrelation

Two questions about one parameter grid, and they are not the same question.

**Does in-sample performance predict out-of-sample performance?** One point per parameter
combination, in-sample net profit against out-of-sample net profit. A cloud that fills all four
quadrants means optimising in-sample buys nothing out of sample; a cloud on the rising diagonal
means the surface carries information and the in-sample ranking is worth trusting.

**And is the way I pick parameters prone to overfitting at all?** That one is not about this
history. It splits the history 252 ways, picks by each half in turn, and counts how often the
winner came back below average — the CSCV of Bailey, Borwein, López de Prado and Zhu. It is run
once per selection rule, so the answer is not "this strategy decays" but **"choosing by plateau
centre instead of by maximum takes the PBO from 41 % to 5 %"**.

Reads contract **C3** (`metrics.parquet`, from `sqx.variants.collect`) and, for the CSCV,
`equity.parquet` (from `sqx.variants.equity`). Writes `wfc.html`, `wfc.json`, `cscv.html` and
`cscv.json` beside them.

| file | what it does | run it | in → out |
|---|---|---|---|
| `config.yaml` | the trade floor, the rho below which the ranking is not worth trusting, and every knob of the CSCV | edited | — |
| `measure.py` | which points are usable, Spearman's rho, its 95 % interval, and the call | imported | C3 → rho, call |
| `render.py` | the scatter, as inline SVG | imported | points → svg |
| `report.py` | the correlation: `python3 -m strategies.walkForwardCorrelation.report --work <dir>` | command | C3 → `wfc.html` |
| `matrix.py` | the N × T panel the CSCV runs on, and where the real in-sample boundary is | imported | equity → panel |
| `rules.py` | the three ways a person picks one parameter set off a surface, behind one signature | imported | scores → a choice |
| `cscv.py` | the partitions, the per-period Sharpe, and the choose-then-score loop | imported | panel → 252 rows |
| `summary.py` | what those rows say: PBO, carry-over, probability of loss, dominance | imported | rows → numbers |
| `trials.py` | how many independent trials the grid really holds, and the deflated Sharpe that follows | imported | panel → count, DSR |
| `cost.py` | what each rule cost on the split that actually happened, and how far the optimum moved | imported | panel → percentiles |
| `figures.py` | the CSCV page: the lambda bands, the partition cloud, and every statistic explained | imported | rows → html |
| `pbo.py` | the CSCV: `python3 -m strategies.walkForwardCorrelation.pbo --work <dir>` | command | C3 + equity → `cscv.html` |

**The interval is the point, not the coefficient.** With a dozen tuples the sampling error on a
correlation is enormous, so the study reports a band and will say `indeciso` rather than pretend.
`indeciso` means fabricate more points, not lower the threshold.

## Three traps measured here, and the code is shaped around all three

**The PBO of pure noise has a standard deviation of 0.21.** Measured 2026-09-22 over twelve
synthetic panels: individual draws ran from 0.25 to 0.92 with a mean of 0.52. The 252 partitions
overlap heavily and are nothing like 252 independent observations. A grid at 0.45 and a grid at
0.55 are not distinguishable, so the 50 % gate is a coarse filter and `tests/test_cscv.py` checks
the *average* over panels, never one.

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
