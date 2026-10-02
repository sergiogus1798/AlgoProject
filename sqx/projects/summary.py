#!/usr/bin/env python3
"""Say out loud what building a project applied, which is the half a human reads."""

from sqx.projects.rankings import describe


def say(done: dict, role: str) -> None:
    """Print one build's result, warnings last.

    Args:
        done: What `builder.build` returned.
        role: The install it was written into, for the run-it line.

    The warnings sit at the end on purpose: a provisional cost and a silenced acceptance
    stamp every number the project will produce, and they are what gets skimmed past when
    they are buried between two lines of configuration.
    """
    print(f"{done['project']} on {done['install']}")
    print(f"  template  {done['template']}")
    print(f"  tasks     {', '.join(done['tasks'])}   caps {done['max_strategies']} strategies "
          f"/ {done['minutes']} min")
    if done["added"]:
        print(f"  workflow  + {', '.join(done['added'])}: todas las tareas del workflow, "
              "activas sólo CONSTRUCCION y OOS. CrossTF va a build..oos1; las WFC se "
              "precian con sqx.projects.wfc")
    bars = done["exit_bars"]
    # A project with no Build task has no generator, so there are no exit bounds to report.
    print(f"  doctrina  {done['timeframe']} en todas las tareas, sesión {done['session']}"
          + (f", salida por barras {bars[0]}–{bars[1]}" if bars else ", sin tarea de construcción"))
    print("  segments  " + ", ".join(f"{m}={s}" for m, s in done["segments"].items()))
    # A 0 here is the tell OPEN.md issue 35 went unread: `configure` counted it, but the
    # human-readable summary never printed it, so a task still trading the donor's market
    # at the donor's costs read as an ordinary silent success.
    print("  setups    " + ", ".join(f"{m}={n}" for m, n in done["setups"].items()))
    if done["feed_replaced"]:
        print(f"  feed      {done['feed_replaced']} → {done['feed']} en {len(done['setups'])} "
              f"tarea(s), traído de {done['session_borrowed_from']}")
    if done["acceptance"]["tasks"]:
        print(f"  aceptación  {describe(done['acceptance'])}  (assets/_study.yaml, "
              f"build {done['acceptance']['build_years']} años)")
    print(f"  to disk   {', '.join(done['synced_to_disk']) or 'already syncing'}")
    if done["silenced"]:
        print(f"  ⚠️ {done['silenced']} condiciones de aceptación apagadas — esas tareas "
              "miden, no filtran")
    if done["provisional_costs"]:
        print(f"  ⚠️ PROVISIONAL: {', '.join(done['provisional_costs'])}")
    print(f"\nrun it:  bin/sqx-worker.sh --role {role} start && "
          f"python3 -c \"from core import worker; "
          f"worker.call('-project action=start name={done['project']}','{role}')\"")
