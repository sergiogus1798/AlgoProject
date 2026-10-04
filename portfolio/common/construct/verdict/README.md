# construct/verdict — what the chosen combination is worth out of sample, against a null that was selected too

INFERENCE (PLAN §3, §5.5, §14.3): it receives numbers and judges none it produced. **It never
imports `search/` or `equity/`** — `../funded_b.py` runs the searches and hands the figures over
(`tests/test_portfolio_verdict.py` checks the imports).

**Imports from:** `pairs/stress` · **Consumed by:** `../funded_b.py`

| file | what it does | run it | in → out |
|---|---|---|---|
| `metrics.py` | RAR, R-cubed, gain-to-pain, P(losing year) and the daily Sharpe of daily P&L paths, and their drawdown episodes — pure; `search/objective.py` ranks them on build, the verdict will read them out of sample | imported | paths, dates → metrics |
| `null.py` | Where the chosen combination's figure sits among the null searches' winners: the mid-rank percentile, per measure | imported | chosen figures, null figures → percentiles |
| `hold.py` | «Did the diversification hold»: the chosen members' pair measures on the judging stretch against the thresholds they were admitted under — reported, removes nothing | imported | pairs table → pairs over threshold, effective N |
| `decide.py` | The verdict dict and its Spanish sentence, cost next to gain; `pass` stays `None` until `verdict.pass_measure` and `verdict.pass_percentile` exist (Q11, the owner's) | imported | measures, hold, cost → verdict, sentence |

## Traps
- **There is no pass bar.** Nobody has set the percentile that passes; do not add one here or in
  `config.yaml` — it arrives as `ledger:portfolio.funded.verdict_percentile` when the owner decides.
- **The selected null draws from the same pool**, so the pool's edge is in the null too: it asks
  whether the search chose better than chance among admissible combinations, not whether the
  strategies have an edge. A null search with enough candidates to cover a small pool finds the
  same combination and the percentile reads ~50 % whatever the edge
  (`knowhow/research/selected-null-same-pool.md`).
- **A pair under 24 shared months on the judging stretch is not judged** (`short`), never read
  as held.
