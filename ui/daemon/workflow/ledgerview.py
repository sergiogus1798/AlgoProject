"""The ledger as the rail reads it: which studies are this project's, the oos2 budget, the blind door."""

import pandas as pd

from ledger import gate, spend, study as studymod
from ui.daemon.runner import where
from ui.daemon.runs import guess_asset
from ui.text.numbers import num


def studies_of(project: str) -> list[str]:
    """The ledger studies that belong to a project.

    Args:
        project: Project name.

    Returns:
        Study ids whose id ends with the project's name or whose rows name it (a
        `launched_by` or a `note` pointing at its folders). The ledger is keyed by asset,
        timeframe and family, not by project, so this link is read, not recorded.
    """
    return [s for s in studymod.studies()
            if s.endswith(f"_{project}")
            or project in studymod.path(s).read_text(encoding="utf-8")]


def frame(ids: list[str]) -> pd.DataFrame:
    """Every row of those studies, oldest first, in the contract's columns."""
    rows = [r for s in ids for r in studymod.read(s).to_dict("records")]
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=list(studymod.COLUMNS))


def symbol(rows: pd.DataFrame, project: str) -> str | None:
    """The project's asset: what its ledger rows say, else what its name says."""
    return rows["symbol"].mode()[0] if len(rows) else guess_asset(project)


def asset_reads(asset: str) -> tuple[int, int]:
    """How often any study has read this asset's oos2, and how many studies did.

    Args:
        asset: The asset.

    Returns:
        (reads, studies). oos2 belongs to the asset, not to a project: every study that
        looks at it spends the same stretch.
    """
    reads = []
    for s in studymod.studies():
        f = studymod.read(s)
        reads.append(int(((f["symbol"] == asset) & (f["segment"] == "oos2")).sum()))
    return sum(reads), sum(1 for n in reads if n)


def oos2(rows: pd.DataFrame, asset: str | None) -> dict:
    """The oos2 gauge: how often this project's studies looked, and who may.

    Args:
        rows: What `frame` returned.
        asset: The asset, or None when neither the ledger nor the name says it.

    Returns:
        `looks`, `allowed` (None: `_policy.yaml` names who may read oos2, never how many
        times), `virgin`, `text`, and `reserved_for` (steps) and `by_step` (step → reads).
    """
    if asset is None:
        return {"looks": 0, "allowed": None, "virgin": True, "reserved_for": [],
                "by_step": {}, "text": "Sin activo: ni el ledger ni el nombre del proyecto "
                                       "dicen cuál es, así que no se sabe de qué oos2 hablar."}
    reads = rows[rows["segment"] == "oos2"]
    by_step = {num(s): int(n) for s, n in reads["step"].value_counts().sort_index().items()}
    allowed_steps = gate.reserved(asset).get("oos2", [])
    stray = sorted(num(s) for s in set(reads["step"]) if s not in allowed_steps)
    looks = spend.virgin(rows, asset)["oos2"]["reads"]
    total, studies = asset_reads(asset)
    text = (f"OOS2 de {asset}: {looks} mirada(s) de este proyecto"
            + (f" ({', '.join(f'paso {k}: {v}' for k, v in by_step.items())})" if looks else "")
            + f"; {total} en {studies} estudio(s) de {asset}"
            + (f". Reservado para los pasos {', '.join(num(s) for s in allowed_steps)}"
               f" (sólo para un agente autónomo)" if gate.enforced() else "")
            + (f". ⚠ lo leyeron pasos fuera de la reserva: {', '.join(stray)}"
               if stray and gate.enforced() else ""))
    return {"looks": looks, "allowed": None, "virgin": looks == 0, "text": text,
            "reserved_for": [num(s) for s in allowed_steps], "by_step": by_step}


def door_study(project: str) -> str | None:
    """The one study the blind door is asked about: the one blindJoint signs and reads.

    Args:
        project: Project name.

    Returns:
        `<symbol>_<timeframe>_<template folder>` from the project's registry row (owner, Q9
        of plan 24), or None when the registry names no template. Rows signed under the
        project's own name (E1's tests) are never counted: the rail's door and step 20's
        must be the same door.
    """
    row, family = where.enrolled(project), where.family(project)
    return studymod.study_id(row["symbol"], row["timeframe"], family) if family else None


def blind(rows: pd.DataFrame) -> dict:
    """The door over whatever rows it is handed: kept for callers written before `door`.

    Args:
        rows: Ledger rows.

    Returns:
        `sealed`, `done` and `text`, as `door` — but over those rows, not over the study
        blindJoint reads; new callers ask `door(project)`.
    """
    done = [num(s) for s, ran in gate.done(rows).items() if ran]
    if not gate.enforced():
        return {"sealed": False, "done": done,
                "text": "abierto: 17, 18 y 19 se leen cuando quieras (la puerta ciega sólo "
                        "se cierra a un agente autónomo)"}
    try:
        gate.allow_read(rows)
    except PermissionError as refused:
        return {"sealed": True, "done": done, "text": str(refused).removeprefix("ledger: ")}
    return {"sealed": False, "done": done,
            "text": "17, 18 y 19 están los tres en el ledger: se leen a la vez."}


def door(project: str) -> dict:
    """The door of step 20, asked of `ledger.gate` over exactly the study blindJoint reads.

    Args:
        project: Project name.

    Returns:
        `sealed`, `done` (the blind steps with a row), `study` (None without a template),
        and `text` (the gate's own sentence when sealed, naming the study).
    """
    study = door_study(project)
    if study is None and gate.enforced():
        return {"sealed": True, "done": [], "study": None,
                "text": "sin plantilla en projects/registry.csv no hay estudio del ledger que "
                        "abra el paso 20: queda cerrado"}
    if not gate.enforced():
        return blind(pd.DataFrame(columns=["step"])) | {"study": study}
    got = blind(studymod.read(study))
    return got | {"study": study, "text": (f"{got['text']} (en el estudio {study})"
                                          if got["sealed"] else
                                          f"17, 18 y 19 están los tres en el ledger del estudio "
                                          f"{study}: se leen a la vez.")}
