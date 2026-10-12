---
name: literature-scout
description: Run the literature scout by hand — search arXiv and OpenAlex for published trading research, let the literatureScout agent reject each paper by the owner's hard filters or extract its rules as entries anchored to verbatim quotes, record what the run cost, measure the new entries on `build` with the market profile, and show the owner the rejections, the entries, the open questions and which cells reach the board. Touches no SQX. Use when the owner asks to look for papers, for new published ideas, to feed or extend the literature file, "busca papers", "qué dice la bibliografía", or about the queue of entries waiting to be measured.
---

# /literature-scout

The front of the research chain: papers in, anchored entries out. From an entry on, the chain
that exists takes over (market profile → board → `researchDirector` → the owner's veto). Nothing
here touches SQX, and nothing here reads `oos1` or `oos2`. Code and tables:
`studies/research/literature/README.md`. It also runs alone every day
(`bin/daily-literature-scout.sh`); this skill is the same run by hand.

## 1. Search (0 tokens) — only to look before reading

```bash
python3 -m studies.research.literature.scout search          # 20 papers; --papers N for another count
                                                             # (the daily script runs this itself)
```

Prints `RUN <id>` and the new papers. A paper already in the register or in the literature file
is dropped and recorded as `duplicate`. Nothing new → say so and go to step 4.

## 2. Read the papers — `bin/daily-literature-scout.sh`

```bash
bin/daily-literature-scout.sh     # search, triage, fetch, one call per paper, cost, register
```

It does step 1 itself. Every read is a single-turn headless call with no tools (owner,
2026-10-02: PDFs are read by agents, never by this session, and cheaply; cost is said in tokens,
never dollars). Log: `AlgoData/logs/daily-literature-scout.log`. Never Read a paper's text in
this session. The `literatureScout` agent exists for a one-off paper the owner names
(«Extract <key>» after `scout fetch`); it costs several times more per paper than the script.

What a run costs is in `python3 -m studies.research.literature.report` (the `run` lines, tokens
per paper) — say it before launching when the owner did not ask for a run explicitly.

## 3. Measure the new entries on `build`

```bash
nice -n 19 python3 -m studies.research.marketProfile.report --top-up
```

Only the measures the stored cells lack are run, against their own null draws; then the whole
map is judged again (Benjamini-Hochberg over every test, so a new measure also makes every
other one slightly harder to pass). `BIBLIOGRAFÍA sin medir — …` lines name the entries left
out and why. It holds about 1.4 GB per worker: never raise `run.workers` above 4 while an SQX build is
running (Python's share of the RAM is 20 GB for every session), and check `free -g` first.

## 4. Show the owner

```bash
python3 -m studies.research.literature.report                # status, runs' cost, questions, queue
python3 -m studies.research.literature.report --rejections   # each rejection: filter, reason, quote
python3 -m studies.research.board                            # which cells are on the board now
```

Tell him, in Spanish: papers searched, rejected by which filter, entries accepted, each one's
reading on `build`, which cells reach the board, tokens per paper and per entry (never dollars).
The papers register he reads is `AlgoData/research/literature/REGISTRO.md`.
An entry that passes nothing is a result — say it plainly.

**An open question is a stop (hard rule 11).** Show each `PREGUNTA` with its readings and ask
him which; write his choice with `report --answer <ID> <N>`. Never choose for him. After his
answer the entry still has no measure: write them from the reading he chose (existing
`CONDITIONS` keys only, one per parameter value the paper tested) as a YAML list of
`{name, args}` and `python3 -m studies.research.literature.scout measure <ID> <that file>`, then
top-up again.

**«sin medida: falta una condición»**: the entry's `translation.note` names the condition
`marketProfile/measure/rules.py` lacks. Adding it is code — one line in `CONDITIONS`, its series
in `series.py` or `higher.py` when needed — done by a session, never by the scout; then
`scout measure` as above.

## Never

Launch a build, a template or the director from here; measure on `oos1`/`oos2`; edit an entry's
anchored fields by hand; raise `run.budget_tokens` or install a paper-search tool without the
owner's yes; run two scouts at once.
