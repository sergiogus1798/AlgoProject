# ui/desktop/matrix — the population matrix

`Matrix(QFrame)`, named `term`: the strategies of the databank in `SELECTION` (rows: name +
identity) against the studies (columns), each cell painted in its contract state's colour from
`blocks/states.py`, with the study's own label, hatched and marked ◷ when today's config would sign
another hash, «·» when never run. Each study header carries its role mark (red disc = eliminates,
`gate`; eye = only describes), the title, a bar and the counts per state of the **visible** rows;
its tooltip says the step and what the role means. Pickers for project and databank come from
`/api/projects` and write into `SELECTION`. What the daemon could not read (`skipped`) is one
amber line above the grid, never hidden.

Clicking a study cell (no Ctrl/Shift) chooses that strategy and identity in `SELECTION` and emits
`open_study(key)`; clicking a study header emits `open_population(key)`; clicking a fixed header
sorts. Right-click on a header: sort ▲/▼, show/hide each state, and on a gate column the `/curate`
command. Ctrl/Shift-click selects several rows; the run bar queues one per-strategy study on them
through `POST /api/study/run` (scope `one`) and prints the daemon's refusal sentence if any.

**Imports from:** `ui/desktop/{client,selection,theme,blocks/states}` · **Consumed by:** `shell.py`

| file | what it does | run it | in → out |
|---|---|---|---|
| `view.py` | `Matrix`: pickers, name filter, all-studies toggle, table wiring, clicks and signals | imported | selection → widgets |
| `model.py` | `MatrixModel(QAbstractTableModel)`: visible rows filtered and sorted in Python, counts per column, tooltips | imported | `/api/matrix` → cells |
| `paint.py` | `CellDelegate` (state colour, stale hatch) and `StudyHeader` (role mark, title, bar, counts) | imported | model → pixels |
| `menus.py` | Column menu, state filters, clear filters, the gate-study picker for /curate | imported | view → menu |
| `actions.py` | `RunBar` (batch run of one study) and `CurateStrip` (the /curate line to copy, and what applying it means) | imported | selection → job · command |

## Traps

- **No proxy model.** Sorting and filtering rebuild `model.rows` (indices into `strategies`) in
  Python; a `QSortFilterProxyModel` would call back into Python per comparison. 5,000 × 10
  measured 2026-09-26 offscreen: load + first paint 0.08 s, sort 0.02 s, filter 0.07 s.
- **The sort survives filters and the all-studies toggle** because it is kept by field (study
  key), not by column index.
- **No font here has ⛔ or 👁.** The header paints both marks; text elsewhere uses ⊘ and ◉.
- **The window never runs `/curate`.** The strip shows the command naming
  `AlgoData/reports/<P>/<D>/<day>/<study>/verdict.csv` of the newest day; the count it shows is
  the cells in `fail` on that day, which is what the study's `DESCARTAR` maps to.
- **Pairing never crosses databanks**: the matrix only asks for the chosen one.
