# studies/readings/entryQuality — does the entry carry information, or would any entry do?

One study, one folder. It walks the bars forward from every entry and answers two questions that
never touch the strategy's own exits:

| | the question | the PDF's item |
|---|---|---|
| **e-ratio** | did price run further in favour than against, more than a random entry at the same hours would have? | 3 |
| **retraso** | how much of the edge is given up by entering d bars late? | 4, tier 1 |

They share one kernel — the forward path from an entry — which is why they are one folder.

| file | what it does | run it | in → out |
|---|---|---|---|
| `report.py` | **The command**: one strategy's two readings, printed and written to `reports/<P>/<D>/<export day>/entryQuality/estrategias/` | `python3 -m studies.readings.entryQuality.report --export <trades.parquet> --strategy "Strategy 35.44.31"` | trades + bars → two readings |
| `one.py` | The measurements — the e-ratio against its band, per side, and the two delay tables — as the contract's data the window paints | imported — the window calls it | trades + bars → result |
| `contract.py` | The two tabs, each with its reading, and the glossary | imported | numbers → tabs |
| `tooltips.py` | One sentence per `config.yaml` knob, for the window's configuration drawer | imported | — |
| `inputs.py` | The knobs, the trades placed on the bar grid, the ATR, the cost and which trades have a full path | imported | export → located trades |
| `excursion.py` | MFE and MAE at every horizon, and the same in units of the entry's own volatility | imported | bars → paths |
| `eratio.py` | e(k), the matched random benchmark and its 5-95% band | imported | paths → curve, band |
| `delay.py` | The price given up by a late entry, and what it is worth against the edge and the costs | imported | bars → delay tables |
| `verdict.py` | What the two curves mean | imported | numbers → readings |
| `config.yaml` | Every tunable, grouped by the layer that reads it; a `ledger:<key>` value is a threshold whose number lives in `ledger/thresholds.yaml` | edited, or `--set section.key=value` | — |

Manual page, in Spanish: `docs/manual/42-calidad-de-la-entrada.md`.

## Five decisions, and each one moves the answer

**The walk starts at the bar after the entry.** The entry bar's own high and low are partly before
the fill, so counting them credits the entry with a move it could not have caught.

**The ATR is read at the bar before the entry**, for the same reason: the entry bar's range is
information the entry did not have, and it is the scale every excursion is divided by.

**Excursions come off highs and lows, not closes.** A close-based excursion understates both, and
understates the adverse one most — which is the one a stop would have hit.

**e(k) is a ratio of means, not a mean of ratios.** The second is dominated by the trades whose
adverse excursion was near zero, and those are the ones that say least.

**The benchmark is matched on the hour of day and on the long/short split.** Random entries are
drawn hour by hour in the real proportions, and the real sides are shuffled rather than redrawn.
Without the first, the band is partly a statement about the session the strategy trades in; without
the second, a long-only strategy in a rising market beats any band by being long.

## What tier 1 assumes, and when it is wrong

The delay table holds the exits where they were. That is approximately right for signal and
bar-count exits, and **wrong for a stop or a target**, which move with the entry price. The XAUUSD
population carries none of those (`studies/CLAUDE.md`), which is what makes tier 1 readable here
and will stop being true. Tier 2 — the replay simulator — is
`docs/encargos/16-replay-de-operaciones.md`.

⚠️ **The delay cost is expressed against total modelled cost, not against the spread.** The PDF asks
for spread units; on this install the spread is inside the fill prices and does not appear in the
`gross - net` residual (`knowhow/costs/where-the-spread-is.md`), so the spread alone is not recoverable per trade.
Reading the ratio as spreads would overstate the delay's severity.

## What it does not tell you

- **Nothing about the exits.** That is the point: it isolates the entry. A strategy can read
  `no_signal` here and still be profitable — and then its profit comes from the exit structure or
  from drift, which is a different object to own.
- **Nothing causal about a high DCR.** A large cost of one bar's delay is either latency fragility
  or lookahead in the signal, and this test cannot separate them.
