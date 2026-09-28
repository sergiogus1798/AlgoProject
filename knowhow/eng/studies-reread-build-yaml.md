---
q: does a finished run keep the settings it ran with? crossTF blocks order, wfc tasks segment, study re-reads assets/_build.yaml at analysis time, changing _build.yaml rewrites the reading of an old run, Configuración SQX warning
tag: 📓  date: 2026-09-28  see: editing-asset-yaml
---
# Two studies re-read `assets/_build.yaml` when they analyse a run that already happened
`studies/transfer/crossTF` takes the block order (`crosstf.timeframes[<source>]`) and
`studies/readings/structure` takes each WFC databank's segment (`wfc.tasks[].segment`) from the
file as it is TODAY, not from what the run used. Change either value after a run and the old run is
read with the new one: crossTF scores each cell on another timeframe's bars, structure files a leg
under the wrong window — both in silence. Until runs save their own blocks (OPEN.md §80), change
these only between runs, or re-run; the Configuración SQX zone shows «aviso: un run ya hecho se
relee con este valor» beside both.

## Evidence
- `studies/transfer/crossTF/inputs.py:42` — `return [source] + doctrine()["crosstf"]["timeframes"][source]`
  unless the config gives `run.blocks` (only for a task written with `--timeframes`).
- `studies/readings/structure/inputs.py:63` — `segment = {t["databank"]: t["segment"] for t in
  assetdata.doctrine()["wfc"]["tasks"]}`; the ledger gate is then checked against that segment.
- `sqx.projects.crosstf` only prints the blocks to the terminal; nothing on disk keeps them.
  `sqx.variants` does record each leg's segment in the batch's `ran.json`, but
  `structure/inputs.py` does not read it (read 2026-09-28).
