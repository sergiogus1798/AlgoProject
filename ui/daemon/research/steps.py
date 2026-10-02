"""The five real steps one idea goes through: rule 5, the template, the project, the palette, the autopilot."""

import json
import re
import subprocess
import sys
from types import FrameType

from core.datapaths import template_dir
from core.researchpaths import autopilot_runs
from core.paths import CLAUDE_BIN, ROOT

# The seconds a cancelled step's child gets to stop its worker (`sqx-worker.sh stop` waits 5 min).
GRACE_S = 330
UNATTENDED = ("\n\nLo lanza la ventana (cola de «Investigar»): nadie te contesta. Si algo es "
              "ambiguo (regla dura 11), NO elijas: termina con una línea que empiece por "
              "«PREGUNTA:» con las lecturas posibles.")
CHILD: list[subprocess.Popen] = []


class Failed(Exception):
    """A step ended badly: the queue halts."""


class Question(Exception):
    """A step came back with a question for the owner: this idea waits, the next one goes."""


def terminate(_signum: int, _frame: FrameType | None) -> None:
    """SIGTERM from the daemon's cancel: pass it to the running child, wait for it, leave."""
    for child in CHILD:
        child.terminate()
        try:
            child.wait(timeout=GRACE_S)
        except subprocess.TimeoutExpired:
            child.kill()
    sys.exit(143)


def call(argv: list[str]) -> str:
    """Run one command in the repository, echo its output into the job's log, return it."""
    child = subprocess.Popen(argv, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True)
    CHILD.append(child)
    out, _ = child.communicate()
    CHILD.remove(child)
    print(out, flush=True)
    if child.returncode:
        raise Failed(f"{' '.join(argv[:4])}… salió con {child.returncode}")
    return out


def agent(which: str, text: str, tag: str) -> str:
    """One specialist, headless, as «Crear la plantilla con Claude» runs its skill.

    Returns:
        The name after the line `<TAG>: <name>` it must end with.
    """
    out = call([str(CLAUDE_BIN), "-p", f"Sigue .claude/agents/{which}.md al pie de la letra.\n\n"
                + text + UNATTENDED + f" Al terminar, una línea «{tag}: <nombre>».",
                "--permission-mode", "auto", "--output-format", "text"])
    if "PREGUNTA:" in out:
        raise Question(out[out.index("PREGUNTA:"):].splitlines()[0])
    found = re.search(rf"^{tag}: (\S+)", out, re.M)
    if not found:
        raise Failed(f"el {which} no terminó con su línea «{tag}: <nombre>»")
    return found.group(1)


def assets(ctx: dict) -> None:
    """Hard rule 5: `core.assets` must exit zero before anything is authored."""
    call([sys.executable, "-m", "core.assets", ctx["symbol"]])


def template(ctx: dict) -> None:
    """`templateArchitect` on this idea; the template it files becomes `ctx["template"]`."""
    i = ctx["idea"]
    ctx["template"] = agent("templateArchitect", (
        f"Fichero de ideas: {i.get('idea_file', '')}\nIdea elegida: {i['name']}\n"
        f"Regla exacta: {i['rule']}\nDirección: {i['direction']} (una sola, regla dura 13)\n"
        f"Bloques custom a crear: {json.dumps(i['custom_blocks'], ensure_ascii=False)}\n"
        f"Respuestas del dueño: {json.dumps(i['questions'], ensure_ascii=False)}"), "PLANTILLA")


def project(ctx: dict) -> None:
    """`sqx.projects.builder --workflow` on the custodian, one project per idea."""
    c = ctx["proposal"]["cell"]
    call([sys.executable, "-m", "sqx.projects.builder", ctx["project"], "--purpose",
          f"Director de investigación {ctx['proposal']['id']}: {ctx['idea']['name']} "
          f"({c['family']}, {c['direction']})",
          "--template", str(template_dir(ctx["template"]) / "template.sqx"),
          "--symbol", ctx["symbol"], "--timeframe", ctx["timeframe"], "--role", "custodian",
          "--workflow"])


def palette(ctx: dict) -> None:
    """`buildingBlocksExpert` writes and applies the palette the proposal already decided."""
    i = ctx["idea"]
    agent("buildingBlocksExpert", (
        f"Fichero de ideas: {i.get('idea_file', '')}\nIdea: {i['name']}\n"
        f"Plantilla: {ctx['template']}\nProyecto: {ctx['project']} (custodio, parado)\n"
        "La paleta YA está decidida por el director de investigación; escríbela y aplícala "
        f"sin cambiar sus familias:\n{json.dumps(i['palette'], ensure_ascii=False, indent=1)}"),
        "PALETA")


def autopilot(ctx: dict) -> None:
    """The autopilot from the build on, then the run's verdict closed in the memory."""
    try:
        call([sys.executable, "-m", "pipeline.autopilot.run", "--project", ctx["project"],
              *(["--own-log"] if ctx.get("ran_before") else [])])
    finally:
        runs = sorted((autopilot_runs() / ctx["project"]).glob("*/"))
        if runs:
            call([sys.executable, "-m", "studies.research.memory.report", "--close",
                  str(runs[-1])])


RUNNERS = {"activos": assets, "plantilla": template, "proyecto": project, "paleta": palette,
           "autopilot": autopilot}
