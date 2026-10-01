---
name: sqx-spp
description: Configure a System Parameter Permutation (SPP) cross-check on a StrategyQuant X retest task, with the owner's standing defaults — max 10,000–15,000 runs (never exhaustive), ±35–40 % range, ~4 % per step, and Recommended parameters only. Use when the user asks to set up, run or fix an SPP, a parameter permutation, or a robustness reconnaissance on a strategy, or when a task's cross-check block has to be built or audited.
allowed-tools: Bash(python3:*), Read, Write, Edit, Glob, Grep
---

# sqx-spp — configure a System Parameter Permutation properly

An SPP re-runs a strategy over a grid of parameter values around the ones it was built with, and
leaves an **optimization profile** on the strategy: one row per permutation. It answers *does this
strategy sit on a plateau or on a spike?* Everything downstream — the design grid, the variant
study, the walk-forward correlation — is built from that profile.

## The four rules. Each one has been got wrong once.

### 1 · SPP is `OptProfileSysParamPermutation`. It is NOT `SequentialOptimization`.

They sit side by side inside the same `<CrossChecks>` block of a retest task, and both talk about
permuting parameters:

```xml
<CrossChecks use="true" evaluateAll="false">
  <RetestOnAdditionalMarkets use="false">
  <WalkForwardOptimization use="false">
  <RetestWithHigherPrecision use="false">
  <MonteCarloRetest use="false">
  <WalkForwardMatrix use="false">
  <MonteCarloManipulation use="false">
  <OptProfileSysParamPermutation use="true">   ← THIS IS THE SPP
  <WhatIf use="false">
  <SequentialOptimization use="false">          ← this is NOT
```

`SequentialOptimization` walks parameters one at a time hunting for a better setting. Different
question, different cost, and **it writes no optimization profile**. Turning on the wrong one costs
hours and produces nothing: measured at 47 cores for 91 minutes with an empty result.

### 2 · `MaxTests` must be SET, never inherited. Exhaustive is not an option.

```xml
<MaxTests>1000000001</MaxTests>   ← SQX's sentinel for EXHAUSTIVE. Every combination.
```

A donor task can carry it, and on a real strategy that is not a long run, it is an unbounded one.
**Default 15,000. Never above it unless the user names a number.** 10,000 is equally fine.

### 3 · Range ±35–40 %, and about 4 % per step.

`Steps` is not chosen directly — it follows from how finely you want to walk the range:

```
Steps = round(2 * spread / step_pct)      ±35 % at 4 % → 18      ±40 % at 4 % → 20
```

±30 % is too narrow and 12 steps (5 % each) is too coarse; both appear in donor tasks and neither is
the default.

### 4 · `WhatToParametrize` = Recommended parameters, and nothing else.

```xml
<WhatToParametrize type="0" symmetricVariables="false">
  <Recommended>true</Recommended>
  <Periods>false</Periods>      <Shifts>false</Shifts>
  <Constants>false</Constants>  <OtherParams>false</OtherParams>
  <EntryParams>false</EntryParams>   <EntryLogic>false</EntryLogic>
  <ExitParamsUsed>false</ExitParamsUsed>  <ExitParamsUnused>false</ExitParamsUnused>
  <BooleanParams>false</BooleanParams>
</WhatToParametrize>
```

`type="0"` is the Recommended choice; `type="1"` is hand-picked families. Hand-picking permutes
things the strategy does not key on and inflates the run for nothing.

## Everything else must MATCH the strategy

The SPP block is the only part you set. The in-sample / out-of-sample window, the Friday close, the
money management, the exits, the spread and the slippage all have to be **what these strategies were
actually built with** — so the task is built by copying one the owner already uses, and only the
cross-check block and the databanks are replaced. Never hand-assemble a task.

## Doing it

`sqx/variants/harness.py` in the AlgoProject repo implements all of the above:

```bash
python3 -m sqx.variants.harness --kind spp_is --project Test_XAUUSD --output SPPOut \
  --chart "XAUUSD_M1 M30 5" --spp
# defaults: --spp-spread 35  --spp-step-pct 4  --spp-max-tests 15000
```

It refuses to write while the install is up — SQX rewrites `project.cfx` on exit, so an edit made
against a running instance is lost in silence.

## Verify, always

Ask SQX what it actually loaded rather than trusting the file you wrote:

```bash
python3 -c "from core import worker; print(worker.call('-project action=saveconfig \
name=Test_XAUUSD file=/tmp/live.cfx', role='custodian'))"
```

then read `/tmp/live.cfx` and check: exactly one cross-check `use="true"`, `MaxTests` ≤ 15000,
`DistributionUp/Down` 35 or 40, `Steps` consistent with 4 %, `WhatToParametrize type="0"` with only
`Recommended` true.

## What an SPP costs, so nobody reads silence as a hang

It logs once per parameter in the first seconds and then says **nothing** until it finishes;
`-project action=status` reports `Total tested 0` throughout. There is no per-permutation progress
in SQX. The honest signal is the JVM's resident memory: climbing means working, flat means hung.
Memory, not time, is the binding constraint — never run two SPPs on one install.
