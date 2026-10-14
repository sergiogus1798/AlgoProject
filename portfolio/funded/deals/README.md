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
fee, at list price and with today's deals, and how far the deal moves each plan in that ranking. That
floor says nothing about the owner's strategies, so below it `worth` prints **the bank's expected
value** of each universe plan from the newest bank table that covers it
(`portfolio.funded.decide.tables`, encargo 33 §7.7): EV at list, EV with today's price —
`ΔEV = (list − now) × (purchases − refunds)`, exact under re-buy `none`, a constant-purchases
approximation under `same_plan` — and whether the deal turns a negative EV positive. **With no bank
table it says so in one explicit line and the judgement stays the zero-edge floor** — it never
fails for lack of one, so the daily flow is untouched. FTMO's euros are converted at the ECB's daily rate.

| file | what it does | run it | in → out |
|---|---|---|---|
| `add.py` | Put a discount code found somewhere on the books — verified with the firm itself where it can be. | `python3 -m portfolio.funded.deals.add hantec DROP50 --source <url>` | code → `deals` |
| `book.py` | The deals table: record what was seen today, expire what was not, and the universe the owner buys from. | — | rows → `deals` |
| `notify.py` | Tell the owner, with a desktop notification, about every deal in his universe he has not heard of yet. | `python3 -m portfolio.funded.deals.notify` | `deals` → notification |
| `scan.py` | Look at every place a firm shows offers, record what is on today, expire what is gone. | `python3 -m portfolio.funded.deals.scan` | sites → `deals` |
| `sources.py` | Where each firm shows its offers: Hantec's banner and code check, FTMO's pricing table, FundedNext's catalogue. | — | sites → deal rows |
| `worth.py` | Is a deal worth it? Every universe plan at the zero-edge floor and, where a bank table exists, at the bank's expected value — list price against today's. | `python3 -m portfolio.funded.deals.worth [deal_id]` | `deals` + catalogue + bank tables → stdout |
