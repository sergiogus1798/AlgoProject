---
q: IS proxies inside top Sharpe decile, TRL Ratio SQN ZScore R Expectancy, Param Count negative, second filter after Sharpe, regression to the mean stratify
tag: 🤔  date: 2026-09-06  see: research/ga-target-choice, research/post-selection-bias
---
# Per-trade edge quality separates survivors inside the top Sharpe decile — not shippable yet
Stratify on `Sharpe Ratio (IS)` first (removes mechanical regression to the mean). Inside the top decile,
`TRL Ratio`, `SQN`, `ZScore`, `R Expectancy` (IS) lean positive 5/5 — one axis, not four findings. Contradicts the
nine-candidate result (TRL flipped sign above absolute 0.6). Not a filter until run through `improvement.py`
(bootstrap interval) and `replication.py`.

## Evidence
Each of 5 XAUUSD runs, top decile `Sharpe Ratio (IS)` (n=1000, baseline hit 39.4–56.7 % on NP(OOS)>0), split at candidate median, high − low:

| candidate | per-run gap (pp) | mean |
|---|---|---|
| `TRL Ratio (IS)` | +5.0 +14.8 +7.4 +6.8 +5.2 | **+7.8** |
| `SQN (IS)` | +4.2 +7.6 +9.0 +3.6 +2.8 | +5.4 |
| `ZScore (IS)` | +12.2 +2.0 +4.2 +0.4 +6.0 | +5.0 |
| `R Expectancy (IS)` | +3.4 +8.4 +8.6 +2.8 +1.2 | +4.9 |
| `Param Count (IS)` | −0.6 −11.2 −3.0 −8.4 +3.2 | −4.0 |
| `DoF Ratio (IS)`, `# of trades (IS)` | sign changes | ~−3 |

Difference from the contradicting result: stratification (top decile vs absolute 0.6) and outcome (NP(OOS)>0 vs Ret/DD(OOS)).
`Param Count` leans negative — the direction overfitting theory predicts.
