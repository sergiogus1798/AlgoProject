#!/usr/bin/env python3
"""Turn a template plus an asset into a Builder project installed and ready to run."""

import argparse
import json
import re
import shutil
import zipfile
from pathlib import Path

from core.assetcheck import pending, provisional
from core.assetdata import doctrine, load
from core.paths import worker_dir
from core.datapaths import projects_backup
from sqx.inspect.keep_tasks import keep
from sqx.projects import crosschecks
from sqx.projects.configure import configure, ignored_templates, running_install
from sqx.projects.databanks import chain_databanks
from sqx.projects.doctrine import blockers, borrow_session
from xml.etree import ElementTree

DONOR = projects_backup("XAUUSD_base_2026-09-21") / "project.cfx"
TEMPLATES_REL = "user/settings/StrategyTemplates"
NAME_OK = re.compile(r"^[A-Za-z0-9_]+$")
SYNCED = "Auto-sync every 1 hour"


def set_template(text: str, path: Path) -> str:
    """Point a Build task at one template and make it actually use it.

    Args:
        text: A task XML.
        path: Absolute path of the .sqx inside the install that will build.

    Returns:
        The task XML with templateFile replaced and StrategyType forced to "template".
        The second half is the free gate: with type="simple" SQX builds generically and
        ignores the template, with no error anywhere (OPEN.md issue 9).
    """
    text = re.sub(r'templateFile="[^"]*"', f'templateFile="{path}"', text)
    return re.sub(r'(<StrategyType[^>]*?)type="[^"]*"', r'\1type="template"', text)


def set_caps(text: str, strategies: int, minutes: int) -> str:
    """Cap how much the builder may produce and how long it may run.

    Args:
        text: A task XML.
        strategies: MaxStrategies, the databank-full stop.
        minutes: Wall-clock cap on the run.

    Returns:
        The task XML with both caps applied. A build with no cap inherits the donor's,
        which on XAUUSD is 10,000 strategies and 90 minutes.
    """
    text = re.sub(r"<MaxStrategies>\d+</MaxStrategies>",
                  f"<MaxStrategies>{strategies}</MaxStrategies>", text)
    return re.sub(r'(<StopCondition[^>]*passedStrategies=")\d+("[^>]*hours=")\d+("[^>]*minutes=")\d+',
                  rf"\g<1>{strategies}\g<2>{minutes // 60}\g<3>{minutes % 60}", text)


def sync_databanks(config: str) -> tuple[str, list[str]]:
    """Make every databank of the project write itself to disk.

    Args:
        config: The project's config.xml as text.

    Returns:
        The config and the databanks changed. The donor ships its build outputs as
        "Auto-sync never", which builds fine and leaves the directory empty, so nothing
        outside SQX can read the result and /curate has no files to act on.
    """
    changed = re.findall(r'<Databank name="([^"]*)"[^>]*syncType="Auto-sync never"', config)
    return re.sub(r'(<Databank name="[^"]*"[^>]*syncType=")Auto-sync never',
                  rf"\g<1>{SYNCED}", config), changed


def build(name: str, template: Path, symbol: str, role: str, timeframe: str, strategies: int,
          minutes: int, donor: Path, segment: str | None = None,
          tasks: tuple = ("Build",), only: set | None = None,
          session_from: Path | None = None, silence: tuple = ()) -> dict:
    """Assemble one Builder project and install it, priced and dated from assets/.

    Args:
        name: Project name, underscores only — the HTTP API splits on whitespace.
        template: The .sqx to build from, from the template library.
        symbol: Asset name, e.g. "XAUUSD".
        role: Which headless install it is installed into and will build on.
        timeframe: SQX timeframe name. Every task of the project gets this one — a retest
            on another timeframe is not testing the strategy that was built.
        strategies: MaxStrategies and the databank-full stop.
        minutes: Wall-clock cap.
        donor: The project cloned for its data feed, exits and acceptance conditions.
        segment: Force one segment on every task. Omit so each takes its own from its
            type — the build on `build`, the retests on `oos1`, in one project.
        tasks: Which task types to keep from the donor.
        only: Task XML file names to narrow those types to, e.g. {"Retest-Task1.xml"}.
        silence: Task types whose acceptance conditions are turned off, so the task reads
            instead of filtering. A task that deletes what fails turns a measurement into
            a selection, and then the only thing the study can say is how many survived.
        session_from: A project.cfx that defines the asset's session, for when the donor does
            not. Read only. Omit when the donor already carries it.

    Returns:
        What was done, as data: where the project and the template landed, the caps, the
        databanks switched to syncing, and the verification. Every step here was a
        hand-edit of the task XML until 2026-09-23, which is what made the chain
        impossible to embed in an application.
    """
    install = worker_dir(role)
    # Every library folder holds a file literally called template.sqx, so installing it
    # under that name makes two different templates collide silently. The folder is the
    # template's name.
    stem = template.parent.name if template.stem == "template" else template.stem
    installed_template = install / TEMPLATES_REL / "authored" / f"{stem}.sqx"
    installed_template.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(template, installed_template)

    with zipfile.ZipFile(donor) as z:
        members = {n: z.read(n) for n in z.namelist()}
    members, kept = keep(members, set(tasks), only=only)

    borrowed = (borrow_session(members, load(symbol)["session"], session_from)
                if session_from else None)

    config, synced = sync_databanks(members["config.xml"].decode("utf-8"))
    members["config.xml"] = re.sub(r'<Project name="[^"]*"', f'<Project name="{name}"',
                                   config, count=1).encode("utf-8")
    kinds = {t.get("taskXMLFile"): t.get("type")
             for t in ElementTree.fromstring(members["config.xml"]).find("Tasks")}
    quiet = 0
    for member in [n for n in members if n.endswith(".xml") and n != "config.xml"]:
        text = set_template(members[member].decode("utf-8"), installed_template)
        text = set_caps(text, strategies, minutes)
        if kinds.get(member) in silence:
            text, n = crosschecks.silence(text)
            quiet += n
        members[member] = text.encode("utf-8")

    chained = chain_databanks(members)

    out = install / "user/projects" / name / "project.cfx"
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for member, blob in members.items():
            z.writestr(member, blob)

    costs = configure(out, symbol, segment, timeframe)
    with zipfile.ZipFile(out) as z:
        final = {n: z.read(n) for n in z.namelist()}
    doc = next((c for _, c in costs.values() if c.get("generator")), {})
    return {"project": name, "install": install.name, "cfx": str(out), "timeframe": timeframe,
            "exit_bars": doc.get("exit_bars"), "session": load(symbol)["session"],
            "session_borrowed_from": str(session_from) if session_from else None,
            "session_borrowed_into": borrowed,
            "template": str(installed_template), "tasks": kept["kept"],
            "databanks": kept["databanks"], "synced_to_disk": synced,
            "chain": chained,
            "max_strategies": strategies, "minutes": minutes, "silenced": quiet,
            "segments": {n: seg for n, (seg, _) in costs.items()},
            "template_ignored": ignored_templates(final),
            "provisional_costs": provisional(load(symbol)),
            "setups": {n: c.get("setups", 0) for n, (_, c) in costs.items()}}


def main() -> None:
    """Build and install one Builder project, refusing on anything undecided."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("name", help="project name, underscores only")
    ap.add_argument("--template", type=Path, required=True)
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--role", default="custodian")
    ap.add_argument("--timeframe", required=True, help="M15, M30, H1 or H4 — every task gets it")
    ap.add_argument("--max-strategies", type=int,
                    default=doctrine()["databank"]["max_strategies"])
    ap.add_argument("--minutes", type=int, default=10)
    ap.add_argument("--donor", type=Path, default=DONOR)
    ap.add_argument("--session-from", type=Path,
                    help="a project.cfx that defines the asset's session, when the donor "
                         "does not — read only, never written")
    ap.add_argument("--segment", choices=("build", "oos1"),
                    help="force one segment on every task; omit to take each task's own")
    ap.add_argument("--tasks", default="Build",
                    help="comma-separated donor task types to keep, e.g. Build,Retest")
    ap.add_argument("--silence", default="",
                    help="comma-separated task types whose acceptance conditions go off, "
                         "e.g. Retest — the task then reads instead of filtering")
    ap.add_argument("--only", help="comma-separated task XML files to narrow --tasks to, "
                    "e.g. Build-Task3.xml,Retest-Task1.xml")
    ap.add_argument("--json", action="store_true", help="emit the result as JSON only")
    a = ap.parse_args()

    if not NAME_OK.match(a.name):
        raise SystemExit(f"'{a.name}': project names are underscores only — the HTTP API "
                         "splits its command on whitespace.")
    if not a.template.exists():
        raise SystemExit(f"{a.template} does not exist.")
    missing = pending(load(a.symbol))
    if missing:
        raise SystemExit(f"{a.symbol}: {', '.join(missing)} have no agreed value. Ask the owner "
                         "before authoring anything for it (hard rule 5).")
    held = running_install(worker_dir(a.role) / "user/projects" / a.name / "project.cfx")
    if held:
        raise SystemExit(f"the {held} is running and rewrites a project.cfx on exit. "
                         f"Stop it: bin/sqx-worker.sh --role {held} stop")

    stop = blockers(load(a.symbol), a.timeframe)
    if stop:
        raise SystemExit("\n".join(stop))
    done = build(a.name, a.template, a.symbol, a.role, a.timeframe, a.max_strategies,
                 a.minutes, a.donor, a.segment, tuple(a.tasks.split(',')),
                 set(a.only.split(',')) if a.only else None, a.session_from,
                 tuple(x for x in a.silence.split(',') if x))
    if done["template_ignored"]:
        raise SystemExit("the template would be IGNORED: " + "; ".join(done["template_ignored"]))

    if a.json:
        print(json.dumps(done, indent=2))
        return
    print(f"{done['project']} on {done['install']}")
    print(f"  template  {done['template']}")
    print(f"  tasks     {', '.join(done['tasks'])}   caps {done['max_strategies']} strategies "
          f"/ {done['minutes']} min")
    bars = done["exit_bars"]
    # A project with no Build task has no generator, so there are no exit bounds to report.
    print(f"  doctrina  {done['timeframe']} en todas las tareas, sesión {done['session']}"
          + (f", salida por barras {bars[0]}–{bars[1]}" if bars else ", sin tarea de construcción"))
    print(f"  segments  " + ", ".join(f"{m}={s}" for m, s in done["segments"].items()))
    print(f"  to disk   {', '.join(done['synced_to_disk']) or 'already syncing'}")
    if done["silenced"]:
        print(f"  ⚠️ {done['silenced']} condiciones de aceptación apagadas — esas tareas "
              "miden, no filtran")
    if done["provisional_costs"]:
        print(f"  ⚠️ PROVISIONAL: {', '.join(done['provisional_costs'])}")
    print(f"\nrun it:  bin/sqx-worker.sh --role {a.role} start && "
          f"python3 -c \"from core import worker; "
          f"worker.call('-project action=start name={a.name}','{a.role}')\"")


if __name__ == "__main__":
    main()
