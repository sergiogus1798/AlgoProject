# sqx/workflow — the steps of the workflow and what the disk says of them

| file | what it does | run it | in → out |
|---|---|---|---|
| `launchsteps.py` | Which SQX tasks one workflow step launches from the window, and the SQX steps it cannot launch. | imported | step, project.cfx → titles |
| `records.py` | The records the rail passes between its modules: the step row, the install view, the context. | — | — |
| `sources.py` | What the disk holds for one project: its install, its tasks, its study results, its template. | imported | disk → dicts |
| `steps.py` | The steps of docs/AgentPDFs/WORKFLOW.md: where the disk says each happened, its tests and its tab. | imported | — |
