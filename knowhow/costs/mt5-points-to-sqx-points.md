---
q: MT5 spread to SQX spread; divide by 10 forex only; EURUSD spread 1 in MT5 is 0.1 in SQX; MT5 point vs SQX tick size; pipette vs pip; gold index spread same number; Brent Hantec multiply by 10; exotic FX divide by 100; conditions.py spread conversion; mt5_point to_sqx
tag: 🔬  date: 2026-10-01  see: costs/darwinex-real-spread, costs/where-the-spread-is
---
# MT5 points → SQX points = × `to_sqx` (MT5 `point` ÷ SQX `TICKSIZE`), per asset AND per firm — not a fixed ÷10
- SQX's "point" is the instrument's `TICKSIZE`; MT5's is `symbol_info.point` (= 10^-digits). Stored per
  asset in `assets/symbols/<S>.yaml` `mt5_point.<firm>.to_sqx`. Every cost in `assets/` is in SQX points.
- FX majors and JPY crosses, FTMO and Hantec: **0.1** (FTMO EURUSD spread 1 → 0.1 in SQX).
- Gold, silver, DAX40, DJ30, NIKKEI225, USA500, USATEC, both firms: **1** — same number.
- **Brent: FTMO `UKOIL.cash` 1, Hantec `UKOIL.h` 10** — one asset, two factors: ÷10 is no rule.
- Exotic FX (SQX ticks 0.001/0.01) may be ÷100. `mt5/verify/conditions.py` uses the LIVE point and
  warns when it differs from the stored `mt5_point`.

## Evidence
- 🔬 `mt5.live.ask("symbol", …)` on FTMO-Server4 and HantecMarketsMU-MT5, 2026-10-01, all 18 assets:
  FX point 1e-05 (5 digits), JPY 0.001, XAU/indices 0.01, XAG 0.001, UKOIL.cash 0.001, UKOIL.h 0.01.
- 🔬 `SQX_w1/user/data/data.db` `INSTRUMENTS`: `EURUSD_ftmo` TICKSIZE 0.0001, `USDJPY_ftmo` 0.01,
  `XAUUSD_ftmo` 0.01, `US500.cash_ftmo` 0.01, `UKOIL.cash_ftmo` 0.001.
- 📓 Verificar, FTMO XAUUSD 2026-09-29: "spread 35.0 puntos de SQX = 35 puntos de XAUUSD × 0.01".
