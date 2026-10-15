---
q: What does `funding.sqlite` not hold for the funded stage, and which `gaps.*` inputs of `portfolio/funded/sim` fill it?
kw: funded stage payout_days reward_share fee_refund catalogue gap, catalog.plan funded stage min_days, Endurance payout days NULL, Hantec fee refund unknown, combos consistency_pct NULL EnhancedX, FTMO price EUR account USD, what the bank simulation needs that funding.sqlite lacks, gaps config
tag: 📓  date: 2026-10-14  see: costs/prop-firm-catalogue-hantec, research/funded-bank-ev-read-against-the-monkey
---
# What `funding.sqlite` does not hold for the FUNDED stage — each is an explicit `gaps.*` input of `portfolio/funded/sim`
- `rules.catalog.plan()` returns no split and no payout frequency: read `stages` or `combos`.
- A withdrawal's effect on a **trailing** floor (Express, FTMO 1-step funded) is not in the catalogue.
- **Answered 2026-10-14 (encargo 54, B), in `portfolio/funded/sim/config.yaml`:** Hantec refund `false`,
  Endurance payout `14` days, floor after payout `initial` (Express) / `stays` (FTMO 1-step, ambiguous).
  FTMO 2-step DOES refund the fee (`rules/ftmo.yaml`, confirmed; the Council's `false` was wrong).
  Answered 2026-10-15: `tax_rate` 0.40 (display only, never in the kernel), `p_payout_denied` 0.05 per payout.

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

- 2026-10-14: the owner edits these from the window (Fondeo/Banco › «Entradas del dueño»); it writes the local layer
  `config/owner.yaml` (not in git, so gorilla never sees it), laid over the YAML by
  `core.study.config.load(owner=...)` before `--set`.
- Add-ons apply as the difference between a `combos` row and the bare row; FTMO's USD accounts are priced in EUR (the rate is an input, written with the result).
