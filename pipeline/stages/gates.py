"""The hard refusals: what must exist, what must still be true, and how full the disk is."""

import hashlib
import json
from pathlib import Path

from core.assets import load as load_asset, pending
from core.paths import DATA
from perf.disk import budget, inventory
from perf.inputs import config as perf_config
from pipeline.ledger import state


def missing(paths: list[Path]) -> list[Path]:
    """Which of these are not on disk.

    Args:
        paths: Absolute paths.

    Returns:
        The absent ones, in the order given.
    """
    return [p for p in paths if not p.exists()]


def entering(stage: dict) -> None:
    """Refuse to start a stage whose inputs are not there.

    Args:
        stage: A resolved recipe row.

    Raises:
        SystemExit: Naming every missing input. A stage started without its input either
            crashes deep inside someone else's module or, worse, writes a plausible empty
            answer, and a hundred unattended mothers is exactly where that goes unnoticed.
    """
    gone = missing(stage["needs"])
    if gone:
        raise SystemExit(f"{stage['name']}: falta la entrada " +
                         ", ".join(str(p.relative_to(DATA)) for p in gone))


def leaving(stage: dict) -> None:
    """Refuse to call a stage finished when it did not write what it promised.

    Args:
        stage: A resolved recipe row.

    Raises:
        SystemExit: Naming every promised output that is absent.
    """
    gone = missing(stage["produces"])
    if gone:
        raise SystemExit(f"{stage['name']}: terminó sin escribir " +
                         ", ".join(str(p.relative_to(DATA)) for p in gone))


def done(ledger: dict, stage: dict) -> bool:
    """Whether this stage can be skipped on a rerun.

    Args:
        ledger: The state.json contents.
        stage: A resolved recipe row.

    Returns:
        True when the ledger recorded a completion *and* the outputs are still on disk.
        Both halves are needed: the ledger outlives the data it describes, so a mother
        whose variants were swept would otherwise be read as one still holding them.
        A row marked `recompute` is never done -- that is how a changed verdict threshold
        re-judges without re-running anything that costs machine time.
    """
    if stage.get("recompute"):
        return False
    return state.is_done(ledger, stage["name"]) and not missing(stage["produces"])


def disk() -> dict:
    """What the data root weighs against the budgets perf/disk owns.

    Returns:
        The whole-root verdict plus the branches that broke their own ceiling. The budget
        is what has to stop a multi-day run: a full disk stops it too, but by then the
        stage that was writing has already left half a file behind.
    """
    cfg = perf_config.load()
    tree = inventory.tree(cfg)
    return {"total": budget.total(tree, cfg), "over": budget.failed(budget.judge(tree, cfg))}


def room(stop: bool) -> None:
    """Refuse to start another mother when the data root is already over budget.

    Args:
        stop: The `run.stop_over_budget` setting.

    Raises:
        SystemExit: Naming the total and every branch over its ceiling.
    """
    if not stop:
        return
    found = disk()
    if not found["total"]["over"] and not found["over"]:
        return
    branches = ", ".join(f"{r['branch']} {r['gb']:.1f}/{r['budget_gb']} GB"
                         for r in found["over"])
    raise SystemExit(f"AlgoData {found['total']['gb']:.1f} GB de "
                     f"{found['total']['budget_gb']} GB. {branches or 'total excedido'}. "
                     "Libera espacio o sube el presupuesto en perf/config.yaml.")


def costs(asset: str) -> None:
    """Refuse to start when the asset's trading costs have never been agreed.

    Args:
        asset: Asset name as assets/<asset>.yaml is called.

    Raises:
        SystemExit: A required override still has no value, which is the same condition
            `python3 -m core.assets <SYMBOL>` exits non-zero on. Days of unattended
            machine spent on backtests priced with nothing at all is the failure this
            costs one file read to prevent. A *provisional* value is not blocking: it is
            a decision the owner has made and stamped, and the ledger carries the stamp.
    """
    undecided = pending(load_asset(asset))
    if undecided:
        raise SystemExit(f"assets/{asset}.yaml: {', '.join(undecided)} sin valor acordado. "
                         f"Corre `python3 -m core.assets {asset}` y pregúntale al dueño.")


def unchanged(ledger: dict, stage: dict) -> None:
    """Refuse to continue when a file this stage fingerprinted is no longer that file.

    Args:
        ledger: The state.json contents.
        stage: A resolved recipe row.

    Raises:
        SystemExit: The recorded hash and the file on disk disagree. For `brief_hash`
            that means the design changed after the variants were built, so every stage
            after it is measuring one design against the numbers of another -- a failure
            that produces plausible results rather than an error, which is why it is a
            refusal and not a warning.
    """
    entry = ledger["stages"].get(stage["name"], {})
    for field, path in stage["hash"].items():
        before = entry.get(field)
        if before and path.exists():
            now = hashlib.sha256(path.read_bytes()).hexdigest()
            if now != before:
                raise SystemExit(
                    f"{stage['name']}: {path.name} ha cambiado desde que se registró "
                    f"({field} {before[:12]}… -> {now[:12]}…). Lo que viene después ya no "
                    f"corresponde a este diseño: borra la carpeta de la estrategia en "
                    f"AlgoData/pipeline/ para rehacerla, o recupera el fichero anterior.")


def must(stage: dict) -> None:
    """Refuse to advance past a stage whose own output says the experiment is invalid.

    Args:
        stage: A resolved recipe row.

    Raises:
        SystemExit: A `must` rule of the row was broken. These are gates, not thresholds:
            a failed canary does not mean the strategy is bad, it means the variants SQX
            ran are not the variants that were written, and nothing measured afterwards
            means anything. A threshold belongs in config.yaml and produces a verdict; a
            gate belongs here and stops the run.
    """
    if not stage["must"]:
        return
    got = json.loads(stage["record_from"].read_text(encoding="utf-8"))
    for rule in stage["must"]:
        value = got[rule["number"]]
        low, high = rule.get("min"), rule.get("max")
        if (low is not None and value < low) or (high is not None and value > high):
            raise SystemExit(f"{stage['name']}: {rule['number']} = {value}. {rule['why']}")
