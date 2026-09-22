#!/usr/bin/env python3
"""The last stage: judge one mother against the thresholds, from numbers already on disk."""

import argparse
import json
from pathlib import Path

from pipeline.stages import recipe

PROCEED, REJECT = "proceed", "reject"
SKIP = {"state.json", "verdict.json"}


def numbers(work: Path, brief: Path) -> dict:
    """Every figure the earlier stages left, under one flat namespace.

    Args:
        work: The strategy's work directory.
        brief: Path of the design_brief.json sppUltra wrote.

    Returns:
        Keys of the form "<source>.<field>": `brief.n_eff`, `wfc.rho`, and so on, one
        source per JSON file in the work directory. Only scalars are kept -- a threshold
        is a comparison against a number, and anything else in those files belongs to the
        stage that wrote it.
    """
    found = {}
    for path in [brief] + sorted(work.glob("*.json")):
        if path.name in SKIP:
            continue
        source = "brief" if path == brief else path.stem
        got = json.loads(path.read_text(encoding="utf-8"))
        found |= {f"{source}.{k}": v for k, v in got.items()
                  if isinstance(v, (int, float)) and not isinstance(v, bool)}
    return found


def judge(found: dict, rules: list[dict]) -> list[dict]:
    """Which thresholds this mother failed.

    Args:
        found: What `numbers()` returned.
        rules: The `verdict.rules` block of config.yaml.

    Returns:
        One row per broken rule, with the value, the limit and the reason the threshold
        exists. A rule naming a number nothing produced raises instead of passing: a
        threshold silently skipped is a strategy silently approved.
    """
    broken = []
    for rule in rules:
        value = found[rule["number"]]
        low, high = rule.get("min"), rule.get("max")
        if (low is not None and value < low) or (high is not None and value > high):
            broken.append({"number": rule["number"], "value": value,
                           "limit": low if low is not None else high,
                           "bound": "min" if low is not None else "max",
                           "why": rule["why"]})
    return broken


def main() -> None:
    """Write verdict.json for one mother strategy."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", required=True, type=Path)
    ap.add_argument("--brief", required=True, type=Path)
    args = ap.parse_args()

    rules = recipe.settings()["verdict"]["rules"]
    print(f"PROGRESS 20 leyendo los números de {len(rules)} umbrales")
    found = numbers(args.work, args.brief)
    print(f"PROGRESS 60 {len(found)} cifras reunidas")
    broken = judge(found, rules)
    verdict = REJECT if broken else PROCEED

    (args.work / "verdict.json").write_text(json.dumps(
        {"verdict": verdict, "failed": broken, "numbers": found},
        indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"PROGRESS 100 {verdict}" + (f", falla {broken[0]['number']}" if broken else ""))


if __name__ == "__main__":
    main()
