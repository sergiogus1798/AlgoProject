# marketProfile/measure — the measures, one signature each

Holds what is measured on a series. It must never hold the null, the p-value or a filter: a
measure returns a statistic and, when it trades, the entry and exit bars — nothing about whether
that is a lot. `one.py` runs the same functions on the real series and on every null draw.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | `REGISTRY` — every function `config.yaml` may name — and `SYMMETRIC`, the ones with no direction | imported | — |
| `trades.py` | A signal's entry and exit bars (open to open), the t of its returns, the hit rate against the base rate | imported | mask → entry, exit, statistic |
| `structure.py` | Directionless: variance ratio, Hurst, Dickey-Fuller on the level and on the distance to the mean, autocorrelation of the range, narrow-against-wide | imported | series → statistic |
| `price.py` | Trend (lookback × hold, Fitschen's band), breakout (channel, false breaks), reversion (extreme in ATR), momentum (big bar), the break of a narrow bar | imported | series → statistic, trades |
| `pattern.py` | Bar states: inside bar, engulfing, k closes in a row followed or faded | imported | series → statistic, trades |
| `position.py` | One position at a time (numba): entry at the open after the signal, exit at the open after the exit signal, a cap in bars or a trailing distance | imported | masks → entry, exit |
| `rules.py` | `CONDITIONS` — every named entry, filter and exit, read from prices alone — and `rule`: an entry, its filters, an exit; what the long-horizon trend, the daily channel, the conditioned reversion and the pullback are built from in `config.yaml` | imported | series + frame → statistic, trades |
| `session.py` | The best hour, band and weekday, each chosen inside the draw too, and the break of a band's range | imported | series + calendar → statistic, trades |

Every measure is written for longs. The short side is the same function on the mirrored series
(`higher.mirror`, on top of `series.mirror`), so a long and a short can never drift apart.

A measure must be a rule a strategy could trade: one direction, fills at the next open, and **no
clock** — `rules.py` reads nothing of the calendar but `least`, and `tests/test_marketprofile.py`
checks it. The four measures of `session.py` do read it: `config.yaml` marks them `clock: true`
and they are measured but never proposed. A `d1_*` value is the previous day's
(`higher.closed`): the D1 bar of the day in course is never read.
