# studies/breakage/spp — does this strategy deserve 5,000 variants?

Stage 1 of the robustness protocol. It reads the Sys. Param Permutation grid SQX already computed
and answers three things: **what moves the result, what is provably dead, and whether the family is
anything but noise.** It produces two outputs, not one — a report for the owner, and the
`design_brief.json` the fabrication stage consumes.

It never talks to SQX. The owner runs the SPP and names the databank; this reads what came out.

```
config.yaml ─▶ inputs ─▶ model ─▶ verdict ─▶ contract
 every knob   the grid   what      is it     the report
              and the    moves it  worth
              original   and what  more?
                         is dead
```

| folder | the question it answers | read its README before |
|---|---|---|
| `inputs/` | what grid is this, and what was the original tuple? | touching an export path or a column name |
| `model/` | what does a number read off this grid mean? | changing how a parameter is judged live or dead |
| `verdict/` | is this family worth the next stage? | moving the noise threshold |

| file | what it does | run it |
|---|---|---|
| `run.py` | One strategy's whole reading, and the brief derived from it | imported |
| `surface.py` | Two parameters at a time: the verdict metric's median on every cell of each ordered pair's grid, θ₀ left out of the cells, the top decile as plateau, and where θ₀ sits | imported |
| `contract.py` | The reading as the contract's tabs: the noise call, influence, plateaus, the pair surfaces (a `grid` per ordered pair, «Eje X» / «Eje Y» selectors, θ₀ as `mark`) and the design | imported |
| `one.py` | **One strategy as the contract's data**, its brief carried in the summary | imported — the window calls it |
| `report.py` | The command: every strategy of one export to `reports/<P>/<D>/<day>/spp/` — a page and a JSON each, and the `design_brief_<strategy>.json` the fabrication reads — plus `strategies.csv` (`strategy, identity, brief, note`), what pairs the folder by identity (the archive, the matrix); a `--strategy` run rewrites it with those strategies only | `python3 -m studies.breakage.spp.report --project XAUUSD --databank SPP_IS` |
| `tooltips.py` | One sentence per `config.yaml` knob, for the window's configuration drawer | imported |
| `config.yaml` | Every tunable, grouped by the layer that reads it | edited, or `--set section.key=value` |

## The three things this module exists to get right

**Two SPP runs cannot be paired.** 🔬 Measured 2026-09-19 on `Strategy 17.9.39`: the IS run and the
OOS run, same strategy and byte-identical settings, share **6 tuples out of ~11,600**. So nothing
here compares two windows — not because it was not built, but because the data cannot support it.
That is the entire reason the 5,000 designed variants exist, and the report says so in its first
paragraph.

**Freezing is decided by the duplicate test, not by eta-squared.** An SPP samples unbalanced, so an
inert parameter still scores above any threshold you would pick — `CBlock_SqzMmnInt21` is proven
inert (217 groups, 217 identical) at eta-squared 0.0173. Details in `model/README.md`. This is the
one place where following the obvious rule would have silently shrunk every design.

**The design must be able to show that the plateau moved.** The centre of an in-sample plateau is an
estimate. Centre the variant grid on it and trim, and an out-of-sample plateau that shifted falls
outside the grid and nobody finds out. `design_levels` spans symmetrically and widens until it
contains the original tuple and the in-sample argmax as well.

**θ₀ never vouches for itself on a surface.** A two-parameter cell is the median of every tuple
that used that pair of levels — *other than θ₀*. 🔬 SQX's step grid missed θ₀'s own level of
`BBerDeviation1` on all three USDJPY M30 SPPs (2026-09-27), so its cell held θ₀ alone and read "on
the plateau" by construction; now it is empty and says so (`knowhow/research/spp-origin-level-sampled-once.md`).
The one-parameter profiles in `model/` still include it: `OPEN.md` §79.

## Open, and deliberate

Read `POSSIBLE_IMPROVEMENTS.md`. The first item is the one that matters: the symmetric-span rule
gives a **narrow** range to a parameter whose centre, argmax and original sit close together, even
when it is the most influential one on the axis that counts. For shifts this is handled by routing
them to their own saturated design (the brief marks `is_shift`); for anything else it is not handled
yet, and it is a modelling choice, not a bug to quietly patch.
