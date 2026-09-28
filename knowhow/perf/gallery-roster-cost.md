---
q: gallery slow, /api/projects/all 12 seconds, roster cost, find.roster lru_cache 64 thrash, count strategies of every project, identity hashing cost per strategy, total strategies per project
tag: 🔬  date: 2026-09-27  see: sqx-format/strategy-identity, sqx-format/project-cfx
---
# Counting every project's distinct strategies costs ~12 s once; keep the count cached per folder mtime
`loader.find.roster` hashes each `.sqx` (`sqxfile.identity`, ~1.7 ms each): 7 181 strategies on the
three installs = ~12 s cold. Its `lru_cache(maxsize=64)` cannot hold a walk over every databank
(~414 folders, ~57 non-empty), so a second walk cost the full 12 s again. Cache the **count** per
`(project, databank, mtime)` unbounded (`ui/daemon/projects/sources.distinct`), skip empty folders
without hashing, and fetch the gallery off the GUI thread. Warm: ~0.03 s.

## Evidence
- 2026-09-27, `sources.gallery()`: cold 13.5 s, warm 13.5 s with only find's cache
  (`CacheInfo(hits=0, misses=414, maxsize=64)`); warm 0.03 s with the count cache + regex chart.
- Distinct < files: XAUUSD on the master holds 1 805 `.sqx` and 1 679 identities.
