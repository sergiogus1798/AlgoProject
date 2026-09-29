---
name: ea-news
description: Make SQX-exported MetaTrader 5 EAs obey a prop firm's news rule — per strategy one EA with the firm's news filter (close before a high-impact release, no entries around it) and one without, both compiled. Use when the owner exports EAs from SQX for a funded account, asks to add or adapt a news filter, or names Hantec or FTMO news restrictions.
---

# /ea-news

SQX writes no news filter. An EA that trades through a red-folder release on a funded account can
lose the account. Everything here is `mt5/newsfilter/` — read its README first.

## 1. Which firm, and does it apply

`python3 -m portfolio.funded.catalog.show <firm>` and the `news_*` rules in
`AlgoData/funding/rules/<firm>.yaml`. Firms with a profile: `hantec`, `ftmo` (`mt5/newsfilter/firms.py`).
A firm without one is a **stop**: its window, its calendar and its symbol table are the owner's to
confirm (CLAUDE.md rule 11) — list what the firm's pages say and ask before adding the profile.

## 2. Every symbol is covered

For each EA, the symbol it trades must move with at least one currency: in its name (`EURUSD`,
`XAUUSD`) or through `COUNTRY_OF` in `firms.py` (`US500` → USD, `GER40` → EUR, `JP225` → JPY).
A symbol that matches nothing would never block: ask the owner which currency it takes, add it, and
rerun `python3 tests/test_newsfilter.py`.

## 3. Write and compile

```bash
python3 -m mt5.newsfilter.run hantec ~/Desktop/<folder of SQX .mq5> --compile
```

The MT5 terminal must be closed for `--compile` (MetaEditor shares its lock). Check the last line
reads **0 errores**; any error is a stop, not a retry.

## 4. Hand over

Tell the owner, in Spanish: where the two EAs of each strategy are (`AlgoData/mt5/eas/<Firm>/` and
`MQL5/Experts/AlgoProject/<Firm>/`); that `_<Firm>` goes on the funded account and `_NoNews` on the
challenge or with the news add-on; that Forex Factory needs `https://nfs.faireconomy.media` allowed
in MT5 → Herramientas → Opciones → Asesores expertos → WebRequest; and that **a backtest shows
nothing of the filter** — the calendar does not exist in the Strategy Tester.
