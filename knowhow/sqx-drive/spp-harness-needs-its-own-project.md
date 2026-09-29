---
q: sqx.variants.spp on Retester hard rule 10 violation; which project does the SPP reconnaissance harness use; harness.write overwrites Retest-Task1.xml; can the SPP harness share the mother's workflow project
tag: 🔬  date: 2026-09-29  see: sqx-drive/variant-chain-custom-project, sqx-drive/spp-task-type
---
# `sqx.variants.spp`'s harness needs a project of its own — never Retester, never the mother's project

`harness.write()` overwrites the single member `Retest-Task1.xml` of `<project>/project.cfx`,
whichever real task that file name holds. `sqx.variants.spp` called this against the stock
`Retester` by default until 2026-09-29 (OPEN.md §38, owner) — hard rule 10, but not a corruption,
since `Retester` carries nobody's work. Pointing it at the mother's own multi-task workflow project
instead WOULD corrupt it in silence: that project's `Retest-Task1.xml` is likely the real `build`
task, and SQX rewrites `project.cfx` on save with no error printed.

## Evidence
`harness.write(project, task, role)`: `members[TASK] = task.encode(...)` where
`TASK = "Retest-Task1.xml"`, unconditionally, for whatever `project` is passed.

## Fix (2026-09-29)
`sqx.variants.spp` now takes `--project` (required) and refuses `execute.STOCK` (`Builder`,
`Retester`). The harness needs a **dedicated single-Retest-task project**, built once per symbol:
`python3 -m sqx.projects.builder Trade_<SYMBOL>_variantesSPP --purpose "..." --tasks Retest --only
Retest-Task1.xml`. The unattended pipeline names it in `pipeline/config.yaml#run.spp_project`,
substituted as `{spp_project}` in `pipeline/recipe.yaml`'s `spp_is`/`spp_oos`/`spp_export` rows —
never `{project}`, which is the mother's own build/retest project.
