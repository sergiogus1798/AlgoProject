#!/usr/bin/env python3
"""The command: which parameters move a mother's excess across her variant batch, and whether the ranking can be read."""

import argparse
import json
from pathlib import Path

from core.study import draws, output
from core.study.render import markdown
from studies.optimisation.cloud import one
from studies.optimisation.cloud.inputs.config import config


def main() -> None:
    """Read one retested batch as a map, print what it says, and write it into the batch."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--work",
        required=True,
        type=Path,
        help="batch directory, with its variant_trades.parquet",
    )
    ap.add_argument("--out", type=Path, help="also write every number here as JSON")
    ap.add_argument("--set", dest="overrides", action="extend", nargs="+", default=[])
    a = ap.parse_args()

    got = one.run(a.work, config(a.overrides))
    title = f"Nube de parámetros — {got['strategy']}"
    lede = (
        "Diagnóstico, nunca selección: el mapa no tiene regla, no corta nada y no "
        "sustituye a la madre por una variante mejor."
    )
    print(markdown.render(got, title))
    rows = got.pop("draws")
    output.population(a.work / "estudios", "cloud", got, title, lede)
    draws.save(a.work / "estudios", rows)
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(got["summary"], indent=1), encoding="utf-8")
    print(f"-> {a.work / 'estudios' / 'cloud.html'}")


if __name__ == "__main__":
    main()
