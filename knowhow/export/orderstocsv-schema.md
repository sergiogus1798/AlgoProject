---
q: how to export trades from SQX; orderstocsv columns schema; MAE MFE units points or dollars; Sample type IST OOS1; unfilled pending order EndTest; recover commission per trade
tag: 🔬  date: 2026-09-29  see: export/trade-export-columns, export/storage-format, costs/commission-methods
---
# `orderstocsv` exports every .sqx of a folder in one JVM — mind 4 traps
`-tools action=orderstocsv file=<folder> output=<dir> data=main` via `bin/sqx-worker.sh run` (one-shot).
1. MAE/MFE are in account currency: `price = abs(MAE_$) / (Size * pointValue)`, per-trade `Size`.
2. `Sample type` is only as good as the strategy's last retest — use it when IST/OOS1 present, else `Open time`.
3. Drop rows with a blank close price (last row may be an unfilled pending order, `Close type=EndTest`).
4. Give it a folder, even for one strategy: `file=<one .sqx>` writes `<output>.csv` beside the output folder, not a CSV inside it.

## Evidence
2026-09-29, `mt5.verify`: `file=…/MT5Verify_ftmo/Strategy 3.48.75.sqx output=…/sqx/ftmo` → log «orders exported to '…/sqx/ftmo.csv'», the folder `sqx/ftmo/` left empty.
- Folder input: 231 strategies in ~4 min. Read-only; needs no build, touches no project state; worker stays stopped after.
- 16 columns: Ticket, Symbol, Type, Open time, Open price, Size, Close time, Close price, Profit/Loss,
  Balance, Sample type, Close type, MAE ($), MFE ($), Time in trade, Comment.
- MAE/MFE: `pointValue=100` for XAUUSD_Infinox. `Size` varies (risk-based sizing) → a fixed divisor is wrong.
  Verified: MAE_price always brackets the realised adverse move.
- Sample type: in `SPP OOS` / `WFM` databanks every `data=main` row was `IST` (useless; window from `Open time`).
  The `OOS` databank of the same project exports both: `IST` = 2008.01.02–2017.12.29, `OOS1` = 2018.01.02–2022.12.30,
  clean split at the retest boundary. A strategy's stored main result = whatever period it was last retested over:
  46 of 231 in `SPP OOS`+`WFM` covered only 2018–2023 → zero trades to a 2008–2017 study.
- Costs per trade = `gross - reported P/L`, `gross = (close-open) * Size * pointValue`. Measures $8/lot/side
  ($16/lot round turn) = `commissions=<Method type="SizeBased">8`. Spread (`defaultSpread="10.0"`) is inside the
  fill prices, not in that residual. Overnight trades show extra drag (swap: long −73.42 pts, short +38.76 pts).
