---
q: Why does a radius-2 Chebyshev plateau box across six parameters hold only the mother?
kw: plateau membership n=1, neighbourhood radius 2 too tight, cloud ensemble one variant, marketSurfaces region empty, how many variants inside the plateau
tag: 🔬  date: 2026-09-30  see: research/cloud-ranking-stability
---
# A Chebyshev box of radius 2 across six live parameters usually holds only the mother
`marketSurfaces.measure.region.plateau` (a box of radius `region_radius` on every parameter at once;
the cloud's own copy, `cloud.model.neighbourhood`, was retired with encargo 48, 2026-10-07) shrinks fast
with the parameter count: at ~500 variants sampled from a space of millions, a box that must hold on **all**
six live parameters simultaneously usually contains nobody but θ₀ itself. This is not a bug —
the cloud's retired C1 panel read "Meseta de 1 variantes" on the same batch — but it makes an inside/outside
comparison built on it uninformative (n=1) more often than not.

## Evidence
`Test_USDJPY_donchianUpperCrossUp_H1`, `region_radius=2`, `region_delta=0.20`, 6 live parameters:

| mother | variants | plateau n |
|---|---|---|
| Strategy 16.9.76 | 500 | 1 |
| Strategy 1.27.61 | 499 | 1 |
| Strategy 10.9.72 | 500 | 2 |
| Strategy 4.17.74 | 437 | 8 |

The retired `cloud.json` of Strategy 16.9.76 confirmed n=1 for the same radius/delta on its own C1 ensemble (old stratified batches).

Widening `region_radius` (the batch is a Latin hypercube over the plateau since 2026-10-07, with no neighbourhood stratum) grows the plateau;
a marketSurfaces report whose "dentro (n)" column reads 1 everywhere is reporting this correctly, not failing.
