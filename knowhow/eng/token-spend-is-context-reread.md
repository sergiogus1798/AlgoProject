---
q: why are the tokens so high, where do Claude tokens go, token cost, cache read, long session, 1M context, compact, clear, graphify code graph, graphify-out, graphify query explain affected, reduce tokens
tag: 🔬  date: 2026-10-02  see: cron-schedule-no-shared-minute
---
# Three quarters of the spend is re-reading a long session's context, not the fixed prompt
Every turn re-reads the conversation: cost is 75 % cache reads, 16 % cache writes, 8 % output. The dear sessions
hold 300-530k tokens per turn for 500-1700 turns; `CLAUDE.md`, skills and MCP names are under 5 % of such a turn.
So: one task per session, `/clear` between tasks, `/compact` at a milestone, a long job's state in a file. Tool
output fills the context — Bash 81 %, Read 16 %: cap it (`| head`, a slice, `grep -c`); rules 16-17 of `CLAUDE.md`.
For "where is X, what calls it": `graphify explain "<path>::<symbol>"`, `graphify affected "<symbol>"`, `graphify
query "<question>" --budget 800` — local AST, no LLM, in `AlgoData/graphify/graphify-out` behind the git-ignored
`graphify-out` link; cron 02:20, or `graphify update .`. Never `graphify hook install` nor `graphify claude install`.

## Evidence
2026-10-02: 477 transcripts of this project (2026-09-02 → 10-02), usage summed per unique message id: 10 119 M
cache-read tokens, 168 M cache-write, 20.8 M output, 0.1 M uncached input. Top sessions: 1693 turns at 511k per turn,
1009 at 439k, 789 at 480k. Subagent transcripts: about 31 % of the total. Tool results over the last 12 days: 103 M
chars, Bash 83.7 M (33 821 calls), Read 16.8 M (2 331 calls, 246 over 20k chars). Graph: `graphifyy` 0.9.73 by
`uv tool install`, `graphify extract . --code-only --out AlgoData/graphify` 80 s on 1325 files; after `update`
19 548 nodes, 41 217 edges.
Bash cap: setting `bashOutputMaxChars` (default 30 000 chars inline, clamped 4 000-128 000; the rest goes to a file with a
preview and its path), Claude Code 2.1.287. Over 34 001 Bash results of 12 days: a cap of 20 000 saves 2.3 % of the chars,
15 000 6.8 %, 10 000 15.7 % (cuts 6 % of the results), 6 000 29 %.
