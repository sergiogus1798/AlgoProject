# walkForwardMatrix/verdict — what it means

| file | what it does | in → out |
|---|---|---|
| `call.py` | Three outcomes from the pooled interval, and the paragraph a human reads first | pooled, drift → verdict, sentence |

- **`predicts`** — the interval sits above zero. Re-optimising picks configurations that go on to do
  better, which is what walk-forward optimisation assumes it does.
- **`blind`** — the interval straddles zero. The in-sample ranking carries no information about what
  follows. Re-optimising is not harmful, it is pointless, and its cost is real.
- **`perverse`** — the interval sits **below** zero. What optimises better goes on to do worse. The
  procedure is not merely uninformative, it is selecting for what will fail, and more history does
  not fix it.

`blind` is the wide middle and it is deliberately wide: `zero_band` is 0.0, so a correlation is only
called either way when its interval clears zero entirely. At 30 cells drawn from one history, that
is already a generous standard.

A verdict is always printed with the same correlation on the companion metrics. One that holds only
on the metric it was read on is a property of that metric.
