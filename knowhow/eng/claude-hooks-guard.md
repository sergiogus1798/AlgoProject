---
q: claude hooks, PreToolUse guard, blocked by guard.py, hook blocks git add -A worktree switch pkill sqcli master project.cfx csv, PostToolUse ruff lint, settings.local.json additionalDirectories
tag: 🔬  date: 2026-09-29  see: headless-claude-from-cron, claude-permission-path-syntax
---
# Rules 2, 4, 7 and 12 are enforced by `.claude/hooks/guard.py`, not only written down
A PreToolUse hook blocks (exit 2): `pkill`/`killall` with `StrategyQuant`; `sqcli` naming the master
install while port 5050 listens (`SQX_w1`/`SQX_w2` pass); Edit/Write of any `project.cfx`;
`git worktree`, `git switch`, `git checkout -b`, `git add -A|--all|.` anywhere in a compound command;
Write of `.csv`/`.parquet` inside the repo outside `scratch/` and `tests/`. A block is the rule firing
— never route around it. A hook exception lets the call through. `lint_py.sh` (PostToolUse) runs ruff
F821/F811/F823/E9 on each edited `.py` and hands findings back. Machine paths
(`additionalDirectories`) live in the git-ignored `.claude/settings.local.json`.

## Evidence
2026-09-29, fed sample JSON to each script: 6 blocked commands exit 2, `git status`, `git add <file>`,
`git checkout -- f`, sqcli on the workers exit 0; the master sqcli block tested against a fake
listener on a spare port. Live: `git add -A --dry-run` in a session → "BLOCKED by guard.py — rule 12".
Guard runs in ~50 ms. Test one case:
`echo '{"tool_name":"Bash","tool_input":{"command":"git worktree add x"}}' | python3 .claude/hooks/guard.py; echo $?`
🤔 Headless runs in an untrusted workspace ignore `permissions.allow` (headless-claude-from-cron);
whether they also skip project hooks is untested — check the next nightly log for a "hook" line.
