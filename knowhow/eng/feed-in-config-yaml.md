---
q: can a config.yaml name the feed / symbol / asset? wrong feed, scored against gold bars, crossTF USDJPY, reconciliation below 0.99
tag: 🔬  date: 2026-09-24  see: research/bar-file-wider-than-backtest
---
# A config.yaml declares thresholds and models, never the asset
Which asset/feed a run reads is a property of the run and goes on the command line (`--project`, feed arg).
A fixed `feed:` in a module's `config.yaml` silently scores every other asset against the wrong bars.
Asset names in warnings must come from the feed actually read, not from config.

## Evidence
- `strategies/crossTF/config.yaml` had `run.feed: XAUUSD_DukasM1_Infinox`. crossTF on USDJPY scored all
  12 cells against gold bars: reconciliation vs SQX P/L −0.20 to −0.34; correct feed → 0.98–0.99.
- The gate caught it: `RECONCILIACION ... por debajo de 0.99` fired in all 12 cells ("nothing below
  describes the backtest SQX ran"). Missing piece was only that the feed was a constant.
- Provisional-cost warning also named XAUUSD for any asset; now from `assetdata.symbol_for(feed)` +
  `assetcheck.provisional()`.
- 🤔 Still to review: `strategies/sppUltra/`, `strategies/retest/`, `strategies/crossmarket/` take
  `--project`, but check none stores a feed.
