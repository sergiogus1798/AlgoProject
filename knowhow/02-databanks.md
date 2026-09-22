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

**Before anything that restarts SQX: snapshot `user/projects` at the file level.** It is a complete
safety net, because the loss is always disk-files-versus-memory.

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
