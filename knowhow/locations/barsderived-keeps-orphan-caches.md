---
q: barsDerived orphan caches; old fingerprint parquet; bar library refresh leaves stale resampled timeframes; what can be deleted in barsDerived; D1-<version>.parquet
tag: 🔬  date: 2026-09-27  see: export/bars, export/storage-format
---
# A bar-library refresh orphans every resampled timeframe, and nothing sweeps them
`core.barstore.read` names each cache `barsDerived/<feed>/<TF>-<M1 fingerprint>.parquet`, so a refreshed M1 is never
answered from old bars — but the old files stay. A file whose fingerprint differs from `bars/manifest.json`'s
`version` for its feed is dead weight: deleting it costs nothing (the live one is rebuilt on read, ~1 s).
Any size of `barsDerived/` (the Datos zone's catalogue, `perf.disk.report`) includes them.

## Evidence
- 2026-09-27, measured: 6 of 34 files in `barsDerived/` carry XAUUSD's pre-2026-09-24 fingerprint `1831822b`
  (library version `db58f31f`): 20.6 MB of 155 MB. Check: compare `p.stem.split('-')[1]` with
  `barstore.library()[p.parent.name]['version']` for every `barsDerived/*/*.parquet`.
- Found while building `ui/daemon/data/` (plan 24, F10), whose first D1 request for XAUUSD wrote `D1-db58f31f.parquet`
  beside the orphan `D1-1831822b.parquet`. Nothing was deleted.
