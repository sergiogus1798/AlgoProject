#!/usr/bin/env python3
"""Write the eight MC Retest tasks of a custom project: one perturbation each, as evidence."""

import argparse
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from core.assetcheck import pending
from core.assetdata import doctrine, load
from sqx.projects.configure import running_install
from sqx.projects.databanks import set_databank
from sqx.projects.orders import pending_orders
from sqx.projects.perturbations import disable, usable, write_task
from sqx.projects.stage import own


def active(config: str, title: str, on: bool) -> str:
    """Switch one task of the project on or off by the title the GUI shows.

    Args:
        config: The project's config.xml as text.
        title: The task's title attribute, e.g. "MCR 4 MinDist".
        on: Whether SQX runs it when the project runs.

    Returns:
        The config with that task's `active` rewritten. A task the study does not want is
        left in place and switched off rather than deleted: the decision is reversible,
        and a project missing a task looks like a different project.
    """
    tag = re.search(rf'<Task\b[^>]*title="{re.escape(title)}"[^>]*/>', config).group(0)
    return config.replace(tag, re.sub(r'active="[^"]*"', f'active="{str(on).lower()}"', tag), 1)


def member_of(config: str, title: str) -> str | None:
    """The task XML member the project's task with this title points at.

    Args:
        config: The project's config.xml as text.
        title: The task's title attribute.

    Returns:
        The member name, or None when the project has no such task.
    """
    tag = next((t for t in ElementTree.fromstring(config).find("Tasks")
                if t.get("title") == title), None)
    return tag.get("taskXMLFile") if tag is not None else None


def configure(cfx: Path, symbol: str, source: str, databank: Path | None) -> dict:
    """Write every MC Retest task of one project, and say which were skipped and why.

    Args:
        cfx: Path of a project.cfx. Must not be held by a running install.
        symbol: Asset name, e.g. "XAUUSD".
        source: The databank all eight tasks read. They do NOT chain: the same population
            goes into each one, so the eight results are eight readings of one thing and
            not a funnel whose later tasks see whatever the earlier ones left.
        databank: That databank's directory on disk, for reading what the population
            actually trades with. None before the build has run.

    Returns:
        One row per catalogue task under "tasks", the pending-order verdict under
        "orders", and the project name.
    """
    data = load(symbol)
    with zipfile.ZipFile(cfx) as z:
        members = {n: z.read(n) for n in z.namelist()}
    config = members["config.xml"].decode("utf-8")
    orders = pending_orders(members, databank)
    catalogue = doctrine()["mc_retest"]

    rows = []
    for spec in catalogue["tasks"]:
        member = member_of(config, spec["title"])
        methods, dropped = usable(spec, data, orders["pending"])
        if not member or not methods:
            rows.append({"title": spec["title"], "member": member, "written": False,
                         "dropped": dropped,
                         "why": f"el proyecto no lleva la tarea {spec['title']}" if not member
                         else "; ".join(sorted(set(dropped.values())))})
            if member:
                config = active(config, spec["title"], False)
                text = disable(members[member].decode("utf-8"))
                members[member] = set_databank(text, "Input", source)[0].encode("utf-8")
            continue
        sims = spec.get("simulations", catalogue["simulations"])
        text, done = write_task(members[member].decode("utf-8"), spec, methods, data, sims)
        members[member] = set_databank(text, "Input", source)[0].encode("utf-8")
        config = active(config, spec["title"], True)
        rows.append({"title": spec["title"], "member": member, "written": True,
                     "simulations": sims, "dropped": dropped, **done})

    members["config.xml"] = config.encode("utf-8")
    with zipfile.ZipFile(cfx, "w", zipfile.ZIP_DEFLATED) as z:
        for name, blob in members.items():
            z.writestr(name, blob)
    return {"project": ElementTree.fromstring(config).get("name"), "orders": orders,
            "simulations": catalogue["simulations"], "input": source, "tasks": rows}


def main() -> None:
    """Configure a project's MC Retest tasks, refusing on anything undecided."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("symbol")
    ap.add_argument("--cfx", required=True, type=Path)
    ap.add_argument("--input", required=True,
                    help="databank the eight tasks read, e.g. 'OOS'. No se adivina: es la "
                         "poblacion que se perturba")
    ap.add_argument("--databank-dir", type=Path,
                    help="carpeta de ese databank, para mirar que ordenes lleva la "
                         "poblacion. Por defecto, la del propio proyecto")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    missing = pending(load(a.symbol))
    if missing:
        raise SystemExit(f"{a.symbol}: {', '.join(missing)} sin valor pactado. "
                         "Preguntale al dueno antes de configurar nada (regla dura 5).")
    held = running_install(a.cfx)
    if held:
        raise SystemExit(f"el {held} tiene este proyecto abierto y reescribe el .cfx al "
                         f"salir. Parala: bin/sqx-worker.sh --role {held} stop")
    folder = a.databank_dir or a.cfx.parent / "databanks" / a.input
    done = configure(a.cfx, a.symbol, a.input, folder if folder.is_dir() else None)
    staged = own(a.cfx, "mcretest", [r["title"] for r in done["tasks"] if not r["written"]])

    if a.json:
        print(json.dumps(done, indent=2, default=str))
        return
    print(staged)
    o = done["orders"]
    verdict = {True: "SI", False: "no", None: "SIN RESOLVER"}[o["pending"]]
    read = f", {o['read']} estrategias leidas" if o["read"] else ""
    print(f"{done['project']}  {a.symbol}  <- {done['input']}")
    print(f"  ordenes ({o['source']}{read}): {', '.join(o['types']) or 'ninguna'}"
          f"  ->  pendientes: {verdict}")
    for row in done["tasks"]:
        if not row["written"]:
            print(f"  ⊘ {row['title']:<14} NO configurada — {row['why']}")
            continue
        print(f"  ✓ {row['title']:<14} {'+'.join(row['methods'])}  {row['segment']} "
              f"{row['from']}→{row['to']}  {row['simulations']} sims  "
              f"{row['silenced']} condicion(es) apagada(s)")
        for method, why in row["dropped"].items():
            print(f"      ⚠️ sin {method}: {why}")
    print("\nLas ocho leen el MISMO databank: son ocho lecturas de una poblacion, no un "
          "embudo.\nEl veredicto se toma en Python (strategies/retest/) y se aplica con "
          "/curate.")


if __name__ == "__main__":
    main()
