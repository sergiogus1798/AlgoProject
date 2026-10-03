# knowhow — hard-won facts, one card per fact

**Find, don't browse.** Reading costs tokens; every step below costs less than the next.

1. Scan a domain's questions: `grep -rh '^q:' knowhow/<domain>/`. Find a card by symptom or error text:
   `grep -rli '<symptom or error text>' knowhow/` (it matches the `kw:` line).
2. Read only the card's header: `sed '/^## Evidence/q' knowhow/<domain>/<slug>.md`. The rule is there.
3. Read `## Evidence` only to reproduce or challenge the rule. `<domain>/INDEX.md` lists every card with its `q:`.

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
| `eng/` | engineering habits that already cost time: Claude, hooks and cron, tokens, logs, refactoring, portability |
| `mt5/` | MetaTrader 5: Wine install, the tester, MetaEditor, EA news filters and calendars, the fleet and verify clocks |
| `ui/` | our desktop window: Qt traps, the daemon, progress, the rail, how its tests run |
| `pipeline/` | the unattended pipeline: autopilot facts, the blind door and the OOS2 door, ledger thresholds, resumable runs |
| `market-profile/` | the market profile and the research chain: its power and blind spots, ideas as trials, literature, the director's memory |

## Writing a card

```
---
q: <ONE plain question an agent would ask, ≤ 120 characters, ending in ?>
kw: <symptoms, error strings, keywords: free length, for grep -rli; never shown in an index>
tag: 🔬|📓|🤔  date: YYYY-MM-DD  see: other-slug
---
# <the fact, as a title>
<the rule, 1–5 lines: a reader who stops here must act correctly>

## Evidence
<command, file, numbers — only what reproduces or challenges it>
```

🔬 verified by direct test · 📓 read from logs or files · 🤔 inferred (say what would confirm it).
English. Header ≤ 12 lines (the `kw:` line is extra), card ≤ 3 KB (6 KB hard). **Edit the card that exists — never append, never
`cat >>`.** When a fact changes, rewrite the rule and bump `date:`; git keeps the old one. After
adding or renaming a card: `python3 tools/knowhowmap.py`. `tools/checks.py` enforces all of this.
