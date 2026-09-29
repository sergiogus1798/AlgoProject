# portfolio/funded/deals — prop-firm offers: found daily, checked with the firm, notified, judged

Owner, 2026-09-29: discounts come and go; hear of each the day it appears, and have one command that
says whether it is worth it. Everything lives in the `deals` table of the funding database
(`portfolio/funded/catalog/README.md`), one row per deal × plan.

Every day at 10:00 `bin/daily-funding-deals.sh` runs three stages:

1. **scan** — the places a firm shows offers: FTMO's pricing table (`discounted_price`), Hantec's
   purchase-page banner ("50% off all Challenges…", no code), and every Hantec code on the books,
   re-checked plan by plan. What is not seen again is marked `expired`.
2. **the `dealHunter` agent** — searches the web for codes no firm page shows and records each only
   through `add`: Hantec's own `CheckDiscount` decides; an FTMO code (no public check) is stored
   `unverified` and only on FTMO's own word or two agreeing sources.
3. **notify** — one desktop notification (`notify-send`) per deal touching the owner's universe
   (`book.UNIVERSE_SQL`: 10k USD at most, EAs allowed) not notified yet. A deal that gets better
   (a deeper cut, or valid again) notifies again.

`worth` answers "is it worth it" **provisionally**: every universe plan's expected fees per $1,000
of funded account at the zero-edge floor (barrier geometry), net of the passing account's refunded
fee, at list price and with today's deals, and how far the deal moves each plan in that ranking. It
says nothing about the owner's strategies: that is encargo 33's expected value, and `worth` is where
it plugs in when it exists. FTMO's euros are converted at the ECB's daily rate.

| file | what it does | run it | in → out |
|---|---|---|---|
| `sources.py` | the firms' offer surfaces: FTMO's table, Hantec's banner, Hantec's code check (discount box, then affiliate box) | — | sites → deal rows |
| `book.py` | record what was seen today (new or better is returned), expire what was not; the owner's universe | — | rows → `deals` |
| `scan.py` | stage 1 | `python3 -m portfolio.funded.deals.scan` | sites → `deals` |
| `add.py` | put a found code on the books, checked with the firm where it can be | `python3 -m portfolio.funded.deals.add hantec DROP50 --source <url>` | code → `deals` |
| `notify.py` | stage 3: one desktop notification per new deal in the universe | `python3 -m portfolio.funded.deals.notify` | `deals` → notification |
| `worth.py` | the provisional verdict: the universe ranked per funded $1,000, list vs today | `python3 -m portfolio.funded.deals.worth [deal_id]` | `deals` + catalogue → stdout |
