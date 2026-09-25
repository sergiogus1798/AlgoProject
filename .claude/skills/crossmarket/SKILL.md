---
name: crossmarket
description: Retest surviving strategies on other markets with SQX's Retest on additional markets cross-check — the markets from assets/_markets.yaml, each over its own window and at its own declared costs. Configures and runs a task on the custodian. Use when the owner asks to test an edge on other markets, to run the cross-market or crossmarket retest, or asks which markets an asset is checked against.
---

# /crossmarket

The task after the OOS gate. It asks one question: **does this logic survive a market it was never
fitted to?**

## The markets are already chosen, and that is the point

```bash
python3 -m sqx.projects.crossmarket <SYMBOL>
```

They come from `assets/_markets.yaml`, per main asset, in two categories:

- **`family`** — the same economic driver. The easy test: passing proves little, failing says a lot.
- **`structural`** — the same *shape* of market (volatility, session, noise) with no shared driver.
  The hard test: passing here means the logic caught something about how price moves.

⚠️ **The list is fixed before any result is looked at.** Never add a market because it looked
promising, and never drop one because it did not: that turns the test into a selection and its
p-values into decoration. If the universe is wrong, the owner edits the file first.

## The window is each market's own

`assets/_build.yaml` declares it once for every asset, under `crossmarket.segment`: **`build..oos1`**
(owner, 2026-09-24), the same two-dot notation the MC Retest uses. That means from the main asset's
**build start** — or from that market's first bar, whichever is later — to the end of `oos1`. For XAUUSD: XAGUSD runs 2008–2022, and a market whose data starts in 2013 runs
2013–2022. The whole history is used on purpose; cutting it to the main asset's window throws away
the years that would answer the question.

## The costs are each market's own, and they are not copied from anywhere

Every extra market gets its own `<Setup>` inside the cross-check, with its own spread, slippage,
commission method and swap, read from **its own** `assets/symbols/<SYM>.yaml`.

The command **refuses to write anything** when a declared market has no file in `assets/symbols/`.
That is the point of the refusal: SQX would run it happily at whatever default the instrument
registry carries, and a cross-market result at an invented cost is worse than no result. Report the
list to the owner and ask — hard rule 5.

One Setup carries one spread while the window spans both segments, so the **OOS** figures are
charged. The market that has to surprise us is never given the cheaper price.

`<MainTestValues>` says what comes from the main test instead: the timeframe, the precision and the
minimum distance are shared; the dates, spread, slippage, commissions and swap are the market's own.
The session is inherited, because `assets/` declares no session for a cross-check market — say so
when reporting rather than choosing one.

## Set it up and run it

```bash
python3 -m core.assets <SYMBOL>                          # hard rule 5, blocking
python3 -m sqx.projects.builder <P> --timeframe <TF> --symbol <SYMBOL> --role custodian \
    --template <plantilla> --tasks Build,Retest --only <build>.xml,Retest-Task3.xml
python3 -m sqx.projects.crossmarket <SYMBOL> --cfx <install>/user/projects/<P>/project.cfx \
    --task Retest-Task3.xml --timeframe <TF>
```

`Retest-Task3.xml` is the donor's additional-markets task; it reads and writes
`Retest Markets - Family`. Then start the custodian, `action=start`, poll, stop — the run half is
`/template-run`, and its rules hold here: `start` and never `startOnlyTask`, `action=stop` before a
second start, one job at a time, always end stopped.

## What the result means

**Nothing is filtered here.** `crossmarket.conditions: []` in `assets/_build.yaml` is the owner's
decision (2026-09-24), and the command enforces it: every acceptance condition of the cross-check is
switched off and `DeleteFailedStrategies` forced to false, and it prints how many it silenced. The
donor brought one live — `ReturnDDRatio > 1` on the first market — and with a live condition SQX
does not write the failing strategy into the output databank, which leaves the Python analysis
without the dead ones: the half of the evidence that says *which market killed which strategy*.
SQX runs the backtests; the verdict is taken in Python and applied with `/curate`.

🤔 With zero live conditions, `<MinConditions>` and `<MinMarkets>` are inert and are left untouched.
Check on the first real run that the output databank holds every strategy the input had, and write
what you saw into `knowhow/conditions/crossmarket-crosstf-no-conditions.md`.

**A strategy that fails here is not necessarily broken, and one that passes is not validated.** The
family test shares a driver with the main asset, so passing it may only mean the two markets are
the same trade. Say which category each market belonged to when reporting the counts.

## Do not

- Add, drop or swap a market based on what the results looked like.
- Write a cross-check for a market whose costs are not declared.
- Run it on a population that has not been through `/oos-gate`. This task is expensive and the
  gate is what makes it affordable.
