# complex_breakout.xml — compound, session-gated breakout blocks

11 blocks, category `BreakoutComplex_user`. **Every block is a multi-clause AND** (you asked for
complex conditions, not the simple single-signal ones), and each uses the **Bar & Time** atoms
(`BarHour` / `BarDayOfWeek`) to gate *when* the breakout is allowed to fire.

- Validated **7/7** (`python engine/validate.py complex_breakout.xml --catalog catalog.json`)
- Edge-hygiene **0 CRITICAL**, grade **B (89/100)** (`python engine/assess.py …`) — the only flags
  are the intentional compound-AND warnings.
- Built from this install: `C:\StrategyQuantX`.

## Shift discipline (no look-ahead — SQX default, NOT TradeStation)
Everything evaluates on the **last closed bar**. SQX (and MT-style engines) must read OHLC at
shift ≥ 1; shift 0 is the developing bar and only safe on TradeStation's intrabar engine.
- **OHLC on the signal bar = shift 1**: `Close`, `BarRange`, and the time gates `BarHour`/`BarDayOfWeek`.
- **Channel reference = shift 2**: `Highest`/`Lowest`/`HighD`/`LowD`/`BiggestRange` — one bar *behind*
  the signal bar, so the channel excludes it (a `Close[1] > Highest[1]` could never fire, since
  `Close[1] ≤ High[1] ≤ Highest[1]`). Same breakout geometry as before, just on the confirmed bar.
- `HighestIndex`/`LowestIndex` stay shift 1 — a fresh-extreme *state* read on the last closed bar
  (not a cross, no self-reference). `ATRPercentRank` gate shift 1.

## The blocks

| # | Block (long / short) | Compound rule | Time/Bar atom | Knobs |
|---|---|---|---|---|
| 1–2 | `DonchianSessionBreakUp` / `…Down` | Close breaks the prior **N-bar Highest/Lowest** channel **AND** inside an hour window | `BarHour` window | Channel Period, Session Start/End Hour |
| 3–4 | `PrevDayBreakSqueezeUp` / `…Down` | Break of **prior-day High/Low**, **AND** after the open hour, **AND** out of a **quiet vol regime** (ATR%Rank < ceiling = squeeze→break) | `BarHour >` | Trade-After Hour, ATR%Rank Quiet Ceiling |
| 5–6 | `FreshHighSessionUp` / `FreshLowSessionDown` | The confirmed bar just set a **fresh N-bar high/low** (`HighestIndex`/`LowestIndex` = 0) **AND** inside the hour window | `BarHour` window | Period, Session Start/End Hour |
| 7–8 | `RangeExpBreakUp` / `…Down` | N-bar channel break **AND** it's a **range-expansion bar** (`BarRange` > `BiggestRange(M)[1]`) **AND** after the early session | `BarHour >` | Channel Period, Expansion Window, Trade-After Hour |
| 9–10 | `MidWeekBreakUp` / `…Down` | N-bar channel break **AND** only on **mid-week** bars (skip week-open/close) | `BarDayOfWeek` window | Channel Period, DoW Low/High Bound |
| 11 | `IntradayCoilArm` (symmetric, `CBlock_null`) | **No fresh extreme either side** (`HighestIndex` & `LowestIndex` both > k) **AND** inside the hour window = an intraday **coil that arms a breakout** | `BarHour` window | Period, Min Bars Since Extreme, Start/End Hour |

## Why these are "complex," not the usual breakouts
- **Squeeze-then-break (3–4):** a prior-day break is only taken when ATR Percent Rank is *low* —
  i.e. breaking *out of compression*, the highest-information breakout state, not a late extension.
- **Recency cores (5–6, 11):** `HighestIndex`/`LowestIndex` are `ignoreInBuilder` atoms — SQX's
  random builder can never assemble these, so the fresh-extreme and coil gates are genuinely new
  raw material, not a re-skin of the channel breaks you already have.
- **Expansion-confirmed (7–8):** the break must coincide with a volatility-expansion bar, filtering
  the limp drifts that creep over a level without energy.

## ⚠ Calibrate on first import (INTRADAY only)
- **All hour bounds are broker SERVER-TIME** — the defaults (≈07–20, after-08/09) assume a generic
  session; set them to your broker's clock and the symbol's active hours.
- **`BarDayOfWeek` numbering** assumes Mon=1…Fri=5 (matches your existing `Session_v144` blocks). If
  your broker numbers days differently, adjust the DoW bounds.
- These are meaningless on D1+ (one bar = one day). Use on H1/M30/M15 etc.
- First emits on this install via the portable skill: `ATRPercentRank` (✦ your custom, mid 50),
  `HighestIndex`/`LowestIndex` (native, `ignoreInBuilder`), `BiggestRange` — all catalog-confirmed;
  glance at one generated strategy to confirm they bind as expected.

Regenerate: `python gen_complex_breakout.py catalog.json complex_breakout.xml`
