# replay — each trade walked again from a shifted entry until its stop or its scheduled exit

Encargo 56, front 3 (ex 16, tier 2 of the delay). Computes, never judges. The entries are SQX's
and the entry logic is never re-run: only the stop is recomputed, from the new fill and the ATR
of the bar before the new entry. Tier 1 (`studies/readings/entryQuality/delay.py`) holds exits
fixed, which is right for signal and bar-count exits and wrong for a stop.

## What it reproduces (delay 0, 🔬 2026-10-14, seven `Stop_p90` harvests, 18,520 trades, 6,051 stops)

| harvest | trades | exit bar and reason as SQX | stops within 2 ticks |
|---|---|---|---|
| NIKKEI225 M30 simpleL ×4 | 2,740-2,783 | 99.50-99.64 % | 98.8-98.9 % |
| USA500 H1 indicesIBS | 1,121 | 99.38 % | 99.05 % |
| USDJPY M30 doubleROC | 2,992 | 99.90 % | 100 % |
| NIKKEI225 M30 volatilidadL | 3,331 | 99.58 % | 99.12 % |

The rest falls on one to four dates per harvest (2020-10-30 01:00 on every NIKKEI one), where
SQX stops a bar later than today's bars say. The rules it took (`knowhow/export/fill-and-pricing.md`):
level = fill − side × coef × round(ATR20[entry − 1], 6), **rounded to the tick** (tickStep on
forex); hit when the bar's Low (High for a short) reaches it — testPrecision 1, on the strategy's
own bars; filled at the level, or at the bar's **open when it gaps through** (6 % of NIKKEI
stops), less slippage.

## Delay rules (§3.3 of the encargo)

| case | rule |
|---|---|
| Exit After X Bars | moves with the entry |
| Exit Signal, Deleted | stays when only the entry is late; moves +d under full latency |
| End Of Friday | stays (a clock exit) |
| signal/clock exit at or before the delayed entry | the trade does not exist: `dropped`, reported |
| SQX stopped it, the new stop misses | its signal exit is unknown: runs to the strategy's longest trade, `unknown`, reported |
| SL and TP in one bar | none here (no PT); SQX's rule is `knowhow/export/sl-pt-same-bar-convention.md` |
| pending (stop/limit) entries | not supported: the chain trades at market (rule 15) |

A per-trade numpy slice walks 3,000 trades in 0.01 s: no Numba (D-7).

| file | what it does | run it | in → out |
|---|---|---|---|
| `inputs.py` | A stop harvest made ready to replay: its trades on their bar grid, each with its stop's ATR multiple. | imported | `harvest/<P>/Stop_p90/<day>` → bars + trades |
| `reconcile.py` | The replay at delay 0 against SQX's own trade list: same exit bar, same reason, same price. | imported | replay + SQX's list → match |
| `walk.py` | Each trade walked again on its own timeframe's bars, from a possibly shifted entry, until its stop or its scheduled exit. | imported | bars + trades + delay → exits |
