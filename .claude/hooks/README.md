# .claude/hooks — Claude Code hooks, registered in `.claude/settings.json`

| file | event | what it does |
|---|---|---|
| `guard.py` | PreToolUse (Bash, Edit, Write, MultiEdit, Agent, Task, EnterWorktree) | blocks what breaks HARD RULES 2, 4, 7 and 12 of `CLAUDE.md`; exit 2 with the rule on stderr |
| `shellwords.py` | — (imported by `guard.py`) | splits a shell line into the simple commands it runs: `;`, `&&`, `\|\|`, `\|`, newlines, subshells, `$(…)`, backticks, `bash -c`, heredocs; wrappers (`sudo`, `env`, `xargs`…) removed |
| `gitrule.py` | — (imported by `guard.py`) | rule 12 on one git command, decided on its subcommand after git's global options |
| `lint_py.sh` | PostToolUse (Edit, Write, MultiEdit) | ruff F821/F811/F823/E9 on the `.py` just edited; findings go back to Claude |

A hook bug must never block work: both let the call through on any internal error, and a shell line
the parser cannot read (an unbalanced quote) is judged by the old raw-text checks (`guard.legacy`).
The guard judges the command position, so a forbidden command quoted as an argument of `grep`,
`echo` or `git commit -m` is data and passes. What it blocks and what it does not:
`knowhow/eng/claude-hooks-guard.md`; its known-answer test: `python3 tests/test_guard.py`.
