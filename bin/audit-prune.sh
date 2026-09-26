#!/bin/bash
# audit-prune — gzip old daily audit reports in place, in audit/.
#
# tools/daily_audit.py and the auditor agent write two files a day, forever
# (audit/YYYY-MM-DD.md, audit/YYYY-MM-DD-mechanical.md). Unlike SQX's own logs there is no
# separate archive step: this gzips the report itself once it is older than KEEP_DAYS, keeping
# the text (small, greppable) but off the working tree's daily view. Never touches today's
# reports or audit/state.json. Nothing is deleted — a .md.gz is still every byte the report had.
#
# Usage:
#   audit-prune            gzip reports older than KEEP_DAYS; verbose
#   audit-prune --dry-run  list what would be gzipped; touch nothing
#   KEEP_DAYS=90 audit-prune
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1
KEEP_DAYS="${KEEP_DAYS:-60}"
DIR="audit"

DRY=0
case "${1:-}" in
  --dry-run) DRY=1 ;;
  "")        ;;
  *)         echo "unknown argument: $1" >&2; exit 2 ;;
esac

[ -d "$DIR" ] || { echo "no $DIR/ here"; exit 1; }

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
exit 0
