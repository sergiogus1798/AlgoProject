# Open Issues

Tracked issues for the AlgoProject / StrategyQuant X pipeline.
Split out of `CLAUDE.md` on 2026-09-02 so the always-loaded instructions stay lean.
Migrated into the rebuilt project on 2026-09-03; paths updated to this tree.

Status: 🔴 open · 🟡 in progress · 🟢 resolved · ⚪ closed / won't fix

Reviewed 2026-09-04. 6 and 7 are resolved, 5 is closed, 3 and 9 are settled and built but blocked on
one thing: **the master GUI must be closed**. Nothing here writes to the master while it is up.

| # | was | now | what remains |
|---|---|---|---|
| 1 | 🟡 | 🟡 | mitigation needs the lifecycle lane |
| 3 | 🔴 | 🟡 | repair written and dry-run verified — run it with SQX closed |
| 4 | 🔴 | 🟡 | detector wired; restamping is GUI work |
| 5 | 🔴 | ⚪ | decoded and proven dead metadata |
| 6 | 🔴 | 🟢 | archived, 4.4 GB → 102 MB; schedule it |
| 7 | 🟡 | 🟢 | golden test committed with a 28 KB fixture |
| 9 | 🔴 | 🟡 | **confirmed**: the template really is ignored. Owner decided to change nothing |
| 10 | — | 🔴 | new: the maps ignore `active`, so issue 1's table overstates 5 of 9 projects |
| 11 | — | 🔴 | new: the master's only template project points at the worker's install |
| 12 | — | 🟠 | new: nothing cited in `knowhow/` is reproducible from the current data root |
| 13 | — | 🟠 | new: two analyses claim more than their samples support |
| 16 | — | 🟠 | new: an export has no manifest, and the trade-dedup gap now spans three live reports |
| 17 | — | 🟠 | new: `Param Count` corrected, but every existing strategy keeps the old stored value |
| 19 | — | 🔴 | new: three Monte Carlo thresholds are placeholders and need the owner's decision |
| 20 | — | 🟡 | new: `.claude/settings.json` gates one destructive repair script but not the other |
| 21 | — | 🟡 | new: `bin/sqx-worker.sh` is bash, so half the project cannot run on Windows |

---

## 1. 🟡 Databanks shrink between sessions — CAUSE FOUND

**Not a record cap, and not specific to XAUUSD.** Two mechanisms combine:

**(a) SQX treats memory as the source of truth.** Every sync writes memory → disk and deletes
on-disk `.sqx` files that are not in memory. The log states it plainly:

```
log_2026_08_18.log
08:11:31  'Project - USDJPY/WFM'  before sync 248 / after sync  36 / saved  36 / removed 248
08:24:58  'Project - XAUUSD/WFM'  before sync 1208 / after sync 1142 / saved 1142 / removed 66  (826 s)
```

The USDJPY line is an **hourly auto-sync**, not a shutdown. So closing SQX is *not* the trigger —
shutdown is merely one more sync. Hard rule 1 is a symptom, not the disease.

**(b) The XAUUSD task chain clears databanks in memory, by design.** From `project.cfx/config.xml`,
the 16-task chain ends:

```
13  Automatic retest 11   SPP (OOS)
14  Automatic retest 2    WFM
15  Clear databanks       ClearDatabanks-Task1.xml
16  Go To Task            → unconditional jump back to "Build strategies 2"
```

`ClearDatabanks-Task1.xml` empties **9 databanks including `SPP OOS`**. Task 16 then loops forever.
There is also an inner loop: task 7 `Clear first Turn` + task 8 `Go back first Turn`
(condition: `Retest Markets - OOS` count `< 1000`).

So each outer cycle empties `SPP OOS` in memory, and the next hourly sync deletes its files from
disk to match. That is the `1208 → 480 → 165` bleed.

**`WFM` is in neither clear list** — its shrink is mechanism (a) alone: the databank was only
partially loaded in memory, and the sync pruned disk down to it. Note the 826 s save time; the
large databanks are slow enough that a partial/incomplete load is plausible.

**GBPJPY is not immune — the note in `CLAUDE.md` was wrong.** Mapping all six projects with
`dump_project.py` shows every one of them has the same shape: build → robustness gauntlet →
`ClearDatabanks` → **unconditional** `GoToTask` back to the builder.

| project | tasks | databanks cleared while auto-syncing | terminal output |
|---|---|---|---|
| XAUUSD | 16 | 7 incl. `SPP OOS` | `WFM` |
| USDJPY | 19 | 8 incl. `SPP OOS` | `WFM` |
| AUDJPY | 19 | 8 incl. `SPP OOS` | `WFM` |
| EURUSD | 19 | 8 incl. `SPP OOS` | `WFM` |
| GBPJPY H1 | 20 | 3: `OOS`, `RetestPairs`, `WFM Performance` | `Final Testing` |
| SP500 H1 | 18 | 6 incl. **`WFM`** | `FinalOOS`, `TICK REAL` |

GBPJPY simply had not reached its clear task during the observed window, so its syncs logged
`removed 0`. SP500 H1 clears its `WFM` databank outright. Every project is exposed.

**Next step (needs the lifecycle lane):** confirm by watching one sync after a ClearDatabanks task
fires. Full task-by-task maps: regenerate with `dump_project.py <PROJECT>` (the old per-project
pipeline docs are retired — see the entry below). Mitigation options: set the at-risk databanks to `Auto-sync never` (they currently say
`Auto-sync every 1 hour` in `config.xml`), or export to a folder before each clear, or drop task 15
from the chain.

## 2. ⚪ ~1,208 `SPP OOS` + ~1,142 `WFM` XAUUSD strategies lost — CLOSED, accepted

Investigated 2026-09-02. Indexed every `.sqx` on the machine by the SHA-256 of its inner
`strategy_Portfolio.xml` (see `sqx/inspect/index_sqx.py`): **17,754 files → 13,288 unique
strategies**, 5 unreadable.

The lost strategies are **not recoverable**. Every archived XAUUSD copy on disk dates from
Dec 2025, Apr 2026 or Jun 2026 — nothing from the Jul–Sep window when the lost ones were generated.
They existed only in the live databank. The `2026-09-02_1953` snapshot was taken *after* the 14:12
loss; `~/Desktop/SQX.zip` is a June install backup containing 32 example strategies.

Owner's decision: accept the loss and regenerate. **Do not spend more time on recovery.**

Still on disk if ever wanted as seed material (unique, not in the master project):

| symbol | in master | elsewhere | main sources |
|---|---|---|---|
| XAUUSD | 461 | 5,746 | `~/Desktop/user` (June tree) 5,189 · `~/Desktop/StrategiesWFM/XAUUSD` 458 · `~/Desktop/WorkSQX` 148 |
| USDJPY | 409 | 592 | June tree 1,429 copies · WorkSQX 34 · Banquillo 21 |
| AUDJPY | 2,348 | 22 | June tree 12 · Banquillo 12 · WorkSQX 10 |

Two pools were undocumented in `CLAUDE.md`: `~/Desktop/WorkSQX` (635 `.sqx`) and
`~/Desktop/AddonsSQX` (68). Both are now covered by the indexer.

## 3. 🟡 `Infinox_SP500ft_H4_HighPrecision` never loads — repair built, waiting on SQX

`project.cfx` holds 4 files but `config.xml` declares 8 active tasks. A larger
`project_backup.cfx` (306 KB, 2025-10-13) sits beside it.

**Confirmed 2026-09-03 (🔬):** the running master's own project list returns **14** projects while
`user/projects/` holds **15** directories. The missing one is exactly
`Infinox_SP500ft_H4_HighPrecision` — SQX silently skips it at load rather than reporting an error.

**Cause (🔬):** `config.xml` references 8 task files; five — `Retest-Task4/6/8/9/10.xml` — are absent
from the live archive, and the backup holds exactly those five. The GUI cannot resolve a declared
task, so it drops the project. `sqx/inspect/project_health.py` scans every project for this in one
pass; it is still the only broken one.

**The repair OPEN.md first proposed was wrong (🔬 2026-09-04).** Swapping `project.cfx` for
`project_backup.cfx` wholesale would regress three things, found by diffing the archives member by
member:

| what | live archive (keep) | backup (would overwrite) |
|---|---|---|
| project name | `Infinox_SP500ft_H4_HighPrecision` | `Infinox - SP500ft - H4 (High Precision)` — spaces break the HTTP API, hard rule 6 |
| databanks | 10 registered | also registers `OOS`, since removed |
| `Retest-Task2.xml` | input `Results` | input `Complete Data Uncorrelated` |

**The repair, built and verified 2026-09-04:** `sqx/repair/graft_tasks.py` keeps every live member
and copies in only the five absent ones. Rehearsed on a copy in the scratchpad: the result is a valid
9-member archive, nothing still missing, the underscore name kept, and every databank the five
grafted tasks name (`SPP`, `WFM LaCity`, `MC Trades`) already registered in the live `config.xml`.

**What remains — needs the master GUI closed.** The tool reads `/proc` and refuses to write while any
process runs out of the install; it currently exits on that guard. When the lifecycle lane is free:

```bash
python3 -m sqx.repair.graft_tasks Infinox_SP500ft_H4_HighPrecision           # dry run
python3 -m sqx.repair.graft_tasks Infinox_SP500ft_H4_HighPrecision --apply   # then reopen SQX
```

It backs the old archive up to `AlgoData/backups/projects/` first. Confirm afterwards that the
master's project list returns 15.

## 4. 🟡 Projects are older than the app — measured, restamping is GUI work

🔬 Measured across all 16 projects 2026-09-04 with `sqx/inspect/project_health.py`. The newest
stamp any project carries is **144.2953**, and only the four the current install has saved carry it —
`Builder`, `Optimizer`, `Retester`, `PortfolioComposer`. The other twelve are older:

| version | projects |
|---|---|
| 142.2399 | AUDJPY, EURJPY_H1, EURUSD, GBPJPY_H1, Infinox_SP500ft_H4_HighPrecision, SP500_H1, USDJPY, XAUUSD, XAUUSD_Breakout_H1 |
| 142.2396 | CADJPY_H1, USDCHF |
| 140.2166 | PortfolioMaster |

🤔 The install's own build is not written to any file this project could find — `internal/updates/
updates.db` is empty and no version string sits in the binaries. It is inferred from the newest
project stamp, which is sound because SQX restamps a project to its own build every time it saves it.

**That is also the fix, and it is not code:** a project is restamped by being opened and saved in the
GUI. Nothing here can do it, and nothing so far shows the drift causing a failure — the detector now
reports it every day so a regression would surface.

## 5. ⚪ Mojibake Windows path in task configs — decoded, closed as dead metadata

🔬 Decoded 2026-09-04. It is **seven** rounds of UTF-8-read-as-CP1252, not one or two, and it reads:

```
C:\Users\Rubén Martínez\OneDrive\Escritorio\FILTROS\Build strategies.cfx
```

Two corrections to the original note. It is **not in the Build task** — it is `<Project
templateFile=>` in `config.xml`, one occurrence per project, recording the `.cfx` a project was
imported from. And it is **not a strategy template**: it points at a `.cfx`, while the template that
matters is `<StrategyType templateFile=>` inside the Build task (issue 9). Nothing resolves it —
it is a Windows path on a Linux box, on 11 of 16 projects, always the same string.

**Closed.** Repairing it means rewriting eleven `project.cfx` archives offline, under the same
GUI-closed constraint as issue 3, for a field nothing reads. `project_health.py` now decodes and
prints any such field, so the value is legible on demand and no longer costs anyone a puzzle.

## 6. 🟢 SQX logs pruned to 14 days — archived

🔬 Confirmed and fixed 2026-09-04. `sqx/export/archive_logs.py` copies both installs' logs to
`AlgoData/logs/<install>/` as `.gz`, skipping anything already archived and unchanged, and leaves a
`manifest.json`. First full archive taken the same day: **58 files, 4.4 GB → 102 MB**, master back to
2026-06-13 and worker to 2026-09-02.

Why it needed streaming: one day's log is not small. `log_2026_08_18.log` — the day the databank loss
in issue 1 was recorded — is **4.66 GB** on its own, and compresses to 105 MB. It was inside SQX's
14-day window by five days.

It is safe while the GUI is up: it reads files and drives no instance.

**Scheduled 2026-09-04**, daily at 08:00, as the machine's only crontab entry. Updated the same day
when the layout refactor moved invocation to `python3 -m`:

```cron
0 8 * * * cd /home/sergioguslw/Desktop/AlgoProject && /usr/bin/python3 -m sqx.export.archive_logs \
          >> /home/sergioguslw/Desktop/AlgoData/logs/cron.log 2>&1
```

Verified under a bare `env -i` shell from `$HOME`, which is how cron will run it. Daily against a
14-day window leaves ample margin. Cost measured: **0.07 s** once everything is archived, and a normal
day adds 4–120 KB compressed (17 days totalled 394 KB). The 4.66 GB day was an anomaly.

`tools/daily_audit.py` is deliberately **not** scheduled. It renders all 16 projects, so if it reads
a `project.cfx` while SQX is rewriting it on save or exit it reports a spurious "fails to render" —
harmless, but noise in a report nobody asked for. Run it with `/audit`.

**Note (auditor, 2026-09-04 afternoon):** "4.4 GB → 102 MB" above is the size of the *compressed
copy* the archiver writes to `AlgoData/logs/`. `archive_logs.py` never deletes the source, so
`~/Desktop/SQX/user/log` on the live master is still **4.4 GB** (`log_2026_08_18.log` alone is
4.66 GB, uncompressed, still on disk 17 days after the date it logged — SQX's claimed 14-day prune
does not appear to be happening). Not urgent: 439 GB free on the disk. Flagging only because the
prose above could be read as "the master's log directory shrank," which it has not.

## 7. 🟢 `core.sqxfile` has a golden test

Done 2026-09-04: `tests/test_sqxfile.py` against `tests/fixtures/strategy.sqx`, wired into
`tools/daily_audit.py` next to the `.cfx` one. It pins the identity hash, the symbol and feed, all 28
parameters, and a census of the rule tree — the census is what catches an XML change the flat fields
would miss. Verified by mutation: lower-casing the feed in `core/sqxfile.py` makes it fail, and it
passes again once reverted.

**The premise that blocked this was wrong.** A `.sqx` is not "about 6 MB". Measured over the 15,971
on the master: min **28 KB**, median 226 KB, p90 870 KB, max 15.4 MB. Size tracks `orders.bin` and the
daily equity curve — how much *result* a strategy carries — not its complexity. The fixture is a real
28 KB strategy from `USDCHF/FinalOOS`, the same order as the 2.4 KB `optimizer.cfx` already
committed, and it still exercises everything the parser reads. `.gitignore` keeps `*.sqx` excluded
and makes `tests/fixtures/` the single exception.

## 8. 🟡 Migrated analyses are parked, not converted — partly done

`archive/studies/` held eight scripts from the previous project. They were written against the old
data layout, so reusing one means rewriting it over `core/` and the data root.

**Converted 2026-09-04:** the IS→OOS predictor study is now `tasks/analysis/` plus
`tasks/reports/is_oos.py`. It is a rewrite, not a port — the old `is_oos_analysis.py` would crash on
the current export, because its hard-coded `PAIRED` list names columns this view does not have. The
new code derives the pairs from the header, deduplicates nothing (this export is one databank, so the
cross-databank duplicate trap does not apply) and adds a Benjamini-Hochberg correction the old study
lacked. The interactive panel is a fresh `panel.html`, not the old `scatter_page.html`.

**Still parked:** `atr_stop.py`, `atr_stop_study.py`, `scan_strategies.py`, `validate_trades.py`,
`plots.py`. `plots_is_oos.py` and `scatter_page.py` are superseded in purpose but kept, because the
new panel draws to canvas and produces no static PNG figures — if a report ever needs those, the
matplotlib styling in `plots_is_oos.py` is the starting point.

`scan_strategies.py` is the one worth converting next: it reads exit configuration straight out of
each `.sqx` with no SQX process, which is how the "two structurally different populations in one
databank" trap gets detected before anything is pooled.

## 9. 🟡 Nine projects ARE ignoring their strategy templates — confirmed, fix is the owner's call

🔬 Measured 2026-09-03: **AUDJPY, CADJPY_H1, EURJPY_H1, EURUSD, GBPJPY_H1, SP500_H1, USDCHF, USDJPY
and XAUUSD** all declare `<StrategyType type="simple">` in their Build task while also naming a real
`templateFile`. Only `XAUUSD_Breakout_H1` declares `type="template"`.

**🔬 Confirmed against real built strategies 2026-09-04. It is no longer an inference: the template
is not applied.** `sqx/inspect/template_check.py` settles it, read-only.

Method: take the blocks a template *fixes* — every `Item` under its `Rules` with `categoryType` of
`indicator`, `simpleRules`, `priceValue` or `priceRange`, **skipping the subtree of any
`randomBlock`**, because those are the holes the builder is supposed to fill. Then open strategies
the project actually wrote and look for that signature.

**0 of 642 strategies from built databanks carry it**, over 8 projects and 30 built databanks,
25 sampled per databank, seed 0:

| project | template | block it fixes | carrying |
|---|---|---|---|
| XAUUSD | `DoubleVortexLong_Template.sqx` | `Vortex` | 0 / 75 |
| AUDJPY | `DoubleROCLong_Template.sqx` | `ROCAboveLevel` | 0 / 70 |
| EURUSD | `DoubleROCLong_Template.sqx` | `ROCAboveLevel` | 0 / 160 |
| USDJPY | `DoubleROCLong_Template.sqx` | `ROCAboveLevel` | 0 / 75 |
| GBPJPY_H1 | `AroonLong_Template.sqx` | `AroonCrossesAbove` | 0 / 260 |
| USDCHF | `CCIPercShort_Template.sqx` | `CCI` | 0 / 2 |

Every strategy uses a different random indicator instead — `UlcerIndex`, `Fractal`, `TrueRange`,
`StdDevLower` — which is what generic generation looks like.

**Positive control**, so this is not a blind check: of 53 strategies sampled from `Existing portfolio`
databanks, **2 do carry the block** (SP500_H1 `HurstExponent`, EURJPY_H1 `BBWidthRatio`). Those hold
strategies built elsewhere and imported, so they say nothing about these builders — they only prove
the detector fires when the block is there.

⚠️ **Two of the nine this method cannot settle, and neither is evidence against the finding.**
CADJPY_H1's `AcceleratorEMALong_Template.sqx` is made of nothing but `RandomCondition` blocks, so it
fixes no block to look for. XAUUSD_Breakout_H1 — the only `type="template"` project, and the natural
control group — has no strategies on disk at all.

**Owner's decision, 2026-09-04: do not change any of them.** Whether a project builds generically or
from a template is his call, not a defect to repair. No project's config is to be touched unless he
names that project — now hard rule 3. So this issue stays 🟡 as a *recorded fact about the install*,
not as work waiting to be done:

> The nine projects listed above build generic strategies. Their `templateFile` is inert. Anything
> read out of their databanks was **not** generated from the template its project names.

That matters when interpreting those populations — `tasks/` analysis over XAUUSD/OOS is analysis of
generic strategies, whatever `DoubleVortexLong_Template.sqx` implies. Rerun `template_check.py` after
any deliberate change to confirm the new setting took.



## 10. 🔴 The pipeline maps count disabled tasks as live — issue 1's table is overstated

🔬 Found 2026-09-04 by the auditor. `sqx/inspect/project_map.py` never reads a task's `active`
attribute: `databank_flow()` records reads/writes/clears for every task, and `tldr()` walks every
`GoToTask`, whether or not SQX will run it. `core/cfx.py:51` already exposes `active` correctly — the
map generator simply does not use it. Same class of mistake as `use="false"` on a condition
(`knowhow/05`), one level up.

Recomputed honouring `active`, across all 15 renderable projects:

| project | unconditional loop actually active? | at-risk databanks reported → real |
|---|---|---|
| AUDJPY | yes, task 19 | 8 → 8 |
| XAUUSD | yes, task 16 | 7 → 7 |
| SP500_H1 | yes, task 18 | 6 → 6 |
| GBPJPY_H1 | yes, task 5 (task 20 is off) | 3 → **1**, `OOS` only |
| USDJPY | **no** — tasks 6, 11, 19 all off | 8 → 8 |
| USDCHF | **no** — task 22 off; 4 and 7 conditional | 8 → 8 |
| EURUSD | **no** — tasks 6, 11, 19 all off | 8 → **2**: `OOS`, `Retest Markets - Family` |
| CADJPY_H1 | **no** — task 19 off | 7 → **6** |
| EURJPY_H1 | **no** — task 18 off | 7 → 7 |

**Four projects loop forever, not nine, and three at-risk counts are inflated.** The error is in the
safe direction — it over-warns — but the 🔬 claim in `knowhow/02` that "every project on this install
has that shape" is wrong as written, and issue 1's mitigation would be aimed partly at clear tasks
that are already disabled.

**Fix:** filter on `active` in `databank_flow()` and `tldr()`. The per-project pipeline maps this
issue was written against are retired pending a redesigned format (below); once that format lands,
regenerate for all 15 projects and rewrite issue 1's table and the `knowhow/02` bullet. The
`terminal` list is affected too — a databank cleared only by a disabled task is currently excluded
from it.

**Related:** issue 1's table covers 6 projects because only 6 maps existed when it was written; there
are now 15 projects to map. `CADJPY_H1`, `EURJPY_H1` and `USDCHF` belong in it, and all three clear a
`WFM` databank while auto-sync is on, so "SP500 H1 clears its `WFM` outright" reads as unique when
four projects do it.

## 11. 🔴 `XAUUSD_Breakout_H1` depends on the worker's template directory

🔬 Found 2026-09-04. The project is registered on the **master** and is the only one declaring
`<StrategyType type="template">`, but all five Build tasks name templates under
`~/Desktop/SQX_w1/user/settings/StrategyTemplates/breakout_xau/` — the **worker's** install. The
master's `StrategyTemplates/` holds no `breakout_xau/`:

```
master : highest_breakout.sqx, highest_breakout_template_daily_filter.sqx, SQ3/SQ4 examples
worker : the same, plus breakout_xau/  (5 templates)
```

It works today only because both installs share one filesystem. `bin/clone-sqx-worker.sh` refuses to
run while the worker exists, so re-cloning means deleting `~/Desktop/SQX_w1` — which would silently
break the master project's five build tasks. It also contradicts `knowhow/03`'s own rule that
`templateFile` resolves against the *target* install and templates must be copied there first.

This project is also the natural control group for issue 9, so keeping it working matters.

**Fix, when the authoring lane is free:** copy `breakout_xau/` into
`~/Desktop/SQX/user/settings/StrategyTemplates/` and repoint the five fields through the worker's
`-project` API. **Until then, do not delete the worker.**

## 12. 🟠 Results cited in `knowhow/` cannot be reproduced from the current data root

🔬 Found 2026-09-04. Every quantitative claim in `knowhow/06-locations.md` and
`knowhow/07-practices.md` — the 231-strategy corpus, the ~129/~11 population split, the ATR-stop PF
figures — comes from the previous project's export. `~/Desktop/AlgoData/` holds **36** strategies'
trades. The generating scripts are parked in `archive/studies/` against the old data layout
(issue 8), so nothing cited can be re-run, checked or challenged today, and both current manifests
say `code_version: "migrated from AlgoProject_Old, pre-git"` rather than naming a commit.

**Fix:** either re-export the corpus with a proper manifest, or mark the affected bullets "from the
old project, not reproducible here", so nobody builds on them assuming they can.

## 13. 🟠 Two analyses state conclusions their samples do not support

🔬 Found 2026-09-04, reading `knowhow/` against `archive/studies/`.

- **ATR-stop study.** `knowhow/07` quotes PF 2.09 at 0.5×ATR. That figure is **in-sample**: the pool
  was selected by SQX search over 2008–2017 and `atr_stop_study.py` restricts to 2008–2017. The
  reported N is the argmax over an 11-point grid (`N_GRID = 0.5…3.0 step 0.25`) and it lands on the
  grid edge — a selected maximum, with no out-of-sample confirmation and no multiple-testing
  statement, on strategies that were themselves produced by search. Only the *relative* degradation
  under slippage is defensible, and that rests on a single slippage value (`SLIP_REF = 0.25`), not a
  curve. The script's own CAVEATS block still says "Slippage on the stop fill is not modelled", which
  its code contradicts.
- **Two-population split.** `knowhow/06` claims "~129 bar-cap + ~11 signal-exit" of 231 — that is
  140, leaving **91 strategies (39%) unclassified**, with the classification threshold unstated. The
  median-MAE comparison (1.37 vs 0.95 ×ATR) rests on **n=11**. The denominator is the raw 231, which
  `knowhow/04` says contains **45 byte-identical trade lists**, so the proportions violate
  `tasks/CLAUDE.md`'s own first trap; and the pool mixes retest windows (46 of 231 cover only
  2018–2023). It carries a 🔬 tag.

**Fix:** restate the ATR lesson as the slippage delta only, and retag the population split 🤔 with its
threshold, denominator and window — or redo it on deduplicated trade lists over one window.

## 14. ⚪ The per-project pipeline maps are retired, format undecided

The 15 per-project pipeline maps under `docs/` were deleted in the layout refactor (2026-09-04): they
were hand-triggered, drifted from `project.cfx` between runs, and issue 10 found their generator has
a real bug. `dump_project.py` is unchanged and is still the source — run it on demand
(`sqx/inspect/dump_project.py <PROJECT>`) instead of reading a stale file in `docs/`.
`tools/daily_audit.py` already runs it that way, to `/dev/null`, purely as a health check (it raises
on a corrupted project archive). A persisted, regenerable format may return later; not designed yet.

## 16. 🟠 The trade-dedup gap now spans four live reports

Found by the auditor 2026-09-04 (afternoon pass). The unmanifested `raw/XAUUSD/OOS/2026-09-03/` this
issue originally named is gone as of 2026-09-11 — resolved, whether by cleanup or by being superseded
is not recorded.

`metrics/XAUUSD/OOS/metrics.csv` (10,000 rows) is read by three reports: `tasks/reports/is_oos.py`,
`tasks/reports/filters.py` and `tasks/reports/compare.py`. None deduplicate on the exported trade
list before computing a correlation, a bootstrap interval or a BH-corrected p-value — the exact trap
`tasks/CLAUDE.md` names first ("45 of 231 strategies had byte-identical trades under different
hashes"). Inner-XML identity hashing across all 10,000 `.sqx` on disk shows 0 duplicates, which is
reassuring but is precisely the check that trap warns not to trust, since the known duplicates in the
old corpus had *different* hashes and identical trades.

**Widened again 2026-09-11:** `tasks/reports/decay.py` (new, reads the `OOS` databank's `.sqx` files
directly rather than `metrics.csv`) reports "834 estrategias → 4 supervivientes" and argues 4-out-of-
834 survivors "es aproximadamente lo que produce el azar" — a multiplicity argument whose denominator
(834) is itself unchecked for duplicate strategies. If a meaningful fraction of the 834 are the same
trade list under a different `.sqx` hash, both the survival count and the "looks like chance" framing
shift. `decay.py`'s own manual page already discloses the *search*-multiplicity gap ("no corrige por
el número de intentos") but not this one.

**Fix:** export trades for a sample of `XAUUSD/OOS` and check for byte-identical lists before
trusting any of the four reports' p-values, intervals or survivor counts — or add one sentence to
each report naming this as an open assumption, the way `filters.py`'s own report already
names its other assumptions.

## 17. 🟠 Every strategy that already exists carries the OLD `Param Count`

Opened 2026-09-06, when the column was rewritten to stop counting `MagicNumber`, the four signal
variables and the `Shift` parameters (all 1286 of them have the value 1). See `knowhow/08-columns.md`.

A custom column's value is **stored in the strategy's own `settings.xml`** when its result is
computed, and `compute()` is never called again — not on export, not on load. Proven by exporting
`XAUUSD/SPP OOS` with `compute()` replaced by `return 99.0`: the 165 exported values did not move.
There is no `-databank` verb that recalculates.

So the corrected column applies **only to results computed from now on** — a new build, a retest, an
optimisation. Consequences, all live:

- Every `metrics.csv` under `~/Desktop/AlgoData/metrics/` carries the old, inflated count, and so do
  the panel, the filter sweeps and `replication.md`. Any filter or conclusion phrased on
  `Param Count` is phrased on ~8 units of noise per strategy.
- Once the owner rebuilds, one databank can hold strategies counted both ways with nothing in the
  CSV to distinguish them.

**Fix:** either recompute the corpus by retesting it in the GUI (owner's call — it is his project),
or mirror the same count in Python from `strategy_Portfolio.xml` and join it into the exports, which
needs no SQX at all and would also make the metric testable. Not built: it is a new command and would
ship with its manual page.

## 18. 🟠 `EdgeDecayRatio` / `EdgeDecayFilter` retired — waiting on the GUI to unwire it

Decided 2026-09-06 by the owner, after the metric was measured against all five XAUUSD exports:
four independent defects, the worst of them a net-profit decay term that is a pure 10y-vs-5y calendar
artifact. Evidence and numbers: `knowhow/08-columns.md`, section "EdgeDecayRatio — measured, and
retired".

Nothing has been removed yet. The master GUI was up, and `EdgeDecayFilter` is referenced by a
CustomAnalysis task in **four** projects — `AUDJPY`, `EURUSD`, `USDJPY`, `XAUUSD`. Deleting the
`.java` first would leave those tasks pointing at a missing method, and project config is the
owner's (HARD RULE 3).

Order of operations, once the owner has unwired it in the GUI and closed the master:

1. Owner: remove the `EdgeDecayFilter` CustomAnalysis step from those four projects, and the
   `Edge Ratio Decay` column from the two databank views that carry it — `Modo Sergiogus.vw` and
   `Modo Sergiogus - OOS.vw`, present in **both** installs.
2. Then: move `user/extend/Snippets/SQ/Columns/Databanks/EdgeDecayRatio.java` and
   `user/extend/Snippets/SQ/CustomAnalysis/EdgeDecayFilter.java` to `archive/` from `SQX` **and**
   `SQX_w1` — the two extend trees are separate.
3. The frozen values already inside existing `.sqx` cannot be removed and stay meaningless; they were
   never exported, so no report depends on them.

## 15. ⚪ Layout renamed — `1_sqx/` etc. are now `sqx/` etc. — CLOSED

Renamed 2026-09-04: `1_sqx/` → `sqx/`, `2_tasks/` → `tasks/`, `3_strategies/` → `strategies/`,
`4_portfolio/` → `portfolio/`, `5_mt5/` → `mt5/`. The digit prefix made the folders invalid Python
package names, forcing 12 `sys.path.insert` hacks; every documented command now runs as
`python3 -m package.module` from the repo root instead of by path. Full plan and verification ladder
in `scratch/refactor-plan.md`.

**Everything under `audit/` and `archive/` from before this date keeps the old numbered names on
purpose and is not rewritten** — those are dated records of a tree that, on that date, really was
named that way. `mt5/README.md` lost the `5_` in its own title; it is still a reserved, empty
directory, just now a valid package name for whenever it is built.

## 19. 🔴 Three Monte Carlo thresholds are placeholders

`strategies/monteCarlo/` ships with the thresholds the specification gave, and three of them are
not the owner's decision yet. Measured on the 36 strategies of `XAUUSD/Results` (2026-09-09):

1. **`scoring.survival_dd_pct` = 10% of the account.** Vetoes 21 of 36 on its own. It is a
   statement about **position size** as much as about the strategies — at 1,000 $ of risk on a
   100,000 $ account. It stays a placeholder until the prop-firm rules fix it.
2. **The dead-block veto** — any non-overlapping 24-month block with a negative bootstrap median —
   vetoes 30 of 36. The blocks are real losing periods, so the rule is doing work; but a rule that
   fails five of every six candidates is a threshold question. Alternatives in
   `strategies/monteCarlo/POSSIBLE_IMPROVEMENTS.md` §1.
3. **The Family D sub-score saturates at 0** for every strategy, because it takes the worst of
   three parts and the worst block's 5th-percentile profit factor is almost always below 1. It is
   faithful to the specification and currently carries no information.

Nothing here is a bug and nothing blocks a run: the three live in `config.yaml` and `gates.py`, and
changing one re-decides every strategy without touching code.

---

## Constraints discovered while investigating

- **SQX rewrites every `project.cfx` on save/exit.** All 14 project files were restamped within the
  same second (`14:33:43`, 2026-09-02). Editing a `project.cfx` on disk while the GUI holds that
  project **will be silently overwritten**. Config edits must be made in the GUI, or on disk only
  while SQX is not running.
- `project.cfx` is a plain ZIP: `config.xml` + one `<Type>-Task<N>.xml` per task. Safe to *read*
  at any time.

## 20. 🟡 `.claude/settings.json` gates one destructive repair script but not the other

Found by the auditor 2026-09-11. The broadened permission set added this session allows any
`python3:*` command without asking, then carves `sqx.curate.apply_verdict` (moves strategies between
databanks) back out into `ask` — appropriately, it rewrites a live databank. `sqx.repair.graft_tasks`
does the same class of thing to a project archive (issue 3) and takes the same `--apply` flag, but
has no matching `ask`/`deny` entry, so it now runs under the blanket `python3:*` allow with no
confirmation prompt. It still refuses to write while the master GUI is up (its own `/proc` guard), so
this is not a path to silent corruption today, but the two scripts are the same shape of risk and
only one is gated.

**Fix:** add `Bash(python3 -m sqx.repair.graft_tasks:*)` to `ask` alongside `apply_verdict`, or gate
on `--apply` generally.

---

## 21. 🟡 `bin/sqx-worker.sh` keeps half the project off Windows

Opened 2026-09-12 while making the project cloneable. Everything that drives StrategyQuant X —
`core/worker.py`, `core/exportdrv.py`, `sqx/export/`, `sqx/curate/apply_verdict.py` — shells out to
`bin/sqx-worker.sh`, which needs `rsync`, `ss`, `md5sum`, `curl`, `setsid` and `stat -c`;
`apply_verdict.py` also uses `pgrep` and the bare `sqcli` name, where Windows ships `sqcli.bat`.
The analysis half is pure Python over exported CSVs and runs anywhere, so the working split today is
**export on Linux, analyse on either**, and `core.worker.require_posix()` makes the boundary fail
with one clear sentence instead of a `FileNotFoundError` on a `.sh`.

The script also hardcodes `MASTER` and `WORKER` as absolute paths, duplicating `config/machine.yaml`.
`tools/checks.py` does not catch it because the rule only scans `.py`.

**Fix, if it is ever wanted:** port it to `core/workerctl.py` — `socket.connect_ex` for the port
check instead of `ss`, `shutil.copy2` instead of `rsync`, `hashlib` instead of `md5sum`,
`urllib.request` instead of `curl`, `subprocess.Popen` with `CREATE_NEW_PROCESS_GROUP` /
`start_new_session` instead of `setsid`, and the paths read from `core/paths.py`. That removes the
split and the duplicated paths in one change. Not done: the owner only needs the analysis half on
Windows today.
