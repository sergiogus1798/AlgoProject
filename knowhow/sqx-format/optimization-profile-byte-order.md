---
q: Why does an SPP databank look changed after every SQX save though nothing in it changed?
kw: optimizationProfile.bin CRC changes every save, byte order differs same size, SPP databank re-exported at every stop, export fingerprint stale, zip CRC unstable, core/sqxfile mark byte histogram, _entries state.py
tag: 🔬  date: 2026-10-05  see: sqx-format/optimization-profile-bin, perf/autopilot-dead-time
---
# SQX re-serialises `optimizationProfile.bin` in a different byte order at every save — a zip CRC cannot fingerprint it
Trap: the member (19.5 MB inside each SPP-result `.sqx`) keeps its size and its multiset of bytes, but ~894k
positions move at every save, so its zip CRC changes. A fingerprint built from member CRCs calls every SPP
databank stale at each stop and re-exports it (63 s wasted per stop). Fix (230c856): hash that member
order-free — `core/sqxfile.py` `mark` uses a byte histogram; consumer `sqx/databank/state.py` `_entries`.
Not: "a changed CRC means changed content". 🤔 In the validation run the SPP databanks were still re-exported
at the stop of step 19 (WFM); another cause is open.

## Evidence
- 🔬 2026-10-05, `Test_NIKKEI225_M30_simpleL_ref`: two saves of the same SPP-result `.sqx`: same member size,
  same byte histogram, ~894k positions differ, different CRC. Reproduce: `unzip -p <a>.sqx optimizationProfile.bin`
  of two saves, compare with `cmp -l | wc -l` and a `collections.Counter` of the bytes.
- Format of the member itself: `sqx-format/optimization-profile-bin`.
