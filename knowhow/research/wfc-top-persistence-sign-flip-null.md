---
q: Does the WFC's top persistence, or its median OOS/IS Sharpe ratio, tell a zero-edge variant family from a real one?
kw: wfc persistencia del top exceso_persistencia_minimo mediana_ratio_Sharpe sign-flip null rademacher dependent variants hypergeometric baseline keep regression to the mean criterion diagnostic
tag: 🔬  date: 2026-10-04  see: spp-decay-metrics-zero-edge-null
---
# Top persistence separates from a zero-edge family (offered as a criterion); the median Sharpe ratio does not (diagnostic)

`studies/optimisation/wfc/measure/persistence.py`. The excess of the top's persistence over `keep`
(`wfc.summary.exceso_persistencia_*`) leaves the zero-edge null in 4 of 10 mothers: offered in
`pipeline/autopilot/offered.yaml`, no threshold. The median Sharpe ratio OOS/IS does in 1 of 10:
diagnostic. Read the excess against the sign-flip null (±0.27), never against N variants (±0.09);
the quantiles a threshold is read from are below.

## Evidence
`studies/optimisation/wfc/measure/persistence.py`. Persistence = share of the build's best `top`
(20 %, by net profit) that stays in the best `keep` (50 %) of one OOS window; by chance it is `keep`,
so the fact is the EXCESS (`wfc.summary.exceso_persistencia_<window>`, `_minimo` = worst window).
The null flips the sign of each OOS day for all variants at once: every variant expects zero, the
variants stay as dependent as they are. That null is ~3× wider than the independent (hypergeometric)
one — ±0.27 against ±0.09 at 64 of 320 — so never read the excess against N variants.
The median of per-variant Sharpe OOS/IS (IS above 0.1) is covered by the same null: one OOS path
moves every variant together. It also sits below 1 with no decay at all (entering on a high IS
Sharpe regresses to the mean).

`Trade_NIKKEI225_M30_volatilidadL`, 10 mothers, 220–477 usable variants, build → oos1 ONLY (oos2 is
reserved and was not used to decide anything), 1,000 flips. Quantiles 5/25/50/75/95:

| metric | real (across the 10) | zero-edge null (median across the 10) | real beyond null p95 |
|---|---|---|---|
| excess persistence, top 20 % → upper half | −0.13 −0.07 0.08 0.34 0.37 | −0.26 −0.12 0.00 0.13 0.29 | 4 / 10 (0.5 expected) |
| median ratio Sharpe OOS/IS | −0.63 0.36 0.62 0.82 1.33 | −1.23 −0.47 0.01 0.51 1.24 | 1 / 10 |

Persistence is cross-sectional only: `Strategy 13.3.390` reads +0.34 with a median ratio of −0.22 —
the build's ranking held while the whole family lost. It says «the ranking is informative», never
«there is an edge»; the flip null also credits to the family any ranking that comes from exposure.
Test: `tests/test_wfc_persistence.py`. The day a threshold is set on the excess, log that choice in
the ledger as a look of step 17 (the metric family is ~10 looks, none logged while nothing judges).
