---
q: MonteCarloRetest task XML; MCR tasks silently run a plain retest; doctrine apply_doctrine turns off crosscheck; MCBacktestPrecision vs testPrecision; MCUseFullSample; MCR task names contract; RandomizeMinDistance; set_crosschecks regex kills conditions
tag: 🔬  date: 2026-09-23  see: costs/mc-retest-ranges, conditions/active-conditions-in-crosschecks
---
# The doctrine switches the MC Retest crosscheck off; `mcretest.py` must re-enable it after
- `doctrine.apply_doctrine()` (`crosschecks.default: []`) sets every unlisted crosscheck `use="false"` → a `sqx.projects.builder` project's 8 MCR tasks silently run a plain retest.
  `sqx/projects/mcretest.py` enables the crosscheck itself, after the doctrine, never before.
- `tasksettings.set_crosschecks()` regex also matches `<Condition use="true">` → every acceptance condition of every crosscheck ends `use="false"`.
  So `RetestWithHigherPrecision` in Build runs with no acceptance (evidence, not filter) — a regex side effect, not a written decision.
- Task titles `MCR 1 Bar` … `MCR 8 Stress` are a contract with `studies/breakage/mcRetest/inputs/tasks.py`; renaming breaks step 14.
- Configure the MinDistance task only when the build produced stop/limit entries (owner rule).

## Evidence
```xml
<CrossChecks use="true" evaluateAll="false">
  <MonteCarloRetest use="true"><Settings>
    <Methods><Method use="true" type="RandomizeSpread"><Params><Param key="Min">5</Param><Param key="Max">30</Param></Params></Method> …</Methods>
    <NumberOfSimulations>1000</NumberOfSimulations>
    <MCUseFullSample>false</MCUseFullSample>
    <MCBacktestPrecision>2</MCBacktestPrecision>
  </Settings><AcceptanceSettings>…</AcceptanceSettings></MonteCarloRetest>
```
- Master `XAUUSD`, `Retest-Task5..12`, verified by writing with `mcretest.py`.
- `MCBacktestPrecision` = fidelity of the 1000 sims; Setup `testPrecision` = main backtest. Master: Setup 2 / MC 1 in `MCR 1 Bar`, `MCR 5 Params`; 2/2 in the other six.
- `MCUseFullSample` decides the sample: 7 isolated tasks `false`, empty `<OutOfSample showGraph="false" />`, window 2008–2017; stress task `true`, 2008–2022,
  `<OutOfSample><Range dateFrom="2018.01.01" …>`. `studies/breakage/mcRetest/` labels the run from it — must match the window.
- Regex: `re.findall(r"<(\w+) use=\"(?:true|false)\">", block)`. Donor: 1 active condition in `MonteCarloRetest`; fresh builder clone: 0.
  Hence `mcretest.py` reports `0 condiciones apagadas` on a new project; its `silence()` still needed for projects not passed through the doctrine.
- 🤔 `RandomizeMinDistance` on a market-order population perturbs nothing (min distance separates a pending order from price). Not confirmed against SQX's engine; measured only that the population has no such orders.
- Reading a population's order types: 0.2 ms/strategy (231 strategies, 36 MB, 45 ms) — open `.sqx`, `strategy_Portfolio.xml`, search `key="EnterAt…"`. 10k = 2 s, no sampling needed.
