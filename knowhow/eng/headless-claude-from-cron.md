---
q: How do I run `claude -p` from cron so it finds the binary, its tools and its directories?
kw: run claude headless from cron, unattended agent, claude -p, binary not on PATH, workspace not trusted, add-dir
tag: 🔬  date: 2026-09-25  see: 
---
# Headless Claude from cron: find the binary, pass tools and dirs explicitly
There is no `claude` on PATH here: the only binary is inside the VS Code extension, under a folder
named by version (`~/.vscode/extensions/anthropic.claude-code-<ver>-linux-x64/resources/native-binary/claude`)
that changes on every update — pick the newest with `sort -V | tail -1` each run, never hardcode it.
Headless, the workspace is "not trusted", so `.claude/settings.json` `permissions.allow` and
`additionalDirectories` are **ignored**: pass `--allowedTools` and one `--add-dir` per path outside the
repo (data root, every SQX install). Auth works under cron's bare environment. `gh` is not logged in
and git has no credential helper, so an unattended push fails until `gh auth login` is run by hand.

## Evidence
`env -i HOME=$HOME PATH=/usr/bin:/bin <claude> -p "Responde solo: OK"` → `OK`, preceded by
"Ignoring 42 permissions.allow entries … this workspace has not been trusted" and the same for 4
additionalDirectories. `git push --dry-run origin HEAD` → "could not read Username". Scripts that
apply this: `bin/nightly-audit.sh`, `bin/nightly-commit-proposal.sh`.

Every unattended script sources `bin/lib-agent-alert.sh` and calls the agent through `agent_run <job> <model> <report> timeout … claude -p --output-format json …`: it logs the result text, appends `date,job,model,input_tokens,output_tokens,duration_s,exit` to `AlgoData/logs/agent-spend.csv`, and on a non-zero exit, `is_error` or a missing/empty report writes `AlgoData/audit/ERROR-<job>-<date>.txt` and sends a desktop notification. Use it only where the report is a file the agent writes, not claude's stdout.
