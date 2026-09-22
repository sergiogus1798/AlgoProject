#!/usr/bin/env python3
"""The two proofs this is a pipeline: progress streams and is monotonic, and a kill resumes."""

import argparse
import sys

from pipeline.stages import execute, recipe
from pipeline.verify import fixture, monotonic, resume

MARKER = "PROGRESS"
LONG = ["--seconds", "8"]          # long enough for the parent to kill it halfway


def drive(name: str) -> None:
    """Run one stage of the fixture to completion. Used as the child the resume test kills.

    Args:
        name: Stage name.
    """
    ctx = recipe.context(fixture.PROJECT, fixture.DATABANK, fixture.STRATEGY, fixture.DAY)
    stage, = [s for s in fixture.chain(ctx) if s["name"] == name]
    execute.run(stage | {"command": stage["command"] + LONG}, fixture.work(), MARKER)


def main() -> None:
    """Run both proofs against a throwaway fixture and exit non-zero if either fails."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--drive-stage", help="uso interno: corre una etapa para que la maten")
    ap.add_argument("--keep", action="store_true", help="no borra el fixture al terminar")
    args = ap.parse_args()
    if args.drive_stage:
        drive(args.drive_stage)
        return

    print("## monotonía del progreso")
    problems = monotonic.check(fixture.build())
    print("## interrumpir y reanudar")
    problems += resume.check(fixture.build())

    if not args.keep:
        fixture.remove()
    for line in problems:
        print(f"  {line}")
    print(f"\n{len(problems)} problemas")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
