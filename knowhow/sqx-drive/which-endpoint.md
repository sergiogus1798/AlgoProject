---
q: which port/endpoint to call SQX on; 5050 vs 5060 vs 8080; "CLI not ready"; worker project not visible on master; can I edit project.cfx; read vs write boundary
tag: 🔬  date: 2026-09-02  see: sqx-drive/project-verb, sqx-drive/mcp-server-limits, sqx-drive/three-install-topology
---
# Drive SQX through a worker's command API; the master's needs its GUI closed
Use the worker command API (conductor 5060, custodian 5070) — headless, always answers. Master 5050
refuses while the GUI is up; master 8080 is MCP/web, read-only plus run/stop.
Installs are independent: a project built on a worker never appears on the master.
Editing a `project.cfx` on disk under a running instance is silently lost; write through the API.

## Evidence
| endpoint | port | GUI up? | notes |
|---|---|---|---|
| master command API | 5050 | ❌ `Error: CLI not ready.` | needs GUI closed |
| master MCP / web | 8080 | ✅ | `/call` 404s — not the command API |
| worker command API | 5060 (W1) / 5070 (W2) | ✅ always | use this |

Read vs write — the boundary is whether a running instance holds the project, not which agent:
- read a `project.cfx`: always safe
- create/modify via API on a worker: always safe
- edit `project.cfx` on disk under a running instance: silently lost (hard rule 4)
- anything on the master: needs GUI closed (SQX-lifecycle lane)

Moving a worker project to the master: import its `.cfx` through the master GUI, or copy the
directory with SQX closed. When handing over a worker-built project, say it: "nothing on your
master was touched" also means "you will not see it there".
