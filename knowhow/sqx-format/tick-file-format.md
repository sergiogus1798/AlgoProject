---
q: read SQX tick data without SQX; read M1 bars from SQX History without export; _M1.dat format; _TICK.dat format; DarwTick feed ask bid; decode tick file; History folder .dat; spread from ticks; SQDataLib TickDataReader; ICryptable internal.dat
tag: 🔬  date: 2026-09-27  see: export/feed-clock-timezones, costs/darwinex-real-spread
---
# A `*_TICK.dat` is plain, delta-coded ask/bid: `core.tickfile` reads it without SQX, 650 M ticks in 25 s
Path `SQX/user/data/History/<feed>/<feed>_TICK.dat` (`core.datapaths.tick_file`); one file per feed, several GB.
SQX's own classes can't be called from outside: `SQDataLib.jar` needs `ICryptable`, which lives in the encrypted `internal.dat`. Reimplemented from the bytecode instead.
Header = Java UTF "4.2", "D" (plain; "C" = encrypted), "ABCDEFGH", long, int n × (UTF, int), "SnRbTs". Then every 1,000 records a 15-byte chain 00..0e + int block index. Record = 2 config bytes + time, ask, bid, volume, each 1/2/4/8 bytes big-endian unsigned (2 bits) applied as minus/plus/as-is (2 bits). Prices ÷ 10^6, volume ÷ 10^5.
`*_M1.dat` (bars) is the same format, 3 config bytes and six values (time, O, H, L, C, volume): `core.tickfile.bars`, 8.7 M USDJPY bars in 2 s, equal to the library's SQX export except a duplicated 2003–04 hour (keep the first).
Times are ms on the feed's naive clock — the same clock as its M1 bars (gold's first tick 2017-10-02 01:01, Dukascopy's first bar 01:00).

## Evidence
- `javap -c -p` on `newDataFormat.{TickDataReader,NewDataFormat,NewDataFormatReader,TickDataBinReaderNew,DataBinReaderNew}` from `internal/libs/SQDataLib.jar` (JDK in `SQX/j64/bin`).
- Config bits: c0 = time logic<<6 | time width<<4 | ask logic<<2 | ask width; c1 = bid logic<<6 | bid width<<4 | vol logic<<2 | vol width.
- Validated against Dukascopy M1 closes, minute by minute: 1-min return correlation 0.99 (gold) / 0.985 (USDJPY), level difference 0.09 / 0.001 median. `tests/test_spread.py` round-trips a hand-written file.
- USDJPY_DarwTick_the5ers 368 M ticks 13 s; XAUUSD_DarwTick_Infinox 647 M ticks 25 s (numba, memmap).
