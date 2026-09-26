---
q: SQX commission methods SizeBased PercentageBased PerTrade None Stockpicker; commission per side or round turn; computeCommissionsOnOpen; issue 26 percentage commission once or twice
tag: 🔬  date: 2026-09-26  see: costs/per-task-costs, costs/where-the-spread-is, export/orderstocsv-schema
---
# `SizeBased` = $ per lot × size; `PercentageBased` = % of notional; both computed "on open" — but `PercentageBased` reconciles as CHARGED TWICE per trade, not once
Methods: `None`, `SizeBased`, `PerTrade`, `PercentageBased`, `Stockpicker`. Master: 359 instruments `SizeBased`, 2 `None`, `PercentageBased` unused live, but priced into `assets/symbols/XAUUSD.yaml`.
⚠️ Exports recover $8/lot/side ($16 round turn) under `SizeBased 8` although the code charges only on open — 🤔 probably per order leg.
🔬 OPEN.md issue 26, measured 2026-09-26 (`studies/readings/edgeCost`, harvest `XAU_ISOOS_ejemplo`): on the 45,488 same-day trades (no swap to confound), fitting `price_pnl − Profit/Loss = k × commission_once` by least squares gives **k = 1.87**, not 1 — a single charge (k=1) leaves a residual mean of −1.38 $/trade (31 standard errors from zero over n=45,488); k=1.87 leaves +0.02 (well inside one SE). **`PercentageBased` is charged roughly TWICE per trade** (once per leg), not once as `_classes.yaml`'s formula reads today. The 0.13 short of an exact 2.0 is unexplained (residual std 9.44 $/trade, plausibly slippage/spread noise on top) but the once-per-trade hypothesis is conclusively rejected.
Consequence: `assets/symbols/XAUUSD.yaml`'s `commission.use` (0.001 %) should be read as the PER-LEG rate if the intent was to declare a round-turn cost, or doubled if it was meant as round-turn already — the owner's file comment assumed once-per-trade and is now known wrong. Not yet fixed here: outside this module's owned paths (`assets/` is not `studies/readings/edgeCost/`).

## Evidence
Decompiled `internal/libs/SQTradingLib.jar` + `internal/extend/Snippets/SQ/Trading/Commissions/*.java`; 📓 `CommissionsMethodsList` loads snippets from `SQ/Trading/Commissions`.

| method | charges (as read from the snippet) |
|---|---|
| `SizeBased` | `Commission × size` (dollars per full lot) |
| `PercentageBased` | `(CommissionPct / 100) × size × openPrice × pointValue` — but see the k=1.87 measurement above |

- 🔬 Both charge in `computeCommissionsOnOpen`; `computeCommissionsOnClose` returns 0 — yet the trade *export*'s reconciliation says the total charged is ~2× the snippet's single-leg formula, which the snippet alone does not explain (possibly a second call site, or `computeCommissionsOnOpen` invoked once per order rather than once per closed trade).
- Full population (118,257 XAUUSD trades, swap included) is inconclusive on its own: residual mean −28.9 (k=1) vs −27.4 (k=2), both dwarfed by unmodelled swap on positions held overnight (std 34.6) — **the same-day subset is what isolates the commission signal**, and it is the test this card should be redone with on another asset before trusting the factor generally.
- Still open: whether the same 2× applies to every `no_forex` asset or is specific to XAUUSD's fee schedule; whether it is exactly 2.0 with the 0.13 gap explained by something else, or genuinely ~1.87.
