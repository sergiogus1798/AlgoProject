---
q: which databank holds the mothers of the variant batches; WFC_Build WFC_OOS1 WFC_OOS2 rows; S00V000 names; why cloud wfc cscv marketSurfaces read unjudged in a databank table; where to show batch studies per mother
tag: 🔬  date: 2026-10-01  see: locations/which-reports-pair-by-identity
---
# The WFC tasks' databanks hold the variants, never a mother — read the batch studies on WFM
`WFC_Build`, `WFC_OOS1` and `WFC_OOS2` are the variant factory's retest databanks: their rows are
`S00V000…`, one per parameter variant. The batch studies (`cloud`, `wfc`, `cscv`, `marketSurfaces`)
are keyed by the MOTHER's name, so a table over those databanks matches nothing. The mothers sit in
the stages just before: `WFM`, `SPP OOS`, `SPP IS` (and `MCR_All`, whose metrics are a perturbed
retest). `ui.daemon.databank.layout.mothers_bank` picks, among WFM and SPP first, the databank that
holds the most mothers with the smallest roster.

## Evidence
`Test_USDJPY_donchianUpperCrossUp_H1`, 2026-10-01: 15 mothers with a batch; `WFC_Build` 66 rows,
0 of them mothers; `WFM`, `SPP OOS`, `SPP IS`, `MCR_All` 15 rows, 15 mothers. `_M30`: 6 mothers;
`WFM` 43 rows (6), `SPP IS` 24 (6), `SPP OOS` 21 (5).
