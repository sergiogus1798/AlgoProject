---
q: Does an index CFD's spread scale with its price, and what do FTMO's and Hantec's own ticks say the spread is?
kw: spread percent of price vs constant points; index spread fixed in points; NIKKEI225 1000 points FTMO; FTMO Hantec tick history depth copy_ticks_range; rollover hour spread forex p97.5; time-weighted vs tick-weighted mean spread; spread as PercentageBased commission; MC Retest range per segment
tag: 🔬  date: 2026-10-03  see: costs/darwinex-real-spread, costs/mc-retest-ranges, costs/commission-methods, costs/funded-accounts-real-costs
---
# Index spreads are near-constant in POINTS, not in % of price; only gold scales with price
Carrying today's spread-as-% back to an older segment's mean price understates an index's cost
there by 2–4×: over 2017–2026 Darwinex's measured spread in points stayed flat on NIKKEI225, USATEC,
USA500 and DJ30 while price rose 2–4× (elasticity of points to price −0.64, −0.14, −0.10, −0.02;
1 would be constant %). DAX40 is in between (+0.56); XAUUSD does scale (+1.18). Firms change regime
instead (below).

- Applied 2026-10-04 (owner): the widest firm's % of price × each segment's mean price, slippage
  35 % of it, MC Retest 0.5×–2× — % on purpose: history pays 2026's friction relative to price.

## Evidence
- What moves a firm's spread is a change of regime by the firm, not price: FTMO's JP225.cash averaged 745 pt in 2024, 487 in 2025 and 920 in 2026 (1094 in Jul–Sep); its crude went 20 → 58–65 pt and silver 16 → 64 pt from 2024 to 2026; Hantec's GER40.h fell from 156 pt (2025) to 19 (2026).
- FTMO quotes XCUUSD at 100× the SQX feed's price: convert through % of price, never raw points.
- Real fills: round trip 1.33 ± 0.16 × the worst firm's 12-month mean spread over 600 live deals (below).
Reproduction and further facts (🔬 ticks via `live.series("ticks", …)`, 2026-10-03):

- FTMO serves ticks back to between 2023-10 and 2024-10; Hantec back to between 2022-10 and 2023-10.
  A 2-week `live.series("ticks", …)` chunk of ~1 M ticks takes ~10 s; 27 + 25 symbols × 2 months = 3.4 GB.
- `mt5_ticks`/`live.series` use whatever account the terminal holds: switch first with
  `live.ask("account", account={login, server})`. With the terminal closed and no account the call
  hangs for its 900 s timeout.
- Forex: the 97.5th percentile of the spread IS the rollover hour (00h server, 10–100× the rest of
  the day; 1 h in 24 is 4.2 % of the time). A p2.5–p97.5 range therefore spans "tightest quote" to
  "rollover", not the range of a backtest-wide average spread.
- Tick-weighted means understate what a bar-open entry sees (EURUSD FTMO 0.12 vs 0.23 time-weighted,
  quote capped at 60 s so closed hours weigh nothing). Use the time-weighted mean.
- FTMO is the wider firm on every asset but UK100; Hantec's indices are flat quotes (GER40.h 0.10,
  US500.h 0.40, US100.h 0.40, JP225.h 5.00).

Ticks 2026-08-01 → 2026-10-02, `AlgoData/mt5/ticks/<firm symbol>/`, time-weighted, SQX points:

| asset | FTMO mean [p2.5, p97.5] | % of price | Hantec mean | card build/oos1/oos2 before |
|---|---|---|---|---|
| NIKKEI225 | 1056 [1000, 1954] | 0.0160 | 523 | 607 / 916 / 561 |
| USA500 | 60 [60, 60] | 0.0078 | 40 | 34 / 43 / 50 |
| USATEC | 158 [145, 195] | 0.0053 | 40 | 70 / 104 / 115 |
| DJ30 | 227 [210, 268] | 0.0043 | 110 | 260 / 385 / 327 |
| DAX40 | 202 [113, 359] | 0.0078 | 15 | 145 / 205 / 253 |
| XAUUSD | 44 [37, 52] | 0.0102 | 26 | 16 / 23 / 37 |
| EURUSD | 0.23 [0.00, 2.10] | 0.0020 | 0.18 | 0.54 / 0.45 / 0.49 |

Darwinex, measured days only (`AlgoData/spread/<SYM>_TICK/daily.parquet`, `source == medido`), year means:
NIKKEI225 2017 556 pt at 22 147 (0.0251 %) → 2026 618 pt at 61 122 (0.0101 %);
USATEC 2018 75 pt at 7 153 (0.0105 %) → 2026 112 pt at 27 516 (0.0041 %);
USA500 2018 54 pt at 2 777 (0.0195 %) → 2026 64 pt at 7 233 (0.0088 %);
XAUUSD 2017 9 pt at 1 277 (0.0071 %) → 2026 63 pt at 4 558 (0.0139 %).
No tick source reaches before 2017, so 2008–2016 is unmeasured by anyone.

Sampled tick history (Tue–Thu of each month's second week, `AlgoData/mt5/ticks_hist/<firm>/<ASSET>/`,
🔬 2026-10-04): FTMO serves ticks from 2024-02 (32 months to 2026-09), Hantec from 2023-02 (44; USATEC
and XAUUSD only 9), FundingPips (`11308943 @ FundingPips2-SIM`, not in `config/machine.yaml`) 19 of 21
months from 2025-01, no HK50, AUS200 or XCUUSD. FundingPips is the widest on DAX40, USA500, USATEC,
NIKKEI225 and XAGUSD; FTMO on the rest.

Live deals against the quote just before the fill (`history` verb + a 3-minute `ticks` window per
deal; 94 FTMO, 272 Hantec, 235 FundingPips, 🔬 2026-10-04):

- FTMO fills at the quote: 98 % of deals with zero slippage. Hantec fills worse than the quote on
  50 % of deals (mean 0.002 % of price a leg, about 0.8 of its own tiny spread); FundingPips on 27 %.
- Per leg, in units of the WORST firm's 12-month mean spread: signal exits and entries 0.44 (FTMO),
  0.60 (FundingPips), 0.57 (Hantec); stop-loss fills 1.24, 1.23, 0.61. Round trip 1.17, 1.64, 1.13.
- SQX applies slippage in full on entry AND exit (2.05 × per trade, 2 562 trades), so slippage s as a
  share of the spread charges spread × (1 + 2s): 12.5 % → 1.25 ×, 25 % → 1.5 ×, 50 % → 2 ×.
- MT5 tester, M1 OHLC against real ticks, 32 EAs: same trade count in all; OHLC undercharges a trade
  by 0–6 % of the spread on indices, 10 % on gold, 33–54 % on forex.
