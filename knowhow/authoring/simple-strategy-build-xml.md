---
q: Which Build task switches make a Simple Strategy build, and where is its direction set?
kw: build a Simple Strategy project without a template; StrategyType type simple; MarketSides type long short both; EntrySymmetry; one direction without a template; templateFile with type simple; SQ3StrategyTemplateExample.sq4; random-generation twin BuildMode generationType; builder --simple --random; count what a Build task will generate; census
tag: 📓  date: 2026-10-02  see: authoring/condition-count-simple-vs-template, authoring/builder-block-switches
---
# A Simple Strategy build is three switches of the Build task; its direction is `<MarketSides type=>`
`python3 -m sqx.projects.builder <P> --purpose "…" --simple long|short [--random] --symbol S --timeframe TF --workflow --acceptance calibration`, then a palette: without one the donor's 400 conditions, 26 values, 10 levels stay ON.
- `<StrategyType type="simple">`, with `templateFile="SQ3StrategyTemplateExample.sq4"` — what SQX's stock Builder carries while simple; any other name beside `type="simple"` is the «template ignored» refusal.
- `<MarketSides type="long|short|both">`, both symmetries false: the ONLY direction gate without a template (rule 13). A template's direction comes from its rules; the builder leaves the donor's `long` there.
- `<BuildMode generationType="random-generation">` is the random twin (`--random`); `set_genetic` copies the owner's block over everything else and keeps that attribute.
- Count before any run: `python3 -m sqx.projects.buildingblocks --project P [--palette a,b] --count [--json]` (`sqx.projects.buildcensus.census(cfx)`).

## Evidence
- 📓 2026-10-02, every `project.cfx` of the three installs: `MarketSides` is `long` (14 Builds), `short`
  (master `EURJPY_H1`, `USDCHF`, both `type="simple"`, symmetries false) or `both` (the three stock `Builder`,
  `EntrySymmetry` true). The owner's simple projects keep a stale `templateFile`; the stock one names
  `SQ3StrategyTemplateExample.sq4`, a file under `user/settings/StrategyTemplates/`.
- 🔬 `tests/test_builder_simple.py`: a project built in a temp install reads simple, long, 1..2 / 1..2,
  `EnterAtMarket` only, `<BuildMode>` equal to `buildmode_model.xml`; its twin differs in that attribute alone.
- 🤔 No Simple Strategy project of this builder has been STARTED in SQX yet (files only, 2026-10-02): the first
  population confirms that SQX accepts the stock `templateFile` name and builds one side only.
