---
q: What does restricting the gate monkey to the strategy's own entry hours do to z_mono, and what is its MC error?
kw: z_mono hours, mono con horas, monkey same hour of day, windowed.draw by_hour, intraday drift, USATEC H1 ruptura, Monte Carlo standard error of z, draws cost
tag: 🔬  date: 2026-10-12  see: gate-monkey-z-tracks-drift-t, monkey-reprice-audit
---
# The monkey that enters at the strategy's own hours passes 98 of 169 on USATEC H1 ruptura, against 65 for the uniform one
`windowed.draw` now re-enters each trade at a uniform eligible bar of its calendar window AND of the clock hour of the real entry (encargo 65 §5.0), so the monkey has the strategy's count per hour. On 169 alive strategies of `Test_USATEC_H1_ruptura_leaseWeb` (2026-10-11 export, 5,000 draws, same seed) `z_mono >= 1.65` went 65 -> 98 (63 in both, 2 lost, 35 gained; mean z 1.62 -> 1.73): the uniform null credited hour-of-day drift to the strategy's timing in the other direction, i.e. spread entries over hours with a different intraday drift. Replaying the old null with the new code reproduces the stored scorecard exactly (max |dz| = 0).
MC error of z at N draws is ~ sqrt((1 + z^2/2)/N): 0.022 at z = 1.645 (p = 0.05), 0.027 at z = 2.24 (p = 0.0125) for N = 5,000; measured over 12 seeds on the ten strategies nearest the cut: mean sd 0.022. The empirical p has se sqrt(p(1-p)/N) = 0.0031 (p = 0.05) and 0.0016 (p = 0.0125). Cost is linear in draws: ~0.12 ms per draw per 10 strategies (263 trades each) beyond 5,000; 169 strategies x 4 rungs x 5,000 draws = 5 s on this machine.

## Evidence
Scratch run 2026-10-12 (not kept); known answers in `tests/test_gate_mono.py` (15:00-only strategy -> 15:00-only monkeys with the same count; two hours keep both counts; session mask respected).
