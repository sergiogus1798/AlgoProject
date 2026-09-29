---
q: sqx.variants.spp on Retester hard rule 10 violation; which project does the SPP reconnaissance harness use; harness.write overwrites Retest-Task1.xml; can the SPP harness share the mother's workflow project; SPPRecon_In/SPPRecon_Out
tag: 🔬  date: 2026-09-29  see: sqx-drive/variant-chain-custom-project, sqx-drive/spp-task-type
---
# The SPP reconnaissance harness lives in the mother's own workflow project, by title

`harness.write()` used to overwrite the single member `Retest-Task1.xml` of whatever project it
was pointed at — safe only because `--project` was, until 2026-09-29, a dedicated single-task
project built just to hold it. The owner rejected that shape outright (2026-09-29): "no entiendo
por qué se ha de crear uno y que se copien de ahí" — hard rule 10 is **one project for the whole
workflow**, not a second one per study. `harness.write(cfx, task, kind, role)` now finds its
target by **title** inside the mother's own workflow project and rewrites only that member.

## Evidence
`sqx/variants/harness.py`: `write()` calls `member_of(config, TITLES[kind])`
(`TITLES = {"spp_is": "SPP IS", "spp_oos": "SPP OOS", "retest": "OOS"}`), never a hardcoded file
name. `Build-Task3.xml`'s `<Databank label="Output databank" name="Output" value="Results">`,
read off the frozen donor 2026-09-29.

## The fix: target by title, not by file name

A workflow project built with `sqx.projects.builder --workflow` already carries a task titled
"SPP IS" and one titled "SPP OOS" — kept straight from the frozen donor because `spp:` is a step
in `sqx/projects/stages.yaml`. `write()` rewrites only the member that title maps to — never the
project's real `OOS`/`CONSTRUCCION`/`WFM` member, whatever file name those happen to occupy.
`sqx.variants.spp --project` is now the mother's own workflow project; it still refuses a stock
one (`execute.STOCK`).

Before `action=start`, `sqx.projects.stage.just(cfx, [TITLES[kind]])` switches on only that one
task — the project carries every other workflow step's task too, and `action=start` runs every
task marked active.

## The databank collision this surfaces

The reconnaissance harness's own Input/Output databank names (`sqx/variants/config.yaml#execute`)
used to be `Results`/`RetestOut`, harmless in an empty dedicated project. Inside the real workflow
project, `Results` is not free: it is the Build task's actual output databank. Loading the one
mother being reconnoitred into a databank called `Results` there would drop it straight into the
project's real build population. Renamed to `SPPRecon_In` / `SPPRecon_Out`, chosen against every
databank name the workflow itself declares (`Results`, `Results-Rexpect`, `OOS`, the MCR titles,
`SPP IS`, `SPP OOS`, `WFM`, `CrossTF`/`CrossTF_Input`, `assets/_build.yaml#wfc.input` and its
three legs).

## What was removed

`pipeline/config.yaml#run.spp_project` and `Trade_XAUUSD_variantesSPP` are gone.
`pipeline/recipe.yaml`'s `spp_is`/`spp_oos`/`spp_export` rows take `{project}` — the mother's
own — like every other stage.
