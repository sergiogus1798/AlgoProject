# spread — what the spread really is, and what a strategy earns once it pays it

Built 2026-09-27 on the owner's request: building on Dukascopy's M1 and retesting at DATATICK
on Darwinex is embarrassingly expensive, and the one thing Darwinex's tick feed has that
Dukascopy's bars lack is the ask — the spread. XAUUSD and USDJPY first (owner, same day): an
asset whose price and spread explode, and a forex pair supposed to stay put. Two halves:

- **Step 4 — describe the spread.** Per asset, independent of any strategy: the spread of every
  minute of Darwinex's ticks, by year in points and in basis points of price, by hour; whether
  the relative spread is constant (owner's ±20 %); if not, which model reconstructs it best back
  to Dukascopy's first day; and the cost each segment should carry in SQX, times the owner's 1.25.
- **Step 8 — reprice.** Per strategy of a gate harvest: SQX's flat spread given back and the real
  one taken, trade by trade, at the minute each trade pays it. Which strategies stop earning.

```
core.tickfile ─▶ inputs ─▶ measure ─▶ verdict (constancy, model ◀─ model.MODELS) ─▶ asset / scan     step 4
                 inputs ─▶ reprice (daily.parquet, hours.parquet from the scan) ─▶ one / many / report   step 8
```

| file | what it does | run it | in → out |
|---|---|---|---|
| `config.yaml` | Every knob; the owner's two numbers are `ledger:` placeholders | — | — |
| `tooltips.py` | One Spanish sentence per knob, for the window's drawer | imported | — |
| `inputs.py` | The knobs, a tick feed's minute table cached against the `.dat`'s stamp, Dukascopy's daily volatility, a harvest's trades and names, and the spread each of its tasks charged (from the live or the retired `project.cfx`) | imported | files → frames |
| `measure.py` | The spread per day beside the volatility, per year, per hour, per weekday × hour; the spread standing at any instant | imported | minutes → tables |
| `model.py` | **The four models** of the daily relative spread, one contract and one registry | imported | days → params → days |
| `verdict.py` | Constancy against the tolerance, the two-way validation, the model chosen, the reconstruction and the proposal per segment | imported | tables → decision |
| `asset.py` | One asset's report as the contract's data | imported | tables → result |
| `scan.py` | **Step 4's command** | `python3 -m studies.data.spread.scan [--symbol S]` | ticks + bars → `spread/<tick feed>/{daily,hours,minutes}.parquet, summary.json, spread.*` |
| `band.py` | The daily mean spread as a power law of price, `a · price^b`, for the mean (least squares) and each quantile (quantile regression, rearranged so they never cross); the band's calibration by year | imported | days → curves |
| `bands.py` | **The band's command**, one report per asset; the extreme quantiles are the MC Retest's RandomizeSpread Min and Max | `python3 -m studies.data.spread.bands [--symbol S]` | ticks → `spread/<tick feed>/band.{json,html,md}`, `band_days.parquet`, `band_summary.json` |
| `registry.py` | What SQX's own `data.db` says of a symbol, read-only: its DukasM1 and DarwTick feeds, instrument, data range, and the mean swap of every broker's variant | imported | symbol → facts |
| `onboard.py` | **The asset onboarding command** (`/asset-onboard`): plans segments, spreads, slippage, commission, swap, triple swap and MC range by the owner's rules in `onboard:`; with `--write`, the one module here that writes `assets/`, through `core.assetwrite` | `python3 -m studies.data.spread.onboard --symbol S --kind index\|metal\|forex [--write] [--spread-only]` | symbol → `assets/symbols/<S>.yaml` |
| `reprice.py` | The spread each trade really paid (tick or model), its adjusted P/L, and the twin table kept on disk | imported | trades → trades |
| `one.py` | One strategy's reading as the contract's data | imported | trades → result |
| `many.py` | The population panel and the verdict per strategy | imported | results → panel |
| `report.py` | **Step 8's command**, after `gate.report` and `scan` | `python3 -m studies.data.spread.report --project P --databank D --feed F [--strategy S]` | harvest → `reports/<P>/<D>/<day>/spread/`: `trades.parquet` (every trade with SQX's P/L and the one at the real spread), `verdict.csv` |

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
- **Onboarding rules are data** (`onboard:` in `config.yaml`, owner 2026-09-27): per kind the
  segments, commission, swap, triple-swap night and the build model; the factor is the ledger's.
- **Three versions of every trade are kept** (owner, 2026-09-27): `trades.parquet` carries the
  harvest's columns untouched — `Profit/Loss` is SQX's, at the costs its task declared — and
  beside them the spread at entry and at exit, `Profit/Loss spread real` and `Profit/Loss spread y
  slippage reales`. SQX charges its slippage on BOTH fills (gold: +0.025 at entry, −0.025 at exit
  at 2.5 points); the variable one is half the real spread at each fill, the owner's convention.
  `reprice.judge` says which version «se rompe» is read against (default: both costs). The page of a
  strategy draws the three curves per segment, each from zero, since each segment is its own backtest.
- **`action: mark`**: the repricing flags the strategies the real spread breaks; `drop` would
  write DESCARTAR for /curate.

- **The band models the daily MEAN spread** (owner, 2026-09-27: «el spread medio diario … y su
  desviación»): SQX's MC Retest draws ONE spread per simulation for the whole backtest
  (`RandomizeSpread.java`, uniform on 0.1-point steps), so the minute's tail — the rollover — is
  not what one run pays. The curve form, the quantity and the quantiles are `band.` knobs.

## What it cannot tell

- **The spread before October 2017 is modelled, never measured.** The build segment
  (2008–2017) is 97 % model. The validation measures the model on 2017–2026 only; brokers'
  spreads were plausibly wider before, so the reconstruction there is more likely short than
  long — the factor 1.25 is the only margin against it.
- **USDJPY's chosen model leans on the price level**, which over 2017–2026 moved with time;
  back in 2011–2012 (USDJPY at 76–80) it predicts the thinnest spreads of all. See
  `POSSIBLE_IMPROVEMENTS.md`.
- **The repricing changes the spread only**, not Darwinex's own bid path (0.09 median difference
  on gold, 0.001 on USDJPY against Dukascopy's close). It has not yet been checked against a
  real DATATICK retest on Darwinex — the test that would license it as that retest's stand-in.
