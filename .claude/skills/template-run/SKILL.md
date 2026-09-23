---
name: template-run
description: Build an existing strategy template on a market — set up the project, run it on the custodian, check the strategies really carry the template's fixed block, and record the run. Touches live installs and burns CPU. Use when the owner asks to try, run, test or build a template on a symbol or timeframe, or asks whether one has been tried there already.
---

# /template-run

This one starts SQX and spends cores. Everything here has a cost; the authoring half is
`/strategy-template`. Defaults and the owner's contract: `sqx/templates/README.md`.

## Before anything — two lookups that cost nothing

```bash
grep <template> ~/Desktop/AlgoData/templates/runs.csv      # has it been tried here already?
python3 -m core.assets <SYMBOL>                            # hard rule 5
```

The preflight is the source of every number in the project. **Read its output back to the owner**:
the costs, their units, the segment windows, and what it flags. Its exit code decides whether there
is a run at all — `2` a cost with no agreed value, `3` a broken schema or a feed SQX does not hold,
`0` go. Never pick a value it says is undecided.

Two things it prints that are easy to skim past:

- **PROVISIONAL.** A working figure the owner put in, not one agreed with the broker. It does not
  block, and it stamps every result: say so when you report.
- **The MC Retest ranges.** Undecided ones do not block either, but that task is uninterpretable
  until they are set — SQX's factory `1.0–5.0` is the same on every instrument and is meaningless
  at any scale but forex's.

## The install that builds must hold the blocks

```bash
python3 -m sqx.inspect.vocabulary --diff custodian
```

A gap here is the failure that looks like success: the build runs and the template is quietly
ignored. If blocks are missing, install them (`python3 -m sqx.blocks.install … --role custodian`)
with the install stopped.

## Set the project up — one command

```bash
python3 -m sqx.projects.builder <name> --template <library>/template.sqx \
    --symbol <SYMBOL> --role custodian --max-strategies <n> --minutes <m> [--json]
```

That is the whole setup. It clones the frozen donor, keeps only the Build task, installs the
template under its library name, forces `StrategyType type="template"`, applies the caps, switches
every output databank off `Auto-sync never`, and dates the window from `assets/`. Each of those was
a hand-edit of the task XML until 2026-09-23, which is what kept this chain out of an application.
`--json` emits the same result as data.

It refuses, rather than producing something that fails later: a name with whitespace, a template
that is not there, a cost still at `use: null`, an install that is up, and a task where the template
would be **ignored**.

⚠️ **A worker cannot be priced from `assets/` today — say so, do not pretend otherwise.**
Measured 2026-09-23, three ways, all closed: a task whose `<InstrumentInfo>` differs from SQX's
registry refuses to start (*"Project has unresolved resources"*, any attribute, any value); the
registry itself lives in `user/data/data.db`, which **every worker start copies from the master**,
so an `-instrument action=edit` is wiped; and the validation uses the registry as loaded at
startup, so editing it mid-session changes nothing either. The only place that decides is the
**master's** instrument list, and that is the owner's.

`builder` prints the gap before building — slippage, commission method and swap all differ on
XAUUSD today. **Report it with the result**: the run is priced with the master's figures, not the
declared ones, and every number it produces carries that.

## The cross-check markets come from `assets/` too

A retest across markets asks which markets. They are declared, per main asset, in
`assets/_markets.yaml` and printed by the preflight:

```
- retest family: XAGUSD_DukasM1_Infinox, BRENTCMDUSD_ftmo
- retest structural: (vacío)
```

`family` shares the main asset's economic driver — the easy test, where passing proves little and
failing says a lot. `structural` shares only the shape of the market — volatility, session, noise —
with no common driver, and is the hard test. **The list is fixed before any result is looked at**:
choosing markets after seeing where the strategies work turns the test into a selection. Never add
one to a cross-check task because it looked promising; if the universe is wrong, the owner changes
the file first.

## Run it

```bash
bin/sqx-worker.sh --role custodian start
python3 -c "from core import worker; print(worker.call('-project action=stop name=<P>','custodian'))"
python3 -c "from core import worker; print(worker.call('-project action=start name=<P>','custodian'))"
```

- **`action=start`, never `startOnlyTask`** — the latter reports success and tests nothing. `start`
  runs the whole chain, which is safe only because this project is a single task.
- **`action=stop` before every second `start`.** A second start on a project that already ran does
  nothing, silently, forever.
- Poll with `-project action=status` and `-databank action=count`. The custodian takes **one job at
  a time and no other command between start and collect** — that is what makes rule 1 stop existing
  for the databank it is holding.

Then `bin/sqx-worker.sh --role custodian stop`. The shutdown sync is what writes the strategies to
disk. Always end stopped.

## Check it actually applied the template

The only check that matters, and the one nobody runs:

```bash
python3 -m sqx.inspect.template_check --role custodian <PROJECT>
```

`--role` is load-bearing: without it the tool looks in the master, which knows nothing of a project
built on a worker. On the master's nine projects — all `type="simple"` — the answer is **0 of 642**;
on a task declaring `type="template"` it is all of them, measured **30 of 30**. So this is the
proof, not the detector: the detector is the static attribute check above, before the CPU is spent.
Report the number, not an impression.

## Record it

```bash
python3 -m sqx.templates.registry --run --set template=<name> --set symbol=<SYM> \
    --set timeframe=<TF> --set project=<P> --set date=<date> \
    --set strategies_built=<n> --set strategies_kept=<n> --set report=<path>
```

One row per (template, symbol, timeframe) — that is what answers "have I tried this on NASDAQ H1".
If the strategies carried the fixed block, also flip the template's `status` to `buildConfirmed`.

## Do not

- Build on the master, or on the conductor. Builds go to the custodian.
- Leave a worker running.
- Call a smoke build evidence about the strategy. It proves the chain, not the idea.
