# 09 — what SQX can charge, and in what unit

How the engine prices a trade. Read this before writing a number into `assets/`, because three of
these fields mean something other than what their name suggests.

All of it verified on this install on 2026-09-22 by decompiling `internal/libs/SQTradingLib.jar` and
reading `internal/extend/Snippets/SQ/Trading/Commissions/*.java`.

## Costs live per task, not per project

🔬 **`InstrumentInfo` is stored inside each task's XML, not once in `project.cfx`.** A project with a
Build task and three retest tasks carries four copies of every instrument's costs, and they are free
to differ. This is what makes a different spread in-sample and out-of-sample expressible at all:
`assets/`'s `spread_is` goes on the build task and `spread_oos` on the rest. It is also a trap — a
cost "fixed" in one task is unchanged in the other three.

## The five commission methods

📓 `CommissionsMethodsList` loads them as snippets from `SQ/Trading/Commissions`. On this install:
`None`, `SizeBased`, `PerTrade`, `PercentageBased`, `Stockpicker`. Across the master's projects only
two are actually in use: **359 instruments on `SizeBased`, 2 on `None`** — `PercentageBased` is used
by nothing yet.

| method | what it charges |
|---|---|
| `SizeBased` | `Commission × size`. Dollars per full lot. |
| `PercentageBased` | `(CommissionPct / 100) × size × openPrice × pointValue` — a % of the notional |

🔬 **Both charge in `computeCommissionsOnOpen` only; `computeCommissionsOnClose` returns 0.**

⚠️ That reading contradicts the export measurement in `04-export.md`, which recovers **$8 per lot per
side, $16 round turn** against `SizeBased 8`. The most likely explanation is that the engine applies
the method to each leg of the order, so "on open" means "on the opening of each order" rather than
"once per trade" — but that is **inferred, not tested**. 🤔 It matters by a factor of two, and the
whole of `assets/`'s `no_forex` commission depends on it. The test is cheap: run one strategy with
`PercentageBased` at a known percentage and recover `gross − reported P/L` per trade, the same
residual `04-export.md` already uses.

## The three swap types

📓 `SwapTypes` = `points`, `percent`, `money`. The master uses `points` on every forex pair and on
gold, and `money` on the index CFDs. All 142 configured instruments share
`tripleSwapOn="WEDNESDAY" rolloutHour="23:00"`, which is why `assets/_policy.yaml` states those once.

`SwapCalculator.calculateSwapCost` computes one night, and the result is multiplied by the number of
nights held (3 on the triple-swap day):

| type | one night costs |
|---|---|
| `points` | `size × pointValue × tickStep × swap` |
| `percent` | `size × pointValue × openPrice × (swap / 100 / 360)` |
| `money` | `size × swap` |

🔬 **The `percent` swap is an ANNUAL rate on the notional, not a nightly one.** SQX divides by 100
*and by 360* — a commercial year — before applying it. Writing one night's percentage into that field
is wrong by 360×.

Worked conversion, for moving an existing `points` swap to `percent` at a chosen reference price:

```
pct_annual = points × tick_size × 36000 / reference_price
```

36000 is the 360 days of the commercial year times the 100 of the percentage. Dropping that 100 is
the easy mistake, and it gives an answer 100× too small that still looks plausible.

Gold's current `-73.42` points long, at tick_size 0.01 and a reference price of 3500:
`73.42 × 0.01 × 36000 / 3500` = **7.55 % annual**; the short side's `+38.76` gives **3.99 %**. Both
check out: priced either way, one night on one lot costs $73.42 and $38.76.

## The MC Retest ranges are absolute points, and the default fits nothing

📓 `RandomizeSpread` and `RandomizeSlippage` each carry a `Min` and a `Max` `Double`, inside the
task XML like every other cost:

```xml
<Method use="true" type="RandomizeSpread">
  <Params><Param key="Min" type="Double">1.0</Param><Param key="Max" type="Double">5.0</Param></Params>
</Method>
```

🔬 **Both are absolute point ranges, not multiples of the instrument's spread.** Swept across every
`project.cfx` on the master on 2026-09-22: `spread 1.0-5.0` and `slippage 0.0-5.0` — SQX's factory
values — are what almost every instrument carries, identical on gold, on the Nikkei and on EURUSD.
On `NIKKEI225_DukasM1_Infinox`, whose `defaultSpread` is 1100, that perturbs the spread between 1
and 5 points, roughly 200× cheaper than the backtest's own cost.

Where real ranges have been set they do sit at the instrument's scale —
`XAUUSD_DukasM1_Infinox` carries `spread 5-12` against a real spread of 10, and
`NIKKEI225_DukasM1_Infinox` `spread 80-200` and `120-400`. 🤔 So the factory value is what an
untouched task inherits, not a choice; `assets/<SYMBOL>.yaml`'s `mc_retest` block is where the
chosen range now lives, and `core.assetdata.mc_pending()` names the assets that still have none.

`RandomizeMinDistance` has the same shape and a factory range of `0.0-10.0`. It is not in `assets/`
yet: the owner asked for the two above.

## Six assets were pointed at a tick feed fourteen years shorter than their own M1

🔬 `-symbol action=list` on the conductor, 2026-09-22. Six of the seventeen assets carried a
`DarwTick` feed as their `sqx_symbol`, and a tick feed on this install starts in 2017 or 2018 while
the `DukasM1` feed of the same instrument reaches back to 2003–2012:

| asset | was | now | history gained |
|---|---|---|---|
| `EURUSD`, `USDJPY` | `*_DarwTick_the5ers`, 2017-10-02 | `*_DukasM1_the5ers`, 2003-05-05 | 14 years |
| `AUDUSD` | 2017-10-02 | 2003-08-04 | 14 years |
| `AUDJPY` | 2017-10-02 | 2003-12-01 | 14 years |
| `NIKKEI225` | 2017-10-02 | 2011-09-19 | 6 years |
| `USA500` | 2018-06-27 | 2012-01-19 | 6 years |

🔬 **The switch changes no cost.** Every `InstrumentInfo` field — spread, commission, swap, tick
size, point value, min distance — is byte-identical between each pair on the master. Only the
history length and the `mc_retest` witness differ. The owner made the call on 2026-09-22.

⚠️ **`SP500ft_Plus02_Infinox` does not exist in SQX at all** — no feed carries that prefix. That
asset cannot be built or tested until the feed is set up, and its `data` is null.

## Refreshing what SQX holds, without touching the master

📓 `sqcli` exposes **`-data action=update`** — the CLI equivalent of the GUI's "Update all" — beside
`import`, `export`, `exportToMT4/5`, `clone` and `timezones`. The full verb reference is
`internal/web/SQUANT/help.txt`, readable without starting anything.

🔬 **But the download has to happen on the master, not a worker.** `bin/sqx-worker.sh` runs
`rsync -a --exclude='History/' "$MASTER/user/data/" "$WORKER/user/data/"` on every start: the flow
is master → worker. `History` is a shared symlink so new bar files would land in the right place,
but the three H2 databases a backtest actually reads are per-install copies, and a worker's fresh
copy is **overwritten by the master's stale one** at the next start. A download run on a worker
therefore disappears, while the master's GUI keeps building on the old bars.

Consequence: automating the download means running `sqcli` on the master, which hard rule 2 forbids
while its GUI is up, and hard rule 1 means snapshotting `user/projects` first. It is the owner's
button, and the honest automation is the *read* side.

🔬 **`python3 -m core.assets --dataranges` is that read side**, and it is safe at any time: it asks
the conductor and rewrites the `data:` line of all seventeen assets in `assets/_policy.yaml`. The
conductor sees the master's store because of the same rsync. Proven on 2026-09-22 — run mid-update,
it caught four feeds moving from `2026-01-16` to `2026-09-22` and left the other thirteen alone.

## Slippage is declared everywhere and measured nowhere

🔬 `defaultSlippage` is **0.0 on every one of the seventeen instruments** the master configures
(swept 2026-09-22). That is SQX's factory value, not a measurement, and it is an optimistic one: a
backtest priced with zero slippage assumes every order filled exactly where it asked.

`assets/symbols/<SYMBOL>.yaml` carries a `slippage` cost field in both classes, in points, and
`sqx_settings()` emits it as `defaultSlippage`. It deliberately does **not** block authoring the way
spread and commission do — `crossmarket`'s execution stress already models worse fills separately
from what the backtest charged.

🤔 **It cannot be measured from an export.** A backtest applies the slippage it is given, so
`gross − P/L` recovers what was assumed, never what a real broker would do. Any figure here is a
convention, and the owner chose **half the spread** on 2026-09-22. That is the one rule that holds
across classes: a flat figure in points cannot, because a point is worth
`tick_size × point_value` and that runs from $0.0065 on the Nikkei to $11.53 on USDCHF — 2.5 points
is $0.02 on one and $28.82 on the other. Half the spread gives $0.33–$5.00 per lot per side across
the seventeen, and on gold it lands on 5 points, the midpoint of the 0–10 range its own MC Retest
already samples.

## Where the spread is

🔬 The spread is **not** a charge. It is baked into the fill prices — `04-export.md` measures gold's
entry sitting exactly 0.05 above the bar open and the exit on it, which is
`defaultSpread = 10.0 points × tick_size 0.01 = 0.10`, half of it per side. It therefore never
appears in the `gross − P/L` residual, and anything that folds a spread into a commission while
leaving `defaultSpread` non-zero **charges it twice**.

## Why `assets/` splits forex from everything else

🤔 A fixed spread in points is a constant cost in dollars while the price moves. Over gold's
2008–2017 build window that is a real slope: 0.10 of spread is 0.0083 % of notional at 1200 and
0.0029 % at 3500, a factor of three inside the sample the generator sees. Currency pairs do not move
like that, so they keep one spread and a dollar commission; everything else gets two spreads and
percentage-based commission and swap. The schema is in `assets/_classes.yaml`, checked by
`core.assets.validate()` rather than remembered.

## What SQX's own FX costs are worth, and why they are not a fallback

📓 Measured 2026-09-23 with `sqx.inspect.instruments` over every `project.cfx` on the master. The ten
`the5ers` pairs carry **`commission: SizeBased 0.00` — zero — and these `defaultSpread` values**, one
per pair with no disagreement between projects:

| 0.1 | 0.2 | 0.6 | 1.2 |
|---|---|---|---|
| USDJPY, EURUSD, GBPUSD, AUDUSD, **CADJPY** | USDCAD, USDCHF | EURJPY, AUDJPY | GBPJPY |

Two things follow, and both matter more for a cross-market test than for a single-asset build.

🤔 **The level is wrong by about 10×.** the5ers charges on the order of 8 $/lot round-turn. On a pair
with `point_value` 100000 a pip is 10 $/lot, so that commission alone is **0.8 pips** — against a
modelled total of 0.2 (spread 0.1 + slippage 0.05 per side). A build at these numbers produces
strategies whose edge is the missing cost.

🤔 **The ordering between pairs is not credible, which is the part that poisons a cross-market
test.** CADJPY sits at 0.1 while GBPJPY sits at 1.2 — same `point_value` 653.92, same family, 12×
apart — and CADJPY comes out six times cheaper than EURJPY (0.6) despite being the less liquid of
the two. These are factory defaults, not a cost structure. A retest across markets charged this way
partly answers *"where did SQX undercharge"* rather than *"where does the edge survive"*, which is
the failure mode `/crossmarket` refuses to write for when a market has no `assets/symbols/` file at
all — and which a file full of these defaults passes straight through.

🔬 They are still usable for one thing: **measuring how correlated a strategy's equity is across
markets**. A correlation between curves barely moves with the cost level, while profitability moves a
lot. So a run at these costs sizes the effective sample of a multi-market test (`N_eff = N / (1 +
(N−1)ρ)`) and must not be used to decide whether an edge is real. The ten files say so in every
`why:` and in their `notes:`, written the same day.

## A session cannot be borrowed from another asset

🔬 2026-09-23. `sqx.projects.doctrine.unify_sessions` copies a session definition **between the tasks
of one project** and returns `None` when no task defines it at all — the builder then refuses. The
XAUUSD donor (`projectsBackup/XAUUSD_base_2026-09-21`) carries only `XAUUSD_ftmo` and
`XAUUSD_the5ers`, so **no project cloned from it can build a non-gold asset** until its session comes
from somewhere. 📓 Which master project defines what, read from the `.cfx` files:

| session | defined in |
|---|---|
| `USDJPY_ftmo`, `USDJPY_the5ers` | master project `USDJPY` |
| `EURUSD_the5ers` | master project `EURUSD` |
| `AUDJPY_the5ers` | master project `AUDJPY` |
| `CADJPY_the5ers`, `EURJPY_the5ers`, `GBPJPY_the5ers`, `USDCHF_the5ers` | `CADJPY_H1`, `EURJPY_H1`, `GBPJPY_H1`, `USDCHF` |
| `XAUUSD_ftmo` | `XAUUSD`, `Retester`, and the frozen donor |

🔬 **Fixing the session is not enough, and that is the trap.** Borrowing `USDJPY_ftmo` into the gold
donor made `builder` succeed — and the project it produced still built `XAUUSD_DukasM1_Infinox` at
gold's spread, with USDJPY's trading hours, because `--symbol` never switches the market. The session
is the blocker that *announces itself*; the market is the one that does not. `OPEN.md` issue 35.

GBPUSD, AUDUSD and USDCAD have **no session defined in any project on this machine**, so authoring
for them needs one registered in SQX first. Inventing the hours is the one thing the code will not
do, and that is deliberate: a task naming a session it does not define trades the wrong hours in
silence.

## The triple swap day is per feed, and the policy hardcoded one for everybody

🔬 2026-09-23, found while verifying a written cross-check `<Setup>` against the master. The
`<Swap tripleSwapOn>` SQX carries is **not** the same day everywhere:

| day | feeds |
|---|---|
| `WEDNESDAY` | 17 — every FX pair, XAUUSD, XAGUSD |
| `FRIDAY` | 7 — `BRENTCMDUSD_ftmo`, `DJ30`, `NIKKEI225` (both feeds), `USA500` (both feeds), `USATEC` |
| `NEVER` | 1 — `EURUSD_M1_dukas`, a stale feed no asset file claims |

`assets/_policy.yaml` declares `swap: {triple_swap_on: WEDNESDAY}` **once, for all of them**, and has
no per-asset field. So five assets with a file — BRENT, DJ30, NIKKEI225, USA500, USATEC — were being
configured with the wrong night. It is not cosmetic: the triple charge is 3× one night's financing,
and BRENT's short side alone is −9.54 % annual, so a decade of it lands on the wrong bars.

🔬 **The override needs no code.** `core.assetdata.load` returns `{**policy, **asset_file}`, so a
top-level `swap:` in an asset file **replaces the policy's block entirely** — which is why the
override must repeat `rollout_hour` even when it does not change. Field-by-field merging is not what
happens. All five files now carry it and `load()` agrees with the master on all nineteen.

🤔 The cleaner fix is a per-asset `triple_swap_on` in `_policy.yaml` next to the segments, so the day
sits with the other read-from-SQX facts instead of in five hand-written overrides. That needs a small
change in `load()` and has not been done.


## Cuánto tarda cada paso del workflow (2026-09-24)

📓 Del log del custodio y de `/usr/bin/time`, corrida completa 1→16.5 sobre USDJPY H1. La tabla
entera está en `docs/manual/12-rendimiento.md`; aquí sólo lo que cambia una decisión:

- 🔬 **El MC Retest es el 89 % del tiempo de SQX de la cadena** (1.955 s de 2.202), y dentro de él
  `MCR 7 OHLC` (695 s) y `MCR 8 Stress` (1.022 s) son el 88 %. Medido con CINCO tareas activas; con
  las siete que ahora se configuran, más.
- 🔬 **`crossmarket.report` es el único cuello de botella de Python**: 13 min a 2.000 sorteos y >50
  min sin terminar a los 10.000 de su config, con 8 estrategias × 9 mercados en un núcleo. Todo lo
  demás de Python son segundos.
- 🔬 **`retest.ingest` pica 3,2 GB con 36 corridas de 1.000 simulaciones.** Escala con corridas ×
  sims: 800 corridas pedirían del orden de 70 GB si la proporción aguanta. Medirlo antes de lanzarlo.
- 🔬 **Parar y arrancar el custodio cuesta ~39 s**, de los cuales 21,5 son la CLI, que responde mucho
  después de que el puerto conteste. Se paga una vez por etapa porque `startOnlyTask` no corre nada
  en este install, así que cribar entre pasos implica ese ciclo.
- ⚠️ Sin medir: los pasos 17, 18 y 19, y el retest del lote de variantes que los alimenta — que es
  el candidato a más caro de toda la cadena (240 variantes × 3 tramos × 9 mercados).
