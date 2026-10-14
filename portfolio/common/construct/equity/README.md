# construct/equity — the universe: each strategy's equity, daily and inside the day

Rebuilds each strategy's floating equity from its trades and the feed's M1 bars, cuts it into days
on any server's clock, keeps its worst and best intraday excursion per day and per 5-minute block,
and reconciles the rebuild against SQX's own numbers before anything uses it. Contracts P, D, M in
`portfolio/EXECUTION.md` §1.

**Imports from:** `inputs/`, `core.barstore`, `core.assetdata`, `engines.market.calibrate` · **Consumed by:** `pairs/`, `search/`, the funded objective, `../universe.py`

| file | what it does | run it | in → out |
|---|---|---|---|
| `blocks.py` | M5 floating-equity blocks per member, and a combination's joint day extremes (contract M). | imported | path → float32 arrays |
| `clock.py` | Naive feed-clock times to UTC, and the day a UTC instant belongs to in any server clock. | imported | times, zone → UTC, day labels |
| `closecurve.py` | A population's close-to-close daily P&L on its feed's own days, rebuilt from trades and M1. | imported | trades + M1 → days × N |
| `days.py` | One row per server day from a minute path, and the daily P&L it implies (contract D). | imported | path, zones → day table |
| `excursions.py` | Per-trade MAE/MFE rebuilt from M1 wicks, and the check that licenses the rebuild (§14.2). | imported | trades + M1 → per trade, verdict |
| `matrix.py` | Per-strategy daily P&L series stacked into day and month matrices, and a calendar segment slice. | imported | series → frames |
| `paths.py` | Minute-by-minute floating and realised equity from trades and M1 bars (contract P). | imported | trades + M1 → arrays |
| `reconcile.py` | The rebuild checked against SQX's own daily curve: each day's lowest equity, day by day. | imported | two series → dict |
| `sqxcurve.py` | SQX's own daily curve — each day's LOWEST equity, floating included — per policy segment. | imported | `equity.parquet` → frame |
| `stopexit.py` | A stopped trade's real exit minute: SQX stamps a stop-loss exit at the OPEN of the bar it was hit in. | imported | trades + M1 → trades, excursions |
| `store.py` | Where a built universe lives on disk, and reading a finished one back. | imported | frames → files |
| `universe.py` | Pool -> per-member equity, reconciled against SQX, cached under its pool hash and config fingerprint. | imported by the command | pool → cache folder |

## Traps
- **SQX's daily curve is each day's LOWEST equity, not a mark to market** (🔬 2026-09-30, 100 % of
  3,983 days within 1 $): it licenses the rebuild, it never feeds P&L (`knowhow/sqx-format/daily-equity-bin.md`).
- **The exit minute is not floating**; the realised P&L lands there and anchors the close, so a
  strategy's days sum exactly to its trades' `Profit/Loss` (`knowhow/export/mae-mfe-from-m1.md`).
- **A stop-loss exit is stamped at the OPEN of the bar it was hit in** (🔬 2026-10-05, 891 of 891 on NIKKEI225 M30):
  `universe` and `search/stageb_data` re-time it (`stopexit.retime`) before building any path; a source dict needs
  `timeframe` and its trades `Close type`. Without it the licence read 0.47 on strategies with the step-24 stop.
- **Swap is not in floating equity**: SQX books it inside `Profit/Loss` at the close.
- **The commission IS in floating equity, whole, from the entry** (🔬 2026-10-04, 182,389 strategy-days:
  gap = 5.000 $ × lots). `minute_path` without its `commission` argument matches SQX only on a
  zero-commission asset; `search/stageb_data.py` still calls it that way.
- **The card's point value and commission are not the build's** once the card is recalibrated:
  `closecurve.measured` reads both off the trades (`knowhow/sqx-format/equity-reconstruction-usdjpy-gap.md`).
- **A strategy archived before its feed changed clock is refused, not rebuilt** (🔬 2026-10-04): `inputs/source.py`
  reads the clock live and `universe._commission` today's card. On its own clock (`clock.reclock`) and its own
  commission it reconciles 100 % (`knowhow/export/archived-trades-vs-reclocked-bars.md`).
- **A combination's intraday low is not the sum of its members' daily lows** (×1.6 too deep):
  sum the 5-minute blocks (`knowhow/perf/intraday-floating-resolution.md`).
- **The members are ordered by identity** (2026-10-05): the workers answer in the order they finish,
  and a rebuild in another order moved every sum over members in its last bits (1e-15 on the rank
  search's metrics). The cache key carries the WHOLE config's fingerprint: any `--set`, a search knob
  included, builds a new universe folder — and so does any edit to `equity/*.py` or `inputs/*.py`.
