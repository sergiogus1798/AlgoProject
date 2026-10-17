"""The Estrategia page's routes: metadata, basic stats, the curve, and «Archivar»."""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from sqx.databank import locate
from studies.run import where
from ui.daemon.runs import guess_asset
from ui.daemon.strategy import archive_write as write
from ui.daemon.strategy import archived, costcurve, meta, stats
from ui.daemon.tearsheet import harvest

ROUTER = APIRouter()


class Archive(BaseModel):
    """One press of «Archivar»: which strategy, at which step, and the owner's note."""

    project: str
    databank: str
    identity: str
    step: str
    note: str = ""


def _read(
    project: str,
    databank: str,
    identity: str,
    source: str,
    version: str,
    strategy: str = "",
) -> dict | str:
    """The cosecha rows of one strategy, live or archived; a databank without a cosecha
    borrows one of the project's (`tearsheet.borrow`: same XML, else by `strategy`'s name),
    and the dict's `databank` and `note` say which.

    Returns:
        `harvest.read`'s dict or the refusal sentence.
    """
    if source == "live":
        return harvest.read(project, databank, identity, strategy)
    got = archived.load(identity, version)
    return got if isinstance(got, str) else archived.tearsheet(identity, version)


def _asked(
    project: str, databank: str, identity: str, source: str
) -> dict[str, str] | None:
    """The refusal for an incomplete question or an unknown source, or None."""
    if not (project and databank and identity):
        return {"error": "Elige un proyecto, un databank y una estrategia."}
    return archived.bad_source(source)


@ROUTER.get("/api/strategy/meta")
def strategy_meta(
    project: str = "",
    databank: str = "",
    identity: str = "",
    source: str = "live",
    version: str = "",
) -> dict[str, Any]:
    """What the strategy is: signal, direction, orders, costs, money management, Friday close.

    Returns:
        `sqx.inspect.strategymeta.read`'s dict plus `origin` (where the .sqx was found);
        archived: the fields frozen that day; or `{"error"}` («sin .sqx en ningún install»).
    """
    refused = _asked(project, databank, identity, source)
    if refused:
        return refused
    try:
        return (
            meta.live(project, databank, identity)
            if source == "live"
            else meta.frozen(identity, version)
        )
    except Exception as e:  # noqa: BLE001 — the boundary with a person: a sentence, never a 500
        return {"error": f"No pude leer el .sqx: {type(e).__name__}: {e}"}


@ROUTER.get("/api/strategy/costcurve")
def strategy_costcurve(
    project: str = "",
    databank: str = "",
    identity: str = "",
    source: str = "live",
    version: str = "",
    strategy: str = "",
) -> dict[str, Any]:
    """SQX's equity, IS then OOS1.

    Returns:
        As `costcurve.curve`, plus `asset` and `note` (where the cosecha came from, "" for
        this databank's own); or `{"error"}`.
    """
    refused = _asked(project, databank, identity, source)
    if refused:
        return refused
    data = _read(project, databank, identity, source, version, strategy)
    if isinstance(data, str):
        return {"error": data, "absent": isinstance(data, harvest.Absent)}
    return costcurve.curve(data) | {
        "asset": guess_asset(project),
        "note": data.get("note", ""),
    }


@ROUTER.get("/api/strategy/stats")
def strategy_stats(
    project: str = "",
    databank: str = "",
    identity: str = "",
    source: str = "live",
    version: str = "",
    strategy: str = "",
) -> dict[str, Any]:
    """Trade count, net, PF, win rate, DD, Sharpe and the return distribution, per sample.

    Returns:
        As `stats.build`, plus `asset` and `note` (as `/costcurve`); OOS2 `{"blocked": …}` until 17-19 are
        in the ledger, then from a cosecha with an oos2 sample or «OOS2 abierto, sin export…».
    """
    refused = _asked(project, databank, identity, source)
    if refused:
        return refused
    data = _read(project, databank, identity, source, version, strategy)
    if isinstance(data, str):
        return {"error": data, "absent": isinstance(data, harvest.Absent)}
    return stats.build(project, data, source == "live") | {
        "asset": guess_asset(project),
        "note": data.get("note", ""),
    }


@ROUTER.post("/api/strategy/archive")
def strategy_archive(req: Archive) -> dict[str, Any]:
    """Freeze the strategy with everything the window shows of it (`archive_write`).

    Returns:
        `{"folder", "version"}`, or `{"error"}`: no template in the registry (no family to
        sign the ledger count under), no .sqx anywhere, SQX writing the project, the same
        minute archived twice.
    """
    if not req.step.strip():
        return {"error": "Falta el paso del WORKFLOW en que está la estrategia."}
    family = where.family(req.project)
    if family is None:
        return {"error": where.no_family(req.project)}
    path, origin = locate.sqx(req.project, req.databank, req.identity)
    if path is None:
        return {"error": origin}
    # A file off the install is passed by hand, so the manifest says it did not come from there.
    by_hand = None if path.parents[1].name == "databanks" else path
    try:
        folder = write.archive(
            req.project,
            req.databank,
            req.identity,
            req.step,
            req.note,
            family=family,
            sqx=by_hand,
        )
    except (OSError, RuntimeError, ValueError) as e:
        return {"error": f"No se archivó: {e}"}
    return {"folder": str(folder), "version": folder.name, "origin": origin}
