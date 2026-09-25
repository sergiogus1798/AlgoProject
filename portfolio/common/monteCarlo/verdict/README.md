# monteCarlo/verdict — given those numbers, what do we conclude?

The inference layer: the statistics that are not simulations, and the decision. It reads a `result`
dict that `run.py` already filled and turns it into flags, sub-scores, a composite, a tier and the
one constraint that is holding the score down. **It computes none of the numbers it judges**, and it
does not import `simulate/` at all — a module that drew its own paths and then graded them could not
be cross-examined.

**Imports from:** `inputs/` (for `HEADLINE`/`BASELINE`) and itself
**Consumed by:** `run.py`, `render/`, `explorer/`
**Must not contain:** a simulation, an equity path, or any HTML

| file | what it does | run it | in → out |
|---|---|---|---|
| `confidence.py` | Whether the sample can hold up a number | imported | N, q → tier |
| `significance.py` | **Family E.** Probabilistic Sharpe Ratio and its cross-check against the bootstrap | imported | P&L → PSR |
| `gates.py` | **Every threshold in the study.** What vetoes, what only warns | imported | result → flags |
| `scoring.py` | Sub-scores, composite, verdict tier and the binding constraint | imported | result → verdict |

## Contracts and traps

- **Every threshold in the study is in `gates.py`, and nowhere else.** That is the property that
  makes a verdict arguable: one file can be read end to end and disagreed with. A limit hard-coded
  in `render/` or `simulate/` would be a rule nobody can find — if you need one there, it belongs
  here instead. To change what disqualifies a strategy, change `config.yaml` and `gates.py`.
- **A flag is not a veto.** `gates.check()` returns every check that fired; only those with
  `gate=True` disqualify. The rest have to be *seen* — printed in the report — and deliberately do
  not move the verdict.
- **`INCONCLUSIVE` is not `FAIL`.** `confidence.py` tags each statistic `reliable` /
  `provisional` / `unreliable` from its sample size, and a verdict resting on unreliable numbers is
  reported as inconclusive rather than dressed up as a judgement.
- **The composite never overrules a veto**, and `BUILT_FROM` exists so the report can print what
  each sub-score was made of: a score whose ingredients are invisible is a number nobody can argue
  with.
- **This study does not measure overfitting and never will.** No Deflated Sharpe, no CSCV: both need
  the population of strategies tried during generation, which does not exist at this stage.
  Fabricating a trial count would produce a credible, false number. That question belongs to the
  generation study.
