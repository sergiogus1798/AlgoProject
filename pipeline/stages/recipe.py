"""The stage registry: recipe.yaml read into concrete commands, gates and output paths."""

from pathlib import Path

import yaml

from core.paths import DATA, report_dir
from pipeline.ledger import state

HERE = Path(__file__).resolve().parent.parent
RECIPE = HERE / "recipe.yaml"
CONFIG = HERE / "config.yaml"


def settings() -> dict:
    """The pipeline's own tunables.

    Returns:
        The parsed config.yaml, unmodified.
    """
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def stages() -> list[dict]:
    """The recipe as written, in order.

    Returns:
        The rows of recipe.yaml. Still full of placeholders -- `resolve` turns one row
        into something runnable for one strategy. The daemon that replaces the CLI reads
        this same list, which is why the stages are data and not functions.
    """
    return yaml.safe_load(RECIPE.read_text(encoding="utf-8"))["stages"]


def context(project: str, databank: str, strategy: str, day: str) -> dict:
    """Every placeholder a recipe row can use, for one mother strategy.

    Args:
        project: Project name on the master.
        databank: Databank the SPP export came from, underscores not spaces.
        strategy: Name as SQX shows it.
        day: Report date as YYYY-MM-DD.

    Returns:
        The substitution table. `work` and `reports` are absolute because commands receive
        them as arguments; the shorter paths stay relative and land under the data root.
    """
    work = state.work_dir(project, strategy)
    return {"project": project, "databank": databank, "strategy": strategy,
            "safe": state.safe(strategy), "day": day, "work": str(work),
            "reports": str(report_dir(project, databank, day)),
            # 0 means "the whole design": --sample 0 is falsy to the factory, which then
            # fabricates every planned row rather than a slice of them.
            "sample": settings()["run"]["sample"],
            # The mother the SPP reconnoitres. Frozen copies, not the live databank: SQX
            # rewrites what it holds, so a run started today and resumed tomorrow would
            # otherwise be reconnoitring a different file under the same name.
            "mother": str(DATA / settings()["run"]["mothers"] / f"{strategy}.sqx")}


def resolve(stage: dict, ctx: dict) -> dict:
    """One recipe row, filled in for one strategy.

    Args:
        stage: A row of `stages()`.
        ctx: What `context()` returned.

    Returns:
        The same row with `command` as an argument list and `needs` and `produces` as
        paths. The command template is split on whitespace *before* the placeholders are
        filled, so a strategy name with spaces stays a single argument instead of becoming
        three -- the same trap that forces SQX project names to use underscores.
    """
    default = f"{{work}}/{stage['name']}.json"
    return stage | {
        "command": [token.format(**ctx) for token in stage["command"].split()],
        "needs": [DATA / p.format(**ctx) for p in stage["needs"]],
        "produces": [DATA / p.format(**ctx) for p in stage["produces"]],
        "record_from": DATA / stage.get("record_from", default).format(**ctx),
        "hash": {field: DATA / p.format(**ctx)
                 for field, p in stage.get("hash", {}).items()},
        "must": stage.get("must", [])}
