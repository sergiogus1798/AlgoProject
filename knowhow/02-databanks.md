# Databanks — how strategies get deleted

📓 **Memory is the source of truth. Every sync deletes on-disk `.sqx` files not held in memory.**

Log format (`user/log/StrategyQuant/log_YYYY_MM_DD.log`):

```
'Project - USDJPY/WFM' saved - files before sync 248 / after sync 36 / saved 36 / removed 248
```

- 📓 **The hourly auto-sync does this, not just shutdown.** The line above is `Auto-sync every 1 hour`.
  Closing SQX is simply one more sync. The long-standing belief that "closing SQX deletes strategies"
  was a misdiagnosis.
- 🔬 **`ClearDatabanks` tasks empty a databank in memory; the next sync then deletes its files.** That
  is the loss mechanism. A project whose chain ends `ClearDatabanks` → unconditional `GoToTask` back
  to the builder wipes those databanks every cycle, forever.
- 🔬 **Every project on this install has that shape.** GBPJPY is not the safe counter-example the old
  notes claimed — it clears `OOS`, `RetestPairs`, `WFM Performance`, all auto-syncing. It had merely
  not reached its clear task when observed. SP500 H1 clears its `WFM` outright.
- 🔬 `dump_project.py <PROJECT>` renders a **Databank flow** table marking exactly which databanks are
  at risk in each project. Read it before running anything (the old per-project docs under `docs/`
  are retired — regenerate instead, `OPEN.md`).
- 📓 Large databanks are slow to sync — XAUUSD `WFM` took **826 s**. A databank only partially loaded
  in memory gets pruned down to that partial set. This is a second, separate shrink mechanism, and it
  hits databanks no `ClearDatabanks` touches.

- 🔬 **A sync only touches the databanks that were loaded. One nobody opened is not pruned — it is
  not in the sync at all.** This narrows the headline rule above, which is too broad as stated, and
  it was established by reading the custodian's own log for 2026-09-23
  (`SQX_w2/user/log/StrategyQuant/log_2026_09_23.log`):

  | evidence | what it shows |
  |---|---|
  | **26 `removed` fields in the whole day, every one `removed 0`** | nothing was pruned all day, across ~9 start/stop cycles |
  | **22 `Synchronizing databanks to files` events, ~9 `StrategiesSaver` lines** | most syncs wrote nothing, because nothing was loaded. A sync with no loaded databank logs the header and `Synchronization finished.` with no databank line between them |
  | the 07:20–07:33 cycles loaded only `bench_smt` and `smoke_keltnerUpperCrossUp` | `Retester/RetestOut` never entered memory in those starts and kept its **962 `.sqx`** through all of them |
  | `Retester/RetestOut saved - files before sync 962 / after sync 962 / removed 0 in 21.95 s` at 06:48 | the one cycle that *did* load it round-tripped it intact |

  **So the loss mechanism is narrower than "any sync while the files are not in memory".** It is a
  databank that gets **loaded and then emptied or only partly filled**: the `ClearDatabanks` case
  and the partial-load case above, which are exactly the two examples this file already carried.
  The USDJPY line at the top — `before sync 248 / after sync 36 / removed 248` — is the first of
  those, not a sync of something untouched.

  ⚠️ **This is a narrowing, not an all-clear**, and the practical rules do not move: a batch left on
  a worker is still destroyed by anything that loads it and then clears it, the custodian's
  no-commands-between-start-and-collect discipline still earns its place, and the snapshot is still
  the safety net. What changes is only that another session starting that install for unrelated work
  does not, by itself, endanger a databank it never opens.

  🤔 Corrected the same day from a first reading that called the survival luck. It was not: the
  files were never a candidate for pruning. Worth recording because the wrong version is the
  intuitive one.

- 🔬 **`-databank` verbs move data in opposite directions and none is as read-only as it sounds.**
  `action=count` syncs **from** files and destroys what `action=load` put in memory
  (`sqx/variants/execute.py`); `action=list` fills memory **from** disk, and a running worker
  answering it logs `Loaded 30 strategies`; `action=export` reads memory and is the safe reader.
  Which one you reach for decides whether a restart preserves or discards.

**Before anything that restarts SQX: snapshot `user/projects` at the file level.** It is a complete
safety net, because the loss is always disk-files-versus-memory.

🔬 **Exclude `<project>/log/` from the snapshot.** The 2026-09-21 snapshot is 4.5 GB, and 1.03 GB
of it is ten `global_log_*.log` files (one of 566 MB) that hard rule 1 does not protect and that
`sqx/export/archive_logs.py` does not cover either (it archives `user/log`, not the projects' own
`log/`). Without them a master snapshot is ~3.5 GB. Use `rsync -a --exclude='log/'`.

🔬 **A snapshot cannot be deduplicated against the live master or against the next snapshot.**
Two days after the 2026-09-21 copy, 7,402 of the master's 7,546 `.sqx` differed in size and mtime:
SQX rewrites every file on sync, even when nothing changed. `--link-dest` and hashing gain nothing;
the only lever is what a snapshot includes.

🔬 **A snapshot is deleted once the restart it guarded is verified** (owner, 2026-09-23). Checked
that day: the 2026-09-21 copy (7,546 `.sqx`, 3.5 GB) held **no file and no databank count** the
live master did not, and the worker's 66 were rebuildable projects of ours. `AlgoData` is for data,
not an ark: take the copy, do the restart, compare counts per databank (`projectsBackup/
install-configs-2026-09-21/count_sqx.sh` does it with `find -print0`), delete the copy.

## Memory vs disk also bites the exporter

🔬 **A databank set to `Auto-sync never` can hold records in memory and have an empty directory on
disk.** XAUUSD `Results` showed **36 records** via MCP while `user/projects/XAUUSD/databanks/Results/`
held **0 `.sqx`**. Any file-based export (`orderstocsv` takes a path) therefore sees nothing, while the
GUI shows a full databank.

- Every `-databank` verb that could fix this (`synctofiles`, `save`) needs the instance that holds the
  project — the master — and the master's CLI is unavailable while its GUI is up. There is no
  code-only route to a never-synced databank's strategies.
- 🔬 **Look for the same strategies downstream instead.** XAUUSD task 4 retests `Results` → `OOS`, and
  `OOS` auto-syncs hourly: its 36 on-disk `.sqx` were the *identical* strategy set (verified by
  name-set equality against `list_strategies` on `Results`). Run `dump_project.py <PROJECT>` to see
  which downstream databank carries a synced copy.
- ⚠️ The downstream copy is the **retested** strategy, so its stored main result covers whatever window
  that retest used — here 2008–2022 with an IS/OOS split, not the builder's 2008–2017.

## A new databank can sit at "Auto-sync every 1 hour" and still have nothing on disk

🔬 2026-09-05, XAUUSD. `OOS-Sharpe` reported **9,997 records** and `syncType: Auto-sync every 1 hour`
through MCP `list_databanks`, while `user/projects/XAUUSD/databanks/OOS-Sharpe/` **did not exist** —
same for `Results-Sharpe` (10,000 records). The master had been up 1d21h, so many hourly ticks had
passed. The label describes the databank's setting, **not** evidence that a sync has ever run for it.

- Practical consequence: `exportdrv.stage()` copies from the master's on-disk directory, so a
  metrics export of such a databank silently stages **0** strategies. Always `ls` the directory
  before exporting a databank you have not exported before — the MCP record count will not warn you.
- 🔬 The owner syncing it by hand from the GUI wrote all 9,997 `.sqx` to disk within a minute, and
  the reference `OOS` kept its 10,000 through that sync. Asking him to sync is the working route;
  there is still no code-only one while the master's GUI is up.

## The custodian role — how the sync rule stops being a permanent risk

Decided 2026-09-21, alongside the three-install topology (`knowhow/03-driving-sqx.md`).

Hard rule 1 — *every sync deletes on-disk `.sqx` not held in memory* — is usually described as
something to be careful about. It can instead be designed away, because **the rule is per install**.

**The condition, and it is the whole of it:** the install holding a large databank receives **no
command between "start" and "collect"**. Not a `-databank action=count`, not a `-project
action=status`, not an export of something else. Any of those can trigger the sync that prunes disk
down to whatever memory happens to hold.

That is impossible to guarantee with a single worker, because the same worker is also the one
answering every other request. With a dedicated **custodian** (`SQX_w2`, port 5070) it is guaranteed
by construction, and the **conductor** (`SQX_w1`, port 5060) absorbs everything else.

Two corollaries worth stating, because both have already cost work:

- ⚠️ **Only the install that holds a databank can export it.** A `-databank` verb addresses that
  instance's own projects. So the 5,000 variants are exported by W2, not W1 — which is also why W1
  can stay small (16 GB) while W2 is large (48 GB).
- ⚠️ **Opening a worker's GUI triggers syncs**, and it must never run at the same time as that
  install's CLI daemon. With a 5,000-variant databank inside, opening it is the USDJPY log scenario
  (`before sync 248 / after sync 36 / removed 248`). Inspect **before** fabricating or **after**
  collecting — never in between. 🤔 Inferred from the master's behaviour; not verified on a worker.

## 🔬 Curating a databank: the CLI selector does not work, files do (2026-09-23)

Measured end to end on the custodian against a 30-strategy databank. The question was how a Python
verdict removes strategies from SQX so the next task only sees the survivors.

**`strategies=` is unreachable from either CLI path.** Both report success and change nothing:

- 🔬 **Over the worker's HTTP API the name is cut at its first space.** Every SQX strategy is called
  `Strategy 11.3.25`, and the server splits the command on whitespace (hard rule 6). `%20`, `+`,
  `%2520` and `"quotes"` were all tried: the count never moved. `action=delete` answered
  `Reports removed.` each time.
- 🔬 **A one-shot `sqcli -databank …` never loads the records.** `action=save` with **no** selector
  wrote **0 of 30** files while answering `Reports saved.` So the verb acts on an empty memory. A
  running worker does load them — a `-databank action=list` prints `Loaded 30 strategies` — which
  is why the HTTP path at least sees the databank.
- ⚠️ **`action=move` with a selector that does not arrive moves the WHOLE databank.** Naming two
  strategies moved all thirty. There is no partial failure and no error.

**What works: move the files with the install stopped.** SQX syncs a databank *from* files on its
next access, so the curated directory becomes memory:

```bash
# install stopped
mv "<install>/user/projects/<P>/databanks/Results/Strategy 11.3.36.sqx" \
   "<install>/user/projects/<P>/databanks/Rejected/"
# start it
-databank action=list  →  Loaded 27 strategies to databank Results
```

Verified 30 → 28 → 27 → 24 across four rounds, each confirmed by the record count SQX reports after
the restart. `sqx/curate/apply_verdict.py` does this, with a snapshot outside the install first.

🔬 **A destination databank can be created over the API, or by `mkdir` alone**, and a restart picks
both up: `Rejected` was created with `-databank action=create` on the worker and carried its records
after the next start. The older note that it had to be made in the GUI does not hold here.

🔬 **Rejects are deleted after a record, and the name is checked against a hash** (2026-09-23,
conductor, `Retester/Results`, 66 → 34 → 33). Each `.sqx` weighs ~5 MB (32 → 158 MB), so keeping
8k rejects of 10k would be 40 GB per cut, and a `Rejected` databank inside the project is worse:
SQX loads every databank of a project on start, so they would cost RAM too. The owner's decision:
`apply_verdict` writes `before-<stamp>.csv` (name, identity, bytes, verdict and reason of everything on disk)
and `rejected-<stamp>.csv` (the dropped rows of the metrics export) beside the verdict under
`reports/<P>/<bank>/<day>/curate/`, then unlinks the files. A cut's record is ~56 KB. The verdict
carries `identity` = SHA-256 of the inner `strategy_Portfolio.xml`: a file swapped under a judged
name (`Strategy 11.10.85(1)` replaced by another strategy) is caught in the dry run and nothing
is touched. Names are not identities — this export already had 5 `(1)` collisions in 66. Two
earlier versions the same day copied the whole databank first (50 GB per cut at 10k) and then
moved rejects to `AlgoData/rejected/`; both are gone.

📓 **`-databank action=synctofiles` exists** and forces memory → disk (`knowhow/03-driving-sqx.md`
records it for the equity harvest). An earlier note in this project claimed no verb forces a write;
that was wrong. It is the opposite direction from the one curation needs, which is disk → memory.

## Dropping tasks with `--only` leaves the survivors reading the wrong databank

🔬 2026-09-23. Each task carries `<Databank label="Input databank" name="Input" value="…">` and an
`Output` beside it, and SQX matches them **by string against `config.xml`** — a name no `<Databank>`
declares is silently ignored, not an error. The chain is therefore only correct for the tasks the
donor shipped, in the order it shipped them.

Keep a subset with `builder --only` and the survivors still point where they used to. Measured on a
three-task clone of the XAUUSD donor: the additional-markets task read **`Retest Markets - Family`,
its own output**, so the cross-market check would have run over an empty databank and passed
everything for free. Nothing announces it — the task runs, writes a result, and tests nothing.

`sqx.projects.databanks.chain_databanks` now threads it: each task's `Input` becomes the previous
task's `Output`, in `config.xml`'s own `<Task>` order, and `builder --json` reports the result as
`chain` with what each task read before. The correct wiring for the build → OOS → cross-market chain
is:

| task | reads | writes |
|---|---|---|
| Build | — (see below) | `Results` |
| Retest (OOS) | `Results` | `OOS` |
| Retest (additional markets) | `OOS` | `Retest Markets - Family` |

📓 **The first task's input is left alone on purpose.** There is no previous output to hand it, and a
Build on `generationType="genetic-evolution"` seeds from the system databanks (`Initial population`,
`Strategies to improve`), not from its `Input`. The donor ships `Results-Rexpect` there, which no
project declares — and so do the owner's own master projects: `XAUUSD` and `TestXAUUSD2` carry
`Results-Rexpect`, `USDJPY`, `EURUSD` and `AUDJPY` carry `Retest Markets IS`, `SP500_H1` and the five
`XAUUSD_Breakout_H1` build tasks carry `null`. Six of his eleven build tasks point at a databank that
does not exist, the builds run, and `XAU_ISOOS_ejemplo` produced 120 strategies with the phantom in
place. It is his configuration and it is inert; nothing here changes it.

## Un databank con espacios en el nombre es inalcanzable por la API HTTP (2026-09-23)

- 🔬 `-databank action=count project=P name=Retest Markets - Family` responde
  **`Error: Databank 'Retest' doesn't exist.`**: el nombre se corta en el primer espacio, igual que
  el selector `strategies=`. **`%20` no lo arregla** — probado. `action=load` falla igual.
- 🔬 **La vía que sí funciona es la de ficheros**, la misma que usa `/curate`: con la instalación
  parada, copiar los `.sqx` dentro de `user/projects/<P>/databanks/<nombre con espacios>/` y
  arrancar. El log lo confirma: `Loaded 9 strategies to databank Retest Markets - Family`.
- 📓 Cuatro de los siete databanks del donante llevan espacios (`Retest Markets - Family`,
  `MC Trades`, `Last generation`, `Initial population`). Cualquier herramienta que los direccione
  por la API los pierde en silencio.
