#!/bin/bash
# sqx-log-prune — cap the size of SQX's own log directories.
#
# SQX writes one log per day per install and never prunes them in practice: this
# machine held 35 days, 4.5 GB, of which a single day (2026-08-18) was 4.4 GB and
# another (2026-09-20) 55 MB. The big days are error storms, not normal operation.
#
# The safety rule, and it is the whole of it: a log is deleted only when
# `sqx.export.archive_logs` already holds a .gz copy of it in the data root. So
# pruning moves the bytes, it does not discard them. `--auto` archives first, which
# is what makes a frequent prune actually reclaim anything.
#
# Never touches the current day's log, nor any file a process holds open: SQX appends to it.
#
# Two retentions, because days alone did not bound the folder (2026-10-06: the custodian held
# 1.8 GB, one past day of 854 MB, all of it archived and none of it a week old): a small log
# stays KEEP_DAYS for a quick grep; a past day's log above BIG_MB is an error storm and goes
# as soon as its .gz is up to date and it has been quiet for an hour (a run that crosses midnight
# writes on in yesterday's file for a moment) — read it with `zgrep` in the archive.
#
# Usage:
#   sqx-log-prune            archived logs older than KEEP_DAYS go; verbose
#   sqx-log-prune --dry-run  list what would go; delete nothing
#   sqx-log-prune --auto     archive, then prune, quietly, at most once per MIN_HOURS.
#                            Meant for hooks and for sqx-worker.sh — safe to call often.
#   KEEP_DAYS=14 BIG_MB=100 sqx-log-prune
#   ONLY="SQX_w1 SQX_w2" sqx-log-prune   only these installs (folder names)
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KEEP_DAYS="${KEEP_DAYS:-7}"
BIG_MB="${BIG_MB:-20}"          # an archived past-day log above this goes whatever its age
MIN_HOURS="${MIN_HOURS:-4}"     # --auto does nothing if it ran more recently than this
WARN_MB="${WARN_MB:-200}"       # a current-day log above this is shouted about

# core/paths.py is the only place that knows where an install lives, so ask it
# instead of parsing YAML in bash. One line each, so a path with a space survives.
_WHERE=$(cd "$ROOT" && python3 -c '
from core.paths import DATA, MASTER, WORKERS
print(MASTER)
print(DATA)
for w in WORKERS.values():
    print(w["path"])' 2>&1) || {
  printf 'cannot resolve the installs:\n  %s\n' "$_WHERE"; exit 1; }
mapfile -t _WHERE <<< "$_WHERE"
MASTER="${_WHERE[0]}"
DATA="${_WHERE[1]}"
INSTALLS=("${_WHERE[@]:0:1}" "${_WHERE[@]:2}")   # master + every worker role

DRY=0
AUTO=0
case "${1:-}" in
  --dry-run) DRY=1 ;;
  --auto)    AUTO=1 ;;
  "")        ;;
  *)         echo "unknown argument: $1" >&2; exit 2 ;;
esac

STAMP="$DATA/logs/.prune-stamp"

# --auto is called from a session hook and from every worker start, so it must be
# cheap to call and boring when there is nothing to do.
if [ "$AUTO" = 1 ]; then
  if [ -f "$STAMP" ]; then
    age=$(( ($(date +%s) - $(stat -c%Y "$STAMP")) / 3600 ))
    [ "$age" -lt "$MIN_HOURS" ] && exit 0
  fi
  mkdir -p "$(dirname "$STAMP")"
  # Archive first. Without this a frequent prune finds nothing it is allowed to
  # delete, because a log is only deletable once its .gz exists.
  (cd "$ROOT" && python3 -m sqx.export.archive_logs) >/dev/null 2>&1
  touch "$STAMP"
fi

TODAY="log_$(date +%Y_%m_%d).log"
freed=0
kept_unarchived=0
out=""                          # --auto buffers, and prints only if it matters

say() { if [ "$AUTO" = 1 ]; then out+="$1"$'\n'; else printf '%s\n' "$1"; fi; }

for install in "${INSTALLS[@]}"; do
  name=$(basename "$install")
  logdir="$install/user/log"
  archdir="$DATA/logs/$name"
  [ -d "$logdir" ] || continue
  [ -n "${ONLY:-}" ] && [[ " $ONLY " != *" $name "* ]] && continue
  # What any process holds open in this folder, read from /proc: never deleted, whatever its name.
  held=$(find /proc/[0-9]*/fd -lname "$logdir/*" -printf '%l\n' 2>/dev/null | sort -u)
  [ "$AUTO" = 1 ] || echo "== $name  (archivo: $archdir)"

  # The live day: open, appended to, never deletable. Pruning cannot help, so the
  # only useful thing is to shout before it eats the disk.
  while IFS= read -r -d '' live; do
    mb=$(( $(stat -c%s "$live") / 1048576 ))
    if [ "$mb" -ge "$WARN_MB" ]; then
      say "AVISO: $name/$TODAY son ${mb} MB y es el log del dia en curso — la poda no puede tocarlo."
      say "       Eso es una tormenta de errores en marcha. 'tail -100' ese fichero y arregla la causa."
    else
      [ "$AUTO" = 1 ] || printf '   viva    %-30s %12d bytes (dia en curso)\n' "$TODAY" "$(stat -c%s "$live")"
    fi
  done < <(find "$logdir" -type f -name "$TODAY" -print0)

  while IFS= read -r -d '' f; do
    base=$(basename "$f")
    # Belt and braces: -mtime cannot return today's file, but KEEP_DAYS=0 could.
    [ "$base" = "$TODAY" ] && continue
    grep -qxF "$f" <<< "$held" && continue
    # Delete only what the archiver already holds.
    rel="${f#$logdir/}"
    gz="$archdir/$rel.gz"
    if [ ! -f "$gz" ] || [ "$f" -nt "$gz" ]; then
      say "KEEP    $base — sin copia al dia en el archivo, no se borra"
      kept_unarchived=$((kept_unarchived+1))
      continue
    fi
    size=$(stat -c%s "$f")
    if [ "$DRY" = 1 ]; then
      printf '   would   %-30s %12d bytes\n' "$base" "$size"
    else
      rm -f "$f" || continue
      [ "$AUTO" = 1 ] || printf '   deleted %-30s %12d bytes\n' "$base" "$size"
    fi
    freed=$((freed+size))
  done < <(find "$logdir" -type f -name '*.log' \( -mtime "+$KEEP_DAYS" -o \( -size "+${BIG_MB}M" -mmin +60 \) \) -print0 | sort -z)
done

human=$(numfmt --to=iec "$freed" 2>/dev/null || echo "$freed B")

if [ "$AUTO" = 1 ]; then
  # Silence is the normal outcome. Speak only when bytes moved or something is wrong.
  [ "$freed" -gt 0 ] && printf 'logs SQX: %s liberados (retencion %s dias)\n' "$human" "$KEEP_DAYS"
  [ -n "$out" ] && printf '%s' "$out"
  exit 0
fi

printf '\nretencion: %s dias · %s: %d bytes (%s)\n' \
  "$KEEP_DAYS" "$([ "$DRY" = 1 ] && echo 'se liberarian' || echo 'liberados')" "$freed" "$human"
[ "$kept_unarchived" -gt 0 ] && \
  echo "AVISO: $kept_unarchived log(s) sin copia archivada; ejecuta 'python3 -m sqx.export.archive_logs' y repite."
exit 0
