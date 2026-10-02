---
q: plateau membership n=1, neighbourhood radius 2 too tight, cloud ensemble one variant, marketSurfaces region empty, how many variants inside the plateau
tag: 🔬  date: 2026-09-30  see: research/cloud-ranking-stability
---
# A Chebyshev box of radius 2 across six live parameters usually holds only the mother
`cloud.model.neighbourhood.near` (radius, every parameter at once) and `marketSurfaces.measure.region.plateau`
(the same box, reused so "the plateau on the main asset" is one definition, `FEEDBACK §8.5`) both shrink fast
with the parameter count: at ~500 variants sampled from a space of millions, a box that must hold on **all**
six live parameters simultaneously usually contains nobody but θ₀ itself. This is not a bug in either study —
`cloud`'s own C1 panel already reads "Meseta de 1 variantes" on the same batch — but it makes an inside/outside
comparison built on it uninformative (n=1) more often than not.

## Evidence
`Test_USDJPY_donchianUpperCrossUp_H1`, `region_radius=2`, `region_delta=0.20`, 6 live parameters:

| mother | variants | plateau n |
|---|---|---|
| Strategy 16.9.76 | 500 | 1 |
| Strategy 1.27.61 | 499 | 1 |
| Strategy 10.9.72 | 500 | 2 |
| Strategy 4.17.74 | 437 | 8 |

`cloud.json` of Strategy 16.9.76 independently confirms n=1 for the same radius/delta on its own C1 ensemble.

Widening `region_radius` (or sampling denser near θ₀, e.g. `neighbourhood` stratum weight) grows the plateau;
a marketSurfaces report whose "dentro (n)" column reads 1 everywhere is reporting this correctly, not failing.
