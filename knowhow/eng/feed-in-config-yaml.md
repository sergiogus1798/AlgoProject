---
q: can a config.yaml name the feed / symbol / asset / timeframe? wrong feed, scored against gold bars, crossTF USDJPY, reconciliation below 0.99, XAUUSD shown in a USDJPY project, config viewer donor values
tag: 🔬  date: 2026-09-28  see: research/bar-file-wider-than-backtest
---
# A config.yaml declares thresholds and models, never the asset
Which asset/feed a run reads is a property of the run and goes on the command line (`--project`, feed arg).
A fixed `feed:` in a module's `config.yaml` silently scores every other asset against the wrong bars.
Asset names in warnings must come from the feed actually read, not from config.
The window's runner (`ui/daemon/runner/`) passes the project's feed/symbol/timeframe by `--set`,
and `ui/daemon/results/forproject.SET` lists them so the config viewer shows what will run.

## Evidence
- `studies/transfer/crossTF/config.yaml` had `run.feed: XAUUSD_DukasM1_Infinox`. crossTF on USDJPY scored all
  12 cells against gold bars: reconciliation vs SQX P/L −0.20 to −0.34; correct feed → 0.98–0.99.
- The gate caught it: `RECONCILIACION ... por debajo de 0.99` fired in all 12 cells ("nothing below
  describes the backtest SQX ran"). Missing piece was only that the feed was a constant.
- Provisional-cost warning also named XAUUSD for any asset; now from `assetdata.symbol_for(feed)` +
  `assetcheck.provisional()`.
- 🤔 Still to review: `studies/breakage/spp/`, `studies/breakage/mcRetest/`, `studies/transfer/crossmarket/` take
  `--project`, but check none stores a feed.
- 2026-09-28: the owner saw «XAU USD» in a USDJPY project (Calidad de entrada, Nube de parámetros).
  The viewer showed config.yaml's donor values; entryQuality/conditionalMap ran right (`--set`), but
  `cloud` (`run.symbol`), `exposure` (`study.timeframe`) and `gate` (`monkey.timeframe`) ran on the
  donor's XAUUSD/M30. Harmless on that M30 project (cloud's symbol only matters under
  `ALGO_AUTONOMOUS`); wrong on H1/H4. Runner now sets all three.
