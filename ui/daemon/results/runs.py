"""One stored result with its staleness, and every run of a study on a databank or a strategy."""

from pathlib import Path

from ui.daemon.databank.batches import STUDIES as BATCH_STUDIES
from ui.daemon.databank.batches import batches
from ui.daemon.databank.cells import norm
from ui.daemon.results import knobs, store
from ui.daemon.results.slice import slice_for, verdict_row, whole


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


def _batch_path(project: str, study: str, strategy: str) -> tuple[Path | None, str | None]:
    """Where a batch study's result for one mother lives, `cloud`/`wfc`/`cscv` (OPEN #51).

    Args:
        project: SQX project name.
        study: Study key.
        strategy: The mother's name; these studies never judge a population.

    Returns:
        (`<batch>/estudios/<study>.json`, None), or (None, the reason in Spanish) when the
        study is not one of these, no strategy was asked for, no batch carries this mother,
        or two batches do (`ui.daemon.databank.batches.batches`, the same ambiguity the
        databank panel refuses to pick for the owner).
    """
    if study not in BATCH_STUDIES or not strategy:
        return None, None
    found = batches(project).get(norm(strategy), [])
    if not found:
        return None, "esta estrategia no es madre de ningún lote de variantes"
    if len(found) > 1:
        return None, "dos lotes de variantes para esta madre: sin uno solo que leer"
    return found[0] / "estudios" / f"{study}.json", None


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
    current = knobs.signed(study, [], population=not strategy)
    skipped = []
    batch_path, batch_why = _batch_path(project, study, strategy)
    if batch_why:
        return {"result": None, "meta": {"day": None, "path": None, "config_hash": None,
                                         "current_hash": current, "stale": False,
                                         "computed_at": None,
                                         "skipped": [{"day": "", "reason": batch_why}]}}
    if batch_path:
        got, why = store.load(batch_path)
        if why:
            return {"result": None, "meta": {"day": None, "path": str(batch_path),
                                             "config_hash": None, "current_hash": current,
                                             "stale": False, "computed_at": None,
                                             "skipped": [{"day": "", "reason": why}]}}
        return {"result": got, "meta": {
            "day": (got.get("computed_at") or "")[:10], "path": str(batch_path),
            "config_hash": got["config_hash"], "current_hash": current,
            "stale": current is not None and got["config_hash"] != current,
            "computed_at": got.get("computed_at"), "skipped": []}}
    for d in [day] if day else store.days(project, databank, study):
        path = _path(project, databank, study, d, strategy)
        got, why = store.load(path)
        if strategy and not path.is_file():      # a population study: its rows for this one
            path = _path(project, databank, study, d, "")
            population, why = store.load(path)
            row = (store.verdicts(path.parent) or {}).get(strategy)
            mine = population and (slice_for(population, strategy)
                                   or (row and verdict_row(population, row, strategy)))
            # Its rows are checked against the verdict.csv identity by `_mismatch`; the whole
            # population is nobody's, so it carries the identity asked for.
            alone = not (path.parent / "estrategias").is_dir()   # it writes no ficha at all
            got = ({**mine, "identity": None} if mine else
                   {**whole(population, strategy), "identity": identity or None}
                   if population and alone else None)
            why = why or (None if got else "la corrida de la población no nombra esta estrategia")
        why = why or _mismatch(got, path.parent.parent if strategy and path.parent.name ==
                               "estrategias" else path.parent, identity)
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
    current = knobs.signed(study, [], population=not strategy)
    runs, skipped = [], []
    batch_path, batch_why = _batch_path(project, study, strategy)
    if batch_why:
        return {"runs": [], "skipped": [{"day": "", "reason": batch_why}]}
    if batch_path:
        row = store.slim(batch_path)
        why = store.load(batch_path)[1] if row is None else None
        if why:
            return {"runs": [], "skipped": [{"day": "", "reason": why}]}
        return {"runs": [{"day": (row["computed_at"] or "")[:10],
                          "config_hash": row["config_hash"], "computed_at": row["computed_at"],
                          "state": row["state"], "label": row["label"],
                          "stale": current is not None and row["config_hash"] != current}],
               "skipped": []}
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
