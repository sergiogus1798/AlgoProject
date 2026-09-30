# ui/daemon/create — the window creates a template and a project

Owner, 2026-09-28: the path from a prompt to a project runs from the window's buttons. Two
creations, each a job on the conductor lane (one at a time, like every job that reaches an
install):

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Package marker | — | — |
| `api.py` | `GET /api/create/options` (templates with a `.sqx`, assets, timeframes, the form's defaults: 500 strategies, 180 min), `POST /api/create/template` (the chat's draft → `author`), `POST /api/create/project` (the form → `project`; a name `registry.check_name` refuses is answered, not queued) | imported | request → job |
| `author.py` | «Crear la plantilla con Claude»: the chat's prompt (`brief.prompt`) plus an unattended note, to `CLAUDE_BIN -p --permission-mode auto` in the repository; exit 2 when the answer carries `PREGUNTA:` (hard rule 11: a question, never a guess) | `python3 -m ui.daemon.create.author --name N` | draft → template in the library |
| `project.py` | «+ Nuevo proyecto»: `core.assets` (hard rule 5, stops on non-zero), then `sqx.projects.builder --workflow --role custodian` | `python3 -m ui.daemon.create.project NAME --template T --symbol S --timeframe TF --max-strategies N --minutes M --purpose P` | template + asset → project on the custodian |

**Imports from:** `core/`, `sqx/projects/registry`, `ui/daemon/jobs`, `ui/daemon/brief` ·
**Consumed by:** `ui/desktop/chat.py`, `ui/desktop/workspace/newproject.py` (over HTTP)

The author runs Claude Code with no one in front of it: the skill's own questions become the
`PREGUNTA:` line in the job's log, and the owner answers them in a session.
