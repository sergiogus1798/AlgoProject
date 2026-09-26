# Open Issues

Tracked issues for the AlgoProject / StrategyQuant X pipeline.
Split out of `CLAUDE.md` on 2026-09-02 so the always-loaded instructions stay lean.
Migrated into the rebuilt project on 2026-09-03; paths updated to this tree.

Status: 🔴 open · 🟡 in progress · 🟢 resolved · ⚪ closed / won't fix

Reviewed 2026-09-04. 6 and 7 are resolved, 5 is closed, 3 and 9 are settled and built but blocked on
one thing: **the master GUI must be closed**. Nothing here writes to the master while it is up.

**Reviewed 2026-09-21.** Issue 3 is **⚪ withdrawn by the owner** — the SP500 repair is out of the
plan and is not to be run; read its box before acting on anything that tails the master's log or
counts its projects. The GUI-closed window also stopped being the blocker it was: the three-install
topology was built and verified that day (`knowhow/sqx-drive/three-install-topology.md`).

| # | was | now | what remains |
|---|---|---|---|
| 1 | 🟡 | 🟡 | mitigation needs the lifecycle lane |
| 3 | 🟡 | ⚪ | **withdrawn by the owner 2026-09-21** — repair not to be run; the hourly error stays |
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
| 20 | — | 🟢 | moot 2026-09-26: the ungated script was deleted; ⚠️ nothing is gated on this machine's settings today |
| 21 | — | 🟡 | new: `bin/sqx-worker.sh` is bash, so half the project cannot run on Windows |
| 22 | — | 🟡 | new: `crossmarket` rebuilt as a one-strategy panel; four threads left open |
| 23 | — | 🟡 | topology **settled**; design unblocked, execution still waiting on lane P and W2 |
| 24 | — | 🔴 | new: **the holdout pre-registration is a one-way door** — scaffolded, unsigned |
| 25 | — | 🟢 | new: the authoring chain is proven headless end to end; `OPEN.md` issue 9 now has its positive control |
| 26 | — | 🔴 | new: the `%` commission may charge per leg or per trade — a factor of 2, unmeasured |
| 27 | — | 🟠 | new: 16 of 17 assets still have no agreed cost, now in the owner's new units |
| 28 | — | 🟠 | new: `DAX40`'s feed is in no project on the master, so its file cannot be refreshed |
| 29 | — | 🟡 | forex and metals filled 2026-09-22; the 6 index CFDs still have no IS/OOS window |
| 30 | — | 🟡 | new: the data-update command is guarded and documented; its download awaits a GUI-closed run |
| 31 | — | 🔴 | new: **revisión completa 2026-09-22** — `ran` hereda el arnés SPP, `spp_export` lee el databank/ventana equivocados, el IC del WFC ignora la dependencia entre variantes, sin candado ni timeout en el custodio. `docs/AgentPDFs/revision-proyecto-2026-09-22.md` |
| 37 | 🔴 | 🟢 | **hecho 2026-09-24**: el lector salta la tarea que no corrió (MinDist nunca aplica a órdenes a mercado), los rangos de spread/slippage salen de `mc_retest.default_multiples` (1x–4x el coste del backtest, dueño 2026-09-24) y tres fórmulas mal reconstruidas están corregidas. 71 desacuerdos → 2 celdas sueltas |
| 38b | — | 🟡 | new 2026-09-24: **`/plugin` no existe en este entorno**, así que `sqx-lab` va instalado a mano con `bin/sqx-lab-install.sh`. Funciona igual pero **no se actualiza solo**, y una versión nueva descomprimida encima se lleva la skill local `sqx-spp`. Hay que reejecutar el script tras cada actualización |
| 38 | 🔴 | 🟡 | **hecho en parte 2026-09-25**: el retest de variantes ya no corre en el `Retester` de serie — `sqx.variants.execute` exige `--project` (el del workflow, de `builder --workflow`) y se niega si hay activa otra cosa que las tres patas del WFC. **Queda** el arnés SPP del pipeline desatendido (`sqx.variants.spp`, `pipeline/recipe.yaml`), que sigue escribiendo su tarea en el `Retester` de serie, contra la regla 10 |
| 48 | — | 🟡 | new 2026-09-25: **dos parches locales al código de sqx-lab 1.2.0**, marcados `LOCAL PATCH` y listados en `tools/sqx-lab/LOCAL_PATCHES.md` — `sqx-random-group` reexportaba bloques sin `categoryType="Custom blocks"`, y la verificación de `sqx-strategy-project` exigía un databank que los proyectos de serie de los workers no traen. Una versión nueva descomprimida encima los borra: `bin/sqx-lab-install.sh` avisa si faltan |
| 39 | 🔴 | 🟢 | **hecho 2026-09-25**: el bucle sobre estrategias de `crossmarket.report` se reparte entre los núcleos con `fork` (`--workers`, por defecto todos). 8×9 a 500 sorteos: **623,5 s → 156,1 s con 7 procesos**, `verdict.csv` idéntico byte a byte. `docs/manual/12-rendimiento.md` |
| 40 | 🔴 | 🟢 | **hecho 2026-09-25**: el ATR se cachea por `(barras, ventana)` (`engines/market/calibrate.py`) y la tabla OOS se agrupa una vez por identidad (`studies/screening/gate/monkey.py`), y el mono va en paralelo. `studies.screening.gate.report` a 500: **31,1 s → 6,1 s**, `scorecard` de 500×29 idéntico columna a columna |
| 41 | — | 🟢 | new 2026-09-24: **`sqx-worker.sh stop` volvía a los 20 s diciendo «did not stop»** mientras la JVM seguía escribiendo databanks, y quien leía después veía 211 de 500 `.sqx`. Ahora espera hasta 5 min a que el proceso se vaya de verdad. **No se perdió nada**: la sincronización acabó sola |
| 42 | — | 🟢 | new 2026-09-24: una estrategia que **no dispara en ningún mercado ajeno** tumbaba el lote entero del paso 10 con `KeyError: 'bar_cap'`. Ahora se anota como veredicto propio. Salió a la primera con 8 estrategias reales |
| 43 | — | 🔴 | new 2026-09-24: **la mitad de los análisis de Python no está ejercitada.** De 23 puntos de entrada se han medido 7; de los 5 primeros que se probaron a mano, 4 fallaron por prerrequisitos o por entrada de la forma equivocada. El peor: **`studies.readings.monkey.report` escribe «0 estrategias» y sale con éxito** cuando `--sample OOS1` no casa con el export (los de crossmarket sólo llevan `IST`). `tasks.is_oos` muere con `StopIteration` en un databank sin OOS y funciona perfecto (0,57 s) en el correcto; `exposure.report` y `tasks.nulls` mueren con `IndexError` en vez de nombrar el fichero que les falta |
| 33 | — | 🟢 | new: **un clon del donante seguía operando ORO** para cualquier activo que no fuese XAUUSD. Arreglado el 2026-09-24 con `sqx/projects/resources.py` y un guardia; `knowhow/authoring/donor-clone-market.md` |
| 34 | 🔴 | 🟢 | **causa hallada y arreglada 2026-09-24**: `crossTF/config.yaml` llevaba el feed de XAUUSD fijo y puntuaba USDJPY contra barras de oro. Con `--feed` correcto la correlación sube de −0.34 a 0.98–0.99; el aviso de costes ya nombra el activo real. `knowhow/authoring/donor-clone-market.md` |
| 35 | — | 🟢 | new: `export_metrics` sólo leía el maestro y `sync_bars` moría en un `markets.FILE` inexistente. Los dos arreglados el 2026-09-24; `knowhow/export/bars.md` |
| 36 | 🔴 | 🟢 | **hecho 2026-09-24**: `studies/transfer/crossmarket/report.py` juzga la población entera por amplitud y escribe el `verdict.csv` de `/curate`. ⚠️ Revierte la decisión del 2026-09-15 de no guardar resultados; el panel sigue siendo donde se mira UNA estrategia |
| 41 | — | 🟠 | new: **el diseño de variantes gasta la mitad del presupuesto en combinaciones que apenas operan** — 1.002 de 2.000 filas de `Strategy 17-9-39` quedan bajo 30 operaciones, y el filtro colapsa `DICrossShift1` a un valor. Medido 2026-09-24 con `studies/optimisation/cloud/` |
| 46 | — | 🔴 | new 2026-09-25: **la tarea del paso 10 es una estrategia, y debería ser una estrategia-mercado**. En un lote de 96 la mayor lleva 117.612 operaciones y cuesta **453 s ella sola**: es el suelo de cualquier reparto a partir de 24 procesos, y por eso 96 procesos sólo dan 14,2x. Los 9 mercados son independientes dentro de `analyse_market` — repartir por ahí divide la tarea más larga por ~9. Toca la forma de `analyse_strategy`, que es la puerta del panel: decisión de diseño. `docs/manual/12-rendimiento.md` |
| 47 | — | 🟠 | new 2026-09-25: **el lote del paso 10 no deja ver por dónde va** — `pool.map` devuelve en orden y la corrida de 499 estuvo **38 min sin imprimir una línea**, indistinguible de un cuelgue. Desde fuera tampoco: `py-spy` necesita ptrace y está bloqueado. Se arregla imprimiendo por orden de terminación |
| 44 | — | 🟢 | new 2026-09-25: **`stress.simulate` reservaba 816 MB por mercado** — la matriz de 25.000 corridas entera, con tres arrays `float64` de valores booleanos. Troceada en lotes de 500: **140 MB**, cifras idénticas. Sin esto, 96 procesos no caben en 125 GB: un intento llegó a 94,5 GB y otro a 89 GB, y **el núcleo mató la ventana de VSCode** |
| 45 | — | 🔴 | new 2026-09-25: **`nulls.seed` no fija nada**. `engines/nulls/simulate.py:nulls()` usa `abs(hash(rung))`, y `hash()` de una cadena está aleatorizado por proceso: dos `studies.screening.gate.report` sobre los mismos ficheros dieron **227 y 229 supervivientes**. Arreglo de una línea (hash estable) pero **cambia una vez todos los p almacenados** — decisión del dueño. `knowhow/perf/python-parallelism.md` |
| 32 | — | 🟡 | **mitad cerrada**: `sqx-worker.sh` ya rechaza un segundo lanzamiento sobre el mismo install y un puerto derivado (2026-09-23). Falta el candado de propietario: **el custodio no tiene candado** — 2026-09-23 dos sesiones se pisaron en W2: `stop` mató corridas ajenas. Evidencia en vivo del §2.D de la revisión. `knowhow/perf/smt-in-sqx-retest.md` «dos sesiones sobre el custodio a la vez» |

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

## 8. 🟡 Migrated analyses are parked, not converted — partly done

`archive/studies/` held eight scripts from the previous project. They were written against the old
data layout, so reusing one means rewriting it over `core/` and the data root.

**Converted 2026-09-04:** the IS→OOS predictor study is now `studies/screening/analysis/` plus
`studies/screening/isOos/report.py`. It is a rewrite, not a port — the old `is_oos_analysis.py` would crash on
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
trades. The generating scripts are parked in `archive/studies/` against the old data layout
(issue 8), so nothing cited can be re-run, checked or challenged today, and both current manifests
say `code_version: "migrated from AlgoProject_Old, pre-git"` rather than naming a commit.

**Fix:** either re-export the corpus with a proper manifest, or mark the affected bullets "from the
old project, not reproducible here", so nobody builds on them assuming they can.

## 13. 🟠 Two analyses state conclusions their samples do not support

🔬 Found 2026-09-04, reading `knowhow/` against `archive/studies/`.

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

Still unverified underneath all of it: whether SQX applies `PercentageBased` per leg or per trade
(issue 26).

## Constraints discovered while investigating

- **SQX rewrites every `project.cfx` on save/exit.** All 14 project files were restamped within the
  same second (`14:33:43`, 2026-09-02). Editing a `project.cfx` on disk while the GUI holds that
  project **will be silently overwritten**. Config edits must be made in the GUI, or on disk only
  while SQX is not running.
- `project.cfx` is a plain ZIP: `config.xml` + one `<Type>-Task<N>.xml` per task. Safe to *read*
  at any time.

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

1. 🔴 **The manual has no screenshots.** `docs/manual/05-retest-mercados.md` describes every tab of a
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

**Where the plan lives:** `docs/AgentPDFs/protocolo-robustez-2026-09-21.md`. Its status table is
authoritative; this entry only says that the work exists and is unfinished, so it surfaces in the
daily audit.

Built (2026-09-21): `core/surface/` with its property test, `studies/breakage/spp/`,
`studies/optimisation/wfm/`, and the disk budget plus provisional costs in `perf/disk/` and
`assets/XAUUSD.yaml`. Three manual pages, and the findings in `knowhow/sqx-format/` and
`knowhow/export/`.

Built 2026-09-21, later the same day: **`sqx/variants/` design, fabrication and manifest** —
contract C1 in, `.sqx` batch and contract C2 out, with `tests/test_variants.py` and
`docs/manual/18-variantes.md`. Verified on `Strategy 17.9.39`: 5,000 tuples designed, 3 fabricated
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
`docs/manual/25-cscv.md`. Measured on `Strategy 17.9.39`, 479 usable variants: **PBO 30 % choosing
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
   are lane S of `docs/AgentPDFs/plan-ejecucion-2026-09-21.md`. **`sqx/variants/` design is
   unblocked**; execution additionally waits for lane P's path work and for W2 to exist.
   ⚠️ `docs/SETUP-NEW-MACHINE.md` §2 still says "two is the working minimum" and is now stale —
   task P1 updates it.
2. **`bin/sqx-worker.sh` is bash, and the platform must run on several Linux machines.** That
   promotes the port to Python from "decide early" to a requirement. Cheapest moment is whenever
   `sqx/variants/` is built, since that layer is being touched anyway. ⚠️ Related debt found the
   same day: `bin/sqx-worker.sh` and `bin/clone-sqx-worker.sh` carry this machine's paths hard-coded
   and `checks.py` does not see them, because it only scans `.py`.
3. **The holdout pre-registration.** 2022–2026 is read by the WFM study and the variant study at
   once, so what would count as approved has to be written, with a date, **before** either runs.
   Nothing has been written. `studies/optimisation/wfc/` must not run until it exists.

Also pending the owner: the WFC verdict thresholds are PROPOSED, not approved; and the costs in
`assets/XAUUSD.yaml` are SQX defaults, not agreed Infinox figures, so every cost-bearing result
produced before he replaces them carries that caveat.


---

## 24. 🔴 The holdout pre-registration does not exist, and it is a one-way door

Split out of issue 23's blocker list on 2026-09-21 because it is not a variant-study problem: it
gates every study that reads **2022–2026**, and unlike everything else here it **cannot be fixed
retroactively**. The first analysis that looks at that window without it burns the holdout
permanently, and no later result over that window is defensible.

Scaffolding written 2026-09-21 to `docs/preregistro/holdout-XAUUSD-2026-09-21.md` — **in the
repo, not in `AlgoData`**: it has to be under version control to be worth anything, and hard rule 7
governs heavy data, not a governance document. **It is not
in force until the owner fills in the four decisions and signs it** — the file names them
explicitly and says so at the top.

Until it is signed, no module reads 2022–2026. Lots build and verify against the SPP Phase 0 export
already on disk (`raw/XAUUSD/SPP_IS/2026-09-10/`).

Related: the WFC verdict thresholds are PROPOSED, not approved — but the owner decided 2026-09-21
that **thresholds do not block anything**: the user decides them and they are changeable. The
pre-registration records whichever number is current, and records the change when it changes. That
is what keeps it honest while the criteria are still moving.

## 26. 🟠 `PercentageBased` charges ~twice per trade — MEASURED 2026-09-26, the fix is the owner's

🔬 Measured by encargo 11 on existing harvest data, no SQX run: least squares of
`price_pnl − Profit/Loss = k · commission_once` over **45,488 same-day XAUUSD trades** (no swap to
confound) gives **k = 1.87**, not 1 — k = 1 sits 31 standard errors off. The commission is charged
close to once per leg, so today's `no_forex` formula (`_classes.yaml`) understates gold's commission
by nearly half. `knowhow/costs/commission-methods.md` has the fit. **Not applied**: changing
`assets/symbols/XAUUSD.yaml` (and every index) is the owner's decision; until then every gold result
with costs carries `costs_provisional`. What follows is the original entry.

Every `no_forex` asset in `assets/` now declares its commission as a **percentage of notional**,
applied by SQX's `PercentageBased` method. Reading the snippet
(`internal/extend/Snippets/SQ/Trading/Commissions/PercentageBased.java`, 2026-09-22) it charges in
`computeCommissionsOnOpen` only and returns 0 on close. But `knowhow/costs/commission-methods.md` measures **$8 per
lot per side, $16 round turn** against `SizeBased 8`, which only fits if the engine applies the
method to each leg.

**It is a factor of two on the commission of gold and every index.** Until it is settled, any figure
written into a `no_forex` `commission` field is uncertain by 2×, and XAUUSD's carries the caveat in
its own `why`.

The test is cheap and needs no new code: build or retest one strategy with `PercentageBased` at a
known percentage, export its trades, and recover `gross − reported P/L` per trade — the same
residual `portfolio/common/monteCarlo/inputs/costs.py` already computes. One worker job.

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

## 30. ✅ `sqx.data.update` ran end to end on 2026-09-25

`python3 -m sqx.data.update --apply` drives `-data action=update` on the master — the CLI form of
the GUI's "Update all" — then proves no `.sqx` was lost and refreshes `assets/_policy.yaml`.

**Run on 2026-09-25, master GUI closed, owner's order:** the no-symbol form updated **all 67
configured symbols** in 16 min (19:42→19:58 UTC), exit 0. Rule 1 held: 7,546 `.sqx` before and
after (full copy taken first in `AlgoData/snapshots/2026-09-25-master-antes-update-data`). The
seventeen assets' ranges moved from `2026-09-22` to `2026-09-25` (BRENT to `2026-09-24`). Log kept
at `AlgoData/backups/data-update/2026-09-25T194240Z.log`.

**Left open:** two days of `MSFT_DukasM1_ICMarkets` (2026-09-21, 2026-09-23) failed with HTTP 429 —
the feed's rate limit. The next run fetches them; nothing to fix in the code.

**Scheduled since 2026-09-25:** `bin/weekly-data-update.sh`, Saturdays 03:00 from cron — full copy
of `user/projects` first (last three kept), then the update. Not guarded: a worker **started**
during the ~16 min copies half-written H2 databases, since `sqx-worker.sh` does not know the update
is running.

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

## 28. 🟠 `DAX40` has an asset file but the master configures no such feed

`assets/DAX40.yaml` names `DAX40_DukasM1_Infinox`, and a sweep of every `project.cfx` on the master
on 2026-09-22 found that symbol in none of them — the other sixteen assets all resolve. Its
`instrument` block and `sqx_now` values are therefore the ones read on 2026-09-03 and carried
forward, not re-read from the live install.

Either the feed was removed from the projects since, or the file was written for a market not yet
set up. **Not a finding against the master's configuration** — that is the owner's — just a note
that this one file cannot be refreshed from `sqx.inspect.instruments` until the feed exists.


---

## 17 · 🟠 `benchmark=0` is the wrong null for PSR, in three finished studies

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

## 18 · 🟠 `crossmarket` already computes the answer to a question it does not ask

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
number. Same reasoning as issue 17: `crossmarket` is finished and this is the owner's call.

## 31. 🔴 Revisión completa del proyecto — 2026-09-22

Revisión en modo revisor pedida por el dueño: fallos, mejoras, optimizaciones de tiempo, memoria y
tokens, y decisiones pendientes. Está entera en `docs/AgentPDFs/revision-proyecto-2026-09-22.md`;
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

## 32. 🔴 El custodio no tiene candado de propietario

📓 2026-09-23. Cinco sesiones de Claude paralelas en la máquina (`ListAgents`). Una hacía un
benchmark en `SQX_w2` (arrancar, cargar, correr, **parar**, cambiar `coreUsage`) mientras otra
bisecaba costes en el mismo custodio. Siete `stop` mataron corridas ajenas; los proyectos de ambas
arrancaron sobre instancias de la otra; un tercer arranque murió con `Database may be already in
use`. Timeline completa en `knowhow/perf/smt-in-sqx-retest.md`, «Lo que salió mal: dos sesiones sobre el
custodio a la vez».

Es el §2.D de `docs/AgentPDFs/revision-proyecto-2026-09-22.md` visto en vivo. Arreglo propuesto:
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
`docs/AgentPDFs/revision-proyecto-2026-09-22.md` already proposes for the sampling.

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

## 45. 🟡 `pipeline/XAUUSD/Strategy_17-9-39` no longer runs in the CSCV

Its batch predates the per-segment columns: `cscv.report` fails with `KeyError: NetProfit
(build+oos1)`. It is still usable by the parameter cloud. Re-harvest it or retire it; never use a
real batch as a CSCV regression test anyway — every run reads `oos2`
(`knowhow/research/cscv-always-reads-oos2.md`).

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
