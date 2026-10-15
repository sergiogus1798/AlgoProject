---
q: Why does step 8 (or `core.store save`) die with `OSError: List index overflow` on a 10,000-strategy build?
kw: List index overflow pyarrow distribuciones.parquet row group 2**31 list offsets int32 facts.from_folder core.store save collect gate 10000 strategies
tag: 🔬  date: 2026-10-15  see: batch-facts-three-traps
---
# A distributions parquet in one row group cannot be read back
pyarrow's `list<>` columns index their elements with int32 offsets **per row group**. The gate's
`distribuciones.parquet` of a 10,000-strategy build (42,538 rows, 5.8 GB) was written as ONE row group
holding more than 2**31 list elements: it wrote fine and no reader could open it — `pd.read_parquet`,
`core.store save`, the window. Fix: `core.study.draws._write` writes `row_group_size=1_000`; and
`pipeline.autopilot.facts.from_folder` reads only the `strategy` column of a parquet first and skips
whole reads of tables with several rows per strategy (trades, distributions). A file written before
2026-10-15 is re-chunked by streaming `ParquetFile.iter_batches(1000)` into a `ParquetWriter` (172 s,
8.8 GB RAM for 5.8 GB): same rows, readable.

## Evidence
Run `Test_USATEC_H1_breakoutL_v8_leaseWeb` 2026-10-15, `fallo.md` of step 8; `core/study/draws.py`
(`_write`); `pipeline/autopilot/facts.py` (`from_folder`).
