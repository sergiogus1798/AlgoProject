# construct/verdict — is the chosen combination better than chance on oos1, and real on oos2

INFERENCE (PLAN §3, §5.5, §14.3): it receives numbers and judges none it produced. **It never
imports `search/` or `equity/`** — `../many.py` (real path) and `../funded_verdict.py` (funded path)
draw the nulls and hand the figures over (`tests/test_portfolio_verdict.py` checks the imports).
The rule is Q11 (d), Council 2026-10-04: **oos1 first, oos2 only if oos1 passed, never pooled**.

**Imports from:** `pairs/stress`, `ledger.trials` · **Consumed by:** `../many.py`, `../funded_verdict.py`, `../oos2.py`, `search/objective.py` (`metrics`)

| file | what it does | run it | in → out |
|---|---|---|---|
| `decide.py` | The verdict of both paths (Q11 d): oos1 first, oos2 only if it passed, and the funded sentence. | imported | readings, hold, cost → verdict, sentence |
| `decide_real.py` | The real path's decision sentence (PLAN §5.5): the cost next to the gain. | imported | verdict → text |
| `deflate.py` | The oos2 reading (Q11 d): the chosen portfolio's daily Sharpe against the best that luck gives N trials. | imported | daily P&L, σ, N → reading |
| `hold.py` | Did the diversification hold: the chosen members' pair measures re-read on the judging stretch. | imported | pairs table → pairs over threshold, effective N |
| `metrics.py` | Window-robust metrics of daily P&L paths: RAR, R-cubed, gain-to-pain, P(losing year), Sharpe. | imported | paths, dates → metrics |
| `null.py` | Where the chosen combination sits among the selected null's winners. | imported | chosen figures, null figures → reading |

## Traps
- **The funded bar is not set.** `verdict.pass_measure: mc_p` (owner, 2026-10-05); nobody has set
  `verdict.pass_percentile` — do not add one here or in `config.yaml`: it arrives as
  `ledger:portfolio.funded.verdict_percentile` when the owner decides. Until then the funded
  verdict is «SIN CRITERIO (falta verdict.pass_percentile)» and oos2 is not opened.
- **Two nulls, two knobs.** The real path's is `real.null_draws` (10,000 random admissible
  combinations of the chosen K, `ledger:portfolio.verdict.null_draws`); the funded path's is
  `verdict.null_draws` (100 whole searches: stage A on random combinations + stage B, PLAN §14.3).
- **The selected null draws from the same pool**, so the pool's edge is in the null too: it asks
  whether the search chose better than chance among admissible combinations, not whether the
  strategies have an edge (`knowhow/research/selected-null-same-pool.md`).
- **A small pool cannot be judged, and the output says so.** With fewer than 20 admissible
  combinations of size K the chosen one is ≥ 5 % of the draws and the 95th percentile is its own
  figure: `no_discrimina`, no percentile printed, `pass` None, oos2 shut. The funded analogue:
  the share of null searches that chose the same combination ≥ 1 − `pass_percentile`.
- **The oos1 false-positive rate is the nominal 5 %** 🔬 `tests/test_portfolio_verdict_real.py`:
  a random trio of 12 noise members passes in 5.0 % of 200 seeds.
- **A pair under 24 shared months on the judging stretch is not judged** (`short`), never read
  as held.
