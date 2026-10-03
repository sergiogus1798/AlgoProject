---
q: How does our PSR/MinTRL/DSR convention differ from the jsharpe package?
kw: PSR DSR MinTRL differ from jsharpe, tschm jsharpe contrast, Lopez de Prado 2025 variance under the null SR0, Bailey 2012 variance at observed Sharpe, n-1 or T, skew kurtosis ignored at benchmark zero, deflated Sharpe convention, expected maximum Sharpe matches, which PSR formula do we use
tag: 🔬  date: 2026-10-02  see: research/mintrl-explosion-is-correct, research/trial-count-half-rule
---
# Our PSR / MinTRL / DSR are Bailey–López de Prado 2012-14; jsharpe is the 2025 paper — same arithmetic, different convention
Fed our convention, `tschm/jsharpe` (MIT) reproduces `core.significance.psr`, `min_track_record`, `core.surface.plateau.expected_max_sharpe` and `deflated_sharpe` to 1e-12. Called as published it does not, in three places, none a bug:
- **Where the Sharpe's variance is evaluated.** Ours: at the OBSERVED Sharpe (`variance_factor(SR…)`). jsharpe: UNDER THE NULL, at SR0 — so against benchmark 0 its PSR ignores skew and kurtosis entirely (variance 1/T). Ours punishes a left-skewed series and rewards a right-skewed one.
- **n−1 (ours) against T**, and **`1 +` in MinTRL (ours)** against none.
- **SR ≤ SR0**: ours `needed=None`; jsharpe squares the negative gap and answers a finite length.
The expected maximum of K trials is the same formula in both. jsharpe has no DSR function: it is its PSR with SR0 = that expected maximum. Do not "fix" either side to match the other; if the project ever switches convention, PSR, MinTRL and DSR switch together.

## Evidence
`python3 tests/test_inference_vs_jsharpe.py` — 24 deterministic series (normal, left/right skew,
t(4); n 60/250/1000; SR 0.05/0.15 per observation), fixture `tests/fixtures/jsharpe/reference.json`
from jsharpe commit 36f7f94 (generator: `scratch/ext/c1/reference.py`). Widest gaps on that grid:
PSR 0.850964 (ours) vs 0.877361 (left skew, n=60, SR 0.15, SR0 0) — median gap 0.0013;
MinTRL 7355.99 vs 7111.74 (relative gap up to 29.6 %; e.g. left skew n=250 SR 0.15 SR0 0: 153.2 vs 120.2);
DSR 0.185235 vs 0.165677 (right skew, n=60, K=1000). At SR0=0, n=60, SR 0.15: normal 0.8742 vs
0.8774, left skew 0.8510 vs 0.8774, right skew 0.8982 vs 0.8774, fat tails 0.8732 vs 0.8774.
Unreachable case SR 0.05 < SR0 0.08: ours None, jsharpe 3015.8.
