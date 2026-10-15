#!/bin/bash
# ledger-pull — bring another server's search-ledger files into this machine's ledger/_remote/<server>/
# (D27, option A: one writer per file, the union read by ledger.shards.read_all).
#
# Pulls, read-only on the remote (rsync pull; nothing is written or deleted there), every ledger file
# of the four families, mirroring their path under its data root:
#   ledger/*.jsonl  ledger/tried/*.jsonl  ledger/cells/*.csv  campaign/ledger*.jsonl
# Idempotent: pulling twice duplicates nothing (read_all deduplicates by row content).
# Run it before each cell on either server, as bin/remote.sh does `git pull`.
#
# Usage:
#   ledger-pull <server>            e.g. gorilla (a name under mirrors: in config/machine.yaml)
#   ledger-pull <server> --dry-run  list what would be copied, copy nothing
# Exit 0: pulled. 1: another pull is running, or rsync failed. 2: bad arguments.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1

[ $# -ge 1 ] || { sed -n 2,14p "$0"; exit 2; }
NAME="$1"; shift
DRY=()
case "${1:-}" in --dry-run) DRY=(-n -v) ;; "") ;; *) sed -n 2,14p "$0"; exit 2 ;; esac

_CFG=$(python3 -c '
import sys
from core.paths import DATA, MIRRORS
from ledger.shards import REMOTE
m = MIRRORS[sys.argv[1]]
print(m["ssh"]); print(m.get("data", "Desktop/AlgoData")); print(DATA); print(REMOTE / sys.argv[1])' "$NAME") || {
  echo "ledger-pull: no server \"$NAME\" under mirrors: in config/machine.yaml"; exit 2; }
mapfile -t C <<< "$_CFG"
HOST="${C[0]}"; RDATA="${C[1]}"; LOCAL="${C[2]}"; DEST="${C[3]}"

mkdir -p "$DEST" || exit 1
exec 8>"$LOCAL/ledger/_remote/.pull.lock"
flock -n 8 || { echo "ledger-pull: another pull is running; nothing done"; exit 1; }

# --relative keeps the remote path under the data root, so DEST/ledger/X.jsonl mirrors DATA/ledger/X.jsonl
SSH="ssh -o BatchMode=yes -o ConnectTimeout=20"
COMMON=(-a -R --ignore-missing-args --prune-empty-dirs "${DRY[@]}" -e "$SSH")
rc=0
rsync "${COMMON[@]}" --exclude=_remote --exclude=archive \
  --include='*/' --include='*.jsonl' --include='*.csv' --exclude='*' \
  "$HOST:$RDATA/./ledger/" "$DEST/" || rc=1
rsync "${COMMON[@]}" --include='ledger*.jsonl' --exclude='*' \
  "$HOST:$RDATA/./campaign/" "$DEST/" || rc=1
[ "$rc" = 0 ] && echo "ledger-pull: $NAME -> $DEST" || echo "ledger-pull: rsync failed"
exit "$rc"
