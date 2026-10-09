---
q: Does a quadratic surface fitted to pure noise still give a Sobol ranking, and what R² is that noise worth?
kw: cloud sobol ranking noise first order 0.8 total 1.2 adjusted R2 shuffled reference 0.06 458 variants 105 coefficients 0.23 raw R2 rank of design matrix legible sin estructura distinguible del ruido
tag: 🔬  date: 2026-10-07  see: plateau-radius-degenerates-at-six-params
---
# Sobol indices rank the fitted surface, not the world: read them only above the shuffled adjusted R²
A quadratic fitted to pure noise still distributes its variance among the parameters: Σ first-order
≈ 0.8 and Σ total ≈ 1.2 in the test. So the cloud prints the ranking only when the **adjusted** R²
beats a percentile (95) of the same fit on the metric shuffled among the variants. With 458 variants
and 105 coefficients the shuffled adjusted R² sits near **0.06**; the 0.23 of the proposal is the raw
R². The adjustment uses the design matrix's **rank**, not its width: a parameter with two values makes
its square collinear with itself and would be counted as a coefficient.

## Evidence
`studies/optimisation/cloud/model/surrogate.py` (`1 − (1 − R²)(n − 1)/(n − rank)`),
`measure/reference.py`; `tests/test_cloud_map.py` (pure noise called legible at about the nominal rate).
