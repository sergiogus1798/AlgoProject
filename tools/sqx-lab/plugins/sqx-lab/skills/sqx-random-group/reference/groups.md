# Random-group XML format (condensed)

Enough to read and debug what the engine emits. A set file is:

```xml
<RandomGroups>
  <Group …>   <!-- one named pool -->
    <Item …/> <!-- one alternative the builder may pick -->
    <Item …/>
  </Group>
</RandomGroups>
```

## What a random group is

A **pool of interchangeable building blocks the builder draws ONE item from per strategy**,
to fill one slot. It overrides the global Building-Blocks settings for that slot. A strategy
template binds a group to a placeholder block — `SameCondition` (a group of `type="Condition"`),
`SameValue` (`type="Value"`), or `SameAction` — by the group's **UUID**. So: *template slot →
group UUID → the pool's items → builder samples one.* That's why every `<Group>` has an `id`.

## `<Group>`

```xml
<Group id="UUID" name="BreakoutUP" type="Condition" strategyType="Standard"
       category="Breakout" status="0" action="add"> … </Group>
```

| attr | notes |
|---|---|
| `id` | UUID, unique in file — a template references the group by this |
| `name` | unique in file |
| `type` | **`Condition`** (boolean items) or **`Value`** (price/number items) — the load-bearing split |
| `category` | free-form pool name shown in the builder's selector |
| `status="0" action="add"` | **optional** — a UI-made group omits them; AlgoWizard tolerates absence. The engine emits them by default for explicitness |

## Two item modes

**HYBRID** — re-export an existing custom block by reference. `categoryType="Custom blocks"`,
a bare `CBlock_*` (no `<Contents>` — AlgoWizard re-resolves it at import). Top-level `<Param>`s
copied from the block; `oppositeBlockKey` rides along (groups don't pair long/short — it's
inherited). This is what most real 144 groups are: a thin index into your block library.

```xml
<Item category="PriceLevels" oppositeBlockKey="CBlock_SuperTrendLevel"
      returnType="price" type="Price level" display="…" name="ChandelierLong"
      key="CBlock_ChandelierLong" help="…" categoryType="Custom blocks"
      strategyType="Standard" status="0" action="add">
  <Param key="#Chart1#" … >0</Param>
  <Param name="Period" key="#Int2#" … >22</Param>
</Item>
```

**INLINE** — a fresh item built from a config template. Three shapes:
- a **simpleRules** boolean (`categoryType="simpleRules"`): "HMA is falling", "Momentum is rising".
- a **value atom** (`categoryType` indicator/priceValue/priceRange): a bare `EMA`/`ATR`/`Close` line.
- an **operator comparison** (`categoryType="operators"`): one operator over two value operands,
  each in a `<Block key="#Left#/#Right#">`.

```xml
<Item customSnippet="false" key="HMAFalling" name="HMA is falling"
      display="HMA(@Chart@#Period#)[#Shift#] is falling" returnType="boolean"
      mI="HullMovingAverage" categoryType="simpleRules">
  <Param key="#Chart#" … >0</Param>
  <Param key="#Period#" … paramType="period" … >10</Param>
  <Param key="#Shift#" … paramType="shift" … >1</Param>
</Item>
```

Inline items keep the indicator's **native** param keys (`#Period#`, `#Level#`) and the full
catalog metadata (`genMinValue`/`builderStep`…). Hybrid items use the block's re-exported keys
(`#Int2#`/`#Double3#`) and are leaner. Neither has any **outer** `<Param>` declarations (unlike a
custom block) — every value is concrete, on the atom itself.

## Optimizer model (per `<Param>`)

| state | meaning |
|---|---|
| no `generate` attr | **frozen** — the builder always uses the default; never varies it |
| `generate="random" randomValue="default"` | optimize over the param's **own** `minValue/maxValue/step` |
| `generate="random" randomValue="10:60:5"` | optimize over an explicit (usually narrower) range |

(Old advice that every knob *must* carry `randomValue="min:max:step"` was wrong for 144 — the
atom already has native min/max/step, and frozen is a legitimate choice.)

## Rules

- **Type contract.** Every item in a `Condition` group has `returnType="boolean"`; every item in a
  `Value` group has `returnType` ∈ {`price`, `pricerange`, `number`, `pricenumber`}. Don't mix.
- **Flat items.** An item is a single rule or one comparison. **No `AND`/`OR` joiner** inside a
  group item — compound logic goes in a custom block, then pool it via HYBRID.
- **Duplicate keys are allowed** within a group (two `IsGreater` items is normal — the key is the
  operator type, not a unique id).
- **Escape** `display=`/`help=` text: `&gt;` `&lt;` `&amp;` (the engine does this for you).

That's the whole format. `catalog.md` enumerates what THIS install can pool.
