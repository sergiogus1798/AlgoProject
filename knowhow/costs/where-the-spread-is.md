---
q: where is the spread charged SQX; spread in fill prices not commission; double counting spread; why assets split forex vs no_forex; percentage commission; field meanings assets
tag: 🔬  date: 2026-09-22  see: export/fill-and-pricing, costs/commission-methods, costs/swap-types
---
# The spread is in the fill prices, not a charge — folding it into a commission charges it twice
Read `knowhow/costs/` before writing a number into `assets/`: three cost fields mean something other than their name.
`assets/` splits classes: forex = one spread + dollar commission; everything else = two spreads + percentage commission and swap. Schema `assets/_classes.yaml`, checked by `core.assets.validate()`.

## Evidence
- Source for the cost cards: decompiled `internal/libs/SQTradingLib.jar`, `internal/extend/Snippets/SQ/Trading/Commissions/*.java` (2026-09-22).
- Gold entry 0.05 above bar open, exit on it = `defaultSpread 10.0 points × tick_size 0.01 = 0.10`, half per side (`export/fill-and-pricing`). Never in the `gross − P/L` residual.
- 🤔 Why split: a fixed point spread is a constant $ cost while price moves. Gold 2008–2017: 0.10 = 0.0083 % of notional at 1200, 0.0029 % at 3500 (3× inside the build sample). FX doesn't move like that.
