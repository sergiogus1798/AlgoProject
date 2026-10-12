---
q: What does step 20 use as its benchmark, and how is it built from random traders?
kw: blindJoint benchmark, paso 20, SPA StepM benchmark, buy and hold equal risk replaced, random trader same footprint daily series, mean of random traders, benchmark.draws 2000, Monte Carlo error mc_day, calibrate.charged no spread, reprice.pnl, time-averaged exposure
tag: 🔬  date: 2026-10-11  see: research/random-trader-oos-only, research/monkey-reprice-audit, research/random-entry-nulls
---
# Step 20 judges each mother against the MEAN day of random traders with her own footprint
- Owner, 2026-10-11: equal-risk buy and hold is gone from `studies/closing/blindJoint`. The excess the SPA and the StepM read is `mother's day − mean day of benchmark.draws random traders` who take her oos2 trades (count, side, lots, each trade's own hold, declared costs) at uniform entries over oos2. Null: no mother earns more than her own trades entered at random — conditional on her footprint, only *when she enters* is tested.
- The ladder's kernel (`engines/nulls/kernel.py`) returns five statistics per run, never days. A mean needs no per-run days: it is linear, so `benchmark.footprint` draws with `model.RUNGS[rung]`, averages the position per M1 bar, and marks it at each day's last M1 close. Away from the segment's edges that mean is 🤔 buy and hold at her time-averaged lots minus her costs.
- **Never price it with `calibrate.charged`** (the ladder's cost): it holds no spread or slippage. In the monkey study that cancels, the real run being repriced alike; here the mother's side is SQX's P&L, so the benchmark would be under-charged by `PV·size·(spread + 2·slippage)` per trade. It is priced by `reprice.pnl` at `reprice.costs(feed, "oos2")`.
- Monte Carlo error of the mean ≈ `1/sqrt(draws)` of the mother's own standard error: 2.2 % at 2,000 (variance +0.05 %, a t moved < 0.05). The bootstrap does not resample it; `mc_day` prints it per mother.
- No look added: it reads the mothers' oos2 trades and M1 bars `inputs.panel` already opens behind `gate.allow(20, "oos2")`.

## Evidence
`tests/test_blindjoint.py` (2026-10-11): on a synthetic market drifting up, 50 long mothers that ARE
random traders of their own footprint earn 180 each and exceed their benchmark by −2.5 (z −1.54);
the StepM names one in 0 of 10 families; a constant +3 per trade on one mother moves her total
excess by exactly 3 × trades and she alone is named in 10 of 10. Off the test, 300 such mothers:
mean excess +0.25 (z 0.39) against a drift of 181; `mc_day` / mother's standard error 1.2 % median,
1.5 % worst (150 trades, 2,000 draws). Not yet run on a real oos2.
