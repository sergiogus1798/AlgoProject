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
  - `sqx_now` — what the master carries today, **with its own unit**, which is often not the unit of
    `use`. A gold swap is `{type: points, value: -73.42}` while `use` will be a percentage.
  - `why` — one line on why it differs. The part that stops the same discussion recurring.

  `spread` and `commission` block while undecided. `slippage` and the swaps do not, and both now
  carry a PROVISIONAL figure: **slippage is half the spread**, the owner's convention of
  2026-09-22. It is not a measurement and cannot be one — SQX carries `defaultSlippage = 0.0` on
  all seventeen, and a backtest applies whatever slippage it is given, so none is recoverable from
  an export. A flat figure in points is wrong across classes: 2.5 points is $0.02 on the Nikkei and
  $28.82 on USDCHF. Half the spread scales with the instrument and lands on 5 points for gold, the
  midpoint of the range its own MC Retest already explores.
- `mc_retest` — the spread and slippage ranges the MC Retest task draws from, in points.

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

| segment | what it is for | spread |
|---|---|---|
| `build` | generation. The only sample the builder ever sees | `is` |
| `oos1` | everything from the retest through the SPPs | `oos` |
| `oos2` | **reserved** for Walk Forward Correlation and Matrix, the last tests | `oos` |

`reserved_for` marks a segment whose data is spent by looking at it. The preflight prints it with a
warning, because pointing an ordinary task at a holdout is a one-way door.

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

Since 2026-09-24 the desktop app's **Activos** zone reads and writes everything described here:
the costs with their units, the windows, the MC Retest ranges, the retest universe and the two
shared schemas. It keeps every comment in place — `core.assetyaml` round-trips the file and only
the changed line moves — and regenerates `INDEX.md` after each write. `docs/manual/38-app-activos.md`
is its page. The rule above does not change: **the window is not the preflight**. What stops work
is `python3 -m core.assets <SYMBOL>` and its exit code.

The one writer is `core.assetwrite`. Nothing else in the project writes these files, and a second
writer is how a comment gets lost.

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
`SP500ft` se queda en `null` porque SQX no tiene su feed.

⚠️ **Una sesión se define DENTRO del proyecto**, en `<Resources><Sessions>`. Una tarea que nombra
una sesión que su proyecto no lleva carga sin quejarse y opera otro horario.
`sqx/projects/doctrine.py` copia la definición a las tareas que la nombran sin llevarla, y se
**niega** cuando ninguna tarea del proyecto la define: un horario de mercado no se inventa.

El registro completo está en `user/data/data.db`, que es **SQLite** pese al nombre — tablas
`SESSIONS` y `ELEMENTS`, y `BROKER` para los perfiles (FTMO es el 8, The5ers el 9).
