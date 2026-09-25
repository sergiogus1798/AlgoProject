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
 "warnings": [{"code": str, "state": str, "text": str}, ...],   # they colour, they never remove
 "glossary": [{"term": str, "text": str}, ...],
 "summary": {...}}                                               # optional: the flat row this strategy adds to its population
```

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
 "real": float, "median": float, "band": [float|None, float|None],
 "percentiles": {"1": float, "5": float, ..., "99": float},
 "p": float | None, "note": str, "mark": str}                    # mark (optional): what the line at `real` is, when not a real run

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
 "labels": [[str, ...], ...] | None}

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
 "series": [{"label": str, "values": [float | None, ...], "role": "real" | "sim" | "reference"}, ...]}

# table
{"kind": "table", "title": str, "columns": [str, ...], "rows": [[...], ...],
 "align": ["left" | "right", ...], "note": str}

# verdict — the label NEVER alone: its meaning goes with it
{"kind": "verdict", "label": str, "state": str, "score": float | None, "meaning": str,
 "parts": [{"label": str, "state": str, "value": float | None, "note": str}, ...]}
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
| `reports/<P>/<D>/<day>/<study>/*.csv` with a `strategy` column | `ui/daemon/studies.py` |
| `harvest/<P>/<D>/<day>/{metrics,equity,trades}.parquet`, `missing_oos.csv`, `manifest.json` | `ui/daemon/gateview.py` |
| `reports/.../gate/{scorecard.parquet,funnel.csv,manifest.json}` | `ui/daemon/gateview.py` |
| every study's `python3 -m ….report` and its flags | `ui/daemon/runs.py` |

Check with `bin/algoui`: a broken import in the daemon is the whole window failing to open.
