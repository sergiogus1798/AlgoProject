# engines/weekly — the weekly excess panel and its sign-flip null

What steps 17 (WFC), 18.5 (market surfaces) and 19 (WFM) compute the same way: trades into a
weeks × units matrix of excess, and a null that flips whole weeks with one sign for every unit.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Names what the package is; holds no code | — | — |
| `panel.py` | `per_trade` (`engines.variants.excess.per_trade` plus `net`, `gross` = net + the cost `reprice.real` charged, and the stamps), `weekly` (weeks × units, `net` and `gross`, each trade whole in the Monday-to-Sunday week it closes in, one index of every week touching the window, zeros where nothing closed), `per_year`, `years`, `monday`, `sqx_gap` (share of units whose repriced P/L misses SQX's `NetProfit` by more than a tolerance) and `straddle` (share of trades closed on a Monday or Tuesday after a weekend) | imported | trades of one leg + bars + costs → per-trade frame → weekly panels |
| `flip.py` | `signs` (B × W of ±1 from one seed, blocks of 1 or 2 weeks sharing a sign), `chunks` (the same matrix a few draws at a time), `tails` (`p_mas`, `p_menos` as (1 + #) / (1 + B), `nulo_p5`, `nulo_p95`) and `spearman` (one fixed vector against B redrawn ones, average ranks) | imported | seed + weekly panel → draws × units by `signs @ panel` |

**The drift is the project's, decided (owner, 2026-10-08).** The WFC proposal's formula («the mean per bar of
the calendar year, summed bar by bar over the bars held») is NOT what is used. Steps 17-19 subtract the same
drift as steps 8-14, the gate's: `{"window": "year", "variant": "d"}`, a 1/ATR-weighted blind trade of the same
hold, taken in the year the trade opened in (`excess.per_trade`; the caller's `drift` block passes it through).
Variant `b` (the plain mean bar of that year times the bars held) stays available and is not the project's.

**The flip null assumes a week's excess is as likely as its mirror.** Measured on no-edge panels
of 143 weeks × 30 units, 2,000 panels, 199 draws, nominal 5 % (`tests/test_weekly_flip.py`):
correlated Gaussian noise rejects 5.1 / 5.0 % (Spearman, upper / lower tail) and 4.6 / 4.6 %
(median of the units' totals); a mean-zero lottery (one week in ten wins 9, the rest lose 1,
Student-t(3) sizes) rejects 5.3 / 5.1 % with Spearman but 2.2 / 13.3 % with the median — the
lower tail of a median statistic over-rejects on positively skewed excess.
