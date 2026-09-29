---
q: news filter for SQX EA, prop firm news rule Hantec FTMO, patch mq5 exported by SQX, where to insert inputs OnTick entry rule, Forex Factory calendar JSON faireconomy, red folder impact High, WebRequest allowed URL 4014, pending orders cancelled before news, sqCloseAllPositions, SQX mq5 not ASCII
tag: 📓  date: 2026-09-29  see: eng/mt5-tester-unattended, eng/metaeditor-compile-under-wine
---
# An SQX EA gets a news filter at four fixed places; `mt5.newsfilter` writes it, and it only acts live
- SQX's MQL5 export has the same shape in every EA: inputs go before `// Money Management variables`, helpers after `// -- Functions`, the call after `openingOrdersAllowed = sqHandleTradingOptions();`, and `&& !newsBlock` before the lone `)` of every `// Rule: Long|Short entry`. `python3 -m mt5.newsfilter.run <firm> <mq5...>` does it and refuses any other shape; never hand-edit.
- `sqCloseAllPositions("Any", MagicNumber, ±1, "")` closes this EA's positions **and** its pending orders — no separate `OrderDelete` loop is needed (the hand FTMO patch had one).
- Forex Factory: `https://nfs.faireconomy.media/ff_calendar_thisweek.json`, compact JSON, `impact:"High"` = red folder, `date` in New York time **with its offset** (`2026-09-29T08:30:00-04:00`). Needs the URL in MT5 → Options → Expert Advisors → WebRequest (else error 4014).
- A global variable named with `_` can be deleted by SQX's `OnTimer` cleanup (it splits names on `_`); the filter's is `AlgoProjectNewsFFFetch`.
- SQX's `.mq5` can hold UTF-8 bytes (not pure ASCII): read and write it as UTF-8.

## Evidence
2026-09-29: the 6 before/after pairs of the owner's FTMO patch (`AlgoData/mt5/newsfilter-reference/`) insert at exactly these anchors — `tests/test_newsfilter.py` reproduces every insertion point. `sqCloseAllPositions` and `OnTimer` read in `Strategy 3.23.151.mq5` (SQX build of 2026-04). FF feed fetched with curl that day. `Strategy 3.23.151.mq5` has byte 0xe2 at 175305. The 14 Hantec/NoNews EAs compiled 0 errors, 0 warnings (MetaEditor, build 5830). Live behaviour (a close logged before a real red release) not yet seen — OPEN.md #85.
