# The grammar of a StrategyQuant X strategy (abstract model)

The foundational reference for this skill. A `.sqx` is a ZIP holding `strategy_Portfolio.xml`
(the program) + `lastSettings.xml`. Everything here is derived from the live install's own
proven templates (`internal/web/AlgoWizard/examples/*`, `user/settings/StrategyTemplates/*`,
`VolumeProfile/templates/*`) and `…/branding/global/config.xml` — not guessed.

## The one sentence

**A SQX strategy is a typed, declarative, event-driven expression program. A *template* is
that program with some sub-expressions replaced by typed holes, plus a specification of how
to fill and vary those holes.** Everything below follows from this.

## 1. One node, one type system

Almost every element is `<Item key="…" returnType="…">`, composed through named slots
(`<Block key="#Left#">`, `<Block key="#Value#">`) and leaf `<Param>`s. Composition is
**type-directed**, over a small lattice:

`boolean · number · price · pricerange · pricenumber · order · none(action)`

- comparison(`pricenumber`,`pricenumber`) → `boolean`
- logic `AND/OR/Not`(`boolean`…) → `boolean`
- arithmetic `Plus/Minus/…`(`pricenumber`…) → `pricenumber`
- entry order → `order`; action → `none`

So a **condition is a boolean tree**, a **stop price is a pricenumber tree**, an **order is an
order-typed node carrying its exit stack**. The ~144 strategy-level primitives collapse into
**four roles**:

- **Sources (leaves):** indicators, OHLC/price, constants, variables, time/session
  (`BarHourIs`, `BarDayOfWeekIs`, `BarDayOfWeekIsNot`), market-state (`MarketPositionIsLong/Short/Flat`),
  P/L (`OpenPLInPips`, `ClosedPLInMoney`), account (`AccountEquity`).
- **Pure operators/functions:** logic (`AND/OR/Not`); comparison (`IsGreater/IsLower/Equals/NotEquals`,
  `CrossesAbove/Below`, `IndicatorAboveMA`, `IsRising/Falling`, `IsGreaterPercentil`, `IsGreaterCount`);
  arithmetic (`Plus/Minus/Multiplication/Division/Abs/Minimum/Maximum/Round/SquareRoot/Logarithm`,
  `IndicatorHighest/Lowest`, `ConvertToPips/ConvertToRealPips`, `FixedPips`); and the formula
  wrappers (`SQ.Formulas.Price.UseFormula`, `…SLPT.…`, `…RangeLevel.…`).
- **Effects:** entry orders `EnterAtMarket / EnterAtStop / EnterAtLimit / EnterReverseAtMarket`;
  actions `SetStopLoss / SetProfitTarget / ClosePosition / CloseAllPositions / CloseBestPosition /
  CloseWorstPosition / ClosePendingOrder / AssignVariable / LogToFile / SendEmail / DrawUpArrow / CustomAction`.
- **Holes (builder-only, `categoryType="randomBlock"`):** `RandomCondition / RandomValue / RandomAction`
  (sample from a pool via `#Group#`) and `NegatedCondition / OppositeValue / SameValue` (mirror).
  These are *typed placeholders* — the thing that makes a template a template.

## 2. Anatomy (the containers)

- `<Strategy engine="…">` — the **execution model**: `Stockpicker` (portfolio/ranking; uses
  `StockpickerEntryExit` + `StockpickerPS` rules) vs `MetaTrader` (single-instrument, event-driven;
  `IfThen`). Globals: `<MoneyManagement>` (11 schemas: `FixedSize`, `RiskFixedBalancePct`,
  `ATRRiskBasedSizing`, `PickerRiskFixedPctOfAccount`, `SimpleMartingaleMM`, …), `<GlobalSLPT>`,
  `entryTriggeredAt="AfterBarClose|OnBarClose"`.
- `<Datas>` — the **data streams**: `<data><id>0</id><symbol>…</symbol><timeFrame>0</timeFrame></data>`.
  *Multi-timeframe and multi-symbol live HERE, not on indicators.* Every source leaf binds to a
  stream via its `#Chart#` param (0 = main, 1 = subchart). A daily filter on an intraday entry =
  a second `<data timeFrame=1440>` + a condition with `#Chart#=1`.
- **variables** — typed state with UUID identity: the 4 signal vars + `MagicNumber`
  (`11111111-1111-1111-1111-111111111111`) + user vars. Read in conditions, written by `AssignVariable`.
- `<Rules>` — the logic, per bar. Rule *types* (verbs): **Signal** (pure — writes the signal vars,
  no order side-effects), **IfThen / IfThenElse** (condition → effects), **Stockpicker\*** (engine-specific).
- `<RandomGroups>` — the **pools** that fill `#Group#` holes. In a saved template they are embedded
  `<Group id=… name=… type="Condition|Value" randomGroupType="Conditions|Values">`; the builder also
  resolves the `#Group#` UUID against the install's `user/settings/blockGroups.xml`.

## 3. The signal-variable protocol (a convention, not the language)

The standard idiom used by the builder and by this skill's skeletons:

- One `Rule type="Signal"` computes 4 booleans, fixed UUIDs:
  - `LongEntrySignal  33333333-1111-1111-3333-333333333333`
  - `ShortEntrySignal 33333333-2222-1111-3333-333333333333`
  - `LongExitSignal   33333333-1111-2222-3333-333333333333`
  - `ShortExitSignal  33333333-2222-2222-3333-333333333333`
- `Rule type="IfThen"` rules consume them (`BooleanVariable` referencing the UUID), gated by
  `MarketPositionIsLong/Flat`, to place/close orders.
- Short = mirror of long: `Not(...)` on the variables + `NegatedCondition`/`OppositeValue` with
  `generate="opposite"` on the holes.

This is **one well-worn path through a larger grammar** — direct `IfThen` entries, `SignalFuzzy`,
and grid rules keyed by distinct `MagicNumber`s are all equally legal.

## 4. Template = program + holes + search space

Orthogonal to all logic is a **generation overlay**:

- **per-`<Param>` 3-state:** *frozen* (no `generate`) · `generate="random" randomValue="default"`
  (auto-bounds from `builderMinValue/builderMaxValue/builderStep`) · `randomValue="lo:hi:step"` (explicit).
- **holes:** `generate="random"` (sample `#Group#`) · `generate="opposite"|"same"` (mirror).
- **co-optimization:** related params share an `identification="…"` so they vary together
  (e.g. an order's SL/PT/TS/`BarsValid`/`ExitAfterBars`).

So authoring a template is three independent decisions: **Structure** (rules, rule types, tree shape,
orders, exits, data, engine) · **Search space** (what is hole vs pinned vs free param) · **Binding**
(which pools, how varied).

## 5. The design space — orthogonal axes

| Axis | Minimal (this skill today) | Full grammar |
|---|---|---|
| **A. Data** | 1 stream `#Chart#=0` (most shapes); **`mtf_filter`** adds a daily subchart + a filter hole on `#Chart#=1` | multi-TF / multi-symbol via `<Datas>` + `#Chart#` (subcharts beyond daily, multi-symbol) |
| **B. Condition** | flat `AND` of 2 random holes | arbitrary `AND/OR/Not` over atoms **and** holes; pinned+random mixed; 3+ slots; time/session/market-state gates |
| **C. Execution** | market, stop | + limit (present in `buy_dips`/`mean_reversion`), + reverse; price-hole side; mirror |
| **D. Exit** | exit stack frozen-or-default | rule-driven exits (`SetStopLoss` trail by `Lowest(n)`, close-on-signal, `ExitAfterBars`, close-at-time), custom exit formulas |
| **E. Position** | single position | grid/pyramid (`MarketPosition*` + distinct `MagicNumber` + `Quantity` vars), MM schema, engine choice |
| **F. Generation** | default sampling | full 3-state tuning, `identification` co-opt links |

## 6. The validity gap — why structure can't just be emitted

The type lattice is **necessary but not sufficient.** A tree can be perfectly type-correct and still
be rejected at build, because the binding constraints live *outside* the grammar and are invisible to a
schema validator:

- **engine exclusions:** `EnterAtStop/Limit` = `forEngine="*,-TS,-MC"`; `talib_*` crashes single-symbol
  builds (`Strategy.Stockpicker is null`); trail/reverse excluded on SP/SA.
- **identity wiring:** `MagicNumber` linking entry↔modify↔close; the signal-var UUID protocol;
  `identification` co-opt links.
- **mirror discipline:** every long hole needs its opposite (`NegatedCondition`/`OppositeValue`).
- **bar discipline:** OHLC look-ahead (shift), multi-output indicators need `#Line#`, XML escaping.

**Only the engine — import + build — is the oracle of validity.** This is *why* the skill transplants
into a build-confirmed **skeleton**: the skeleton carries all the semantic wiring correctly, and varying
only the typed holes stays strictly inside proven-valid territory.

## 7. The lab→product loop for new structure

"Inventing a structurally-new template" = moving to a new region of axes **A–E**. Each move is paid for
**once** with an import+build; on confirmation it becomes a new skeleton and the whole region opens for
free generation thereafter. Same lifecycle as the block and group tiers.

- **Skeletons today:** `stop`, `session_market`, `two_entry_market` (build-confirmed); `market`,
  `market_single`, `stop_long_single`, `role_market`, `multi_leg`, **`mtf_filter`** (validated, pending
  build-confirm) — all the signal-variable shape, short mirrors, exit stack present. `mtf_filter` is the
  first on **axis A** (multi-TF): a 2-stream `<Datas>` + a filter hole on `#Chart#=1`, derived from
  `highest_breakout_template_daily_filter` (see `engine/build_mtf_filter_skeleton.py`).
- **Confirmed-available-but-not-yet-a-skeleton:** `limit` (proven in `buy_dips`/`mean_reversion`),
  rule-driven trailing (`SetStopLoss` + `Lowest`), grid/pyramid (`GridExample1`), OR-trees / 3+ slots
  (deep AND/Not proven in built strategies; top-level OR not yet build-exhibited).
- **Method:** derive each new skeleton from the install's own proven template that already exhibits the
  structure (don't hand-write novel XML from the type rules alone) → import + build-confirm → register
  the shape in `engine/generate.py` (`SHAPES`).
