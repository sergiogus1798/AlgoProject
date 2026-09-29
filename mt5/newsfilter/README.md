# mt5/newsfilter — a prop firm's news rule, written into SQX's MQL5 export

SQX exports an EA with no news filter. A funded account at Hantec (or FTMO) may not open or close a
trade within a few minutes of a high-impact release, so every EA that goes to such an account is run
through this first. Per strategy it writes **two** EAs (owner, 2026-09-29): `<name>_<Firm>.mq5` with
the filter, for the funded account, and `<name>_NoNews.mq5`, SQX's own untouched, for the challenge
or an account with the news add-on. Skill: `/ea-news`. Manual: chapter `75-filtro-noticias`.

What the filter does, per firm (`firms.py`): from `close_before` minutes before a release until
`rule_minutes` before it, close this EA's positions and cancel its pending orders (an SL or TP hit
inside the window is a close); from `block_before` before until `block_after` after, open nothing.
Hantec: releases from MT5's calendar (HIGH) and Forex Factory's red folder, counting for a symbol
when their currency is in its name or is the country of its index or commodity (`COUNTRY_OF`).
FTMO: only FTMO's own restricted list (`FTMO_EVENTS`, 37 MT5 event codes — MT5 rates half of them
medium, `knowhow/eng/ftmo-news-vs-mt5-importance.md`), crude inventories on oil alone.
**Neither calendar exists in the Strategy Tester**: there the filter does nothing, so a backtest
cannot show what it costs. `knowhow/eng/ea-news-filter.md`.

| file | what it does | run it | in → out |
|---|---|---|---|
| `firms.py` | Each firm's window, calendars and symbol → currency map | imported | — |
| `patch.py` | Insert the filter at the four places of an SQX export: inputs, helpers, the call in `OnTick`, a guard in every entry rule; refuses a source it cannot place | imported | .mq5 text → .mq5 text |
| `run.py` | Both EAs per strategy into `MT5_DATA/eas/<Firm>/`; `--compile` copies them to `MQL5/Experts/AlgoProject/<Firm>/` and compiles (terminal closed) | `python3 -m mt5.newsfilter.run hantec <mq5 or folder>... [--compile]` | SQX .mq5 → two .mq5 (+ .ex5) |

`mql/` holds the MQL5 the filter is made of, as `string.Template` text (`$label`, `$rule_minutes`…).
Test: `tests/test_newsfilter.py`, against the hand-made FTMO patch kept in
`MT5_DATA/newsfilter-reference/`.
