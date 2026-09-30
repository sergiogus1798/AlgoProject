---
q: zero P/L trade flat trade, Winning Percent half win, ZScore flat counts as win, WinningPct formula, KellyFormula win rate excludes flats wins/(wins+losses), reconstruction mismatch USDJPY
tag: 🔬  date: 2026-09-25  see: sqx-format/mc-retest-reconstruction
---
# A zero-P/L trade is half a win in `WinningPct`, a full win in `ZScore`, and left out of `KellyFormula`
`WinningPct = (wins + 0.5 × flats) / n`. In the Wald–Wolfowitz runs `ZScore`, a flat trade counts as a
win. `KellyFormula` takes its win rate as `wins / (wins + losses)` — flats dropped. None is documented by SQX. Fixed in `studies/breakage/mcRetest/model/` (71 disagreements → 2).
⚠️ Keep `n` and the run counter consistent: excluding flats from `n` while the run counter sees their
sign changes adds two phantom runs per flat.

## Evidence
- 2026-09-25, `KellyFormula`, MC Retest of USDJPY H1 `Strategy 15.12.75` (task Exits, ~1.7 flats per 511
  trades): SQX's 11 stored levels 12.26 / 11.77 / 10.81 / 10.34 match `wins/(wins+losses)` (12.2594,
  11.7715, 10.8155, 10.3401) at every level; the half-win rate gives 12.245 / 11.729 / 10.777 / 10.273 and
  flat=loss 11.89 / 11.53 / 10.38 / 9.66. The ingest refused on 20 runs before; 0 disagreements after.
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

⚠️ Open (2026-09-28, cosecha `trades.parquet` of Test_USDJPY M30 `Results`, 526 zero trades in 348 k):
`wins/(wins+losses)` matches `Winning Percent [IS]` within rounding on 200 of 200; the half-win rule is off
by up to 0.013 on 28. Suspect: the cosecha rounds P/L to the cent, so a «zero» there may be a tiny win or
loss. `ui/daemon/databank/segments.py` uses the non-zero form for its IS+OOS1 column.
Unseen before: the XAUUSD calibration corpus has zero flat trades; USDJPY has 6 of 4,482 (0.13 %) — enough
to break `WinningPct`, `KellyFormula` (amplifies the win-rate error) and `ZScore`, blocking workflow step 14.
