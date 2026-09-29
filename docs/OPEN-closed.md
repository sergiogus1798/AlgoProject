# Closed OPEN.md issues (archive)

This file holds every OPEN.md issue that was closed (heading marked ⚪, 🟢 or ✅), moved out
verbatim on 2026-09-29 so the always-scanned `OPEN.md` stays small. Issue numbers are unchanged,
so a citation like "OPEN.md §26" still resolves here. See `OPEN.md`'s own index for the full
open-and-closed table and the status legend.

---

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


## 68. 🟢 `stress.simulate` reservaba 816 MB por mercado — troceado 2026-09-25

new 2026-09-25: **`stress.simulate` reservaba 816 MB por mercado** — la matriz de 25.000 corridas
entera, con tres arrays `float64` de valores booleanos. Troceada en lotes de 500: **140 MB**, cifras
idénticas. Sin esto, 96 procesos no caben en 125 GB: un intento llegó a 94,5 GB y otro a 89 GB, y
**el núcleo mató la ventana de VSCode**.


