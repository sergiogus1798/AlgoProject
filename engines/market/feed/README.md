# engines/market/feed — what is wrong with a price feed, minute by minute

The detectors of encargo 17, kept apart from the study that reads them
(`studies/data/feedQuality/`) so any study that needs "was this minute of the feed sound?"
can ask without importing a study. They compute; what a count means, and every threshold,
is the study's and the ledger's.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Feed-quality detectors over M1 bars: the scale of an ordinary move, spikes, frozen runs, gaps. | — | — |
| `runs.py` | Frozen runs of identical bars, and holes in the session, as event tables. | imported | bars + session → event tables |
| `scale.py` | The size of an ordinary one-minute move at each hour of the week, trailing, with a floor. | imported | bars → σ per bar |
| `session.py` | A feed's trading week as a minute-of-week mask: deduced from the feed, written and read as text. | imported | bar minutes → mask |
| `spikes.py` | Spikes on the close and on the wick, in units of the bar's own scale, and whether they reverted. | imported | bars + σ → z, reversions |

Nothing here reads a file: arrays in, arrays out. `tests/test_feedquality.py` plants events of
known size in a synthetic feed and checks each is found or missed as its size says.
