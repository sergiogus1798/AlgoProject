---
q: Why does a build abort at once with «Strategy from template file requires 2 charts, 1 defined»?
kw: requires 2 charts 1 defined; Error while running project; CONSTRUCCION aborts in one second; StrategyTemplateGenerator.fixCharts; filterMALong; filterMAShort; spRSI2; #Chart# 1; second chart; D1 filter; multi-timeframe template
tag: 🔬  date: 2026-10-07  see: authoring/headless-authoring-chain, sqx-drive/transient-abort-automatic-retry
---
# A template whose block reads chart 1 aborts the build: our projects define one chart
A template block with `<Param key="#Chart#" …>1</Param>` computes on a second chart (a D1 filter
under an intraday entry). `sqx.projects.builder` gives every task ONE chart, so the Build task dies
before its first strategy: «CONSTRUCCION : Error while running project», the exception one line
above it in the install's log. It is not the transient abort: a rerun fails the same way, and the
builder does not refuse the template beforehand. In the library on 2026-10-07: `filterMALong`,
`filterMAShort` (and their `_withExit`) and `spRSI2`; the other 56 use chart 0 only. Check a
template with `re.findall(r'key="#Chart#"[^>]*>(\d+)<', xml)` over its members: any value above 0.

## Evidence
`Test_EURUSD_M30_filterMALong_10k`, custodian, 2026-10-07 17:53:40 (`SQX_w2/user/log/StrategyQuant/
log_2026_10_07.log`): `java.lang.Exception: Strategy from template file requires 2 charts, 1
defined.` at `StrategyTemplateGenerator.fixCharts`, 0.5 s after «Project started»; the autopilot
reported «FALLO en el paso 6+7». The template's MA carries `#Chart#` = 1 and its own setup lists a
TICK chart and a D1 chart.
