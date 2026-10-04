---
q: Do the surfaces' Jaccard lift, or «the mother inside the other markets' top decile», beat a zero-edge market?
kw: marketSurfaces lift_Jaccard_mediano exceso_madre_en_top Jaccard lift J_chance q/(2-q) hypergeometric sign-flip null clustered variants top decile chosen point consensus map diagnostic unit check
tag: 🔬  date: 2026-10-04  see: wfc-top-persistence-sign-flip-null
---
# Neither separates on the Nikkei: both stay diagnostics. J by chance is 0.04–0.09 per market, not 0.053, and one market's lift needs ~3 to leave its null

`studies/optimisation/marketSurfaces/measure/lift.py`. J by chance comes from the other market
under zero edge (daily sign flips shared by variants and markets), not from q/(2−q): 0.04–0.09 per
market, and one market's lift needs ~3 to leave its null — only the median over markets is
readable. On the Nikkei neither metric leaves the null: diagnostics, not offered. The unit check
(absolute vs dimensionless parameters) is NOT done: no register says a parameter's unit.

## Evidence
`studies/optimisation/marketSurfaces/measure/lift.py`. J_chance is not q/(2−q): it is the mean J
of the main market's real top decile against the other market under zero edge — each of its days
keeps its size and takes a random sign, the same for every variant and, per calendar day, for every
market (1,000 draws), so variants and markets stay as dependent as they are. Lift = J / J_chance.
«Mother inside» = share of secondary markets whose top decile holds θ₀, minus that share under the
same draws. A market sharing fewer than 10 distinct usable variants with the main one is missing.
Clustered variants make the null wide, not biased: per market the lift's 95th percentile under zero
edge is ~3 (2.8–3.0), so a single market at L = 2 says nothing; only the median over markets is
narrow enough to read (5–95: 0.3–1.5).
Not done — the unit check (absolute vs dimensionless parameters): no register in the repo says
which parameter is in price units (`sqx/variants/lengths.yaml` rules bar lengths only), and a
guess by name is what rule 11 forbids. The consensus map already marks θ₀ and counts its markets;
it is labelled diagnostic-only.

`Trade_NIKKEI225_M30_volatilidadL`, 10 mothers, 9–11 secondary markets each, build and oos1 ONLY
(oos2 reserved, not used to decide). Quantiles 5/25/50/75/95:

| metric | segment | real (across the 10) | zero-edge null (median across the 10) | real beyond null p95 |
|---|---|---|---|---|
| median lift | build | 0.10 0.37 0.57 0.77 0.97 | 0.26 0.50 0.78 1.00 1.49 | 0 / 10 |
| median lift | oos1 | 0.13 0.34 0.44 0.71 0.86 | 0.29 0.48 0.81 0.96 1.46 | 0 / 10 |
| excess of «mother inside» | build | −0.10 −0.08 −0.02 0.07 0.25 | −0.08 −0.08 0.00 0.02 0.17 | 1 / 10 |
| excess of «mother inside» | oos1 | −0.04 0.00 0.06 0.13 0.24 | −0.08 −0.08 0.00 0.04 0.18 | 1 / 10 |

Per market: J_chance 5/50/95 = 0.039/0.066/0.091 (build), 0.043/0.069/0.087 (oos1); the real J
leaves its own null's p95 in 4 of 108 pairs (build) and 2 of 108 (oos1) — fewer than the 5.4 chance
gives. The real overlap sits at or BELOW a zero-edge market's: under the flip the variants that
trade most fill both tops, and that alone overlaps more than these markets do. Same reading as the
study's own call («la región no viaja») and as the owner's example (J 0.03–0.07 in 11 of 12).
Caveat for a batch where it does separate: on long-only strategies two markets drifting together
rank variants by time-in-market, which lifts J with no region travelling — read it beside
`rho_neutral`. Test: `tests/test_surfaces_lift.py`.
