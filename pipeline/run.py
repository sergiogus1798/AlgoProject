#!/usr/bin/env python3
"""Chain every stage over every mother strategy, resumable, with the ledger as the record."""

import argparse
from datetime import date

from pipeline import cleanup
from pipeline.ledger import state
from pipeline.stages import execute, gates, recipe
from strategies.sppUltra.inputs import config as spp_config, export


def mothers(project: str, databank: str, day: str | None, named: list[str] | None) -> list[str]:
    """Which strategies this run walks through.

    Args:
        project: Project name on the master.
        databank: Databank the SPP export came from, underscores not spaces.
        day: Export date, or None for the most recent.
        named: Explicit strategy names, or None.

    Returns:
        The names given, or every strategy in the SPP export. The export is the owner's
        own statement of which strategies are mothers, so nothing here maintains a second
        list that could disagree with it.
    """
    return named or export.strategies(spp_config.export(project, databank, day))


def one(strategy: str, args: argparse.Namespace, settings: dict) -> str:
    """Take one mother through the recipe, skipping what an earlier run finished.

    Args:
        strategy: Name as SQX shows it.
        args: The parsed command line.
        settings: The parsed config.yaml.

    Returns:
        The name of the last stage that completed.
    """
    work = state.work_dir(args.project, strategy)
    state.open_run(work, strategy, args.project, args.databank, args.asset)
    ctx = recipe.context(args.project, args.databank, strategy, args.report_day)

    for row in recipe.stages():
        stage = recipe.resolve(row, ctx)
        gates.unchanged(state.read(work), stage)
        if gates.done(state.read(work), stage):
            print(f"  {stage['name']:<10} hecho, se salta")
            continue
        print(f"  {stage['name']:<10} {' '.join(stage['command'])}")
        gates.entering(stage)
        execute.run(stage, work, settings["run"]["protocol"])
        gates.leaving(stage)
        gates.must(stage)
    return state.read(work)["stage"]


def main() -> None:
    """Run the pipeline over one project's mother strategies."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", default="SPP_IS",
                    help="carpeta del export, con guiones bajos en vez de espacios")
    ap.add_argument("--strategy", action="append",
                    help="repetible; por defecto, todas las del export")
    ap.add_argument("--day", help="fecha del export; por defecto, la más reciente")
    ap.add_argument("--report-day", default=date.today().isoformat(),
                    help="fecha de la carpeta de informes que sppUltra escribe")
    ap.add_argument("--asset", help="nombre en assets/; por defecto, el del proyecto")
    ap.add_argument("--sweep", action="store_true",
                    help="borra los datos de variantes al terminar cada madre")
    args = ap.parse_args()
    args.asset = args.asset or args.project

    settings = recipe.settings()
    gates.costs(args.asset)
    names = mothers(args.project, args.databank, args.day, args.strategy)
    print(f"{len(names)} estrategias madre en {args.project}/{args.databank}\n")

    for n, strategy in enumerate(names, 1):
        print(f"[{n}/{len(names)}] {strategy}")
        gates.room(settings["run"]["stop_over_budget"])
        last = one(strategy, args, settings)
        if args.sweep:
            freed = cleanup.sweep(state.work_dir(args.project, strategy), True)
            print(f"  barrido     {sum(r['bytes'] for r in freed):,d} B en {len(freed)} rutas")
        print(f"  -> {last}\n")


if __name__ == "__main__":
    main()
