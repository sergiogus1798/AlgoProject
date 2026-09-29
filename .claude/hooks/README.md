# .claude/hooks — Claude Code hooks, registered in `.claude/settings.json`

| file | event | what it does |
|---|---|---|
| `guard.py` | PreToolUse (Bash, Edit, Write, MultiEdit) | blocks what breaks HARD RULES 2, 4, 7 and 12 of `CLAUDE.md`; exit 2 with the rule on stderr |
| `lint_py.sh` | PostToolUse (Edit, Write, MultiEdit) | ruff F821/F811/F823/E9 on the `.py` just edited; findings go back to Claude |

A hook bug must never block work: both let the call through on any internal error. It matches the
raw command text, so a quoted example of a forbidden command is blocked too. What each one blocks,
and how to test it by piping sample JSON: `knowhow/eng/claude-hooks-guard.md`.
