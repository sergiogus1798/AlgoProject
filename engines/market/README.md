# engines/market — how a trade is priced from bars, the way SQX priced it

One copy of what every study that re-prices trades needs: the ATR a trade is scaled by, the
point value measured from the trades themselves, the cost SQX charged, and which bar price SQX
filled at — reconciled against SQX's own P/L before anything downstream is trusted.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Names what the package is; holds no code | — | — |
| `calibrate.py` | ATR, point value, charged cost, sizing by volatility, the fill conventions and the P/L reconciliation that licenses a null | imported | trades + bars → point value, cost, fill |
| `atr.py` | The ATR exactly as SQX computes it for an ATR-based stop — Wilder with an averaged start, rounded to 6 as the stop formula rounds it. Not `calibrate.atr`, which is a rolling mean | imported | bars → ATR per bar |
| `replay/` | *Not built (encargo 16).* Trade replay on the bar tape | — | — |
| `feed/` | Whether the feed itself is sound, minute by minute: the trailing hour-of-week scale, spikes and their reversion, frozen runs, gaps in a session (encargo 17) | imported | bars → anomalies |

`studies/transfer/crossmarket/mechanics/pricing.py` keeps what only the cross-market study needs — the
price-error reconciliation, the fill profile, the per-market unit — and imports the rest from here.
