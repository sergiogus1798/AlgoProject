---
q: strategy name in databank after load, filename vs StrategyName, collision rename (1), P00000(1), join key variant_id sqx_name
tag: 🔬  date: 2026-09-22  see: sqx-format/writing-a-variant, sqx-format/strategy-identity
---
# SQX names a loaded strategy after its FILE; on collision it appends `(N)`
The databank, export and retest all use the filename as the handle, not `<StrategyName>` /
`ResultsGroup/@ResultName`. Join contract C2 to the retested panel on `variant_id`, not `sqx_name`,
and strip `\(\d+\)$` before joining.

## Evidence
- `P00000.sqx` shows as `P00000` although both inner fields say `Strategy 17.9.39 P00000`. Renaming them
  is still right, but not what prevents a batch collapsing under one name.
- Loading the same folder of `P00000/1/2` twice → 6 records: `P00000`, `P00001`, `P00002`, `P00002(1)`,
  `P00001(1)`, `P00000(1)`. Hence `variant_id` is also written inside the file and C2 keeps `sqx_name` apart.
