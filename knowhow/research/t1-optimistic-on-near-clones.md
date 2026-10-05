---
q: Why does stage B's trade bootstrap T1 give a higher P(pass) than D, T2 and stage A, and is it a bug?
kw: funded_b; stageb; T1 0.359 T2 0.302; trade bootstrap per strategy; members independent; near-clones; Test_nikkei_ref; fail rate too low; most pessimistic decides; daily correlation 0.65-0.78; days with an opening
tag: 🔬  date: 2026-10-05  see: research/rank-score-rar-is-a-mean, research/selected-null-same-pool
---
# T1 draws each member alone, so on correlated members it reads the portfolio's risk too small: it is optimistic by construction and never decides
T1 resamples each member's trades from its own history and lays the members side by side independently:
losses that coincided in history stop coinciding. On a pool of near-clones that is most of the risk, so T1
fails less and passes more than D (joint days) and T2 (synchronised trade windows), which agree with each
other and with stage A's start-day figure. Not a bug: rolling each member's REAL day table by a random
offset (no resampling at all, only independence) reproduces T1's figures. «The most pessimistic decides»
is what keeps T1 from choosing; on diversified members the three should converge.

## Evidence
- `Test_nikkei_ref`, test root, thresholds 0.90, `hantec:express:10000:USD`, winner K = 4 at r 0.6 %
  (run `2026-10-05T1000_…`): stage A 0.328 (exact M1 start days: 0.328); D@2 0.319, D@20 0.328; T2@2 0.303,
  T2@20 0.319; **T1 pass 0.360, fail 0.048, open 0.592**.
- Control, same members, each member's real day table rolled by its own random offset: pass 0.322, fail
  0.041, open 0.637 — T1's low failure rate with no bootstrap involved.
- 126-day P&L: mean 726-742 in D/T2 against 774 in history, sd 870-940 against 783; T1 sd 541. Share of
  days with an opening: 0.31 in T1 against 0.10 in history (the members open on the same days).
- Daily ρ between members 0.65-0.78. Politis-White block length measured 1-3 days.

## Counter-evidence
One pool, ten near-clones, one plan. Not measured on diversified members.
