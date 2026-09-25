---
q: run claude headless from cron, unattended agent, claude -p, binary not on PATH, workspace not trusted, add-dir
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
apply this: `bin/nightly-audit.sh`, `bin/nightly-sync.sh`.
