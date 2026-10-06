# engines/market — how a trade is priced from bars, the way SQX priced it

One copy of what every study that re-prices trades needs: the ATR a trade is scaled by, the
point value measured from the trades themselves, the cost SQX charged, and which bar price SQX
filled at — reconciled against SQX's own P/L before anything downstream is trusted.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Names what the package is; holds no code | — | — |
| `calibrate.py` | ATR, point value, charged cost, sizing by volatility, the fill conventions and the P/L reconciliation that licenses a null | imported | trades + bars → point value, cost, fill |
| `reprice.py` | The one repricer: a market-order trade's money P/L and the declared cost it was charged, from RAW bar opens and the task's costs (card → `costs`). Spread and slippage go on the fill here and only here (long: in at open + spread + slippage, out at open − slippage; short: the mirror, spread on the entry), the fill rounded to the tick; swap per night on Mon–Fri rollovers with the triple night — percent per year on the entry notional, or points × `tick_step` (= tick_size / 10) on forex cards — signed as the card and MT5 sign it (negative = the holder pays, both sides); commission once at the open. `cost` is the unrounded formula `PV·size·(spread + 2·slippage) + swap + commission`; `pnl` is rounded to the cent. Audited on 1,312 long trades at 0 % commission and percent swap to `0.02 + 2·tick·PV·size` per trade; shorts, a non-zero commission and a points swap are UNVERIFIED against SQX. `calibrate.charged()` is SQX's residual (swap and commission only): new code prices with this file | imported | feed + segment → `Costs`; bar opens, times, side, size, `Costs` → (P/L, cost); bars + positions → opens |
| `atr.py` | The ATR exactly as SQX computes it for an ATR-based stop — Wilder with an averaged start, rounded to 6 as the stop formula rounds it. Not `calibrate.atr`, which is a rolling mean | imported | bars → ATR per bar |
| `excursion.py` | Per trade: the ATR of the bar closed before the entry, MAE and net result in that ATR, winner = net P/L > 0. Shared by step 8 (`maeDepth`) and step 24 (`atrCalculator`) so both measure the same number | imported | trades + ATR → per-trade table |
| `replay/` | *Not built (encargo 16).* Trade replay on the bar tape | — | — |
| `feed/` | Whether the feed itself is sound, minute by minute: the trailing hour-of-week scale, spikes and their reversion, frozen runs, gaps in a session (encargo 17) | imported | bars → anomalies |

`studies/transfer/crossmarket/mechanics/pricing.py` keeps what only the cross-market study needs — the
price-error reconciliation, the fill profile, the per-market unit — and imports the rest from here.
