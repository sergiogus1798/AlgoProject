# edgeCost — how much edge each trade carries over what it costs to make

Encargo 11. One question: rebuild the gross P&L SQX never exports directly, and read it
against the cost this project models today, in two places — step 8, as a screen over a
population right after the OOS gate, and step 25, the very end of the workflow, on the
version that will be traded.

The spread is never a charge in the export: it sits inside the fill price
(`knowhow/costs/where-the-spread-is.md`), so gross has to be rebuilt as
`Profit/Loss + comisión + coste_spread`, never read off a residual. `costs.py` is the only
place that formula lives. **The spread cost itself is measured, never assumed**
(`spread_share.py`): a review BLOCKER (2026-09-26) found the first version's `SPREAD_SHARE
= 0.5` applied the same fraction to every feed, when the project's own knowhow already
showed it does not hold even between gold, silver and Brent on the same export.

```
inputs ─▶ spread_share ─▶ costs ─▶ one / many ─▶ report
 the      the round-trip   the        the edge      the
 harvest  cost ACTUALLY    gross and   and the       command
 or       embedded,        the         breakeven,
 export   measured off     reconcile-  per strategy
          the bars         ation        or the panel
```

| file | what it does | run it | in → out |
|---|---|---|---|
| `inputs.py` | The knobs, and the harvest this study reads (trades, the timeframe, the identity → strategy name it carries no other way) | imported | folder → frames |
| `spread_share.py` | **Measures** the round-trip spread actually embedded in the fill price, per feed and sample segment, against the M1 bars — refuses on a feed with no bars, or a segment too small to trust | imported | trades + feed → measured price offset |
| `costs.py` | Rebuilds gross P&L per trade from the fill prices and the ACTUAL measured cost, reconciles it against what SQX reported, and separately prices today's modelled cost (`assets/symbols/*.yaml`, undiluted) for the edge's denominator; the provisional-cost and issue-26 warnings | imported | trades + asset + feed → priced trades, reconciliation |
| `one.py` | **One strategy against its own edge-per-cost bar, as the contract's data**: the reconciliation (shown first), the headline numbers, the by-hour and by-weekday breakdown | imported — the window calls it | one strategy's priced trades → result |
| `many.py` | Every strategy of one harvest, judged against the same bar, as one panel | imported | priced trades → panel |
| `report.py` | **The command**: every strategy of one harvest to `verdict.csv` (`strategy, identity, …, verdict`, identity the harvest's own) and its page, or `--strategy` for one read in full | `python3 -m studies.readings.edgeCost.report --project USDJPY_emaCross_H1 --databank Results --feed USDJPY_M1 [--strategy "Strategy 10.9.51"]` | harvest → reports |
| `tooltips.py` | One sentence per `config.yaml` knob, for the window's configuration drawer | imported | — |

## What is the owner's, not this code's

`min_edge_spreads` and `action` (`mark`/`drop`) in `config.yaml` are the owner's bar, fixed
before looking at results (owner, 2026-09-26). The threshold is registered in
`ledger/thresholds.yaml`.

## The spread cost is measured, and it is feed-specific

`spread_share.measure()` reads the M1 bars (`core.barstore`) and takes the median gap
between each trade's fill price and its own bar's Open, per sample segment — the same
"locate on the grid, compare against the open" method `engines/market/calibrate.convention()`
uses for the monkey study, and the entry offset `knowhow/export/fill-and-pricing.md` already
measured on gold. Measured 2026-09-26 on the harvests this module was verified against:

| feed | segment | measured entry offset (price units) | declared spread today | ratio |
|---|---|---|---|---|
| `USDJPY_M1` | IS and OOS (one spread field) | 0.002 | 0.001 (0.1 pt × tick 0.01) | 2.0 |
| `XAUUSD_M1` | IS | 0.08 | 0.05 (5 pt × tick 0.01) | 1.6 |
| `XAUUSD_M1` | OOS | 0.15 | 0.10 (10 pt × tick 0.01) | 1.5 |

None of these is 0.5. The measured value — not the ratio — is what `costs.per_trade()` uses
for `spread_cost` (the actual cost gross has to remove); the DECLARED spread is used,
undiluted, only for `cost_today` (the "coste modelado hoy" denominator the encargo asks the
edge to be a multiple of). The two are deliberately never the same column, so a run built
years ago under a different spread never gets priced as if it ran under today's.

A feed with no entry in the bar library, or a sample segment under 30 trades, makes
`spread_share.measure()` raise rather than default to any number — `tests/test_edgecost.py`
checks both.

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
module inherits that, and says so in its warnings. The percentage commission of the
`no_forex` assets is charged once per trade, on the open price (OPEN.md issue 26, settled
2026-09-27 — `knowhow/costs/commission-methods.md`).

## What this module deliberately does not do

- **It does not build a Sharpe-vs-cost-multiplier curve.** The MC Retest task perturbs the
  spread over a *range*, not the four discrete multiples (1x/1.5x/2x/3x) the encargo asked
  for, and `SharpeRatio` is not one of the 30 metrics a MC Retest simulation can
  reconstruct — it is computed on the daily equity curve, which no simulation file carries
  (`studies/breakage/mcRetest/model/recon.py`, `ANALOGUE`). This is a declared gap, not an
  invented curve.
- **It never re-stages a `.sqx`.** Step 8 reads the gate's harvest; step 25 reads whatever
  trades export the traded version produces, in the same shape. Neither call touches SQX.
