# construct/equity — the universe: each strategy's equity, daily and inside the day

Rebuilds each strategy's floating equity from its trades and the feed's M1 bars, cuts it into days
on any server's clock, keeps its worst and best intraday excursion per day and per 5-minute block,
and reconciles the rebuild against SQX's own numbers before anything uses it. Contracts P, D, M in
`portfolio/EXECUTION.md` §1.

**Imports from:** `inputs/`, `core.barstore`, `core.assetdata`, `engines.market.calibrate` · **Consumed by:** `pairs/`, `search/`, the funded objective, `../universe.py`

| file | what it does | run it | in → out |
|---|---|---|---|
| `clock.py` | Naive feed-clock times to UTC; the server day an instant falls in; when a server day ends. `EETUS` = New York + 7 h | imported | times, zone → UTC, day labels |
| `paths.py` | One strategy's equity minute by minute: realised plus each open position at the minute's worst wick, best wick and close | imported | trades + M1 → arrays |
| `days.py` | The minute path cut into server days: closed P&L, floating at the day's end, the day's low and high against its opening equity | imported | path, zones → day table |
| `blocks.py` | The same low and high per 5-minute block on a UTC grid, and a combination's joint daily low and high from them | imported | path → float32 arrays |
| `excursions.py` | Each trade's MAE and MFE rebuilt from the wicks, and the licence: does the rebuild match SQX's own columns | imported | trades + M1 → per trade, verdict |
| `sqxcurve.py` | SQX's daily curve — each day's **lowest** equity — per segment, legs and warm-up handled; a known answer, never P&L | imported | `equity.parquet` → frame |
| `matrix.py` | Per-strategy series stacked to days × N (0 inside history, NaN outside), monthly sums, a segment slice | imported | series → frames |
| `reconcile.py` | The rebuild's daily lowest equity against SQX's own curve, day by day: exact share, largest gap, verdict | imported | two series → dict |
| `universe.py` | A pool's universe: sources, one M1 read per feed, rebuild, reconciliation (a member that fails is excluded, never kept silently), daily and monthly matrices in EET, server-day tables and M5 blocks per firm clock | imported by the command | pool → cache folder |
| `store.py` | The universe cache: folder named by pool hash **and** config fingerprint, write and load | imported | frames → files |

## Traps
- **SQX's daily curve is each day's LOWEST equity, not a mark to market** (🔬 2026-09-30, 100 % of
  3,983 days within 1 $): it licenses the rebuild, it never feeds P&L (`knowhow/sqx-format/daily-equity-bin.md`).
- **The exit minute is not floating**; the realised P&L lands there and anchors the close, so a
  strategy's days sum exactly to its trades' `Profit/Loss` (`knowhow/export/mae-mfe-from-m1.md`).
- **Swap is not in floating equity**: SQX books it inside `Profit/Loss` at the close.
- **A combination's intraday low is not the sum of its members' daily lows** (×1.6 too deep):
  sum the 5-minute blocks (`knowhow/perf/intraday-floating-resolution.md`).
