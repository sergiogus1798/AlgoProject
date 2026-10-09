---
q: What does Darwinex publish on DARWIN risk normalisation, D-Score, DarwinIA SILVER/GOLD and trading constraints?
kw: Darwinex, DARWIN, DarwinIA, SILVER, GOLD, D-Score, risk engine, 6.5% VaR, D-Leverage, divergence, capacity, investable attributes, yardstick Q10
tag: 📓  date: 2026-10-06  see: funded-bank-ev-read-against-the-monkey
---
# Darwinex's published rules for DARWIN risk, D-Score and DarwinIA — what is stated and what is not published
Owner's goal for the real account is DarwinIA (owner, 2026-10-06). **No code implements any of this**; `portfolio/PLAN.md:1023` («not researched here») points here.
**Caveat:** quotes came through a small model's page summaries and most help pages carry no date — re-check the exact wording on the source page before coding any threshold.
Anything the table lists as «not published» stays a gap: never fill it. Open questions for the owner: one account or several DARWINs; SILVER or GOLD; trades <60 min in scope; account currency and symbols; ask Darwinex support for `f`, the SILVER formula, the drawdown floor.

## Evidence
| topic | published | not published |
|---|---|---|
| Risk target | 6.5% monthly VaR, 95% confidence; oscillates 3.25–6.5%; VaR over the last 45 exposed days (6 months max lookback cited) | factor `f` in `Lev(investor) = Lev(trader) * (target VaR / strategy VaR) * f`; explicit rule when VaR is far off target (above => cut, below => raise is 🤔 read from the formula) |
| Max D-Leverage | 16.25 (<15 min), 13 (30–60 min), 9.75 (>60 min) | the 15–30 min band |
| D-Score | exists, 5-year return-curve quality, quote data only; 55 => 20% discount, 60 => 40% | formula |
| 12 attributes (Ex, Mc, Rs, Ra, Os, Cs, R+, R-, Dc, La, Pf, Cp) | names; Pf = risk-adjusted return vs 10,000 random same-risk strategies | per-attribute formulas and thresholds |
| DarwinIA SILVER | equity >= 1,000 USD (exclusion at 900); correlation <0.95 to others, <0.5 to own DARWINs; 1 trade this or last month; rating >= 75; 30k–375k EUR for 3 months | rating formula; minimum tracked history |
| DarwinIA GOLD | history >8 months; 1y >20% / 2y >25% / 3y >30% / 4y >35% / 5y >40%, each with Return/DD >2.5; top 50 by month return; 50k–500k EUR for 6 months; max negative divergence -0.4 (Zero page) | — |
| Fee | 15% performance fee, high-water mark, quarterly | — |
| Creation | 25 trading decisions, 15 days since first trade, min balance 1,000 EUR/USD/GBP, live MT4/MT5, manual approval | one account = one DARWIN; allowed instruments |
| Capacity | used capacity = max(current / max monthly divergence, investor capital / max); default max divergence -1%; closes at 100%, reopens below 95% | — |
| Allocation drawdown floor | none beyond the 900 equity exclusion | any other loss condition |
| Min trade duration, martingale, grid | no ban found; martingale «not allowed» is 🤔 third-party only | Darwinex's own stance |

Gathered 2026-10-06 from Darwinex's own pages (📓 documents, not tested). Source notes: scratchpad `darwinex-rules.md` (session-local).
- https://help.darwinex.com/risk-manager , https://help.darwinex.com/darwin-vs-its-underlying-trading-strategy (no date)
- https://help.darwinex.com/d-score , https://help.darwinex.com/what-are-investable-attributes
- https://help.darwinex.com/darwinia , https://help.darwinex.com/what-is-darwinia (no date); https://darwinexzero.document360.io/docs/darwinia-gold ("Updated: 2026-03-23")
- https://help.darwinex.com/how-to-create-a-darwin , https://help.darwinex.com/used-capacity (references Nov–Dec 2023)
- Third-party only: Zero's 25,000 EUR Booster, Oct 2025 recap totals (thegodfunded.com, snippets); martingale and cross-account hedging snippet.
