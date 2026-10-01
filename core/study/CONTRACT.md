# The study contract — what a result dict holds

Encargo 19 (owner, 2026-09-25), kept here once it was built and the encargo deleted. The
browser panels were retired so the desktop window could draw every study with native widgets;
for that a study hands back **data**, never HTML. `blocks.validate` enforces this file.

## 1. The result of one strategy (or of a population)

```python
{"module": "monteCarlo", "strategy": str, "identity": str,      # SHA-256 of the normalised XML; a name identifies nothing
 "config_hash": str, "computed_at": "ISO", "wall_s": float,
 "verdict": {verdict block} | None,                              # None when the study describes and does not judge
 "tabs": [                                                       # in reading order
   {"name": str, "title": str, "note": str,                      # note: the paragraph the tab opens with (optional)
    "selectors": [{"key": str, "label": str, "options": [str, ...], "default": str}, ...],
    "blocks": [ ...blocks of §2... ]}],
 "warnings": [{"code": str, "state": str, "text": str,
              "highlight": bool | None,                         # optional (2026-09-30): drawn bigger, at the very top of the page
              "help": str | None}, ...],                        # optional (2026-10-01): a «?» on the line, this sentence its tooltip
 "glossary": [{"term": str, "text": str}, ...],
 "summary": {...}}                                               # optional: the flat row this strategy adds to its population
```

**Warnings sit at the top of the page** (2026-09-30, feedback §1): the highlighted ones first
(`highlight: true` — a KS test that rejects, say), then the rest folded behind a count, all of it
before the tabs. A study marks `highlight` only for what the reader must not miss; everything else
still shows, just smaller and lower.

**A block's `title`, a table's column headers and a selector's label all take an optional `help`**
(str): the window puts a uniform "?" tooltip wherever one is given — `card.py` for a block title,
`table.py` for a column header, `tabpage.py` for a selector. No `help` means no "?": a study adds
one only where the concept is not obvious, not on every label.

**Selectors.** A tab with `selectors` carries **every** block already computed, one per
combination, tagged `"select": {"market": "EURUSD", "model": "block_shift"}`. The window filters
and redraws without calling the study again. Static pages and the markdown draw only the default
combination (`render/page.shown`).

**A partial run** — one Monte Carlo sub-test again, one crossmarket market alone — is
`one.run(..., only=...)`, returning a partial dict with no verdict. Merging it beside the stored
result is the daemon's job, not the study's.

## 2. The eight block kinds

`"kind"` comes first. The window has one widget per kind: **a ninth kind is a new widget, so a
study asks before inventing one.**

```python
# distribution — histogram with the real value marked: every MC test, every null model
{"kind": "distribution", "title": str, "unit": str,             # "USD", "%", "R", ""
 "bins": [float, ...], "counts": [int, ...],                     # aggregated, NEVER the draws
 "real": float | None, "median": float, "band": [float|None, float|None],
 "percentiles": {"1": float, "5": float, ..., "99": float},
 "p": float | None, "note": str, "mark": str,                    # mark (optional): what the line at `real` is, when not a real run
 "series": [{"label": str, "counts": [float, ...],               # optional (encargo 24 E3): overlaid samples on the SAME bins,
             "n": int, "median": float,                          #   counts as a DENSITY — sum(counts × bin width) = 1 per series
             "real": float | None}, ...],                        #   optional (2026-09-30): THIS series' own real backtest, not the block's
 "shift": {"median": float, "ks_p": float} | None}               # optional: median(last) − median(first) and the two-sample KS p

# cone — equity cone with the real curve on top
{"kind": "cone", "title": str, "unit": str,
 "x": ["YYYY-MM-DD" | int, ...],
 "bands": {"2.5": [...], "25": [...], "50": [...], "75": [...], "97.5": [...]},
 "real": [float, ...], "split": "YYYY-MM-DD" | None}             # where the OOS starts, if any

# grid — heat map: window sweep, SPP, WFM, parameter cloud
{"kind": "grid", "title": str, "rows": [str, ...], "cols": [str, ...],
 "values": [[float | None, ...], ...],
 "scale": "discrete" | "diverging" | "sequential",
 "levels": [float, ...] | None,                                  # cuts of a discrete scale; the owner wants discrete scales
 "labels": [[str, ...], ...] | None,
 "mark": {"row": str, "col": str, "label": str} | None,          # optional (E3): one cell marked, e.g. θ₀; row ∈ rows, col ∈ cols
 "scale_range": [lo, hi] | None,                                 # optional (E3): colour extent shared by several grids, lo < hi
 "region": [{"row": str, "col": str}, ...] | None}               # optional (2026-09-30, §8.5): a faint outline
                                                                  #   on every listed cell, e.g. a plateau box carried
                                                                  #   over from another surface — never hides `values`,
                                                                  #   unlike `labels`, which replaces the printed number

# scatter — WFC in against out, any x/y per combination
{"kind": "scatter", "title": str, "x_label": str, "y_label": str,
 "points": [{"x": float, "y": float, "label": str, "group": str}, ...],
 "quadrants": bool, "fit": {"slope": float, "intercept": float, "r": float} | None}

# bars — attribution, funnel, power per block, contribution per market
{"kind": "bars", "title": str, "unit": str,
 "items": [{"label": str, "value": float, "error": [float, float] | None, "state": str}, ...],
 "reference": float | None}

# lines — several series in time
{"kind": "lines", "title": str, "unit": str, "x": [...],
 "series": [{"label": str, "values": [float | None, ...], "role": "real" | "sim" | "reference"}, ...],
 "auto_dash_negative": bool | None,       # optional (2026-09-30): a series ending < 0 draws dashed
 "zero_shade": bool | None}               # optional: background green above 0, red below (needs unit in USD-like terms)

# table
{"kind": "table", "title": str, "columns": [str, ...], "rows": [[...], ...],
 "align": ["left" | "right", ...], "note": str,
 "help": [str | None, ...] | None,        # optional (2026-09-30): one "?" tooltip per column, parallel
                                          # to columns. A list, not a string — `card.py`'s title
                                          # tooltip only fires on a plain str, precisely so the two
                                          # never collide (fixed 2026-09-30, block E1).
 "states": [[str | None, ...], ...] | None,   # optional: explicit per-cell state, overrides the Pass/Fail word guess
 "tips": [[str | None, ...], ...] | None,     # optional (2026-10-01): the cell's own hover text, parallel to rows;
                                              # None keeps the default «column: value» (WFM's conditions per cell)
 "threshold": {"column": str | [str, ...], "default": float} | None}  # optional: editable threshold, recolours the column(s) live

# verdict — the label NEVER alone: its meaning goes with it
{"kind": "verdict", "label": str, "state": str, "score": float | None, "meaning": str,
 "parts": [{"label": str, "state": str, "value": float | None, "note": str}, ...]}

# callout — one sentence the study wants seen, not read past (added 2026-09-30, feedback §1.7)
{"kind": "callout", "text": str, "state": str | None}   # state picks the border colour, "info" if absent

# list — title in bold + a short description under it, one item after another (2026-09-30, §1.10)
{"kind": "list", "title": str, "note": str | None,
 "items": [{"title": str, "text": str}, ...]}
```

Rules of the blocks:

- **Aggregated, never raw.** `blocks.distribution` and `blocks.cone` take the draws and keep the
  histogram and the percentiles: a result weighs kilobytes, not gigabytes.
- **Every block has its `title` and `note` in Spanish**: the window invents no text.
- **`state` is one of five words**: `pass`, `fail`, `watch`, `info`, `none` — the window's colour
  scale (`ui/desktop/theme.py`). A study's own words (MANTENER, FAIL, worth_it) live in
  `verdict.csv`, which is for `/curate`, never in a block.
- **No colour in the data.** The data says `state`; the window picks the colour.
- Numbers are rounded to six significant digits on the way out (`result.DIGITS`).
- **Two samples, one histogram** (encargo 24 E3, for 22 §6.1). A `distribution` with `series`
  still carries every required key: `counts`, `median`, `band` and `percentiles` describe the
  union of the series, `real` is None when nothing real is marked, `p` repeats `shift.ks_p`.
  A reader that knows no `series` draws the union and is not wrong; one that knows draws each
  series as a density, because IS and OOS have different lengths. Only time-free metrics go
  there — never Net Profit, drawdown or Ret/DD, which grow with the window. When each sample
  carries its own real backtest instead of one shared real (SPP's IS against OOS, 2026-09-30),
  the study passes `reals={label: value}` to `blocks.distribution`; each `series[i]["real"]`
  is drawn as a solid line in that series' own colour, `block["real"]` stays None.
- **Optional keys are absent or null**, never a different shape: an old block validates
  unchanged, and `blocks.validate` checks the new ones (area 1 within 1e-3, the mark on a
  real cell, `lo < hi`).
- **A value's `unit` reaches `chart.num`/`numbers.num` as its second argument, never
  concatenated after** (2026-09-30): `"%"` is always one decimal, even on a whole number
  (`7.7`, never `8`) — string concatenation after the call skips that rule.
- **Pass/Fail colours itself, automatically, in a `table` block.** A cell whose text is
  `pass`/`fail`/`aprobado`/`suspenso` (any case) is coloured green/red and bold with no
  contract change; a study that needs a different word to colour writes the optional
  `states` grid instead (`ui/desktop/blocks/table.py`, `PASS_WORDS`/`FAIL_WORDS`).
- **Market names shorten on screen, not in the data.** A study still writes the full SQX
  symbol (`USDJPY_M1`); a `table` column named `market`, `mercado`, `symbol`,
  `activo` or `asset` is shown by `core.symbols.alias` and sorts/tooltips by the full string.
  Call `core.symbols.alias` directly wherever else a symbol reaches the reader (a study's own
  labels, `bars`/`grid` items) — the renderer does not guess at those today.

## 3. What a study module owes the window

- `one.run(strategy, inputs, cfg) -> dict` and, when it judges a population,
  `many.run(inputs, cfg) -> dict`, both JSON-safe.
- `cfg` comes in as an argument and its hash goes out as `config_hash`; the window marks stale a
  result whose hash does not match its drawer.
- `--set section.key=value` on the command, cast by `core.study.config.apply`.
- `PROGRESS <0..100> <state>` lines on stdout.
- `reports/<P>/<D>/<day>/<study>/verdict.csv` with `strategy`, `identity`, `verdict`, and a
  `manifest.json` naming the absolute input judged and the overrides. The window pairs report and
  input by that manifest, never by the folder's date.

## 4. What the window already reads — renaming any of it is a same-commit change in `ui/`

| what | read by |
|---|---|
| `studies.screening.gate.inputs.config`, `studies/screening/gate/config.yaml` | `ui/daemon/gateview.py` |
| `core.assetdata`, `core.datapaths`, `core.paths` | the whole daemon |
| `sqx.templates.holes`, `sqx.templates.registry`, `sqx.blocks.palette`, `sqx.blocks.taxonomy` | the template and palette zones |
| `reports/<P>/<D>/<day>/<study>/*.csv` and `estrategias/*.json`, paired by identity | `ui/daemon/results/`, `ui/daemon/databank/` |
| `harvest/<P>/<D>/<day>/{metrics,equity,trades}.parquet`, `missing_oos.csv`, `manifest.json` | `ui/daemon/gateview.py` |
| `reports/.../gate/{scorecard.parquet,funnel.csv,manifest.json}` | `ui/daemon/gateview.py` |
| every study's `python3 -m ….report` and its flags | `ui/daemon/runs.py` |

Check with `bin/algoui`: a broken import in the daemon is the whole window failing to open.
