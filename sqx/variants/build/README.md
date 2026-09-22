# sqx/variants/build — how a combination becomes a file

Mechanics. Nothing here decides anything: it is handed a tuple and it writes it.

| file | what it does | in → out |
|---|---|---|
| `rewrite.py` | One `.sqx` into another: new values, new name, identifier stamped inside, inherited fingerprint gone | members, tuple → members |
| `fabricate.py` | Every row of a plan, written to a folder | plan → files |

## What a rewrite changes, and nothing else

**Substitution, not an XML round trip.** Every member SQX has to read back comes out byte-identical
everywhere the tuple did not reach. A round trip through `ElementTree` would reformat attributes,
self-closing tags and whitespace across a 33 KB file that SQX parses with its own reader, for no
gain. `tests/test_variants.py` holds that as an invariant: rewriting the parent's own tuple back
into the parent reproduces the parent byte for byte apart from the stamp.

| what | where | why |
|---|---|---|
| the parameter values | `strategy_Portfolio.xml`, `<variable><id>NAME</id>…<value>N</value>` | the only place a parameter lives. The rules reference the variable by name, so rewriting `<value>` rewrites the rule. `settings.xml` carries no parameter names at all |
| the identifier | a comment after the XML declaration of `strategy_Portfolio.xml` | SQX may rename on collision, so the external name cannot be the identity |
| the name, twice | `settings.xml`: `<ResultsGroup ResultName>` **and** `<StrategyName>` | miss one and the whole batch arrives in the databank under a single name |
| the fingerprint, removed | `settings.xml`, the `<Fingerprint>` element | every variant inherits the parent's. If the databank deduplicates on it, the batch collapses to one strategy |

`set_values` raises when a name in the tuple is not a variable of the strategy. A silent miss is the
failure this whole module is arranged against: the manifest would claim a combination the file does
not contain and nothing downstream could tell.

**Int is not double.** The variable declares its type and the value is written to match — `67`, not
`67.0`. SQX itself writes an integral double without a decimal point (`TrailingStop1` is `50` in the
test fixture), so `%g` is its convention, not an approximation of it.

## Shapes

`rewrite.SHAPES` decides which ZIP members a variant carries. Measured on `Strategy 17.9.39`,
2026-09-21, per file and for a batch of five thousand:

| shape | members | size | 5,000 | time |
|---|---|---|---|---|
| `minimal` | `META-INF`, `settings.xml`, `strategy_Portfolio.xml`, `lastSettings.xml`, `version.txt` | 13.7 KB | 70 MB | 6 s |
| `no_profile` | everything but `optimizationProfile.bin` | 98.7 KB | 505 MB | 49 s |
| `full` | a copy of the parent's members | 123.3 KB | 631 MB | 65 s |

Which one is right is **open** — whether SQX loads a 5-member file at all is not known on this
install. `config.yaml` picks; nothing else changes. Note the numbers depend on the parent: this one
carries a 306 KB optimization profile, and a parent whose SPP was run with 3D-chart data stored
carries a 2.2 MB one, which makes `full` roughly twenty times worse.
