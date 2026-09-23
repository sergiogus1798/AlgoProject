"""One strategy against its monkeys, readable: where it landed, and where its edge came from."""

import argparse

import numpy as np

from nulls import inputs, simulate, verdict
from nulls.report import newest

BARS = 30           # rows of the text histogram
WIDTH = 46          # its widest bar, in characters


def table(seen: dict, drawn: dict, names: list[str]) -> list[str]:
    """Each statistic against the null distribution of the headline rung.

    Args:
        seen: What simulate.real() returned.
        drawn: The headline rung's null statistics.
        names: statistics.report.

    Returns:
        One line per statistic: what the strategy did, what the average monkey did, the
        monkey's 95th percentile, the strategy's own percentile among them, and the p.
        Five statistics and no composite, because which of them matters is the owner's
        call -- and because they disagree by up to 45 points of the population.
    """
    head = (f"{'':>8} {'tu estrategia':>15} {'mono medio':>13} {'mono p95':>12} "
            f"{'percentil':>10} {'p':>8}")
    rows = [head, "-" * len(head)]
    for name in names:
        null = drawn[name]
        found = verdict.pvalue(seen[name], null, name)
        rows.append(f"{name:>8} {seen[name]:>15,.2f} {null.mean():>13,.2f} "
                    f"{np.percentile(null, 95):>12,.2f} {100 * (null < seen[name]).mean():>9.1f}% "
                    f"{found:>8.4f}{'  <--' if found < 0.05 else ''}")
    return rows


def channels(seen: dict, per_rung: dict, name: str) -> list[str]:
    """Where the margin over the loosest monkey came from.

    Args:
        seen: What simulate.real() returned.
        per_rung: Rung name to the null statistics it produced.
        name: Which statistic to decompose.

    Returns:
        One line per channel. The remainder is the entry timing itself: it is what is left
        after the channels that CAN be handed to chance have been, not a separately measured
        quantity, and the report says so rather than printing it as though it were one.
    """
    got = verdict.attribute(seen, per_rung, name)
    rest = got["total"] - got["holding_time"] - got["sizing"]
    return [f"  ventaja total sobre el mono suelto .... {got['total']:>14,.2f}",
            f"  de cuanto aguanta la posicion ......... {got['holding_time']:>14,.2f}",
            f"  del tamano por volatilidad ............ {got['sizing']:>14,.2f}",
            f"  resto, que es el momento de entrar .... {rest:>14,.2f}"]


def histogram(null: np.ndarray, seen: float, unit: str) -> list[str]:
    """The null distribution drawn in text, with the real run marked in it.

    Args:
        null: The statistic over every null run.
        seen: The real run's value.
        unit: What the axis is counted in, for the caption.

    Returns:
        One line per bin. This is the picture the whole study is about -- thousands of
        random runs, and where the real one fell among them -- and it is text so that it
        survives a terminal, a log and a paste into a report.
    """
    edges = np.linspace(min(null.min(), seen), max(null.max(), seen), BARS + 1)
    counts, _ = np.histogram(null, edges)
    here = int(np.clip(np.searchsorted(edges, seen) - 1, 0, BARS - 1))
    lines = [f"  distribucion de {len(null):,} monos, en {unit}:", ""]
    for i, count in enumerate(counts):
        mark = "  TU >>>" if i == here else "        "
        lines.append(f"{mark} {edges[i]:>12,.0f} {'#' * int(WIDTH * count / counts.max())}")
    return lines


def main() -> None:
    """Run one strategy against its monkeys and print the three readings."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True)
    ap.add_argument("--feed", required=True, help="SQX feed name, e.g. XAUUSD_DukasM1_Infinox")
    ap.add_argument("--strategy", required=True)
    ap.add_argument("--timeframe", default="M30")
    ap.add_argument("--sample", default="OOS1", help="IST in sample, OOS1 out of it")
    ap.add_argument("--statistic", default="net", help="which one the histogram and channels use")
    ap.add_argument("--set", action="append", default=[], help="section.key=value")
    a = ap.parse_args()

    cfg = inputs.config(a.set)
    trades = inputs.sample(newest(a.project, a.databank), a.strategy, a.sample)
    kept = simulate.fixed(trades, inputs.bars(a.feed, a.timeframe), cfg)
    names = cfg["statistics"]["report"]
    seen = simulate.real(kept, names)
    per_rung = {rung: simulate.nulls(kept, rung, cfg) for rung in cfg["nulls"]["rungs"]}

    print(f"\n{a.strategy}   {len(trades)} operaciones   muestra {a.sample}   "
          f"{cfg['nulls']['draws']:,} monos por peldano")
    print(f"reconciliacion {kept['checks']['corr']:.6f}  (relleno {kept['checks']['fill']}, "
          f"segunda convencion {kept['checks']['runner_up']:.4f})\n")
    print("\n".join(table(seen, per_rung[cfg["nulls"]["headline"]], names)))
    print(f"\nde donde sale la ventaja, medida en '{a.statistic}':")
    print("\n".join(channels(seen, per_rung, a.statistic)))
    print()
    print("\n".join(histogram(per_rung["free"][a.statistic], seen[a.statistic], a.statistic)))
    print()
    for line in verdict.distrust(kept, {n: verdict.pvalue(seen[n],
                                                          per_rung[cfg["nulls"]["headline"]][n], n)
                                        for n in names}, len(trades), cfg):
        print(f"  ! {line}")


if __name__ == "__main__":
    main()
