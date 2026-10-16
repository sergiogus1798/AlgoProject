---
q: Does the identity a study records for a strategy change between databanks of one project?
kw: same strategy name different identity across databanks of one project, pair results across databanks, Results vs OOS vs MCR_All vs WFM identity, MCR_All drops Strategy prefix, matrix pairing by identity, name collision, WFM reorders variables
tag: 🔬  date: 2026-10-16  see: sqx-format/strategy-identity, databanks/curate-verdict-identity-per-databank, sqx-format/loaded-name-is-filename, sqx-format/names-reused-between-builds
---
# One identity across every databank of a project — the WFM included since 2026-10-16
Rule (rewritten 2026-10-16): with the canonical identity (`strategy-identity`) one strategy keeps one identity from Results through SPP and the WFM. Not: «the WFM rewrites the parameters» — the WFM files of `SQX_w2` measured on 2026-10-16 only wrote the same variables in another order with the same values; the text hash called them other strategies. A WFM that really picks other values is still another identity. Step-12 sisters differ (fabricated file vs retested copy). A name alone is not a key: `MCR_All` drops the `Strategy ` prefix and builds reuse names. Pair by identity, or through `lineage.csv`.

## Evidence
- ⚠️ Superseded count — an artefact of the unstripped attributes, kept as the repro of the trap. `ui.daemon.results.matrix.matrix(P, D)` identities, pairwise shared (2026-09-26):
  `Results` 200 vs CrossTF / MCR_All / OOS / Retest_Markets_-_Family / SPP_IS / SPP_OOS / WFM → 0 each;
  those six retest banks share 8 (3 with OOS) among themselves; `WFM` 3 → 0 with all.
- `Strategy 1.23.51`: `Results/gate` and `snoopingScreen` verdict.csv `0b91ad2b2354…`;
  `OOS/exposure`, `CrossTF/crossTF`, `MCR_All/mcRetest` `8f9c864c1f46…`.
- Cause found 2026-10-06 (above): the strip. Original note: The gate keys by the BUILD identity by design (`studies/screening/gate/
  pairing.py` keeps an alias for a retest identity that changed); `wfm` signs `None` in its JSON and
  its verdict.csv carries another. Contrast `strategy-identity`: 115/115 normalised identities
  matched across one XAU retest — so "identity survives a retest" is not general. Confirm with
  `core.sqxfile.identity()` on the `.sqx` files of two databanks.
- 🔬 2026-10-12 The identity carried runtime state: the four signal variables
  (`LongEntrySignal`, `ShortEntrySignal`, `LongExitSignal`, `ShortExitSignal`) are saved with
  the value the LAST bar of the last backtest left in them, so a strategy whose entry held on
  the build's final bar and not on the retest's had two identities. `Test_XAUUSD_H1_verif`
  (custodian, seeded random entry): 4 of 6 differed between `Results` and `OOS`, the only
  difference `<value>true</value>` → `false` under `LongEntrySignal`, and the harvest stopped
  («COSECHA PARADA … mismo nombre e identidad distinta 4»). Real builds carried it too: 83 of
  400 files of `Trade_NIKKEI225_M30_volatilidadL/Results` hold a `true`. Fixed that day
  (owner's order): `core.sqxfile._hashed` hashes those four as `false` (`SIGNAL`), 6 of 6 pair,
  and an identity that never held a `true` did not move (`tests/test_sqxfile.py`).
- 🔬 2026-10-12 The store was re-keyed with it: 94 of 866 folders carried a moved identity —
  63 renamed, 31 merged into the folder the SAME strategy already had under its other identity
  (866 → 835; a repeated test of another content became `<stem>.N.zip`, a step both had said
  differently stays under the manifest's `merged`), each manifest keeping the old identity in
  `aliases`. Copy of every touched folder: `AlgoData/backups/store-identidad-2026-10-12.tar`.
  Not rewritten: the dated exports and reports of earlier runs (`raw/…/identity.csv`,
  `lineage.csv`, `reports/…/verdict.csv`, ~430 files of `Test_` projects) still name the old
  string for those strategies; a re-export writes the new one.

🔬 2026-10-16 `tests/fixtures/identity/wfm_reordered.*.sqx` (from `SQX_w2`): build and WFM file differ only in the order of `<Variables>`; old identity differed, canonical one is equal.
