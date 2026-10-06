---
q: Why is ~/.claude/usage.json never written under the VSCode extension?
kw: usage.json, statusline, usage-refresh.sh, rate_limit_event, 5h 7d limit, vscode extension
tag: 🔬  date: 2026-10-04
---
# The VSCode extension never runs the statusline, so `usage.json` stays stale
Run `~/.claude/usage-refresh.sh`: a minimal Haiku `claude -p` call that reads `rate_limit_event`, writes `~/.claude/usage.json` and prints `5h X % · 7d Y %`.

## Evidence
2026-10-04 cleanup (`INFRA_REVIEW.md`, deleted 2026-10-06).
