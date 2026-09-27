"""One stored result with its staleness, and every run of a study on a databank or a strategy."""

from pathlib import Path

from ui.daemon.results import knobs, store


def _path(project: str, databank: str, study: str, day: str, strategy: str) -> Path:
    """Where one result lives.

    Args:
        project: SQX project name.
        databank: Databank name.
        study: Study key.
        day: Report day.
        strategy: Strategy name, "" for the population result.

    Returns:
        `<study>.json` or `estrategias/<name>.json`; names carry dots, so the suffix is
        appended, never swapped (as `core.study.output.member` writes it).
    """
    folder = store.bank(project, databank) / day / study
    return folder / "estrategias" / f"{strategy}.json" if strategy else folder / f"{study}.json"


def _identity(result: dict, folder: Path) -> str | None:
    """The identity a stored result belongs to.

    Args:
        result: A contract result, or its slim row.
        folder: Its study folder.

    Returns:
        The result's own identity, else the one its run's verdict.csv gave the same name —
        some studies (wfm) sign the JSON without it. None when neither carries one.
    """
    row = (store.verdicts(folder) or {}).get(result["strategy"] or "", {})
    return result["identity"] or row.get("identity")


def _mismatch(result: dict, folder: Path, identity: str) -> str | None:
    """Why a result found by name is not the strategy asked for, if it is not.

    Args:
        result: A contract result, or its slim row.
        folder: Its study folder.
        identity: The identity asked for, "" when the caller gave none.

    Returns:
        The reason in Spanish, or None when it matches or nothing was asked.
    """
    if not identity:
        return None
    got = _identity(result, folder)
    if got is None:
        return "el resultado no guarda identidad: no se puede emparejar"
    return None if got == identity else "otra estrategia con el mismo nombre (identidad distinta)"


def result(project: str, databank: str, study: str, strategy: str, identity: str,
           day: str) -> dict:
    """The newest contract result of a study, for the population or for one strategy.

    Args:
        project: SQX project name.
        databank: Databank name.
        study: Study key.
        strategy: Strategy name, "" for the population result.
        identity: The strategy's identity, "" to trust the name.
        day: A report day, "" for the newest that holds a contract result.

    Returns:
        `result` (the contract dict or None) and `meta`: day, path, config_hash,
        current_hash, stale, computed_at, and `skipped` — the newer days passed over, each
        with its reason.
    """
    current = knobs.signed(study, [])
    skipped = []
    for d in [day] if day else store.days(project, databank, study):
        path = _path(project, databank, study, d, strategy)
        got, why = store.load(path)
        why = why or _mismatch(got, path.parent.parent if strategy else path.parent, identity)
        if why:
            skipped.append({"day": d, "reason": why})
            continue
        return {"result": got, "meta": {
            "day": d, "path": str(path), "config_hash": got["config_hash"],
            "current_hash": current,
            "stale": current is not None and got["config_hash"] != current,
            "computed_at": got.get("computed_at"), "skipped": skipped}}
    return {"result": None, "meta": {"day": None, "path": None, "config_hash": None,
                                     "current_hash": current, "stale": False,
                                     "computed_at": None, "skipped": skipped}}


def history(project: str, databank: str, study: str, strategy: str, identity: str) -> dict:
    """Every day a study left a contract result for the population or one strategy.

    Args:
        project: SQX project name.
        databank: Databank name.
        study: Study key.
        strategy: Strategy name, "" for the population.
        identity: The strategy's identity, "" to trust the name.

    Returns:
        `runs` newest first — day, config_hash, computed_at, state, label, stale — and
        `skipped`, the days with a report that is not a contract result or not this
        strategy, each with its reason.
    """
    current = knobs.signed(study, [])
    runs, skipped = [], []
    for d in store.days(project, databank, study):
        path = _path(project, databank, study, d, strategy)
        row = store.slim(path) if path.is_file() else None
        why = (store.load(path)[1] if row is None
               else _mismatch(row, path.parent.parent if strategy else path.parent, identity))
        if why:
            skipped.append({"day": d, "reason": why})
            continue
        runs.append({"day": d, "config_hash": row["config_hash"],
                     "computed_at": row["computed_at"], "state": row["state"],
                     "label": row["label"],
                     "stale": current is not None and row["config_hash"] != current})
    return {"runs": runs, "skipped": skipped}
