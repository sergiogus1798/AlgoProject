# sqx-lock — the real owner lock bin/sqx-worker.sh writes and enforces (OPEN.md #32).
#
# One JSON file per install, <install>/user/log/OWNER: {holder, pid, since}. `start` writes
# it once the worker is up; `stop` from a different holder refuses unless --force; a lock
# whose sqcli PID is dead and whose port is down is stale and clears itself. Sourced by
# bin/sqx-worker.sh and by tests/test_worker_lock.sh, so there is exactly one implementation
# to test and to trust.
#
# The caller sets WORKER (the install's top folder) and defines running() (true when its
# port answers) before sourcing this file.

owner_file() { printf '%s/user/log/OWNER' "$WORKER"; }

# Holder = $CLAUDE_CODE_SESSION_ID when set (Claude sessions export it, subagents inherit
# their parent's, which is right — one Claude session, one holder across its subagents),
# else an explicit --owner/$SQX_OWNER, else "owner" (the window, or a human at a shell).
resolve_holder() {
  if [ -n "${CLAUDE_CODE_SESSION_ID:-}" ]; then printf '%s' "$CLAUDE_CODE_SESSION_ID"
  elif [ -n "${OWNER_ARG:-}" ]; then printf '%s' "$OWNER_ARG"
  elif [ -n "${SQX_OWNER:-}" ]; then printf '%s' "$SQX_OWNER"
  else printf 'owner'; fi
}

# owner_field holder|pid|since — '' when the lock is missing or the key is absent.
owner_field() {
  [ -f "$(owner_file)" ] || return 0
  python3 -c '
import json, sys
try:
    d = json.load(open(sys.argv[1]))
except (OSError, ValueError):
    sys.exit(0)
print(d.get(sys.argv[2], ""))' "$(owner_file)" "$1" 2>/dev/null
}

# write_lock <sqcli-pid> — called right after `start` confirms the worker is up.
write_lock() {
  mkdir -p "$(dirname "$(owner_file)")"
  python3 -c '
import datetime, json, sys
json.dump({"holder": sys.argv[2], "pid": int(sys.argv[3]),
           "since": datetime.datetime.now().astimezone().isoformat(timespec="seconds")},
          open(sys.argv[1], "w"))' "$(owner_file)" "$(resolve_holder)" "$1"
}

# A lock whose sqcli PID is dead and whose port is down is stale: nothing is running, a
# crash or a `kill -9` skipped the clean `stop` that would have removed it. Clearing it
# here means a dead session never blocks a live one from `start` or `stop`.
clear_stale_lock() {
  [ -f "$(owner_file)" ] || return 0
  running && return 0
  local pid; pid=$(owner_field pid)
  [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null && return 0
  rm -f "$(owner_file)"
}

# refuse_stop_if_held — call right before a `stop` touches a running install. FORCE_STOP=1
# (the --force flag) overrides it; no lock, or the caller's own lock, never refuses.
refuse_stop_if_held() {
  [ -f "$(owner_file)" ] || return 0
  local held cur; held=$(owner_field holder); cur=$(resolve_holder)
  if [ -z "$held" ] || [ "$held" = "$cur" ] || [ "${FORCE_STOP:-0}" = "1" ]; then
    return 0
  fi
  printf 'REFUSING: %s is held by %s since %s (you are %s).\n' \
    "$(basename "$WORKER")" "$held" "$(owner_field since)" "$cur"
  printf "A stop from a different holder kills someone else's run (OPEN.md #32).\n"
  printf 'Use --force only when you are sure that holder is gone.\n'
  return 1
}
