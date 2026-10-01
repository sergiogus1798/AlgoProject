---
q: SQX swap types points percent money formula; percent swap annual or nightly 360; convert points to percent; triple swap day per feed WEDNESDAY FRIDAY; tripleSwapOn override asset file; swap points unit tickStep vs tick_size; JPY swap 10x overcharge; swap_long swap_short assets yaml units
tag: 🔬  date: 2026-10-01  see: costs/per-task-costs, costs/where-the-spread-is, costs/funded-accounts-real-costs
---
# `points` swap is in tickStep, not tick_size; `percent` swap is an ANNUAL rate (÷100 ÷360); the triple-swap day is per feed
- `swap_long`/`swap_short` in `assets/symbols/*.yaml` (points type, forex) are SQX points = **tickStep**: one night = size × pointValue × tickStep × pts. On FX tickStep = tick_size/10 (JPY 0.001, 5-digit 0.00001). A model that prices them with `instrument.tick_size` overcharges FX swap **10×**. Spread and slippage points stay in tick_size.
- One night × nights held (3 on the triple day). `pct_annual = points × tickStep × 36000 / reference_price` (dropping the 100 → 100× too small, still plausible).
- `tripleSwapOn`: WEDNESDAY for FX, XAUUSD, XAGUSD; FRIDAY for BRENT, DJ30, NIKKEI225, USA500, USATEC — these override via a top-level `swap:` in their asset file.
- ⚠️ An asset-file `swap:` replaces the policy block wholesale (`core.assetdata.load` = `{**policy, **asset_file}`): repeat `rollout_hour`.

## Evidence
📓 `SwapTypes` = `points`, `percent`, `money`. Master: `points` on every FX pair and gold, `money` on index CFDs. `SwapCalculator.calculateSwapCost`:

| type | one night |
|---|---|
| `points` | `size × pointValue × tickStep × swap` |
| `percent` | `size × pointValue × openPrice × (swap / 100 / 360)` |
| `money` | `size × swap` |

🔬 tickStep, 2026-10-01: InstrumentInfo in `Test_Calib_USDJPY_H1` retest tasks: USDJPY tickSize 0.01, tickStep 0.001, pointValue 631.337; `projectsBackup/install-configs-2026-09-21/w2-retester-before/project.cfx`: AUDJPY 0.01/0.001, EURUSD GBPUSD AUDUSD USDCAD USDCHF 1E-4/1E-5, XAUUSD 0.01/0.01, XAGUSD 0.001/0.001. USDJPY.yaml `swap_short −21.37` came from FTMO −13.97 $/lot/night ÷ (653.92 × 0.001). Priced with tickStep that is −13.5 $/lot/night; with tick_size, −135. In the random-entry null (`scratchpad null/`, H1, 100 trades/yr, ATR-risk sizing), the tick_size version made short USDJPY lose −25.6 k$/yr IS against −5.2 k$/yr with tickStep.
- Gold `-73.42` pts long, tick 0.01, ref 3500 → 7.55 % annual; short `+38.76` → 3.99 %. Either way one night on one lot = $73.42 / $38.76.
- Per feed: WEDNESDAY 17 (every FX pair, XAUUSD, XAGUSD); FRIDAY 7 (`BRENTCMDUSD_ftmo`, `DJ30`, `NIKKEI225` ×2 feeds, `USA500` ×2, `USATEC`); NEVER 1 (`EURUSD_M1_dukas`, stale, unclaimed). `load()` agrees with the master on all 19.
- Wrong day matters: triple = 3× one night; BRENT short alone −9.54 % annual.
- 🤔 `studies/data/spread/registry.broker_swaps` rescales broker points by TICKSIZE ratios. That is right only while every variant has the same tickStep/tickSize ratio (true for the variants above).
