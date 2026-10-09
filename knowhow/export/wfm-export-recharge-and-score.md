---
q: Whose costs does a WFM export carry, why can't reprice.real price its EndTest trades, and what is SQX's score built on?
kw: WFM export charged at oos1 costs recharge oos2 EndTest off the bar grid reprice.real refuses score all_ oos_only wfm.costs_segment
tag: 🔬  date: 2026-10-07  see: wfm-export, fill-and-pricing, off-grid-stamps-and-stop-exits
---
# A WFM export is charged at ONE segment's costs (oos1), EndTest trades are off the bar grid, and `score` is built on `all_`
- The task pays the costs of `wfm.costs_segment` (`assets/_build.yaml`, oos1); trades closing in oos2 are
  re-charged by hand (lots × point value × (Δspread + 2 Δslippage) + Δcommission); `recharge.charged` must agree.
- Cells end with `EndTest` trades off the bar grid (103 in the reference export): `reprice.real` refuses them.
- `all_<metric>` = first optimisation window + out-of-sample, and SQX's `score` is built on it (67–79 % already
  seen): the study rescales it to the out-of-sample alone (`measure/gaterule.oos_only`).

## Evidence
`Trade_NIKKEI225_M30_volatilidadL`, 10 mothers: build and oos1 trades reprice at oos1's costs to 0.21 USD a
trade, at build's or oos2's they miss by 19 and 37 a trade (that is how the charged segment is verified on a
new export). See `studies/optimisation/wfm/inputs/README.md` and `README.md`.
