---
q: Why cap what a tool call SENDS, not only what it returns?
kw: heredoc in context, inline python script cost, bash command tokens, cd before every command, image png tokens, screenshot cost, read an image, haiku for unattended agents, cheapest model, tool input cost
tag: 🔬  date: 2026-10-09  see: token-spend-is-context-reread
---
# A command, a heredoc and an image are re-read by every later turn, exactly like the output
Rule 18 and the Bash output cap only cover what comes back. What goes out is re-read too: over 406 transcripts the
`Bash` **commands themselves** cost 1,49 Bn tokens amortised — 230 tokens each, mostly `python3 - <<'EOF'` scripts
that then live in the context to the end of the session. So a script over ~20 lines goes to the scratchpad and runs
from there, nothing gets a `cd` of its own (54 % of the calls opened with one: absolute path, or `&&`), and a PNG —
~1,6k tokens, 430k amortised — is opened only by the `uiCritic` agent.
Mechanical unattended work runs on `haiku`: Haiku 5.5 (`claude-haiku-5-5`, 2026-10-07) is a fifth of Sonnet's input
price and a fortieth of Opus's, and the CLI alias and `model: haiku` both resolve to it (verified 2026-10-09).

## Evidence
2026-10-09, the audit behind rule 20 of `CLAUDE.md`: 406 transcripts, 2026-09-17 → 10-09, 16.000 M tokens.
Amortised cost (a block's tokens x the assistant messages that follow it in its session): `Bash` results
3,71 Bn over 23.540 calls, `Bash` command text 1,49 Bn (5,4 M raw), `Read` 364 M over 510 calls, images 152 M
over 353 reads, `Agent` results 151 M over 1.174 calls, `Write` inputs 378 M over 907 calls. First command word:
`cd` 12.680, `python3` 2.161, `sed` 1.097, `grep` 1.046, `cat` 1.043. Moved to `haiku` the same day:
`projectJanitor` and its `bin/weekly-project-cleanup.sh`, `bin/nightly-commit-proposal.sh`, and
`studies/research/literature/config.yaml` `run.triage_model`. Kept on `sonnet` because they judge code, prose or
rules: `auditor`, `fixer`, `documenter`, `fundingWatcher`, `dealHunter`, `uiCritic`, `literatureScout`.
Haiku 5.5 list price $0,10 / $0,50 per MTok up to a 100k prompt, $0,50 / $2,50 above it, against Sonnet 5.5's
$2 / $10 and Opus 5.5's $4 / $20. Verified with `claude -p --model claude-haiku-5-5` and `--model haiku --output-format json`, whose `modelUsage`
reports `claude-haiku-5-5`.
