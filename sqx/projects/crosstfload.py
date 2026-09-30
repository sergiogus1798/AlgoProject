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
from sqx.projects import crosstf, crosstfsolo, registry
from sqx.projects.configure import running_install
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
    held = running_install(cfx)
    if held:
        raise SystemExit(f"el {held} tiene {cfx.parent.name} abierto y reescribe sus databanks "
                         f"al sincronizar: páralo antes (bin/sqx-worker.sh --role {held} stop)")
    with zipfile.ZipFile(cfx) as z:
        return {n: z.read(n) for n in z.namelist()}


def refill(folder: Path, files: list[Path]) -> int:
    """Empty a databank folder of its .sqx and copy these in; SQX loads them on its next start
    (`knowhow/databanks/curating-a-databank.md`: a stopped install syncs from its files)."""
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.glob("*.sqx"):
        old.unlink()
    for f in files:
        shutil.copy2(f, folder / f.name)
    return len(files)


def load_input(project: str, role: str, day: str) -> dict:
    """Step 10.5: scale the Cross Market survivors, wire the CrossTF task, fill CrossTF_Input.

    Args:
        project: A workflow project (`builder --workflow`) on a worker.
        role: The worker holding it, stopped.
        day: The batch's day under `core.datapaths.crosstf_dir`.

    Returns:
        `mothers`, `siblings`, `loaded`, `source` (tf), `targets`, `blocks`, `batch`,
        `clamped` (siblings whose periods hit the builder's floor).
    """
    install = worker_dir(role)
    cfx = project_dir(project, install) / "project.cfx"
    members = members_of(cfx)
    fed = feeders(banks(members))
    if CROSSTF["input"] not in fed:
        raise SystemExit(f"{project} no lleva la tarea de Cross Market: no hay supervivientes "
                         "que escalar")
    mothers = sorted(databank_dir(project, fed[CROSSTF["input"]], install).glob("*.sqx"))
    if not mothers:
        raise SystemExit(f"«{fed[CROSSTF['input']]}» no tiene ningún .sqx en {install.name}: "
                         "corre antes el Cross Market (paso 9) y su corte (paso 10)")
    task = members[member_of(members["config.xml"].decode("utf-8"), CROSSTF["title"])]
    source = crosstf.main_chart(task.decode("utf-8"))[1]
    targets = doctrine()["crosstf"]["timeframes"][source]
    symbol = next(r["symbol"] for r in reversed(registry.rows()) if r["name"] == project)
    batch = crosstf_dir(project, day)
    shutil.rmtree(batch / "sqx", ignore_errors=True)   # a second preparation the same day
    frame = scale.fabricate(mothers, batch, source, targets)
    # The same targets, in the same order, are the tasks `wire` writes, one each: the study
    # places each sibling in its `target_tf`'s databank, and one missing there is a KeyError.
    wired = crosstf.wire(cfx, symbol, day)
    loaded = refill(databank_dir(project, CROSSTF["input"], install),
                    sorted((batch / "sqx").glob("*.sqx")))
    return {"mothers": len(mothers), "siblings": len(frame), "loaded": loaded,
            "source": source, "targets": targets, "blocks": wired["blocks"], "batch": batch,
            "clamped": int(frame["clamped"].sum()), "warning": wired["warning"],
            "tasks": wired["tasks"]}


def load_mothers(project: str, role: str) -> dict:
    """Before step 13: the mothers CrossTF kept, without their siblings, into CrossTF_Mothers.

    Args:
        project: A workflow project on a worker.
        role: The worker holding it, stopped.

    Returns:
        `mothers` copied and `siblings` left behind. MC Retest perturbs the strategies the
        owner may trade; a sibling is a measuring device of step 11, not a candidate. The
        CrossTF databank is left whole: its export is what step 12 reads.
    """
    install = worker_dir(role)
    cfx = project_dir(project, install) / "project.cfx"
    members = members_of(cfx)
    config = members["config.xml"].decode("utf-8")
    if f'<Databank name="{CROSSTF["mothers"]}"' not in config:   # a project built before it
        members["config.xml"] = declare(config, [CROSSTF["mothers"]]).encode("utf-8")
        with zipfile.ZipFile(cfx, "w", zipfile.ZIP_DEFLATED) as z:
            for name, blob in members.items():
                z.writestr(name, blob)
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


def fill(bank: str, project: str, role: str) -> str:
    """Fill one of the two databanks and say what went in, in the owner's words.

    Args:
        bank: CrossTF_Input or CrossTF_Mothers.
        project, role: As `load_input`.
    """
    if bank == CROSSTF["mothers"]:
        got = load_mothers(project, role)
        return (f"{got['mothers']} madres de {CROSSTF['output']} -> {bank} ({got['siblings']} "
                f"hermanas escaladas se quedan en {CROSSTF['output']})")
    got = load_input(project, role, date.today().isoformat())
    return "\n".join([f"{got['mothers']} madres x {len(got['targets'])} timeframes -> "
                      f"{got['siblings']} hermanas ({got['clamped']} con períodos pegados al "
                      "mínimo: se leen solo sin escalar)",
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
    a = ap.parse_args()
    print(fill(CROSSTF["mothers"] if a.mothers else CROSSTF["input"], a.project, a.role))


if __name__ == "__main__":
    main()
