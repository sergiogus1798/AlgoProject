#!/bin/bash
# weekly-claude-cleanup — delete the scratchpads old Claude sessions left in /tmp, Sunday 23:30.
#
# Every Claude Code session gets /tmp/claude-$UID/<project>/<session-id>/ and nothing removes it
# when the session ends. /tmp is its own 3.9 GB partition here: on 2026-09-26 it filled to 100 %
# (one scratchpad alone held 958 MB, 23 days old) and every session's shell started failing.
# Owner, 2026-09-26: clean them weekly. A session folder goes only when the NEWEST file anywhere
# inside it is older than KEEP_DAYS — a folder's own date does not move when a subfolder is
# written, so a live session could look old. Also trims bash-edit-diff/. Nothing else in /tmp,
# and never ~/.claude/projects (the conversations themselves). Plain shell: no model is needed
# to compare two dates.
#
# Usage:
#   weekly-claude-cleanup            delete what is old; one line per folder in the log
#   weekly-claude-cleanup --dry-run  list what would go and how much it frees; delete nothing
#   KEEP_DAYS=7 weekly-claude-cleanup
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1
KEEP_DAYS="${KEEP_DAYS:-3}"
BASE="/tmp/claude-$(id -u)"

DRY=0
case "${1:-}" in
  --dry-run) DRY=1 ;;
  "")        ;;
  *)         echo "unknown argument: $1" >&2; exit 2 ;;
esac

if [ "$DRY" -eq 0 ]; then
  DATA=$(python3 -c 'from core.paths import DATA; print(DATA)' 2>&1) || {
    printf 'cannot resolve the data root:\n  %s\n' "$DATA"; exit 1; }
  exec >>"$DATA/logs/claude-cleanup.log" 2>&1
fi

[ -d "$BASE" ] || { echo "$(date -Is) no $BASE, nothing to do"; exit 0; }

now=$(date +%s)
limit=$(( KEEP_DAYS * 86400 ))
freed=0
gone=0
kept=0
echo "=== $(date -Is) claude cleanup start (keep ${KEEP_DAYS} days, dry=${DRY})"
echo "    /tmp before: $(df -h /tmp | awk 'NR==2 {print $3 " used, " $4 " free"}')"

# Session scratchpads: <project folder>/<session uuid>/
for dir in "$BASE"/*/*/; do
  name=$(basename "$dir")
  [[ "$name" =~ ^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$ ]] || continue
  newest=$(find "$dir" -printf '%T@\n' 2>/dev/null | sort -n | tail -1 | cut -d. -f1)
  [ -n "$newest" ] || continue
  if [ $(( now - newest )) -lt "$limit" ]; then kept=$((kept + 1)); continue; fi
  kb=$(du -sk "$dir" | cut -f1)
  echo "    $(( (now - newest) / 86400 )) d  $(( kb / 1024 )) MB  $dir"
  if [ "$DRY" -eq 0 ]; then rm -rf -- "$dir" || { echo "    failed: $dir"; continue; }; fi
  freed=$(( freed + kb ))
  gone=$(( gone + 1 ))
done

# Edit diffs the harness keeps per edit; old ones are never read again.
if [ -d "$BASE/bash-edit-diff" ]; then
  old=$(find "$BASE/bash-edit-diff" -type f -mtime +"$KEEP_DAYS" | wc -l)
  echo "    bash-edit-diff: $old files older than ${KEEP_DAYS} d"
  [ "$DRY" -eq 0 ] && find "$BASE/bash-edit-diff" -type f -mtime +"$KEEP_DAYS" -delete
fi

echo "    $gone session folders $([ "$DRY" -eq 1 ] && echo 'would go' || echo 'deleted'), $(( freed / 1024 )) MB; $kept recent kept"
echo "    /tmp after:  $(df -h /tmp | awk 'NR==2 {print $3 " used, " $4 " free"}')"
echo "=== $(date -Is) claude cleanup end"
