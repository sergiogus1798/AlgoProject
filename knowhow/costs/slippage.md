---
q: slippage value per asset; defaultSlippage zero; can slippage be measured from export; half the spread convention; point value dollars per point
tag: 🔬  date: 2026-09-22  see: costs/where-the-spread-is, costs/mc-retest-ranges
---
# Slippage cannot be measured from an export; the convention is half the spread (owner, 2026-09-22)
- `defaultSlippage` = 0.0 on all 17 master instruments — factory, optimistic.
- `assets/symbols/<SYMBOL>.yaml` `slippage` (points, both classes) → `sqx_settings()` emits `defaultSlippage`. It does NOT block authoring (unlike spread/commission); `crossmarket` execution stress models worse fills separately.
- A flat point figure can't work across classes; half the spread does.

## Evidence
- 🤔 A backtest applies the slippage it is given: `gross − P/L` recovers the assumption, never a broker's reality.
- A point = `tick_size × point_value`: $0.0065 (Nikkei) to $11.53 (USDCHF); 2.5 points = $0.02 vs $28.82.
  Half the spread → $0.33–$5.00 per lot per side across the 17; gold → 5 points = midpoint of its MC Retest 0–10 range.
