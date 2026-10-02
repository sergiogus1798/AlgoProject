"""Whether a proposal's queue may be launched now, and the sentence the owner confirms."""

from core.paths import CLAUDE_BIN
from sqx.projects import registry
from studies.research.board import proposal
from ui.daemon.advance import preflight as advance
from ui.daemon.launch import api as launch
from ui.daemon.research import queue

ROLE = "custodian"
PER_IDEA_USD = 15      # the dossier's §6: template and palette of one launched idea


def check(proposal_id: str) -> dict:
    """Every precondition of «Crear plantillas y lanzar en SQX».

    Args:
        proposal_id: A saved proposal.

    Returns:
        `ok`, `reasons`, `ideas` (the names that would go, in order), `projects`, `skipped`
        (name → why it stays), `hours`, and `text`, the confirmation sentence when ok.
    """
    p = proposal.load(proposal_id)
    go = [i for i in p["ideas"] if proposal.launchable(i)[0]]
    skipped = {i["name"]: proposal.launchable(i)[1] for i in p["ideas"] if i not in go}
    reasons = []
    if not go:
        reasons.append("ninguna idea se puede lanzar: " + "; ".join(
            f"{n} ({why})" for n, why in skipped.items()))
    projects = [queue.project_name(p, i["name"]) for i in go] if not reasons else []
    live = {r["name"] for r in registry.rows() if not r["retired"]}
    reasons += [f"el proyecto {name} ya existe" for name in projects if name in live]
    if not CLAUDE_BIN.exists():
        reasons.append(f"no encuentro Claude Code en {CLAUDE_BIN} (config/machine.yaml: claude_bin)")
    reasons += advance.busy(ROLE, "") + launch.queued()
    got = {"ok": not reasons, "reasons": reasons, "ideas": [i["name"] for i in go],
           "projects": projects, "skipped": skipped, "role": ROLE,
           "hours": sum(i["custodian_hours"] for i in go), "text": ""}
    if got["ok"]:
        got["text"] = text(p, got)
    return got


def text(p: dict, got: dict) -> str:
    """What the owner confirms: what runs, where, in which order, and what it costs."""
    c = p["cell"]
    lines = [f"Se van a crear y lanzar {len(got['ideas'])} idea(s) de {c['family']} en "
             f"{c['symbol']} {c['timeframe']} {c['direction']}, UNA DETRÁS DE OTRA en el custodio:",
             *[f"  {n}. {idea}  →  proyecto {project}"
               for n, (idea, project) in enumerate(zip(got["ideas"], got["projects"]), 1)],
             *[f"  no va: {name} ({why})" for name, why in got["skipped"].items()], "",
             "Cada idea: core.assets → templateArchitect (crea la plantilla y sus bloques custom, "
             "los instala en los dos workers) → proyecto con todo el workflow → "
             "buildingBlocksExpert (aplica la paleta) → autopilot (build y pasos 7 a 16).", "",
             f"Coste: unas {got['hours']} h de custodio y hasta {PER_IDEA_USD * len(got['ideas'])} "
             f"$ en tokens (unos {PER_IDEA_USD} $ por idea).",
             f"En esta celda ya van {p['ideas_spent']} ideas; con estas, el listón sube "
             f"{len(got['ideas'])} ensayos más. Las supervivientes se parecerán entre sí."]
    if p["provisional_costs"]:
        lines.append(f"AVISO: los costes de {c['symbol']} son provisionales.")
    lines.append("Una pregunta del templateArchitect aparta esa idea y sigue la siguiente; "
                 "cualquier otro fallo para la cola.")
    return "\n".join(lines)
