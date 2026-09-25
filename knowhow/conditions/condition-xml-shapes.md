---
q: parse acceptance condition XML; Condition shapes Column-Value Numeric-Value GoToTask ResultsCount; use="false" disabled condition; subresult sampleType plType; condition count XAUUSD
tag: 🔬  date: 2026-09-24  see: conditions/wfm-acceptance, conditions/active-conditions-in-crosschecks, export/databank-metrics-is-oos
---
# Conditions come in three XML shapes; always check `use=`
A parser must handle all three (`core/cfx.py` does): acceptance (`Left-Side`/`Comparator`/`Right-Side`),
GoToTask (`type="ResultsCount"` with `<Field>`s), and acceptance whose right side is a `Column-Value`.
`use="false"` conditions stay in the file and gate nothing. `sampleType`: 10 IS · 20 OOS · 127 full. `subresult`: 30/31/32/33 → `conditions/wfm-acceptance`.

## Evidence
```xml
<Condition use="true">
  <Left-Side><Column-Value column="ProfitFactor" resultType="WalkForwardMatrix" subresult="30"/></Left-Side>
  <Comparator value="&gt;"/>
  <Right-Side><Numeric-Value value="1.20"/></Right-Side>
</Condition>
<Condition type="ResultsCount">   <!-- GoToTask -->
  <Field type="databank">Retest Markets - OOS</Field>
  <Field type="comparator">&lt;</Field>
  <Field type="number">1000</Field>
</Condition>
```
- Third shape: SPP compares permuted vs own main result, `NetProfit(OptProfileSysParamPermutation) >= NetProfit(main)`.
  Assuming `Numeric-Value` on the right crashes on the XAUUSD WFM and SPP tasks.
- XAUUSD project (`core/cfx.py`, all nested crosscheck blocks): 138 `Condition` in 16 tasks, 101 active; Build task 49, 24 active.
  Not: "13 conditions in Build" (counted one block).
- `plType` (10, 20) meaning still undecoded (WFM reads default 10).
- A condition can read `resultType="WalkForwardOptimization"` inside a task where that cross-check is `use="false"` — XAUUSD's WFM task does.
