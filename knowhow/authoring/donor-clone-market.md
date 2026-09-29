---
q: builder clone of donor still trades XAUUSD; project for non-XAUUSD asset built on gold; set_costs only rewrites matching Chart symbol; resources.py borrow Symbol InstrumentInfo Broker; zero Setup on asset feed guard; unresolved resources; builder leaves half-built project on refusal; stray donor feed after swap; setups count not printed; builder scope from the master session or instrument only never task config; InstrumentInfo embeds a cost blob but Setup governs
tag: 🔬  date: 2026-09-29  see: sqx-drive/only-flag-wrong-databank, costs/per-task-costs, eng/feed-in-config-yaml, costs/sessions-per-asset
---
# A donor clone must have its feed swapped, staged before it ever touches an install, and refused if the swap left a trace
`sqx/projects/resources.py` borrows `<Symbol>`/`<InstrumentInfo>`/`<Broker>` from a project already
trading the asset (`source.py` finds it) and swaps the donor's `<Chart>` only — hand-editing
`<InstrumentInfo>` is what gives "Project has unresolved resources". 🔬 2026-09-29 (OPEN.md 34-35,
closed): `build` used to write into `user/projects/<name>/` before `configure` could still raise,
leaving a half-built clone behind; it now stages the .cfx in a `tempfile` dir and only moves it in
once `resources.refuse()` (an ignored template, a task's `setups` at 0, or the donor's feed string
still present after a swap) has passed. `summary.say` now prints `setups` per task.

## Evidence
Log: `CONSTRUCCION : Loading backtest data for Higher backtest precision - XAUUSD_DukasM1_Infinox / H1`.
Cause: `setups.py` `set_costs` rewrites only a `<Setup>` whose `<Chart symbol=…>` already is the asset.
Donor feed read from the first `<Chart>` of its Build task; same mechanism as `borrow_session`.
Guard: `builder` refuses when a task ends with zero `<Setup>` on the asset feed (count existed since 2026-09-23, unread).
`runs.csv` holds only XAUUSD runs, so probably nothing contaminated.
`tests/test_builder_feedswap.py`: building `Test_USDJPY_feedswap` from the frozen donor leaves no
occurrence of the donor's feed in any task and prices every task; building `USA500` (no session
source exists) raises `SystemExit` and leaves the staging install untouched. Verified once against a
real conductor install (`SQX_w1`) on 2026-09-29: `Test_USDJPY_feedswap` built clean, `-project
action=status` listed it with no "unresolved resources" anywhere in the worker log.
🤔 Indices (USA500, USATEC, DAX40, …) have no session defined on any install as of 2026-09-29:
`source.pick` returns `None` and `builder` correctly refuses. A data gap (register the session in
SQX first), not a code bug — `--symbol` alone still cannot author an index today.

## Builder scope: only bar data, instrument definitions and sessions from the master
Audited 2026-09-29 (owner's scope rule): `source.pick` may land on a project on the **master**
itself — it is just the newest install with any project defining the asset's session/feed — so
what `resources.definitions`/`doctrine.borrow_session` are allowed to take from it matters. Read
end to end: `resources.definitions` returns exactly `<Symbol>`, `<InstrumentInfo>`, `<Broker>`;
`doctrine.borrow_session` exactly one `<Session>`. Neither ever touches a `<Setup>`, a `<Task>`, a
`<Databank>` or an acceptance/exit block — confirmed by grepping every forbidden tag out of the
three borrowed blocks (`tests/test_builder_scope.py::test_definitions_scope`/`test_session_scope`).

⚠️ The borrowed `<InstrumentInfo>` embeds the master's own cost blob whole
(`defaultSpread="0.1" … commissions="…8…" swap="…-73.42…"` on a real master project) — it is SQX's
identity field for the instrument, not inert text, so "nothing but definitions is copied" is not
provable by grepping the borrowed block alone. What proves it is `setups.py`'s `set_costs`, which
rewrites **every** `<Setup>` from `assets/`'s own declared costs unconditionally, per task, on
every build — never conditionally on what the donor or a borrowed `InstrumentInfo` already carried.
`test_finished_setups_carry_assets_costs_not_the_masters` builds a real USDJPY project borrowing
from the master (`defaultSpread="0.1"`) and checks every `<Setup>` trading USDJPY carries
`assets/symbols/USDJPY.yaml`'s declared 0.65 — the master's 0.1 never appears in a finished Setup.
Nothing to fix: the existing split (identity in `<InstrumentInfo>`, cost in `<Setup>`) already
enforces the rule; the gap this closes was that nothing said so out loud or tested it end to end.
