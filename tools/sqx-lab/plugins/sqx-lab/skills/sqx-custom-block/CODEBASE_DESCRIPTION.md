# Custom Block Builder — a Claude Code skill for StrategyQuant X / AlgoWizard

> Describe a trading rule in one sentence. Get back a validated, import-ready AlgoWizard
> custom block — built from the indicators **your own** StrategyQuant X install actually has.

The Custom Block Builder turns a plain-English idea ("go long when RSI reclaims 30", "a stop
two ATRs under the Hull MA", "a Donchian breakout filtered by ADX") into a ready-to-import
custom-block XML. It reads your install to learn what *you* can build, assembles the block,
and validates it before you ever open AlgoWizard. Works on **any SQX 14x build** — it discovers
your indicator vocabulary instead of hard-coding one.

## What it does

- **Plain English → importable block.** Say the rule; get a validated `.xml` you import via
  *Custom Blocks → Import*. It then behaves exactly like a block you'd hand-build in the editor.
- **Two block types, not one:**
  - **Condition blocks** — true/false signals (entries, exits, filters): crosses, level breaks,
    rising/falling, percentile, count, arithmetic.
  - **Price-level blocks** — blocks that *return a price*: stops, targets, bands, breakout and
    session anchors, `anchor ± k·ATR` trails, and `max/min` confluence levels.
- **Built from YOUR install.** It scans your StrategyQuant X folder and detects every usable
  indicator automatically — no manual file hunting, no editing the engine.
- **Your own custom indicators are first-class.** Indicators you've registered or coded are
  recognised and used directly — surfaced in a ⭐ *YOUR custom indicators* section. The detection
  is machine-independent (it reads the `customSnippet` marker), so it works **with or without**
  the `.java` source on disk — fixing the classic *"it didn't find my indicator on another PC."*
- **Idea mode.** Don't have a specific rule? Ask *"what momentum blocks could I build that I
  don't already have?"* and it proposes candidates **grounded in your catalog**, kills weak,
  overfit, repainting, or duplicate ideas with an adversarial critic, and authors the ones you pick.

## Why the blocks actually work

Two layers of checking ship with the skill:

- **`validate.py` — proves it imports.** A 7-check linter run before every hand-off: correct
  schema, declared optimizer params, the required `#Line#` on multi-output indicators, safe
  naming, and more.
- **`assess.py` — proves it won't quietly lose money.** An edge-hygiene linter that grades each
  block A–D and flags the silent edge-destroyers a syntax check can't see: **look-ahead** on the
  developing bar, **repainting** indicators read unconfirmed, and thresholds outside an
  indicator's range (so the block can never fire).

Hard-won guardrails are baked into the engine, so common footguns simply can't ship:
OHLC reads the last *closed* bar (refuses look-ahead `shift=0`); `talib_*` atoms are refused in
single-symbol/FX builds (they throw a Stockpicker error at build time); multi-output indicators
auto-carry their line selector; and block names that AlgoWizard mis-renders are rejected.

## Requirements

- StrategyQuant X **build 14x** (build-144 schema; backward-compatible).
- **Python 3.8+** — standard library only, no pip installs.
- [Claude Code](https://claude.com/claude-code).

## Setup (once per machine)

Drop the `sqx-custom-block/` folder into your Claude Code skills directory, point it at your
StrategyQuant X install once, and it builds a catalog of everything you can use. After that, just
ask for blocks in plain English.

## What's new in this version

- **Price-level blocks** — a second authorable block type (stops / targets / bands / anchors).
- **Edge-hygiene assessment (`assess.py`)** — A–D grading + look-ahead / repaint / dead-threshold
  detection on top of import validation.
- **First-class support for your own indicators** — machine-independent detection, works without
  the `.java` source, surfaced as ⭐ *YOUR custom indicators*.
- **Idea mode with an adversarial critic** — propose → critique → gate → author, all grounded in
  your catalog.
- **Deterministic self-test** — an 8-case eval harness keeps the skill regression-proven.

## Companion skills

The Custom Block Builder is the first of a three-skill pipeline — **build the rules → pool them
→ wire them into a buildable strategy:**

- **Random Group Builder** (`sqx-random-group`) — author the random groups the strategy builder
  samples from.
- **Strategy Template Builder** (`sqx-strategy-template`) — author importable `.sqx` strategy
  templates bound to your install's own groups and blocks.

*(Strategy-template generation lives in that companion skill, not in the Custom Block Builder.)*
