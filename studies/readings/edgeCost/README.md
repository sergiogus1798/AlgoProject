# edgeCost — how much edge each trade carries over what it costs to make

Encargo 11. One question: rebuild the gross P&L SQX never exports directly, and read it
against the cost this project models today, in two places — step 8, as a screen over a
population right after the OOS gate, and step 25, the very end of the workflow, on the
version that will be traded.

The spread is never a charge in the export: it sits inside the fill price
(`knowhow/costs/where-the-spread-is.md`), so gross has to be rebuilt as
`Profit/Loss + comisión + coste_spread`, never read off a residual. `costs.py` is the only
place that formula lives.

```
inputs ─▶ costs ─▶ one / many ─▶ report
 the      the        the edge      the
 harvest  gross and   and the       command
 or       the         breakeven,
 export   reconcile-  per strategy
          ation        or the panel
```

| file | what it does | run it | in → out |
|---|---|---|---|
| `inputs.py` | The knobs, and the harvest this study reads (trades and the identity → strategy name it carries no other way) | imported | folder → frames |
| `costs.py` | Rebuilds gross P&L per trade from the fill prices and the asset's declared cost, and reconciles it against what SQX reported; the provisional-cost and issue-26 warnings | imported | trades + asset → priced trades, reconciliation |
| `one.py` | **One strategy against its own edge-per-cost bar, as the contract's data**: the headline numbers, the reconciliation, the by-hour and by-weekday breakdown | imported — the window calls it | one strategy's priced trades → result |
| `many.py` | Every strategy of one harvest, judged against the same bar, as one panel | imported | priced trades → panel |
| `report.py` | **The command**: every strategy of one harvest to `verdict.csv` and its page, or `--strategy` for one read in full | `python3 -m studies.readings.edgeCost.report --project USDJPY_emaCross_H1 --databank Results --feed USDJPY_DukasM1_the5ers [--strategy "Strategy 10.9.51"]` | harvest → reports |
| `tooltips.py` | One sentence per `config.yaml` knob, for the window's configuration drawer | imported | — |

## What is the owner's, not this code's

`min_edge_spreads` and `action` (`mark`/`drop`) in `config.yaml` are the owner's bar, fixed
before looking at results (owner, 2026-09-26). The threshold is registered in
`ledger/thresholds.yaml`.

## Verification, before any gross figure is trusted

`costs.reconcile()` compares a price-only P&L (`Close price - Open price`, signed, times
`Size` and the asset's `point_value` — the fill prices already carry the spread) against
`Profit/Loss + commission_cost`. On `USDJPY_emaCross_H1` (92,502 trades, zero commission)
the correlation is 1.000000; on `XAU_ISOOS_ejemplo` (118,257 trades, `PercentageBased`
commission) it is 0.999553 — both above the 0.99 floor `studies/readings/monkey/` set as
precedent. Below that floor the gross is decoration; `one.run` and `many.run` both refuse
to stay silent about it (a `reconciliation` warning fires).

## What is still provisional

Every asset's spread, commission, slippage and swap are the owner's stand-ins until the
broker's real figures replace them (`assets/symbols/*.yaml`, `why: PROVISIONAL`) — this
module inherits that, and says so in its warnings. On top of that, **OPEN.md issue 26** is
open specifically for `no_forex` assets (XAUUSD, the metals and index CFDs): whether the
percentage commission is charged once per trade or once per leg is unverified, a factor of
two this module cannot resolve without a SQX run it is not allowed to make on its own
(`knowhow/costs/commission-methods.md`). Every XAUUSD result this module produces is
`costs_provisional` for that reason; USDJPY is not, because its commission is `0.0` either
way.

## What this module deliberately does not do

- **It does not build a Sharpe-vs-cost-multiplier curve.** The MC Retest task perturbs the
  spread over a *range*, not the four discrete multiples (1x/1.5x/2x/3x) the encargo asked
  for, and `SharpeRatio` is not one of the 30 metrics a MC Retest simulation can
  reconstruct — it is computed on the daily equity curve, which no simulation file carries
  (`studies/breakage/mcRetest/model/recon.py`, `ANALOGUE`). This is a declared gap, not an
  invented curve.
- **It never re-stages a `.sqx`.** Step 8 reads the gate's harvest; step 25 reads whatever
  trades export the traded version produces, in the same shape. Neither call touches SQX.
