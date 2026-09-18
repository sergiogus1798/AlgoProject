# Acceptance conditions — reading them correctly

🔬 **Three shapes exist, not two.** A parser must handle all of them — `core/cfx.py` does:

```xml
<!-- acceptance conditions -->
<Condition use="true">
  <Left-Side><Column-Value column="ProfitFactor" resultType="WalkForwardMatrix" subresult="30"/></Left-Side>
  <Comparator value="&gt;"/>
  <Right-Side><Numeric-Value value="1.20"/></Right-Side>
</Condition>

<!-- GoToTask conditions - completely different -->
<Condition type="ResultsCount">
  <Field type="databank">Retest Markets - OOS</Field>
  <Field type="comparator">&lt;</Field>
  <Field type="number">1000</Field>
</Condition>
```

**Third shape, found 2026-09-03**: 🔬 the right side can be a `Column-Value` too, not only a
`Numeric-Value`. SPP tasks use it to compare a permuted result against the strategy's own main result:
`NetProfit(OptProfileSysParamPermutation) >= NetProfit(main)`. A parser that assumes `Numeric-Value`
on the right crashes on the XAUUSD WFM and SPP tasks.

- 🔬 **`use="false"` conditions stay in the file.** Always check the attribute — a threshold in a
  disabled condition gates nothing.
- 🔬 Counted 2026-09-03 with `core/cfx.py` across the whole XAUUSD project: **138 `Condition` elements
  in 16 tasks, 101 of them active**, counting every nested crosscheck block. The Build task alone
  holds 49, of which 24 are active. An earlier note claiming 13 conditions in the Build task was
  counting only one block of them.
- 🤔 **`subresult=30` is the raw metric; `subresult=31` appears to be a percentage of matrix
  combinations passing.** Inferred from its pairing with `format` (`Decimal2` vs `Decimal2Pct`). It is
  what makes `ProfitFactor >= 60` sensible rather than absurd. **Not confirmed** against SQX's enum
  table.
- 🔬 `sampleType` **is** decoded: **10 = IS, 20 = OOS, 127 = full period** (see `04-export.md`).
  `plType` (10, 20) is still undecoded.
- 🔬 Watch for a condition reading `resultType="WalkForwardOptimization"` inside a task where that
  cross-check is `use="false"` — XAUUSD's WFM task does exactly this.

### Which window a strategy was selected on — read it before calling anything out of sample

🔬 Measured 2026-09-17 on `XAUUSD/project.cfx`, `Build-Task3.xml`, counting only `use="true"`
conditions: selection touches **every** window of the sample, not just the in-sample one.

| resultType | sampleType | active conditions |
|---|---|---|
| `main`, `WhatIf`, `RetestWithHigherPrecision`, `MonteCarloRetest` | 127 (full 2008–2022) | 8 |
| `WalkForwardOptimization`, `MonteCarloManipulation` | 10 (IS) | 10 |
| `WalkForwardMatrix` | 20 (OOS) | 2 — `NetProfit > 0` |
| `RetestOnAdditionalMarkets` | 127 | 1 — `ProfitFactor > 1.5` |

Two consequences for any study that wants a clean out-of-sample test:

- The 2018–2022 stretch is **not virgin data** for a databank built by this task. It enters selection
  twice: inside every `sampleType=127` condition, since the full period contains it, and explicitly
  through the walk-forward matrix's OOS net profit. 🔬 Measured on the 30-strategy sample of
  `Retest Markets - Family`: **30 of 30 are profitable on gold over 2018–2022** — the shape a
  selected window has, not the shape an unseen one has.
- The additional markets of a retest can be a selection filter too, through
  `RetestOnAdditionalMarkets`. Check which task wrote the databank being analysed before reading a
  cross-market result as untouched evidence.

🔬 **Where the untouched data starts: 2023-01-01.** Every `dateTo` in the build and retest tasks is
`2022.12.31`, so no condition in the project has ever read a bar after it, while the bar files run to
2026-01-16 (XAUUSD, XAGUSD) and 2026-06-01 (BRENT). A retest over 2023-01-01 → today is the only
window of this project that is out of sample in the strict sense, for the base asset and for the
additional markets at once.

A p-value computed inside a selected window is still a valid statement *about that window's
mechanics* — e.g. "the entry timing beats a random placement here" — but it is not a statement about
unseen data, and across a population of selected strategies it is biased low.
