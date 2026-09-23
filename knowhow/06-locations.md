# Where things actually live

🔬 These hold real content and are easy to miss:

| path | contents |
|---|---|
| `~/Desktop/WorkSQX/` | 635 `.sqx`, plus `AlgoWizardTemplates/` (a main template source) |
| `~/Desktop/AddonsSQX/` | 68 `.sqx`, `Templates/`, `CustomBlocks/`, `RandomGroups/` |
| `~/Desktop/StratsProblem/` | 6 `.sqx` |
| `~/Desktop/user/` | ⚠ NOT debris — a 12 Jun project tree, the ONLY copy of XAUUSD/Results (4,805 `.sqx`). Do not delete |
| `~/Desktop/AlgoProject_Old/` | the previous project. Read-only archive, incl. 8.5 GB of `snapshots/` |
| `~/.local/share/Trash/` | 11,440 `.sqx` — mostly June-tree duplicates. **The owner has asked that Trash be excluded from strategy searches** |
| `~/Desktop/SQX.zip` | 1.28 GB **June install backup**, only 32 example `.sqx`. Not a strategy archive |

🔬 97 AlgoWizard templates across `WorkSQX/AlgoWizardTemplates/` and `AddonsSQX/Templates/`
(`TemplatesSergiogus`, `TemplatesClaude`, `TemplatesLaCity`, `TemplatesBook`).

## Logs

🔬 `<install>/user/log/StrategyQuant/log_YYYY_MM_DD.log` keeps **14 days**; SQX prunes the rest on
start. A single day reaches multi-GB — `log_2026_08_18.log` alone is **4.66 GB**, and the master's
whole log tree was 4.4 GB. It gzips to 102 MB, so archiving is cheap and there is no reason not to.
`AlgoData/logs/<install>/` holds them (`SQX/projects/<P>/` the projects' own logs, condensed — see
`07-practices.md`, log retention); `sqx/export/archive_logs.py` refreshes it and must run more
often than every 14 days. First full archive taken 2026-09-04, back to 2026-06-13.

🔬 Data coverage, from `-symbol action=list` on the worker: `XAUUSD_DukasM1_Infinox` runs
**2003.05.05 → 2026.01.16**. The XAUUSD build task's window stops at **2017.12.31**, leaving 8 years of
gold data unused.

## The building-block vocabulary

🔬 The **whole AlgoWizard block vocabulary** is one file:
`<install>/internal/web/SQWIZARD/branding/global/config.xml` (1.19 MB). Its single `<Blocks>`
element holds four sections, each a list of `<Category>` of `<Item key= name= display= returnType=>`:
**Comparisons 23 · Conditions 500 (63 categories) · Actions 23 · Values 303 (8 categories,
190 of them indicators)** = 849 built-ins. `display` is the block's written form with its
`#Param#` holes; `key` is what a template or a group references.

⚠ Do not confuse it with `<install>/internal/ctemplate/config.xml` (18 KB) — that one is the
*editor's* defaults, a `<UsedBlocks>` shortlist of ~14 keys, not the catalogue.

🔬 The owner's own blocks are separate: `<install>/user/settings/customBlocks.xml` (1.3 MB,
**171 `<Item>`**, flat, each with `category`, `type` and `oppositeBlockKey`). Backups sit beside it
in `customBlocks-backups/`; the same folder pattern holds for `blockGroups.xml`.
Total on the master today: **1,020 blocks**.

🔬 `tools/sqx-lab/.../sqx-custom-block/catalog.json` is a derived index of the *value* atoms only
(235 = 178 native + 57 the owner's), not of the conditions — regenerate it, don't hand-edit it.

### 🔬 A RandomCondition needs no group, and a fixed block beside it is already proven (2026-09-22)

Read out of `highest_breakout_template_daily_filter.sqx`, the template this install ships and the
one the `session_market` shape was derived from. Its entry signal is:

```xml
<Item key="AND">
  <Block><Item key="RandomCondition" ...>
           <Param key="#Group#" name="Random group" randomGroupType="Conditions" />   <!-- empty -->
  <Block><Item key="BarDayOfWeekIsNot" ...>                                           <!-- concrete -->
```

Two facts, both load-bearing for authoring templates from a plain-English idea:

🔬 **`#Group#` is empty and the template builds.** A `RandomCondition` left without a group samples
the whole Conditions vocabulary — 500 blocks — rather than a pool. Binding it to a group narrows the
search; it is an option, not a requirement. Anything claiming a hole needs a group is wrong.

🔬 **`AND(RandomCondition, <concrete block>)` is build-confirmed** on this install. The shape the
owner asks for — one fixed condition that states the idea, plus one random condition — needs no new
skeleton. Only which concrete block sits in the fixed slot varies.

Consequence for the pooling note below: **a group matters only for a hole.** A block that no group
pools is unreachable from a `RandomCondition`, and perfectly usable as the fixed half.

### 🔬 A block no group pools is unreachable from a template's HOLE (2026-09-22)

A template's **hole** references a random group, never a block — the fixed half of a signal is the opposite case, see above. So the install knowing a block is
necessary and not sufficient: if no group contains it, no template can point a hole at it. Measured
with `sqx/inspect/vocabulary.py` on the conductor, which reports exactly this.

The Keltner channel is the worked case. SQX ships a whole native category, `Conditions/Keltner
Channel`, with **16 ready-made conditions** — `KCBarClosesAboveUpper` is literally "the bar closes
above the upper band". **None of the 16 is in any group.** The indicator is reachable only as a
*value*, through `BollingerBands_Lower`, a Value group whose name misleads: it pools eleven band
indicators, `KeltnerChannel` and `MTKeltnerChannel` among them. So a Keltner **price level** is
available today and a Keltner **entry condition** is not, until a group is authored for it.

⚠️ **An empty group is a silent failure.** `RandConditions` on this install has zero items, and the
`catalog.json` of `sqx-strategy-template` lists it among the clean condition groups. A template
pointing a hole at it does not fail: it builds, and samples nothing. `vocabulary.py` prints those
groups on their own `EMPTY, unusable` line for that reason.

🔬 **The three installs carry the same vocabulary today** — 849 native + 171 own blocks, 20 groups,
identical on master, `SQX_w1` and `SQX_w2` (`--diff` reports no gap either way). That stops being
true the moment anything is authored on only one of them, which is why a template authored on the
conductor and built on the custodian has to be diffed first.

## Tools built here

| tool | does |
|---|---|
| `sqx/inspect/index_sqx.py` | index every `.sqx` by inner-XML hash + symbol; 17.7k files in 1.5 s |
| `sqx/inspect/dump_project.py` | `project.cfx` → Markdown pipeline map (TL;DR, databank flow, per-task detail) |
| `sqx/inspect/keep_tasks.py` | emit a variant of a `.cfx` keeping only chosen task types |
| `sqx/inspect/project_health.py` | every project's broken task references, version drift and mangled fields |
| `sqx/inspect/template_check.py` | whether built strategies carry the blocks their template fixes |
| `sqx/repair/graft_tasks.py` | heal a project archive missing task files, with SQX closed |
| `sqx/inspect/vocabulary.py` | what an install can express: blocks, groups, what pools what, and the gap against another install |
| `sqx/export/archive_logs.py` | copy both installs' logs to `AlgoData/logs/` before SQX prunes them |
| `sqx/export/export_metrics.py` | databank metrics with paired IS/OOS columns, via the worker |
| `sqx/export/export_trades.py` | a databank's trades plus the bars they were traded on |

## The XAUUSD generated corpus — what it actually is

🔬 Contradicts a common assumption: **these strategies have no stop loss, no take profit and no
trailing stop.** All 231 carry `SQ.Formulas.SLPT.None`. The build task explains it —
`<SLRequired>false</SLRequired>`, `<SLATR>false</SLATR>`, `<PTRequired>false</PTRequired>`. The ATR
machinery is configured (`MinSLATRMultiple 2`, `MaxSLATRMultiple 8`, period 20 fixed) but the toggle is
**off**, so none of it reaches a generated strategy.

- 🔬 Long-only, from `<MarketSides type="long">`. 231/231 have a long entry order, zero short.
- 🔬 `ExitAfterBars` is **uniformly 8** across all 231, though the generator range is 5–20.
- 🔬 Two structurally different populations share the pool: ~129 **bar-cap** strategies (100% of exits
  at the 8-bar cap, median MAE 1.37×ATR) and ~11 **signal-exit** strategies (exit on a rule after 1–3
  bars, median MAE 0.95×ATR, some near 0.01). Any pooled exit statistic hides this.
- 🔬 In-sample window is `2008.01.01–2017.12.31` (`<Setup dateFrom= dateTo=>` in `Build-Task3.xml`).
