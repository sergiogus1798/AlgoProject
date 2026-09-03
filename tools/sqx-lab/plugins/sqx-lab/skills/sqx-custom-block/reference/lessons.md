# Hard-won lessons — the *why* behind each guard

These rules were learned by authoring 600+ custom blocks and importing them into AlgoWizard.
Most are enforced automatically by the engine; this file explains why, so you don't "fix"
a guard that's actually load-bearing. Each says **what**, **why**, and **how it's enforced**.

## 1. Four sources, and the user's customs are marked in config
**What:** an atom can come from native `config.xml`, the user's `customBlocksExport.xml`
(**proven**), their `user/extend` `.java` snippets (**coded**), or `UserCustomIndicators.xml`
(**synthesized**). The user's OWN custom indicators are identified by config.xml's
`customSnippet="true"` marker — **machine-independent, works with or without the `.java` source** —
and surfaced in catalog.md's **⭐ YOUR custom indicators** section. **Why:** judging availability
from native built-ins alone wrongly declares a user's own indicators "unusable," and identifying
them *only* by `.java` files fails on a machine that has them registered but not the source (the
real bug that cost many furious rounds). **Enforced:** `bootstrap.py` merges all sources into
`catalog.json` with a `confidence` field and a `user_custom` flag; check `cat.has(key)`, never your
memory. A `✎` (synthesized) atom imports but is best-effort — recommend the user seed it (use in one
block → export → re-bootstrap) to upgrade it to proven.

## 2. talib_* atoms crash single-symbol builds
**What:** never put a `talib_*` atom (DEMA/WMA/TRIMA/talib_MA…) in a block for a
single-symbol or FX project. **Why:** `TALibIndicator.evaluateBlock` dereferences
`Strategy.Stockpicker`, which is null outside a portfolio/stockpicker engine → NPE at
strategy-build time (fails the majority of generated strategies). **Enforced:** the catalog
flags them `usable_single_symbol=false` (`⚠` in `catalog.md`); `emit.atom()` refuses them
unless `allow_talib=True`; `validate.py` check 7 fails if one is present. Use native
MovingAverage / KAMA / HMA instead.

## 3. Multi-output indicators need a #Line# param
**What:** any indicator with >1 output (MACD, Stochastic, Aroon, ADX, Ichimoku, QQE…) must
carry a `#Line#` param selecting the output — even when the display string omits `.#Line#`.
**Why:** without it the indicator can't resolve which series to read, and it only crashes at
build time (the validator for declared-params won't catch it). **Enforced:** `config.xml`
encodes `#Line#` as a second `<paramCategory name="Line">`; bootstrap captures it, emit
always emits it, and `validate.py` check 7 (with `--catalog`) fails a multi-output atom that
is missing it. You only choose which line: `cat.atom("MACD", line="1")`.

## 4. Oscillator midlines are per-indicator — never copied
**What:** read each oscillator's midline/range from `catalog.md` before comparing it to a
level. **Why:** they differ and guessing produces silently-wrong signals. RSI 50 (0–100),
CCI 0 (±~200), Momentum **100** (not 0), Williams %R **−50** (−100–0), Stochastic 50,
DeMarker 0.5, ROC 0. **Enforced:** the catalog carries `middleValue` / `indicatorMin/Max`
straight from the build; surface them, don't assume.

## 5. Escape help/display text
**What:** `&`, `<`, `>` in any `display=` or `help=` string must be entities
(`&amp;` `&lt;` `&gt;`). **Why:** a raw `>` or `&` breaks XML parsing — the batch won't
import at all. **Enforced:** wrap human text in `grammar.esc()`; `emit` escapes everything
it generates (attribute values *and* inner text). Hit 3× in real batches before it was
automated.

## 6. No `_<digits><letters>` suffix on block names
**What:** don't end a block `name=` with a version-ish suffix like `_144Native`, `_2v3`,
`_3x`. **Why:** AlgoWizard's UI strips a trailing `_<digits><letters>` when rendering
opposite-block links, causing confusing display and potential mis-binding. **Enforced:**
`validate.py` check 6 fails it. Safe suffixes: `_Long`, `_Short`, `_Filter`, `_user`.

## 7. Single timeframe by default
**What:** build on the chart TF unless the user explicitly asks for multi-timeframe. **Why:**
MTF changes the data semantics (reads a higher-TF series) and is rarely what a first request
means. **Enforced:** convention — `emit` only adds `chartTF` when you pass `chart_tf="D1"`.

## 8. Verify an atom exists before authoring (no phantoms)
**What:** before promising a block, confirm the indicator is in `catalog.json`. **Why:**
research notes and papers name indicators that may not exist in *this* build; authoring
against a phantom yields a block that won't import. **Enforced:** `cat.has()` / `cat.search()`;
if absent, substitute a real equivalent and say what you swapped.

## 9. One block = one signal (default)
**What:** prefer clean single-rule blocks; don't stack a second confirming indicator with AND
unless asked. **Why:** the user's standing preference — compound stacking belongs in strategy
assembly, not in an atomic block. A multi-bound single pattern (a session's open+close hour,
a band's upper+lower) is still one signal and is fine. **Enforced:** convention / Step 2 spec.

## 10. Batches are additive; opposites are symmetric
**What:** write a new batch rather than editing a shipped one; long/short pairs must
cross-link both ways. **Why:** edited artifacts drift from what was already imported;
asymmetric opposites confuse AlgoWizard's pairing. **Enforced:** `validate.py` check 3 fails
asymmetric pairs; treat existing batches as immutable.

## 11. Never modify the user's source registries
`config.xml` and `customBlocksExport.xml` are inputs you READ. Never write to them. The skill
only ever produces new `*.xml` batches and the derived `catalog.*`.

---

# Profitability / edge-hygiene lessons (correctness ≠ edge)

A block can pass every `validate.py` check and still quietly lose money. These are the silent
edge-destroyers; `assess.py` is the lint that catches them.

## 12. Never read OHLC / a value atom on the developing bar (look-ahead)
**What:** default `#Shift#=1` (the last *closed* bar). `#Shift#=0` reads the still-forming bar.
This applies to **OHLC** (`Close`/`Open`/`High`/`Low`/`BarRange`) just as much as to indicators —
shift-0 OHLC is **TradeStation-only**; on SQX's default and MT-style engines it is look-ahead.
**Why:** the developing bar's O/H/L/C — and any indicator derived from them — keeps changing until
the bar closes, so a rule using it peeks at information you would not have live. The backtest looks
great and dies in real time. **Breakout geometry:** put the signal-bar OHLC at shift 1 and the
**channel reference one bar behind (shift 2)** so it excludes the signal bar — `Close[1] > Highest[1]`
can never fire (`Close[1] ≤ High[1] ≤ Highest[1]`). `HighestIndex`/`LowestIndex` stay shift 1 (a state,
not a cross). **Enforced:** `emit` defaults shift to 1; `assess.py` flags any `#Shift#=0`
`categoryType="indicator"` **or** `priceValue`/`priceRange` (OHLC) atom as CRITICAL. Time atoms
(`BarHour`/`BarTime`, `categoryType="other"`) are exempt — a bar's clock is deterministic, not a peek.

## 13. Repainting indicators lie in backtests
**What:** some indicators revise their own recent values as new bars arrive — fractals, ZigZag,
HalfTrend, Gann HiLo, and some SuperTrend / Heiken-Ashi / SSL variants. Two kinds:
*historical-repaint* (fractals/ZigZag — late-confirmed pivots; even closed bars stay provisional)
and *developing-repaint* (HalfTrend/SuperTrend/Gann/SSL — only the current bar can flip). **Why:**
the backtest scores the *final, hindsight* values you never actually had in real time, so the
equity curve is fiction. **Enforced:** `assess.py` flags historical-repaint CRITICAL always, and
developing-repaint CRITICAL at `shift=0` / WARN at `shift≥1`; it also scans the indicator's Java
source for repaint / forward-reference tells. Read repainting series confirmed (`shift≥1`) or
prefer a non-repainting equivalent.

## 14. SQX mass-tests — so a weak block is worse than none
**What:** every block you add is raw material SQX's search tries in thousands of combinations,
keeping whatever backtests best. **Why:** feed it arbitrary plausible-looking rules and it *will*
find spurious strategies that die out-of-sample (multiple-testing / data-mining bias). A
hypothesis-driven, deduplicated, orthogonal library shrinks that false-discovery burden — fewer,
better, distinct edges beat a kitchen sink. **Enforced (research front-half):** every proposed spec
carries a falsifiable edge hypothesis (`research-prompt.md`); an adversarial critic kills
folklore / duplicate / overfit / repaint specs (`critic-prompt.md`); `check_specs.py` flags
>2-knob and compound specs; `assess.py` penalizes overfit shape (too many knobs, AND/OR
compounding, over-precise thresholds).
