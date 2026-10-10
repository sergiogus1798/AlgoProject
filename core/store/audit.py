"""Whether everything a project left on disk is in the store: each folder in some zip, or ignored by name."""

import zipfile
from pathlib import Path

from core.datapaths import variants_dir
from core.paths import DATA
from core.store import late, verify, write

# Every folder of the data root that keeps one sub-folder per project, and why the store does
# not take it. A folder that is neither here nor read below is reported: a new writer has to
# be given a place, on purpose.
IGNORED = {
    "autopilot": "el diario de cada run; lo que dijo cada paso está en el manifiesto",
    "harvest": "las métricas de toda la población generada; las de cada guardada van en cosecha.*",
    "projects": "el registro y los project.cfx retirados",
    "atrCalculator": "pasos 21 en adelante (rejilla de stops): aún no se guardan",
    "structural": "pasos 21 en adelante (pruebas estructurales): aún no se guardan",
    "neighbours": "los .sqx de las vecinas de T1 se rehacen de la madre; su tabla va en vecinas.*",
    "store": "el propio almacén",
}
READ = ("reports", "raw", "metrics", "crosstf", "strategyPermutations")


def held(project: str) -> tuple[dict[tuple, set[str]], dict[str, str]]:
    """What the store holds of a project.

    Returns:
        (study, databank, day) -> the file names inside every zip filed under it, over all the
        project's stored strategies (an `also` of a trades zip counts as its own key); and
        strategy name -> identity.
    """
    have: dict[tuple, set[str]] = {}
    who = {}
    for identity in verify.stored():
        doc = write.manifest(identity)
        if doc["origin"]["project"] != project:
            continue
        who[doc["origin"]["strategy"]] = identity
        for file, about in doc["files"].items():
            with zipfile.ZipFile(write.folder(identity) / file) as z:
                inside = {Path(n).name for n in z.namelist()}
            keys = [(about.get("study"), about.get("databank"), about.get("day"))]
            keys += [("operaciones", *also.rsplit(".", 1)) for also in about.get("also", [])]
            for key in keys:
                have.setdefault(key, set()).update(inside)
    return have, who


def missing(project: str) -> tuple[list[str], list[str]]:
    """What a project left on disk that no stored strategy carries.

    Args:
        project: SQX project name.

    Returns:
        (`falta`, `ajeno`). `falta`: a report folder or one of its tables, an export, a
        variant batch of a stored mother, a scaling table or a project folder nobody decided
        about — each a line saying what and where. `ajeno`: exports that vouch for no stored
        strategy (another build's, or a strategy that did not pass the gate); they are not
        failures, but a pairing that broke looks exactly like this, so they are listed.
    """
    have, who = held(project)
    falta, ajeno = [], []
    for top in sorted(p.name for p in DATA.iterdir() if (p / project).is_dir()):
        if top not in IGNORED and top not in READ:
            falta.append(f"{top}/{project}: carpeta que el almacén no conoce")
    for folder in sorted(p for p in (DATA / "reports" / project).glob("*/*/*") if p.is_dir()):
        databank, day, study = folder.parts[-3:]
        inside = have.get((study, databank, day))
        if inside is None:
            vouched = any(late.names(project, databank, day, i) for i in who.values())
            (falta if vouched else ajeno).append(
                f"reports/{databank}/{day}/{study}: en ningún zip"
                + ("" if vouched else " (no avala a ninguna guardada)"))
            continue
        lost = sorted(p.name for p in folder.iterdir()
                      if p.is_file() and p.suffix not in late.PAGES and p.name not in inside)
        falta += [f"reports/{databank}/{day}/{study}/{n}: fichero en ningún zip" for n in lost]
    for folder in sorted(p for p in (DATA / "raw" / project).glob("[!_]*/*") if p.is_dir()):
        databank, day = folder.parts[-2:]
        vouched = any(late.names(project, databank, day, i) for i in who.values())
        tables = [p for p in folder.rglob("*") if p.suffix in late.TABLES and p.parent != folder
                  and "strategies" not in p.parts and not any(x.startswith("_") for x in p.parts)]
        for study, there in (("operaciones", (folder / "trades.parquet").exists()),
                             ("exportacion", bool(tables))):
            if there and (study, databank, day) not in have:
                (falta if vouched else ajeno).append(
                    f"raw/{databank}/{day}: {study} en ningún zip"
                    + ("" if vouched else " (no avala a ninguna guardada)"))
    if (DATA / "metrics" / project).is_dir() and not any(k[0] == "metricas" for k in have):
        falta.append("metrics: en ningún zip")
    for path in sorted((DATA / "crosstf" / project).glob("*/scaling.parquet")):
        if ("hermanas", None, path.parent.name) not in have:
            falta.append(f"crosstf/{path.parent.name}/scaling.parquet: en ningún zip")
    for name, identity in sorted(who.items()):
        folder = variants_dir(project, name)
        if folder.is_dir():
            studies = {a.get("study") for a in write.manifest(identity)["files"].values()}
            falta += [f"strategyPermutations/{folder.name}: sin {s} en {identity[:12]}"
                      for s in ("variantes", "optimizacion")
                      if s not in studies and (s == "variantes" or (folder / "estudios").is_dir())]
    known = {n.replace(" ", "_") for n in who}
    ajeno += [f"strategyPermutations/{p.name}: lote de una estrategia que no está guardada"
              for p in sorted((DATA / "strategyPermutations" / project).glob("*"))
              if p.is_dir() and p.name not in known]
    return falta, ajeno
