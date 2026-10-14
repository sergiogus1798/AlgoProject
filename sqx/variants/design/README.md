# sqx/variants/design — which combinations, and why those

Pure maths. Nothing here opens a `.sqx` or writes a byte; it turns contract C1 into a table of
tuples. That is what makes the design arguable on its own: the grid can be changed and inspected
without fabricating anything, with `make.py --design-only`.

| file | what it does | in → out |
|---|---|---|
| `canaries.py` | The controls: tuples whose result is known before the retest runs, and the pairs that must tie. | brief, known results → rows |
| `levels.py` | The values each parameter may take: the plateau for the live ones, a rebuilt range for the frozen. | brief → levels |
| `lhs.py` | The design: a Latin hypercube over the live parameters, inside their in-sample plateau. | box, n, seed → tuples |
| `pilot.py` | Which few hundred tuples the pilot samples, and which levels its trade counts drop. Pure maths. | live levels, trade counts → banned levels |
| `plan.py` | Turn one design brief into the list of tuples to fabricate. Pure maths; touches no file. | brief, banned levels → the plan |

## The pilot, before any of it (OPEN.md #41, owner 2026-09-29)

ON by default (`pilot.enabled`, `--no-pilot` to skip). Half a design's budget can go on
combinations that barely trade (🔬 2026-09-24: 1,002 of 2,000 fabricated rows under 30 trades in
sample) — a region nothing in this folder knew was silent until the whole batch had already been
fabricated, loaded and retested. The pilot answers that cheaply, before the hypercube draws from the
live levels: `pilot.sample` draws a few hundred tuples over the live parameters (Sobol, the
frozen ones untouched — whether a region trades is decided by what moves), `sqx.variants.pilot`
fabricates and retests them on the same project the full batch will use, and `pilot.decide` reads
back which live-parameter LEVELS (never a whole parameter, and never the origin's own value) traded
below `pilot.min_trades` with enough support (`pilot.min_support`) to trust the median. `plan.build`
then removes exactly those levels before the hypercube samples from them, and names them in its own
report (`pilot_dropped`) and in `pilot.json` — a batch is never smaller than what it says it is.

## The design (encargo 48 F, owner 2026-10-07 — replaces the three strata)

One Latin hypercube over the live parameters, inside `[plateau.from, plateau.to]` of the SPP IS
(**build only**: a brief whose source is `SPP_OOS` is refused by `inputs.brief`). The WFC asks what
happens if an optimiser chooses inside the family, so the batch has to be a representative sample of
what could be chosen, not corners nor a heap on one point. Frozen parameters and shifts
(`mapa.is_fixed`, the only source of the patterns) are fixed at the mother's value in every variant;
`class` in the brief says which is which (`live`, `shift`, `frozen`).

`n = min(n_max, max(n_min, per_coefficient × p))`, `p = 1 + 2k + k(k-1)/2`, `k` = live parameters
(ledger rows `variants.*`). `n` counts the analysed variants; the controls come on top. `n` is a cap:
a tuple is never repeated, and the report (`design.json`, `build.json`) carries `capped` (the cap cut
it: fewer than 8 variants per coefficient) and `shortfall` (duplicates after rounding).

`stratum` is `lhs`, `origin` (`P00000`), `canary` or `inert`. The last three are controls and enter
no analysis.
