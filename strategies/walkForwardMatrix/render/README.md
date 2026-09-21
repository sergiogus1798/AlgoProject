# walkForwardMatrix/render — how it is read

| file | what it does | in → out |
|---|---|---|
| `text.py` | The whole report as markdown | result → markdown |

The page opens with **what the export allows you to claim** — how many cells, what overlaps what,
that they all re-split the same history — before any correlation appears. That ordering is the
point: a reader who sees rho first will read the interval as a standard error, and it is not one.

Tables are written by hand rather than through `DataFrame.to_markdown`, which pulls in `tabulate`
for one table. This is the **second** study to carry that helper (`strategies/sppUltra/render` has
the other); a third makes it `core/`.
