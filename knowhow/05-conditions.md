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
