---
q: How does the workflow size each trade: fixed $1,000 risk over 4*ATR(20)?
kw: which money management do the strategies use, ATRRiskBasedSizingFixedRisk parameters, why does Size vary per trade, risk per trade in SQX, convert SQX P&L to another risk or stop, lastSettings.xml MoneyManagement use=true, fixed risk R multiple
tag: 🔬  date: 2026-09-30  see: export/orderstocsv-schema, sqx-format/daily-equity-bin
---
# The workflow's strategies size every trade at a FIXED $1,000 risk over 4·ATR(20) — SQX's P&L is already fixed-risk
The active method in `lastSettings.xml` (`Method[@use="true"]`) is `ATRRiskBasedSizingFixedRisk`:
`Amount` 1000 (USD per trade, on the 100k initial — not compounding), `ATRPeriod` 20, `ATRMult` 4,
`Decimals` 2, `LotsIfNoMM` 0.01, `MaxLots` 500. So `Size` varies trade by trade with the ATR. At risk
r of an account S with a stop of X·ATR(20), a trade's P&L = SQX's × **4 / (1000 · X)** × r · S — one
constant per strategy (`portfolio/common/construct/inputs/risk.py`). A stop grafted by step 24 is a
different number (`StopLossCoef1`), read from the strategy itself.

## Evidence
- Archived USDJPY M30 `4d679e…/2026-09-28T0919/strategy.sqx`, 2026-09-30: every other method in
  `lastSettings.xml` has `use="false"`; `settings.xml` `MoneyManagement.UseFromStrategy` false,
  `InitialCapital` 100000; its 2,094 trades' `Size` runs 0.68-15.37 (median 3.67).
- `tests/test_portfolio_search.py`: the mapping read back, and X read from a stop grafted in memory.
- 2026-10-14, encargo 61: `AlgoData/audit/money-management/por-stop-2026-10-14.md` (NIKKEI M30 `Stop_p90`, `scratch/mm_por_stop.py`).
- 🔬 Stock `FixedAmount` (`RiskedMoney`, `Decimals`, `LotsIfNoMM`, `MaxLots`) sizes by the order's own `sl` (none: `LotsIfNoMM`) and has MT5 templates; swapping to it scales sizes by `ATRMult/X`, ratios unchanged unless `MaxLots` bites.
- 🤔 2026-10-15 (encargo 61-4d) `mt5.verify` runs two modes, 1 lot (`FixedSize`) and 1,000 USD from the stop (`FixedAmount` `RiskedMoney`, EA input `mmRiskedMoney`). The doctrine's strategies have NO stop since step 24 was removed (2026-10-11), so the `risk` mode is skipped for them («riesgo fijo: no aplica, sin SL», owner 2026-10-15) and the 1-lot verdict stands: `FixedAmount` without `sl` trades `LotsIfNoMM`, not a risk size.
