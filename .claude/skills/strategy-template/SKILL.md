---
name: strategy-template
description: Turn a trading idea into a StrategyQuant X strategy template — understand the logic, check whether the condition already exists, author the custom block if it does not, and emit the .sqx into the library. Authoring only, no SQX running and no CPU burnt. Use when the owner describes an entry idea, asks for a template, a custom block, or a signal.
---

# /strategy-template

Nothing here starts SQX or costs CPU. It writes files. Running the template on a market is
`/template-run`.

**Read `sqx/templates/README.md` first** — the owner's three steps and his defaults live there, in
one place, so this skill and `/template-run` cannot drift apart. Apply a default silently and say
which one you applied.

## 0. The asset decides nothing here — and that is the point

A template carries no symbol, no timeframe, no cost and no window. All of those belong to the run
(`/template-run`), which takes them from `assets/`. If a request mixes the two — "a Keltner template
for XAUUSD M30" — the template is `keltnerUpperCrossUp` and XAUUSD M30 is a row in `runs.csv`.

## 1. Understand the logic — ask, always

The only step with no default. State and transition are different strategies: "the close **is
above** the upper band" fires on every bar of a move, "the close **crosses** it" fires once. Name
the readings you can see and ask which. Cheap message now, wasted CPU later.

## 2. Does it already exist, and is it reachable?

```bash
python3 -m sqx.inspect.vocabulary <term>
```

Two different answers in one output:

- **The block exists** — native or the owner's own. Then no authoring is needed.
- **`pooled by:`** — which random groups contain it. This matters **only for the random hole**. The
  fixed half of a signal reaches any block directly, pooled or not.

If the exact logic is not there, author it. Do not substitute the nearest block that is: that is
the owner's step 2 and he was explicit about it.

## 3. Author the block

Write the `<Item key="CBlock_…">` XML into the template's `deps/blocks.xml`. **Copy the worked
example** — `AlgoData/templates/library/keltnerUpperCrossUp/deps/blocks.xml` — it is a
build-confirmed pair (a condition and its directional mirror) and shows the shape exactly:
exposed `#Chart1#` / `#PeriodN#` / `#DoubleN#` params, `<Contents>` holding the expression, inner
blocks binding to the exposed params with `customParam="true"`.

Author the opposite block too and point `oppositeBlockKey` at it. Every block on this install has
one, and a dangling key breaks a mirror silently.

Then install it on **both** installs — the one you author on and the one that will build:

```bash
python3 -m sqx.blocks.install <deps/blocks.xml> --role conductor
python3 -m sqx.blocks.install <deps/blocks.xml> --role custodian
python3 -m sqx.inspect.vocabulary --diff custodian     # must report no gap
```

The installs must be stopped; the tool refuses otherwise. That `--diff` is not optional — a
template referencing a block the build install lacks does not error, it disappears from the builder.

## 4. Emit the template

```bash
python3 -m sqx.templates.build <name> <deps/blocks.xml> <CBlock_key> <out.sqx>
```

Default shape `market_long`: `AND(<the fixed block>, RandomCondition with #Group# empty)` — one
fixed condition and one free random one, which is what the owner asks for when he names no group.
The command aborts if the block does not land, if more than one hole is left, or if the XML does
not parse.

## 5. Write the brief and register it

Every template folder under `AlgoData/templates/library/<name>/` carries `template.sqx`,
`brief.md` (Spanish, readable), `brief.json`, `manifest.json` and `deps/`. Copy the structure of
`keltnerUpperCrossUp`. The brief states the thesis and **lists the decisions taken and which
default produced each**.

```bash
python3 -m sqx.templates.registry --set name=<name> --set archetype=<breakout|meanReversion|…> \
    --set shape=market_long --set entry=… --set created=<date> --set origin=authored \
    --set status=validated
```

`status` is `validated` until a real build produces strategies carrying the fixed block. Only
`/template-run` may write `buildConfirmed`.

## Do not

- Name a template after a symbol or a timeframe. A template belongs to no market; that is a row in
  `runs.csv`.
- Parametrise something the owner named. He fixes what he says; periods and deviations he did not
  name are left optimizable.
- Claim a template works. Emitting valid XML proves nothing — only a build does.
