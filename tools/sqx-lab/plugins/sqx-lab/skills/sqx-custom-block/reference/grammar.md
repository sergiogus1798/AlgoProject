# Block XML format (condensed)

Enough to read and debug what `emit`/`grammar` produce. A batch file is:

```xml
<CustomBlocks>
  <Item ...>   <!-- one CBlock_* per condition block -->
  <Item ...>
</CustomBlocks>
```

## The CBlock_* wrapper

```xml
<Item category="MeanReversion_user" oppositeBlockKey="CBlock_FailOverbought"
      returnType="boolean" type="Condition" display="RSI(@Chart@14) crosses above 30"
      name="ReclaimOversold" key="CBlock_ReclaimOversold" help="..."
      categoryType="Custom blocks" strategyType="Standard" status="0" action="add">
  <Contents> ...operator tree... </Contents>
  <Param key="#Chart1#" .../>      <!-- the block's data var, once -->
  <Param key="#Int2#"   .../>      <!-- outer optimizer knobs, AFTER </Contents> -->
  <Param key="#Double3#" .../>
</Item>
```

Key facts:
- `key` must start `CBlock_` and be unique across the batch.
- `oppositeBlockKey` points at the partner block (or `CBlock_null` for a symmetric single).
- **Outer `<Param>` defs live AFTER `</Contents>`** — this is the 144 schema (not before).
- Outer optimizer-knob keys are `#Int2#`, `#Int3#`, `#Double3#`, `#Double4#`, … (`#Int1#`/
  `#Chart1#` are reserved for the chart var).
- **Two block types.** The above is `type="Condition"` / `returnType="boolean"`. The other is
  `type="Price level"` / `returnType="price"` — same wrapper, but it RETURNS A PRICE and its
  `<Contents>` is a single **value** expression (see below). Emit it with `make_price_level`.

## The Contents tree

`<Contents>` holds exactly one root. For a **Condition** block that root is boolean — a
comparison operator, or an `AND`/`OR` of them:

```xml
<Contents>
  <Item key="CrossesAbove" ... categoryType="operators">
    <Block key="#Left#"  name="Left"  type="value" controlType="value"> ...atom... </Block>
    <Block key="#Right#" name="Right" type="value" controlType="value"> ...atom... </Block>
  </Item>
</Contents>
```

For a **Price-level** block the root is a **value** instead — one price atom, or an arithmetic
node (`Plus`/`Minus`/`Multiplication`, `returnType="pricenumber"`) over atoms + a `Number`.
No `AND`/comparison wrapper:

```xml
<Contents>                              <!-- HMA(n) + k*ATR(n) -->
  <Item key="Plus" ... returnType="pricenumber" ignoreInBuilder="true">
    <Block key="#Left#" ...> ...HMA atom... </Block>
    <Block key="#Right#" ...> <Item key="Multiplication" ...> Number * ATR </Item> </Block>
  </Item>
</Contents>
```

Boolean operators (roots): `IsGreater`, `IsLower`, `CrossesAbove`, `CrossesBelow`,
`IsRising`, `IsFalling`, `IsGreaterPercentil`/`IsLowerPercentil` (percentile rank),
`IndicatorAboveMA`/`BelowMA`/`CrossesAbove/BelowMA` (vs its own signal line),
`IsGreaterCount`/`IsLowerCount` (true for X bars). Joiners: `AND`, `OR`.

Value functions (nest INSIDE an operand, return a value): `Plus`, `Minus`,
`Multiplication`, `Division`, `Abs`, `Maximum`, `Minimum`. Use for bar geometry and
ratios, e.g. `is_greater(minus(high(), close()), mult(cat.number("1.5"), cat.atom("ATR", period="#Int2#")))`.

## An atom (indicator operand)

A value atom is the indicator `<Item>` copied from the user's `config.xml`, with its params
made block-ready:

```xml
<Item key="RSI" ... categoryType="indicator" middleValue="50" indicatorMin="0" indicatorMax="100">
  <Param key="#Chart#"  type="data" ... paramType="data" value="#Chart1#">#Chart1#</Param>
  <Param key="#ComputedFrom#" controlType="combo" values="Close=0,...">0</Param>
  <Param key="#Period#"  paramType="period" ... customParam="true" value="#Int2#">#Int2#</Param>
  <Param key="#Shift#"   paramType="shift" ...>1</Param>
</Item>
```

Param roles and how `emit` fills them:
| role | param | emit behavior |
|---|---|---|
| chart | `#Chart#` (`type="data"`) | bound to the block var: `value="#Chart1#"` |
| shift | `paramType="shift"` | inner text = `shift=` (default 1) |
| period | `paramType="period"` | bind to a knob (`period="#Int2#"`) or freeze (`period="14"`) |
| double | `type="double"` | bind (`atrmult="#Double3#"`) or freeze (`atrmult="3"`) |
| combo | `controlType="combo"` | pick a value (`computedfrom="2"`); default = its defaultValue |
| line | `#Line#` (multi-output) | pick the output (`line="1"`); default = 0 |

The kwarg name for a param is its key without `#`, lowercased: `#ATRPeriod#` → `atrperiod`,
`#Fast#` → `fast`, `#Line#` → `line`.

## Binding vs freezing
- Pass a `#...#` reference → the knob is **bound** to that outer optimizer param (the strategy
  builder can optimize it). You must declare a matching `int_param`/`double_param` on the block.
- Pass a plain number → the knob is **frozen** at that literal (not optimized).

That's the whole format. Everything else is the operator/atom catalog, which `catalog.md`
enumerates for this specific install.
