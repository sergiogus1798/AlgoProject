---
q: USDJPY no tiene símbolo en FTMO, mt5 symbols.csv empty for an asset, verify refuses a firm no symbol, why does FTMO have no USDJPY when it obviously does, symbols.csv only lists XAUUSD, which asset needs a row in mt5/symbols.csv, CFD index naming FTMO Hantec GER40 US30 JP225 US500 US100 UKOIL suffix .cash .h
tag: 🔬  date: 2026-09-30  see: eng/mt5-account-switch-unattended
---
# `mt5/symbols.csv` never had more than one row — every other asset "had no symbol", by design

Since 2026-09-30 (owner) the map lives in `mt5:` of each `assets/symbols/<S>.yaml`, versioned — the CSV was git-ignored and the fix existed only on disk. `mt5.verify.firms.usable()` refuses a firm the asset does not name — on purpose, never guessed (encargo 35 §1 #3). The file only ever had the `XAUUSD` row; nobody added the other 17, so every other asset "had no symbol on FTMO", USDJPY included, though FTMO obviously carries it — the mapping logic was never wrong, the data was never filled in.
Filled from a live read (`mcp__mt5__mt5_symbols`, see `eng/mt5-account-switch-unattended`), not guessed: FX and metals share the SQX name plus Hantec's `.h` suffix (`USDJPY`/`USDJPY.h`). Indices carry each broker's own name: DAX40→`GER40.cash`/`GER40.h`, DJ30→`US30.cash`/`US30.h`, NIKKEI225→`JP225.cash`/`JP225.h`, USA500→`US500.cash`/`US500.h`, USATEC→`US100.cash`/`US100.h` (FTMO suffixes CFDs `.cash`). BRENT is `UKOIL` on both, not `USOIL`/WTI.

## Evidence
2026-09-29: `mt5.live.ask("symbols", {"group": "*"}, account)` on `ftmo` (541350656,
FTMO-Server4, 166 symbols) and `hantec` (8063673, HantecMarketsMU-MT5, 75 symbols) listed every
name above verbatim. `mt5.verify.firms.usable("USDJPY")` and `.usable("BRENT")` both return
`why: null` for both firms after `mt5/symbols.csv` was filled for all 18 assets in `assets/symbols/`
(excluding `_retired/`).
