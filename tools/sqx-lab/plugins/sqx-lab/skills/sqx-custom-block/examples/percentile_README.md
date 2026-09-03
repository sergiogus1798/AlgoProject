# Percentile-rank breakout family — 72 blocks, 3 files

Combines the **percentile-rank operator** (`IsGreaterPercentil` / `IsLowerPercentil` — "X is in the
top / bottom P% of its OWN last N values") with **Highest/Lowest channel breaks** and
**SRPercentRank / ATRPercentRank**. All built from `C:\StrategyQuantX`,
all validated **7/7**, edge-hygiene **0 CRITICAL**.

Why percentile-rank is a strong breakout primitive: it is **self-normalising** — "RSI in the top
10% of its own last 100 values" means the same thing on every instrument and every regime, so there
is **no absolute level to calibrate** and far less overfit surface than a hard threshold. All read
**confirmed (shift ≥ 1)** — no look-ahead. OHLC reads the last **closed** bar (`Close` shift 1,
breakout channel shift 2 so it excludes the signal bar); shift-0 OHLC is TradeStation-only and is
avoided throughout.

## 1. `percentile_indicators.xml` — 48 blocks · grade A (100/100, clean)
Each indicator wrapped as "at a self-relative extreme of itself."
- **16 directional pairs (32 blocks)** — `…PctHigh` (long / self-relative strong) ↔ `…PctLow`
  (short / weak), auto-paired: RSI, CCI, Momentum, ROC, AO, CMMA✦, ZScore✦, Disparity✦, DeMarker,
  OSMA, MACDV✦, WaveTrend, BHErgodic✦, VST✦, LaguerreRSI, SmoothedRSI✦.
- **8 regime gauges × 2 (16 blocks)** — `…PctExpand` (top P% = expansion/strong regime) and
  `…PctQuiet` (bottom P% = compression/coil), symmetric (non-directional): ATR, StdDev, ATRPercent✦,
  BBWidth, BarRange, ADX, Choppiness✦, Hurst✦.
- Knobs (2): **Lookback Bars** (#Int2#, default 100) + **Percentile %** (#Double3#, 90 high / 10 low).

## 2. `srpercentrank.xml` — 12 blocks · grade A (100/100, clean)
Dedicated support/resistance & ATR percent-rank.
- `SRPctRankCrossUp50` / `CrossDown50` — regime-birth 50-cross (pair).
- `SRPctRankHigh` (>80) / `Low` (<20) — extended-vs-S/R state (pair).
- `SRPctRankRising` / `Falling` — rank slope (pair).
- `SRPctRankPctHigh` / `PctLow` — percentile-of-the-rank (meta self-extreme, pair).
- `ATRPctRankStretched` (>70) / `Coiled` (<30) — vol regime (symmetric).
- `ATRPctRankRising` / `Falling` — vol expanding/contracting (symmetric).

## 3. `percentile_breakout_combos.xml` — 12 blocks · grade A/B (0 critical)
The explicit **combination** ask: a Highest/Lowest channel break **AND** a percentile gate. Compound
by design (so each carries the intended AND warning). Long/short pairs:
- `ChanBreakVolExpand` — break **AND** ATR%Rank in top percentile (vol expansion).
- `ChanBreakSRRegime` — break **AND** SRPercentRank on the breakout side of 50.
- `ChanBreakMomThrust` — break **AND** Momentum at a self-relative extreme.
- `ChanBreakFromCoil` — break **AND** ATR%Rank coiled (squeeze-then-break).
- `ChanBreakTrending` — break **AND** Choppiness in its bottom percentile (trending regime).
- `FreshHighSR` / `FreshLowSR` — fresh N-bar high/low (`HighestIndex`/`LowestIndex` = 0) **AND** SR
  regime. (`HighestIndex`/`LowestIndex` are `ignoreInBuilder` — SQX's random builder can't make these.)

## Verify on first import (low risk — all catalog-confirmed)
- The `IsGreaterPercentil` / `IsLowerPercentil` operator is export-proven on your install; the wrapped
  customs (✦) are config-registered. Glance at one generated strategy to confirm binding.
- Percentile defaults (top 10% / bottom 10% over 100 bars) are sane starting points — the Percentile
  and Lookback knobs are there to optimise.

Regenerate: `python gen_percentile_blocks.py catalog.json`
