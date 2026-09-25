---
q: variant chain in a custom project sqx.variants; WFC databank names underscores; config.xml must declare databanks; task conditions block additional markets; retest-only project no Total tested In databank; holding() misses workers cwd; result key vs Results folder name
tag: 🔬  date: 2026-09-25  see: sqx-drive/variant-route, databanks/no-spaces-in-names, sqx-drive/running-a-task-headless
---
# Running `sqx.variants` in a custom project: six silent breakers, all now handled
1. No spaces in databank names (`WFC_Variants`, `WFC_Build`, `WFC_OOS1`, `WFC_OOS2` in `assets/_build.yaml` `wfc:`).
2. SQX loads only databanks declared in the project's `config.xml` (`sqx.projects.wfc` declares them).
3. Task acceptance conditions must all be off, or additional markets are skipped.
4. Retest-only project: `status` has no `Total tested`; watch `In databank`.
5. Find a worker JVM by its cwd, not its command line. 6. Result key ≠ `Results/` folder name.

## Evidence
Project `USDJPY_variantes`, custodian, three windows + family markets.
1. `name="WFC Variants"` → `Databank ''WFC' doesn't exist`; `core.worker.call` turns spaces into `%20`
   and the server splits there anyway. Hard rule 6 applies to databanks.
2. Neither `mkdir` nor a task naming it suffices (closed OPEN §40).
3. Donor `build`-window task had `AnnualPctReturn (OOS) > 0` active; `build` has no OOS → all fail, and
   with `evaluateAll="false"` SQX skips additional markets → window came back USDJPY only.
   `wfc.py` turns all task conditions off (`wfc.conditions: []`).
4. `In databank` = sum over ALL the project's databanks (loaded + returned + every other step's); `execute.run` takes it once before `start` and counts from there (🔬 2026-09-25: workflow project, 3 in `WFC_Variants` + 3 in `OOS` → 6 before, 15 after three legs).
5. Worker JVM runs as `./sqcli` from inside the install; `core.worker.holding()` (hard rule 4 guard) now also checks process cwd.
6. `settings.xml` key `Main: USDJPY_DukasM1_the5ers/H1` vs folder `Results/Main: USDJPY_DukasM1_the5ers_LOM_H1/`;
   common prefix ends at `/`; `equity.markets_of` cuts there.

Measured, 30 variants: 3-window retest with 9 markets 174 s end to end, JVM ~23 GB, markets 87–90 %
of retest time. Emptying the 4 databanks (start, `clear`, `synctofiles`, stop) 33 s → 0 files on disk.
