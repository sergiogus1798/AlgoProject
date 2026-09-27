# spread — what could change, and why it has not

Measured 2026-09-27 on XAUUSD and USDJPY (`python3 -m studies.data.spread.scan`).

## The model back in time

Two-way validation, split at 2022, mean |error| of each year's mean relative spread:

| model | XAUUSD backwards | XAUUSD forwards | USDJPY backwards | USDJPY forwards |
|---|---|---|---|---|
| `relativo` | 25 % | 27 % | 47 % | 32 % |
| `puntos` | 119 % | 26 % | 97 % | 49 % |
| `volatilidad` | **19 %** | 32 % | 40 % | 29 % |
| `volatilidad_precio` | 19 % | 37 % | **10 %** | 10 % |

- **Gold 2020** (covid) is 46–49 % short under every model: a regime, not volatility.
- **USDJPY's winner uses the price level.** Over 2017–2026 the level moved with the calendar
  (108 → 159) and the spread with it; the fit may be reading «time», not «price». Applied to
  2011–2012 (76–80) it gives the thinnest spreads anywhere in the history — optimistic exactly
  where nothing checks it. Alternatives, in order of cost: take `volatilidad` for forex (40 %
  backwards, but no extrapolation in level); floor any modelled year at the lowest measured
  year; or ask Darwinex/the broker for older spread history.
- **Hour-of-day effects** are applied as a fixed multiplier on the modelled day; a model fitted
  hourly (log rel ~ log rv + hour) would let the shape change with volatility. Not tried.

## The validation against SQX itself

The repricing has not been checked against a real DATATICK retest on the Darwinex tick feed —
one worker job on a few strategies of an existing harvest. Until it is, «exact where the ticks
exist» is argued from how SQX fills, not measured.
