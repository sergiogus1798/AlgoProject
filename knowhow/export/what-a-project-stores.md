---
q: which bar data to store; M1 resample equals SQX M30 H1 export; float32 vs float64 zstd size; bars/ directory per export; duplicate strategies SPP OOS WFM dedupe by name or hash
tag: 🔬  date: 2026-09-21  see: export/bars, export/storage-format, export/trade-export-columns
---
# Store only M1 bars; dedupe strategies on the trade list, not name or XML hash
- Pandas resample of M1 reproduces SQX's higher-TF export exactly → M30/H1/H4/D1 are caches; `core/barstore.py` builds them on first use.
- Keep float64: under zstd it is smaller than float32 on this data.
- Same name in `SPP OOS` and `WFM` is usually a different strategy; but identical logic can have a different XML hash.
  For any pooled statistic, deduplicate on the exported trade list.

## Evidence
- `XAUUSD_DukasM1_Infinox`: 7,708,823 M1 bars → M30 = 274,832 bars vs SQX 274,832, identical index,
  `max|diff| = 0.000000` on OHLC. `Volume` differs on 13 of 274,832 bars by ≤2 units (SQX rounding).
- Read M1: 0.78 s Parquet vs 5.57 s CSV; each resample 0.3–0.4 s → cold TF ~1.2 s, cached 0.02 s.
- float64 6.71 MB vs float32 7.08 MB (same 274,832 M30 bars): float32 rounding of 2-decimal prices = mantissa noise.
- Per-export `raw/<P>/<D>/<date>/bars/bars_<TF>.csv` (written by `export_trades.py`) was never read by any module,
  and worse (228,979 bars from 2007 vs 274,833 from 2003, different md5). Removed 2026-09-21 with 29 MB of copies.
- Duplicates: only 1 of 231 files a true inner-XML duplicate; 45 of 231 have byte-identical trade lists —
  WFM re-exports the SPP OOS strategy with parameters `makeExternal="true"` (changes hash, not logic).
