---
name: oos-gate
description: Close the loop between an OOS retest and the next SQX task — harvest the two databanks into Python, run the gate's screens, and put the verdict back so the next task only sees the survivors. Stops and restarts installs and deletes rejected strategies. Use when the owner asks to screen, filter or cull a population after its out-of-sample retest, to apply a Python verdict to a databank, or to prepare the survivors for the cross-market test.
---

# /oos-gate

Build → retest → **this** → the next task. Python decides, SQX obeys.

```
Results (IS)  ┐                                              ┌ verdict.csv ┐
              ├─ gate.harvest ─▶ gate.report ─▶ scorecard ───┤             ├─▶ curate ─▶ next task
OOS (retest)  ┘   join on identity   seven screens           └ resumen.md  ┘
```

Two databanks, not one. SQX charges one spread and one slippage per backtest and these windows
are years long, so the build and the retest are separate tasks with separate costs — and separate
databanks. The harvest is what joins them.

## 1 · Harvest, with the install stopped

```bash
bin/sqx-worker.sh --role custodian stop
python3 -m gate.harvest --project <P> --databank Results --oos-databank OOS --role custodian
```

**Pairs on identity, not on name.** SQX renames on collision and two databanks of one project can
hold different strategies under the same name; the identity — the SHA-256 of the inner
`strategy_Portfolio.xml` — is stable across databanks. A strategy in the build with no twin in the
retest is dropped: SQX already judged it, by its own red flags.

That drop happens **before** anything is exported, so nothing is spent on the dead. In one run 689
of 694 died there and 5 were exported.

## 2 · The screens

```bash
python3 -m gate.report --project <P> --databank Results --feed <FEED>
```

`gate/config.yaml` holds the screens as data — order, kind, threshold, and why each exists — so the
owner's UI edits that file and not this skill. Read the funnel out loud: **how many each screen
killed** is the finding, not the survivor count.

Two things that are easy to get wrong when reporting:

- **The thresholds are deliberately loose** and were set to measure what each screen kills before
  any of them is tightened. A cut made under them is a statement about the threshold, not about the
  strategies. Say so.
- **`redundancia` is `soft`**: it groups and names, it does not drop. Do not report its groups as
  rejections.

## 3 · Put it back — `/curate`

The gate writes one `verdict.csv` per databank. Applying it is `/curate`, which owns that half:
the guards, the record written before anything moves, and the count back afterwards. Follow it.

Two of its rules matter most here and are the ones skipped under time pressure:

- **Look before `--apply`.** The dry run is also where the identity check happens.
- **Count back after restarting.** `-databank action=count` is the only place SQX says what the
  next task will really read.

## 4 · Hand over

The next task in the chain is the cross-market retest — `/crossmarket`. It reads the databank this
left behind, so the handover is just that databank's name and its count.

## Do not

- Run any of this while the custodian is working. One job at a time.
- Curate a databank a task is writing.
- Report a survivor count as a result. The population that entered, what each screen removed, and
  on which threshold — that is the result.
