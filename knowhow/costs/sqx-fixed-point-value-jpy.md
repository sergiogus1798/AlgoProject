---
q: SQX P&L in USD for USDJPY JPY pairs fixed point value; MT5 P&L larger than SQX same trade; point_value 631.3 653.92; conversion at a fixed rate; profit per trade differs by year; Verificar row 2 R gap row 5 drawdown JPY
tag: 🔬  date: 2026-10-01  see: costs/sqx-fx-costs, eng/mt5-history-depth-first-bar
---
# SQX prices a JPY-quoted pair at one fixed point value; MT5 at each moment's rate
`USDJPY_M1` carries `point_value` 631.3 USD per yen per lot since 2026-10-01 — 100,000 / 158.4,
the rate FTMO's MT5 gave that day (653.92, the5ers' 152.9, before) — and SQX converts every trade
with it. MT5 converts at the rate of the trade, so the same trade's USD P&L differs by (158.4 /
rate): +17 % in 2022 (≈135) and about +98 % in 2011-2012 (≈80) — SQX's USD figures for 2008-2017
(the build) are understated by up to half. Ratios on one trade list (PF, win rate) barely move; USD
sums, drawdowns and anything compared across eras or against MT5 do. «Verificar» therefore
judges price moves at one point value for both sides (`mt5.compare.in_points`; owner, 2026-09-30).

## Evidence
- 🔬 2026-09-30, `Strategy 10.1.79` (H1), «Verificar» 2022-06→2026-09 on FTMO, 439 paired trades
  with |P&L| > 30: median MT5/SQX ratio by year 1.12 (2022), 1.10 (2023), 1.03 (2024), 1.04
  (2025), 0.96 (2026) — the USDJPY rate's inverse. Same entry times, same lot (0.1).
