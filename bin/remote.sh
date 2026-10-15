#!/bin/bash
# remote — run a command in another server's clone of this repo, after `git pull` there.
#
# The other servers (`mirrors:` in config/machine.yaml — gorilla) hold a read-only clone that
# only ever receives code by `git pull`. This is the one door for running anything there, so the
# pull is a mechanism and not something to remember (owner, 2026-10-10):
#   - no SQX running there: `git pull --ff-only` first; if it fails, nothing runs (exit 97).
#   - SQX running there: no pull — the code is never changed under a run — and it says so.
#   - a workflow running there (`pgrep -f` on pipeline.autopilot / bin/workflow.sh — it leaves no
#     lock or pid file, so the process name is the marker): nothing runs (exit 96).
#
# Usage:
#   bin/remote.sh gorilla <command...>            run it in the clone, wait, return its exit code
#   bin/remote.sh gorilla collect <PROJECT> [--dry-run]
#                                                 bring that project's survivors (.sqx + store folder +
#                                                 ledger rows, suffix _gorilla) to this machine for step 26;
#                                                 only reads on gorilla (core/store/collect.py)
#   bin/remote.sh --detach gorilla <command...>   launch it detached (it survives the SSH
#                                                 session), print its PID and its log, return
#
# Wait for a detached one with:  ssh <host> tail --pid=<PID> -f /dev/null   (a read-only wait;
# remote.sh refuses anything while a workflow runs there, so it cannot be the door for this)
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1

DETACH=0
[ "${1:-}" = "--detach" ] && { DETACH=1; shift; }
[ $# -ge 2 ] || { sed -n '2,19p' "$0"; exit 2; }
NAME="$1"; shift
[ "${1:-}" = "collect" ] && { shift; exec python3 -m core.store.collect "$NAME" "$@"; }

_CFG=$(python3 -c '
import sys
from core.paths import MIRRORS
m = MIRRORS[sys.argv[1]]
print(m["ssh"], m.get("repo", "Desktop/AlgoProject"))' "$NAME") || {
  echo "remote: no server \"$NAME\" under mirrors: in config/machine.yaml"; exit 2; }
read -r HOST REPO <<< "$_CFG"

CMD=$(printf '%q ' "$@")
if [ "$DETACH" = "1" ]; then
  RUN="mkdir -p ~/Desktop/AlgoData/logs; L=~/Desktop/AlgoData/logs/remote-\$(date +%Y%m%d-%H%M%S).log
setsid nohup bash -c $(printf '%q' "$CMD; echo remote-rc=\$?") >\"\$L\" 2>&1 </dev/null &
echo \"pid \$!  log \$L\""
else
  RUN="$CMD"
fi

ssh -o BatchMode=yes -o ServerAliveInterval=30 "$HOST" "
cd ~/$REPO || { echo 'remote: no clone at ~/$REPO on $NAME' >&2; exit 97; }
if pgrep -u \"\$USER\" -f '[p]ipeline\\.autopilot|[b]in/workflow\\.sh' | grep -qvx \"\$\$\"; then
  echo 'remote: a workflow is running on $NAME — nothing run (rule 19: nothing CPU-heavy beside it)' >&2; exit 96
fi
if pgrep -u \"\$USER\" -x 'sqcli|StrategyQuantX' >/dev/null; then
  echo 'remote: SQX is running on $NAME — no pull, the code stays as it is under the run' >&2
else
  # One pull at a time: two commands sent at once each pulled, both wrote FETCH_HEAD, and one
  # died with «Cannot fast-forward to multiple branches» and ran nothing (📓 2026-10-11).
  flock -w 120 .git/remote-pull.lock git pull --ff-only -q \\
    || { echo 'remote: git pull failed on $NAME — nothing run' >&2; exit 97; }
fi
export SQX_OWNER=\"\${SQX_OWNER:-claude_leaseWeb}\"
export PATH=\"\$HOME/.local/bin:\$PATH\"   # pip --user tools (ruff, pyright): not on a non-login PATH
$RUN"
