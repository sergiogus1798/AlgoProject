# knowhow — hard-won facts, one card per fact

**Find, don't browse.** Reading costs tokens; every step below costs less than the next.

1. `grep -rh '^q:' knowhow/<domain>/` — or `grep -ril '<term>' knowhow/` when the domain is unclear.
2. Read only the card's header: `sed '/^## Evidence/q' knowhow/<domain>/<slug>.md`. The rule is there.
3. Read `## Evidence` only to reproduce or challenge the rule. `<domain>/INDEX.md` lists every card.

| domain | what it holds |
|---|---|
| `sqx-format/` | inside a `.sqx` or `project.cfx`: members, binaries, `SQStats`, identity, MC/WFM/SPP storage |
| `databanks/` | why strategies disappear: sync, memory vs disk, snapshots, curating a databank |
| `sqx-drive/` | driving SQX: endpoints, `-project` API, workers and roles, headless tasks, SPP, variants |
| `authoring/` | blocks, groups, templates, projects: the vocabulary, the builder's switches, the headless chain |
| `export/` | getting trades, metrics, SPP, WFM, cross-market results and bars out, and how to store them |
| `conditions/` | acceptance conditions, `sampleType`, which window selected a strategy, WFM/MC task anatomy |
| `locations/` | where things live on disk, logs, the XAUUSD corpus, report conventions |
| `columns/` | custom metric columns, frozen values, zero-P/L trades |
| `costs/` | commissions, swaps, spread, slippage, sessions, per-task costs |
| `research/` | statistical lessons: selection bias, nulls, Monte Carlo, targets, what a gate can measure |
| `perf/` | what things cost on this machine: cores, RAM budget, numba, pools, step durations |
| `eng/` | engineering habits that already cost time: parsing, resumable jobs, logs, portability |

## Writing a card

```
---
q: <the question it answers, with the words someone would grep for>
tag: 🔬|📓|🤔  date: YYYY-MM-DD  see: other-slug
---
# <the fact, as a title>
<the rule, 1–5 lines: a reader who stops here must act correctly>

## Evidence
<command, file, numbers — only what reproduces or challenges it>
```

🔬 verified by direct test · 📓 read from logs or files · 🤔 inferred (say what would confirm it).
English. Header ≤ 12 lines, card ≤ 3 KB (6 KB hard). **Edit the card that exists — never append, never
`cat >>`.** When a fact changes, rewrite the rule and bump `date:`; git keeps the old one. After
adding or renaming a card: `python3 tools/knowhowmap.py`. `tools/checks.py` enforces all of this.
