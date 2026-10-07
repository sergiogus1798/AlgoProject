#!/usr/bin/env python3
"""Fill the two databanks Cross TF reads on disk, install stopped: its input (10.5) and the mothers MC Retest reads (13)."""

import argparse
import re
import shutil
import zipfile
from datetime import date
from pathlib import Path

from core.assetdata import doctrine
from core.datapaths import crosstf_dir
from core.paths import databank_dir, project_dir, worker_dir
from sqx.projects import cfxio
from sqx.projects import crosstf, crosstfsolo, registry
from sqx.projects.crosschecks import member_of
from sqx.projects.databanks import databanks
from sqx.projects.stage import titles
from sqx.projects.wfc import declare
from sqx.projects.workflow import CROSSTF
from sqx.variants import scale

# A sibling as `sqx.variants.scale` names it, and as SQX renames a second copy of it: «(1)».
SIBLING = re.compile(r"_Scaled[MHD]\d+(\(\d+\))?$")


def banks(members: dict[str, bytes]) -> dict[str, dict]:
    """Every task's databanks, by title: {title: {"Input", "Output"}}."""
    config = members["config.xml"].decode("utf-8")
    return {t: databanks(members[f].decode("utf-8")) for f, t in
            re.findall(r'<Task\b[^>]*?taskXMLFile="([^"]*)"[^>]*?title="([^"]*)"', config)
            if f in members}


def feeders(io: dict[str, dict]) -> dict[str, str]:
    """The databanks this module fills, each with the databank it fills it from.

    Args:
        io: Every task's databanks by title, as `banks` returns them.

    Returns:
        {CrossTF_Input: the Cross Market task's output, CrossTF_Mothers: CrossTF}. Cross TF's
        input is the Cross Market survivors scaled, never a task's output, so a launcher that
        only follows task outputs sees it empty forever (the symptom of 2026-09-29).
    """
    market = next((io[t]["Output"] for t in titles("crossmarket") if t in io), None)
    out = {CROSSTF["mothers"]: CROSSTF["output"]}
    return out | ({CROSSTF["input"]: market} if market else {})


def members_of(cfx: Path) -> dict[str, bytes]:
    """The project's files, refused while an install holds it (hard rule 4)."""
    held = cfxio.held(cfx)
    if held:
        raise SystemExit(f"el {held} tiene {cfx.parent.name} abierto y reescribe sus databanks "
                         f"al sincronizar: páralo antes (bin/sqx-worker.sh --role {held} stop)")
    return cfxio.members(cfx)


def refill(folder: Path, files: list[Path]) -> int:
    """Empty a databank folder of its .sqx and copy these in; SQX loads them on its next start
    (`knowhow/databanks/curating-a-databank.md`: a stopped install syncs from its files)."""
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob("*.sqx"):
        old.unlink()
    for f in files:
        shutil.copy2(f, folder / f.name)
    return len(files)


def load_input(project: str, role: str, day: str, cfx: Path | None = None,
               folder: Path | None = None, targets: list[str] | None = None) -> dict:
    """Step 10.5: scale the Cross Market survivors, wire the CrossTF task, fill CrossTF_Input.

    Args:
        project: A workflow project (`builder --workflow`) on a worker.
        role: The worker holding it, stopped.
        day: The batch's day under `core.datapaths.crosstf_dir`.
        cfx: The project.cfx to wire; default the install's own. A live session passes a copy.
        folder: Mothers taken from here, every `.sqx` under it, instead of the Cross Market
            databank — a calibration feeds the step from `keep/<P>/{survivors,sample}`.
        targets: The timeframes to scale to and retest; the doctrine's list when None.

    Returns:
        `mothers`, `siblings`, `loaded`, `source` (tf), `targets`, `blocks`, `batch`,
        `clamped` (siblings whose periods hit the builder's floor).
    """
    install = worker_dir(role)
    cfx = cfx or project_dir(project, install) / "project.cfx"
    members = members_of(cfx)
    fed = feeders(banks(members))
    if not folder and CROSSTF["input"] not in fed:
        raise SystemExit(f"{project} no lleva la tarea de Cross Market: no hay supervivientes "
                         "que escalar")
    source_of = folder or databank_dir(project, fed[CROSSTF["input"]], install)
    mothers = sorted(source_of.rglob("*.sqx"))
    if not mothers:
        raise SystemExit(f"{source_of} no tiene ningún .sqx: corre antes el Cross Market "
                         "(paso 9) y su corte (paso 10), o da una carpeta con madres")
    task = members[member_of(members["config.xml"].decode("utf-8"), CROSSTF["title"])]
    source = crosstf.main_chart(task.decode("utf-8"))[1]
    targets = [t for t in doctrine()["crosstf"]["timeframes"][source]
               if targets is None or t in targets]
    symbol = next(r["symbol"] for r in reversed(registry.rows()) if r["name"] == project)
    batch = crosstf_dir(project, day)
    shutil.rmtree(batch / "sqx", ignore_errors=True)   # a second preparation the same day
    frame = scale.fabricate(mothers, batch, source, targets)
    # The same targets, in the same order, are the tasks `wire` writes, one each: the study
    # places each sibling in its `target_tf`'s databank, and one missing there is a KeyError.
    wired = crosstf.wire(cfx, symbol, day, project, targets)
    for bank in wired["databanks"] if folder else []:   # a calibration project is reused:
        refill(databank_dir(project, bank, install), [])  # an earlier attempt's retest goes
    loaded = refill(databank_dir(project, CROSSTF["input"], install),
                    sorted((batch / "sqx").glob("*.sqx")))
    return {"mothers": len(mothers), "siblings": len(frame), "loaded": loaded,
            "source": source, "targets": targets, "blocks": wired["blocks"], "batch": batch,
            "clamped": int(frame["clamped"].sum()), "warning": wired["warning"],
            "tasks": wired["tasks"], "databanks": wired["databanks"],
            "unverified": int((frame["unverified"] != "").sum())}


def load_mothers(project: str, role: str, cfx: Path | None = None) -> dict:
    """Before step 13: the mothers CrossTF kept, without their siblings, into CrossTF_Mothers.

    Args:
        project: A workflow project on a worker.
        role: The worker holding it, stopped.
        cfx: As `load_input`.

    Returns:
        `mothers` copied and `siblings` left behind. MC Retest perturbs the strategies the
        owner may trade; a sibling is a measuring device of step 11, not a candidate. The
        CrossTF databank is left whole: its export is what step 12 reads.
    """
    install = worker_dir(role)
    cfx = cfx or project_dir(project, install) / "project.cfx"
    members = members_of(cfx)
    config = members["config.xml"].decode("utf-8")
    if f'<Databank name="{CROSSTF["mothers"]}"' not in config:   # a project built before it
        members["config.xml"] = declare(config, [CROSSTF["mothers"]]).encode("utf-8")
        cfxio.write(cfx, members)
    files = sorted(databank_dir(project, CROSSTF["output"], install).glob("*.sqx"))
    kept = [f for f in files if not SIBLING.search(f.stem)]
    if not kept:
        raise SystemExit(f"«{CROSSTF['output']}» no tiene ninguna madre en {install.name}: "
                         "corre antes el Cross TF (paso 11)")
    refill(databank_dir(project, CROSSTF["mothers"], install), kept)
    return {"mothers": len(kept), "siblings": len(files) - len(kept)}


def separate_titles(cfx: Path) -> list[str]:
    """The extra-timeframe Cross TF tasks the project carries: step 11 runs them with
    «CrossTF»; `load_input` creates them, so a preflight run before it cannot list them."""
    with zipfile.ZipFile(cfx) as z:
        return crosstfsolo.present(z.read("config.xml").decode("utf-8"))


def phase2_tasks(cfx: Path) -> list[dict]:
    """The phase-2 tasks of a project (step 11.7) as {timeframe, title, databank}; [] when it
    has none — a project built before encargo 47 — never an exception. Step 11.7 runs
    `stage.just(cfx, [t["title"] for t in phase2_tasks(cfx)])`; step 11 needs no change."""
    with zipfile.ZipFile(cfx) as z:
        return crosstfsolo.present_phase2(z.read("config.xml").decode("utf-8"))


def fill(bank: str, project: str, role: str, cfx: Path | None = None,
         folder: Path | None = None, targets: list[str] | None = None) -> str:
    """Fill one of the two databanks and say what went in, in the owner's words.

    Args:
        bank: CrossTF_Input or CrossTF_Mothers.
        project, role, cfx, folder, targets: As `load_input`.
    """
    if bank == CROSSTF["mothers"]:
        got = load_mothers(project, role, cfx)
        return (f"{got['mothers']} madres de {CROSSTF['output']} -> {bank} ({got['siblings']} "
                f"hermanas escaladas se quedan en {CROSSTF['output']})")
    got = load_input(project, role, date.today().isoformat(), cfx, folder, targets)
    return "\n".join([f"{got['mothers']} madres x {len(got['targets'])} timeframes -> "
                      f"{got['siblings']} hermanas ({got['clamped']} con períodos pegados al "
                      f"mínimo y {got['unverified']} con una longitud sin verificar: no se "
                      "leen como escaladas)",
                      f"desde {got['source']}: {', '.join(got['targets'])} · una tarea por "
                      f"timeframe: {', '.join(got['blocks'])}",
                      f"{got['loaded']} .sqx en {bank} (madres + hermanas) · lote {got['batch']}",
                      *[f"«{s['title']}»: {s['timeframe']} con {s['engine']} -> {s['databank']}"
                        for s in got["tasks"]],
                      got["warning"]]).strip()


def main() -> None:
    """Fill CrossTF_Input (default) or, with --mothers, CrossTF_Mothers."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--role", required=True, choices=["conductor", "custodian"])
    ap.add_argument("--mothers", action="store_true",
                    help="llena CrossTF_Mothers (lo que lee el MC Retest) en vez de CrossTF_Input")
    ap.add_argument("--from-folder", type=Path,
                    help="madres desde esta carpeta (todo .sqx bajo ella) en vez del databank "
                         "de Cross Market")
    ap.add_argument("--targets", nargs="+",
                    help="solo estos timeframes de `crosstf.timeframes`; por defecto todos")
    a = ap.parse_args()
    print(fill(CROSSTF["mothers"] if a.mothers else CROSSTF["input"], a.project, a.role,
               folder=a.from_folder, targets=a.targets))


if __name__ == "__main__":
    main()
