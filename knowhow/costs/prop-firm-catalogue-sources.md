---
q: where does each prop firm's catalogue come from, FundedNext packages Next.js payload, FundingPips blocked Vercel checkpoint Cloudflare, which firm sites can be read by code, manual catalogue
tag: 🔬  date: 2026-09-29  see: prop-firm-catalogue-hantec, prop-firm-discounts
---
# FundedNext's catalogue is inline in its home page; FundingPips' site cannot be read by code — typed, never forced
- FundedNext: the home page's `self.__next_f.push` chunks, joined and JSON-unescaped, hold two
  `"packages":[…]` arrays — CFD (Stellar 2-Step, 1-Step, Lite, Instant, FNL 001) and futures (Flex,
  Legacy, Rapid, not MT5). Per plan: `originalPrice` (list, only when on sale), `discountedPrice`,
  `promoCode`, and rule lists in dollars (`challengeRules`, `fundedRewardRules`).
- FundingPips: `fundingpips.com` answers 429 with a Vercel Security Checkpoint, its help centre 403
  (Cloudflare), aggregators (propfirmmatch) 403. Its catalogue is typed in `manual/fundingpips.yaml`.
  Getting past a bot protection is not done here.

## Evidence
- 2026-09-29: `portfolio/funded/catalog/fundednext.py` → 23 CFD plans; START6K on the 6k 2-Step
  (59.99 → 29.99). FundedNext's EAs: below 50k only, with an EA fee of unpublished amount
  (help.fundednext.com, article 8020763, updated 2026-09-08).
- `curl -A Mozilla/5.0 https://fundingpips.com/` → 429, title "Vercel Security Checkpoint";
  WebFetch → 429. propfirmsfinder.com (readable) lists FundingPips prices after a 20 % code.
