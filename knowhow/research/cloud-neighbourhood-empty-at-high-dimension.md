---
q: Why do the parameter cloud's A1 and A3 read "Sin dato" on a mother with many parameters?
kw: Sin dato A1 A3 parameter cloud, neighbourhood of one variant, Chebyshev radius 2 level steps, 13 parameters, surrogate needs 105 points, dense stratum centred on plateau
tag: 🔬  date: 2026-10-04  see: research/cloud-ranking-stability
---
# With 13 live parameters, the origin's box of radius 2 holds only the origin
A1 and A3 read the neighbourhood `model/neighbourhood.near`: every variant within `radius` level steps on ALL
parameters at once. A3's quadratic needs 1 + 2k + k(k-1)/2 points (105 for k=13). Not a calculation fault: the
design's dense stratum (`sqx/variants/design/strata.neighbourhood`) is centred on the SPP plateau's midpoint
(`levels.centre`, brief `center`), not on theta-zero, and the study counts steps over the batch's distinct values
(up to 97 per parameter), so the stratum sits ~45 steps from theta-zero. A2 (Sobol, whole cloud) is unaffected.

## Evidence
`Trade_NIKKEI225_M30_volatilidadL` / `Strategy 4.13.338`: 458 variants, k=13, near n=1, nearest variant 12 steps
away; the 99 `neighbourhood` variants are 44-46 steps away (BBWRPrcInt51: origin 300, stratum 212-214).
