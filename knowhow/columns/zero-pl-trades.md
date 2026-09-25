---
q: zero P/L trade flat trade, Winning Percent half win, ZScore flat counts as win, WinningPct formula, KellyFormula error flat trades, reconstruction mismatch USDJPY
tag: 🔬  date: 2026-09-24  see: sqx-format/mc-retest-reconstruction
---
# A zero-P/L trade is half a win in `WinningPct` and a full win in `ZScore`
`WinningPct = (wins + 0.5 × flats) / n`. In the Wald–Wolfowitz runs `ZScore`, a flat trade counts as a
win. Neither is documented by SQX. Fixed in `studies/breakage/mcRetest/model/` (71 disagreements → 2).
⚠️ Keep `n` and the run counter consistent: excluding flats from `n` while the run counter sees their
sign changes adds two phantom runs per flat.

## Evidence
USDJPY H1, SQX `metrics.csv` vs exported trades of the same backtest.

| strategy | flats | `>0`/n | `>=0`/n | SQX WinPct |
|---|---|---|---|---|
| Strategy 11.1.50 | 1 of 506 | 51.581 | 51.779 | **51.680** |
| Strategy 23.1.60 | 1 of 401 | 52.369 | 52.618 | **52.500** |
| Strategy 23.1.71 | 2 of 838 | 52.267 | 52.506 | **52.390** |

Control: the five strategies with no flats match both ways. ZScore: `flat=win` within 0.003 on all five
with flats; `flat=loss` and dropping it do not.

| strategy | old (bug) | drop | **flat=win** | flat=loss | SQX |
|---|---|---|---|---|---|
| Strategy 11.1.50 | 0.3823 | 0.2039 | **0.3404** | 0.1562 | 0.3400 |
| Strategy 23.1.71 | −0.1764 | −0.3845 | **−0.4468** | −0.3213 | −0.4500 |

Unseen before: the XAUUSD calibration corpus has zero flat trades; USDJPY has 6 of 4,482 (0.13 %) — enough
to break `WinningPct`, `KellyFormula` (amplifies the win-rate error) and `ZScore`, blocking workflow step 14.
