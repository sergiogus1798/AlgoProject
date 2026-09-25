# cscv — is the way I pick parameters prone to overfitting at all?

Step 18. Not a question about this history: it splits the history 924 ways, picks by each half in
turn, and counts how often the winner came back below average — the CSCV of Bailey, Borwein,
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

**Twelve blocks, C(12,6) = 924 partitions, ranked by per-period Sharpe.** López de Prado's own
numbers and the owner's decision of 2026-09-23; `report.py --blocks N` overrides the count per run,
and `cscv.score` takes `sortino` as well. What it will never take is Ret/DD — a score has to be a
rate per period to be comparable across windows. `../wfc/POSSIBLE_IMPROVEMENTS.md` §2 and §3 carry
both arguments.
