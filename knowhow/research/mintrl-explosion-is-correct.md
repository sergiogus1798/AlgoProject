---
q: MinTRL absurd huge five digit number bug or correct crossmarket USDCHF 35000 35426, SR below SR* negative gap squared, no alcanzable unreachable, SR SR* not glued gamma4 non-excess kurtosis Bailey Lopez de Prado, 27 avisos en total 3 avisos por test crossmarket bug or real
tag: 🔬  date: 2026-10-01  see: research/random-entry-nulls
---
# MinTRL is only defined when SR > SR*; below it, it is «No alcanzable», not a big number

`MinTRL = 1 + variance_factor·(z_α/(SR−SR*))²` squares the gap, so an SR **below** SR* printed a
finite number (USDCHF: 35,426) that read as "reachable with more data". It is not: no sample makes
SR > SR* significant when the observed SR sits under it. Since 2026-10-01
`core.significance.min_track_record` returns `needed=None, enough=False` when SR ≤ SR*, and the
Cross Market table prints «No alcanzable» in red. Above SR* the formula is unchanged and correct
(γ₄ raw kurtosis; SR and SR* both per-trade, never annualised — `sharpe_total` never enters it).

## Evidence

`Test_USDJPY_donchianUpperCrossUp_H1/Retest Markets - Family/2026-09-30`, `Strategy 1.26.74` on
USDCHF: SR = −0.0519 < SR* = −0.0432 (gap −0.00868), γ₄ = 11.38, 754 trades → old formula 35,238.8.
Rerun in-process 2026-10-01 (`nulls.draws=300`): USDCHF, AUDJPY, AUDUSD, GBPUSD, USDCAD now read
«No alcanzable»; CADJPY (SR > SR*, tiny gap) still reads 10,886 — large but genuinely reachable.
Known answer: `tests/test_significance.py::test_min_track_record_unreachable_when_sharpe_does_not_clear_benchmark`.

"27 avisos en total" on the same strategy is 9 markets × 3 warnings (`short_sample`,
`bad_hold_fit`, the hidden `no_drift`) — a real count, not a bug.
