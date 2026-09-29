# Closed OPEN.md issues (archive)

This file holds every OPEN.md issue that was closed (heading marked ⚪, 🟢 or ✅), moved out
verbatim on 2026-09-29 so the always-scanned `OPEN.md` stays small. Issue numbers are unchanged,
so a citation like "OPEN.md §26" still resolves here. See `OPEN.md`'s own index for the full
open-and-closed table and the status legend.

---

## 1. ⚪ Databanks shrink between sessions — CAUSE FOUND

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

**Closed 2026-09-29.** Owner, 2026-09-29: the master's projects are left as they are, so their clear-plus-auto-sync chains are not touched. Moot for builder-made projects: `keep()` strips every task but Build/Retest, so they carry no ClearDatabanks (verified on an archived workflow project).

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


## 3. ⚪ `Infinox_SP500ft_H4_HighPrecision` never loads — WON'T FIX, owner's decision 2026-09-21

> **The owner withdrew this from the plan on 2026-09-21** ("olvídate de ese proyecto del SP500";
> "quita de la ejecución del plan ese punto"). The repair is written and dry-run verified, and is
> **not to be run**. Everything below stands as a recorded fact about the install, not as work.
>
> **Two consequences that outlive the decision, and both bite other work:**
> - **The hourly `Project ... does not exist.` keeps being written.** `bin/sqx-log-prune.sh` caps the
>   disk, it does not stop the cause. Anything tailing the master's log (the progress monitor, lane
>   P0) **must** filter `ProgressEngine` at source — now a requirement, not an optimisation.
> - **The master's project list will always be 14 against 15 directories.** That gap is this, not a
>   new bug. Do not re-diagnose it.


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

**The repair was built and verified 2026-09-04, then removed as dead code 2026-09-26** (the owner's
"not to be run" is permanent, not a pause — a tool nobody may run is not worth keeping around to go
stale). `sqx/repair/graft_tasks.py` kept every live member and copied in only the five absent ones.
Rehearsed on a copy in the scratchpad: the result was a valid 9-member archive, nothing still
missing, the underscore name kept, and every databank the five grafted tasks name (`SPP`,
`WFM LaCity`, `MC Trades`) already registered in the live `config.xml`. The reasoning that would
have to be rebuilt is above (why graft and not restore); the tool read `/proc` and refused to write
while any process ran out of the install, backed the old archive up to `AlgoData/backups/projects/`
first, and its verification was: confirm the master's project list returns 15.


## 4. ⚪ Projects are older than the app — measured, restamping is GUI work

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

**Closed 2026-09-29.** Owner, 2026-09-29: the master's projects stay as they are — he no longer uses the master — and are not to be used as the reference for new projects. No restamping. The daily detector may keep reporting the drift; it is not a finding.

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

**Scheduled 2026-09-04**, daily at 08:00, as the machine's only crontab entry; moved to 04:00 on
2026-09-25 by the owner. Updated the same day
when the layout refactor moved invocation to `python3 -m`:

```cron
0 4 * * * cd /home/sergioguslw/Desktop/AlgoProject && /usr/bin/python3 -m sqx.export.archive_logs \
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

**2026-09-23:** the live master no longer holds `log_2026_08_18.log` (its biggest file is now
`log_2026_09_20.log`, 53 MB), and the archived `.gz` was replaced by
`log_2026_08_18.condensed.log.gz` (36 KB) — what it was is in `knowhow/eng/log-retention.md`, log
retention. `AlgoData/logs/` went from 105 MB to 11 MB.


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


## 8. ⚪ Migrated analyses from the old project — CLOSED 2026-09-26

`archive/` was deleted on 2026-09-26 (owner). Its eight scripts were written against the old data
layout and could not run. Two had been rewritten: `is_oos_analysis.py` became
`studies/screening/isOos/` and `atr_stop*.py` became `studies/closing/atrCalculator/` (step 24). The
rest (`scan_strategies.py`, `validate_trades.py`, the plots) are in git history before that date;
`scan_strategies.py` read exit configuration straight out of each `.sqx`, the idea worth reusing if
the two-populations trap ever needs detecting again.


## 9. ⚪ Nine projects ARE ignoring their strategy templates — confirmed, fix is the owner's call

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

**Update 2026-09-21 — XAUUSD no longer matches the row above.** Read off the live `project.cfx`
while freezing the donor copy (`AlgoData/projectsBackup/XAUUSD_base_2026-09-21/`), its Build task now
declares `<StrategyType type="template">` with
`templateFile=…/AddonsSQX/Templates/TemplatesClaude/StructuralBreakFilters_EntryOnly.sqx` — neither
the `type="simple"` nor the `DoubleVortexLong_Template.sqx` measured on 2026-09-03. The owner changed
it; per hard rule 3 that is a decision, not a defect. Recorded only because the consequence is
factual: **strategies already sitting in XAUUSD's databanks were generated under the old setting**,
so the "generic strategies" reading still holds for them and stops holding for anything built from
now on. `template_check.py` against a databank built after this date is what would settle the new
one. The other eight rows are unverified since 2026-09-04 and may have moved the same way.

**Closed 2026-09-29.** Owner's decision of 2026-09-04 stands (change none of the nine); `sqx/inspect/template_check.py` keeps reporting. Nothing pending.

## 10. 🟢 The pipeline maps count disabled tasks as live — issue 1's table is overstated

🔬 Found 2026-09-04 by the auditor. `sqx/inspect/project_map.py` never reads a task's `active`
attribute: `databank_flow()` records reads/writes/clears for every task, and `tldr()` walks every
`GoToTask`, whether or not SQX will run it. `core/cfx.py:51` already exposes `active` correctly — the
map generator simply does not use it. Same class of mistake as `use="false"` on a condition
(`knowhow/conditions/`), one level up.

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
safe direction — it over-warns — but the 🔬 claim in `knowhow/databanks/sync-only-touches-loaded.md` that "every project on this install
has that shape" is wrong as written, and issue 1's mitigation would be aimed partly at clear tasks
that are already disabled.

**Fix:** filter on `active` in `databank_flow()` and `tldr()`. The per-project pipeline maps this
issue was written against are retired pending a redesigned format (below); once that format lands,
regenerate for all 15 projects and rewrite issue 1's table and the `knowhow/databanks/sync-only-touches-loaded.md` bullet. The
`terminal` list is affected too — a databank cleared only by a disabled task is currently excluded
from it.

**Related:** issue 1's table covers 6 projects because only 6 maps existed when it was written; there
are now 15 projects to map. `CADJPY_H1`, `EURJPY_H1` and `USDCHF` belong in it, and all three clear a
`WFM` databank while auto-sync is on, so "SP500 H1 clears its `WFM` outright" reads as unique when
four projects do it.

**Closed 2026-09-29.** `sqx/inspect/project_map.py` honours `active` in `databank_flow()`, `tldr()` and `task_order()` (`is_active()`, core.cfx convention); test `tests/test_project_map.py`. Regenerated: loops live only in XAUUSD (task 17), AUDJPY (19), SP500_H1 (18), GBPJPY_H1 (5).

## 11. ⚪ `XAUUSD_Breakout_H1` depends on the worker's template directory

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
break the master project's five build tasks. It also contradicts `knowhow/sqx-drive/`'s own rule that
`templateFile` resolves against the *target* install and templates must be copied there first.

This project is also the natural control group for issue 9, so keeping it working matters.

**Fix, when the authoring lane is free:** copy `breakout_xau/` into
`~/Desktop/SQX/user/settings/StrategyTemplates/` and repoint the five fields through the worker's
`-project` API. **Until then, do not delete the worker.**

**Closed 2026-09-29.** Owner, 2026-09-29: deleted. `python3 -m sqx.projects.retire XAUUSD_Breakout_H1 --role master --yes` with the master closed; archive `AlgoData/projects/retired/SQX/XAUUSD_Breakout_H1-2026-09-29.tar.gz`. `SQX_w1/.../StrategyTemplates/breakout_xau/` kept, now referenced by nothing.

## 12. ⚪ Results cited in `knowhow/` cannot be reproduced from the current data root

🔬 Found 2026-09-04. Every quantitative claim in `knowhow/locations/xauusd-corpus.md` and
`knowhow/research/research-lessons.md` — the 231-strategy corpus, the ~129/~11 population split, the ATR-stop PF
figures — comes from the previous project's export. `~/Desktop/AlgoData/` holds **36** strategies'
trades. The generating scripts were in `archive/studies/`, deleted 2026-09-26 (issue 8), so nothing cited can be re-run, checked or challenged today, and both current manifests
say `code_version: "migrated from AlgoProject_Old, pre-git"` rather than naming a commit. The old
project itself was deleted on 2026-09-26, so those figures can no longer be traced to their source.

**Fix:** either re-export the corpus with a proper manifest, or mark the affected bullets "from the
old project, not reproducible here", so nobody builds on them assuming they can.

**Closed 2026-09-29.** Labelled: `knowhow/locations/xauusd-corpus.md` and `knowhow/research/research-lessons.md` now say their figures come from the old project and cannot be reproduced here. No re-export.

## 13. 🟢 Two analyses state conclusions their samples do not support

🔬 Found 2026-09-04, reading `knowhow/` against `archive/studies/` (deleted 2026-09-26, in git history).

- **ATR-stop study.** `knowhow/research/research-lessons.md` quotes PF 2.09 at 0.5×ATR. That figure is **in-sample**: the pool
  was selected by SQX search over 2008–2017 and `atr_stop_study.py` restricts to 2008–2017. The
  reported N is the argmax over an 11-point grid (`N_GRID = 0.5…3.0 step 0.25`) and it lands on the
  grid edge — a selected maximum, with no out-of-sample confirmation and no multiple-testing
  statement, on strategies that were themselves produced by search. Only the *relative* degradation
  under slippage is defensible, and that rests on a single slippage value (`SLIP_REF = 0.25`), not a
  curve. The script's own CAVEATS block still says "Slippage on the stop fill is not modelled", which
  its code contradicts.
- **Two-population split.** `knowhow/locations/xauusd-corpus.md` claims "~129 bar-cap + ~11 signal-exit" of 231 — that is
  140, leaving **91 strategies (39%) unclassified**, with the classification threshold unstated. The
  median-MAE comparison (1.37 vs 0.95 ×ATR) rests on **n=11**. The denominator is the raw 231, which
  `knowhow/export/what-a-project-stores.md` says contains **45 byte-identical trade lists**, so the proportions violate
  `studies/CLAUDE.md`'s own first trap; and the pool mixes retest windows (46 of 231 cover only
  2018–2023). It carries a 🔬 tag.

**Fix:** restate the ATR lesson as the slippage delta only, and retag the population split 🤔 with its
threshold, denominator and window — or redo it on deduplicated trade lists over one window.

**Closed 2026-09-29.** Both conclusions restated in `knowhow/research/research-lessons.md` and `knowhow/locations/xauusd-corpus.md` (retagged 🤔, denominators stated).

## 14. ⚪ The per-project pipeline maps are retired, format undecided

The 15 per-project pipeline maps under `docs/` were deleted in the layout refactor (2026-09-04): they
were hand-triggered, drifted from `project.cfx` between runs, and issue 10 found their generator has
a real bug. `dump_project.py` is unchanged and is still the source — run it on demand
(`sqx/inspect/dump_project.py <PROJECT>`) instead of reading a stale file in `docs/`.
`tools/daily_audit.py` already runs it that way, to `/dev/null`, purely as a health check (it raises
on a corrupted project archive). A persisted, regenerable format may return later; not designed yet.


## 15. ⚪ Layout renamed — `1_sqx/` etc. are now `sqx/` etc. — CLOSED

Renamed 2026-09-04: `1_sqx/` → `sqx/`, `2_tasks/` → `tasks/`, `3_strategies/` → `strategies/`,
`4_portfolio/` → `portfolio/`, `5_mt5/` → `mt5/`. The digit prefix made the folders invalid Python
package names, forcing 12 `sys.path.insert` hacks; every documented command now runs as
`python3 -m package.module` from the repo root instead of by path. Full plan and verification ladder
in `scratch/refactor-plan.md`.

**Everything under `audit/` from before this date keeps the old numbered names on
purpose and is not rewritten** — those are dated records of a tree that, on that date, really was
named that way. `mt5/README.md` lost the `5_` in its own title; it is still a reserved, empty
directory, just now a valid package name for whenever it is built.


## 16. 🟢 The trade-dedup gap now spans four live reports

Found by the auditor 2026-09-04 (afternoon pass). The unmanifested `raw/XAUUSD/OOS/2026-09-03/` this
issue originally named is gone as of 2026-09-11 — resolved, whether by cleanup or by being superseded
is not recorded.

`metrics/XAUUSD/OOS/metrics.csv` (10,000 rows) is read by three reports: `studies/screening/isOos/report.py`,
`studies/screening/filters/report.py` and `studies/screening/replication/report.py`. None deduplicate on the exported trade
list before computing a correlation, a bootstrap interval or a BH-corrected p-value — the exact trap
`studies/CLAUDE.md` names first ("45 of 231 strategies had byte-identical trades under different
hashes"). Inner-XML identity hashing across all 10,000 `.sqx` on disk shows 0 duplicates, which is
reassuring but is precisely the check that trap warns not to trust, since the known duplicates in the
old corpus had *different* hashes and identical trades.

**Widened again 2026-09-11:** `studies/screening/decay/report.py` (new, reads the `OOS` databank's `.sqx` files
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

**Closed 2026-09-29.** `studies/screening/{isOos,filters,replication,decay}` now drop duplicates before any statistic (`studies/screening/analysis/metrics.deduplicated`, `core/surface/dedupe.{curve,trade}_duplicates`) and print the count; `XAUUSD/OOS`: 52 of 10,000 dropped.

## 17. 🟢 Every strategy that already exists carries the OLD `Param Count`

Opened 2026-09-06, when the column was rewritten to stop counting `MagicNumber`, the four signal
variables and the `Shift` parameters (all 1286 of them have the value 1). See `knowhow/columns/param-count.md`.

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

**Closed 2026-09-29.** `core.sqxfile.param_count()` recounts from `strategy_Portfolio.xml`; `core/sqxview.frame()` overwrites `Param Count (IS)` and adds `Param Count source`. Corrected on the next `export_metrics`.

## 18. ⚪ `EdgeDecayRatio` / `EdgeDecayFilter` retired — waiting on the GUI to unwire it

Decided 2026-09-06 by the owner, after the metric was measured against all five XAUUSD exports:
four independent defects, the worst of them a net-profit decay term that is a pure 10y-vs-5y calendar
artifact. Evidence and numbers: `knowhow/columns/edge-decay-retired.md`, section "EdgeDecayRatio — measured, and
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

**Closed 2026-09-29.** Owner, 2026-09-29: he no longer uses the master, so unwiring `EdgeDecayFilter` from its four projects in the GUI will not happen. The retired `.java` files stay where they are; nothing reads them.

## 20. 🟢 `.claude/settings.json` gates one destructive repair script but not the other — moot, tool removed

Found by the auditor 2026-09-11. `sqx.repair.graft_tasks` took the same `--apply` flag as
`sqx.curate.apply_verdict` but had no matching `ask`/`deny` entry, so it ran under the blanket
`python3:*` allow with no confirmation prompt while `apply_verdict` was carved back out into `ask`.

**Resolved 2026-09-26 by removing the asymmetry's cause**, not by adding the entry: `graft_tasks.py`
was deleted along with the rest of `sqx/repair/` (issue 3, "not to be run" is permanent).

⚠️ **Found while closing this out, and worth a separate look**: today's `.claude/settings.json` has
`"defaultMode": "bypassPermissions"` and an empty `"ask": []` — so `apply_verdict` is not actually
gated either anymore, on this machine's current settings. The asymmetry this issue named is gone, but
not because anything got gated; nothing is. Not investigated further here — outside what this pass
was asked to do.

---


## 21. ⚪ `bin/sqx-worker.sh` keeps half the project off Windows

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

**2026-09-28 (plan 24, F0 + F13): the window's half closed.** The owner answered Q2: the window is
used on Linux only, so nothing of `ui/` is ported. What stays is a guard: `/api/health` carries
`sqx.installs`, and on a machine without any install the window opens read-only (banner, the load
bar's ↻ disabled with its reason — `ui/desktop/shell.py` `guard`, F0). «Continuar workflow» (F7)
refuses too, through its preflight. The worker script's own port to Windows is still open, as
above.

**Closed 2026-09-29.** Owner, 2026-09-29: he does not expect to run this script on Windows. Not ported; `bin/sqx-worker.sh` (with `bin/sqx-lock.sh`) stays the one implementation.

## 23. 🟢 The XAUUSD robustness protocol is half built

**Where the plan lives:** `docs/AgentPDFs/WORKFLOW.md` (the protocol dossier of 2026-09-21 was
retired on 2026-09-26, its status table long stale). The WORKFLOW's step table is authoritative; this entry only says that the work exists and is unfinished, so it surfaces in the
daily audit.

Built (2026-09-21): `core/surface/` with its property test, `studies/breakage/spp/`,
`studies/optimisation/wfm/`, and the disk budget plus provisional costs in `perf/disk/` and
`assets/XAUUSD.yaml`. Three manual pages, and the findings in `knowhow/sqx-format/` and
`knowhow/export/`.

Built 2026-09-21, later the same day: **`sqx/variants/` design, fabrication and manifest** —
contract C1 in, `.sqx` batch and contract C2 out, with `tests/test_variants.py` and
`docs/manual/09-optimizacion.pdf` (cap. 18-variantes). Verified on `Strategy 17.9.39`: 5,000 tuples designed, 3 fabricated
and read back clean. **The batch has not been loaded into SQX and no variant has been retested** —
that is W3 and it stays blocked.

Not built: `sqx/variants/` **execution and collection** (`views.py`, `run.py`, `collect.py`),
`studies/optimisation/wfc/` with its PBO, `pipeline/`, the multi-market study, and all six
skills.

**Built 2026-09-22: the CSCV / PBO** (`studies/optimisation/wfc/` gained `inputs/panel.py`,
`measure/rules.py`, `measure/cscv.py`, `verdict/summary.py`, `verdict/trials.py`, `verdict/cost.py`,
`render/figures.py` and the `pbo.py` command), fed by a new
harvest stage `sqx/variants/equity.py` that reads every retested variant's daily curve straight out
of the custodian's `.sqx`. Two new pipeline rows, `equity` and `cscv`; `tests/test_cscv.py`;
`docs/manual/09-optimizacion.pdf` (cap. 25-cscv). Measured on `Strategy 17.9.39`, 479 usable variants: **PBO 30 % choosing
the in-sample maximum against 4 % choosing the plateau centre**, and the in-sample maximum landed in
the 0.2nd out-of-sample percentile.

**Settled 2026-09-23** (owner, on `POSSIBLE_IMPROVEMENTS.md` §1, §2, §3 and §8): weekly periods
stay; the score has to be a rate per period, so `cscv.score` now takes `sharpe` or `sortino` and
never Ret/DD; the default is **twelve blocks, 924 partitions**, López de Prado's own number, with
`pbo.py --blocks N` to override it per run; and the open last period keeps being dropped. The move
from 252 to 924 partitions costs 6 s → 14 s and moved the `argmax` PBO from 41 % to 30 %, well
inside the 0.21 null spread — same reading, and neither figure survives a decimal. §4 to §7 stay
open on purpose until there is a fully tested strategy to rule on them with.

⚠️ **Contract C4 (trades per variant) still does not exist**, and this did not build it. The CSCV
needs returns per period, which the daily curve gives for 1.5 s per batch against ~90 min to export
the trades. Anything that needs MAE, MFE or exit types per variant still has no source.

Three decisions `sqx/variants/` took under stated assumptions, all cheap to revisit:

- **The file shape defaults to `no_profile`** (98.7 KB, 505 MB for 5,000). Whether SQX loads the
  13.7 KB five-member form, and whether the databank dedupes on the inherited `<Fingerprint>`, are
  still unmeasured; all three shapes are implemented and `sqx/variants/config.yaml` picks one.
- **A frozen parameter's range for the coverage stratum is reconstructed**, ±30 % and 0..6 for a
  shift, the way SQX builds its own permutation ranges. The brief gives a value and no span, and
  coverage has to vary it or it only restates the freezing decision.
- **Contract C2 gained one column the protocol's table does not list**, `canary_expect_same_as`.
  An inert-pair canary has no absolute expectation — it must equal the origin row — and without it
  the pairs are unusable at collection time. Null everywhere else. Needs the owner's nod.

Three things block it, and only the last is technical:

1. ~~**The SQX installation topology.**~~ 🟢 **SETTLED 2026-09-21: three installs per machine** —
   master + conductor (W1, 5060) + custodian (W2, 5070), on both PCs. Heaps, core caps and the
   reasoning are in `knowhow/sqx-drive/install-ports-and-heap.md` and `knowhow/perf/ram-budget.md`; the execution tasks
   were lane S of the execution plan of 2026-09-21 (retired 2026-09-26, in git history). **`sqx/variants/` design is
   unblocked**; execution additionally waits for lane P's path work and for W2 to exist.
   ⚠️ `docs/SETUP-NEW-MACHINE.md` §2 still says "two is the working minimum" and is now stale —
   task P1 updates it.
2. **`bin/sqx-worker.sh` is bash, and the platform must run on several Linux machines.** That
   promotes the port to Python from "decide early" to a requirement. Cheapest moment is whenever
   `sqx/variants/` is built, since that layer is being touched anyway. ⚠️ Related debt found the
   same day: `bin/sqx-worker.sh` and `bin/clone-sqx-worker.sh` carry this machine's paths hard-coded
   and `checks.py` does not see them, because it only scans `.py`.
3. ~~The holdout pre-registration~~ — declined by the owner 2026-09-26 (issue 24).

Also pending the owner: the WFC verdict thresholds are PROPOSED, not approved; and the costs in
`assets/XAUUSD.yaml` are SQX defaults, not agreed Infinox figures, so every cost-bearing result
produced before he replaces them carries that caveat.

**Closed 2026-09-29.** Owner, 2026-09-29: file shape `no_profile` is the default (`sqx/variants/config.yaml`), the ±30 % coverage stratum is final, `canary_expect_same_as` is an approved column.

## 24. ⚪ The holdout pre-registration — CLOSED 2026-09-26, the owner declined it

The unsigned scaffolding `docs/preregistro/holdout-XAUUSD-2026-09-21.md` was deleted on 2026-09-26.
Owner: *«yo me controlo a la hora de mirar»*. What protects the last untouched window is the
WORKFLOW's `oos2` reservation, enforced by `ledger.gate` and `assets/_policy.yaml`; thresholds live
in `ledger/thresholds.yaml` with who set them and when. The file is in git history.


## 25. 🟢 The authoring chain is proven headless end to end — issue 9's positive control

**No narrative section was ever written for this issue** — it existed only as a status-table row in the old preamble, preserved here verbatim during the 2026-09-29 OPEN.md cleanup:

> new: the authoring chain is proven headless end to end; `OPEN.md` issue 9 now has its positive control.

## 26. 🟢 `PercentageBased` is charged ONCE per trade — settled 2026-09-27

🔬 Re-measured trade by trade on the same harvest (`XAU_ISOOS_ejemplo`, `PercentageBased 0.001` on
both tasks): of 45,488 same-date XAUUSD trades, **every one that does not cross the 23:00 rollover
matches a single charge `(pct/100) × size × openPrice × pointValue` to the cent, and none matches
two**. The 2026-09-26 fit (k = 1.87, «charged twice») kept 1,566 trades that cross 23:00 on the same
date and carry swap (18–75 $/lot); a least-squares k absorbed it. `_classes.yaml`'s formula was right.
Consequence: a `%` in a `no_forex` asset file is the round-turn cost, and the «SIN VERIFICAR» in
`XAUUSD.yaml` / `XAGUSD.yaml` `why` can go (the owner's files). `studies/readings/edgeCost` no longer
warns about it. Card: `knowhow/costs/commission-methods.md`. Still unreconciled the same way: the
older «$16 round turn under `SizeBased 8`».


## 30. ✅ `sqx.data.update` ran end to end on 2026-09-25

`python3 -m sqx.data.update --apply` drives `-data action=update` on the master — the CLI form of
the GUI's "Update all" — then proves no `.sqx` was lost and refreshes `assets/_policy.yaml`.

**Run on 2026-09-25, master GUI closed, owner's order:** the no-symbol form updated **all 67
configured symbols** in 16 min (19:42→19:58 UTC), exit 0. Rule 1 held: 7,546 `.sqx` before and
after (full copy taken first in `AlgoData/snapshots/2026-09-25-master-antes-update-data`). The
seventeen assets' ranges moved from `2026-09-22` to `2026-09-25` (BRENT to `2026-09-24`). Log kept
at `AlgoData/backups/data-update/2026-09-25T194240Z.log`.

**Left open:** the weekly run keeps hitting HTTP 429 (rate limit) on the same feeds — as of the
2026-09-27 log, `MSFT_DukasM1_ICMarkets` failed on four dates (2026.09.18, 20, 21, 23) and
`HK50_DukasTick_Infinox` on one (2026.09.25). `.sqx` count held (rule 1) both times checked. The
next run fetches the missing dates; nothing to fix in the code unless it starts costing a project
that actually uses MSFT or HK50.

**Scheduled since 2026-09-25:** `bin/weekly-data-update.sh`, Saturdays 03:00 from cron — full copy
of `user/projects` first (last three kept), then the update. Not guarded: a worker **started**
during the ~16 min copies half-written H2 databases, since `sqx-worker.sh` does not know the update
is running.


## 31. ⚪ Revisión completa del proyecto — 2026-09-22 — CERRADO 2026-09-26

> Cerrado: su fallo principal (`ran` heredando el arnés del Retester) desapareció con la regla dura
> 10 y `sqx.projects.stage`; lo que sigue vivo tiene entrada propia (§32, el candado del custodio).
> El documento `revision-proyecto-2026-09-22.md` se borró; está en el historial de git.

Revisión en modo revisor pedida por el dueño: fallos, mejoras, optimizaciones de tiempo, memoria y
tokens, y decisiones pendientes. Estaba entera en el documento de la revisión (borrado, en el historial de git);
aquí solo lo que bloquea la siguiente corrida larga, todo verificado en ficheros reales:

- **`ran` no construye su arnés** (`sqx/variants/execute.py`): hereda el que dejó `spp_oos`, y hoy
  `SQX_w2/Retester` está en estado SPP (2008–2017 sola, `OptProfileSysParamPermutation` exhaustivo
  y `SequentialOptimization` encendidos). Lanzar la cadena con la receta actual retestearía las
  variantes con ese arnés, sin error.
- **`spp_export`** exporta el databank de entrada (`Results`) después de `spp_oos`, sobreescribe
  `raw/<P>/<D>/<hoy>/spp/` por madre y no deja el `strategies/` que `inputs.source` espera.
- **IC del WFC** con `n = 1001` sobre variantes con correlación mediana 0,80 (21 clústeres según el
  propio módulo). `no_fiable` e `indeciso` no están sostenidos.
- **Custodio sin candado**, `start` sin `stop` previo, `run()` sin timeout, carga sin verificar.
- **Reanudación rota al cambiar de día** (`{day}` = hoy) y `mothers()` lee un export viejo.
- 5.000 variantes × 2 mercados ≈ 50 GB de JVM contra `-Xmx48g`.
- **20 commits sin push y ~70 ficheros sin commitear**, incluido `studies/readings/monkey/` y `assets/`.

Orden de arreglo y las once decisiones del dueño: §7 y §8 del documento.


## 32. 🟢 El custodio no tiene candado de propietario

📓 2026-09-23. Cinco sesiones de Claude paralelas en la máquina (`ListAgents`). Una hacía un
benchmark en `SQX_w2` (arrancar, cargar, correr, **parar**, cambiar `coreUsage`) mientras otra
bisecaba costes en el mismo custodio. Siete `stop` mataron corridas ajenas; los proyectos de ambas
arrancaron sobre instancias de la otra; un tercer arranque murió con `Database may be already in
use`. Timeline completa en `knowhow/perf/smt-in-sqx-retest.md`, «Lo que salió mal: dos sesiones sobre el
custodio a la vez».

Es el §2.D de la revisión del 2026-09-22 (retirada, en el historial de git) visto en vivo. Arreglo propuesto:
`bin/sqx-worker.sh start` escribe `user/log/OWNER` (sesión, PID, hora); `stop` de otra sesión se
niega salvo `--force`; `check` lo muestra. Y todo script que use un worker pasa por `awake()`, nunca
por un start/stop propio.

Daño colateral verificado: la carrera de dos `sqcli` a las 07:31:41 dejó `SQX_w2/internal/AppSettings.txt`
en **5050** (los puertos del maestro), y W2 arrancó como maestro hasta que algoproject-07 lo restauró a
07:47. Mecanismo en `knowhow/sqx-drive/running-a-task-headless.md`. El arreglo del candado debe incluir que `start`
compruebe el puerto en `AppSettings.txt` antes de lanzar.

**Closed 2026-09-29.** Owner lock `<install>/user/log/OWNER` (`bin/sqx-lock.sh`, used by `bin/sqx-worker.sh` and so by every Python path): `stop` from another holder refuses unless `--force`, stale locks self-clear, `start` still refuses a port drift. `knowhow/sqx-drive/owner-lock.md`, `tests/test_worker_lock.py`.

## 33. 🟢 `pipeline.cleanup` refuses the one finished mother: `metrics.parquet` no longer matches its hash

📓 2026-09-23. `python3 -m pipeline.cleanup --project XAUUSD --strategy "Strategy 17.9.39"` exits
with `el export ya no coincide con su hash: metrics.parquet`. The `collected` stage hashed the file
at 09:40:04 on 2026-09-22 and something rewrote it afterwards — the `wfc` and `verdict` stages ran
in the following second, so one of them, or a later re-run, writes `metrics.parquet` after collect
recorded it. Until that is found the ledger's "removable" (`sqx/`, 2,000 files, 32 MB) cannot be
swept, and the guarantee the sweep rests on is broken for every mother that follows. Nothing was
forced. Find which stage rewrites the file and either hash after it or make it write elsewhere.

**Closed 2026-09-29.** Not a rewrite: `sqx.variants.collect` never hashed its own files. It now records `bytes`+`sha256` and a data-root-relative path (`collect.fingerprint`). Batches collected before today still lack the hash and must be re-collected before `pipeline.cleanup`. `knowhow/eng/collect-never-hashed-its-own-files.md`.

## 34. 🟢 `sqx.projects.builder` installs the donor clone before it refuses

🔬 2026-09-23. Building a USDJPY project from the frozen XAUUSD donor failed at the session gate:

```
ninguna tarea de este proyecto define la sesión USDJPY_ftmo. Hay que darla de alta en SQX,
o clonar de un donante que la lleve — no se inventan horarios de mercado.
```

The refusal is correct (see `knowhow/costs/sessions-per-asset.md`, "A session cannot be borrowed"). **What is wrong
is that `user/projects/USDJPY_crossmarket/project.cfx` was already on disk in the custodian when it
printed that** — and it was an untouched XAUUSD clone: `XAUUSD_DukasM1_Infinox`, `defaultSpread`
10.0, `MarketOpenSession XAUUSD_ftmo`, and the additional-markets cross-check still pointing at
XAGUSD and BRENT. Nothing of USDJPY had been applied. A project named for one asset that builds
another, with that asset's costs, is unattributable the moment anyone runs it — exactly what hard
rule 10 exists to prevent.

Removed by hand from `SQX_w2` on 2026-09-23; a copy of the aborted `.cfx` is in that session's
scratchpad, not in the repo.

**The fix**: run the doctrine blockers — sessions included — against the donor **before** writing
anything into an install, or write to a temporary path and move it into `user/projects/` only once
every gate has passed. Until then, a failed `builder` run leaves a booby trap and the operator has
to know to delete it.

**Closed 2026-09-29.** `builder.build()` stages the `.cfx` in a temp dir, runs every gate there and moves it into `user/projects/` only when all pass; a failed run leaves nothing. `tests/test_builder_feedswap.py`.

## 35. 🟢 `sqx.projects.builder --symbol` does not change the market — it cannot author for a non-donor asset

🔬 2026-09-23, building the first non-gold project. `--symbol USDJPY` produced a project whose three
tasks contain **no occurrence of `USDJPY_DukasM1_the5ers` at all**:

| what | value in the built project |
|---|---|
| main chart | `XAUUSD_DukasM1_Infinox`, M30 |
| spread on the build task | 10.0 — gold's |
| `<Resources><Symbols>` | `XAUUSD_DukasM1_Infinox`, plus a stray `AUDJPY_DarwTick_the5ers` |
| session | `USDJPY_ftmo` ✅ — the only thing that took |
| additional-markets cross-check | the 9 FX pairs ✅, retesting **gold** |

**The cause.** `sqx.projects.setups.set_costs` picks the Setups to rewrite by matching
`<Chart symbol="{data['sqx_symbol']}"`, and `configure` patches dates on `<Symbol name="{feed}"`.
Neither element exists in a donor frozen for a different asset, so **both rewrite zero elements,
silently**, and the donor's own market survives untouched. `--symbol` really drives only the
doctrine, the window, the session and the costs — and the costs are applied by feed match, so they
land nowhere. Nothing caught it because every project built until today came from the XAUUSD donor
*for* XAUUSD, where the match always succeeds.

**It reports success.** The run printed the doctrine line, the segments, and
`⚠️ PROVISIONAL: spread, commission, slippage_is, …`, which reads as though those costs had been
applied to something. `configure` does return a per-task Setup count and `build()` passes it through
as `setups`, but the human-readable output never prints it — a `0` there would have said everything.

Removed from `SQX_w2` by hand; the mongrel `.cfx` is in that session's scratchpad, not the repo.

**What it blocks.** No asset but XAUUSD can be authored today: the USDJPY cross-market programme, the
28-pair FX test, and every `structural` market.

**The fix, and why it is not a one-liner.** Switching market means rewriting the main chart's
`symbol`, the `<Resources><Symbols>` entry and the `<InstrumentInfo instrument=…>` key together — and
`setups.py` already warns that editing `InstrumentInfo` is what produces *"Project has unresolved
resources"*. Two routes:

1. **A donor per asset**, frozen from a master project that already trades it. Cheap and safe; costs
   one snapshot per asset, and inherits that project's exits and acceptance, so results across assets
   stop being comparable unless the donors agree.
2. **A real feed-swap step** in `builder` that rewrites the three places at once, verified by loading
   the project in SQX. Keeps one donor and one doctrine for every asset — the reason to want it — but
   needs the unresolved-resources failure understood first.

Until one exists, `builder` should **refuse** when the donor carries no chart on the target asset's
feed, instead of reporting success. That refusal is the smallest useful change and should land first.

**Closed 2026-09-29.** The feed swap existed (`resources.borrow_symbol`, `doctrine.borrow_session`); added `resources.refuse()` (zero-Setup task, ignored template, or a surviving donor feed → nothing installed) and the per-task `setups` line. USDJPY verified live on the conductor, no unresolved resources. Remaining data gap: no install defines a session for any index CFD, so those still refuse — see #29.

## 36. 🟢 Unit conversions in `no_forex` cost files swing ~5× with the reference price nobody chose

🔬 2026-09-23. The `no_forex` class requires commission as **% of notional** and swap as **% annual**,
while SQX stores `SizeBased` dollars and swap in points. Every such file therefore carries a
conversion, and the conversion needs a price — which is not written down anywhere as a convention.

`XAUUSD.yaml` uses **the last real close**. Following it for the two new metals/energy files gives:

| | at last close | at the tested window's median (oos1) | factor |
|---|---|---|---|
| XAGUSD commission | 0.001776 % (P=90.078) | 0.00863 % (P=18.535) | **4.9×** |
| XAGUSD `swap_long` | −6.35 % annual | −30.9 % annual | **4.9×** |
| BRENT `swap_short` | −9.54 % annual (P=97.235) | −13.5 % annual (P=68.578) | 1.4× |

Silver traded at a median of 18.5 across 2018–2022 and closes at 90 today, so **the last close
understates the cost of the window actually being charged by nearly five times**. The same applies to
`XAUUSD.yaml` itself, whose own file already says the figure "depends on the reference price chosen"
and is `SIN VERIFICAR`.

The three files agree with each other, which is the only reason to keep the last-close convention for
now. **The decision the owner has to make**: reference price = last close, the median of the segment
being charged, or the median of the whole history. It changes cost-bearing results on every `no_forex`
asset, and until it is made, no absolute profitability figure on gold, silver or Brent means much —
relative comparisons between strategies on the *same* asset are unaffected.

Settled 2026-09-27 (issue 26): SQX applies `PercentageBased` once per trade, on the open price.

**Closed 2026-09-29.** Owner, 2026-09-29: reference price = median price of the charged segment (oos1). `studies/data/spread/onboard.py` `_oos1_price`; reproduces this issue's own figures. Applied: XAUUSD commission 0.001778 → 0.004692 %, XAGUSD 0.002516 → 0.008632 %, BRENT swap_long 0.0111 → 0.0157 %, swap_short −9.5373 → −13.5227 %. Manual chapter 24-costes rewritten.

## 37. 🟢 `studies/breakage/mcRetest/` assumes all eight MCR tasks always ran

🔬 2026-09-23, found while writing `sqx/projects/mcretest.py`. The owner's rule is that
`MCR 4 MinDist` is configured **only** when the population trades with stop or limit orders, so on a
market-only population that databank is never written. The Python side does not know that:

- `studies/breakage/mcRetest/ingest.py:99` — `assert found, f"{tasks.DATABANK[task]}: no .sqx found"`, over
  the fixed eight of `tasks.TASKS`. A missing `MCR 4 MinDist` aborts the whole ingest.
- `studies/breakage/mcRetest/inputs/tasks.py`, `METHOD["stress"]` — expects exactly six methods. When the
  population has no pending orders the stress task is written with five, and `verify()` refuses the
  databank for "carrying the wrong methods".
- `studies/breakage/mcRetest/ingest.py` calls `core.paths.databank_dir(project, name)`, whose `install`
  defaults to the **master**. There is no `--role`, so it cannot read a study that ran on a worker —
  and hard rule 3 says the workers are where our runs happen. `sqx/export/export_retest.py` got its
  `--role` on 2026-09-23 (commit 53007d7); this one still needs it.

So today the SQX side and the Python side disagree about what a legal run looks like, and every
market-only study — which is all of them, since `_build.yaml` has `order_types: [EnterAtMarket]` —
hits it at step 14.

🔬 **Ya no es una previsión: medido el 2026-09-23** corriendo el proyecto entero en el custodio
(`SQX_w2/user/projects/XAU_mcr_prueba`, 2 estrategias reales del `OOS` del XAUUSD del maestro,
1.000 simulaciones por tarea). Pasando los `.sqx` producidos por `tasks.verify()`:

| tarea | verify() |
|---|---|
| bar, spread, slippage, params, exits, ohlc | **OK** — 1000/1000 simulaciones, aislamiento correcto |
| mindist | sin databank: `ingest.py:99` abortaría |
| stress | `ran [5 metodos], expected [6]` — le falta `RandomizeMinDistance` |

**The fix** is on the Python side and is a study-level decision, not a patch: a task that could not
exist has to be recorded as absent, with its reason, and the report has to say "seven of eight" in
so many words rather than quietly averaging over what it found. `sqx.projects.mcretest --json`
already emits exactly that, per task, under `dropped`.

**Closed 2026-09-29.** Already fixed in code: `studies/breakage/mcRetest/ingest.py` requires only `bar`,`stress`; `inputs/tasks.py` checks a subset.

## 38. 🟢 Tres divergencias declaradas de los pasos 15, 16.5 y 19 — decisión del dueño

📓 2026-09-23, al escribir `sqx/projects/spp.py`, `sqx/projects/wfm.py` y las skills `/spp`,
`/variants` y `/wfm`. Ninguna es un bug: son tres sitios donde el código sigue lo que hacen las
tareas del maestro y eso **no coincide con la letra** de un fichero de política. Están escritas para
que él decida, no para que la siguiente sesión las "arregle".

1. **La precisión del SPP es `1`, no el `2` de la doctrina.** `_build.yaml` dice
   `precision.default: 2` (un minuto) de la construcción en adelante, y las dos tareas SPP del
   donante corren a `1`. Un SPP son miles de backtests **por estrategia**: a un minuto no termina.
   El catálogo `spp:` lo fija en 1 y lo canta en cada ejecución. Si el dueño quiere el 2, es cambiar
   una línea — y medir antes cuánto tarda una madre real.

2. **`SPP IS` corre sobre `build`.** `_policy.yaml` dice que `build` es «sólo el paso 6, la única
   muestra que el generador ve». Esa frase habla de **selección**; el SPP de IS no selecciona nada
   (las condiciones y los cuatro `Eval*Check` van apagados), sólo vuelve a leer una ventana ya
   gastada, que es lo que significa "in sample" y lo que hacen las tareas del maestro. Si el dueño
   prefiere que el paso 15 no toque `build` en absoluto, se queda sólo el `SPP OOS` y el paso 16
   pierde la mitad de su entrada.

3. **La fábrica de variantes sigue corriendo sobre el `Retester` de serie.**
   `sqx/variants/config.yaml`, `execute.project: Retester`, incumple la regla dura 10. Es anterior a
   la regla. La migración es crear un custom project de una sola tarea Retest
   (`sqx.projects.builder Test_<SIM>_variantes --purpose "..." --tasks Retest --only Retest-Task1.xml`) y poner su nombre
   ahí. No se ha cambiado el default para no romper una cadena que hoy funciona sin que él lo sepa.

**2026-09-29.** Owner, 2026-09-29: (a) SPP precision stays 1, (b) SPP IS stays on `build`. (c) done in code: `sqx.variants.spp` requires `--project` and refuses the stock projects; `pipeline/config.yaml run.spp_project` = `Trade_XAUUSD_variantesSPP`. Left: build that one-Retest-task project once on the custodian (`python3 -m sqx.projects.builder Trade_XAUUSD_variantesSPP --tasks Retest --only Retest-Task1.xml ...`). `knowhow/sqx-drive/spp-harness-needs-its-own-project.md`.

**Closed 2026-09-29.** Owner, 2026-09-29: (a) SPP precision stays 1, (b) SPP IS stays on `build`, (c) no separate harness project. `sqx/variants/harness.write()` finds its task by title (`SPP IS`/`SPP OOS`/`OOS`) inside the mother's own workflow project and `sqx.variants.spp` switches on only that task (`stage.just`); the harness databanks are `SPPRecon_In`/`SPPRecon_Out` (the old `Results` collided with the Build's). `run.spp_project` removed. `tests/test_variants_harness.py`; manual chapter 19-wfc.

## 39. ✅ El WFC en tres tramos — hecho el 2026-09-24

📓 Decisión del dueño: el retest de las variantes son tres tareas de SQX (`build`, `oos1`, `oos2`),
cada una a sus costes y con los mercados adicionales dentro, y la cosecha las une. Hecho de punta a
punta: `sqx/projects/wfc.py` escribe las tareas, `sqx/variants/{legs,execute,equity,united,collect}.py`
las cosechan, y el WFC lee el lote de dos maneras (`split_mode`). Queda una sola cosa viva de esto:

**🟡 Nada de esto se ha corrido todavía sobre un lote de verdad.** Los lectores están probados
contra un databank real del maestro (`XAUUSD/Retest Markets - Family`, 757 estrategias x 3 mercados)
y la aritmética de las uniones está comprobada contra lo que SQX guarda, pero el ciclo entero
—cargar, correr las tres tareas, exportar, cosechar— no. Lo que hay que mirar la primera vez:

1. que `action=start` corra de verdad las tres tareas en cadena y que el contador de `execute.run`
   —que divide el total entre tres— no se quede corto ni largo;
2. que los tres databanks de salida existan en el proyecto (§40), porque SQX ignora en silencio un
   nombre que no declara ningún `<Databank>`;
3. que `unreconciled` devuelva un puñado de variantes y no todas: todas significa que se está
   leyendo el resultado equivocado del `.sqx`.


## 40. ✅ Los databanks del proyecto WFC hay que crearlos a mano — resuelto 2026-09-25

`sqx.projects.wfc` los declara él mismo, y se llaman sin espacios (`WFC_Variants`...): con espacios
la API no puede nombrarlos. Detalle en `knowhow/databanks/no-spaces-in-names.md`. Lo que sigue es la nota original.

### (original)

📓 2026-09-24. `sqx.projects.wfc` apunta las tres tareas a `WFC Variants` (entrada) y a `WFC Build`,
`WFC OOS1` y `WFC OOS2` (salidas), pero **no los crea**: SQX empareja por el nombre exacto e ignora
en silencio un databank que ningún `<Databank>` del `config.xml` declara. Hoy se crean en la GUI del
proyecto custom. Lo natural es que `sqx/projects/databanks.py` sepa añadirlos, que es trabajo de una
sesión y no se ha hecho para no mezclarlo con la autoría de las tareas.



## 41. 🟢 Half the variant budget goes to combinations that barely trade

🔬 Measured 2026-09-24 on `Strategy 17.9.39`'s batch while building `studies/optimisation/cloud/`.
Of the 2,000 fabricated rows in `metrics.parquet`, **1,002 trade fewer than 30 times in sample** —
the trade count is bimodal, with a first quartile of 4 trades and a median of 752. They are not a
tail: they are half the design.

Two costs, and they are different:

- **Budget.** Those slots were fabricated, loaded and retested on the custodian like any other. The
  design's own `n_target` is a cap on *tuples*, and nothing in `sqx/variants/design/` knows that a
  region of the grid produces strategies that do not trade.
- **Inference.** Once they are filtered out — and they have to be, a 4-trade backtest is not a point
  on a performance surface — `DICrossShift1` is left with a single value, so the surface can no
  longer say anything about it. `knowhow/research/trade-filter-parameter-space.md`, "A trade filter is not neutral in
  parameter space".

**Not a bug and not urgent**: the design is doing what it was told, and the reading layer now names
what collapsed instead of quietly fitting around it. What it suggests is a cheap pilot — a few
hundred tuples scored on trade count alone before the full batch is fabricated, so the levels that
produce silence are known before the budget is spent, which is close to what
the 2026-09-22 review (retired, in git history) already proposed for the sampling.

**Whose call:** the owner's, because it changes what a batch contains.

**Closed 2026-09-29.** Pilot before the batch, on by default (`sqx/variants/pilot.py`, `design/pilot.py`): ~300 Sobol tuples retested on the same project; a live level whose median trades < `pilot.min_trades` (30) with support is dropped, recorded in `design.json`/`pilot.json`; `--no-pilot` skips. `tests/test_variants_pilot.py`. Defaults taken from this issue's numbers, not measured.

## 43. 🟢 A retest drops the `<!--variant_id-->` stamp — the file name is the only join key

🔬 Encargo 12, 2026-09-26: the retested `strategy_Portfolio.xml` is the fabricated one minus that
comment. After a run, a variant is found by its file name only. Check that `sqx.variants.collect`
and `equity` never relied on the stamp; `sqx/variants/README.md` failure mode 1 describes it as a
join key and is now inaccurate. Card: `knowhow/sqx-format/writing-a-variant.md`.

**Closed 2026-09-29.** `sqx/variants/README.md` now names the file name as the join key.

## 44. 🟢 The CSCV puts two months of `oos1` P&L on its OOS side — each leg's curve starts early

🔬 Encargo 15, 2026-09-26: each leg's daily curve starts ~2 months before its segment with zero P&L
(warm-up), and `equity.json` `splits`/`windows` record that warm-up start (`splits.oos2 =
2022-11-03`). `engines/variants/panel.split(work, "oos2_only")` returns that date, so `windows()`
puts Nov–Dec 2022 of the **oos1** leg's real P&L on the OOS side of the CSCV's chronological
numbers. It changes computed CSCV/WFC figures, so the fix (split at the segment's own start from
`assets/_policy.yaml`) needs a golden before and after. Card: `knowhow/sqx-format/leg-curve-warmup.md`.

**Closed 2026-09-29.** `engines/variants/panel.split(symbol, comp)` returns the segment's own start from `assets/_policy.yaml` (`core.assetdata.segment_start`); `tests/test_panelsplit.py`. Stored CSCV/WFC figures change on their next run (owner: accepted).

## 45. 🟢 `nulls.seed` no fija nada

new 2026-09-25: `engines/nulls/simulate.py:nulls()` usa `abs(hash(rung))`, y `hash()` de una cadena
está aleatorizado por proceso: dos `studies.screening.gate.report` sobre los mismos ficheros dieron
**227 y 229 supervivientes**. Arreglo de una línea (hash estable) pero **cambia una vez todos los p
almacenados** — decisión del dueño. `knowhow/perf/python-parallelism.md`.

**Closed 2026-09-29.** Owner, 2026-09-29: the monkeys must differ every run. `engines/nulls/config.yaml` `seed: null` → a fresh root from OS entropy per run, recorded in every result/manifest (`nulls_seed`); an explicit `--set nulls.seed=<int>` reproduces a run. `knowhow/eng/nulls-seed-fresh-per-run.md`. Other studies' own fixed seeds untouched.

## 46. ✅ Step 18.5 reads `oos2`, step 23 does not — owner, 2026-09-26

Market surfaces joined `reserved_for` (`assets/_policy.yaml`) and `ledger/gate.py` `STEPS` as
`MarketSurfaces: 18.5`, and read `build`, `oos1` and `oos2` by default. The structural tests (23)
stay on `build` + `oos1`; the gate refuses them `oos2`. The owner trusts his own discipline over a
stricter lock: 18.5 is not added to the blind set that withholds 17/18/19 until all have run.


## 47. ✅ The conditional map has trading sessions — owner's hours, 2026-09-26

Tokyo 9–18, London 8–17, New York 8–17, each local; entries go feed clock → UTC → city clock,
because SQX stamps feeds in the broker's zone (`knowhow/export/feed-clock-timezones.md`). The
on/off switch between sessions and weekdays belongs to the window (`ui/`), which gets all three
views from the study.


## 48. 🟢 Loose ends of the 2026-09-26 batch — each the owner's word, none blocking

- Market surfaces: the call uses the raw rho; `rho_neutral` (each market's exposure × drift
  removed) is shown beside it. Which one should decide is open. Its Fisher interval and J band are
  optimistic because the design clusters variants.
- Edge per cost: no Sharpe-vs-cost-multiplier curve — the MC Retest keeps no daily equity per
  simulation, so it cannot be rebuilt. `min_edge_spreads = 2` and `action = mark` are defaults set by
  the agent at the owner's request that they be parameters.
- The `/oos-gate` skill says the harvest joins "on name"; the gate README and `harvest.py` say identity.
- `engines/nulls/filter.benchmark` needs an observed-value override for path-dependent strategies;
  `studies/readings/structure/` carries its own `subset_null` meanwhile.

**Closed 2026-09-29.** (a) `rho_neutral` decides the market-surface call, raw rho still shown; (b) `min_edge_spreads=2`, `action=mark` final; (c) gate docs: correspondence by name, join on identity; (d) no benchmark override — not needed.

## 49. ✅ Periodic review jobs added — knowhow, dependency map, audit/, docs health — 2026-09-26

Four new cron jobs, asked by the owner: a weekly quality pass over `knowhow/`, plus three more
found by looking for other project parts that age the same way and were not yet on any schedule.

**`bin/weekly-knowhow-review.sh`** — the nightly `documenter` (`bin/nightly-docs.sh`) repairs drift
the daily audit found; it never reads `knowhow/` end to end for what only the prose catches — two
cards answering the same `q:`, a 🔬 tag that oversells its evidence, a card a later one
contradicted without either being rewritten. `tools/checks.py`
(`knowhowmap.bad_cards` / `broken_links` / `stale_indexes`) already enforces card shape
mechanically, so this pass is scoped to the semantic half checks.py cannot see. Runs the
`documenter` agent on Sonnet the same way `nightly-docs.sh` does. **Sundays 05:00.**

**`bin/weekly-docs-health.sh`** — same agent, same day, waits on the knowhow review's lock so the
two never touch OPEN.md at once. Covers what `weekly-knowhow-review.sh` does not: OPEN.md's own
status table against its issues, `docs/SKILLS.md` retirement candidates (reported as a new OPEN.md
issue, never deleted by the agent — the owner's call), `docs/encargos/` against its own "un encargo
cumplido se borra" rule, and a general stale-doc sweep. **Sundays 05:00**, chained after the
knowhow review.

**`docs/DEPENDENCIES.md` regeneration** — `tools/checks.py`'s dependency-map check only ever
flagged staleness, never fixed it (it was stale when this issue was opened); `tools/depmap.py` is
deterministic, so no agent is needed, just a daily run. **Daily 02:40.**

**`bin/audit-prune.sh`** — `audit/` gets two files a day, forever, with no retention job of its
own (unlike SQX's logs, `knowhow/eng/log-retention.md`). Gzips reports older than 60 days in
place; deletes nothing, never touches today's. **Sundays 02:45.**

All four leave their changes uncommitted (the two agent runs) or touch only their own generated
file (the two mechanical ones) — nothing here runs `git add` or `commit`.

Installing the crontab lines hit the classic vixie-cron bug: `crontab <file>` truncates a long
`TMPDIR`-based temp path and fails with a "No such file or directory" that names the wrong file —
worked once the file was copied to a short `/tmp` path first. 🔬 reproduced 2026-09-26,
`knowhow/eng/crontab-long-tmpdir-path.md`.


## 51. 🟢 The study viewer cannot reach cloud, wfc and cscv — they write into the variant batch

The unified window (2026-09-26) reads results only under `reports/<P>/<D>/<day>/<study>/`
(`ui/daemon/results/`). `cloud`, `wfc` and `cscv` write into the mother's batch
(`{strategyPermutations,pipeline}/<P>/<batch>/estudios/`), so `/api/result` and `/api/history`
never find them: the catalogue marks them `source: "batch"` and the page says «aún no conectado».
The runner does start them (one mother, refusing when she has two batches). Needs a batch-keyed
query in `ui/daemon/results/runs.py`; then `notes.absent` needs nothing, the catalogue changes.

**2026-09-27 (plan 24, F3b): half closed.** The new databank panel reaches them:
`ui/daemon/databank/batches.py` reads each mother's `estudios/{cloud,wfc,cscv}.json` and every
`wfc_<composition>.json`, and `GET /api/databank/table` shows them as columns of the row with the
mother's name (a batch carries no identity), sealed with 17-19 while the ledger's door is shut.
Still open: `/api/result` and `/api/history` (the old study page) do not.

**2026-09-28 (plan 24, F13):** the zones that read only `/api/result` for a population (the
matrix and the population's study page) were retired; a mother's cloud, wfc and cscv are read in
Proyecto's databank panel (F3b). Still open, narrower: the study tabs under Estrategia's ficha
(`studypage/`) ask `/api/result` and `/api/history`, so on a mother they still say «aún no
conectado» for those three — the batch-keyed query in `ui/daemon/results/runs.py` is what is left.

**Closed 2026-09-29.** `ui/daemon/results/runs._batch_path` finds `<batch>/estudios/<study>.json` for a mother; cloud, wfc and cscv show on its strategy page.

## 52. 🟢 Every stored crossmarket result reads stale in the window

🔬 2026-09-26: of the 11 `crossmarket/` report folders only 10 cells carry an identity
(`USDJPY_workflow_profiling_v1` 8, `USDJPY_emaCross_H1` 2) and **all 10** are `stale`: the
`config_hash` they signed differs from what `ui/daemon/results/knobs.py` computes for today's
config. Cause not investigated — either the config changed since, or knobs' loader for crossmarket
does not reproduce what `studies/transfer/crossmarket` signs (compare the two hashes on a fresh
run before trusting the ◷ mark on this study). The other 9 folders have no identity column and are
skipped («sin identidad»).

**Identity part, 2026-09-28 (plan 24, E5):** `crossmarket.load` now resolves through
`core.study.identity.resolve` (installs → cosecha → the export's kept `.sqx`) and writes a `note` on
each row it leaves empty. A report whose Retest Markets databank is gone still signs nothing: see §82.
The stale-hash half of this entry is untouched.

**Closed 2026-09-29.** Cause: the population run signs its config with `nulls.draws` replaced by `batch_draws`; the window hashed the raw config. `ui/daemon/results/knobs` signs the population the same way (`crossmarket.inputs.config.population`). `knowhow/eng/population-signs-a-different-config-than-strategy.md`.

## 53. 🟢 `edgeCost`'s verdict.csv has no identity column

`reports/<P>/<D>/<day>/edgeCost/verdict.csv` is `strategy, edge_mean, edge_median, n, verdict`.
Without `identity` the matrix cannot place its rows (199 skipped on `USDJPY_workflow_profiling_v1/
Results`), and `/curate` cannot check that it deletes the strategy that was judged once
`verdict.action: drop` makes edgeCost a gate. Add `identity` as the other studies do.

**Fixed 2026-09-28 (plan 24, E5):** `verdict.csv` is now `strategy, identity, edge_mean, edge_median,
n, verdict`, the identity the harvest's own. The `Test_USDJPY_donchianUpperCrossUp_M30/Results/
2026-09-27` report was signed after the fact from the same harvest it read (numbers untouched).

**Closed 2026-09-29.** Already fixed: `studies/readings/edgeCost/report.py:58` writes `identity`.

## 54. 🟢 A partial re-run (`only`) is not merged beside the stored result — it replaces it — fixed in the window 2026-09-28 (plan 24, F5)

`POST /api/study/run` with `only=<market>` becomes `studies.transfer.crossmarket.report --strategy
S --only <feed>`, which writes `reports/<P>/<D>/<day>/crossmarket/estrategias/<S>.json` holding
that one market — the same file the full run wrote for `S` that day (`--day` is both the export
date and the report folder). The full per-strategy result is overwritten, not merged; the
population JSON and `verdict.csv` still describe the full run. `core/study/CONTRACT.md` §1 names
partial runs; nobody merges them yet. Until then, `↻ solo …` on a day that already holds a full
run loses that strategy's other markets.

**Fixed in the window (F5, 2026-09-28; recorded by F13):** the window no longer calls the study's
`report --only`. `ui/daemon/results/rerun.py` writes the sub-test to
`<study>/parciales/<stamp>_<only>/estrategias/<S>.json` beside the newest full result, `store.load`
attaches it as `partials`, and `desktop/blocks/fuse.merge` swaps only that market on screen, the
stored verdict kept (`knowhow/eng/partial-reruns-beside-stored.md`). Still true from the command
line: `crossmarket.report --strategy S --only F` run by hand overwrites the day's full file.


## 55. 🟢 The custodian pulse shows no progress for runs started outside the window — fixed 2026-09-28 (plan 24, F11)

`/api/pulse` (`ui/daemon/ops/pulse.py`) takes `done/total` from a daemon job's
`PROGRESS <pct> <n> de <N>` line; SQX's own log carries no backtest count. A run launched from a
terminal or another session shows `avance ?` — JVM, CPU and free RAM are still read. Fix: have
`sqx.variants.execute` (and whatever else starts long custodian runs) write its PROGRESS lines to
a file the pulse can find, not only to its own stdout.

**Fixed differently (F11, 2026-09-28):** when no job log carries a count and the custodian's log
says a project runs, `ui/daemon/ops/pulse.py` takes the running **task**'s count from the
worker's status line (`ui/daemon/ops/runs.count` → `progress.state` → `-project action=status`,
the one command the custodian may receive mid-job). «avance de» then reads `estado del custodio ·
<task>`; rate and ETA stay empty, because a task's count over the project's minutes is no rate.
A build has no total, so the line reads `<n> hechos`. What is still missing is a whole-run count
for an external multi-task run; `sqx.variants.execute` writing its PROGRESS lines to a file would
give it, and nobody has needed it yet.

**2026-09-28 (plan 24, F13):** closed as fixed by F11; «En marcha» is the zone that shows it
(Custodio and Generación fused), and `tools/uiwalk.py` opens it with no exception.


## 56. 🟢 The nightly audit and docs agents did not run for 16 days — fixed, running again since the night of 2026-09-26→27

🔬 Found by the 2026-09-27 audit: `AlgoData/logs/nightly-audit.log` and `nightly-docs.log` had
failed every night since 2026-09-11 with "this workspace has not been trusted" followed by (for
docs) "Error: Input must be provided either through stdin or as a prompt argument when using
`--print`". Only `tools/daily_audit.py` (the mechanical half, no model) had actually run — no full
`audit/YYYY-MM-DD.md` was written for any night in between, so `nightly-fix.sh` also had nothing to
act on ("no audit/2026-09-26.md: the audit did not finish; nothing to fix").

**Verified fixed 2026-09-27 (🔬):** both scripts already pass the prompt as a `claude -p` argument
(not stdin, not an empty flag), and last night's run produced real output despite
`hasTrustDialogAccepted` still being `false` in `~/.claude.json` — the trust warning is printed but
no longer fatal. `audit/2026-09-27.md` (6.7 KB, real findings), `audit/2026-09-27-fixes.md` (the
fixer agent, 3.7 KB) and a real documenter run (this same pass's predecessor, which regenerated the
`knowhow/` indexes and added issues #64/#65) all exist with full content, `exit 0` in both logs.
Whatever broke it was fixed by commit `0845d21` (2026-09-26 16:22 UTC, "docs: manual only as PDF,
docs/ pruned, feed-quality decisions, weekly /tmp cleanup"), which touched `bin/nightly-docs.sh`;
not investigated further here since the symptom is gone. `knowhow/sqx-format/INDEX.md`'s staleness
was the visible casualty and was repaired the same night.


## 57. 🟢 Step 10 (`crossmarket`) priced exports on the wrong bars and left out the entry spread — fixed 2026-09-27

On `Test_USDJPY_donchianUpperCrossUp_M30` the report kept 8/8 with `worst_pf` 1.31–1.51 while SQX's own
net P/L gave PF 0.79–1.07. Two causes: `inputs/markets.universe()` priced every export on the timeframe
`_markets.yaml` declares (USDJPY: H1) — an M30 export matched each :30 trade to the bar half an hour
early — and `cost_rate()` was measured from the fill prices, leaving out the offset where SQX puts
spread and slippage. Now the timeframe comes from the export's `manifest.json` and the cost from
`setting()["charged"]`; the same run gives 0/8, returns PF within 0.02 of SQX's, correlation 0.995+.
**Stored step-10 verdicts are wrong wherever the export's timeframe differed from `_markets.yaml`**
(USDJPY at M30, XAUUSD at H1) — rerun those. `_markets.yaml` `timeframe:` is now read by nothing.
`engines/nulls` (the gate's monkey) recovers its cost the same fill-based way but prices real and
random runs alike, so its comparison is fair and only its absolute levels are gross; changing it moves
every stored p (like §45), the owner's call. `knowhow/research/crossmarket-returns-miss-entry-offset.md`.


## 58. 🟢 A strategy's identity changed in place after the MC Retest — fixed 2026-09-27 (owner's call)

After the MC Retest SQX rewrote the databank it read without `autoGenerated="true"` on each
`<variable>`; `core.sqxfile.COSMETIC` stripped only `makeExternal`, so all 8 identities changed and
`/curate` refused the next cut. The owner chose to strip `autoGenerated` too. Pre- and post-MCR copies
of the same strategy now hash alike; on `USDJPY_workflow_profiling_v1` every databank still matches
`Results` as before (WFM excepted, as before: it rewrites parameters). Identities stored before
2026-09-27 for strategies that still carried the attribute use the old formula — no `Trade_` project
exists yet, so nothing needed regenerating. `knowhow/sqx-format/strategy-identity.md`.


## 59. ⚪ MC Retest spread and slippage barely perturb forex at today's provisional costs — measured 2026-09-27

SQX draws the MC spread and slippage on a ~0.1-point grain (one USDJPY tick), not continuously: on
`Test_USDJPY_mcrRanges` spread 0.1–2.0 gave 17 distinct outcomes, 0.1–1.0 gave 8; slippage 0.05–2.0
gave 19, 0.05–0.5 gave 4. The declared 1x–4x (`mc_retest.default_multiples`) of the provisional
USDJPY spread 0.1 / slippage 0.05 spans 0.3 / 0.15 points, so 2 and 1 outcomes: those two axes are
not tested. With a realistic spread (~1 point) 1x–4x would span ~30 steps and work as designed.
**The owner's call**: widen the forex multiples, or wait for the agreed costs. `knowhow/costs/mc-retest-ranges.md`.

**Closed 2026-09-29.** Superseded by #76: every forex pair now carries its own measured MC Retest spread range (0.47–1.98 points) and a slippage span of 0.75–3.33 points, far past the 2-outcome grid this issue measured on the provisional 0.1 spread. `default_multiples` unchanged.

## 60. 🟢 `template_check` no longer checked the owner's condition — fixed 2026-09-27

Since 2026-09-26 the fixed condition sits in a one-item random group, a `randomBlock` the check skipped,
so it signed `MarketPositionIsLong` and passed about the wrong block. `signature()` now adds the only
item of a hole's one-item group, `carried()` counts every block key of a strategy (a drawn block carries
no `categoryType`), and every strategy is opened by default (`-n` still samples). On the custodian's
projects: Donchian 3/3, Keltner 115/115 and 120/120; the only "NOT APPLIED" are step-23 ablations,
which remove the block on purpose.


## 61. 🟢 The parameter cloud could not read `collect`'s panel — fixed 2026-09-27

`cloud/inputs/cloud.py` read `# of trades (IS)` and `config.yaml` `Ret/DD Ratio (IS)`; `collect` writes
`NumberOfTrades (build)` and `ReturnDDRatio (build)`. Renamed both; the three mothers of the M30 run give
the same reading unpatched as they did patched in memory.


## 62. 🟢 `stoploss.graft` needed `key=` to be the first attribute — fixed 2026-09-27

SQX wrote `<Param generated=… gid=… key="#StopLoss.StopLoss#">` in 2 of 3 mothers and step 24 refused
them. The pattern is order-agnostic now; `tests/test_stoploss.py` has the reordered case (fails without
the fix). The same assumption sat in `studies/data/feedQuality/template.py` `EXIT`, which would have
missed a live stop and read the strategy on the wrong column, silently: fixed the same way.


## 63. 🟢 Minor frictions of the 2026-09-26 USDJPY M30 workflow run — fixed 2026-09-27

- `builder` needed `--session-from` for any asset the donor does not trade: `sqx/projects/source.py`
  now picks the newest project on any install that defines both the asset's session and feed (still
  refusing when none does — EURUSD today). Tested with `Test_USDJPY_builderSessionAuto`.
- crossTF `run.blocks` was fixed at `[H1, H4, H12]`: `inputs.blocks()` derives it from the siblings'
  `source_tf` and `_build.yaml` `crosstf.timeframes`; a list is set only for a `--timeframes` task.
- `sqx.templates.registry --set` replaced the whole row: it now updates only the columns named.
- `worker.holding` matched the install path anywhere in a command line (the nightly auditor's prompt):
  only a process whose executable lives in the install counts now.
- The gate stitched IS and OOS at the first day of the retest's curve, which opens ~2 months early:
  the build window lost its last weeks (degradation figures moved in the 3rd decimal, no verdict
  changed). It now joins at the build curve's last day.
- The structure report compared a build rebuild with a stored OOS result: each leg now meets its own
  window only. SQX logged an error loading `scaling.parquet`: the siblings go to `<day>/sqx/` now.
- Left as they are, SQX's own: `synctofiles` at ~6 files/s, and 3 MCR runs that stored 999 of 1,000.


## 64. 🟢 `export_spp.py` never manifests the `strategies/` copies

Found by the 2026-09-27 audit's "exports without a manifest" list, which named only `SPP_IS` and
`SPP_OOS` export roots (never `MCR_*`, `CrossTF`, `WFC_*`, `WFM`, `Results`, `Retest_Markets_-_Family`
in the same runs) — narrow enough to check by hand instead of blaming the checker.

🔬 Verified 2026-09-27 on disk: every `SPP_IS/<date>/` and `SPP_OOS/<date>/` holds two sibling
folders, `spp/` (the profile tables) and `strategies/` (the mother `.sqx` copies, so
`sqx/variants/inputs.py` can resolve them at step 16.5). `sqx/export/export_spp.py` calls
`manifest.write(out, ...)` with `out = export_dir(...) / "spp"` — the manifest lands **inside**
`spp/`, one level deeper than `tools/daily_audit.py`'s `exports_without_manifest()` assumes ("one
manifest at its dated root"). `copy_mothers()` then writes `strategies/` as a *sibling* of `spp/`,
via `out.parent`, and never calls `manifest.write` for it. `strategies/` has no manifest anywhere in
its ancestor chain, so the checker's warning for `SPP_IS`/`SPP_OOS` is correct, not the doubted
blind spot — `manifest_check_blind_spots` does not apply here. `WFM`'s export is not affected: its
tables and the manifest both live inside the same `wfm/` subfolder, so nothing there is uncovered.

**Fix:** either move `manifest.write()` in `export_spp.py` to `out.parent` (covering both `spp/`
and `strategies/` with one manifest naming both), or write a second, smaller manifest inside
`strategies/` recording which project/databank/date the copies came from. Code change — not done
here (Documenter does not touch code).

**Closed 2026-09-29.** Already fixed: `sqx/export/export_spp.py` writes a manifest for both `spp/` and `strategies/`.

## 65. 🟢 `snapshots/` disk budget nearly doubled in one night, `profiling/` pinned at 200 % — resolved 2026-09-27

📓 `AlgoData/logs/disk-nightly.log`, entry 2026-09-27 02:30: `snapshots` had gone from 8.25 GB / 8 GB
(103 %) on 2026-09-26 to 15.02 GB / 8 GB (188 %) on 2026-09-27; `profiling` stayed at 2.00 GB / 1 GB
(200 %), unchanged since at least the 26th. `perf/disk/report.py`'s own duplicate pass named part of
the cause: 925 duplicate groups, 5.6 GB reclaimable, mostly matching project-log pairs between
`snapshots/2026-09-25-master-antes-update-data/` and `snapshots/weekly-data-update-2026-09-26/`.

The owner emptied `snapshots/` by hand on 2026-09-27 13:38 (folder now 4 KB) and `profiling/` fell to
1.2 MB. The 28th's `disk-nightly.log` (02:30) shows neither branch out of budget any more; the 925
duplicate groups disappeared with the folder.


## 66. 🟢 `sqx-worker.sh stop` gave up at 20 s while the JVM was still saving — fixed 2026-09-24

new 2026-09-24: **`sqx-worker.sh stop` volvía a los 20 s diciendo «did not stop»** mientras la JVM
seguía escribiendo databanks, y quien leía después veía 211 de 500 `.sqx`. Ahora espera hasta 5 min
a que el proceso se vaya de verdad. **No se perdió nada**: la sincronización acabó sola.


## 67. 🟢 `pipeline/XAUUSD/Strategy_17-9-39` no longer runs in the CSCV

Its batch predates the per-segment columns: `cscv.report` fails with `KeyError: NetProfit
(build+oos1)`. It is still usable by the parameter cloud. Re-harvest it or retire it; never use a
real batch as a CSCV regression test anyway — every run reads `oos2`
(`knowhow/research/cscv-always-reads-oos2.md`).

**Closed 2026-09-29.** `studies/optimisation/cscv/report.py` refuses a batch without `segments.parquet` or its split's columns with a plain message; `Strategy_17-9-39` stays as it is (re-harvest or retire it).

## 68. 🟢 `stress.simulate` reservaba 816 MB por mercado — troceado 2026-09-25

new 2026-09-25: **`stress.simulate` reservaba 816 MB por mercado** — la matriz de 25.000 corridas
entera, con tres arrays `float64` de valores booleanos. Troceada en lotes de 500: **140 MB**, cifras
idénticas. Sin esto, 96 procesos no caben en 125 GB: un intento llegó a 94,5 GB y otro a 89 GB, y
**el núcleo mató la ventana de VSCode**.


## 69. 🟢 La tarea del paso 10 es una estrategia, y debería ser una estrategia-mercado

new 2026-09-25: en un lote de 96 la mayor lleva 117.612 operaciones y cuesta **453 s ella sola**: es
el suelo de cualquier reparto a partir de 24 procesos, y por eso 96 procesos sólo dan 14,2x. Los 9
mercados son independientes dentro de `analyse_market` — repartir por ahí divide la tarea más larga
por ~9. Toca la forma de `analyse_strategy`, que es la puerta del panel: decisión de diseño.
`docs/manual/03-datos-costes-y-registro.pdf` (cap. 12-rendimiento).

**Closed 2026-09-29.** Already shipped in `cd4503b` (2026-09-26): per-(strategy, market) fan-out, longest first (`core/fanout.py`). Re-measured 2026-09-29: 200 strategies × 9 markets in 135 s, verdicts identical.

## 70. 🟢 El lote del paso 10 no deja ver por dónde va

new 2026-09-25: `pool.map` devuelve en orden y la corrida de 499 estuvo **38 min sin imprimir una
línea**, indistinguible de un cuelgue. Desde fuera tampoco: `py-spy` necesita ptrace y está
bloqueado. Se arregla imprimiendo por orden de terminación.

**Closed 2026-09-29.** Already shipped in `cd4503b`: `core.fanout.run` yields by completion; `many.run` prints PROGRESS per strategy; final table order stays deterministic.

## 72 · 🟢 `crossmarket` already computes the answer to a question it does not ask

**Opened 2026-09-22.** `simulate/metrics.py` computes nine statistics for the real run and every
null run, and the panel prints them side by side. What is missing is the sentence that makes the
spread between them readable:

- `sharpe` is scale-free, so it divides out the very thing that separates a real trade from a
  random one — 🔬 the real ones are **36 % less volatile** (491 $ against 661 $ per trade, skew
  +0.53 against −0.78, kurtosis 6.4 against 27.0). Measured on XAUUSD `OOS1`, the same simulation
  passes **77.4 %** of strategies on `sharpe` and **39.5 %** on `net`. A reader comparing the two
  p-values without that sentence concludes the module contradicts itself.
- `verdict/significance.py`'s MinTRL and the study's own nulls are one axis with two centrings,
  and are presented as two unrelated numbers.
- `stress.py` already computes the breakeven cost multiple, which is what decides whether the
  null's mean is negative at all. Neither number cites the other.

All three are additive — a README section, a tooltip, one extra column. None changes a computed
number. Same reasoning as issue 71: `crossmarket` is finished and this is the owner's call.

**Closed 2026-09-29.** Framing added to the crossmarket panel (Sharpe vs net, MinTRL and the null on one axis, break-even cost) and the «Sharpe de referencia» column. No computed number changed.

## 73. ⚪ Three global `sqx-lab` skills are retirement candidates — owner's call

Found by the 2026-09-27 weekly docs-health pass, reading `docs/SKILLS.md` (regenerated the same
day with `tools/skillmap.py`). The three skills left in `~/.claude/skills/`
(`sqx-custom-block` 6,488 tokens, `sqx-strategy-template` 5,744, `sqx-random-group` 3,022 — a
fourth, `sqx-strategy-project`, is no longer installed there) are generic SQX/AlgoWizard authoring
product: none of them know the owner's defaults, the conductor/custodian split or
`registry.csv`. The risk `SKILLS.md` already names is routing, not spend — a template request can
land in `sqx-strategy-template` instead of this project's own `/strategy-template` and produce a
template that does not follow this house's rules. The only thing from `sqx-lab` actually used today
is its skeletons, and those already live in `tools/sqx-lab/`, so uninstalling the three globals
would lose nothing project-specific.

Not retired here — `docs/SKILLS.md` already says "Decisión pendiente del dueño" and this issue only
gives that pending decision an `OPEN.md` entry, per the weekly docs-health pass's own rule (never
delete a skill unattended, only list candidates for the owner).

**Closed 2026-09-29.** Kept, not retired: the premise is stale. The three globals carry the AlgoProject overlay (`sqx-strategy-template` applies the owner's defaults) and the window's template chat calls them (`ui/daemon/create/author.py`, `sqx/templates/build.py`, `sqx/blocks/install.py`). Uninstalling them would break «Crear la plantilla con Claude».

## 74. 🟢 Steps 23, 24 and 25 export into the same `raw/<P>/WFC_*/<day>/` and overwrite each other

The structural batch (23), the stop grid (24) and its harvest (25) all retest in the WFC legs and export
with `export_retest --databank WFC_Build …`, which writes `raw/<project>/WFC_Build/<today>/`. Run the
same day, each export replaces the previous: on 2026-09-27 the step-23 report could not be rerun,
because its trades had been overwritten by step 24's. A batch should export under its own name (e.g.
`--out <batch>/export`), and `structure.report` / `atrCalculator.report` read from there.

**Closed 2026-09-29.** `core.paths.export_dir(..., batch=)` and `export_retest --batch <tag>`; `structure` and `atrCalculator` read their own tag first and fall back to the flat folder. `knowhow/export/export-retest-batch-tag.md`.

## 75. 🟢 `sqx-worker.sh stop` sent right after `start` is lost

`start` returns once the port answers; the CLI takes ~20 s more. A `stop` in that gap is swallowed and
the script waits 5 minutes before saying `STILL RUNNING` (2026-09-27, conductor). A second `stop`
works. `stop` could wait for "CLI is now ready" in the worker log before sending.

**Closed 2026-09-29.** `bin/sqx-worker.sh stop` waits up to 30 s for `SQX CLI is now ready` before sending `-exit`.

## 77. ⚪ A one-item random group's hole can still drift to a different block

Re-running the USDJPY M30 workflow end to end on 2026-09-27 to verify §57–§63, `template_check`
(fixed by §60) reported **197/200** on a fresh `Results`, not 200/200: 3 strategies —
`Strategy 19.14.48`, `Strategy 19.16.66`, `Strategy 8.25.70` — carry no
`CBlock_CloseCrossesAboveDCUpper` at all. Their `RandomCondition1` slot, the one the template binds
to `donchianUpperCrossUpSignal` (a group holding exactly that one block), resolved instead to an
unrelated native condition (e.g. `AroonCrossesAbove`) with `retries="0"` — not a build-time failure,
not a missing-block case (`sqx.inspect.vocabulary` shows the block installed and pooled on both
workers throughout). §60's fix is not in question: `template_check` correctly flagged the 3 as
`TEMPLATE NOT APPLIED` over the full N=200, which is what it was fixed to do.

The population is generated across many generations (55,908 strategies evaluated for 200 accepted
in this run), so this reads as SQX's own genetic mutation occasionally moving a slot's block choice
outside the group it was seeded from, at roughly 1.5% of the accepted population. `knowhow/authoring/one-item-group-can-drift.md`
has the reproduction. **Not investigated further**: whether this is expected AlgoWizard behavior,
a mutation operator that ignores group membership, or something specific to a one-item group —
the owner's call on whether it is worth a repair or just a rate to watch in `template_check`'s own
output on every build.

**Closed 2026-09-29.** Owner, 2026-09-29: accepted as a rate. `template_check` keeps reporting the ~1.5 % of a population whose one-item group slot drifted; no repair.

## 79. 🟢 SPP marginal profiles read θ₀'s lone level as argmax and spike

2026-09-27, found by encargo 24 E4 (`knowhow/research/spp-origin-level-sampled-once.md`). SQX's SPP
step grid need not contain the original value; on the three USDJPY M30 SPPs it misses
`BBerDeviation1` 2.9 (and `BBerDeviation2` 2.8, `CBlc_ClsCrsDCerInt21` 29 on two of them), so θ₀
(permutation −1) is the only tuple at its level. `model/profile.marginal` aggregates it with the rest:
for those parameters `run.read` reports argmax = original and a width-1 plateau, and the design
brief carries `spike: true` and `argmax_is` = original — an artefact. The new two-parameter surfaces
(`spp/surface.py`) already leave θ₀ out of their cells. Fix: `run.read` passes
`grid[grid.index != export.ORIGINAL]` to `profile.marginal`; it changes design briefs, so it is the
owner's to approve and re-run.

**Closed 2026-09-29.** `studies/breakage/spp/inputs/export.without_original()` shared by `run.read` and `surface`; `tests/test_spp_origin.py`. 43 design briefs regenerated (XAUUSD and USDJPY SPP_IS), each old one kept as `.pre-2026-09-29`; most spikes were the artefact.

## 80. 🟢 Two studies read an old run with today's `_build.yaml` — runs should save their blocks

2026-09-28, found by encargo 24 F9 (`knowhow/eng/studies-reread-build-yaml.md`). `studies/transfer/crossTF`
takes the block order from `crosstf.timeframes` and `studies/readings/structure` each WFC leg's
segment from `wfc.tasks[].segment`, both re-read at analysis time. Since F9 the window can edit both
(Q17), so one change there silently re-labels every past run: crossTF scores cells on another
timeframe's bars, structure files legs under the wrong window. The zone warns beside both values.
Proposal: `sqx.projects.crosstf` writes `blocks.json` (the ordered blocks) next to the project's run
record and the crossTF study reads it before the doctrine; `structure/inputs.py` reads the segments
from the batch's `ran.json`, which `sqx.variants` already writes. The owner decides; until then change
those two values only between runs.

**Closed 2026-09-29.** `sqx/projects/crosstf.py` writes `blocks.json` with the run; crossTF reads it first, structure reads segments from `ran.json`; both warn when they fall back to today's config. `tests/test_run_record.py`.

## 82. ⚪ Crossmarket results of a retired project cannot be archived until the Family databank is re-exported

🔬 2026-09-28 (plan 24, E5). Studies sign identity from the installs, then the newest cosecha that
paired their databank, then what the export kept (`core/study/identity.py`), so edgeCost, spp
(`strategies.csv`), profitShape and monkey (`nulls.csv`) are frozen by `core.archive` after the
project is retired. From 2026-09-28 `sqx/export/export_retest.py` and `export_trades.py` write
`raw/<P>/<D>/<day>/identity.csv` (strategy, identity) from the staged `.sqx` before deleting them
(a few KB; a WFC batch does not keep its `.sqx` three times), so every FUTURE crossmarket run signs.
Exports made before stay unsigned: on `Test_USDJPY_donchianUpperCrossUp_M30`
`core.archive show` still prints «no archivado: Retest_Markets_-_Family/2026-09-27/crossmarket».
**Left: re-export the Family databank (and re-run crossmarket) when the project is rebuilt.**
Guessing `Strategy 10.11.79(1)` → `Strategy 10.11.79` is a name across databanks and is refused.
Still unsigned: a mother's batch studies (`estudios/{cloud,wfc,cscv}.json`).
`→ knowhow/locations/crossmarket-report-signs-no-identity.md`

**2026-09-29.** Going forward fixed: `export_retest`/`export_trades` write `identity.csv` before deleting the staged `.sqx`. The one retired project stays unsigned unless rebuilt.

**Closed 2026-09-29.** Owner, 2026-09-29: the unsigned crossmarket result of the retired project is given up. Future exports sign themselves (`identity.csv` before the staged `.sqx` is deleted).

## 83. 🟢 The window cannot launch a second project on the custodian for 24 h after the first

🔬 2026-09-28, night run from the window. After `+ Nuevo proyecto` created
`Test_XAUUSD_donchianUpperCrossUp_H1`, «▶ Lanzar en SQX», every «▶ SQX» and «Continuar workflow»
refused: «Test_USDJPY_donchianUpperCrossUp_M30 se modificó en SQX_w2 hace 1.0 h: puede ser de otra
sesión» — the owner's own crossmarket run of 21:39. `advance.busy` counts ANY other project touched
in `RECENT_H = 24` h (`ui/daemon/advance/preflight.py`), which is the §32 guard between two steps
of another session; it cannot tell the owner's own project from someone else's. A «Son míos»
button (a claim that lapses when the project is touched again) was written and refused by the
auto-mode classifier as weakening a safety guard, then removed. **The owner's decision**: keep 24 h,
shorten it, add an owner's claim, or a real lock (§32's `user/log/OWNER`).
2026-09-29: the 15-min quiet guard no longer waits on the window's own runs — a job that
releases its worker writes `AlgoData/logs/ui/workers/<role>.released.json`, and a log last
written before that is the window's (owner's choice). The 24-h rule is unchanged.
`→ knowhow/sqx-drive/export-after-every-stop.md`

**Closed 2026-09-29.** Owner, 2026-09-29: one task at a time per worker, but a finished task frees it for any project. The 24 h rule is gone from `advance.busy()`; busy = a live owner lock, the port, or an SQX PID. The 15-min quiet guard stays for a hand-made `stop` (released.json intact).
