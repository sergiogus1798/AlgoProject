---
q: Why does an old project's SPP IS read an empty MCR 8 Stress, and how do I repoint it?
kw: SPP IS input MCR 8 Stress empty, old-chain project, repoint SPP input, MCR 7 OHLC, sqx.projects.spp --input
tag: 🤔  date: 2026-10-07  see: sqx-drive/running-a-task-headless
---
# A project built with the old chain has `SPP IS` reading `MCR 8 Stress`, which nothing fills now
Since 2026-10-07 step 13 runs only `MCR 1 Bar`, `MCR 4 MinDist` and `MCR 7 OHLC` and step 14 cuts on `MCR 7 OHLC`.
An older project still points `SPP IS` at `MCR 8 Stress`. Before step 15, worker stopped:
`python3 -m sqx.projects.spp <SYMBOL> --cfx <cfx> --input "MCR 7 OHLC"`. Inferred from the stage
change, not yet run on such a project.

## Evidence
- `sqx/projects/stages.yaml` (mcretest stage) and its comment on «SPP IS»; `criteria.yaml` key "14" cuts on MCR 7 OHLC.
