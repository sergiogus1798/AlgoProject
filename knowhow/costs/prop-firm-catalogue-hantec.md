---
q: where do Hantec Trader's challenge prices, rules and add-on surcharges come from, how is the price of a plan with add-ons computed, prop firm funded account catalogue scrape
tag: 🔬  date: 2026-09-29
---
# Hantec's whole price list is one public JSON: `GET /purchasechallenge?handler=InitState`
No login, no browser. `plans[]` holds every plan (type × size) with its price and rules; each plan's
`addons[]` gives a surcharge `pricePct`. **Price = base + Σ base·pricePct/100, then the discount on
that total** — add-ons are additive on the base, not compounding. The JSON lacks: phase-2/3 targets,
the base reward share (`profitSharePct` 0 — it is 80 %), fee refund, minimum payout, and the funded
news window (`newsProhibited` false, yet challenge funded accounts may not trade 3 min around
red-folder news without the add-on). Those live in `AlgoData/funding/rules/hantec.yaml`, sourced
from the help centre's per-program articles, which are the firm's own and current.

## Evidence
- `curl -A Mozilla/5.0 'https://myhtrader.hmarkets.com/purchasechallenge?handler=InitState'` →
  44 plans, 2026-09-29; raw in `AlgoData/funding/catalogs/hantec/`, parsed by
  `portfolio/funded/catalog/hantec.py` into `funding.sqlite`.
- Formula: `/js/pages/purchase-challenge-v2.js`, `calculateTotalPrice()` (≈ l.1665-1685):
  `addon price = plan.price * pct/100`; `finalPrice = base + addons - discount(base + addons)`.
- `challengeType`: 1 = 1-step (Express), 2 = 2-step (Enhanced, EnhancedX), 3 = 3-step (Endurance),
  99 = instant (Instant24, Instant Lite, Instant Funding). `staticDrawdown` false = trailing.
- The HTML lists ~30 add-ons (BOGO, double leverage, reward protection…) all "+0%"; only 13 keys are
  active in the JSON — the HTML list is a template, the JSON is the offer.
- Consistency on the page: "Consistency Score (%) = (Best Day's Profit + Total Profit) × 100" — the
  operator was lost in rendering; read it as Best Day ÷ Total 🤔 (confirm in the Terms).
- Help centre, `solutions/articles/158000445797-express-1-step-` (read 2026-09-29): "The default
  profit split is 80%", add-on to 95 %; no minimum days; weekend holding permitted; the 6 % trailing
  loss locks at the starting balance at +6 % and at the first withdrawal. A search snippet of an
  older page said 75 % / 90 %, and third-party reviews said 3 days and no weekends: all wrong.
- The site advertises a code DROP50 (−50 %, not on Instant24); `discountCodes` comes back empty, so
  promotions are not in the catalogue and the price paid must be an input.
