# studies/breakage/spp — does this strategy deserve 5,000 variants?

Stage 1 of the robustness protocol. It reads the Sys. Param Permutation grid SQX already computed
and answers three things: **what moves the result, what is provably dead, and whether the family is
anything but noise.** It produces two outputs, not one — a report for the owner, and the
`design_brief.json` the fabrication stage consumes.

It never talks to SQX. The owner runs the SPP and names the databank; this reads what came out.

The window shows two panels (rebuilt 2026-09-30, feedback §7), independent of the noise call above
and of the design brief: **panel 1** is a histogram per metric — Net Profit, Profit Factor,
Retorno/Drawdown, Max Drawdown, Sharpe, Sortino — over the whole permutation grid, the real backtest
and the median marked, a band of median ± a configured share of its own value, for a period the
reader picks (solo IS, solo OOS1, or the two combined); **panel 2** overlays IS and OOS1 as
transparent densities, but only for metrics that do not grow with the window (Sharpe, Sortino,
Profit Factor, R/Edge ratio — never Net Profit or Ret/DD). What used to be six tabs of
parameter-by-parameter reconnaissance (influence, plateaus, pairwise surfaces, the fabrication
design) are no longer shown — `run.py`'s reading and `model/` still compute all of it, because
`sqx/variants` still needs the design brief; the window just stopped drawing them.

```
config.yaml ─▶ inputs ─▶ model ─▶ verdict ─▶ contract
 every knob   the grid   what      is it     the report
              and the    moves it  worth
              original   and what  more?
                         is dead
```

| folder | the question it answers | read its README before |
|---|---|---|
| `inputs/` | what grid is this, its IS/OOS pair, and what was the original tuple? | touching an export path or a column name |
| `model/` | what does a number read off this grid mean, and how do IS and OOS1 combine? | changing how a parameter is judged live or dead, or the combined metrics |
| `verdict/` | is this family worth the next stage? | moving the noise threshold |

| file | what it does | run it |
|---|---|---|
| `run.py` | One strategy's whole reading (eta², duplicate test, plateaus, noise verdict), and the design brief derived from it — internal now, feeds `sqx/variants` and the noise verdict, not drawn tab by tab | imported |
| `contract.py` | The reading as the contract's tabs: the noise verdict, panel 1 (histograms per period) and panel 2 (IS/OOS1 overlaid, time-free metrics) | imported |
| `one.py` | **One strategy as the contract's data**: finds the strategy's IS/OOS pair on disk, builds both panels, still carries the brief in the summary | imported — the window calls it |
| `report.py` | The command: every strategy of one export to `reports/<P>/<D>/<day>/spp/` — a page and a JSON each, and the `design_brief_<strategy>.json` the fabrication reads — plus `strategies.csv` (`strategy, identity, brief, note`), what pairs the folder by identity (the archive, the matrix); a `--strategy` run rewrites it with those strategies only | `python3 -m studies.breakage.spp.report --project XAUUSD --databank SPP_IS` |
| `tooltips.py` | One sentence per `config.yaml` knob, for the window's configuration drawer | imported |
| `config.yaml` | Every tunable, grouped by the layer that reads it | edited, or `--set section.key=value` |

## The panels read IS and OOS1 as two separate exports, not one databank

`--databank` still names one export (SPP_IS or SPP_OOS), the one the design brief and the noise
verdict are read from, unchanged. `one.py` additionally finds its **pair** on disk
(`inputs.config.other`, by name: `SPP_IS` ↔ `SPP_OOS`) and reads both grids for the panels — this
is a Python-side join, nothing in SQX is touched. The pair may not exist yet (OOS lags IS as a
rule): panel 1 then offers only the one period it has, and panel 2 does not appear, both said in a
note rather than shown empty (§1: no false "sin datos", nothing drawn that cannot be).

**"Combinado" is not a third SPP run — there isn't one.** SPP grids of different windows cannot be
paired (see below): so `model/combine.py` rebuilds Net Profit, Profit Factor, Max Drawdown and
Ret/DD from their additive components (summing a real concatenated backtest could show, Max
Drawdown as an upper bound), and only pools Sharpe and Sortino as a wider sample, since those need
the permutation's own trades to recompute properly and the export does not carry them. The real
backtest's own Sharpe/Sortino under "combinado" needs the actual concatenated trades
(`export_trades`, both sides); when that export is missing, the panel says so instead of guessing.

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
The one-parameter profiles in `run.read` leave it out too (`inputs.export.without_original`,
`OPEN.md` #79, fixed 2026-09-29) — every design brief made before that date needs re-running.

## Open, and deliberate

Read `POSSIBLE_IMPROVEMENTS.md`. The first item is the one that matters: the symmetric-span rule
gives a **narrow** range to a parameter whose centre, argmax and original sit close together, even
when it is the most influential one on the axis that counts. For shifts this is handled by routing
them to their own saturated design (the brief marks `is_shift`); for anything else it is not handled
yet, and it is a modelling choice, not a bug to quietly patch.
