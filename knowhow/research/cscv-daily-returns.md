---
q: CSCV daily or weekly returns, López de Prado PBO matrix rows, is a daily panel all zeros, how many days in equity.parquet, duplicate dates leg overlap, Sundays in equity, CSCV runtime 12870 partitions daily, block sums
tag: 🔬  date: 2026-10-01  see: research/cscv-chosen-point-slope-seesaw, research/cscv-always-reads-oos2
---
# The CSCV reads daily returns, and a daily panel is not "almost all zeros"
Since 2026-10-01 the CSCV ranks trading-day returns like Bailey/López de Prado (`cscv.period: D`).
A batch's `equity.parquet` is marked to market: on a USDJPY H1 batch 75 % of day x variant cells
move, so the old "sixty trades a year make a daily matrix noise" argument for weekly did not hold.
Its index is the days the curves have (every weekday, ~97 Sundays a feed clock opens on, no Jan 1)
and **repeats ~83 dates where two legs' warm-ups overlap** — group by date and sum, never resample
to calendar days. Score each half from per-block sums (`measure/cscv.py::moments`), never by
concatenating rows: row by row a daily 16-block CSCV costs ~79 s per rule and score.

## Evidence
`Test_USDJPY_donchianUpperCrossUp_H1/Strategy_10.1.79`, 500 variants, `equity.parquet` 5,081 rows,
4,998 distinct dates (2007-11-02 → 2026-08-27), weekday counts 996-999 each, 97 Sundays (59 % of
their cells non-zero), 9 missing weekdays all 1 January; non-zero share of all cells 0.7485.
In-process run (nothing written), 16 blocks, split `oos2_only`, PBO argmax / plateau / random:

| mother | weekly (T=982) | daily (T=4,997) |
|---|---|---|
| 10.1.79 | 43.9 / 32.7 / 49.9 % | 44.7 / 34.9 / 49.6 % |
| 1.26.46 | 38.5 / 39.3 / 51.1 % | 31.1 / 29.3 / 51.3 % |
| 6.35.56 | 42.0 / 36.8 / 49.9 % | 50.1 / 43.8 / 50.9 % |

The weekly column reproduces the stored `cscv.json` exactly. Every move is inside the 0.21 null
spread (`verdict/README.md`). Daily whole study 6.6 s (six rule x score workers, ~0.5 GB peak
each) against 2.0 s weekly; one `cscv.run` 0.38 s with block sums vs ~79 s extrapolated row by
row from 200 partitions. `tests/test_cscv.py` holds block sums equal to rows partition by partition.
