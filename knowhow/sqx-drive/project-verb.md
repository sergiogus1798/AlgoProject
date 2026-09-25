---
q: sqcli -project verb actions; loadconfig saveconfig traps; create/modify project programmatically; URL encoding in /call; full sqcli verb reference help.txt
tag: 🔬  date: 2026-09-02  see: sqx-drive/running-a-task-headless, databanks/databank-verbs, sqx-drive/which-endpoint
---
# `-project` creates/modifies projects via API; `loadconfig` never overwrites
Full verb reference: `internal/web/SQUANT/help.txt` (readable without starting SQX) — consult it, don't guess.
`loadconfig` into an existing name creates `Name(2)`; `action=remove` first. Read the response.
`saveconfig` output is not loadable; copy a real `user/projects/<name>/project.cfx` instead.
URL-encode only space→`%20`, `?`, `&`, `#`; never `%28%29`.

## Evidence
```
action: [list, start, startOnlyTask, startFromTask, stop, pause, resume,
         remove, status, loadconfig, saveconfig]
name: Project name   file: Path of the config file   task: Task number, 1-indexed
```
Full create/modify cycle verified end to end: `docs/project-config-workflow.md`.
1. `loadconfig` response says `Project loaded 'MyProject(2)'` — verify that name, not the original.
2. `saveconfig`/`loadconfig` are asymmetric; use the multi-file `project.cfx` form as template.
3. Server reads the query literally: `name=MyProject(2)` works; `%28%29` →
   `Project 'MyProject%282%29' does not exist.`
4. A GUI-loaded project still cannot be edited on disk — the API works because SQX does the write.

Other verbs: `-databank action=list|export|syncfromfiles|synctofiles|clear|count|create|remove|load|save|copy|move|delete`,
`-tools action=orderstocsv`, `-data action=export`, `-symbol action=list`.
