# ui/daemon/create — the window creates a template and a project

Owner, 2026-09-28: the path from a prompt to a project runs from the window's buttons. Two
creations, each a job on the conductor lane (one at a time, like every job that reaches an
install):

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | The window's two creations: a template from the chat's brief, a project from a template. | — | — |
| `api.py` | The creations' routes: what can be chosen, and the two jobs on the conductor lane. | imported | request → job |
| `author.py` | «Crear la plantilla con Claude»: run /sqx-strategy-template headless on the chat's draft brief. | `python3 -m ui.daemon.create.author --name N` | draft → template in the library |
| `project.py` | «+ Nuevo proyecto»: hard rule 5, then `sqx.projects.builder --workflow` on the custodian. | `python3 -m ui.daemon.create.project NAME --template T --symbol S --timeframe TF --max-strategies N --minutes M --purpose P` | template + asset → project on the custodian |

**Imports from:** `core/`, `sqx/projects/registry`, `sqx/jobs`, `ui/daemon/brief` ·
**Consumed by:** `ui/desktop/chat.py`, `ui/desktop/workspace/newproject.py` (over HTTP)

The author runs Claude Code with no one in front of it: the skill's own questions become the
`PREGUNTA:` line in the job's log, and the owner answers them in a session.
