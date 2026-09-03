# Open Issues

Tracked issues for the AlgoProject / StrategyQuant X pipeline.
Split out of `CLAUDE.md` on 2026-09-02 so the always-loaded project instructions stay lean.

Status: 🔴 open · 🟡 in progress · 🟢 resolved · ⚪ closed / won't fix

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

**GBPJPY is not immune — the note in `CLAUDE.md` was wrong.** Mapping all six projects
(`docs/*-pipeline.md`) shows every one of them has the same shape: build → robustness gauntlet →
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
fires. Full task-by-task maps are in `docs/<PROJECT>-pipeline.md`. Mitigation options: set the at-risk databanks to `Auto-sync never` (they currently say
`Auto-sync every 1 hour` in `config.xml`), or export to a folder before each clear, or drop task 15
from the chain.

## 2. ⚪ ~1,208 `SPP OOS` + ~1,142 `WFM` XAUUSD strategies lost — CLOSED, accepted

Investigated 2026-09-02. Indexed every `.sqx` on the machine by the SHA-256 of its inner
`strategy_Portfolio.xml` (see `tools/recovery/index_sqx.py`): **17,754 files → 13,288 unique
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

## 3. 🔴 `Infinox_SP500ft_H4_HighPrecision` never loads — confirmed live

`project.cfx` holds 4 files but `config.xml` declares 8 active tasks. A larger
`project_backup.cfx` (306 KB, 2025-10-13) sits beside it.

**Confirmed 2026-09-03 (🔬):** the running master's own project list returns **14** projects while
`user/projects/` holds **15** directories. The missing one is exactly
`Infinox_SP500ft_H4_HighPrecision` — SQX silently skips it at load rather than reporting an error.
Reproduce with the MCP `list_projects` tool, or `-project action=list` with the GUI closed, and
diff against `ls ~/Desktop/SQX/user/projects/`.

**Cause and repair path confirmed 2026-09-03 (🔬), by comparing the two archives' members:**

| archive | members |
|---|---|
| `project.cfx` (114 KB) | `config.xml`, `Retest-Task1/2/3.xml` |
| `project_backup.cfx` (306 KB) | the same, plus `Retest-Task4/6/8/9/10.xml` |

`config.xml` references 8 task files; **five of them are simply absent from the live archive**, and
the backup holds exactly those five. That is why the GUI drops the project without an error: it
cannot resolve a declared task. `1_sqx/inspect/dump_project.py` fails on the same project with
`KeyError: There is no item named 'Retest-Task8.xml'`, which is a cheap way to detect this class of
corruption across every project.

**Repair, when the SQX-lifecycle lane is free:** close SQX, back up the directory, replace
`project.cfx` with `project_backup.cfx`, reopen, and confirm the master's project list returns 15.
Writing to `user/projects/` needs SQX closed — do not attempt it while the GUI is up.

## 4. 🔴 Projects are older than the app

Install is `144.2953`. `XAUUSD/config.xml` declares `version="142.2399"`, and its Build task
declares `version="126.2189"`. `PortfolioMaster` is `v140.2166`.

## 5. 🔴 Mojibake Windows path in task configs

`XAUUSD/config.xml`, Build task:
`templateFile="C:\Users\RubÃƒÆ’Ã†â€™...n MartÃƒÆ’Ã†â€™...nez\OneDrive\Escritorio\FILTROS\Build strategies.cfx"`
— multiply UTF-8/CP1252 re-encoded `Rubén Martínez`, left over from an imported `.cfx`. Harmless
today (the template is embedded in `Build-Task3.xml`) but it makes the field unreadable.

## 6. 🔴 SQX logs pruned to 14 days

History before 18 Aug is gone. Consider archiving `user/log/StrategyQuant/` on a schedule.

---

## Constraints discovered while investigating

- **SQX rewrites every `project.cfx` on save/exit.** All 14 project files were restamped within the
  same second (`14:33:43`, 2026-09-02). Editing a `project.cfx` on disk while the GUI holds that
  project **will be silently overwritten**. Config edits must be made in the GUI, or on disk only
  while SQX is not running.
- `project.cfx` is a plain ZIP: `config.xml` + one `<Type>-Task<N>.xml` per task. Safe to *read*
  at any time.

## 7. 🟡 `core.sqxfile` has no golden test

`tests/test_cfx.py` protects the project parser; the `.sqx` parser has nothing. A fixture needs a real
strategy file, and those are ~6 MB and git-ignored. Decide between committing one small `.sqx` as an
explicit exception, or pointing the test at a path declared in `config/machine.yaml`.

Until then, a silent change in how symbols, hashes or parameters are read would surface only as
strange analysis results, weeks later.

## 8. 🟡 Migrated analyses are parked, not converted

`archive/studies/` holds eight scripts from the previous project: the ATR-stop studies, the IS→OOS
predictor study, the databank scan, the trade validator and their plotting code. They were written
against the old data layout, so reusing one means rewriting it over `core/` and the data root. Their
findings are already in `knowhow/`; the code is kept only so a result can be reproduced.
