# Open Issues

Tracked issues for the AlgoProject / StrategyQuant X pipeline.
Split out of `CLAUDE.md` on 2026-09-02 so the always-loaded instructions stay lean.
Migrated into the rebuilt project on 2026-09-03; paths updated to this tree.

Status: 🔴 open · 🟡 in progress · 🟠 open, owner's call · 🟢 resolved · ✅ done · ⚪ closed / won't fix

**Closed issues (⚪ 🟢 ✅) live in `docs/OPEN-closed.md`, verbatim, numbers preserved** — this
file (2026-09-29 cleanup) keeps only open sections plus the full index below, so a
"what is broken" read no longer pulls in ~33 KB of settled history.

## Index

| # | status | title | where |
|---|---|---|---|
| 1 | 🟡 | Databanks shrink between sessions — CAUSE FOUND | OPEN.md |
| 2 | ⚪ | ~1,208 `SPP OOS` + ~1,142 `WFM` XAUUSD strategies lost — CLOSED, accepted | docs/OPEN-closed.md |
| 3 | ⚪ | `Infinox_SP500ft_H4_HighPrecision` never loads — WON'T FIX, owner's decision... | docs/OPEN-closed.md |
| 4 | 🟡 | Projects are older than the app — measured, restamping is GUI work | OPEN.md |
| 5 | ⚪ | Mojibake Windows path in task configs — decoded, closed as dead metadata | docs/OPEN-closed.md |
| 6 | 🟢 | SQX logs pruned to 14 days — archived | docs/OPEN-closed.md |
| 7 | 🟢 | `core.sqxfile` has a golden test | docs/OPEN-closed.md |
| 8 | ⚪ | Migrated analyses from the old project — CLOSED 2026-09-26 | docs/OPEN-closed.md |
| 9 | 🟡 | Nine projects ARE ignoring their strategy templates — confirmed, fix is the o... | OPEN.md |
| 10 | 🔴 | The pipeline maps count disabled tasks as live — issue 1's table is overstated | OPEN.md |
| 11 | 🔴 | `XAUUSD_Breakout_H1` depends on the worker's template directory | OPEN.md |
| 12 | 🟠 | Results cited in `knowhow/` cannot be reproduced from the current data root | OPEN.md |
| 13 | 🟠 | Two analyses state conclusions their samples do not support | OPEN.md |
| 14 | ⚪ | The per-project pipeline maps are retired, format undecided | docs/OPEN-closed.md |
| 15 | ⚪ | Layout renamed — `1_sqx/` etc. are now `sqx/` etc. — CLOSED | docs/OPEN-closed.md |
| 16 | 🟠 | The trade-dedup gap now spans four live reports | OPEN.md |
| 17 | 🟠 | Every strategy that already exists carries the OLD `Param Count` | OPEN.md |
| 18 | 🟠 | `EdgeDecayRatio` / `EdgeDecayFilter` retired — waiting on the GUI to unwire it | OPEN.md |
| 19 | 🔴 | Three Monte Carlo thresholds are placeholders | OPEN.md |
| 20 | 🟢 | `.claude/settings.json` gates one destructive repair script but not the other... | docs/OPEN-closed.md |
| 21 | 🟡 | `bin/sqx-worker.sh` keeps half the project off Windows | OPEN.md |
| 22 | 🟡 | `studies/transfer/crossmarket` — state of play after the 2026-09-14/15 rebuild | OPEN.md |
| 23 | 🟡 | The XAUUSD robustness protocol is half built | OPEN.md |
| 24 | ⚪ | The holdout pre-registration — CLOSED 2026-09-26, the owner declined it | docs/OPEN-closed.md |
| 25 | 🟢 | The authoring chain is proven headless end to end — issue 9's positive control | docs/OPEN-closed.md |
| 26 | 🟢 | `PercentageBased` is charged ONCE per trade — settled 2026-09-27 | docs/OPEN-closed.md |
| 27 | 🟠 | Sixteen of seventeen assets have no agreed cost, and the schema changed under... | OPEN.md |
| 28 | 🟠 | `DAX40` has an asset file but the master configures no such feed | OPEN.md |
| 29 | 🟡 | Six index assets have no IS/OOS window, and `SP500ft`'s feed does not exist | OPEN.md |
| 30 | ✅ | `sqx.data.update` ran end to end on 2026-09-25 | docs/OPEN-closed.md |
| 31 | ⚪ | Revisión completa del proyecto — 2026-09-22 — CERRADO 2026-09-26 | docs/OPEN-closed.md |
| 32 | 🔴 | El custodio no tiene candado de propietario | OPEN.md |
| 33 | 🟠 | `pipeline.cleanup` refuses the one finished mother: `metrics.parquet` no long... | OPEN.md |
| 34 | 🔴 | `sqx.projects.builder` installs the donor clone before it refuses | OPEN.md |
| 35 | 🔴 | `sqx.projects.builder --symbol` does not change the market — it cannot author... | OPEN.md |
| 36 | 🟠 | Unit conversions in `no_forex` cost files swing ~5× with the reference price... | OPEN.md |
| 37 | 🟠 | `studies/breakage/mcRetest/` assumes all eight MCR tasks always ran | OPEN.md |
| 38 | 🟡 | Tres divergencias declaradas de los pasos 15, 16.5 y 19 — decisión del dueño | OPEN.md |
| 38b | 🟡 | `/plugin` does not exist here — sqx-lab installed by hand, does not auto-update | OPEN.md |
| 39 | ✅ | El WFC en tres tramos — hecho el 2026-09-24 | docs/OPEN-closed.md |
| 40 | ✅ | Los databanks del proyecto WFC hay que crearlos a mano — resuelto 2026-09-25 | docs/OPEN-closed.md |
| 41 | 🟠 | Half the variant budget goes to combinations that barely trade | OPEN.md |
| 42 | 🟡 | Three Python entry points were never profiled, because they spend `oos2` | OPEN.md |
| 43 | 🟠 | A retest drops the `<!--variant_id-->` stamp — the file name is the only join... | OPEN.md |
| 44 | 🔴 | The CSCV puts two months of `oos1` P&L on its OOS side — each leg's curve sta... | OPEN.md |
| 45 | 🔴 | `nulls.seed` no fija nada | OPEN.md |
| 46 | ✅ | Step 18.5 reads `oos2`, step 23 does not — owner, 2026-09-26 | docs/OPEN-closed.md |
| 47 | ✅ | The conditional map has trading sessions — owner's hours, 2026-09-26 | docs/OPEN-closed.md |
| 48 | 🟡 | Loose ends of the 2026-09-26 batch — each the owner's word, none blocking | OPEN.md |
| 49 | ✅ | Periodic review jobs added — knowhow, dependency map, audit/, docs health — 2... | docs/OPEN-closed.md |
| 50 | 🟡 | Step 20 is built but decides nothing yet — three owner's calls, and 17-19 do... | OPEN.md |
| 51 | 🟠 | The study viewer cannot reach cloud, wfc and cscv — they write into the varia... | OPEN.md |
| 52 | 🟠 | Every stored crossmarket result reads stale in the window | OPEN.md |
| 53 | 🟠 | `edgeCost`'s verdict.csv has no identity column | OPEN.md |
| 54 | 🟢 | A partial re-run (`only`) is not merged beside the stored result — it replace... | docs/OPEN-closed.md |
| 55 | 🟢 | The custodian pulse shows no progress for runs started outside the window — f... | docs/OPEN-closed.md |
| 56 | 🟢 | The nightly audit and docs agents did not run for 16 days — fixed, running ag... | docs/OPEN-closed.md |
| 57 | 🟢 | Step 10 (`crossmarket`) priced exports on the wrong bars and left out the ent... | docs/OPEN-closed.md |
| 58 | 🟢 | A strategy's identity changed in place after the MC Retest — fixed 2026-09-27... | docs/OPEN-closed.md |
| 59 | 🟠 | MC Retest spread and slippage barely perturb forex at today's provisional cos... | OPEN.md |
| 60 | 🟢 | `template_check` no longer checked the owner's condition — fixed 2026-09-27 | docs/OPEN-closed.md |
| 61 | 🟢 | The parameter cloud could not read `collect`'s panel — fixed 2026-09-27 | docs/OPEN-closed.md |
| 62 | 🟢 | `stoploss.graft` needed `key=` to be the first attribute — fixed 2026-09-27 | docs/OPEN-closed.md |
| 63 | 🟢 | Minor frictions of the 2026-09-26 USDJPY M30 workflow run — fixed 2026-09-27 | docs/OPEN-closed.md |
| 64 | 🟡 | `export_spp.py` never manifests the `strategies/` copies | OPEN.md |
| 65 | 🟢 | `snapshots/` disk budget nearly doubled in one night, `profiling/` pinned at... | docs/OPEN-closed.md |
| 66 | 🟢 | `sqx-worker.sh stop` gave up at 20 s while the JVM was still saving — fixed 2... | docs/OPEN-closed.md |
| 67 | 🟡 | `pipeline/XAUUSD/Strategy_17-9-39` no longer runs in the CSCV | OPEN.md |
| 68 | 🟢 | `stress.simulate` reservaba 816 MB por mercado — troceado 2026-09-25 | docs/OPEN-closed.md |
| 69 | 🔴 | La tarea del paso 10 es una estrategia, y debería ser una estrategia-mercado | OPEN.md |
| 70 | 🟠 | El lote del paso 10 no deja ver por dónde va | OPEN.md |
| 71 | 🟠 | `benchmark=0` is the wrong null for PSR, in three finished studies | OPEN.md |
| 72 | 🟠 | `crossmarket` already computes the answer to a question it does not ask | OPEN.md |
| 73 | 🟠 | Three global `sqx-lab` skills are retirement candidates — owner's call | OPEN.md |
| 74 | 🟠 | Steps 23, 24 and 25 export into the same `raw/<P>/WFC_*/<day>/` and overwrite... | OPEN.md |
| 75 | 🟡 | `sqx-worker.sh stop` sent right after `start` is lost | OPEN.md |
| 76 | 🔴 | Darwinex's real spread is 3–8× what `assets/` declares — the proposal is the... | OPEN.md |
| 77 | 🟡 | A one-item random group's hole can still drift to a different block | OPEN.md |
| 78 | 🟡 | MetaTrader 5 under Wine: built, not yet run | OPEN.md |
| 79 | 🟠 | SPP marginal profiles read θ₀'s lone level as argmax and spike | OPEN.md |
| 80 | 🟠 | Two studies read an old run with today's `_build.yaml` — runs should save the... | OPEN.md |
| 81 | 🟡 | The window's cut-over (plan 24) left five owner's calls open | OPEN.md |
| 82 | 🟠 | Crossmarket results of a retired project cannot be archived until the Family... | OPEN.md |
| 83 | 🔴 | The window cannot launch a second project on the custodian for 24 h after the... | OPEN.md |

Read this index, then only the section you need: `grep -n '^## <N>' OPEN.md`.

## Notes

Provenance carried over from the old preamble, kept because it is not restated in any
issue body: this file was split out of `CLAUDE.md` on 2026-09-02, then migrated into the
rebuilt project tree on 2026-09-03 with its paths updated. The 2026-09-04 and 2026-09-21
review notes that used to sit here (issue 3 withdrawn, issues 6/7 resolved, the
three-install topology built and verified) are now folded into issues 3, 6, 7, 9 and 23
themselves — read those sections rather than this note.

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




## 10. 🔴 The pipeline maps count disabled tasks as live — issue 1's table is overstated

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
break the master project's five build tasks. It also contradicts `knowhow/sqx-drive/`'s own rule that
`templateFile` resolves against the *target* install and templates must be copied there first.

This project is also the natural control group for issue 9, so keeping it working matters.

**Fix, when the authoring lane is free:** copy `breakout_xau/` into
`~/Desktop/SQX/user/settings/StrategyTemplates/` and repoint the five fields through the worker's
`-project` API. **Until then, do not delete the worker.**


## 12. 🟠 Results cited in `knowhow/` cannot be reproduced from the current data root

🔬 Found 2026-09-04. Every quantitative claim in `knowhow/locations/xauusd-corpus.md` and
`knowhow/research/research-lessons.md` — the 231-strategy corpus, the ~129/~11 population split, the ATR-stop PF
figures — comes from the previous project's export. `~/Desktop/AlgoData/` holds **36** strategies'
trades. The generating scripts were in `archive/studies/`, deleted 2026-09-26 (issue 8), so nothing cited can be re-run, checked or challenged today, and both current manifests
say `code_version: "migrated from AlgoProject_Old, pre-git"` rather than naming a commit. The old
project itself was deleted on 2026-09-26, so those figures can no longer be traced to their source.

**Fix:** either re-export the corpus with a proper manifest, or mark the affected bullets "from the
old project, not reproducible here", so nobody builds on them assuming they can.


## 13. 🟠 Two analyses state conclusions their samples do not support

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


## 16. 🟠 The trade-dedup gap now spans four live reports

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


## 17. 🟠 Every strategy that already exists carries the OLD `Param Count`

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


## 18. 🟠 `EdgeDecayRatio` / `EdgeDecayFilter` retired — waiting on the GUI to unwire it

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


## 19. 🔴 Three Monte Carlo thresholds are placeholders

`portfolio/common/monteCarlo/` ships with the thresholds the specification gave, and three of them are
not the owner's decision yet. Measured on the 36 strategies of `XAUUSD/Results` (2026-09-09):

1. **`scoring.survival_dd_pct` = 10% of the account.** Vetoes 21 of 36 on its own. It is a
   statement about **position size** as much as about the strategies — at 1,000 $ of risk on a
   100,000 $ account. It stays a placeholder until the prop-firm rules fix it.
2. **The dead-block veto** — any non-overlapping 24-month block with a negative bootstrap median —
   vetoes 30 of 36. The blocks are real losing periods, so the rule is doing work; but a rule that
   fails five of every six candidates is a threshold question. Alternatives in
   `portfolio/common/monteCarlo/POSSIBLE_IMPROVEMENTS.md` §1.
3. **The Family D sub-score saturates at 0** for every strategy, because it takes the worst of
   three parts and the worst block's 5th-percentile profit factor is almost always below 1. It is
   faithful to the specification and currently carries no information.

Nothing here is a bug and nothing blocks a run: the three live in `config.yaml` and `gates.py`, and
changing one re-decides every strategy without touching code.

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

**2026-09-28 (plan 24, F0 + F13): the window's half closed.** The owner answered Q2: the window is
used on Linux only, so nothing of `ui/` is ported. What stays is a guard: `/api/health` carries
`sqx.installs`, and on a machine without any install the window opens read-only (banner, the load
bar's ↻ disabled with its reason — `ui/desktop/shell.py` `guard`, F0). «Continuar workflow» (F7)
refuses too, through its preflight. The worker script's own port to Windows is still open, as
above.


## 22. 🟡 `studies/transfer/crossmarket` — state of play after the 2026-09-14/15 rebuild

Read `studies/transfer/crossmarket/README.md` first — it is now a folder map and an import-direction
table, not a file list — then the `README.md` of the layer you are touching (`inputs/`,
`mechanics/`, `model/`, `simulate/`, `verdict/`, `render/`, `explorer/`), then
`POSSIBLE_IMPROVEMENTS.md`. All of those are current as of the 2026-09-18/19 reorganisation into
layer packages, which moved 37 flat modules and changed no calculation. What is **not** written in
them:

**What changed, in one line each.** No verdict and no market is ever dropped (warnings replace the
gates). Nothing is cached or written to disk — the panel is the output. Random runs are priced in
dollars with the real trades' own sizes and costs, so net / DD / Ret/DD / Sharpe / PF are directly
comparable to SQX's. Four null models, 25,000 draws each per market. Test 1b (paired) and the market
drivers (PDF §5.4 metrics) are new. Everything runs on `envelope.window()` — the backtest's own span,
not the bar file's.

**Open threads, in the order they are worth picking up:**

1. 🔴 **The manual has no screenshots.** `docs/manual/07-otros-mercados-y-timeframes.pdf` (cap. 05-retest-mercados) describes every tab of a
   panel nobody has photographed. Rule 8 forbids inventing them; whoever next opens the panel for
   real should paste a few in. This is the only thing blocking that page from being finished.
2. 🟠 **Only 30 of the 757 strategies are exported.** `raw/XAUUSD/Retest_Markets_-_Family/2026-09-14`
   is a reproducible random sample (`--limit 30`, seed 20260914). The full export is one command and
   ~15 minutes on the worker.
3. 🟠 **`assets/_markets.yaml`'s `structural` category is empty**, so every conclusion so far rests on two
   correlated metals-and-energy markets. The edge-driver regression (`drivers.py` has the metrics,
   not the regression) needs six or more markets before it can be fitted at all, and the PCA on two
   markets is close to vacuous. This is the single change that would most improve what the module
   can say — and it is a retest the owner runs in the GUI, not code.
4. ⚪ **The shareable report was removed** (`text.py`, `panel.render`, the batch command) on the
   owner's instruction that the panel is a one-strategy tool. `reports/XAUUSD/Retest_Markets_-_Family/2026-09-14/crossmarket/`
   is an orphan left by the last batch run. Bringing the report back is a revert, not a rebuild, if
   he ever wants to send someone a page.
5. 🟠 **The only strictly unseen window of this project starts 2023-01-01, and nothing has been
   retested on it.** Added 2026-09-21, building the OOS-stretch tab. Every `dateTo` in every build
   and retest task stops at `2022.12.31` while the bar files run to 2026-01-16 (gold, silver) and
   2026-06-01 (Brent). So the 2018–2022 stretch the new tab tests is out of sample for the
   *generator* but not for the *project*: it entered selection through every `sampleType=127`
   acceptance condition and through the walk-forward matrix's OOS net profit, which is what the
   `selected_window` warning says. A retest over 2023-01-01 → today would be unseen for the base
   asset and for the additional markets at once, would need no such warning, and is a task the
   owner runs in the GUI. `knowhow/conditions/` holds the measurement.
7. ⚪ **`pending_fills` and `fill_mismatch` were measuring the wrong quantity — FIXED 2026-09-21.**
   `pending_fills` read the entry clock, `fill_mismatch` fired on any non-zero price error. Both now
   go through `mechanics/pricing.fill_profile()`: the entry **price** against its own bar's with the
   market's constant spread discounted, and the median error in ATR units against
   `diagnostics.max_fill_error`. Both verified to still fire (a feed displaced 3 ATR, 6% of entries
   moved half an ATR, H1 bars under an M30 backtest). On the three real markets both are now silent,
   which is correct: there are no intrabar fills in this fleet.
   `studies/transfer/crossmarket/POSSIBLE_IMPROVEMENTS.md` §4 holds every measurement.
8. ⚪ **M1 execution was considered for the random-entry study and is not needed by this fleet.**
   Asked 2026-09-21. It would fix nothing here: no strategy has a price exit, every exit lands on a
   bar open, the zero-duration trades share one timestamp (no interval exists at any resolution),
   and the 0.05–0.09 entry offset is a spread. Pricing on M1 would put the study on a grid SQX never
   executed on and *create* a mismatch. It becomes the right build the day a strategy carries a stop,
   a target or a trailing, and `mechanics/pricing.reconcile()`'s exit-side median error is the
   trigger to watch — 0.0000 on 757 of 757 today. Shape it would need then: entries drawn on the
   **logic** timeframe's grid (an M1 placement grid gives the null 30× more room and makes it a
   different, wider null), holds carried in minutes, pricing on M1.

**Two documented reversals live in `knowhow/research/hardest-null.md`** — a null's width is a measurement and
not an intuition, and a bar file is wider than the backtest that ran on it. Read them before
changing anything about how the nulls are placed.

**A gap in `tools/checks.py`, found 2026-09-15.** It verifies every `.py` appears in its folder
README, but not that every file the README names still exists — `text.py` sat in the table for a day
after being deleted. It also cannot catch a call-site broken by a signature change:
`sqx/export/export_bars.py` called `markets.feeds(asset)` for a day after that function started
taking a universe dict, and only failed at runtime. Both classes of drift are cheap to check.

---


## 23. 🟡 The XAUUSD robustness protocol is half built

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


---


## 27. 🟠 Sixteen of seventeen assets have no agreed cost, and the schema changed under them

`python3 -m core.assets --index` shows one asset decided (XAUUSD, and provisionally) and sixteen
blocked. That was already true before the 2026-09-22 reorganisation; what changed is that the units
are now the ones the owner asked for, so **the numbers he gives have to be in the new unit**:

- forex — one spread in points, commission in $/lot, swap in **points per night**;
- everything else — two spreads in points (`build` and OOS), commission in **% of notional**, swap in
  **% ANNUAL** (`knowhow/costs/swap-types.md` has the conversion; the annual/nightly confusion is 360×).

Nothing is blocked that was not blocked before, and no invented value was written.

The same file now also carries `mc_retest` — the spread and slippage ranges the MC Retest task
draws from, in points, per asset. **All 34 of them are undecided.** These do not block: the
preflight warns and exits 0, because an undecided range only makes that one MC Retest task
uninterpretable. `core.assetdata.mc_pending()` names them.


**Update 2026-09-27 — the owner's defaults, applied.** Real broker figures cannot be used as they
are: 8 USD on a 100-oz gold lot at 4,500 is not 8 USD at 500. So:

- **Indices:** commission 0 (raw account); swap −8 % annual on both sides.
- **XAUUSD and XAGUSD:** commission of 8 USD per lot round trip, as % of notional (gold at
  4,500 → 0.001778 %, silver at Darwinex's 63.5907 → 0.002516 %), which scales with each era's
  price; swap −7 % on both sides.
- **Forex:** 8 USD per lot round trip (`SizeBased`); swap = the mean, in points per night, of
  every variant of the pair with an active swap in SQX's instrument registry (7–8 brokers each;
  `monevis` is off and `oanda` is in %, both left out). Still a snapshot of today's rates.

Still open: `SizeBased` is assumed to charge once per trade, as `PercentageBased` was measured to
(#26). If it charges per fill, forex pays 16. Check it with `edgeCost`'s reconciliation on the
first forex harvest built with it. A forex swap model by date (rate differentials) remains possible if the owner wants one.

## 28. 🟠 `DAX40` has an asset file but the master configures no such feed

`assets/DAX40.yaml` names `DAX40_DukasM1_Infinox`, and a sweep of every `project.cfx` on the master
on 2026-09-22 found that symbol in none of them — the other sixteen assets all resolve. Its
`instrument` block and `sqx_now` values are therefore the ones read on 2026-09-03 and carried
forward, not re-read from the live install.

Either the feed was removed from the projects since, or the file was written for a market not yet
set up. **Not a finding against the master's configuration** — that is the owner's — just a note
that this one file cannot be refreshed from `sqx.inspect.instruments` until the feed exists.


---


## 29. 🟡 Six index assets have no IS/OOS window, and `SP500ft`'s feed does not exist

`assets/_policy.yaml` now carries `segments: <SYMBOL>:` for all seventeen, each with the date range
SQX actually holds for its feed (read 2026-09-22 with `-symbol action=list` on the conductor).
**Forex and metals were filled on 2026-09-22** — `build` 2008-01-01 to 2017-12-31, `oos1` to
2022-12-31, `oos2` to 2026-08-30, eleven assets. The **six index CFDs are still
`{from: null, to: null}`**: `window()` refuses to invent one and the preflight warns, so nothing
silently runs on a made-up window.

They were left out deliberately, and it is not a free choice — their histories start in 2011-2013,
so gold's 2008 build window would not fit and `validate()` would reject it:

| asset | data from | | asset | data from |
|---|---|---|---|---|
| EURUSD, GBPUSD, USDCHF, USDJPY, XAUUSD | 2003-05-05 | | NIKKEI225 | 2011-09-19 |
| AUDUSD, EURJPY, GBPJPY, USDCAD | 2003-08-04 | | USA500, USATEC | 2012-01-19 |
| AUDJPY | 2003-12-01 | | DAX40, DJ30 | 2013-09-30 |
| CADJPY | 2004-10-25 | | **SP500ft** | **none** |

⚠️ **`SP500ft_Plus02_Infinox` is in no SQX feed list**, so that asset cannot be built or tested at
all. Its `data` is null and `validate()` reports it. Either the feed needs setting up or the file
describes a market that was never wired.


## 32. 🔴 El custodio no tiene candado de propietario

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


## 33. 🟠 `pipeline.cleanup` refuses the one finished mother: `metrics.parquet` no longer matches its hash

📓 2026-09-23. `python3 -m pipeline.cleanup --project XAUUSD --strategy "Strategy 17.9.39"` exits
with `el export ya no coincide con su hash: metrics.parquet`. The `collected` stage hashed the file
at 09:40:04 on 2026-09-22 and something rewrote it afterwards — the `wfc` and `verdict` stages ran
in the following second, so one of them, or a later re-run, writes `metrics.parquet` after collect
recorded it. Until that is found the ledger's "removable" (`sqx/`, 2,000 files, 32 MB) cannot be
swept, and the guarantee the sweep rests on is broken for every mother that follows. Nothing was
forced. Find which stage rewrites the file and either hash after it or make it write elsewhere.


## 34. 🔴 `sqx.projects.builder` installs the donor clone before it refuses

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


## 35. 🔴 `sqx.projects.builder --symbol` does not change the market — it cannot author for a non-donor asset

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


## 36. 🟠 Unit conversions in `no_forex` cost files swing ~5× with the reference price nobody chose

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


## 37. 🟠 `studies/breakage/mcRetest/` assumes all eight MCR tasks always ran

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


## 38. 🟡 Tres divergencias declaradas de los pasos 15, 16.5 y 19 — decisión del dueño

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


## 38b. 🟡 `/plugin` does not exist here — sqx-lab installed by hand, does not auto-update

**No narrative section was ever written for this issue** — it existed only as a status-table row in the old preamble, preserved here verbatim during the 2026-09-29 OPEN.md cleanup:

> new 2026-09-24: **`/plugin` no existe en este entorno**, así que `sqx-lab` va instalado a mano con `bin/sqx-lab-install.sh`. Funciona igual pero **no se actualiza solo**, y una versión nueva descomprimida encima se lleva la skill local `sqx-spp`. Hay que reejecutar el script tras cada actualización.

## 41. 🟠 Half the variant budget goes to combinations that barely trade

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


## 42. 🟡 Three Python entry points were never profiled, because they spend `oos2`

Encargo 18 (profiling the Python layer) closed on 2026-09-25 with commits `c9011a2` and
`3923010`: nulls, crossmarket, Monte Carlo, filters, CSCV, crossTF, variants, sppUltra, retest and
the gate's harvest, each measured before and after under `AlgoData/reports/perf-optim-2026-09-25`
and `AlgoData/profiling/bench-2026-09-25`, outputs identical. What it could not reach:
`walkForwardCorrelation/report.py` (step 17), its `pbo.py` path over `oos2` (step 18) and
`walkForwardMatrix/report.py` (step 19) — running them spends the reserved window, which is the
owner's one-way door. Measure them the first time the owner runs 17-19 for real, not before.
The MC Retest and the SPP were not measured at 500 either: their cost is SQX's (~34 h and ~2.8 h).


## 43. 🟠 A retest drops the `<!--variant_id-->` stamp — the file name is the only join key

🔬 Encargo 12, 2026-09-26: the retested `strategy_Portfolio.xml` is the fabricated one minus that
comment. After a run, a variant is found by its file name only. Check that `sqx.variants.collect`
and `equity` never relied on the stamp; `sqx/variants/README.md` failure mode 1 describes it as a
join key and is now inaccurate. Card: `knowhow/sqx-format/writing-a-variant.md`.


## 44. 🔴 The CSCV puts two months of `oos1` P&L on its OOS side — each leg's curve starts early

🔬 Encargo 15, 2026-09-26: each leg's daily curve starts ~2 months before its segment with zero P&L
(warm-up), and `equity.json` `splits`/`windows` record that warm-up start (`splits.oos2 =
2022-11-03`). `engines/variants/panel.split(work, "oos2_only")` returns that date, so `windows()`
puts Nov–Dec 2022 of the **oos1** leg's real P&L on the OOS side of the CSCV's chronological
numbers. It changes computed CSCV/WFC figures, so the fix (split at the segment's own start from
`assets/_policy.yaml`) needs a golden before and after. Card: `knowhow/sqx-format/leg-curve-warmup.md`.


## 45. 🔴 `nulls.seed` no fija nada

new 2026-09-25: `engines/nulls/simulate.py:nulls()` usa `abs(hash(rung))`, y `hash()` de una cadena
está aleatorizado por proceso: dos `studies.screening.gate.report` sobre los mismos ficheros dieron
**227 y 229 supervivientes**. Arreglo de una línea (hash estable) pero **cambia una vez todos los p
almacenados** — decisión del dueño. `knowhow/perf/python-parallelism.md`.


## 48. 🟡 Loose ends of the 2026-09-26 batch — each the owner's word, none blocking

- Market surfaces: the call uses the raw rho; `rho_neutral` (each market's exposure × drift
  removed) is shown beside it. Which one should decide is open. Its Fisher interval and J band are
  optimistic because the design clusters variants.
- Edge per cost: no Sharpe-vs-cost-multiplier curve — the MC Retest keeps no daily equity per
  simulation, so it cannot be rebuilt. `min_edge_spreads = 2` and `action = mark` are defaults set by
  the agent at the owner's request that they be parameters.
- The `/oos-gate` skill says the harvest joins "on name"; the gate README and `harvest.py` say identity.
- `engines/nulls/filter.benchmark` needs an observed-value override for path-dependent strategies;
  `studies/readings/structure/` carries its own `subset_null` meanwhile.


## 50. 🟡 Step 20 is built but decides nothing yet — three owner's calls, and 17-19 do not record themselves

`studies/closing/blindJoint/` (encargo 10 B, 2026-09-26) reads the four pieces and puts every
reading of "passes step 20" side by side; it cuts nobody until the owner chooses. Open, all his:
(1) `joint.pieces` × `joint.population` in its `config.yaml`; (2) `BlindJoint` in oos2's
`reserved_for` (`assets/_policy.yaml`) — without it the SPA on oos2 is never read; (3) the CSCV
reads oos2 and the policy does not list it. Engineering, not his: the WFC, CSCV and WFM reports
write no ledger row, so the blind door opens only after `python3 -m ledger.backfill --blind`
(`knowhow/eng/blind-steps-write-no-ledger-rows.md`); wiring them needs (3) first, or the CSCV's own
row would be refused. ⚠️ On 2026-09-26, exploring the USDJPY batches before the module existed,
the session read the two mothers' oos2 daily P&L (sums, correlation) outside the door; no ledger row
records that look — the owner decides whether to add one.

**2026-09-27 (encargo 24, E1):** (3) is decided — the owner put `CSCV` in oos2's `reserved_for`
(Q11). The WFC and the CSCV now write their own rows (one per segment read, through
`engines/variants/look.py`), and `ledger.blind` skips a batch that recorded itself. Still open: (1),
(2), the WFM (19) writing its own row, and `--family` — the WFC and the CSCV now require it and
`pipeline/recipe.yaml` and `ui/daemon/runner/optimisation.py` do not pass it yet (Q9 decides where
the family comes from).

**2026-09-28:** (2) is moot for a human — the owner lifted the oos2 reservation and the blind door
for humans (`knowhow/eng/oos2-door-binds-only-autonomous.md`), so the SPA on oos2 is read whenever a
human runs step 20. It stays open only for an autonomous agent (`ALGO_AUTONOMOUS=1`), together with
whether such an agent should be held at all.


## 51. 🟠 The study viewer cannot reach cloud, wfc and cscv — they write into the variant batch

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


## 52. 🟠 Every stored crossmarket result reads stale in the window

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


## 53. 🟠 `edgeCost`'s verdict.csv has no identity column

`reports/<P>/<D>/<day>/edgeCost/verdict.csv` is `strategy, edge_mean, edge_median, n, verdict`.
Without `identity` the matrix cannot place its rows (199 skipped on `USDJPY_workflow_profiling_v1/
Results`), and `/curate` cannot check that it deletes the strategy that was judged once
`verdict.action: drop` makes edgeCost a gate. Add `identity` as the other studies do.

**Fixed 2026-09-28 (plan 24, E5):** `verdict.csv` is now `strategy, identity, edge_mean, edge_median,
n, verdict`, the identity the harvest's own. The `Test_USDJPY_donchianUpperCrossUp_M30/Results/
2026-09-27` report was signed after the fact from the same harvest it read (numbers untouched).


## 59. 🟠 MC Retest spread and slippage barely perturb forex at today's provisional costs — measured 2026-09-27

SQX draws the MC spread and slippage on a ~0.1-point grain (one USDJPY tick), not continuously: on
`Test_USDJPY_mcrRanges` spread 0.1–2.0 gave 17 distinct outcomes, 0.1–1.0 gave 8; slippage 0.05–2.0
gave 19, 0.05–0.5 gave 4. The declared 1x–4x (`mc_retest.default_multiples`) of the provisional
USDJPY spread 0.1 / slippage 0.05 spans 0.3 / 0.15 points, so 2 and 1 outcomes: those two axes are
not tested. With a realistic spread (~1 point) 1x–4x would span ~30 steps and work as designed.
**The owner's call**: widen the forex multiples, or wait for the agreed costs. `knowhow/costs/mc-retest-ranges.md`.


## 64. 🟡 `export_spp.py` never manifests the `strategies/` copies

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


## 67. 🟡 `pipeline/XAUUSD/Strategy_17-9-39` no longer runs in the CSCV

Its batch predates the per-segment columns: `cscv.report` fails with `KeyError: NetProfit
(build+oos1)`. It is still usable by the parameter cloud. Re-harvest it or retire it; never use a
real batch as a CSCV regression test anyway — every run reads `oos2`
(`knowhow/research/cscv-always-reads-oos2.md`).


## 69. 🔴 La tarea del paso 10 es una estrategia, y debería ser una estrategia-mercado

new 2026-09-25: en un lote de 96 la mayor lleva 117.612 operaciones y cuesta **453 s ella sola**: es
el suelo de cualquier reparto a partir de 24 procesos, y por eso 96 procesos sólo dan 14,2x. Los 9
mercados son independientes dentro de `analyse_market` — repartir por ahí divide la tarea más larga
por ~9. Toca la forma de `analyse_strategy`, que es la puerta del panel: decisión de diseño.
`docs/manual/03-datos-costes-y-registro.pdf` (cap. 12-rendimiento).


## 70. 🟠 El lote del paso 10 no deja ver por dónde va

new 2026-09-25: `pool.map` devuelve en orden y la corrida de 499 estuvo **38 min sin imprimir una
línea**, indistinguible de un cuelgue. Desde fuera tampoco: `py-spy` necesita ptrace y está
bloqueado. Se arregla imprimiendo por orden de terminación.


## 71 · 🟠 `benchmark=0` is the wrong null for PSR, in three finished studies

**Opened 2026-09-22, out of the `studies/readings/monkey/` work.** `core/significance.psr()` takes a `benchmark`
and its docstring says *"Zero asks whether there is any edge"*. All three callers pass zero —
`studies/transfer/crossmarket/verdict/significance.py`, `portfolio/common/monteCarlo/verdict/significance.py`
and `studies/breakage/mcRetest/verdict/evidence.py`.

Zero is not the null a trading strategy is measured against. The honest benchmark is what a
random trader with the same footprint would have got: drift weighted by occupancy, minus cost.
🔬 Measured on XAUUSD `OOS1` that benchmark is **negative in 100 % of 757 strategies** (median
−4,698 $), because a 6-hour position captures ~2,867 $ of gold's rise and pays ~7,756 $ of cost.
So `benchmark=0` is currently the **stricter** of the two, and the studies are conservative rather
than wrong — but they are not answering the question they say they answer.

With Sharpe the two are the same ruler with different centrings (`knowhow/research/`), so
the fix is one argument. **Not done here on purpose**: all three modules are finished, and
changing what a finished study reports is the owner's call, not a side effect of building a
fourth one.


## 72 · 🟠 `crossmarket` already computes the answer to a question it does not ask

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


## 73. 🟠 Three global `sqx-lab` skills are retirement candidates — owner's call

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


## 74. 🟠 Steps 23, 24 and 25 export into the same `raw/<P>/WFC_*/<day>/` and overwrite each other

The structural batch (23), the stop grid (24) and its harvest (25) all retest in the WFC legs and export
with `export_retest --databank WFC_Build …`, which writes `raw/<project>/WFC_Build/<today>/`. Run the
same day, each export replaces the previous: on 2026-09-27 the step-23 report could not be rerun,
because its trades had been overwritten by step 24's. A batch should export under its own name (e.g.
`--out <batch>/export`), and `structure.report` / `atrCalculator.report` read from there.


## 75. 🟡 `sqx-worker.sh stop` sent right after `start` is lost

`start` returns once the port answers; the CLI takes ~20 s more. A `stop` in that gap is swallowed and
the script waits 5 minutes before saying `STILL RUNNING` (2026-09-27, conductor). A second `stop`
works. `stop` could wait for "CLI is now ready" in the worker log before sending.


## 76. 🔴 Darwinex's real spread is 3–8× what `assets/` declares — the proposal is the owner's to apply

`python3 -m studies.data.spread.scan` (2026-09-27), mean opening spread of Darwinex's ticks:
XAUUSD 9 → 63 points 2017 → 2026 against the declared 5 (build) / 10 (oos); USDJPY 4.7 → 10.4
points against 0.1. Neither is constant relative to price (owner's ±20 %: gold's worst year 1.96×,
USDJPY's 1.44×), so the study models the years before October 2017 and proposes, with the owner's
factor 1.25, a `%` commission per segment — XAUUSD 0.0131 / 0.0138 / 0.0118 % (build / oos1 /
oos2), USDJPY 0.0048 / 0.0052 / 0.0078 % — or 16 / 24 / 31 and 0.5 / 0.6 / 1.2 points.
`AlgoData/spread/<tick feed>/spread.html` has the table. **Applied 2026-09-27** to XAUUSD and the ten pairs too (`onboard --spread-only`: spreads, slippage = half, MC spread range; commission and swap kept). **Applied 2026-09-27 to the five index CFDs** on the owner's order: build data start–2019, oos1 2020–2023, oos2 2024–2026-08-31 with its own `spread_oos2` (the schema now allows a segment-named half), oos1/oos2 = Darwinex's mean daily spread in that segment × 1.25; build = the spread PROPORTIONAL to price (owner's option A, `model.fixed`) × 1.25, although fixed-points validates better; slippage = half; MC Retest spread range = the 2.5–97.5 % multiples of measured ÷ proportional mean, times the build spread. Their commission is still null and blocks authoring. Study: `docs/AgentPDFs/spread-real-2026-09-27.pdf`.

Three things are still open:
- **The repricing against SQX itself.** `studies.data.spread.report` swaps SQX's flat spread for
  the real one trade by trade (3 of 115 gold and 3 of 100 USDJPY strategies stop earning OOS). It
  has not been compared with a real DATATICK retest on `*_DarwTick_*` — one short worker job on
  a few strategies of an existing harvest licenses it as that retest's stand-in.
- **USDJPY's model leans on the price level** (`studies/data/spread/POSSIBLE_IMPROVEMENTS.md`):
  back in 2011–2012 it predicts the thinnest spreads of the history.
- **The «poquito de spread»** the owner keeps on top of the `%` is his to name.


## 77. 🟡 A one-item random group's hole can still drift to a different block

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


## 78. 🟡 MetaTrader 5 under Wine: built, not yet run

2026-09-27, owner: test the surviving strategies in MT5 before the portfolio, and give Claude an MCP
over the terminal — backtest, compare with SQX, read-only data; **no order tools**. Built: `mt5/`
(`server.py` registered in `.mcp.json`), `bin/mt5-wine-system.sh` (the root half of MetaQuotes'
official `mt5linux.sh`, without its `apt upgrade`) and `bin/mt5-install.sh` (prefix at `mt5_prefix`,
generic MetaQuotes terminal, Windows Python 3.12 + `MetaTrader5==5.0.6231`). Manual `60-mt5.md`.

Remains, in order:
1. The owner runs `bin/mt5-wine-system.sh` (sudo); then `bin/mt5-install.sh` and the demo login by hand.
2. Verify against a real terminal what was written from the MT5 docs, unrun: the tester ini keys, the
   report's deal rows (13 cells, English `in`/`out`/`buy`/`sell` — a terminal in another language may
   write them translated), `origin.txt` naming the install, MetaEditor compiling a whole folder.
3. The `.mq5`: `sqcli -h` has no verb for it (checked 2026-09-29). Next: a `Test_` project with a
   SaveToFiles task, `SaveSourceCode` + `MNActive` (`knowhow/sqx-drive/export-mql5-source-headless.md`);
   the MT5 generator's name is still to find.
4. The owner sets the bar for "the EA reproduces SQX" (`matched_of_sqx`, gaps) on the first real strategy.

**2026-09-29.** Wine 11.18 staging (owner, sudo), terminal build 6231, the owner's funded account
(Hantec, hedging, `trade_mode` real, symbols suffixed `.h`, terminal in English). `mt5/live.py` reads
account, symbols, bars — verified. Build 6231 ships **MetaQuotes' own MCP** (67 tools, 127.0.0.1:22346,
Bearer token): registered at **local** scope as `metatrader5` (token in `~/.claude.json`, never in git);
its six `trade_*`, `chart_add_expert` and `chart_add_script` are **denied** in `.claude/settings.json`
(owner's choice). Its tester (`tester_prepare_config` → `tester_run_backtest` → `tester_get_report` json)
runs with the terminal open, so it replaces `mt5/tester.py` + `mt5/report.py` **once a real run shows
its report carries every deal**; until then they stay. It has no compile tool: `mt5/metaeditor.py`
stays. `mt5/compare.py` and the Parquet exports stay — MetaQuotes' MCP has neither.
**Planned (owner, 2026-09-29), not built:** multi-account backtests from the one terminal
(Hantec, FTMO; `mt5.login` with the saved password per job, symbol map per account, window and
model chosen per request because some prop firms' data is poor — a per-account data probe first),
then **`weeklyReconciler`**: each weekend, SQX backtests of the live strategies over the last week on
the development data, against the live trades (live EAs run on a separate server; this machine
reads, investor password recommended); a report, form to be decided. Cron slot after
`weekly-data-update` (Sat 03:00).
Note: `Bash(*)` is allowed in this project, so the deny list stops the MCP tools, not a hand-made
HTTP call to the port — the terminal's own "prohibit AI trading" option is the lock that holds.



## 79. 🟠 SPP marginal profiles read θ₀'s lone level as argmax and spike

2026-09-27, found by encargo 24 E4 (`knowhow/research/spp-origin-level-sampled-once.md`). SQX's SPP
step grid need not contain the original value; on the three USDJPY M30 SPPs it misses
`BBerDeviation1` 2.9 (and `BBerDeviation2` 2.8, `CBlc_ClsCrsDCerInt21` 29 on two of them), so θ₀
(permutation −1) is the only tuple at its level. `model/profile.marginal` aggregates it with the rest:
for those parameters `run.read` reports argmax = original and a width-1 plateau, and the design
brief carries `spike: true` and `argmax_is` = original — an artefact. The new two-parameter surfaces
(`spp/surface.py`) already leave θ₀ out of their cells. Fix: `run.read` passes
`grid[grid.index != export.ORIGINAL]` to `profile.marginal`; it changes design briefs, so it is the
owner's to approve and re-run.


## 80. 🟠 Two studies read an old run with today's `_build.yaml` — runs should save their blocks

2026-09-28, found by encargo 24 F9 (`knowhow/eng/studies-reread-build-yaml.md`). `studies/transfer/crossTF`
takes the block order from `crosstf.timeframes` and `studies/readings/structure` each WFC leg's
segment from `wfc.tasks[].segment`, both re-read at analysis time. Since F9 the window can edit both
(Q17), so one change there silently re-labels every past run: crossTF scores cells on another
timeframe's bars, structure files legs under the wrong window. The zone warns beside both values.
Proposal: `sqx.projects.crosstf` writes `blocks.json` (the ordered blocks) next to the project's run
record and the crossTF study reads it before the doctrine; `structure/inputs.py` reads the segments
from the batch's `ran.json`, which `sqx.variants` already writes. The owner decides; until then change
those two values only between runs.


## 81. 🟡 The window's cut-over (plan 24) left five owner's calls open

2026-09-28, closing F13 of `docs/encargos/24-plan-ventana.md` — the owner: «borra la UI anterior;
quiero que en esta máquina esté solo la nueva». The waves ran without gates at the
owner's instruction («programa TODO lo que falte… borra la UI anterior»); where a question was
still open the plan applied its recommended reading (§10) and the owner corrects afterwards. These
five are his, and nothing in the code decides them:

1. **The three ledger files of USDJPY.** Plan 24 §10 says every front left them untouched,
   «decisión del dueño pendiente», without naming them. On disk the likely three are the
   harnesses' — `AlgoData/ledger/USDJPY_H1_perf.jsonl`, `USDJPY_H1_TestUSDJPY_Workflow_v1.jsonl`,
   `USDJPY_H1_USDJPY_workflow_profiling_v1.jsonl` (the last one's project was retired on
   2026-09-27; F13 only stopped the tests using it) — beside the two of the Donchian study. Keep, archive or delete: his call; they count
   searches in Registro de búsquedas meanwhile.
2. **«Subprueba del MC Retest».** F5's acceptance asked to re-run «one MC Retest sub-test»; what it
   built and tested re-runs one test of the trade-level Monte Carlo (`monteCarlo`, by its title)
   or one crossmarket market, beside the stored result (`knowhow/eng/partial-reruns-beside-stored.md`).
   Whether the owner meant that, or one of the eight SQX MC Retest perturbation tasks (an SQX run,
   not a Python one), is his to say.
3. **The default step when archiving.** «Archivar» (F4) asks the step with no default, because the
   rail's last «hecho» can be a reading past a sealed 17-19. Keep it without a default, or name
   the rule.
4. **The knobs chosen for the window.** Q4 (a check in `tools/checks.py`, the rail stays in code),
   Q5 (show «0» where Min Distance is `null`, the YAML untouched), Q15 (filters AND only) and Q17
   (Configuración SQX writes `_build.yaml` for new projects) were applied as recommended.
5. **F7's live test.** «Continuar workflow» is built and tested with every SQX call faked
   (`tests/test_advance.py`, `test_advance_edges.py`); the live run on the conductor with
   `Test_UiContinuar_USDJPY` (Q20) waits for the owner (plan 24 §6).


## 82. 🟠 Crossmarket results of a retired project cannot be archived until the Family databank is re-exported

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


## 83. 🔴 The window cannot launch a second project on the custodian for 24 h after the first

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

## 84. 🟡 What the 2026-09-29 walk of the window left for the owner

🔬 2026-09-29, every button of the window driven on `Test_USDJPY_donchianUpperCrossUp_M30` (steps
13-20 from the rail). The window's bugs found were fixed; these are the owner's calls:

- **A retest that does not empty its output leaves two populations in it.** `OOS`, `MCR 1 Bar`,
  `MCR 2 Spread` and `WFM` of that project hold today's strategies beside earlier ones (saved as
  «Strategy X(1)»), and the harvest pairs by name, so it read the older copies. No `Clear
  databanks` task exists in the project. The launch confirmations now warn; whether the workflow
  project should clear an output before its task is a project-configuration decision.
- **`MCR 3 Slippage` moved nothing on USDJPY** — 1,000 identical simulations for all 21
  strategies (`tarea_sin_dispersion`): 0.325-1.3 points of slippage do not change a market-entry
  M30 strategy. The range (`assets/_policy.yaml`) is his.
- **Steps 10.5 and 16.5 have no button** (the /crosstf and /variants fabrication: the mothers
  to pick and a clamped/rounding review), so 11, 16.5-18.5 cannot be run from the window.
- **Estrategia needs ~1,480 px of width**: it fits 1920, not 1280. A redesign, not a fix.
- **The interview asks «transición o estado» after a sentence that says «cruza»** — it could
  infer it; left as it is.
- During the WFM SQX logs thousands of `StatsComputer - Exception computing databank column
  ParameterCount / DoFRatio` (SQX's own, harmless to the run; the watcher now ignores them).

## Constraints discovered while investigating

- **SQX rewrites every `project.cfx` on save/exit.** All 14 project files were restamped within the
  same second (`14:33:43`, 2026-09-02). Editing a `project.cfx` on disk while the GUI holds that
  project **will be silently overwritten**. Config edits must be made in the GUI, or on disk only
  while SQX is not running.
- `project.cfx` is a plain ZIP: `config.xml` + one `<Type>-Task<N>.xml` per task. Safe to *read*
  at any time.

