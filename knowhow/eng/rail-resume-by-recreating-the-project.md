---
q: How do I resume a retired project so the workflow continues at step 13?
kw: resume retired project, rail derive.py, step done, store resume, until project.cfx restore, Project not found
tag: 📓  date: 2026-10-08  see: eng/claude-hooks-guard
---
# The rail calls an SQX step done when its output databank holds files — resume by recreating the project under the SAME name
`ui/daemon/workflow/derive.py` reads progress off disk: an SQX step is done when its output databank
holds files, a Python step when its report exists under `reports/<P>/`. So a retired project is
resumed by recreating it under the same name and filling the output databanks with stored `.sqx`:
`python3 -m pipeline.autopilot.resume <P> <identity|name>...`, then `bin/workflow.sh run`. A project
built with `--until` has no later tasks, so its archived `project.cfx` cannot be restored for this.

## Evidence
`pipeline/autopilot/resume.py`; `ui/daemon/workflow/derive.py`.
