# research/literature — the literature scout's Python: search, validate, dedupe, store, queue

The front of the research chain. Before it, the literature file
(`AlgoData/research/literature/edges-2026-10-02.yaml`, 62 entries) was built once, by hand. Here
Python finds papers and keeps the books; the `literatureScout` agent
(`.claude/agents/literatureScout.md`) only reads a paper and drafts an entry. **No LLM in this
folder, no SQX, no price data**: the measuring is the market profile's
(`../marketProfile/literature.py` reads the entries; `report --top-up` measures the new ones, run by hand).

| file | what it does | run it | in → out |
|---|---|---|---|
| `amend.py` | What a session adds to a stored entry: the owner's answer to its question, and its measures. | imported; `scout measure ID SPECS.yaml`, `report --answer ID N` | entry + specs → the entry rewritten |
| `anchors.py` | Whether a quote is a verbatim sentence of the stored source, at the place the entry says. | imported | quote, place, text → errors |
| `calls.py` | The two headless calls of a run, as text in and text out: their prompts, and their answers applied. | `python3 -m studies.research.literature.calls triage-prompt` · `triage-apply RESULT.json` · `extract-prompt KEY [--retry RESULT.json --refused FILE]` · `extract-apply KEY RESULT.json [--last]` · `under PREFIX` — used by `bin/daily-literature-scout.sh` | inbox / paper → prompt; answer → register, entries |
| `dedupe.py` | Whether a paper, or a rule under another name, is already in the literature. | imported | paper / draft → what it duplicates |
| `fetch.py` | A paper's source as stored text: its abstract, and its full text page by page when reachable. | imported | paper → text, how much was read |
| `gather.py` | What a run registers: a page of a query's papers, a code collection's and a site's next items. | imported by `scout search` | query / collection → register rows |
| `report.py` | The owner's view of the literature: what was searched, rejected and accepted, and the queue. | `python3 -m studies.research.literature.report` · `--queue` · `--rejections` · `--for XAUUSD [--family reversion]` · `--answer ID N` · `--register` (rewrites `REGISTRO.md`) | register + profile → text |
| `schema.py` | The shape of a literature entry, and what a draft must satisfy before it is stored. | imported | draft + source → every refusal |
| `scout.py` | The scout's command: search papers, fetch one, reject it with its reason, accept or amend an entry. | `python3 -m studies.research.literature.scout search [--papers N]` · `inbox` · `fetch KEY` · `excerpt KEY` · `reject KEY --filter F --quote "…" --where "p. N" --reason "…"` · `reopen KEY` (a rejected paper back to the inbox) · `accept DRAFT.yaml` · `measure ID SPECS.yaml` · `cost RUN --tokens N --model M` (or `--result FILE…`, the JSON of each headless call, summed) | sources → register, entries |
| `search.py` | Papers from arXiv and OpenAlex for one query: metadata and abstract, no full text. | imported | query → paper rows |
| `selection.py` | What an entry records about its authors' selection: whether their sample covers our build. | imported | entry → symbols, overlap line |
| `store.py` | Where the literature lives on disk: the entries, the papers seen, their texts and the runs. | imported | — |
| `waiting.py` | The queue: each scout entry and whether the market profile has measured it yet. | imported | entries + `measures.csv` → rows |
| `config.yaml` | Every knob: papers per run, the sources, the queries (one board family each), the shortest quote, the similarity that flags two rules, asset class → symbols, family → id prefix | edited | — |
| `rules.md` | The text both the headless calls and the agent are given: nothing is inferred, the hard filters, the draft and its anchors, ambiguity is a stop | read by `calls.py` and by `.claude/agents/literatureScout.md` | — |

Manual page, in Spanish: chapter `90-explorador-de-bibliografia` of `AlgoData/manual-fuentes/`.
Tests: `tests/test_literature.py`. Skill: `/literature-scout`. Daily: `bin/daily-literature-scout.sh`.

## Single-turn calls with no tools (owner, 2026-10-02: «agents read the PDFs, and cheaply»; cost in tokens, never dollars)

A call's cost is its context times its turns: the fixed context of a headless Claude Code call
here is about 41k tokens (tools, MCP servers, skills), re-read at every tool use. So the daily
run uses no agent loop: `calls.py` prints a prompt, `claude -p --tools ""` answers once, `calls.py`
applies the answer through the same `reject` and `accept` — the validator is unchanged. One
triage call over the abstracts, one extraction call per surviving paper on its `excerpt`, one
retry when a draft is refused, then `failed`. `run.model` (opus) reads, `run.triage_model` (haiku)
triages; `run.budget_tokens` is a runaway guard, not a ration (owner: spend what reading needs).
What each scheme cost per paper: `knowhow/market-profile/literature-scout-yield.md`; today: `report`.

## What it writes — `AlgoData/research/literature/`

| file | one row per | what |
|---|---|---|
| `papers.jsonl` | paper the search ever returned | `key`, `source`, `arxiv`, `doi`, `title`, `authors`, `year`, `venue`, `url`, `pdf`, `abstract`, `query`, `family`, `run`, `found`, `status` (`inbox`, `rejected`, `accepted`, `duplicate`, `failed`), `read`, `filter`, `quote`, `where`, `reason`, `entries` |
| `papers/<key>.txt` | paper fetched | the source every quote is checked against |
| `scout-<day>.yaml` | entry accepted that day | the sixteen keys of the hand-built file (the contract `marketProfile/bibliography.py` reads) plus `paper`, `read`, `selection`, `anchors`, `question`, `similar_to`, `translation.measures` (one per parameter value the paper tested) and `translation.tested_by` (existing measures that state the same rule) |
| `runs.jsonl` | run closed with `scout cost` | papers read, by status, entries, model, calls, tokens (and the part re-read from cache), per paper and per entry — never dollars |
| `REGISTRO.md` | paper ever seen, newest first, in Spanish for the owner | date, title and link, year, read in full or abstract only, and what came of it: «útil» with its entry ids, «nada» with the filter and reason, «repetido» |

## The rules the code enforces, and the ones it cannot

- **A quote not in the stored text is refused** (`anchors.found`), and so is a field without an
  anchor, an abstract-only read quoting a page, and a value that says «not stated in source»
  while its anchor quotes something (or the reverse). What the code cannot check is that the
  *value* says no more than the quote: that is the agent's rule and the owner's reading.
- **`id`, `source`, `verified`, `read`, `overlaps_is`, `overlaps_oos1`, `overlaps_oos2` are stamped** from the register and from
  `assets/`, never drafted: a draft that carries one is refused.
- **The clock** (hard rule 15): `needs_clock` must open with `no`, and the translation is
  searched for clock words. **Two conditions at most** (hard rule 14): `translation.conditions`
  and, in a measure, `enter` plus one `when`. **One direction** (hard rule 13): a symmetric rule
  is `both (…)` and the profile measures each side apart; two legs held together are rejected.
- **A rule with two readings** (hard rule 11) carries a `question` and no measure until the
  owner answers (`report --answer`); the measure is written after that, by a session.
- **Practitioner sites** (`sources.web`; owner, 2026-10-02): Oxfordstrat's strategy pages, Quantpedia's
  free screener, AQR's research index, `per_run` articles each. traders.com, SSRN, the Alpha
  Architect pages and Semantic Scholar refuse a script; Open Source Asset Pricing, JKP and the
  French library are cross-sectional equity factors and data, which the first hard filter rejects.
- **A substring passes as a quote** (20 characters at least): nothing enforces a whole sentence.
  **One question per entry**: two independent ambiguities are written as their combinations.
- **No cap on the queue** (owner, 2026-10-02: «si salen más se prueban»).
- **Repositories of strategies** (`sources.repos`; owner, 2026-10-02): they enter with the lowest
  grade, `code repository`, stamped by Python whatever the draft says, and an item that reports no
  backtest of its own is rejected (`no_backtest`). `per_run` items of each collection per run.

## The join with the rest of the chain

| what | where |
|---|---|
| a new entry gets its measures in the market profile | `translation.measures` → `marketProfile/literature.py` adds it to the profile's measures with `tag: literature`, `lit: <id>`; `marketProfile.report --top-up` measures only what is new |
| it is counted in the ledger | the top-up appends one row per measure, direction and cell to the profile's `ledger.jsonl`, as every profile measure does |
| it reaches the board | a measure that passes the four filters makes its family pass in that cell: `studies.research.board` reads `scores.csv` |
| it reaches the `ideaExpert` as a `libros` quarry | `report --for <SYMBOL> --family <f>`; the idea file's `Origen:` line names the entry id, and `memory/ideas.py` counts it as `from_book` |
