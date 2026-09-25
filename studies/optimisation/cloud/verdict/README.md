# parameterCloud/verdict — what the numbers mean

| file | what it does | in → out |
|---|---|---|
| `call.py` | Turns each measurement into one of the named readings, against frozen thresholds | numbers → readings |

Computes none of the numbers it judges, and **never selects a variant**. The readings describe the
cloud; replacing theta-zero with a better-scoring clone would make the cloud a larger optimisation
and the strategy more overfit, not less. That is the one rule the whole module exists under.

**The thresholds live in `config.yaml` and belong to the owner.** A threshold moved after seeing the
numbers is not a threshold.
