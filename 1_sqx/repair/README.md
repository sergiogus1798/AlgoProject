# 1_sqx/repair — write to a project on disk, once SQX is not holding it

Unlike `inspect/`, everything here **writes**. SQX rewrites a `project.cfx` on save and on exit, so a
write under a live instance is silently lost. Every tool here reads `/proc` for a process running out
of the install and refuses to touch anything while one exists. That guard is the point of the folder;
do not route around it.

| file | what it does | run it | in → out |
|---|---|---|---|
| `graft_tasks.py` | Heal a project whose archive is missing task files its `config.xml` declares, taking only the absent members from a donor archive | `python3 1_sqx/repair/graft_tasks.py <PROJECT> [--apply]` | broken `.cfx` → repaired `.cfx` |

Defaults to a dry run: it grafts into `project.repaired.cfx`, verifies that nothing is still missing
and that every databank the new tasks name is registered, then deletes it. `--apply` installs it and
keeps the previous archive under `AlgoData/backups/projects/<PROJECT>/<timestamp>/`.

**It keeps the live `config.xml`, not the donor's.** On `Infinox_SP500ft_H4_HighPrecision` the donor
is from 2025-10-13 and still carries the old name with spaces, an `OOS` databank that was since
removed, and a stale input databank on `Retest-Task2`. Replacing the whole archive with the backup —
as `OPEN.md` first suggested — would undo all three.
