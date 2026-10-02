---
q: permissions deny Edit(**/project.cfx) matches nothing, Claude Code permission rule path syntax, // absolute path, ~/ home, settings.json deny outside project root
tag: 🔬  date: 2026-10-02  see: claude-hooks-guard
---
# Edit/Read permission paths are gitignore patterns anchored at the project: `**/x` never leaves it
Docs (code.claude.com/docs/en/permissions, "Read and Edit"): `//path` absolute, `~/path` home, `/path` relative
to the settings source (not the root), `path` relative to cwd. `Edit(**/project.cfx)` covered only this repo;
the real files live under `~/Desktop/SQX*/user/projects/`. A fix would be `Edit(~/Desktop/SQX_w1/**/project.cfx)`
per install: a machine path in a committed file. Decision 2026-10-02: the two dead rules were REMOVED;
`guard.py` (rule 4) is the single enforcer: it blocks Edit/Write/MultiEdit of any `project.cfx` anywhere (not
only a running one), and no skill edits one by hand (they use the `-project` API).

## Evidence
`echo '{"tool_name":"Edit","tool_input":{"file_path":"/home/sergioguslw/Desktop/SQX_w2/user/projects/P/project.cfx"}}' | python3 .claude/hooks/guard.py; echo $?` → BLOCKED, 2.
`grep -rn project.cfx .claude/skills sqx/CLAUDE.md` finds no Edit/Write flow.
