---
q: SQX fill convention open-to-open; entry price offset spread above bar open; intrabar entries pending fills or clock; zero-duration trades; rebuild P/L from bars; point value per market regression; M1 execution grid
tag: 🔬  date: 2026-09-22  see: export/data-all-crossmarket, export/exits-and-m1-library, research/zero-duration-trades
---
# SQX fills this fleet at the logic-TF bar opens (entry and exit); nothing happens inside a bar
- Reprice on the logic timeframe's bar grid; M1 would create a fill mismatch. Switch to M1 only when exit-side median error ≠ 0 (stops/targets) — `crossmarket/mechanics/pricing.reconcile()` decides.
- Entry sits a constant spread above the bar open on gold; exits on the open. Judge price vs bar open, never the clock.
- Rebuild P/L as `(Open[exit]-Open[entry]) * Size * pointValue`; cost = `gross - reported` per trade; `pointValue` by regression.
- Check bar-open alignment against the bar index (`core.trades.on_bar_open()`), not `minute == 0` (wrong on M30).

## Evidence
- 757 strategies / 960,705 M30 trades (`raw/XAUUSD/MC_Trades/2026-09-19`): zero SL/TP/trailing exits; |exit − bar Open| median 0.0000,
  max 0.0100, 0 of 757 non-zero median; |entry − bar Open| median 0.0800, max 0.0900.
- Retest export (`Strategy 24.14.35`, 1,055 gold trades): entry error 0.05 (989) or 0.06 (66), exit 0 = Buy filled at ask. Silver, Brent median 0 →
  property of `XAUUSD_DukasM1_Infinox`. 0.05 on ~1,800 = 2.8 bps = 0.023 ATR. `fill_mismatch` now judged in median-ATR units vs `diagnostics.max_fill_error`.
  Cost recovered: `charged = 0.05 × Size + commission`; `mean_r` is open-to-open both sides → real and null on the same pricer.
- Conventions (XAUUSD M30, P/L corr): open-open 1.0000, close-open 0.9629, open-close 0.9512, close-close 0.8651; 100% of Open/Close prices = bar Open. Earlier H1: 1,101 trades, median error 0.0. `nulls/calibrate.convention()` measures per strategy.
- Late stamps: 4,613 of 960,705 entries (0.48%) off the 30-min grid; price vs bar Open identical to on-time ones (median +0.080, p1 +0.080, p99 +0.090); none outside [0, 0.10].
  Retest export: gold 19 late at minute 1/31, +0.05; silver 72, Brent 67 scattered, +0.000. `crossmarket` `diagnostics.min_on_open` (clock-based) measures nothing real.
  Not: minute-stamped entries = intrabar pending fills (36-strategy export 573/48,894; silver 91.8%, Brent 91.4% on-open) — price check shows clock artefact. 🤔 EURUSD retest strategy entries are minute-level throughout (`2008.01.07 11:12:00`), not re-checked by price.
- Zero-duration: 12,824 of 960,705 (1.33%); retest 69/1,124 gold, 69/913 silver, 60/842 Brent; all `Exit Signal`, Open time = Close time.
  Silver/Brent same price (P/L = cost, −18.6 $ / −26.9 $ mean); gold differs by 0.05 (−16.3 $). Real trades; invisible to duration tests.
- P/L rebuild r = 0.9996 on XAUUSD, XAGUSD, BRENT (2,031 / 2,005 / 1,321 trades); residual cost+swap ~20 $/trade metals, ~29 $ Brent.
  Used by `strategies/crossmarket/simulate/metrics.py` to price nulls in account currency (net profit, DD, Ret/DD, Sharpe, PF).
- Point value = slope of P/L on `(close−open) × Size`, R² ≈ 0.999, residual = swap: XAUUSD 99.8 (configured 100), XAGUSD 5002 (5,000-oz contract),
  BRENTCMDUSD 100.0. `pricing.point_value()` — silver/Brent have no `assets/` file.
