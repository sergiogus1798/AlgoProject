#!/bin/bash
# nightly-commit-proposal — the daily commit PROPOSAL, from cron. It can never commit.
#
# Hard rule 12: the owner commits. the /sync skill unattended would commit and
# push on its own, so it does not exist as a cron job; this script is its propose-only form. A Sonnet
# agent reads the uncommitted tree and writes, in AlgoData/audit/ (core.paths.AUDIT):
#   <date>-commit.md    Spanish, for the owner: groups (message, file count), EN CURSO, PARADAS, checks
#   <date>-commit.json  {"groups":[{"message","body","paths"}], "en_curso":[...], "paradas":[...]}
# The owner says «aplica la propuesta de commit» and a session runs `python3 -m tools.commit_apply`
# (deterministic, no model). See .claude/skills/sync/SKILL.md and manual chapter 10-github.
#
# Cannot commit, by construction: the agent gets Bash only for read-only git and du/ls/wc/stat/date;
# git add/commit/push/reset/stash/checkout/restore/rm/clean/rebase/merge/tag/branch, gh and `git -c/-C`
# are in --disallowedTools; and afterwards this script compares HEAD and the index with what
# it saw before and logs VIOLATION if either moved.
#
# 05:45 daily: after the fixer (04:00, 1-6 min) and, on Sunday, after the knowhow review (05:00) and
# docs-health (05:10), whose locks it waits for; 05:30 is reserved for the off-disk backup (encargo 41, 0.4).
#
# Usage:
#   nightly-commit-proposal            run it
#   nightly-commit-proposal --dry-run  resolve paths and the binary, print them, run nothing
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1
. "$ROOT/bin/lib-agent-alert.sh"

resolve_data
LOG="$DATA/logs/nightly-commit-proposal.log"
LOCK="$DATA/logs/.nightly-commit-proposal.lock"
TODAY=$(date +%F)
OUT="$DATA/audit/$TODAY-commit"

resolve_claude

dry_run "${1:-}" 'root   %s\nlog    %s\nout    %s.{md,json}\nclaude %s\n' "$ROOT" "$LOG" "$OUT" "${CLAUDE:-NOT FOUND}"

exec >>"$LOG" 2>&1
take_lock "$LOCK" "another proposal is running"

echo "=== $(date -Is) commit proposal start"
for l in .nightly-fix.lock .weekly-knowhow-review.lock .weekly-docs-health.lock; do
  exec 8>"$DATA/logs/$l"
  flock -w 14400 8 || { echo "--- $l still held after 4 h; skipped"; exit 1; }
  flock -u 8
done
if [ -z "$CLAUDE" ] || [ ! -x "$CLAUDE" ]; then
  echo "--- no claude binary found; skipped"; exit 1
fi

IN=$(mktemp -d)
python3 -m tools.commit_apply --facts > "$IN/facts.tsv"
if [ "$(wc -l < "$IN/facts.tsv")" -le 1 ]; then
  echo "Nada que proponer: el árbol está limpio ($TODAY)." > "$OUT.md"
  echo '{"groups": [], "en_curso": [], "paradas": []}' > "$OUT.json"
  echo "=== $(date -Is) clean tree, nothing to propose"; rm -rf "$IN"; exit 0
fi

# depmap rewrites docs/DEPENDENCIES.md, so run it before the facts are read.
{ echo "## depmap"; python3 tools/depmap.py 2>&1 | tail -3
  echo "## checks"; python3 tools/checks.py 2>&1 | tail -40; } > "$IN/checks.txt"
python3 -m tools.commit_apply --facts > "$IN/facts.tsv"

# HEAD and the index only: live sessions keep editing the tree while the agent runs.
before() { { git rev-parse HEAD; git diff --cached --name-status; } | sha256sum; }
B=$(before)

PROMPT="Propose today's commits. You only PROPOSE: git write commands are denied and nobody will run them for you.
Inputs: $IN/facts.tsv (every uncommitted path: porcelain code, age in minutes, size in KB) and $IN/checks.txt
(depmap and checks.py output, already run). Read .claude/skills/sync/SKILL.md: follow its Step 2 stops and its
Step 4 grouping themes and message rules, and ignore every step that commits or pushes. Read CLAUDE.md rule 12.
Classify every path in facts.tsv exactly once:
 - EN CURSO, not proposed: modified in the last 180 minutes (age_min < 180), or part of a half-finished change another
   session is still making (callers that no longer match, a new module without its README row or test, a test or
   check that fails on it). When in doubt, EN CURSO.
 - PARADAS, not proposed: config/machine.yaml, data files (.csv .parquet .sqx .db outside tests/fixtures/), anything
   that looks like a secret, anything over 2000 KB that is not a manual screenshot. Say why for each.
 - everything else goes into a group: one theme per group (prefix core:, sqx:, studies:, docs:, knowhow:, ui:, claude:,
   tools:, assets:), message under 72 characters with no final period, a body saying what changed and why; never claim
   verification that was not run. A path is in at most one group; files that must land together stay together.
Write two files with the Write tool and nothing else, no other file in the repo:
 1. $OUT.md, in Spanish, for the owner: a title with the date; a table of the groups (number, message, number of files,
    one-line reason); the EN CURSO list (path and age, grouped by folder if long); the PARADAS list with the reason;
    the depmap/checks result in two lines, naming any problem checks.py reports and whether it is in a proposed group
    (a group that makes checks.py red goes to EN CURSO instead); last line: «Para aplicarla di: aplica la propuesta de commit».
 2. $OUT.json: {\"date\": \"$TODAY\", \"groups\": [{\"message\": ..., \"body\": ..., \"paths\": [...]}], \"en_curso\": [paths],
    \"paradas\": [{\"path\": ..., \"why\": ...}]}. Valid JSON, paths exactly as in facts.tsv.
Finish with one line in Spanish: how many groups, files proposed, files EN CURSO, files PARADAS."

agent_run nightly-commit-proposal haiku "$OUT.json" timeout 30m "$CLAUDE" -p --output-format json --model haiku \
  --permission-mode acceptEdits --add-dir "$DATA" --add-dir "$IN" \
  --allowedTools Read Grep Glob Write \
    "Bash(git status*)" "Bash(git diff*)" "Bash(git log*)" "Bash(git show*)" "Bash(git ls-files*)" \
    "Bash(git check-ignore*)" "Bash(git rev-parse*)" "Bash(du *)" "Bash(ls *)" "Bash(wc *)" \
    "Bash(stat *)" "Bash(date*)" \
  --disallowedTools Edit NotebookEdit "Bash(git add*)" "Bash(git commit*)" "Bash(git push*)" \
    "Bash(git reset*)" "Bash(git stash*)" "Bash(git checkout*)" "Bash(git restore*)" "Bash(git rm*)" \
    "Bash(git clean*)" "Bash(git rebase*)" "Bash(git merge*)" "Bash(git tag*)" "Bash(git branch*)" \
    "Bash(git switch*)" "Bash(git worktree*)" "Bash(git -c*)" "Bash(git -C*)" "Bash(gh *)" \
    "Bash(rm *)" "Bash(mv *)" \
  -- "$PROMPT"
A=$(before)
[ "$A" = "$B" ] || echo "--- VIOLATION: HEAD or the index changed during the agent run"
python3 -c "import json; json.load(open('$OUT.json'))" || { echo "--- $OUT.json missing or invalid"; rm -rf "$IN"; exit 1; }
rm -rf "$IN"
echo "=== $(date -Is) commit proposal end"
