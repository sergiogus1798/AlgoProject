---
q: SQX MQL5 export writes no mq5; Template not found MetaTrader5 MoneyManagement ATRRiskBasedSizingFixedRisk_variables.tpl; SaveToFiles exports last backtest sizing; user snippet money management no MT5 template; Verificar SQX no escribió el .mq5
tag: 🔬  date: 2026-09-30  see: eng/mt5-account-switch-unattended, sqx-drive/export-mql5-source-headless
---
# SaveToFiles writes the sizing the strategy was last backtested with; the doctrine's has no MT5 template
`ATRRiskBasedSizingFixedRisk` (the doctrine's money management) is a user snippet
(`user/extend/Snippets/SQ/MoneyManagement/*.java`) with no MetaTrader 5 source template, so an EA
export of a strategy last retested with it logs «Template not found … ATRRiskBasedSizingFixedRisk
_variables.tpl» and writes nothing — the task still says «Task finished». `sqx.projects.mt5verify`
exports from the first firm's retest, which ran the strategy's own FixedSize; that EA is «Fixed size»,
sized by `mmLots` with no `UseMoneyManagement`/`mmLotsIfNoMM` — `mt5side.fixed_lots` handles both.

## Evidence
- 🔬 2026-09-30, `Strategy 10.1.79` (USDJPY H1, `strategy_Portfolio.xml` FixedSize 0.1, last retested
  in the workflow with the ATR sizing): exported from `MT5VerifyIn` → no `.mq5`, the error above in
  `log_2026_09_30.log` at 09:57:18.
