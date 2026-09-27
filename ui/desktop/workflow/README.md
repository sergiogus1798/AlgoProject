# ui/desktop/workflow — the rail

`WorkflowRail(QFrame)`, named `term`: the steps of `docs/AgentPDFs/WORKFLOW.md` for the project
in `SELECTION`, one painted row each — a node on a vertical line whose shape and colour say the
state (✓ done, ring pending, dashed ring missing, × blocked, dot running, envelope sealed), the
number, the title, SQX/PY/TÚ, the state word and the funnel `N → M` with the loss in red.
Above it, the oos2 gauge (one cell per look, amber when the step is reserved, red when not) and
the 17·18·19 envelope. Every row, cell and envelope carries its `why` on hover. Clicking a step
emits `open_step(dict)` with the step as `GET /api/workflow` sent it.

**Imports from:** `ui/desktop/{client,selection,theme,blocks/states}` · **Consumed by:** `shell.py`

| file | what it does | run it | in → out |
|---|---|---|---|
| `rail.py` | `WorkflowRail`: follows the selection, asks the daemon, lays out gauge, envelope and rows | imported | project → widgets |
| `steprow.py` | One step painted, its tooltip, and the envelope glyph the gauge reuses | imported | step → row |
| `gauge.py` | `Oos2Gauge` and `BlindBanner`, the two locks above the rail | imported | oos2, blind → paint |
| `states.py` | The six step states as colour and word, on top of `blocks/states.py` | imported | state → colour |

## Traps

- **A signal hands over a copy of the dict.** The rail marks the chosen row by the row object,
  never by `step is ...`.
- **Rows are detached before `deleteLater`.** Otherwise the old rows paint under the new ones
  until the event loop runs.
