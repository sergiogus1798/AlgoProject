# marketProfile/measure — the measures, one signature each

Holds what is measured on a series. It must never hold the null, the p-value or a filter: a
measure returns a statistic and, when it trades, the entry and exit bars — nothing about whether
that is a lot. `one.py` runs the same functions on the real series and on every null draw.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | The registry of measures: every function a row of config.yaml's `measures` may name. | imported | — |
| `pattern.py` | Bar states, written for longs: does the state shift the odds of the next bar closing up. | imported | series → statistic, trades |
| `position.py` | One position at a time: a rule's entry and exit bars when the exit is a condition, not a count. | imported | masks → entry, exit |
| `price.py` | Measures that trade a price event, written for longs: trend, breakout, reversion, momentum. | imported | series → statistic, trades |
| `rules.py` | A rule a strategy could trade, written for longs: an entry, its filters, an exit — no clock. | imported | series + frame → statistic, trades |
| `session.py` | Measures of the clock, written for longs: the best hour, band and weekday, and a band's range. | imported | series + calendar → statistic, trades |
| `structure.py` | Measures of the series as a whole: no trade, no direction, only a statistic. | imported | series → statistic |
| `trades.py` | What a signal becomes: its entry and exit bars, and the statistic its returns are judged by. | imported | mask → entry, exit, statistic |

Every measure is written for longs. The short side is the same function on the mirrored series
(`higher.mirror`), so a long and a short can never drift apart.

A measure must be a rule a strategy could trade: one direction, fills at the next open, and **no
clock** — `rules.py` reads nothing of the calendar but `least`, and `tests/test_marketprofile.py`
checks it. The four measures of `session.py` do read it: `config.yaml` marks them `clock: true`
and they are measured but never proposed. A `d1_*` value is the previous day's
(`higher.closed`): the D1 bar of the day in course is never read.
