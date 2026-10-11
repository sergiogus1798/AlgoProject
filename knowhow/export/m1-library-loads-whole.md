---
q: How fast does the XAUUSD M1 bar library load, and is it OHLC-consistent?
kw: M1 bar library size load time; flat bars High equals Low; OHLC consistency; mmap chunking not needed; core.barstore.source
tag: 🔬  date: 2026-10-11  see: export/exits-and-m1-library, export/bars, research/m1-feed-anomaly-statistics
---
# The M1 library loads whole in 0.4 s — read it whole, no mmap or chunking
OHLC-consistent; spikes, frozen runs and gaps → `research/m1-feed-anomaly-statistics`. Split out of `export/exits-and-m1-library` (date 2026-09-24 there).

## Evidence
- `XAUUSD_DukasM1_Infinox`: 7,949,285 bars (2003-05-05 → 2026-09-22), `core.barstore.source` loads all in 0.4 s. 0 OHLC-inconsistent
  (`H < max(O,C)`, `L > min(O,C)`, `H < L`); 40,097 (0.50 %) flat `High == Low`.
