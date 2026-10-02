---
q: ideaReviewer, does the reviewer count as trials, looks at the data, adversarial review of ideas, multiple testing, reviewer tools
tag: 🤔  date: 2026-10-02  see: ideas-are-ledger-trials
---
# The reviewer adds no trial because it cannot compute: no shell, text only
The ledger counts the hypotheses the `ideaExpert` MEASURED on `build`. The `ideaReviewer`
(`.claude/agents/ideaReviewer.md`) has `tools: Read, Grep, Glob` — no Bash — and reasons from the
idea file, the cell's memory and the asset's card, so nothing it does is a look at the data and
nothing is added to N. Keep it that way: giving it a shell, or letting it read exports, turns every
objection it checks into an uncounted look. An objection that needs a number is written as «habría
que medir…» for the owner. Whether its «tumbada» removes an idea is `memory/config.yaml` ›
`review.removes` (off: it annotates; the veto is the owner's either way).

## Evidence
Inferred from the design, not measured: no real proposal has gone through the reviewer yet
(2026-10-02). What would confirm it: the first real run's transcript shows no data file read, and
`ledger.report`'s K for the cell is unchanged before and after the review.
`proposal.check` refuses a draft without a review or whose `reviewer` is the proposer
(`python3 tests/test_research_board.py`).
