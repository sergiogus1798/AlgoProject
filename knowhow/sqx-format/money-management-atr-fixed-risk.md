---
q: How does the workflow size each trade: fixed $1,000 risk over 4*ATR(20)?
kw: which money management do the strategies use, ATRRiskBasedSizingFixedRisk parameters, why does Size vary per trade, risk per trade in SQX, convert SQX P&L to another risk or stop, lastSettings.xml MoneyManagement use=true, fixed risk R multiple, size a strategy with no stop, worst daily floating loss, MAE per day sizing, portfolio factor 1 / worst_day
tag: 🔬  date: 2026-10-15  see: export/orderstocsv-schema, sqx-format/daily-equity-bin
---
# The workflow's strategies size every trade at a FIXED $1,000 risk over 4·ATR(20) — SQX's P&L is already fixed-risk
The active method in `lastSettings.xml` (`Method[@use="true"]`) is `ATRRiskBasedSizingFixedRisk`:
`Amount` 1000 (USD per trade, on the 100k initial — not compounding), `ATRPeriod` 20, `ATRMult` 4,
`Decimals` 2, `LotsIfNoMM` 0.01, `MaxLots` 500. So `Size` varies trade by trade with the ATR. At risk
a stop of X·ATR(20) a trade's P&L would be SQX's × 4 / (1000 · X) × r · S, but since step 24 was deleted
(2026-10-11) no strategy has a stop: the portfolio engine keeps this money management and scales it by one
constant per strategy, `1 / worst_day` — its worst build day of floating loss, the sum of the MAE of the
trades closing that day (`portfolio/common/construct/inputs/risk.py`, OPEN #113 (1), 2026-10-15).

## Evidence
- Archived USDJPY M30 `4d679e…/2026-09-28T0919/strategy.sqx`, 2026-09-30: every other method in
  `lastSettings.xml` has `use="false"`; `settings.xml` `MoneyManagement.UseFromStrategy` false,
  `InitialCapital` 100000; its 2,094 trades' `Size` runs 0.68-15.37 (median 3.67).
- `tests/test_construct_sizing_nostop.py`: the stopless sizing (worst build day by MAE, OOS ignored). All 39 archived harvests carry `MAE ($)` (2026-10-15).
- 2026-10-14, encargo 61: `AlgoData/audit/money-management/por-stop-2026-10-14.md` (NIKKEI M30 `Stop_p90`, `scratch/mm_por_stop.py`).
- 🔬 Stock `FixedAmount` (`RiskedMoney`, `Decimals`, `LotsIfNoMM`, `MaxLots`) sizes by the order's own `sl` (none: `LotsIfNoMM`) and has MT5 templates; swapping to it scales sizes by `ATRMult/X`, ratios unchanged unless `MaxLots` bites.
- 🤔 2026-10-15 (encargo 61-4d) `mt5.verify` runs two modes, 1 lot (`FixedSize`) and 1,000 USD from the stop (`FixedAmount` `RiskedMoney`, EA input `mmRiskedMoney`). The doctrine's strategies have NO stop since step 24 was removed (2026-10-11), so the `risk` mode is skipped for them («riesgo fijo: no aplica, sin SL», owner 2026-10-15) and the 1-lot verdict stands: `FixedAmount` without `sl` trades `LotsIfNoMM`, not a risk size.
