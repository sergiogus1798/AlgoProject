#!/bin/bash
# weekly-refactor-scout — structural review of the codebase, Saturday 04:30, unattended from cron.
#
# Two stages (owner, 2026-10-16): the mechanical half (vulture, ruff, checks, layering ALLOW, line
# counts, the week's churn) runs without a model and writes <date>-mechanical.md; the refactorScout
# agent fans the seven dimensions out to Sonnet subagents and writes <date>.md and findings.json,
# with what is new, fixed and worse since last week. Reports only: nothing in the repo changes.
#
# Usage:
#   weekly-refactor-scout            run it
#   weekly-refactor-scout --dry-run  resolve paths and the binary, print them, run nothing
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1
. "$ROOT/bin/lib-agent-alert.sh"

resolve_data
LOG="$DATA/logs/weekly-refactor-scout.log"
LOCK="$DATA/logs/.weekly-refactor-scout.lock"
OUT="$DATA/audit/refactorScout"
TODAY=$(date +%F)
MECH="$OUT/$TODAY-mechanical.md"
PKGS="core ui studies sqx pipeline portfolio mt5 engines ledger perf tools"

resolve_claude

dry_run "${1:-}" 'root   %s\nlog    %s\nout    %s\nclaude %s\n' "$ROOT" "$LOG" "$OUT" "${CLAUDE:-NOT FOUND}"

exec >>"$LOG" 2>&1
take_lock "$LOCK" "another refactor-scout run is going"
mkdir -p "$OUT"

echo "=== $(date -Is) weekly refactor scout start"
{
  echo "# refactorScout — mecánico $TODAY"
  echo; echo "## Líneas de Python por paquete (sin tests)"; echo '```'
  for d in $PKGS; do
    printf '%-10s %5s ficheros %7s líneas\n' "$d" "$(find "$d" -name '*.py' -not -path '*/sqx-lab/*' | wc -l)" \
      "$(find "$d" -name '*.py' -not -path '*/sqx-lab/*' -exec cat {} + | wc -l)"
  done; echo '```'
  echo; echo "## Ficheros más tocados en 7 días"; echo '```'
  git log --since=7.days --name-only --format= -- '*.py' | grep . | sort | uniq -c | sort -nr | head -20
  echo "commits: $(git log --since=7.days --oneline | wc -l)"; echo '```'
  echo; echo "## vulture (confianza 60)"; echo '```'
  # shellcheck disable=SC2086
  timeout 10m vulture --min-confidence 60 $PKGS --exclude '*/sqx-lab/*' 2>/dev/null > "$OUT/.vulture.txt"
  echo "total: $(wc -l < "$OUT/.vulture.txt")"; cat "$OUT/.vulture.txt"; echo '```'
  echo; echo "## ruff --statistics"; echo '```'
  timeout 10m ruff check --statistics --exit-zero . 2>&1 | head -40; echo '```'
  echo; echo "## Excepciones de capas (tools/layering.py ALLOW)"; echo '```'
  python3 -c 'import sys; sys.path.insert(0, "tools"); import layering as l; print(len(l.ALLOW))' 2>&1 | tail -1; echo '```'
  echo; echo "## tools/checks.py"; echo '```'
  timeout 15m python3 tools/checks.py 2>&1 | tail -25; echo '```'
} > "$MECH"
rm -f "$OUT/.vulture.txt"
echo "--- mechanical above ($MECH)"

if [ -n "$CLAUDE" ] && [ -x "$CLAUDE" ]; then
  agent_run weekly-refactor-scout sonnet "$OUT/$TODAY.md" timeout 3h "$CLAUDE" -p --output-format json \
    --agent refactorScout --model sonnet --add-dir "$DATA" \
    --allowedTools=Agent,Bash,Read,Grep,Glob,Write \
    --disallowedTools=Edit,WebFetch,WebSearch \
    "Weekly structural review, unattended from cron: nobody can answer, so never ask. Follow \
.claude/agents/refactorScout.md: read $MECH and $OUT/findings.json, run the seven dimensions as seven \
Sonnet subagents in one message, write $OUT/$TODAY.md in Spanish and update $OUT/findings.json, and \
end with a summary of at most ten lines. Never edit a repo file, never touch git, never run the test \
suite, never call sqcli, bin/sqx-worker.sh, bin/remote.sh, ssh or MT5."
  echo "--- agent above"
else
  echo "--- no claude binary found; agent half skipped"
fi
echo "=== $(date -Is) weekly refactor scout end"
