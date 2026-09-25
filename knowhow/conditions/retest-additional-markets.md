---
q: RetestOnAdditionalMarkets Setup XML; per-market costs timeframe; MainTestValues inheritance mask override; cross-timeframe retest in one task; AcceptanceSettings MinMarkets market="1"
tag: 🔬  date: 2026-09-23  see: conditions/crossmarket-crosstf-no-conditions, conditions/selection-window, costs/per-task-costs
---
# `RetestOnAdditionalMarkets` = one full `<Setup>` per extra market; `<MainTestValues>` decides which values win
- `MainTestValues` attr `true` = take the main test's value, ignore the Setup's. To override (e.g. timeframe) flip the attribute; editing `<Chart timeframe=…>` alone does nothing.
- A Setup can use another timeframe on the same symbol → crossTF needs no second project. Runs the strategy as built (bars-constant); rescaled periods need fabricated variants.
- `<AcceptanceSettings>` makes it a selection filter; leave it `use="false"` when the check is evidence.

## Evidence
Frozen donor `AlgoData/projectsBackup/XAUUSD_base_2026-09-21/project.cfx` (zip of per-task XML), `Retest-Task4.xml`,
`<CrossChecks><RetestOnAdditionalMarkets><Settings><Setups>`:
```xml
<Setup dateFrom="2008.01.01" dateTo="2022.12.31" testPrecision="2" session="No Session"
       slippage="0" minDist="10" engine="MetaTrader5 (hedged)">
  <Chart symbol="XAUUSD_DukasM1_Infinox" timeframe="M30" spread="8" />
  <Commissions>…</Commissions>
  <Swap use="false" … />
  <MainTestValues timeframe="true" dates="true" precision="true" spread="true" slippage="true"
                  commissions="true" swap="false" session="false" subcharts="false" />
</Setup>
```
- Donor `timeframe="true"` → its `timeframe="M30"` is inert; `swap`, `session` already `false` → Setup's own values live. Mask confirmed by a run 2026-09-23.
- Acceptance: `<Check>all</Check>`, `<MinConditions>`, `<MinMarkets>`; condition `market="1"` picks which Setup is scored.
