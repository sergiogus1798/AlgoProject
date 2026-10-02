---
q: why is a QLabel text cut at a "<" — a trading rule like "Close[1] < Open[1]" shown truncated in the window
tag: 🔬  date: 2026-10-01  see: ui-tests-pytest-fixture-fake
---
# A QLabel in rich text drops everything after a bare `<`: escape what an agent or a person wrote
A label whose text contains any tag (`<b>`, `<br>`) is parsed as HTML, and a `<` inside the data
— every entry rule has one — opens a tag that never closes: the rest of the sentence vanishes, with
no error. Text that comes from an idea, a proposal, a verdict or a note goes through `html.escape`
before it is put between tags (`ui/desktop/research/parts.esc`).

## Evidence
`tests/test_ui_research.py` offscreen shot of the proposal, 2026-10-01: the rule «Corto … si
Close[1] - Open[1] < -2 × ATR(14)[2]» was painted as «Corto … si Close[1] - Open[1]». After
`esc()` on every agent-written field the whole rule shows.
