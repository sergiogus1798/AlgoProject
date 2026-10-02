# cscv — is the way I pick parameters prone to overfitting at all?

Step 18. Not a question about this history: it splits the history 12,870 ways, picks by each half
in turn, and counts how often the winner came back below average — the CSCV of Bailey, Borwein,
López de Prado and Zhu. It is run once per selection rule, so the answer is not "this strategy
decays" but **"choosing by plateau centre instead of by maximum takes the PBO from 30 % to 4 %"**.

Reads `equity.parquet` (from `sqx.variants.equity`) through `engines/variants/`, on the same points
and the same split as `../wfc/`. Writes `cscv.json` beside the batch — the pipeline reads its
scalars, so it does not change shape — and the result the window paints into `estudios/cscv.*`.

```
config.yaml ─▶ engines/variants ─▶ measure ─▶ verdict ─▶ contract
 every knob    the panel, the      the rules,  PBO, DSR,   estudios/
               split, the points   the CSCV    rule cost   cscv.*
```

| folder | the question it answers | read its README before |
|---|---|---|
| `inputs/` | which config, with the knobs shared with the WFC | touching a knob |
| `measure/` | what are the numbers? | touching a selection rule or the partitions |
| `verdict/` | what do they mean? | moving a threshold or a cluster count |

| file | what it does | run it |
|---|---|---|
| `report.py` | The CSCV, once per selection rule | `python3 -m studies.optimisation.cscv.report --work <dir>` |
| `contract.py` | The head rule's PBO as the call, λ per rule, the rules side by side, the head rule partition by partition | imported |
| `config.yaml` | Every knob of the CSCV; the trade floor and the split are in `engines/variants/config.yaml` | edited, or `--set cscv.key=value` |
| `tooltips.py` | One sentence per knob, for the window's configuration drawer | imported |

**As López de Prado does it (owner, 2026-10-01): daily returns, sixteen blocks, Sharpe.** The
matrix is T trading days × N variants — every day the joined curve has, zero-P&L days included,
~5,000 rows on the 2007–2026 USDJPY batches (`engines/variants/panel.py`, `cscv.period: D`);
it is cut into the ledger's 16 blocks, every C(16,8) = 12,870 half is in-sample once, the Sharpe
of each column in each half ranks the variants, argmax picks, λ = logit of the pick's
out-of-sample relative rank, PBO = P(λ ≤ 0); beside it the paper's performance-degradation
regression (the decay tab: the pick's OOS Sharpe on its IS Sharpe, one point per partition) and
its probability of loss («pierde»). Sharpe is shown annualised ×√252 — display only, a constant
moves no rank. `report.py --blocks N` overrides the count per run.

**Each half is scored off block sums, never by concatenating rows** (`measure/cscv.py::moments`):
per block the column sums, sums of squares and sums of squared losses, then one matrix product
per chunk of 1,024 partitions. On `Test_USDJPY_donchianUpperCrossUp_H1/Strategy_10.1.79`
(T = 4,997, N = 500) one rule under one score takes 0.4 s against ~79 s row by row, and the whole
study 6.6 s with a ~0.5 GB peak per worker (🔬 2026-10-01); `tests/test_cscv.py` holds the two
equal partition by partition.

**Extensions of this project, marked as such in the result:** the `plateau_centre` and
`random_profitable` rules, the Sortino score (every rule runs under both Sharpe and Sortino,
`report.py`'s `SCORE_KEYS`, so the window's "Puntuación" selector switches without a second run;
`cscv.score` only picks which signs the verdict and `cscv.json`'s flat keys), the slope across
all variants («Pendiente»), the dominance against the median variant, and the rule cost on the
real chronological split. What a score will never take is Ret/DD — it has to be a rate per
period to be comparable across windows. `../wfc/POSSIBLE_IMPROVEMENTS.md` §2 and §3 carry both
arguments. **PBO and its parts read as one-decimal percentages everywhere in the result**; the
raw fractions stay in `cscv.json`, which the pipeline reads by name.

**The "decay" panel's per-chosen-point slope is a seesaw, not a diagnosis**
(`knowhow/research/cscv-chosen-point-slope-seesaw.md`, `measure/cscv.py::carry`): the two halves
of a partition are complementary, so it reads negative by construction and *more* negative the
more real the edge is. Read the **aggregate slope** (`result["slope"]`, in the verdict and the
glossary) for whether the ranking carries over — never this panel's sign.
