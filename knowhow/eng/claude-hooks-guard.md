---
q: Which commands does .claude/hooks/guard.py block, and which does it let through?
kw: claude hooks, PreToolUse guard, blocked by guard.py, hook blocks git add -A -u commit -a checkout branch clone worktree switch pkill pgrep kill sqcli master project.cfx sed -i csv, isolation worktree EnterWorktree, PostToolUse ruff lint, settings.local.json additionalDirectories
tag: 🔬  date: 2026-10-03  see: headless-claude-from-cron, claude-permission-path-syntax
---
# Rules 2, 4, 7 and 12 are enforced by `.claude/hooks/guard.py` on the command each shell line RUNS
It parses the line (`;` `&&` `|` newlines `$(…)` `bash -c` heredocs), so text quoted to `grep`/`echo`/`commit -m` is
data. Blocks (exit 2) — **12**: `git add -A`/`-u`/`.`/`*`/`:/`, `commit -a`, `switch`, `clone`, `worktree` (not
`list`), `branch <name>`, `checkout` unless `-- <file>`; Agent `isolation: "worktree"`, EnterWorktree. **2**:
`pkill`/`killall` or a `pgrep`-fed `kill` of StrategyQuant|sqcli|java (numeric PID passes); `sqcli` from or on the
master while 5050 listens (`SQX_w1`/`SQX_w2` pass). **4**: Edit/Write, and shell writes (`>`, `tee`, `sed -i`,
`cp`/`mv`, inline python), of any `project.cfx`. **7**: Edit/Write of data files in the repo outside `scratch/`,
`tests/`. NOT enforced: plain `git commit`/`push`; data or a `project.cfx` written by a script. Errors fail open.

## Evidence
Detail — 12: also `-Av`, `-am`, `git -C . add -A`, `git -c k=v switch`, `add -- .`, `branch -d`/`-m`; listing forms
of `branch` pass. 2: `kill` is blocked when fed by `pgrep`/`pidof`/`ps|grep` naming an SQX process; the sqcli check
follows each `cd`. 4: also `perl -i`, `dd of=`, `cp` into a folder that already holds one. 7: `.csv .parquet .pkl
.feather .h5 .npy .npz`. Not enforced either: `rm` of a `project.cfx`, data written by a shell redirection,
`isolation: "remote"` (not rule 12). An exception lets the call through (exit 0); a line the parser cannot read
(unbalanced quote) gets the old raw-text regexes, `guard.legacy`. Parser `shellwords.py`, git rule `gitrule.py`.
2026-10-03, `python3 tests/test_guard.py` → "ok: 195 hook events judged as expected, none executed": 67 blocked
shell lines (the 14 git forms, 5 rule-4 writes and 4 kill pipelines a review got past the raw-text guard of
2026-09-29), 86 passing ones (its false positives: `grep -rn "git worktree" .`, `git log --grep="git add -A"`,
`git worktree list`, a log `tail` naming sqcli and the master), 8 master-sqcli lines blocked with a listener up
and passed with it down (`GUARD_MASTER_PORT` points the check at the test's own port; 5050 is never dialled),
23 tool events, 3 malformed inputs. One call takes ~35 ms. Test one case by hand:
`echo '{"tool_name":"Bash","tool_input":{"command":"git worktree add x"}}' | python3 .claude/hooks/guard.py; echo $?`
Known limit: shlex drops quotes, so a quoted lone `";"` or `"|"` reads as an operator and splits that
command in two (`git commit -m ";" -a` would get past). `lint_py.sh` (PostToolUse) runs ruff F821/F811/F823/E9 on each edited `.py`. Machine paths
(`additionalDirectories`) live in the git-ignored `.claude/settings.local.json`.
🤔 Headless runs in an untrusted workspace ignore `permissions.allow` (headless-claude-from-cron);
whether they also skip project hooks is untested — check the next nightly log for a "hook" line.
