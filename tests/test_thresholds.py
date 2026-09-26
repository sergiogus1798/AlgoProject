#!/usr/bin/env python3
"""A migrated threshold reaches its module from ledger/thresholds.yaml and from nowhere else."""

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.paths import ROOT
from ledger import thresholds

# Every threshold these modules' config.yaml points at must be read through the ledger.
# A module joins the list the commit it is migrated; it never leaves it.
MIGRATED = ("studies/screening/gate/", "studies/screening/snoopingScreen/")


def reader(source: str) -> object:
    """The config() of the module whose config.yaml a `source` pointer names.

    Args:
        source: `studies/<family>/<module>/config.yaml#...`.

    Returns:
        The function the module, the window and the reports all read their knobs through.
    """
    folder = Path(source.split("#", 1)[0]).parent
    dotted = ".".join(folder.parts)
    split = (ROOT / folder / "inputs" / "config.py").exists()
    return importlib.import_module(f"{dotted}.inputs{'.config' if split else ''}").config


def main() -> None:
    """Swap every declared value for a sentinel and check each migrated module sees it."""
    failures = []
    rows = thresholds.declared()
    sentinel = {r["key"]: 1000.0 + i for i, r in enumerate(rows)}
    real = thresholds.value
    thresholds.value = sentinel.__getitem__
    try:
        for r in rows:
            if not r["source"].startswith(MIGRATED):
                continue
            seen = thresholds.walk(reader(r["source"])([]), r["source"].split("#", 1)[1])
            if seen != sentinel[r["key"]]:
                failures.append(f"{r['key']}: el módulo lee {seen!r}, no el valor del ledger")
    finally:
        thresholds.value = real

    real_declared = thresholds.declared
    for fake, why in (([], "ausente"), ([{"key": "k", "value": 1}] * 2, "duplicada")):
        thresholds.declared = lambda fake=fake: fake
        try:
            thresholds.value("k")
            failures.append(f"una clave {why} no hace fallar la lectura")
        except KeyError:
            pass
    thresholds.declared = real_declared

    table = thresholds.divergences()
    if not table["coincide"].all():
        failures.append("--check-thresholds encuentra divergencias")
    migrated = int((table["lee_de"] == "ledger").sum())
    print("\n".join(failures) or
          f"ok: {migrated} de {len(table)} umbrales llegan del ledger y de ningún otro sitio; "
          "una clave ausente o duplicada hace fallar la lectura")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
