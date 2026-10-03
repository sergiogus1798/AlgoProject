---
q: What does `funding.sqlite` not hold for the funded stage, and which `gaps.*` inputs of `portfolio/funded/sim` fill it?
kw: funded stage payout_days reward_share fee_refund catalogue gap, catalog.plan funded stage min_days, Endurance payout days NULL, Hantec fee refund unknown, combos consistency_pct NULL EnhancedX, FTMO price EUR account USD, what the bank simulation needs that funding.sqlite lacks, gaps config
tag: 📓  date: 2026-10-02  see: costs/prop-firm-catalogue-hantec, research/funded-bank-ev-read-against-the-monkey
---
# What `funding.sqlite` does not hold for the FUNDED stage — each is an explicit `gaps.*` input of `portfolio/funded/sim`
- `rules.catalog.plan()` returns no split and no payout frequency: read `stages` or `combos`.
  NULL today: **Hantec Endurance `payout_days`**, **Hantec `fee_refund`**.
- Nothing says what a withdrawal does to a **trailing** floor (Express, FTMO 1-step funded):
  `trailing_lock` locks at +6 %, encargo 33 §3.5.4 says at the first withdrawal — the owner's call.
- Apply an add-on as the difference between its `combos` row and the bare row, plus the option's
  name: `combos` carries the first phase's raw values, not the curated ones.
- FTMO's USD accounts are **priced in EUR**: the rate is an input, written with the result.

## Evidence
`sqlite3 'file:…/funding.sqlite?mode=ro'`, 2026-10-02:
- `stages` of `hantec:endurance:10000:USD`: funded `payout_days` NULL, `reward_share_pct` 80.
- `rules.fee_refund`: hantec NULL unconfirmed; ftmo 1step `False`, 2step `True` with
  `fee_refund_scope` unconfirmed (read as per account).
- `plan()` gives the funded stage the challenge's curated `min_days` and consistency (FTMO 2-step
  funded: 4, where `stages` says 0); the simulation applies them per payout cycle.
- `combos.min_days` is 0 for Endurance with or without `NO_MINIMUM_TRADING_DAYS` (curated: 3);
  EnhancedX `consistency_pct` is NULL, so `CONSISTENCY_RULE` has no computed effect.
- No column for the minimum payout amount, the first payout's timing or `FIRST_PAYOUT_ON_DEMAND`.
- `plans.terms()` raises `Gap` naming each missing key (`tests/test_funded_bank.py` §3).
