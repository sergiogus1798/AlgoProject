---
q: YAML parsing slow in a loop, assetdata.symbol_for cache, crossTF slow, cache by mtime and size, assets/ parsed every call
tag: 🔬  date: 2026-09-25  see: perf/python-parallelism, eng/editing-asset-yaml
---
# Never parse YAML per strategy/cell: `core.assetdata` caches each file by mtime + size
`assetdata` stores each parsed file stamped with its `mtime` and size and hands each call its own copy: a window edit is read on the
next call, and no caller can corrupt the cache by mutating what it gets.

## Evidence
`core.assetdata.symbol_for()` parsed all of `assets/` per call: 54 s of crossTF's 60 s = 1,971 parses of the same YAML.
After: crossTF 48 cells 29.2 → 5.7 s; `studies.readings.monkey.report` 11.1 → 3.6 s (`docs/manual/03-datos-costes-y-registro.pdf` (cap. 12-rendimiento)).
