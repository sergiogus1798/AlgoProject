# assets — the blocking preflight

SQX's own spread, commission and swap for an instrument are frequently **not** what the broker
charges. Those differences decide whether a backtest is honest, so they are recorded here and
consulted before anything is authored.

## The rule

**Before creating or modifying any project, task or template for a symbol, run:**

```bash
python3 -m core.assets <SYMBOL>
```

Read its output back to the owner, saying which values you are applying and where they differ from
SQX. It exits **2** when a required cost still carries `use: null` — the owner has not decided yet.
**Stop and ask. Do not pick a value.** It exits **3** when the file does not match its class.

## Four files, and only one of them is per asset

```
assets/
  _policy.yaml       the research policy: what each segment IS (once), where it starts and ends
                     (per asset, with the data range SQX holds), the swap conventions.
  _classes.yaml      the two cost schemas: which fields exist, in what unit, on which SQX setting.
  _markets.yaml      the retest universe: per main asset, family and structural markets.
  _build.yaml        the build doctrine: rule complexity, order types, exits, sizing, hours,
                     precision and cross-checks. What SHAPE a strategy may have, as opposed to
                     what it costs to trade one.
  symbols/
    <SYMBOL>.yaml    what is genuinely this instrument's own, and nothing else.
```

A retired asset lives in `symbols/_retired/`, which `symbols()` does not glob: out of the library,
not lost, and its `_policy.yaml` block stays so a restore brings its windows back.

The four shared files sit at the top; the per-instrument ones live in `symbols/`, so the
directory shows four entries instead of twenty. `core.assets.symbols()` globs `symbols/` and nothing
else. What a session reads is `load(<SYMBOL>)`, which folds the policy in and hands back one dict —
the lookup unit is still the asset, exactly as before.

## The two classes

The class decides **which fields a file has**, so the schema is checked rather than remembered.
`validate()` reports a forex file with two spreads, or a no_forex file missing one, as an error.

| | `forex` | `no_forex` |
|---|---|---|
| spread | `spread`, one value | `spread_is` **and** `spread_oos` |
| commission | `commission`, $ per lot, `SizeBased` | `commission`, **% of notional**, `PercentageBased` |
| slippage | `slippage`, points, `defaultSlippage` | the same |
| swap | `swap_long`/`swap_short`, **points per night** | `swap_long`/`swap_short`, **% ANNUAL** |

**Why two spreads off forex.** These instruments' prices multiply across the history — gold runs
from 800 to 3500 — so a spread fixed in points costs three times as much in % of notional in 2010 as
it does today, which puts a slope through the build window. One spread for `build` and another for
both out-of-sample segments removes it. It is expressible because **SQX stores costs per symbol
inside each task**, not once per project: the build task carries one `defaultSpread` and the retest
tasks another. `sqx_settings(data, segment)` picks the right one.

**A third spread, when oos1 and oos2 differ.** An asset's own block in `_policy.yaml` may give a
segment its own half — `oos2: {from: 2024, to: 2026-08-31, spread: oos2}` — and its file then
carries `spread_oos2` and `slippage_oos2` (required once named, `fields()` asks for them). The five
index CFDs do since 2026-09-27: their spread fell or rose between the two OOS windows by up to 40 %
(`studies/data/spread`, `docs/AgentPDFs/spread-real-2026-09-27`).

**Why % off forex.** A percentage scales with the price on its own, which is the whole point.
⚠️ Two traps, both in `_classes.yaml` and both verified against the install on 2026-09-22:

- The **swap percentage is ANNUAL**, not per night. SQX divides by 100 and by 360 before applying
  it. Writing one night's percentage there is wrong by 360×.
- `PercentageBased` charges in `computeCommissionsOnOpen` only; `computeCommissionsOnClose` returns
  0. Whether the engine applies it to each leg is **unverified**, and it is a factor of 2.

## What a per-asset file holds

- `class`, `broker`, `sqx_symbol`, `feeds` — what the instrument is.
- `instrument` — `tick_size`, `point_value`, `min_distance`. Facts read from SQX, never decisions.
  Regenerate with `python3 -m sqx.inspect.instruments`.
- `costs` — one block per field of its class, each with:
  - `use` — what to actually apply. `null` blocks authoring.
  - `sqx_now` — the value recorded in the file, **with its own unit**, which is often not the unit
    of `use`. The asset zone does not show it: its «SQX hoy» column reads the custodian's instrument
    registry (`SQX_w2/user/data/data.db`, `sqx.inspect.instruments.registry`) on disk, never the
    master (owner, 2026-09-30). A gold swap is `{type: points, value: -73.42}` while `use` will be a percentage.
  - `why` — one line on why it differs. The part that stops the same discussion recurring.

  `spread` and `commission` block while undecided. `slippage` and the swaps do not, and both now
  carry a PROVISIONAL figure: **slippage is half the spread**, the owner's convention of
  2026-09-22. It is not a measurement and cannot be one — SQX carries `defaultSlippage = 0.0` on
  all seventeen, and a backtest applies whatever slippage it is given, so none is recoverable from
  an export. A flat figure in points is wrong across classes: 2.5 points is $0.02 on the Nikkei and
  $28.82 on USDCHF. Half the spread scales with the instrument and lands on 5 points for gold, the
  midpoint of the range its own MC Retest already explores.
- `mc_retest` — the spread and slippage ranges the MC Retest task draws from, in points.
- `mt5` — the asset's symbol name at each firm. `mt5_point` — each firm's MT5 `point` and
  `to_sqx` = point ÷ `instrument.tick_size`, read off the firm's server (2026-10-01). **Every cost
  in this file is in SQX points**; a figure read in MT5 (spread, swap in points, a stop) enters
  SQX × `to_sqx`, never a remembered ÷10: FX and JPY pairs 0.1, gold/silver/indices 1, Brent at
  Hantec **10**. → `knowhow/costs/mt5-points-to-sqx-points.md`

Its time windows are **not** here: they live in `_policy.yaml` under `segments: <SYMBOL>:`, all
seventeen together, next to the date range SQX actually holds for that feed.

## MC Retest ranges

The `MC Retest` task re-runs the whole backtest against a perturbed input, and two of its methods
draw a value from a range: `RandomizeSpread` and `RandomizeSlippage`. Each asset declares its own,
under `mc_retest`, **in points** — absolute, not a multiple of the real spread.

```yaml
mc_retest:
  spread:   {min: 5, max: 12, sqx_now: …}
  slippage: {min: 0, max: 10, sqx_now: …}
```

An undecided range **does not block**: the preflight prints a warning and exits 0, because an
undecided range only makes that one MC Retest task uninterpretable. `mc_retest(data)` hands back
both ranges; `mc_pending(data)` names the ones still open.

⚠️ SQX's factory range is `spread 1.0-5.0` and `slippage 0.0-5.0`, **the same on every instrument**,
and it is what most feeds on the master still carry. It is meaningless at any scale but forex's: on
NIKKEI225, whose real spread is 1100 points, it perturbs between 1 and 5.

## Segments — the template is shared, the dates are per asset

`_policy.yaml` holds both halves, and the split is the point:

- `segments_default` — **what each segment is**: its role and which spread it uses. One copy,
  for every asset.
- `segments` — **where each one starts and ends, per asset**, with `data` beside it. All 17 blocks
  sit together so the windows can be compared and adjusted in one place.

```yaml
segments:
  XAUUSD:
    data: {from: 2003-05-05, to: 2026-01-16}   # read from SQX, never edited by hand
    build: {from: 2008, to: 2017}
    oos1:  {from: 2018, to: 2022}
    oos2:  {from: 2023, to: 2026}
```

A bound is **a year or an explicit date**. A year means that whole year, both ends inclusive —
`from: 2008, to: 2017` is 1 January 2008 to the last instant of 31 December 2017. A date means that
day, also inclusive, which is how a segment ends mid-year: `to: 2026-08-30` runs to the last instant
of 30 August. `window(data, "build")` turns either into the `(dateFrom, dateTo)` epoch milliseconds
a SQX task carries, and **raises rather than inventing** when the dates are null.

**oos2's end is not hand-edited any more** (owner, 2026-09-30): on the first Saturday of each month,
after the data update, `bin/monthly-oos2-roll.sh` (`python3 -m sqx.data.roll_oos2 --apply`) moves
every decided `oos2.to` to the last day of the previous month — only where `data.to` already reaches
that month's last weekday, never backwards, never a `null`.

| segment | what it is for | spread |
|---|---|---|
| `build` | generation. The only sample the builder ever sees | `is` |
| `oos1` | everything from the retest through the SPPs | `oos` |
| `oos2` | the last out-of-sample: WFC, CSCV, market surfaces, WFM, ATR stop | `oos` |

`reserved_for` binds only an autonomous agent (`ALGO_AUTONOMOUS=1`, `core.assetdata.enforced`):
owner, 2026-09-28, a human may look at any segment whenever. Under that flag the preflight prints
it with a warning and `ledger.gate` refuses other steps.

**Why per asset.** Histories do not start together: gold has M1 from 2003-05-05 and is built from
2008, while the DAX40 has nothing before 2013-09-30 and a 2008 window would silently run short.
`data` is refreshed with **`python3 -m core.assets --dataranges`**, which asks the conductor and
rewrites all seventeen lines — run it after every "Update all" on the master. It sits next to the
windows precisely so the mismatch is visible. Two checks, and only one of them stops the work:

- `before_data()` — a segment starting before its feed does. **Fatal**, the preflight exits 3: that
  window can never be filled.
- `past_data()` — a segment ending after the last bar SQX holds. **A warning only**: the window is
  right and the data is simply not synced yet, which is the normal state of the newest segment.

⚠️ The master's XAUUSD project does not follow the inclusive convention: its Build task carries
`dateTo` = 2017-12-31 00:00, the *start* of the last day. Strategies already in its databanks come
from that window, one day shorter than the one this file describes.

## The retest universe

`_markets.yaml` declares, per **main** asset, the additional markets its edge must survive on, in two
categories that answer different questions:

- `family` — same economic driver. The easy test: passing it proves little, failing it says a lot.
- `structural` — similar structure (volatility, session, noise) with **no** shared driver. The hard
  test: transferring here means the logic caught something about price movement, not a macro factor.

**The list is fixed before any result is looked at.** Choosing markets after seeing where the
strategies work turns the test into a selection and its p-values into decoration. The file
classifies; what a strategy was really retested on is read from the export itself.

## Special cases

`special/` holds cases that cross assets: session filters, news windows, broker quirks. Every file
there is surfaced by the preflight, so a case written once is seen by every future session.

## Editing all of this from the window

Since 2026-09-24 the desktop app's **Activos** zone reads and writes each asset's own part: the
costs with their units, the segment dates (a date selector per segment), the MC Retest ranges and
the «Check de Cross Market» (the retest universe of `_markets.yaml`, row by row). The shared
schemas — `_build.yaml`, `_classes.yaml` and the globals of `_policy.yaml` — moved to the
**Configuración SQX** zone on 2026-09-27 (plan 24, F9). It keeps every comment in place — `core.assetyaml` round-trips the file and only
the changed line moves — and regenerates `INDEX.md` after each write. `docs/manual/02-la-ventana.pdf` (cap. 38-app-activos)
is its page. The rule above does not change: **the window is not the preflight**. What stops work
is `python3 -m core.assets <SYMBOL>` and its exit code.

The one writer is `core.assetwrite`. Nothing else in the project writes these files, and a second
writer is how a comment gets lost.

## The funded worst case — swap, metal commission and the instrument's contract (owner, 2026-10-01)

Funding comes first, so the development costs follow the two funded accounts, **FTMO and Hantec**,
read from the MT5 terminal (`mt5.live`), and this section overrides what the two below say where
they differ:

- **Swap, every asset:** each side is the worse of the two firms **today** —
  `studies.data.spread.fundedswap.worst(symbol)`, the onboard's `swap: funded_worst`. Forex in SQX
  points (the firm's USD per lot per night ÷ the SQX instrument's pointValue × tickStep);
  everything else in % annual on each firm's own notional. It is a figure of the day — brokers moved
  several of them between the morning and the evening of 2026-10-01 — so rerun it before a build.
  The −7 %, −8 % and registry-mean defaults are retired. **Crude only (UKOIL, USOIL): the side that
  is credited today is written 0**, never the positive figure — backwardation paid the long ~+20 %
  annual, and applied back to 2013 that carry was a gift to every long. The charged side is kept.
- **Spread on crude:** no Darwinex ticks exist, so all three segments carry FTMO's spread of today
  × 1.25 (UKOIL 90, USOIL 97.88 points; slippage half). It tripled from 2025-01 with no price move
  behind it, so it is not modelled back; 2013–2024 is unmeasured.
- **Commission on metals and crude:** the worse of FTMO and Hantec per segment, no longer Darwinex's
  0.005 %. Gold: Hantec's 5 USD/lot round trip beats FTMO's 0.0014 % at every segment's median
  price. Silver: 5 USD/lot too, **assuming** Hantec charges silver as it does gold — unconfirmed
  (no XAGUSD.h deal yet); FTMO's confirmed 0.0014 % is cheaper below ~71 USD. Crude: 1 USD/lot. Forex (5 USD/lot) and
  indices (0) were already both firms' figure. Verified against the accounts' own deals:
  `knowhow/costs/funded-accounts-real-costs.md`.
- **The instrument is FTMO's and Hantec's MT5 contract**, not Infinox's or the5ers': `instrument.
  point_value` of USA500 is 1 (was 10), of NIKKEI225 0.0631 (was 0.649); JPY, CAD and CHF pairs carry
  that day's conversion. SQX holds them as `<ASSET>` (forex, metals) or `<ASSET>_ftmo` (indices).
- **Every feed is on FTMO's clock, EETUS** — `knowhow/sqx-drive/renaming-feeds.md`.

## The per-broker commission table, and the development default it decides

Owner, 2026-09-29: every asset's `costs.commission` carries a `brokers:` table, one entry per
firm this project trades or funds with — Darwinex (the spread reference), Infinox, FTMO, Hantec
Trader, the5ers, and whichever of `AlgoData/funding/firms.yaml` is active or a candidate
(FundedNext, FundingPips). `commission.use` is **not** any one broker's own figure: it is the
**development default** SQX builds and retests against, computed as the **most restrictive**
(most expensive) confirmed broker, so a strategy authored at it is never cheaper in SQX than the
worst account it might actually run on. The per-broker figures still matter on their own for the
step-26 final test on each firm's feed and for `weeklyReconciler`'s SQX-vs-live check.

```yaml
costs:
  commission:
    use:                    # one {method, value} PER SEGMENT — never one flat figure
      build: {method: SizeBased, value: 8.0}
      oos1:  {method: PercentageBased, value: 0.005}
      oos2:  {method: PercentageBased, value: 0.005}
    sqx_now: {...}
    why: "…"
    brokers:
      darwinex: {method: PercentageBased, value: 0.005, unit: pct_of_notional,
                 source: https://help.darwinex.com/execution-costs, date: 2026-09-29, confirmed: true}
      infinox:  {method: SizeBased, value: 8.0, unit: usd_per_lot,
                 source: "dueño, 2026-09-29", date: 2026-09-29, confirmed: true}
```

**A figure is `confirmed: true` only off the firm's own page, or the owner's own statement**
(never an aggregator, a review site or a forum), with its `source` (a URL, or `"dueño, <date>"`)
and the `date` it was read or decided. Read it once, in the same task as everything else that
touches `assets/` — never guessed, never left half-typed.

**Correction, same day (owner, 2026-09-29): no per-segment "max broker" pick.** The reading above
— the broker that charges most changes segment to segment, so pick it separately in each — is
wrong. For a `no_forex` asset with commission confirmed (XAUUSD, XAGUSD, BRENT), the WHOLE SQX
workflow — build and every retest, OOS through WFM and the variants — prices at **Darwinex's own
`PercentageBased 0.005 %`**, the same in `build`, `oos1` and `oos2`. `core.assetwrite.set_cost`
already spreads one bare figure over the three segments in the class's own method, so this is
written the ordinary way, with a `why` naming the decision. Forex stays 5 USD/lot `SizeBased`
everywhere, indices stay 0 % — neither changes. `sqx.projects.setups.sqx_settings` still reads
`use[segment]` directly; it is simply the same `{method, value}` in all three now.

**The per-broker figures still matter, on their own, for step 26 and `weeklyReconciler`** — never
for an SQX workflow task. Each broker in `costs.commission.brokers` keeps its native figure AND
gets it converted to a percentage adjusted to itself: `core.commission.commission_pct(method,
value, price, point_value)` turns a `$/lot` broker's flat figure into a % of notional at a given
price (a `%` broker's own figure is returned unchanged), and `python3 -m core.commission --refresh`
(weekly, after `bin/weekly-data-update.sh`'s data update) recomputes it for every confirmed broker
of every asset from **the newest bar `core.barstore` holds for that asset's own feed** — its
`Close`, not a segment median, because this is "what would I pay today", not a historical segment
cost — and writes `pct_now`, `price_now` and `price_date` onto each broker entry through
`core.assetwrite.set_brokers`. A `SizeBased` broker on a feed with no bars synced yet (the five
indices) is left unpriced rather than guessed; a `PercentageBased` broker needs no price at all.
`core.commission.broker_pct(asset, broker)` is the one accessor step 26 (encargo 34, the MT5
validation on each firm's feed) and `weeklyReconciler` (OPEN.md #78) read `pct_now` through — SQX
workflow tasks never call it, they read `costs.commission.use` instead. → `knowhow/costs/commission-per-broker.md`.

## Adding an asset

From the window: **Nuevo activo**, which asks for the identity, the class and the three
`instrument` facts, writes every cost as `use: null` and adds the asset's block to `_policy.yaml` —
without that block `load()` hands back windows with no dates at all. By hand: copy the closest file
in `symbols/` **of the same class**, fill `instrument` and `sqx_now` from `sqx.inspect.instruments`,
leave every `use: null`, add the `_policy.yaml` block, and ask the owner for the real numbers. Then
`python3 -m core.assets <SYMBOL>` — it will exit 3 if the schema is wrong and 2 until the owner
decides. A file with invented values is worse than no file: it looks decided.

## La sesión del activo

`session:` en cada fichero de símbolo nombra la sesión de negociación que SQX aplica a la tarea.
Decisión del dueño, 2026-09-23: **se usan las de FTMO**. Las de The5ers tienen las mismas horas
pero cada tramo cierra al día SIGUIENTE, solapándose con el de mañana; las de FTMO cierran el
mismo día.

FTMO nombra los índices distinto que el feed, así que el mapeo no es mecánico y está escrito
activo por activo: `DAX40 → GER40.cash_ftmo`, `DJ30 → US30.cash_ftmo`,
`NIKKEI225 → JP225.cash_ftmo`, `USA500 → US500.cash_ftmo`, `USATEC → US100.cash_ftmo`.
`SP500ft` se retiró el 2026-09-27 (`symbols/_retired/`): era el mismo índice que `USA500` y SQX
no tiene su feed (dueño).

⚠️ **Una sesión se define DENTRO del proyecto**, en `<Resources><Sessions>`. Una tarea que nombra
una sesión que su proyecto no lleva carga sin quejarse y opera otro horario.
`sqx/projects/doctrine.py` copia la definición a las tareas que la nombran sin llevarla, y se
**niega** cuando ninguna tarea del proyecto la define: un horario de mercado no se inventa.

El registro completo está en `user/data/data.db`, que es **SQLite** pese al nombre — tablas
`SESSIONS` y `ELEMENTS`, y `BROKER` para los perfiles (FTMO es el 8, The5ers el 9).
