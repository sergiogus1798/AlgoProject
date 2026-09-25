---
q: strategy over market ratio E = mean held return / market drift, Brent negative drift, Fieller interval unbounded, bootstrap ratio, cross-market excess A, headline metric
tag: 🔬  date: 2026-09-16  see: research/fixed-reference-window-edge, research/gates-are-owner-decisions
---
# Never divide by a drift that may be zero: read A, report E with a Fieller interval
Headline = A (drift-neutral excess: held return minus market drift) / the market's typical bar move (a
volatility, always positive). E = mean(bar return while held)/mu_m is context only, with a Fieller interval,
which is honestly unbounded when `z²·var(den)/den² ≥ 1`. Never a percentile bootstrap on a ratio (finite
interval exactly when none exists). Any "strategy over market" metric: check the denominator's significance first.

## Evidence
- M30 drifts: gold t = +3.13, silver +1.61, Brent t = −0.11. Brent E = −69.4 for the market with the strongest A of the three.
- Not: withhold E when drift is weak (hides how badly determined it is).
- Brent, `Strategy 1.10.80`: E = +17.4, 90 % CI unbounded, 54.5 % of bootstrap replicates with market drift ≤ 0. Report all three together.
- Resample numerator and denominator from the same replicate (occupied bars ⊂ market bars → covariance).
- Aggregate into blocks before resampling: each block → four totals (sum, count of all bars; sum, count of occupied);
  same estimator at ~1/1000 memory (120,000 bars × 2,000 draws otherwise).
