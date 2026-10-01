---
q: FTMO Hantec real commission per lot from deal history, swap worst case funded accounts, crude oil swap backwardation UKOIL USOIL, FTMO spread oil ticks, swap points unit MT5 vs SQX tickStep, swap differs per contract size
tag: 🔬  date: 2026-10-01  see: costs/swap-types, costs/commission-per-broker, eng/mt5-verify-clock-zones
---
# Funded accounts: commission confirmed from real deals; swap = worst of FTMO and Hantec, live
- Commission from the accounts' own deals: forex 2.50 $/lot/side at both (5 $ round trip); indices 0 at both; gold FTMO 3 $/lot/side at ~4,150 (≈0.0014 % round trip), Hantec 2.50 $/lot/side.
- Swap (owner, 2026-10-01): each side the worse of FTMO and Hantec — `studies.data.spread.fundedswap.worst()`, the onboard's `swap: funded_worst`. It is today's figure: rates and, on crude, the futures roll move it.
- Compare per notional, not per lot: Hantec's index lots are bigger (US30.h −365 $/night vs US30.cash −11.7 $).
- SQX `points` swap = `size × pointValue × tickStep × swap`: MT5 points, not pips.
- Crude in backwardation pays the long, charges the short hard: UKOIL FTMO +6.1/−27.5 $/lot/night, Hantec +15/−72 (≈ +21 % / −262 % annual). FTMO's oil spread tripled 2025-01 → 2026-09 (UKOIL 21 → 72 points of 0.001), 0.027 % → 0.070 % of price: not proportional to price, so not modelled back.
- Owner, 2026-10-01, crude cards: spread = FTMO today × 1.25 in all three segments (UKOIL 90, USOIL 97.88), the credited swap side written 0, segments as the indices (2013–2019 / 2020–2023 / 2024–). Silver commission 5 USD/lot assumes Hantec charges it like gold — unconfirmed.

## Evidence
`mt5.live.ask('history', {start, end}, MT5_ACCOUNTS[firm])`, 2026-10-01: FTMO 95 deals (EURUSD 2.22 lots −5.56 $, USDJPY 1.92 lots −4.82 $, XAUUSD 0.02 lots −0.06 $, US500/JP225/US100 0); Hantec 6 forex pairs −2.5 $/lot/side, US30/US100/US500/JP225 0.
FTMO ticks of UKOIL.cash / USOIL.cash exist from 2025 (none in 2023): time-weighted spread Jan-2025 21.0 / 24.6 points, Sep-2026 72.0 / 78.3.
