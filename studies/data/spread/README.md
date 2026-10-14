# spread — what the spread really is

Built 2026-09-27 on the owner's request: building on Dukascopy's M1 and retesting at DATATICK
on Darwinex is embarrassingly expensive, and the one thing Darwinex's tick feed has that
Dukascopy's bars lack is the ask — the spread. XAUUSD and USDJPY first (owner, same day): an
asset whose price and spread explode, and a forex pair supposed to stay put. One half stays:

- **Step 4 — describe the spread.** Per asset, independent of any strategy: the spread of every
  minute of Darwinex's ticks, by year in points and in basis points of price, by hour; whether
  the relative spread is constant (owner's ±20 %); if not, which model reconstructs it best back
  to Dukascopy's first day; and the cost each segment should carry in SQX, times the safety factor (`safety.factor` of the ledger, 1.0 since 2026-10-04).

```
core.tickfile ─▶ inputs ─▶ measure ─▶ verdict (constancy, model ◀─ model.MODELS) ─▶ asset / scan     step 4
```

| file | what it does | run it | in → out |
|---|---|---|---|
| `asset.py` | One asset's spread report as the contract's data: the proposal, by year, by hour, the model, the tail. | imported | tables → result |
| `band.py` | The daily spread as a curve of price: its mean and its quantile band, for the MC Retest's spread range. | imported | days → curves |
| `bands.py` | The spread band of each asset: its daily mean spread as a curve of price, with a 2.5–97.5 % band for the MC Retest. | `python3 -m studies.data.spread.bands [--symbol S]` | ticks → `spread/<tick feed>/band.{json,html,md}`, `band_days.parquet`, `band_summary.json` |
| `funded.py` | The funded-firms method for an asset's spread: the widest firm's % of price, times the segment's price. | imported | ticks_hist + bars → spreads, slippage |
| `fundedswap.py` | The worst swap of the funded accounts, side by side, read live from each firm's MT5 server. | imported | asset → {long, short} |
| `inputs.py` | What the spread study reads: its knobs, a tick feed's minutes, Dukascopy's daily volatility. | imported | files → frames |
| `measure.py` | The spread as measured: per minute, per day beside Dukascopy's volatility, per year, per hour. | imported | minutes → tables |
| `model.py` | The ways the daily relative spread can be reconstructed where Darwinex has no ticks. | imported | days → params → days |
| `onboard.py` | Recompute the spreads and slippage of existing cards by the funded-firms method. | `python3 -m studies.data.spread.onboard [--symbol S] [--write]` | ticks_hist → `assets/` |
| `scan.py` | Step 4's spread study: each asset's real Darwinex spread, whether it is constant, and what SQX should carry. | `python3 -m studies.data.spread.scan [--symbol S]` | ticks + bars → `spread/<tick feed>/{daily,hours,minutes}.parquet, summary.json, spread.*` |
| `tooltips.py` | One sentence per config.yaml knob of the spread study, for the window's configuration drawer. | imported | — |
| `verdict.py` | Whether the relative spread is constant, which model reconstructs it best, and what to declare in SQX. | imported | tables → decision |
| `config.yaml` | Every knob; the owner's two numbers are `ledger:` placeholders | — | — |

## Decisions the code carries, and whose they are

- **The spread that counts is the first tick's of each minute** (`spread_open`): what a market
  order at that bar's open fills at, at DATATICK precision. The owner builds at market only.
  The time-weighted one is kept beside it; at the top of the hour the first tick is ~13 % wider
  than the minute's average, and that is precisely what an H1 entry pays.
- **A long pays the spread at its entry, a short at its exit.** SQX prices on Dukascopy's bid
  and adds the spread to the ask side; so does the market.
- **The mean, not the median**: a cost accrues its mean. The tail (rollover, news) is real money.
- **The model is chosen by its error on years it did not see**, both ways around `model.split`;
  backwards is the direction the Dukascopy years need. `relativo` wins outright if the owner's
  constancy test passes.
- **The proposal is a % commission** (owner: «mantener el % y poner un poquito de spread»):
  SQX charges `PercentageBased` once per trade on the open price (OPEN.md #26, settled
  2026-09-27), and a round trip pays one whole spread. The «poquito de spread» on top is the
  owner's to name; the points column is the same cost expressed as a flat spread at the
  segment's median price.
- **The owner can pin the model** (`model.fixed`): 2026-09-27 he chose `relativo` (spread
  proportional to price) for the five index CFDs, although fixed-points or volatility + price
  validated better — those carry 2018–19's wide Darwinex regime back to 2012 prices.
- **The MC Retest's spread range is in multiples** (`verdict.mc_multiples`): the 2.5–97.5 %
  quantiles of measured day ÷ the model's mean, times the spread the task runs at. Never pooled
  points across a window: SQX draws one spread per run, and 2012's price is not 2023's.
- **It proposes and never writes `assets/`** — except `onboard.py --write`, which the owner
  invokes (`/asset-onboard`) and which writes only through `core.assetwrite`.

- **The band models the daily MEAN spread** (owner, 2026-09-27: «el spread medio diario … y su
  desviación»): SQX's MC Retest draws ONE spread per simulation for the whole backtest
  (`RandomizeSpread.java`, uniform on 0.1-point steps), so the minute's tail — the rollover — is
  not what one run pays. The curve form, the quantity and the quantiles are `band.` knobs.

## What it cannot tell

- **The spread before October 2017 is modelled, never measured.** The build segment
  (2008–2017) is 97 % model. The validation measures the model on 2017–2026 only; brokers'
  spreads were plausibly wider before, so the reconstruction there is more likely short than
  long — the safety factor (1.0 since 2026-10-04, no margin) does not cover it.
- **USDJPY's chosen model leans on the price level**, which over 2017–2026 moved with time;
  back in 2011–2012 (USDJPY at 76–80) it predicts the thinnest spreads of all. See
  `POSSIBLE_IMPROVEMENTS.md`.
