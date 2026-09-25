---
q: does a retest rewrite inherited SQStats, retested variant own results, IS and OOS in one retest run, startOnlyTask tests nothing Total tested 0, disabled cross-check symbol error, loadconfig merges on exit, origin variant reference
tag: 🔬  date: 2026-09-22  see: sqx-format/five-member-sqx, sqx-format/oos-range-marker, sqx-format/loaded-name-is-filename, sqx-drive/running-a-task-headless
---
# A retest rewrites the inherited SQStats: the variant chain is sound
Retested five-member variants return their own numbers. One run with `<OutOfSample><Range/></OutOfSample>`
returns samples 10 and 20 together. Compare a variant only with the **retested origin** (`P00000`),
never with the inherited figure. Every `<Chart>` in a task must name a symbol the install has, even with
cross-checks off — else the task silently tests nothing.

## Evidence
- 11 variants of `XAUUSD/Strategy 17.9.39`, custodian (W2, 5070), one `action=start`. Before: all controls
  = parent (22650.2, 755 trades, PF 1.15). After:

  | variant | `DICrossPeriod1` | NP IS | trades IS | NP OOS | trades OOS |
  |---|---|---|---|---|---|
  | `P00000` origin | 67 | +26,138.78 | 755 | +14,622.08 | 423 |
  | `P00001` | 43 | +43,647.37 | 1077 | −6,988.39 | 588 |
  | `P00002` | 94 | −33,472.63 | 843 | −12,962.25 | 497 |
- 🤔 Origin: same 755 trades, different P&L vs inherited 22,650.2 → costs/precision differ, not rules.
  Hence `origin` is a stratum, fabricated and retested like any point.
- Inert-pair control: `P00004` differs only in a frozen param → identical row (freezing justified).
  `sqx/variants/collect.py` aborts only when **all** controls are identical.
- Harness was stock `Retester` (1 task, no Build, no `GoToTask`) rewired to the donor's `Retest-Task1.xml`
  (`AlgoData/projectsBackup/XAUUSD_base_2026-09-21/project.cfx`): `Setup` 2008.01.01–2022.12.31,
  `testPrecision 2`, `slippage 0`, `minDist 10`, MetaTrader5 (hedged); `Chart` `XAUUSD_DukasM1_Infinox` M30
  spread 0; OOS 2018.01.01 → 2022.12.31; cross-checks off; all 30 acceptance conditions `use="false"`.
  Backup: `AlgoData/snapshots/2026-09-21/w2-retester-before/project.cfx` (md5 `593ea6ac11eeb600ed7a4e569dd1f910`).
- Earlier attempt: `-project action=startOnlyTask name=Retester task=1` logged `Project started`, then
  `Total tested 0`, `In databank 3`, `Running time so far 0 ms` forever, no error — also for the full
  126 KB parent from `raw/XAUUSD/SPP_IS/2026-09-10/strategies/`, so not the five-member shape.
  `SQX_w2/user/data/History` symlinks the master's (holds `XAUUSD_DukasM1_Infinox_M30.dat`).
  🤔 What fixed it is not recorded; the successful run used `action=start` after the symbol fix below.
- `<CrossChecks use="false">` still logged `ERROR ProjectResources - Error while adding symbol to
  resources - Symbol 'EURUSD_M1_dukas' doesn't exist`, and the task did nothing, without failing.
- `-project action=loadconfig` takes only the task: a `saveconfig` cfx is one `config.xml` holding the task;
  pushed back, the live project lost its databank registrations until stop, when SQX rewrote
  `project.cfx` merged (databanks restored, task kept). Rewrite-on-exit makes `loadconfig` permanent.
- Collision rename `(N)`: see loaded-name-is-filename.
