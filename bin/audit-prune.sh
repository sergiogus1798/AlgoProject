#!/bin/bash
# audit-prune — gzip old daily audit reports in place, in the data root's audit/ (core.paths.AUDIT).
#
# tools/daily_audit.py and the auditor agent write two files a day, forever
# (YYYY-MM-DD.md, YYYY-MM-DD-mechanical.md, and the agents' -fixes/-fondeo/-proyectos). Unlike SQX's own logs there is no
# separate archive step: this gzips the report itself once it is older than KEEP_DAYS, keeping
# the text (small, greppable) but off the working tree's daily view. Never touches today's
# reports or state.json. Nothing is deleted — a .md.gz is still every byte the report had.
#
# Also keeps the last KEEP_LINES lines of each top-level *.log of the data root's logs/ over 1 MB
# (cron jobs append to them forever: fleet-collect, cron, disk-nightly, nightly-fix...).
#
# Usage:
#   audit-prune            gzip reports older than KEEP_DAYS; verbose
#   audit-prune --dry-run  list what would be gzipped; touch nothing
#   KEEP_DAYS=90 audit-prune
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1
KEEP_DAYS="${KEEP_DAYS:-60}"
KEEP_LINES="${KEEP_LINES:-5000}"
DIR=$(python3 -c 'from core.paths import AUDIT; print(AUDIT)' 2>&1) || {
  printf 'cannot resolve the audit folder:\n  %s\n' "$DIR"; exit 1; }

DRY=0
case "${1:-}" in
  --dry-run) DRY=1 ;;
  "")        ;;
  *)         echo "unknown argument: $1" >&2; exit 2 ;;
esac

[ -d "$DIR" ] || { echo "no $DIR yet"; exit 0; }

TODAY_STEM="$(date +%F)"
n=0
while IFS= read -r -d '' f; do
  base=$(basename "$f")
  [[ "$base" == "$TODAY_STEM"* ]] && continue
  if [ "$DRY" = 1 ]; then
    printf 'would gzip  %s\n' "$base"
  else
    gzip -f "$f" && printf 'gzipped     %s\n' "$base"
  fi
  n=$((n+1))
done < <(find "$DIR" -maxdepth 1 -type f -name '*.md' -mtime "+$KEEP_DAYS" -print0 | sort -z)

[ "$n" -eq 0 ] && echo "nothing older than $KEEP_DAYS days"

LOGS=$(python3 -c 'from core.paths import DATA; print(DATA / "logs")' 2>/dev/null) || exit 0
while IFS= read -r -d '' f; do
  if [ "$DRY" = 1 ]; then
    printf 'would trim  %s to %s lines\n' "$(basename "$f")" "$KEEP_LINES"
  else
    tmp=$(mktemp) && tail -n "$KEEP_LINES" "$f" > "$tmp" && cat "$tmp" > "$f" && printf 'trimmed     %s\n' "$(basename "$f")"
    rm -f "$tmp"
  fi
done < <(find "$LOGS" -maxdepth 1 -type f -name '*.log' -size +1M -print0 2>/dev/null)
exit 0
