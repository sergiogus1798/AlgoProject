---
q: which genetic algorithm GA target / fitness to use? Ret/DD vs Sharpe vs R Expectancy vs RSquared, seed variance run-to-run, Sharpe (IS) threshold 0.6, minimum trades 100, second condition, acceptance vs selection
tag: 🔬  date: 2026-09-05  see: research/is-proxies-top-decile, research/post-selection-bias
---
# GA target is unresolved: run-to-run noise (~16 pp) exceeds every target effect
One run per arm cannot rank GA targets; you need replicates per arm or a fixed seed. What does replicate:
select `Sharpe Ratio (IS)` ≥ 0.6 after the build (one condition only), keep the in-sample floor at ≥ 100
trades (a sanity floor; raising it hurts). Prefer selection on a finished databank; setting it as a
build-time acceptance changes what the GA breeds from — treat that as a new arm.

## Evidence
XAUUSD, five 10,000-strategy runs, same build, IS min 100 trades, only target differs: `OOS` Ret/DD,
`OOS-Sharpe`, `OOS-Rexpect` + `OOS-Rexpect2` (R Expectancy ×2), `OOS-Rsquared`. `reports/XAUUSD/_comparison/2026-09-05/`.
- Same target twice: −16.0 pp [−20.2, −11.7] OOS hit rate at each sample's top 10 % `Sharpe Ratio (IS)`, −17.0 pp Sharpe (OOS).
  Between-target vs Ret/DD baseline: Sharpe +3.4, R Expectancy +6.5, RSquared −1.7 pp. `OOS-Rexpect` looked best (flattest 10→5 % curve) and did not reproduce.
- Prediction failed too: `R Expectancy` has no OOS column; carried-threshold sweep gave every ratio ≈50 % hit.
- Within-sample filter replicates: top 10 % `Sharpe Ratio (IS)` beat own population in all 5 (hit 39.4–56.4 % vs 25.0–33.2 %);
  210-candidate sweep on `OOS-Rexpect2` → `Sharpe Ratio (IS)` best, +11.8 pp at top 10 %, BH-corrected.
- 🤔 Cheaper than replicating arms: more strategies per run, or a seed fixed across arms if SQX exposes one.

Absolute thresholds (top-10 % cut is 0.480/0.580/0.500/0.470/0.390 across runs — percentiles don't transfer), hit on Ret/DD (OOS):

| `Sharpe Ratio (IS)` ≥ | kept | hit % |
|---|---|---|
| 0.5 | 6.1–13.8 % | 39.9–56.0 |
| **0.6** | **3.9–9.6 %** | **43.2–59.1** |
| 0.7 | 2.4–5.7 % | 47.3–64.1 |
| 0.8 | 1.2–2.6 % | 48.0–64.9 |

No knee; 0.6 = all five clear +14 pp with 400–950 survivors per 10,000. `R Expectancy (IS)` ≥ 0.15, `Profit factor (IS)` ≥ 1.20: same axis, saturate.
- Trade floor: hit 25.0–33.2 % at ≥100 → 18.6–23.9 % at ≥800, monotonic in all 5. ≥100 passes 99.1–99.8 %.
- Second condition on top of Sharpe ≥ 0.6: nine tried (`RSquared`, `Stability`, `DoF Ratio`, `Param Count`, `TRL Ratio`,
  `Winning Percent`, `# of trades` ceilings) flip sign at ±3 pp; `DoF Ratio` floor consistently harmful (−3.6 to −22.0 pp).

Targets collapse in sample (Spearman, Ret/DD sample): `R Expectancy`≡`SQN`≡`Profit factor` ρ +1.00; `Sharpe`≡`Sortino`≡`PSR` +1.00;
clusters +0.94; `Ret/DD` +0.98 vs Sharpe; `Ulcer Index %` −0.92; `Net profit` +0.97. Only other axis: `RSquared` (−0.32 to −0.40), neighbour `TRL Ratio` (+0.77).
🤔 A GA climbs a surface, so identically-ranking targets may still search differently (why `SQN` was a diagnostic target) — untestable one run at a time.

📓 `Export Data View` emits `R Expectancy`, `Stability`, `RSquared`, `TRL Ratio`, `DoF Ratio`, `# of trades`, `Max DD %`, `Drawdown`, `Param Count`
at `sampleType="10"` only → no persistence figure for those targets. Fix: add them at `sampleType="20"` in
`user/settings/views/databanks/Export Data View.vw`; changes the column set, so re-export every databank before comparing.
`.sqx` of `OOS` and `OOS-Sharpe` cleared 2026-09-05 — those arms can never be re-exported.
