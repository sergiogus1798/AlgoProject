---
q: Why does a resume skip a study step that crashed halfway and leave it with partial results?
kw: partial evidence, resume treats step as done, derive.study, sources.results, spp report 3 of 10, own-log, 16.5 worked on 3 mothers, half-written study
tag: 🔬  date: 2026-10-10  see: pipeline/resumable-jobs, pipeline/autopilot-facts-silent-drops
---
# A study that fails halfway counts as done on resume; the autopilot now reopens it (OPEN.md #111, closed)
Trap: `ui/daemon/workflow/derive.py::study` calls a step done as soon as `sources.results` finds ANY
result. A study that wrote k of n strategies before crashing is therefore never rerun: the plan only
judges the partial facts, and every later step works on the k survivors. The window's rule is unchanged (shared by every study step); since 2026-10-10 `pipeline.autopilot.plan.reopen`
reruns the python step named in the previous stamp's `estado.txt` last line `FALLO en el paso N`. A study failed by
hand is still not seen: delete its partial `results` folder first.

## Evidence
`Test_DAX40_M30_momentumL_mc3`, 2026-10-10: the spp report wrote 3 of 10 strategies, then crashed (see
`research/distribution-series-outside-the-bins`). `bin/workflow.sh run <P> --smoke --own-log` planned
only «16 judge» (598 facts, 3 strategies), never reran the study, and step 16.5 worked on 3 mothers.
