"""The rail's buttons: Python tests, one SQX step, «Correr workflow» — each behind its question — and each step's ⚙."""

import httpx
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMessageBox, QWidget

from ui.desktop import client
from ui.desktop.theme import C
from ui.desktop.workspace.aggregate import ask
from ui.desktop.workspace.railwords import runnable
from ui.desktop.workspace.texts import NO_SCREEN, NOT_YET, SETTINGS, STUDY_NOW
from ui.text.glossary import label
from ui.text.numbers import num
from ui.text.brief import RUNNING, brief, busy, full, off


def post(path: str, body: dict) -> dict:
    """One POST to the daemon; a daemon that is down comes back as `error` (ui boundary)."""
    try:
        return client.post(path, body)
    except httpx.HTTPError as failed:
        return {"error": f"El demonio no respondió: {failed}"}


def panel_choice(rail: QWidget, n: str = "") -> tuple[str, list[str]]:
    """The databank of step `n`'s own sub-panel and the rows chosen there, ('', []) without one.

    Each of 21-25 reads its own sub-panel (Cierre › Exposición reads OOS, Mapa condicional
    and Stop ATR read Results); taking whichever sub-panel happened to be open sent every
    step to OOS (📓 2026-09-29: conditionalMap «necesita la cosecha», atrCalculator crashed).
    The rows chosen count only while that sub-panel is the one on screen.
    """
    zone = rail.parentWidget()
    while zone is not None and not hasattr(zone, "panel"):
        zone = zone.parentWidget()
    if zone is None:
        return "", []
    panel, step = zone.panel, rail.step(n) if n else {}
    shown = panel.sub_spec()
    spec = next((sub for t in panel.tabs if t["tab"] == step.get("tab")
                 for sub in t["subs"] if sub["sub"] == step.get("sub")), shown)
    chosen = panel.table.chosen_names() if spec is shown else []
    return spec.get("databank", ""), chosen


def tests(rail: QWidget, keys: list[tuple[str, str]], databank: str = "",
          strategies: list[str] | None = None) -> None:
    """Queue tests through POST /api/workflow/run and say what started and what did not.

    Args:
        rail: The rail (its `project`, `step`, `said`, `load`, `poll`).
        keys: (step, study) pairs.
        databank: The panel's databank; '' lets each test find its own.
        strategies: The panel's chosen strategies; None or [] for the population.
    """
    if not keys:
        rail.said.setText(label("Nada que correr: marca una prueba o pulsa el ▶ de un paso."))
        return
    costly = [f"· {t['title']}: {t['spends']}" for n, k in keys
              for t in rail.step(n)["tests"] if t["key"] == k and t["spends"]]
    if costly and QMessageBox.question(
            rail, "Esto lee oos2 o escribe en el ledger",
            "Cada run cuenta y no se deshace:\n" + "\n".join(costly) + "\n\n¿Correr?"
    ) != QMessageBox.Yes:
        rail.said.setText("No se lanzó nada.")
        return
    got = post("workflow/run", {"project": rail.project, "databank": databank,
                                "strategies": strategies or [],
                                "tests": [{"n": n, "key": k} for n, k in keys]})
    if "error" in got:
        rail.said.setText(got["error"])
        return
    refused = "   ".join(f"{r['key']} (paso {r['n']}): {r['why']}" for r in got["refused"])
    rail.said.setText(f"{num(len(got['jobs']))} trabajos en cola"
                      + (f"   ·   no se lanzó: {refused}" if refused else ""))
    rail.load(rail.project)
    rail.poll()


def step(rail: QWidget, n: str) -> None:
    """A Python card's ▶: its ticked tests; with none ticked — after a question listing them,
    «No» by default — every free test of it that is not running, or, on a step whose every
    test reads oos2 or writes the ledger (17, 18, 20), those, behind their own question."""
    s = rail.step(n)
    idle = [t for t in runnable(s) if t["state"] != "running"]
    keys = [k for k, on in rail.ticks.items() if on and k[0] == n]
    if not keys:
        picked = [t for t in idle if not t["spends"]] or idle
        keys = [(n, t["key"]) for t in picked]
        if keys and QMessageBox.question(
                rail, f"Correr el paso {n}",
                "No hay ninguna prueba marcada en este paso; se correrían todas estas:\n"
                + "\n".join(f"· {label(t['title'])}" for t in picked) + "\n\n¿Correrlas?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            rail.said.setText("No se lanzó nada.")
            return
    databank, chosen = panel_choice(rail, n) if s.get("panel") else ("", [])
    # 21-25 read the Databanks panel, which may not be on screen: say what they will read.
    if databank and keys and QMessageBox.question(
            rail, f"Correr el paso {n}",
            f"Se corre sobre el databank «{databank}» del panel de Databanks, "
            + (f"sólo sobre las {num(len(chosen))} filas elegidas allí."
               if chosen else "sobre todas sus filas (ninguna elegida allí).")
            + "\n\n¿Correr?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No
    ) != QMessageBox.Yes:
        rail.said.setText("No se lanzó nada.")
        return
    tests(rail, keys, databank, chosen)


def panel(rail: QWidget, tab: str, databank: str = "", strategies: list[str] | None = None) -> str:
    """Databanks' «▶ Correr marcados de este panel»: the ticked tests of this tab's steps, or —
    none ticked, after a question listing them — every free one of them.

    Returns:
        The line for the panel. The ticks live on the rail, off screen from Databanks, so an
        empty tick list did nothing anyone could see (📓 2026-09-29).
    """
    steps = [s for s in rail.data.get("steps", []) if s["tab"] == tab]
    keys = [k for k, on in rail.ticks.items() if on and k[0] in {s["n"] for s in steps}]
    if not keys:
        free = [(s["n"], t) for s in steps if s["kind"] == "python"
                for t in runnable(s) if t["state"] != "running"]
        if not free:
            return (f"«{tab}» no tiene pruebas que se corran desde aquí: un análisis de SQX "
                    "(WFM) se lanza con «▶▶ toda la población» en la ficha de una de sus "
                    "estrategias.")
        if QMessageBox.question(
                rail, f"Correr «{tab}»", "No hay ninguna prueba marcada en esta pestaña; se "
                "correrían todas estas:\n" + "\n".join(f"· {label(t['title'])}" for _, t in free)
                + "\n\n¿Correrlas?", QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No) != QMessageBox.Yes:
            return "No se lanzó nada."
        keys = [(n, t["key"]) for n, t in free]
    tests(rail, keys, databank, strategies)
    return rail.said.text()


def sqx_step(rail: QWidget, n: str) -> None:
    """An SQX card's ▶: the step's preflight, its sentence, and only «Sí» queues the job."""
    got = ask("launch/preflight", project=rail.project, step=n)
    if not got.get("ok"):
        rail.said.setText(f"Paso {n}: " + off(got.get("reasons") or [got.get("error", "?")]))
        rail.said.setToolTip(full(got.get("reasons") or [got.get("error", "?")]))
        return
    if QMessageBox.question(rail, f"Lanzar el paso {n} en SQX", got["text"] + "\n\n¿Confirmas?",
                            QMessageBox.Yes | QMessageBox.No,
                            QMessageBox.No) != QMessageBox.Yes:
        rail.said.setText("No se lanzó nada.")
        return
    done = post("launch/run", {"project": rail.project, "step": n})
    rail.said.setText(f"En marcha: paso {n} ({', '.join(done['titles'])}) — su avance, en "
                      "«En marcha»" if done.get("job") else
                      "No se lanzó: " + brief(done.get("reasons") or [done.get("error", "?")]))
    rail.load(rail.project)
    rail.poll()


def chain(rail: QWidget) -> None:
    """«Correr workflow»: the preflight and the whole plan, and only «Sí» queues the one job."""
    got = ask("launch/chain", project=rail.project)
    if not got.get("ok"):
        rail.said.setText("Correr workflow: " + off(got.get("reasons") or [got.get("error", "?")]))
        rail.said.setToolTip(full(got.get("reasons") or [got.get("error", "?")]))
        return
    if QMessageBox.question(rail, "Correr workflow (hasta la próxima decisión)",
                            got["text"] + "\n\n¿Confirmas?", QMessageBox.Yes | QMessageBox.No,
                            QMessageBox.No) != QMessageBox.Yes:
        rail.said.setText("No se lanzó nada.")
        return
    done = post("launch/chain", {"project": rail.project, "plan": got["plan"]})
    rail.said.setText("En marcha: Correr workflow — su avance, en «En marcha»" if done.get("job")
                      else "No se lanzó: " + brief(done.get("reasons") or [done.get("error", "?")]))
    rail.load(rail.project)
    rail.poll()


def plan_line(chain_plan: dict) -> str:
    """What «Correr workflow» would do now, in one line under its button."""
    do, stop = chain_plan["do"], chain_plan["stop"]
    steps = " → ".join(f"{a['n']}{' (SQX)' if a['kind'] == 'sqx' else ''}" for a in do)
    if busy(stop["why"]):          # the rest is in the step's card (owner, 2026-09-30)
        end = RUNNING
    else:
        end = (f"se para antes del paso {stop['n']} ({label(stop['title'])}): "
               f"{brief(label(stop['why']))}" if stop["n"] else brief(label(stop["why"])))
    return (f"Correría: {steps}   ·   {end}" if do else f"Nada que correr: {end}")


def configure(rail: QWidget, n: str) -> None:
    """A step's ⚙: open the zone and section where its configuration is edited — a section of
    «Configuración SQX», or the project's asset in «Activos» (`texts.SETTINGS`). A step with
    no such screen opens in the drawer with the reason, never an invented editor.

    Args:
        rail: The rail (its `project`, `data`, `open_step`, `said`).
        n: The step's number.
    """
    shell, where = rail.window(), SETTINGS.get(n)
    if where is None or not hasattr(shell, "open_zone"):
        rail.open_step(n)
        rail.said.setText(f"Paso {n}: {NO_SCREEN}")
        return
    name, section = where
    shell.open_zone(name)
    zone = shell.zones[name]
    if name == "Activos":
        asset = rail.data.get("asset") or ""
        QTimer.singleShot(0, lambda: zone.show_page(asset))
        return
    if not zone.sections:
        zone.load()
    at = next((i for i, s in enumerate(zone.sections) if s.section["key"] == section), None)
    if at is not None:
        zone.open(at)
    text = (STUDY_NOW if rail.step(n)["kind"] == "python" else NOT_YET)
    zone.status.setWordWrap(True)      # a long line there would widen the whole window
    zone.say(text.format(project=rail.project, n=n), C["weak"])
