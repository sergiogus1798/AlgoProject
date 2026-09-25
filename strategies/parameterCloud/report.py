#!/usr/bin/env python3
"""The command: where the chosen point sits in its own cloud, and whether the cloud holds up."""

import argparse
import json
from pathlib import Path

from core.study import output
from core.study.render import markdown
from strategies.parameterCloud import one
from strategies.parameterCloud.inputs.config import config


def main() -> None:
    """Read one fabricated batch as a cloud, print what it says, and write it into the batch."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", required=True, type=Path,
                    help="batch directory: metrics.parquet and equity.parquet")
    ap.add_argument("--out", type=Path, help="also write every number here as JSON")
    ap.add_argument("--set", dest="overrides", action="extend", nargs="+", default=[])
    a = ap.parse_args()

    got = one.run(a.work, config(a.overrides))
    title = f"Nube de parámetros — {got['strategy']}"
    lede = ("Diagnóstico, nunca selección: ninguna lectura sustituye el punto elegido por un "
            "clon mejor. Eso lo decide el dueño, y se revalida aparte.")
    print(markdown.render(got, title))
    output.population(a.work / "estudios", "cloud", got, title, lede)
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(got["summary"], indent=1), encoding="utf-8")
    print(f"-> {a.work / 'estudios' / 'cloud.html'}")


if __name__ == "__main__":
    main()
