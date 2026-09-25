"""Turn a finished interview into a draft brief on disk and the command that authors it."""

import json
from datetime import date

from core.datapaths import template_dir, template_draft
from ui.daemon import interview

RANDOM_TEXT = {"one_free": "una condición aleatoria libre (#Group# vacío, 500 condiciones nativas)",
               "one_group": "una condición aleatoria del grupo {group}",
               "two_free": "dos condiciones aleatorias libres",
               "none": "sin condición aleatoria: solo la fija"}
LOGIC_TEXT = {"transition": "transición (cruza / rompe / pasa a estar)",
              "state": "estado (está / sigue)"}


def compose(answers: dict[str, str]) -> dict[str, object]:
    """The brief a finished interview amounts to, in the library's own JSON shape.

    Args:
        answers: Raw answers by question id; blanks are filled with the owner's defaults.

    Returns:
        A dict matching `brief.json` in the library, plus `defaults_applied` naming every
        question the reader skipped — the brief has to say which default produced what, and
        a default applied silently and never written down is how a decision gets lost.
    """
    a = interview.resolved(answers)
    skipped = [q["id"] for q in interview.QUESTIONS
               if interview.applies(q, answers) and not answers.get(q["id"], "")]
    random_text = RANDOM_TEXT[a["random"]].format(group=a.get("group", ""))
    return {"name": a["name"],
            "created": date.today().isoformat(),
            "idea": a["idea"],
            "archetype": a["archetype"],
            "direction": a["direction"],
            "logic": a["logic"],
            "shape": "fixed_and_random" if a["random"] != "none" else "fixed_only",
            "signal": {"fixed": {"block": "por decidir — lo resuelve /strategy-template",
                                 "rule": a["idea"],
                                 "logic": LOGIC_TEXT[a["logic"]]},
                       "random": random_text,
                       "operator": "AND"},
            "entry_order": a["entry"],
            "exits": a.get("exit_rule") or "la pila del esqueleto sin tocar",
            "defaults_applied": skipped,
            "origin": "interview",
            "status": "draft"}


def prompt(brief: dict[str, object]) -> str:
    """The message to paste into Claude Code so the skill authors this template.

    Args:
        brief: The dict `compose` returned.

    Returns:
        A `/strategy-template` invocation carrying every answer, so the skill does not
        re-ask what the interview already settled. The skill still does the two things
        this window cannot: check the vocabulary of the real install, and author the
        custom block if the condition is not there.
    """
    s = brief["signal"]
    return "\n".join([
        f"/strategy-template {brief['name']}",
        "",
        f"Idea: {brief['idea']}",
        f"Lógica: {s['fixed']['logic']} — ya preguntado, no lo vuelvas a preguntar.",
        f"Dirección: {brief['direction']}",
        f"Arquetipo: {brief['archetype']}",
        f"Aleatorias: {s['random']}",
        f"Orden de entrada: {brief['entry_order']}",
        f"Salidas: {brief['exits']}",
        "",
        f"El borrador del brief está en {template_draft(brief['name'])}.",
        "Cuando la plantilla esté emitida y registrada, bórralo.",
    ])


def commands(brief: dict[str, object]) -> list[dict[str, str]]:
    """The shell commands the skill will run, shown so the reader knows what is coming.

    Args:
        brief: The dict `compose` returned.

    Returns:
        One dict per command with the line and what it is for, in the order the skill runs
        them. Displayed, never executed here: authoring installs blocks into a real SQX,
        and that is the conductor's lane, not a window's.
    """
    name = brief["name"]
    lib = template_dir(name)
    return [
        {"what": "¿Existe ya la condición, y qué grupos la agrupan?",
         "cmd": "python3 -m sqx.inspect.vocabulary <término>"},
        {"what": "Instala el bloque en las dos instalaciones (si hay que autorarlo)",
         "cmd": f"python3 -m sqx.blocks.install {lib}/deps/blocks.xml --role conductor"},
        {"what": "Comprueba que la instalación que construye no se queda sin el bloque",
         "cmd": "python3 -m sqx.inspect.vocabulary --diff custodian"},
        {"what": "Emite la plantilla",
         "cmd": f"python3 -m sqx.templates.build {name} {lib}/deps/blocks.xml "
                f"<CBlock_key> {lib}/template.sqx"},
        {"what": "Da de alta la plantilla en el registro",
         "cmd": f"python3 -m sqx.templates.registry --set name={name} "
                f"--set archetype={brief['archetype']} --set status=validated"},
    ]


def save(brief: dict[str, object]) -> str:
    """Write the draft brief where the catalogue's drafts shelf will find it.

    Args:
        brief: The dict `compose` returned.

    Returns:
        The path written, as a string for the client.
    """
    path = template_draft(brief["name"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(brief, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(path)
