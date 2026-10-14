#!/bin/bash
# remote-check — prove on gorilla that what was just pushed works on another machine.
#
# Usage:  bin/remote-check.sh [REV_RANGE]     default origin/master@{1}..origin/master
#
# Runs on gorilla, through bin/remote.sh (pull first; exit 97 pull failed, 96 workflow running —
# then nothing runs): tools/checks.py, tools/audit_tests.py --changed <the range's .py files>,
# and a clean-tree check. tools/depmap.py is NOT run there: it rewrites docs/DEPENDENCIES.md in
# a read-only clone; checks.py already fails when that file is stale, which is the same proof.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1

RANGE="${1:-}"
[ -n "$RANGE" ] || RANGE='origin/master@{1}..origin/master'
FILES=$(git diff --name-only --diff-filter=d "$RANGE" -- '*.py') || exit 2
[ -n "$FILES" ] || { echo "remote-check: no .py files in $RANGE"; exit 0; }

# shellcheck disable=SC2086
exec bin/remote.sh gorilla bash -c 'python3 tools/checks.py && python3 tools/audit_tests.py --changed "$@"; rc=$?; d=$(git status --porcelain); [ -z "$d" ] || { echo "remote-check: gorilla clone is DIRTY:"; echo "$d"; rc=1; }; exit $rc' _ $FILES
