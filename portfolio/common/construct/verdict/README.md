# construct/verdict — is the chosen combination better than chance on oos1, and real on oos2

INFERENCE (PLAN §3, §5.5, §14.3): it receives numbers and judges none it produced. **It never
imports `search/` or `equity/`** — `../many.py` (real path) and `../funded_verdict.py` (funded path)
draw the nulls and hand the figures over (`tests/test_portfolio_verdict.py` checks the imports).
The rule is Q11 (d), Council 2026-10-04: **oos1 first, oos2 only if oos1 passed, never pooled**.

**Imports from:** `pairs/stress`, `ledger.trials` · **Consumed by:** `../many.py`, `../funded_verdict.py`, `../oos2.py`, `search/objective.py` (`metrics`)

| file | what it does | run it | in → out |
|---|---|---|---|
| `metrics.py` | RAR, R-cubed, gain-to-pain, P(losing year) and the daily Sharpe of daily P&L paths, and their drawdown episodes — pure; `search/objective.py` ranks them on build, the real verdict on oos1 | imported | paths, dates → metrics |
| `null.py` | `percentile`/`read` — the mid-rank of the chosen figure among the null's, per measure (funded); `bar` — the real path's oos1 reading: the chosen figure against a percentile of the draws, or `no_discrimina` when the chosen one alone is at least the share of draws that percentile leaves free | imported | chosen figures, null figures → reading |
| `deflate.py` | The oos2 reading: daily Sharpe minus the expected maximum of N trials of spread σ, by `ledger.trials.deflated` (no second formula); `excess` > 0 passes, the DSR is kept beside it | imported | daily P&L, σ, N → reading |
| `hold.py` | «Did the diversification hold»: the chosen members' pair measures on the segments opened against the thresholds they were admitted under — reported, removes nothing, decides nothing | imported | pairs table → pairs over threshold, effective N |
| `decide.py` | `funded_oos1` (the named measure's percentile against `verdict.pass_percentile`; unset → `sin_criterio` naming the knob), `combine` (what oos1 and oos2 decide together: `pass` and a Spanish `label`, a None always with its reason), the verdict dict of either path and the funded sentence; `grouped`, a count as every sentence prints it («10 000», never «10,000») | imported | readings, hold, cost → verdict, sentence |
| `decide_real.py` | The real path's Spanish sentence: cost next to gain, the null's size against its draws | imported | verdict → text |

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
