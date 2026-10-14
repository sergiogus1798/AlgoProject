# CONTRIBUTING — how a change is made, checked and handed over

What the code must look like is `CODESTYLE.md`. This file is the process around it, for every
session and agent that changes code here. The hard rules of `CLAUDE.md` take precedence — above all
rule 12: one folder, `master`, nothing committed without the owner's yes.

---

## 1. Before writing

- **Plan when it is big.** More than three files, or a new module: five lines before any code — what,
  which files, what is deleted, what is reused, and the command that will prove it works.
- **Look first.** `graphify query`, `graphify affected "<symbol>"`, or a grep. Re-implementing what
  lives three folders away is the commonest way this codebase grows.
- **Stay inside the task.** The diff touches what the task named. What you notice on the way goes to
  `OPEN.md`, not into the diff.

## 2. While writing

- **A bug arrives with its test**: first the test, seen failing; then the fix, seen passing.
- **A refactor is proved by difference.** Before the old code is deleted, old and new run on the same
  real input and their outputs are compared; the comparison is the evidence.
- **Three tries, then a report.** The same failure three times: stop and say what was tried. Green is
  never reached by weakening a test, loosening a threshold or catching the error.
- Nothing destructive runs without asking. A skill the owner invokes that deletes by design
  (`/curate`, `/oos-gate`) is the asking.

## 3. Checks

```bash
python3 tools/depmap.py && python3 tools/checks.py && python3 tools/audit_tests.py --changed
```

- `depmap.py` regenerates `docs/DEPENDENCIES.md` from the real imports. Never edit it by hand.
- `checks.py` is `CODESTYLE.md` §12. It blocks nothing while you work; it is green before you hand over.
  When a ratchet count falls it rewrites `tools/ratchet.json` — that file goes with the change.
- `--changed` runs the tests you touched and every test that imports, directly or transitively, a
  changed `.py`. The whole suite runs nightly.

## 4. Performance

A change to a module with a target in `perf/inputs/targets.py` is measured before and after with
`python3 -m perf.catalogue --only <target>`, and both numbers go in the commit message. A new module
that reads a population or runs simulations gets its target in the same task. → `perf/README.md`,
the `/perf` skill.

## 5. Review

For any change beyond a one-file fix, an **independent review** comes before the commit question.
Spawn the `reviewer` agent (Sonnet; `model: "opus"` when the diff touches inference or statistics) and
give it three things only: `git diff -- <the task's files>`, `CODESTYLE.md`, and the task's goal in
one line. **Never your reasoning or your summary** — a reviewer handed the author's account returns it
confirmed. Fix or rebut each `file:line` finding, and tell the owner the ones left standing.

**A mistake caught twice becomes a check** in `tools/checks.py`, so the third is caught by a machine.

## 6. Orchestrated work

A change that creates a module, touches more than three files or changes a contract between packages
is planned by one capable agent and written by cheaper ones (`CLAUDE.md` rule 17). Below that size one
session does it: the briefs would cost more than the change.

- **The orchestrator (Opus) reads, decides and splits — it writes no code**, and it receives file
  lists and command tails from the executors, never diffs or whole files.
- **Each piece is a brief of five things**: the goal in one sentence; the closed list of files it may
  touch; the existing code it must reuse; the acceptance command; and "if the plan looks wrong, stop
  and say so — do not improvise".
- **Executors run on Sonnet**, Haiku when the piece is purely mechanical. Design, statistics and
  template authoring are not handed down.
- **Parallel only on disjoint files** — there is one folder and no worktree.
- **The orchestrator closes the loop**: it runs every acceptance command and `checks.py` itself, then
  the review of §5 reads the whole diff.

## 7. Handing over

- **"Done" carries its evidence**: the command run and the tail of its output — never "this should
  work". A new command is also run once for real on a small real input, and ships with its manual
  chapter (`CLAUDE.md` rule 8).
- **Read your own `git diff`** before reporting: a debugging `print`, a leftover or another task's
  file is found there.
- The task ends with the list of files changed and the commit question (`CLAUDE.md` rule 12).
