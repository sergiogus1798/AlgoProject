# engines/weekly — the weekly excess panel and its sign-flip null

What steps 17 (WFC), 18.5 (market surfaces) and 19 (WFM) compute the same way: trades into a
weeks × units matrix of excess, and a null that flips whole weeks with one sign for every unit.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | The weekly excess panel and the shared-sign flip null the optimisation steps read alike. | — | — |
| `flip.py` | The weekly shared-sign flip null: one sign per week for every unit, and where a statistic falls in it. | imported | seed + weekly panel → draws × units by `signs @ panel` |
| `panel.py` | Trades into weeks x units of excess, gross and net: each trade whole in the week it closes in. | imported | trades of one leg + bars + costs → per-trade frame → weekly panels |

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
