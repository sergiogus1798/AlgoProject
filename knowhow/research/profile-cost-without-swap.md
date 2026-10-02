---
q: market profile cost includes swap or not, research director profile swap nights held, swap vs 2x cost filter pays, AUDUSD extreme3 swap, funded swap per trade on measures
tag: 🔬  date: 2026-10-02  see: costs/swap-types, costs/funded-accounts-real-costs
---
# The profile's cost leaves swap out, and that changes no verdict today
Measured on the 7 measures that pass three filters and 6 near-misses (`scratch/research-director/swap_check.py`): swap moves a measure's cost by 0 % when it holds under a night (the only cell passing all four filters, EURUSD M15 short bar3atr, holds 1 bar), by 7-8 % on XAUUSD H4 (0.9 nights), 16 % on USDCHF H1, 57 % on
AUDUSD H4 (1.4 nights, 2.1 triple-weighted units). No measure crosses the 2× line except one that lands on
it (USDCHF H1 short 2.32 → 2.00). Recommendation (owner's call): keep swap out of the profile's `cost`; show
it as an informational column if a cell ever sits within 25 % of the 2× line.
Traps: forex swap points are **tickStep = tick_size/10**, not tick_size (10× error); % swaps are annual on the entry price (÷100÷360); the card's figures are today's rates, not 2013-2018's; the measure's hold is not the built strategy's hold; weekend rollovers (Sat, Sun) are not charged, Wednesday counts 3 (indices Friday).

## Evidence
`scratch/research-director/swap_check.csv`: per measure hold (median/mean hours), share overnight, nights,
triple-weighted units, swap per trade, effect, cost, multiple now / with swap / with twice the swap.
Entries and exits come from `marketProfile.one.evaluate` on the real build bars, rollover at feed midnight.
