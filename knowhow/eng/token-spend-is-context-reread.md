---
q: Where does most of the token spend of a long session go?
kw: why are the tokens so high, where do Claude tokens go, token cost, cache read, long session, 1M context, compact, clear, graphify code graph, graphify-out, graphify query explain affected, reduce tokens
tag: 🔬  date: 2026-10-02  see: cron-schedule-no-shared-minute, what-a-tool-sends-is-re-read-too
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
Waiting on SQX (rule 18), one background Bash command, `run_in_background`, with the worker's `sqcli` PID in `$PID`:
`L=$(ls -t <worker>/user/log/StrategyQuant/log_*.log | head -1); S=$(stat -c %s "$L"); until tail -c +$((S+1)) "$L" |
grep -q "Project finished" || ! kill -0 $PID 2>/dev/null || [ $(awk '/MemAvailable/{print int($2/1048576)}'
/proc/meminfo) -lt 15 ]; do sleep 20; done; echo ended` — take `$L` and `$S` BEFORE `action=start`. At 450k of context
a 3-minute pulse is 20 turns an hour re-reading everything; the code paths already block (`sqx.projects.live.wait`).
By context size of the turn (main sessions, same transcripts): under 200k 15 % of the spend, 200-400k 24.5 %, 400-700k
21.4 %, over 700k 7.5 %; every turn above 200k run at 150k instead would have saved 32 %. Hence `autoCompactWindow:
300000` in `~/.claude/settings.json` (tokens or `auto`; `/autocompact` shows and sets it; env
`CLAUDE_CODE_AUTO_COMPACT_WINDOW`). Subagents: `general-purpose` on Opus 22.8 % of the spend, on Sonnet 7.7 %, every
named expert under 0.5 %. Cache rewritten after a pause over 5 min: 261 times, 6.2 % extra — `/compact` before leaving.
2026-10-09: 406 transcripts of this project (2026-09-17 → 10-09), every component of `usage` summed: **16.000 M
tokens**, 98,0 % cache read, 1,6 % cache write, 0,4 % output. By model: Opus 5.5 60 %, Opus 5 23 %, Sonnet 5
13,5 %, Fable 5.1 3 %. Amortised cost of a block (its tokens x the assistant messages that follow it in the same
session): `Bash` results 3,71 Bn (23.540 calls, 470 tokens each), the `Bash` commands themselves 1,49 Bn (5,4 M
raw, 230 tokens each), `Read` 364 M (510 calls), the owner's own text 293 M, images 152 M (353 reads, 430k
amortised each), `Agent` results 151 M. The fixed prefix is 41k (median of the first message) x 58.667 assistant
messages = 2,42 Bn, 15 %. 12.680 of the Bash calls opened with a `cd` of their own. The 15 longest sessions were
53 % of the whole spend; one prompt alone («Lee docs/encargos/21-prueba-workflow-completo.md») ran 2.393 steps.
Daily spend after the 2026-10-02 measures (`bashOutputMaxChars: 10000`, `autoCompactWindow: 300000`, rules 16-18):
1.200-2.666 M a day in late September against 175-290 M a day from 10-05 — the measures worked, rule 20 is the
increment. Subagent spend is NOT in these files (`isSidechain` carries no usage): 1.174 `Agent` calls, of which
659 council members, are invisible here — hence the council only on design tasks.
