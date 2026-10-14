#!/usr/bin/env python3
"""Turn a template plus an asset into a Builder project installed and ready to run."""

import argparse
import json
import re
import shutil
import tempfile
import zipfile
from pathlib import Path

from core.assetcheck import pending, provisional
from core.assetdata import doctrine, load
from core.datapaths import projects_backup, tmp_dir
from core.paths import worker_dir
from core.symbols import current
from sqx.inspect.keep_tasks import keep
from sqx.projects import (
    buildrules,
    cfxio,
    crosschecks,
    rankings,
    registry,
    source,
    summary,
)
from sqx.projects.configure import configure, ignored_templates
from sqx.projects.databanks import chain_databanks
from sqx.projects.doctrine import blockers, borrow_session, caps
from sqx.projects.patch import (
    GENERATIONS,
    install_template,
    set_caps,
    set_generation,
    set_simple,
    set_template,
    sync_databanks,
)
from sqx.projects.registryxml import refresh_all
from sqx.projects.resources import borrow_symbol, main_feed, refuse
from sqx.projects import workflow as wf
from xml.etree import ElementTree
from core.xmlget import el, hit
from typing import Any

DONOR = projects_backup("XAUUSD_base_2026-09-21") / "project.cfx"
ENTRY = re.compile(r'<Rule name="(Long|Short) entry".*?</Rule>', re.S)
TEMPLATES_REL = "user/settings/StrategyTemplates"


def directions(template: Path) -> list[str]:
    """The sides a template can open a trade on: each «Long/Short entry» rule holding an Enter action.

    Owner, 2026-10-01, hard rule: one direction per template and per build, never both.
    """
    with zipfile.ZipFile(template) as z:
        text = z.read("strategy_Portfolio.xml").decode("utf-8")
    return sorted(
        {
            m.group(1)
            for m in ENTRY.finditer(text)
            if re.search(r'key="Enter\w*"', m.group(0))
        }
    )


def build(
    name: str,
    template: Path | None,
    symbol: str,
    role: str,
    timeframe: str,
    strategies: int,
    minutes: int,
    donor: Path,
    segment: str | None = None,
    tasks: tuple = ("Build",),
    only: set | None = None,
    session_from: Path | None = None,
    silence: tuple = (),
    workflow: bool = False,
    acceptance: str = "study",
    side: str | None = None,
    generation: str = GENERATIONS[0],
) -> dict[str, Any]:
    """Assemble one Builder project and install it, priced and dated from assets/.

    Args:
        name: Project name, underscores only — the HTTP API splits on whitespace.
        template: The library .sqx to build from; None for a Simple Strategy (needs `side`).
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
        workflow: Every workflow step's task in this one project, only Build and OOS on, every
            retest's acceptance silenced (owner, 2026-09-25/26). Overrides `tasks` and `only`.
        acceptance: Which filters of `assets/_study.yaml` the Build accepts by (`rankings`).
        side: "long" or "short" — the one direction a Simple Strategy build generates.
        generation: One of `patch.GENERATIONS`; "random-generation" is a population's twin.

    Returns:
        What was done, as data: where the project and the template landed, the caps, the
        databanks switched to syncing, and the verification — each one a hand-edit of the
        task XML until 2026-09-23.
    """
    install = worker_dir(role)
    # Every library folder holds a file literally called template.sqx: installed under that
    # name two templates collide silently, so the folder is the template's name.
    installed_template = staged_template = holder = None
    if template:
        stem = template.parent.name if template.stem == "template" else template.stem
        installed_template = install / TEMPLATES_REL / "authored" / f"{stem}.sqx"
        # The gates read `templateFile` (`charts.wanted`), so the copy they read lives outside
        # the install; it moves in only after every gate has passed (OPEN.md issue 114).
        holder = tempfile.TemporaryDirectory(prefix="sqx-template-", dir=tmp_dir())
        staged_template = Path(holder.name) / installed_template.name
        install_template(template, staged_template)

    with zipfile.ZipFile(donor) as z:
        members = {n: z.read(n) for n in z.namelist()}
    # The donor was frozen before SQX's feeds were renamed (2026-10-01): its tasks name feeds
    # SQX no longer holds, so they are translated before anything reads them.
    members = {
        n: current(b.decode("utf-8")).encode("utf-8") if n.endswith(".xml") else b
        for n, b in members.items()
    }
    if (
        workflow
    ):  # every retest measures and none filters, unless the owner names a filter
        tasks, only = (
            ("Build", "Retest"),
            wf.kept_members(members["config.xml"].decode("utf-8")),
        )
        silence = tuple(set(silence) | {"Retest"})
    members, kept = keep(members, set(tasks), only=only)
    added = wf.complete(members) if workflow else []

    borrowed = borrow_session(
        members, load(symbol)["session"], session_from
    )  # else SQX's registry
    # The donor's own feed is read from its generator when it kept one, and otherwise
    # from any task: every task of a one-asset donor names the same chart.
    xml_members = [m for m in members if m.endswith(".xml") and m != "config.xml"]
    build_member = next(
        (m for m in xml_members if m.startswith("Build-")), xml_members[0]
    )
    donor_feed = main_feed(members, build_member)
    replaced = borrow_symbol(
        members, load(symbol)["sqx_symbol"], build_member, session_from
    )
    refresh_all(
        members
    )  # the donor and any borrowed project predate the 2026-10-01 EETUS move

    config, synced = sync_databanks(members["config.xml"].decode("utf-8"))
    members["config.xml"] = re.sub(
        r'<Project name="[^"]*"', f'<Project name="{name}"', config, count=1
    ).encode("utf-8")
    kinds = {
        t.get("taskXMLFile"): t.get("type")
        for t in el(ElementTree.fromstring(members["config.xml"]).find("Tasks"))
    }
    quiet = 0
    for member in [n for n in members if n.endswith(".xml") and n != "config.xml"]:
        text = members[member].decode("utf-8")
        text = (
            set_template(text, hit(staged_template))
            if template
            else set_simple(text, hit(side))
        )
        text = set_caps(set_generation(text, generation), strategies, minutes)
        if kinds.get(member) in silence:
            text, n = crosschecks.silence(text)
            quiet += n
        members[member] = text.encode("utf-8")

    chained = chain_databanks(members)
    if workflow:
        wf.rewire(members)

    out = install / "user/projects" / name / "project.cfx"
    # Staged outside the install first: `configure` can still refuse (a session no task
    # defines) and the checks below can still refuse (a zero-Setup task, the donor's feed
    # surviving the swap), and none of that may leave a half-built .cfx sitting in
    # user/projects — that booby-trapped a USDJPY build on 2026-09-23 (OPEN.md issue 34).
    # Nothing under `install` is touched until every gate here has passed.
    with tempfile.TemporaryDirectory(prefix="sqx-builder-", dir=tmp_dir()) as tmp:
        staged = Path(tmp) / "project.cfx"
        with zipfile.ZipFile(staged, "w", zipfile.ZIP_DEFLATED) as z:
            for member, blob in members.items():
                z.writestr(member, blob)

        costs = configure(staged, symbol, segment, timeframe)
        accepted = rankings.apply(staged, symbol, timeframe, acceptance)
        if workflow:
            wf.finish(staged, symbol)
        with zipfile.ZipFile(staged) as z:
            final = {n: z.read(n) for n in z.namelist()}
        doc = next((c for _, c in costs.values() if c.get("generator")), {})
        result = {
            "project": name,
            "install": install.name,
            "cfx": str(out),
            "timeframe": timeframe,
            "exit_bars": doc.get("exit_bars"),
            "session": load(symbol)["session"],
            "session_borrowed_from": str(session_from) if session_from else None,
            "session_borrowed_into": borrowed,
            "feed": load(symbol)["sqx_symbol"],
            "feed_replaced": replaced,
            "template": str(installed_template or f"Simple Strategy, {side}"),
            "generation": generation,
            "tasks": kept["kept"],
            "added": added,
            "databanks": kept["databanks"],
            "synced_to_disk": synced,
            "chain": chained,
            "max_strategies": strategies,
            "minutes": minutes,
            "silenced": quiet,
            "acceptance": accepted,
            "segments": {n: seg for n, (seg, _) in costs.items()},
            "template_ignored": ignored_templates(final),
            "provisional_costs": provisional(load(symbol)),
            "setups": {n: c.get("setups", 0) for n, (_, c) in costs.items()},
        }

        refuse(result, final, donor_feed, replaced)
        if template:
            assert installed_template and staged_template and holder
            with zipfile.ZipFile(staged, "w", zipfile.ZIP_DEFLATED) as z:
                for member, blob in final.items():
                    z.writestr(
                        member,
                        blob.replace(
                            str(staged_template).encode(),
                            str(installed_template).encode(),
                        ),
                    )
        out.parent.mkdir(parents=True, exist_ok=True)
        if installed_template and staged_template:
            installed_template.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(staged_template, installed_template)
        shutil.move(str(staged), str(out))
        if holder:
            holder.cleanup()
    return result


def main() -> None:
    """Build and install one Builder project, refusing on anything undecided."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "name",
        help="Test_<...> (functional test), Trade_<...> (real work) or Research_<...> (research queue)",
    )
    ap.add_argument(
        "--purpose", required=True, help="one sentence: what this project is for"
    )
    shape = ap.add_mutually_exclusive_group(required=True)
    shape.add_argument("--template", type=Path)
    shape.add_argument(
        "--simple", choices=("long", "short"), help="Simple Strategy, one side"
    )
    ap.add_argument(
        "--family",
        help="Simple Strategy's idea family (required): a key of `_expected_sign`",
    )
    ap.add_argument(
        "--random", action="store_true", help="random generation, not genetic"
    )
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--role", default="custodian")
    ap.add_argument(
        "--timeframe", required=True, help="M15, M30, H1 or H4 — every task gets it"
    )
    ap.add_argument(
        "--max-strategies", type=int, help="default: databank.caps by prefix"
    )
    ap.add_argument("--minutes", type=int, help="default: databank.caps by prefix")
    ap.add_argument("--donor", type=Path, default=DONOR)
    ap.add_argument(
        "--session-from",
        type=Path,
        help="project.cfx to borrow the asset's session "
        "and feed from; default the newest one defining the feed — read only",
    )
    ap.add_argument(
        "--segment",
        choices=("build", "oos1"),
        help="force one segment on every task; omit to take each task's own",
    )
    ap.add_argument(
        "--tasks",
        default="Build",
        help="comma-separated donor task types to keep, e.g. Build,Retest",
    )
    ap.add_argument(
        "--silence",
        default="",
        help="comma-separated task types whose acceptance goes off, "
        "e.g. Retest — the task then reads instead of filtering",
    )
    ap.add_argument(
        "--only",
        help="comma-separated task XML files to narrow --tasks to, e.g. Build-Task3.xml",
    )
    ap.add_argument(
        "--workflow", action="store_true", help="every workflow task, Build+OOS on"
    )
    ap.add_argument(
        "--acceptance", choices=rankings.MODES, default="study", help="_study.yaml"
    )
    ap.add_argument("--json", action="store_true", help="emit the result as JSON only")
    a = ap.parse_args()

    if registry.check_name(a.name):
        raise SystemExit(registry.check_name(a.name))
    if msg := registry.check_family(a.family, bool(a.simple), a.name):
        raise SystemExit(msg)
    if a.template and not a.template.exists():
        raise SystemExit(f"{a.template} does not exist.")
    # Only where something is built: mt5.verify passes a finished strategy as `--template`
    # with `--tasks Retest`, and a generated strategy carries an Enter action on both rules.
    builds = a.workflow or "Build" in a.tasks.split(",")
    sides = directions(a.template) if a.template else [a.simple]
    if builds and len(sides) != 1:
        raise SystemExit(
            f"{a.template.name} abre operaciones en {sides or 'ninguna dirección'}: "
            "una plantilla, y un build, van en UNA sola dirección, long o short "
            "(regla dura del dueño, 2026-10-01)."
        )
    if gate := buildrules.early_gates(
        a.name, a.role, a.template, a.workflow, a.timeframe
    ):
        raise SystemExit("\n".join(gate))
    if a.template and (
        over := buildrules.over_the_cap(a.template, doctrine()["complexity"])
    ):
        raise SystemExit("\n".join(over))
    asset = load(a.symbol)
    missing = pending(asset)
    if missing:
        raise SystemExit(
            f"{a.symbol}: {', '.join(missing)} have no agreed value. Ask the owner "
            "before authoring anything for it (hard rule 5)."
        )
    held = cfxio.held(worker_dir(a.role) / "user/projects" / a.name / "project.cfx")
    if held:
        raise SystemExit(
            f"the {held} is running and rewrites a project.cfx on exit. "
            f"Stop it: bin/sqx-worker.sh --role {held} stop"
        )
    stop = blockers(asset, a.timeframe)
    if stop:
        raise SystemExit("\n".join(stop))
    borrow = a.session_from or source.pick(
        a.donor, asset["session"], asset["sqx_symbol"]
    )
    # `build` stages outside the install and moves in only after every gate (`refuse`).
    done = build(
        a.name,
        a.template,
        a.symbol,
        a.role,
        a.timeframe,
        *caps(a.name, a.max_strategies, a.minutes),
        a.donor,
        a.segment,
        tuple(a.tasks.split(",")),
        set(a.only.split(",")) if a.only else None,
        borrow,
        tuple(x for x in a.silence.split(",") if x),
        a.workflow,
        a.acceptance,
        a.simple,
        GENERATIONS[a.random],
    )

    registry.record(
        done,
        a.purpose,
        a.symbol,
        str(a.template or f"simple:{a.simple}"),
        a.family or "",
    )
    if a.json:
        print(json.dumps(done, indent=2))
        return
    summary.say(done, a.role)


if __name__ == "__main__":
    main()
