# engines/market/feed — what is wrong with a price feed, minute by minute

The detectors of encargo 17, kept apart from the study that reads them
(`studies/data/feedQuality/`) so any study that needs "was this minute of the feed sound?"
can ask without importing a study. They compute; what a count means, and every threshold,
is the study's and the ledger's.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Names what the package is; holds no code | — | — |
| `scale.py` | Bar times as whole minutes since a Monday, close-to-close log returns that never cross a hole, and the size of an ordinary move per hour of the week: MAD × 1.4826 over the whole weeks before each week, growing from a minimum, never under a tick floor nor a share of that week's median hour | imported | bars → σ per bar |
| `spikes.py` | Each bar's move on the close and past its body on the wick, in multiples of its σ; which bars reach K and which of them came back within m bars | imported | bars + σ → z, reversions |
| `runs.py` | Frozen runs (consecutive identical OHLC, as one event each) and holes of in-session minutes with no bar | imported | bars + session → event tables |
| `session.py` | A trading week as a minute-of-week mask: deduced from the minutes a feed quotes in most weeks, written as and read from text, with hours cut out, and the prefix count that turns a span of minutes into its in-session minutes | imported | bar minutes → mask |

Nothing here reads a file: arrays in, arrays out. `tests/test_feedquality.py` plants events of
known size in a synthetic feed and checks each is found or missed as its size says.
