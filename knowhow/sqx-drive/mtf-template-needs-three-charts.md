---
q: How does a task feed a template that reads a second timeframe, and why can the filter end up on the wrong chart?
kw: Strategy from template file requires 2 charts 1 defined; StrategyTemplateGenerator fixCharts; multi timeframe template MTF; D1 moving average filter; second Chart in Setup; Datas data timeFrame 1440; RulesComplexity Chart name D1 chart; BlockSettingsConverter convertToCharts; #Chart# param dataVar; Random group uses chart index 1; filterMALong aborts CONSTRUCCION
tag: 🔬  date: 2026-10-09  see: sqx-drive/cannot-start-unresolved-past-data, authoring/condition-count-simple-vs-template, sqx-drive/crosstf-one-task-per-timeframe
---
# A 2-chart template needs the chart in THREE places; only two of them fail loudly
The template declares its streams in `strategy_Portfolio.xml` (`Datas/data`: `timeFrame` 0 = main chart, 1440 = D1); each block names its chart with `<Param key="#Chart#">1</Param>`. A task needs ALL three: (1) a `<Chart symbol=… timeframe="D1" spread=…/>` in **EVERY** `<Setup>`, cross-checks included, or SQX aborts with `requires 2 charts, 1 defined` (`fixCharts`); (2) a `<data>` stream in the task's `<Datas>`, when the donor has one (177 of 232); (3) a `<Chart name="D1 chart" …/>` under `<RulesComplexity>`, the list `convertToCharts()` builds the builder's chart index from.
**(3) missing does NOT error: every `#Chart#=1` binding degrades to the main chart**, so the databank fills with strategies reading the «daily» filter on the signal's timeframe — the only silent one of the three.
`sqx.projects.charts.ensure` writes all three into EVERY task of the project — a retest names no template but tests the same strategies (`charts.streams`) — from `configure`, from `stage.just` (where `crossmarket`, SPP and WFC, which rebuild `<Setups>` with one chart, all end) and from `mt5verify.configure`. `configure` calls it after `apply`: `set_timeframe` flattens every `<Chart symbol=…>`, so `ensure` normalises to one chart per Setup first. `additionalCharts=` is NOT the chart count: never guard on it.
Steps 11-12: `sqx.variants.lengths.off_main` keeps an off-main-chart period out of the rescaling (owner, 2026-10-09). A period the builder drew is `<Param generated="random" … key="#Period#">`: `key` is NOT the first attribute. Not yet run on a two-chart mother: steps 10, 13-18.5 → `OPEN.md` 110.

## Evidence
- 📓 2026-10-07, `Test_EURUSD_M30_filterMALong_10k` on the custodian: build aborted at 17:53:40
  with `requires 2 charts, 1 defined` (`SQX_w2/.../log_2026_10_07.log`, `SQProject - Exc.`). The
  autopilot's `fallo.md` kept only «Error while running project»: the cause was in SQX's log, not
  in the report.
- 🔬 2026-10-09, `AlgoData/templates/library/filterMALong/template.sqx` (`wanted() == [1440]`)
  against the frozen donor's `Build-Task3.xml` (`projectsBackup/XAUUSD_base_2026-09-21`): both
  Setups at 1 chart and `missing()` naming all three gaps; after `ensure()`, 2 charts per Setup
  (each keeping its own symbol and spread), the `1440` stream and `<Chart name="D1 chart">`, and
  `missing()` clean. `tests/test_charts.py` holds the idempotence case.
- The three-insertion recipe was reverse-engineered from the bytecode plus a live run on
  2026-07-18 and is kept in `tools/sqx-lab/.../sqx-strategy-project/engine/generate.py:325`
  (`ensure_mtf_charts`); `sqx/projects/charts.py` is the port, because the plugin is installed by
  hand and does not auto-update (`OPEN.md` 38b).
- 🔬 2026-10-09, `Test_EURUSD_M30_filterMALong_charts` on the custodian (12-minute build, retired):
  CONSTRUCCION and OOS finished with no `requires 2 charts`; 20/20 `.sqx` declare the `1440`
  stream and carry `MovingAverage` with `#Chart#=1`; `template_check` 10/10. The first pass had
  wired only the tasks that name the template (OOS, CrossTF, WFC stayed at one chart) — hence
  `charts.streams`. `off_main` missed `MovingAveragePeriod1` on the real files until the regex
  stopped assuming `key=` comes first; `scale.sibling` to H1 and M15 then moved only
  `CBlock_ChpInt21` and `ExitAfterBars1` and kept the stream.
- 🔬 2026-10-09, step 26 on `Strategy 3.24.322` (FTMO, 2024-01 → 2025-06, `ohlc_m1`): the exported
  EA compiled and traded 52 times against SQX's 51, 42 paired on the same M30 bar with the same
  P&L, clock offset 0, the same five-month gap with the filter off on both sides. Verdict «No
  validada» (0.82 paired, limit 0.95) — inside the 0.46-0.97 range of single-chart runs.
  `AlgoData/mt5/verify/20261009-121445_Strategy_3_24_322/result.json`.
