# feedQuality — what could change, argued before it is coded

Every item is the owner's to decide: the thresholds are his, frozen in `ledger/thresholds.yaml`
before any strategy was looked at, and his answer 2.16 says a failed injection adjusts the
detector, never K. Measured 2026-09-26.

## 1. The injection's «zero new marks» criterion fails in every feed, by a little — ACCEPTED

**Owner, 2026-09-26: «lo doy por bueno».** The detector stays as it is; what follows is the record.

With ~12,300 events planted per feed (the owner's grid), every other criterion passes in all 13
feeds, including «the real count moves ≤ 2 %» (the largest move is Brent's 0.4 %). But the
detector finds 1 (gold) to 37 (Brent) marks that are neither planted nor in the clean run:

| feed | new | of them already ≥ 0.95 K before | real count |
|---|---|---|---|
| XAUUSD | 1 | 1 | 23,098 → 23,096 |
| USDJPY | 3 | 3 | 1,797 → 1,796 |
| XAGUSD | 19 | 17 | 46,860 → 46,865 |
| BRENT | 37 | 33 | 7,971 → 8,002 |
| USDCAD | 11 | 4 | 2,531 → 2,538 |

Most are real spikes sitting just under K that the planted events of earlier weeks push over:
MAD moves ~1 %, as the owner's own note on 2.16 anticipated («if it is not null, the scale is
not as robust as believed»). The rest come from quiet hours where the MAD sits on one or two
ticks and a few added zeros drop it a whole step (14–27 %). Options: accept (it is 0.1–0.5 % of
the real count); or plant fewer events per run (~500 per run instead of 12,300, twenty-five
runs), which measures the detector rather than the grid's own contamination. Not done: it is
a change to the owner's design.

## 2. Brent's session is wrong, silver's borderline

Deduced from the feed, Brent keeps 109 own gaps a year (silver 33) against the owner's bar of
30. Brent has pauses the 50 % rule does not capture (06–08 h, 20–21 h in 2022–2025, and a very
different 2013–2017). Its `assets/symbols/BRENT.yaml` session is `null`; declaring the FTMO
session with its pauses is the owner's (answer 3.3), and then `calibrate` is rerun for it.

## 3. The metals' own holidays read as the symbol's gaps

Gold and silver are closed from 24-Dec ~20:45 to 26-Dec (≈1,395 min) while the pairs still
quote thinly, so the rule «a holiday is a day every feed is silent» does not fire: one marked
gap a year per metal. A calendar per provider *and class* (metals apart) would fix it.

## 4. A bad tick's echo is counted as a «movimiento extremo»

A one-bar bad tick makes two spikes: the jump (a spike-and-revert) and the return one minute
later, which does not itself revert and so is counted as an extreme move. It never marks a
trade (non-reverting spikes are out of the attribution), but it inflates that column.
Dropping a spike whose previous bar is a spike-and-revert of the opposite sign would fix it.

## 5. At these K the step-8 alarm is almost always «insuficiente»

On `XAU_ISOOS_ejemplo` (M30, ~1,000 trades each) the mean strategy touches 6.7 anomalies,
at most 16: 102 of 115 are «insuficiente», 13 «sin alarma», none alarm. On
`USDJPY_emaCross_H1` (H1) the mean is 1.5. Cost of the screen in strategies: zero today. The
screen earns its place on a strategy that does depend on anomalous minutes, and for
stop/limit strategies once the wick column decides. Lowering `min_flagged` or K would make it
fire more; both are the owner's, and both would be chosen after seeing these numbers.
