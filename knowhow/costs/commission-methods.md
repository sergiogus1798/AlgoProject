---
q: SQX commission methods SizeBased PercentageBased PerTrade None Stockpicker; commission per side or round turn; computeCommissionsOnOpen
tag: 🔬  date: 2026-09-22  see: costs/per-task-costs, export/orderstocsv-schema
---
# `SizeBased` = $ per lot × size; `PercentageBased` = % of notional; both computed "on open"
Methods: `None`, `SizeBased`, `PerTrade`, `PercentageBased`, `Stockpicker`. Master: 359 instruments `SizeBased`, 2 `None`, `PercentageBased` unused.
⚠️ Exports recover $8/lot/side ($16 round turn) under `SizeBased 8` although the code charges only on open — 🤔 probably per order leg. Factor-of-two risk for `assets/`'s `no_forex` commission; test before trusting.

## Evidence
Decompiled `internal/libs/SQTradingLib.jar` + `internal/extend/Snippets/SQ/Trading/Commissions/*.java`; 📓 `CommissionsMethodsList` loads snippets from `SQ/Trading/Commissions`.

| method | charges |
|---|---|
| `SizeBased` | `Commission × size` (dollars per full lot) |
| `PercentageBased` | `(CommissionPct / 100) × size × openPrice × pointValue` |

- 🔬 Both charge in `computeCommissionsOnOpen`; `computeCommissionsOnClose` returns 0.
- Cheap test: run one strategy with `PercentageBased` at a known % and recover `gross − reported P/L` per trade (as in `export/orderstocsv-schema`).
