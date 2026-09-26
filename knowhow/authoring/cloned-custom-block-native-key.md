---
q: cloning a custom block for another indicator; sed rename EMA to HMA; Cannot find block 'HMA'; nested indicator key must match native catalog; XmlStrategyException Cannot find block
tag: 🔬  date: 2026-09-26  see: authoring/block-vocabulary, authoring/fixed-native-block-params
---
# Cloning a custom block for another indicator: the nested `key` must stay the CATALOGUE key, not the display abbreviation
Building `crossAboveHMA_v1` (encargo 21) by copying `emaCloseCrossUp`'s `deps/blocks.xml` and
blind-renaming `EMA`→`HMA` broke the block: the nested price-value `<Item key="EMA" ...>` (the
right-hand side of `Close crosses above EMA`) became `<Item key="HMA" ...>`. `key` is not free text —
it must equal the indicator's real key in `config.xml`/`customBlocks.xml` (`HullMovingAverage` for
Hull, confirmed at `internal/web/SQWIZARD/branding/global/config.xml:9514`), never the short label
shown in `display`/`name` (`"(HMA) Hull Moving Average"`). SQX resolves nested blocks by `key` at
build time from the install's own catalogue; the human-readable prefix (`EMA`, `HMA`, `SMA`) is
coincidentally the same as the key ONLY for the moving averages that happen to be spelled that way
(`EMA` is genuinely the EMA's key) — it is NOT a general rule (`HMA`'s real key is
`HullMovingAverage`, not `HMA`). Also renamed and equally wrong if left alone: `mI="MovingAverage"`
should track the block's own menu index (`mI="HullMovingAverage"` for Hull) — copied verbatim from
config.xml it happens to already match.

The failure mode is silent at authoring/install time (`sqx.blocks.install` and
`sqx.templates.build` both succeed, no XML validation catches it) and only surfaces at build, deep in
every generation: `XmlStrategyException: Cannot create strategy from XML! ... Cannot find block 'HMA'`,
one exception per candidate, `Failed` stays 0 and `Strategies generated` keeps climbing — SQX just
silently drops every candidate that hits the broken rule and moves on, so a `--minutes` cap can burn
the whole budget generating nothing before anyone notices.

## Evidence
- 2026-09-26, custodian, first `USDJPY_workflow_profiling_v1` build attempt (09:33): 8000+ candidates
  generated in ~5 s, `Strategies generated 49` after 35 s, `In databank 0`; log flooded with
  `ERROR BacktestEvaluator ... Cannot find block 'HMA'` (hundreds of lines/s) from
  `Blocking computeThread` workers — no `Failed` counter increment, `action=status` looked ordinary
  except `In databank` never grew past what pre-existed.
- Fix: in `deps/blocks.xml`, both `<Block key="#Right#"><Item key="HMA" ...>` → `key="HullMovingAverage"`,
  `mI="MovingAverage"` → `mI="HullMovingAverage"` (matching `config.xml:9514` exactly, same
  `#Chart#`/`#ComputedFrom#`/`#Period#`/`#Shift#` sub-params). Reinstalled with
  `sqx.blocks.install ... --role conductor` then `--role custodian` (reports `replaced [...]`, not
  `added`, when the key already exists — that's the tell the fix actually overwrote the broken copy),
  rebuilt with `sqx.templates.build`, reran: 09:36:03–09:37:23, 200/200 strategies generated,
  `Failed 0`, no `Cannot find block` in the fresh log window.
- Verified post-fix by direct XML sampling (`template_check`'s signature detector cannot see this
  block — see below): 200/200 `Results` strategies contain `CBlock_CloseCrossesAboveHMA`, 64 distinct
  `HMA_Period` values across them (range asked: 2–220, one-item-group mechanism from
  `authoring/fixed-native-block-params.md`).
- 🤔 `sqx.inspect.template_check` reported only `template fixes MarketPositionIsLong` for this
  template — same as it would for any `market_long` build. Its `blocks()` walker explicitly skips
  `categoryType="randomBlock"` descendants (by design, so a real random hole doesn't count as
  "fixed"), but the one-item-group mechanism that gives a fixed condition a random PERIOD routes the
  whole condition through a `RandomCondition` hole bound to a size-1 group — so the fixed block
  becomes structurally indistinguishable from an actual random pick, and the tool's signature comes
  back empty for it. Direct XML sampling (grep every databank strategy for the block key) is the only
  check that still works for this template shape; `emaCloseCrossUp` has the identical blind spot.
