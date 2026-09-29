#!/bin/bash
# PostToolUse: after an edit to a .py file, show ruff's real-bug findings on that file at once,
# so an undefined name is caught while the file is open rather than by the 03:00 audit.
# Exit 2 hands the findings back to Claude; anything else here passes silently.
FILE=$(python3 -c 'import json,sys; print((json.load(sys.stdin).get("tool_input") or {}).get("file_path",""))' 2>/dev/null)
case "$FILE" in *.py) ;; *) exit 0 ;; esac
[ -f "$FILE" ] || exit 0
RUFF=$(command -v ruff || echo "$HOME/.local/bin/ruff")
[ -x "$RUFF" ] || exit 0
OUT=$("$RUFF" check --select F821,F811,F823,E9 --output-format concise --no-cache "$FILE" 2>/dev/null \
      | grep -vE '^(Found|All checks passed)')
[ -z "$OUT" ] && exit 0
printf 'ruff found real bugs in the file just edited:\n%s\n' "$OUT" >&2
exit 2
