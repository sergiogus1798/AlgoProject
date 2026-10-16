#!/bin/bash
# remote — run a command in another server's clone of this repo, after `git pull` there.
#
# The other servers (`mirrors:` in config/machine.yaml — gorilla) hold a read-only clone that
# only ever receives code by `git pull`. This is the one door for running anything there, so the
# pull is a mechanism and not something to remember (owner, 2026-10-10):
#   - no SQX running there: `git pull --ff-only` first; if it fails, nothing runs (exit 97).
#   - SQX running there: no pull — the code is never changed under a run — and it says so.
#   - a workflow (command word bin/workflow.sh, or python3 -m pipeline.autopilot…) asked for on a mirror whose last data copy did not end (`logs/MIRROR_OK.<name>`,
#     written by bin/mirror-data.sh, says «copying»): nothing runs (exit 95). With no such file at all
#     (no mirror has ever succeeded) the workflow runs with a warning (owner, 2026-10-16, encargo 76 E1);
#     once the file exists it must not say «copying».
#   - a workflow running there (`pgrep -f` on pipeline.autopilot / bin/workflow.sh — it leaves no
#     lock or pid file, so the process name is the marker): nothing runs (exit 96).
#
# Usage:
#   bin/remote.sh gorilla <command...>            run it in the clone, wait, return its exit code
#   bin/remote.sh gorilla collect [<PROJECT>] [--dry-run]
#                                                 bring a project's survivors (store folder, ledger rows,
#                                                 registry row, reports; suffix _gorilla) here and archive
#                                                 them; no project = every one not here yet. Only reads
#                                                 gorilla, no pull (portfolio/common/construct/adopt.py)
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
[ $# -ge 2 ] || { sed -n '2,21p' "$0"; exit 2; }
NAME="$1"; shift
[ "${1:-}" = "collect" ] && { shift; exec python3 -m portfolio.common.construct.adopt "$NAME" "$@"; }

_CFG=$(python3 -c '
import sys
from core.paths import DATA, MIRRORS
m = MIRRORS[sys.argv[1]]
print(m["ssh"], m.get("repo", "Desktop/AlgoProject"), DATA)' "$NAME") || {
  echo "remote: no server \"$NAME\" under mirrors: in config/machine.yaml"; exit 2; }
read -r HOST REPO DATA <<< "$_CFG"
# A workflow is a command whose word is bin/workflow.sh or `python3 -m pipeline.autopilot…`,
# never one that merely names it in an argument (a grep, a log path).
if [[ "$1" == bin/workflow.sh || "$1" == */bin/workflow.sh \
   || ( "$1" == python* && "${2:-}" == -m && "${3:-}" == pipeline.autopilot* ) ]]; then
  OK=$(cat "$DATA/logs/MIRROR_OK.$NAME" 2>/dev/null) || {
    OK="never mirrored by this version"
    echo "remote: warning: no MIRROR_OK.$NAME yet (no mirror has ever succeeded) — running anyway" >&2; }
  [[ "$OK" != copying* ]] || {
    echo "remote: the last data copy to $NAME did not end ($OK): run bin/mirror-data.sh first" >&2; exit 95; }
fi

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
