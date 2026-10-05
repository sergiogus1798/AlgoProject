---
q: Why does a zero-edge trader show positive bank EV on some prop plans?
kw: bank EV of a prop firm plan with zero edge, monkey EV positive funded account, VE_banco mono, funded account is an option on volatility, Express withdraw everything trailing floor after payout, payout cushion, floor_after_payout stays initial, haircut h break-even, advantage over the monkey, bank horizon, rebuy same_plan vs none, EV(h=1) positive, optional stopping
tag: 🔬  date: 2026-10-05  see: research/hardest-null, costs/funded-stage-catalogue-gaps
---
# A zero-edge trader's bank EV turns POSITIVE with the horizon on static-floor plans — read the advantage, never compare horizons
- A funded account is a call on the P&L: a costless zero-drift trader on a static max loss withdraws
  on average the whole max-loss allowance if given time (optional stopping). Read `advantage` = EV −
  the monkey's at its best risk; the `demean` monkey pays no costs (`--monkey` takes real random entries).
- EV is «over the horizon»: ≤ 0 on every plan at 504 days, > 0 on three at 1,008. `same_plan` loses to `none`
  wherever one account's EV is negative; late accounts pay a whole fee for a truncated life.
- A trailing funded floor moving to the initial balance at the first withdrawal
  (`gaps.<firm>_<family>_floor_after_payout`) decides Hantec Express and FTMO 1-Step.

## Evidence
Synthetic set (2,000 × 1,250 days, 60 % closing days, N(0.10 R, 1 R) per closing day, intraday
excursion |N(0, 0.3 R)|), budget 1,000 EUR at 1.17, re-buy same plan, no frictions, risk grid 0.25/0.5/1 %.
- Monkey EV over the horizon, `stays`, cushion 0: FTMO 1-step +709, FTMO 2-step +524, Enhanced 10k
  +432, Endurance 10k +172, Express 10k −161 USD.
- Express 10k at h = 0.5, risk 1 % → 0.5 %, `stays`: cushion 0 → EV +672, 0.02 → +356, 0.04 → +225.
  `initial`, cushion 0.02, risk re-searched: −56. FTMO 1-step: `stays`, cushion 0 → +2,248; `initial`,
  cushion 0.02 → +331.
- `tests/test_funded_sim.py` §3: +7 % withdrawn in full under a locked floor dies on the next tick.
2026-10-05, the Nikkei test pool's funded portfolio (K = 4, Hantec Express 10k; test root, relaxed,
test owner inputs — not a result), 10,000 paths, T2@2, edge recentred on oos1+oos2 (20 % of build's),
no refund anywhere, floors `stays`, tax 20 %, fee 2 %, denied 5 %, firm closes 10 %/yr:
- 504 days: max EV(h = 1) over 22 plan × policy rows −6.7 (seed 1), −8.0 (seed 2). 1,008 days: FTMO
  1-step `none` +11.5, FTMO 2-step `none` +8.7, Enhanced 10k `none` +0.8.
- h = 0.5, 504 days, `none` vs `same_plan`: FTMO 2-step +13.6 ± 4.2 vs −77.5 ± 3.9; Express 10k −71.2
  vs −175.8. Under `none` the worst draw is exactly −price on every row.
- Seed to seed the EVs differ by mean |z| 0.58, max 1.59 of the reported `ev_se`: the error is honest.
- `tests/test_funded_decide.py`: zero drift, static floor, no frictions, long horizon →
  mean withdrawn 1,097 ± 18 against the 1,100 allowance.
