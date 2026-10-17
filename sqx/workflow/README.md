# sqx/workflow — the steps of the workflow and what the disk says of them

| file | what it does | run it | in → out |
|---|---|---|---|
| `chainplan.py` | What «Correr workflow» runs, in WORKFLOW.md's order, and the step it stops before — from the rail. | imported | rail → plan |
| `confirm.py` | The confirmation «Continuar workflow» shows before it deletes anything (encargo 22 §7.2). | imported | preflight → text |
| `launchcheck.py` | Whether «Lanzar en SQX» may start one task of a project now, and every reason it may not. | imported | project, task(s) or step → `{ok, reasons, chosen, off, …}` |
| `launchconfigure.py` | Run the configurator of every chosen task still unconfigured, as its skill does, with the worker stopped. | imported | preflight → configured tasks |
| `launchsteps.py` | Which SQX tasks one workflow step launches from the window, and the SQX steps it cannot launch. | imported | step, project.cfx → titles |
| `records.py` | The records the rail passes between its modules: the step row, the install view, the context. | — | — |
| `sources.py` | What the disk holds for one project: its install, its tasks, its study results, its template. | imported | disk → dicts |
| `steps.py` | The steps of docs/AgentPDFs/WORKFLOW.md: where the disk says each happened, its tests and its tab. | imported | — |
