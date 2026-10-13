---
q: Do the four rungs of the monkey (timing, timing_holds, timing_sizing, free) draw the same random entries?
kw: common random numbers, shared entries, rungs share stream, RUNG_ID removed, N12 B, encargo 66, results before 2026-10-13 not comparable, z_mono_timing_holds, paired difference between rungs, attribute channels variance
tag: 🔬  date: 2026-10-13  see: research/random-entry-nulls, perf/rng-floor-in-table-lookup-monte-carlo
---
# Since 2026-10-13 the four rungs of the monkey read ONE random stream per strategy
Owner, N12 B (encargo 66). Both families (the ladder `engines/nulls/model.py` + `simulate.nulls`, and the gate's
windowed monkey `windowed` + `lookup` + `level3c`) seed per strategy (and ladder block) with NO rung in the key
(`RUNG_ID` is deleted). The uniforms that place the entries come first and are the same for the four rungs; the
redrawn holds come second and are the same for `timing_holds` and `free`. A rung maps a uniform onto the bars ITS hold
leaves room for, so entries are identical for `timing` = `timing_sizing` and for `timing_holds` = `free` (all four
when the holds are equal); each rung alone is the null it was (same law, `tests/test_perf66_shared_entries.py` b).
**Every z, p and distribution stored before this date was drawn with another stream: not comparable draw for draw, only in law; `core/manifest.code_version` (the commit) is the only marker.**

## Evidence
- Why: the gap between two rungs is the channel's worth; on shared entries its variance fell to 0.14-0.43 of the independent one (timing vs timing_sizing 0.14, timing_holds vs free 0.15, timing vs timing_holds 0.43, MEASURED on a 60-trade synthetic strategy).
- Layout: `windowed.draw` always takes `rng.random((draws, 2, n))`; `lookup._fill` skips layer 1 on rungs that keep
  their hold (one extra PCG jump per draw: 0.66 -> 0.67 s for 4 rungs x 100,000 draws, n = 150).
- `level3c._one` keys the stream by `str(identity)` only, so `--only` / `rungs=` replays the full run's entries.
- The levels' reuse across passes (level 0/1a, level-2 table, `q_p`) never touched the draws of other rungs: unaffected.
