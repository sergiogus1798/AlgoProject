---
q: Why does a zero-edge trader show positive bank EV on some prop plans?
kw: bank EV of a prop firm plan with zero edge, monkey EV positive funded account, VE_banco mono, funded account is an option on volatility, Express withdraw everything trailing floor after payout, payout cushion, floor_after_payout stays initial, haircut h break-even, advantage over the monkey
tag: 🔬  date: 2026-10-02  see: research/hardest-null, costs/funded-stage-catalogue-gaps
---
# A zero-edge trader has a POSITIVE bank EV on several plans — read the advantage; the floor reading flips the ranking
- A funded account is a call on the P&L, so zero-drift paths earn the bank money on FTMO 2-step,
  Hantec Enhanced and Endurance once costs are left out. Read `advantage` = EV − the monkey's at its
  best risk, never `ev` alone; the `demean` monkey pays no costs (`--monkey` takes real random entries).
- Whether a trailing funded floor moves to the initial balance at the first withdrawal
  (`gaps.<firm>_<family>_floor_after_payout`) decides Hantec Express and FTMO 1-Step. Under `stays`
  a cushion only delays cash: the trap needs one cycle's profit ≥ the max loss.

## Evidence
Synthetic set (2,000 × 1,250 days, 60 % closing days, N(0.10 R, 1 R) per closing day, intraday
excursion |N(0, 0.3 R)|), budget 1,000 EUR at 1.17, re-buy same plan, no frictions, risk grid 0.25/0.5/1 %.
- Monkey EV over the horizon, `stays`, cushion 0: FTMO 1-step +709, FTMO 2-step +524, Enhanced 10k
  +432, Endurance 10k +172, Express 10k −161 USD.
- Express 10k at h = 0.5, risk 1 % → 0.5 %, `stays`: cushion 0 → EV +672, 0.02 → +356, 0.04 → +225.
  `initial`, cushion 0.02, risk re-searched: −56. FTMO 1-step: `stays`, cushion 0 → +2,248; `initial`,
  cushion 0.02 → +331.
- `tests/test_funded_sim.py` §3: +7 % withdrawn in full under a locked floor dies on the next tick.
