# nulls — the monkey study: is this better than a monkey trading the same market?

One question, asked the same way everywhere it is asked: **how much of this result would a
random trader have got, given the same opportunity set?** A strategy's trades go in, thousands
of imaginary runs on the same bars come out, and each statistic gets an empirical p.

```
config.yaml ─▶ inputs ─▶ calibrate ─▶ model ─▶ simulate ─▶ verdict ─▶ report
 every knob    what it   what SQX     what      the         what there  the
               runs on   charged and  could     numbers     is to       panel
                         how it       have      under a     distrust
                         filled       happened  rung
```

The engine that draws the monkeys is `engines/nulls/` (with `engines/market/calibrate.py`);
this folder is the study that reads one strategy, or one export, against it. Its knobs are the
engine's `config.yaml`.

| file | what it does | run it | in → out |
|---|---|---|---|
| `one.py` | **One strategy against its monkeys, as the contract's data**: where it landed on every rung and statistic, the ladder, where its edge came from, and every reason to distrust it | imported — the window calls it | one strategy → result |
| `many.py` | Every (strategy, market) of one export through every rung, one process each, each on its own market's bars: the panel `monkeyExcess` reads | imported | export → panel |
| `report.py` | **The command**: every strategy to `reports/<P>/<D>/<day>/monkey/nulls.csv` (one row per strategy and market, with `identity` and a `note` where none resolved) and its page, or `--strategy` for one read in full. On a cross-market export, leave out `--feed` and every market is tested on its own bars; `--feed` keeps one. `--seed N` fixes the root of every random stream: same seed, same `nulls.csv` byte for byte; without it a fresh root is drawn (owner, 2026-09-29). Either way the root used is in the manifest (`source.seed`, and in its `command`), in `nulls.csv`'s `seed` column (the fact `monkey.nulls_csv.seed`) and on the last line printed. Also `distribuciones.parquet` (`core/study/draws.py`) beside `nulls.csv`: one row per strategy × rung × statistic (`p_<rung>_<stat>`, the 2,500 sorted draws kept raw), written by the population and by `--strategy` (which replaces only its own strategy's rows) | `python3 -m studies.readings.monkey.report --project XAUUSD --databank Results --feed XAUUSD_M1 [--strategy "Strategy 1.17.44"]` · `python3 -m studies.readings.monkey.report --project P --databank "Retest Markets - Family" --timeframe H1 --sample IST` | export → reports |
| `tooltips.py` | One sentence per `config.yaml` knob, for the window's configuration drawer | imported | — |
| `verify.py` | The two checks that must pass before a p is read | `python3 -m studies.readings.monkey.verify --project XAUUSD --databank Results --feed XAUUSD_M1 --strategy "Strategy 1.17.44"` | one strategy → three checks |
