"""Measure every target, append it to the catalogue, and say what got worse since last time."""

import argparse
import sys

import pandas as pd

from perf import store, verdict
from perf.inputs import config
from perf.inputs.targets import TARGETS, resolve
from perf.measure import harness, hotspots, scaling

SCALING = "scaling.csv"


def measure(names: list[str] | None, cfg: dict, overrides: list[str]) -> list[dict]:
    """Run the chosen targets and build their catalogue rows.

    Args:
        names: Target or area names, or None for all of them.
        cfg: What config.load() returned.
        overrides: Config overrides handed to each target's own process.

    Returns:
        One row per target, ready to append. Each row carries the commit, the machine's load
        and the simulation budget: without them a measurement cannot be compared with
        another, and `--set sample.n_sims=...` changes the work without changing the scale.
    """
    rows = []
    for name in resolve(names):
        print(f"  {name} ...", flush=True)
        run = harness.repeat(name, cfg, overrides)
        rows.append({"target": name, "area": TARGETS[name]["area"], "unit": TARGETS[name]["unit"],
                     "budget": cfg["sample"]["n_sims"], "commit": store.commit()}
                    | store.stamp() | store.context()
                    | {k: v for k, v in run.items() if k != "alloc_top"})
    return rows


def table(judged: pd.DataFrame) -> str:
    """The comparison as the owner reads it.

    Args:
        judged: What verdict.compare() returned.

    Returns:
        One line per target: time now, change against the previous measurement, change in
        peak memory, and the verdict.
    """
    head = f"{'target':<22}{'ahora':>10}{'antes':>10}{'tiempo':>9}{'memoria':>9}  veredicto"
    def before(value: float) -> str:
        """The previous time, or a dash when there was none."""
        return f"{value:>9.2f}s" if value == value else f"{'—':>10}"

    lines = [f"{r.target:<22}{r.wall_s:>9.2f}s{before(r.prev_wall_s)}"
             f"{r.wall_pct:>8.1f}%{r.rss_pct:>8.1f}%  {r.verdict}"
             for r in judged.itertuples()]
    return "\n".join([head] + lines)


def main() -> None:
    """Measure, store, judge, and exit non-zero if anything regressed."""
    ap = argparse.ArgumentParser(description="Measure the project's speed and memory.")
    ap.add_argument("--only", nargs="*", help="target or area names; all of them by default")
    ap.add_argument("--scaling", action="store_true", help="also re-measure the machine's ceiling")
    ap.add_argument("--hotspots", help="profile one target instead of measuring all of them")
    ap.add_argument("--set", action="append", default=[], help="config override, dotted.key=value")
    a = ap.parse_args()
    cfg = config.load(a.set)
    if a.hotspots:
        print(hotspots.text(hotspots.profile(a.hotspots, cfg)))
        return
    print(f"midiendo en {store.commit()}")
    store.append(measure(a.only, cfg, a.set))
    if a.scaling:
        found = scaling.machine(cfg)
        store.append([r | {"kind": k} | store.stamp() for k in ("cache", "dram")
                      for r in found[k]], SCALING)
    judged = verdict.compare(store.history(), cfg)
    print(table(judged))
    failed = verdict.failing(judged)
    print(f"\n{len(failed)} regresiones" if len(failed) else "\nsin regresiones")
    sys.exit(1 if len(failed) else 0)


if __name__ == "__main__":
    main()
