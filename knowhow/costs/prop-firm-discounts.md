---
q: how to detect or verify a prop firm discount code or sale, Hantec CheckDiscount, FTMO discounted price, DROP50, coupon, promo code check without buying
tag: 🔬  date: 2026-09-29  see: prop-firm-catalogue-hantec
---
# Hantec verifies any code per plan through its own `CheckDiscount`; FTMO's sales sit in its pricing table
Hantec: GET the purchase page (cookie + `__RequestVerificationToken`), then POST
`?handler=CheckDiscount` `{"discountCode", "affiliateCode", "selectedPlanId"}` → `validDiscountCode`,
`discountByDiscountCode` in dollars. Aggregator codes are often affiliate codes: try the other box.
The banner ("50% off…") names no code. FTMO has no public code check; its sales are `discounted`,
`discounted_price` and a tooltip in `ftmoPricingTable.prices`. Code: `portfolio/funded/deals/sources.py`.

## Evidence
- 2026-09-29: DROP50 → `discountCodeType` percentage, 50, 99.50 $ off plan 31 (Express 25k, 199 $);
  a made-up code → `validDiscountCode` false. DROP50 is nowhere in the page's HTML.
- The dealHunter's first run: SAVE20 (−20 %) and SAVE15 (−15 %) accepted by Hantec, HTFX rejected;
  FTMO codes on aggregators (TNG 80 %, CHALLENGE 70 %…) not stated by FTMO — not recorded.
- FTMO 2026-09-29: 100k 2-step 540 → 439 €, 1-step 499 → 399 €, "only if you don't already have one
  active".
- Holding a SQLite write transaction across dozens of these requests locks the funding database for
  the weekly refresh: fetch first, then write (`deals/scan.py`).
