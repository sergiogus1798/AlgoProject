# engines/market — how a trade is priced from bars, the way SQX priced it

One copy of what every study that re-prices trades needs: the ATR a trade is scaled by, the
point value measured from the trades themselves, the cost SQX charged, and which bar price SQX
filled at — reconciled against SQX's own P/L before anything downstream is trusted.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | A trade priced from bars the way SQX priced it. | — | — |
| `atr.py` | The ATR exactly as SQX computes it for an ATR-based stop: Wilder with an averaged start. | imported | bars → ATR per bar |
| `calibrate.py` | Recover from the real trades what SQX charged and how it sized, and prove it reconciles. | imported | trades + bars → point value, cost, fill |
| `excursion.py` | Each trade's adverse excursion and final result in units of the ATR the stop would have used. | imported | trades + ATR → per-trade table |
| `reprice.py` | The one repricer: a market-order trade's money P/L from raw bar opens and the task's declared costs, as SQX charges them. | imported | feed + segment → `Costs`; bar opens, times, side, size, `Costs` → (P/L, cost); bars + positions → opens; harvest trades + bars + `Costs` + feed → `enter, leave, side, stop, pnl, cost` |
| `replay/` | Each trade walked again from a shifted entry until its recomputed ATR stop or its scheduled exit (tier 2 of the delay; encargo 56 F3) | imported | stop harvest + delay → exits |
| `feed/` | Whether the feed itself is sound, minute by minute: the trailing hour-of-week scale, spikes and their reversion, frozen runs, gaps in a session (encargo 17) | imported | bars → anomalies |

The cross-market study imports this package (`studies/transfer/crossmarket/`); it has no pricing module of its own any more (`mechanics/pricing.py` no longer exists, checked 2026-10-11).
