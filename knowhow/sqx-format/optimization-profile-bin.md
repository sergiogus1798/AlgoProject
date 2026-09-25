---
q: optimizationProfile.bin format, SPP optimization profile parse, SPP permutations stored, 3D charts setting dontStoreOP3DChartsData, SPP permutation trades, SQUtils.writeUTF, betterHashCode metric keys, optprofile_columns.json
tag: 🔬  date: 2026-09-10  see: sqx-format/sqstats-blob, sqx-format/sequential-optimisation-xml, export/spp-export
---
# optimizationProfile.bin is the SPP profile; it parses (`core/optprofile.py`)
Present only after a cross-check that drives the optimizer (SPP; not sequential optimisation, which
writes XML). Per-permutation results are kept only if *Settings → Performance → "Don't store data for
3D charts in Optimization profile"* is **unticked** — otherwise only medians/histograms survive and the
SPP must be re-run. A permutation is params + `SQStats` only: **SPP permutation trades do not exist.**

## Evidence
- 225 `.sqx` under the master's `user/projects` carry one (2026-09-10).
- Framing = same block-data stream as `dailyEquity.bin`. Layout (from `OptimizationProfile.readFormat2`,
  `internal/libs/SQTradingLib.jar`): int format (2) · boolean *kept* · if kept: original result and
  every permutation (`writeUTF` params + `SQStats` blob each) · three int-keyed maps of 135 entries
  (medians, original values, one JSON histogram per metric) · `writeUTF` permuted parameter names ·
  `writeUTF` profitable/losing counts · 5 ints + 6 doubles of run stats · plain-Java `writeUTF`
  profit distribution chart.
- Setting: `user/settings/settings.xml`, `<dontStoreOP3DChartsData>`. Unticked and re-running
  `XAUUSD/SPP IS`: each `.sqx` **125 KB → 2.2 MB**, 4,309 permutations for one strategy (3,940–4,523
  across five; one sample only, no IS/OOS split). `Infinox_SP500ft_H4_HighPrecision/SPP` has 29 older ones.
- `SQStats.deserialize`: loop of byte-tagged records — `1` int, `2` long, `3` float (double when stats
  format is 1), `101/102/103` same under a name; `default:` throws. `objectMap` exists but `serialize`
  never writes it. No order list reachable.
- `SQUtils.writeUTF` ≠ Java `writeUTF`: marker byte, then 2-byte length if marker is 1 else 4-byte,
  then UTF-8. Used by `OptimizationTestResult` and named `SQStats` records.
- `SQStats` array indices = same key space as the base64 XML blob (`core/sqxstats.py`); matching the
  name-keyed medians table named 79 of 116 indexed slots, 118 of 152 in all; last 34 are 0 everywhere.
  Full inventory: `docs/manual/09-diccionario-spp.md`.
- The 135 metric keys = `SQUtils.betterHashCode(<DatabankColumn simple name>)`, in
  `internal/libs/SQLib.jar` which is **not on disk** (embedded resource); not `String.hashCode` with
  usual finalisers (tested). Names recovered by matching against a 135-column export of 50 SPP
  strategies → `core/optprofile_columns.json`: 101/135 one-to-one; 6 known to a pair, suffixed `?`
  (`Exposure`/`ExposurePosition`, `Outlier`/`Outlier2`, `CalmarRatio`/`AnnualPctReturnDDRatio` — equal
  on all 225); 28 always 0 stay `id:<key>`.
