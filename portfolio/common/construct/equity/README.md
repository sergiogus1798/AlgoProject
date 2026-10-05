# construct/equity — the universe: each strategy's equity, daily and inside the day

Rebuilds each strategy's floating equity from its trades and the feed's M1 bars, cuts it into days
on any server's clock, keeps its worst and best intraday excursion per day and per 5-minute block,
and reconciles the rebuild against SQX's own numbers before anything uses it. Contracts P, D, M in
`portfolio/EXECUTION.md` §1.

**Imports from:** `inputs/`, `core.barstore`, `core.assetdata`, `engines.market.calibrate` · **Consumed by:** `pairs/`, `search/`, the funded objective, `../universe.py`

| file | what it does | run it | in → out |
|---|---|---|---|
| `clock.py` | Naive feed-clock times to UTC; the server day an instant falls in; when a server day ends. `EETUS` = New York + 7 h; `reclock` re-stamps bars from one feed clock to another | imported | times, zone → UTC, day labels |
| `paths.py` | One strategy's equity minute by minute: realised plus each open position at the minute's worst wick, best wick and close, its round-turn commission charged from the entry (`entry_commission` reads it off the asset card) | imported | trades + M1 → arrays |
| `closecurve.py` | A whole population of one feed and one segment: point value and commission measured from its own same-day trades, every strategy's close-to-close daily P&L on the feed's days and its lowest-equity curve to reconcile, in parallel; the asset's day closes. What `studies/screening/snoopingScreen` and `studies/closing/blindJoint` read | imported | trades + M1 → days × N |
| `days.py` | The minute path cut into server days: closed P&L, floating at the day's end, the day's low and high against its opening equity | imported | path, zones → day table |
| `blocks.py` | The same low and high per 5-minute block on a UTC grid, and a combination's joint daily low and high from them | imported | path → float32 arrays |
| `excursions.py` | Each trade's MAE and MFE rebuilt from the wicks, and the licence: does the rebuild match SQX's own columns | imported | trades + M1 → per trade, verdict |
| `stopexit.py` | A stop-loss exit as it happened: `retime` moves it from the bar's open, where SQX stamps it, to the M1 minute that reached its price; `fills` puts each trade's own exit price into its rebuilt MAE/MFE | imported | trades + M1 → trades, excursions |
| `sqxcurve.py` | SQX's daily curve — each day's **lowest** equity — per segment, legs and warm-up handled; a known answer, never P&L | imported | `equity.parquet` → frame |
| `matrix.py` | Per-strategy series stacked to days × N (0 inside history, NaN outside), monthly sums, a segment slice (days only: a segment's months are summed from its own days, a month-indexed frame is refused) | imported | series → frames |
| `reconcile.py` | The rebuild's daily lowest equity against SQX's own curve, day by day: exact share, largest gap, verdict | imported | two series → dict |
| `universe.py` | A pool's universe: sources, one M1 read per feed, rebuild, reconciliation (a member that fails is excluded, never kept silently), daily and monthly matrices in EET, server-day tables and M5 blocks per firm clock | imported by the command | pool → cache folder |
| `store.py` | The universe cache: folder named by pool hash, config fingerprint **and** `code()` — eight hex characters over the bytes of every `.py` of `equity/` and `inputs/` — write and load. A change to the builder's source gets a new folder (OPEN #104-1; 🔬 2026-10-05: a stale universe had moved a stage-A P(pass) from 0.338 to 0.340). ⚠ what those files import from outside (`core.assetdata`, `core.barstore`, the bars) is not in the key | imported | frames → files |

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
