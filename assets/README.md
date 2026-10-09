# assets — per-instrument cost and window cards

SQX's own spread, commission and swap for an instrument are often not what the broker charges, and
that decides whether a backtest is honest. This folder records the real values, per instrument, and
every project is configured from it. Authoring is blocked until the card says what to use.

## What is here

| path | holds |
|---|---|
| `symbols/<SYMBOL>.yaml` | One card per instrument (27 today; `symbols/_retired/` for dropped ones): class, broker, SQX symbol and feeds, trading session, instrument facts, costs (spread, commission, swaps — each with `use`, the value in force, `sqx_now`, and `why`), Monte Carlo retest ranges, MT5 symbol names and point conversion |
| `_classes.yaml`, `_policy.yaml`, `_markets.yaml`, `_build.yaml`, `_study.yaml`, `_aliases.yaml`, `_feed_renames.yaml` | Seven shared files: cost schemes per class, the three data windows, the markets an edge is retested on, build/study defaults, name aliases |
| `RULES.md` | The doctrine: why the preflight blocks, what a null (`use: null`) means, how costs are chosen |
| `INDEX.md` | Generated table of all cards and what is still undecided (`python3 -m core.assets --index`) |

Data windows are three time segments per instrument — `build` (the only sample the generator sees),
`oos1` (retests, Monte Carlo, cross-market) and `oos2` (the last held-out stretch) — defined in
`_policy.yaml`, each with its own spread and slippage. The cards are written in Spanish.

## Read a card

```bash
python3 -m core.assets <SYMBOL>    # preflight: prints the overrides applied, exits non-zero if blocked
```

Cards are edited from the desktop window, through `core.assetwrite`, which keeps the comments.
