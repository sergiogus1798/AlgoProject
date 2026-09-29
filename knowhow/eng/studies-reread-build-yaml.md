---
q: does a finished run keep the settings it ran with? crossTF blocks order, wfc tasks segment, study re-reads assets/_build.yaml at analysis time, changing _build.yaml rewrites the reading of an old run, blocks.json, ran.json, Configuración SQX warning
tag: 🔬  date: 2026-09-29  see: editing-asset-yaml
---
# Fixed: crossTF and structure now read a run's own record, not today's `assets/_build.yaml`
Was: crossTF's block order and structure's segment came from the file as it is TODAY, so a later
edit silently relabelled an old run. Fixed 2026-09-29 (`OPEN.md` #80): `sqx.projects.crosstf`
writes `blocks.json` into `core.datapaths.crosstf_dir(project, --day)`, beside `scaling.parquet`;
`crossTF/inputs.blocks()` reads it first, the doctrine only when missing, with a warning.
`sqx.variants.execute` already wrote `ran.json` beside the batch; `structure/inputs.segments()`
now reads its `legs` first, the doctrine only as that same fallback. An explicit `run.blocks`
override still wins over the file in crossTF.

## Evidence
- `studies/transfer/crossTF/inputs.py::blocks()` — `given` (explicit) > `directory/"blocks.json"`
  > `doctrine()["crosstf"]["timeframes"][source]` (fallback, warns).
- `studies/readings/structure/inputs.py::segments()` — `work/"ran.json"`'s legs >
  `assetdata.doctrine()["wfc"]["tasks"]` (fallback, warns).
- `sqx/projects/crosstf.py::main()` writes `blocks.json`; `sqx/variants/execute.py:~238` already
  wrote `ran.json` before this fix — `structure` just did not read it.
- `tests/test_run_record.py` — known-answer test for both readers, the fallback, and the explicit
  override.
