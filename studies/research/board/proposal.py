#!/usr/bin/env python3
"""A director's proposal: checked, stamped with the board's facts, saved as JSON and Markdown."""

import argparse
import copy
import sys
from datetime import datetime
from pathlib import Path

from studies.research.board import inputs, many, proposalmd, store
from studies.research.board.inputs import CELL
from studies.research.memory import queries, sheet

QUARRIES = ("perfil", "libros", "propia")
STEPS = ("leer el tablero", "elegir la celda", "pedir tres ideas al ideaExpert",
         "pasar las tres ideas por el ideaReviewer", "preparar la paleta de cada idea",
         "escribir la propuesta")
IDEA_KEYS = ("name", "rule", "mechanism", "direction", "quarry", "palette", "custom_blocks",
             "custodian_hours", "failure", "questions", "sheet", "review")
PROPOSERS = ("ideaExpert", "researchDirector")
VERDICTS = ("resiste", "dudosa", "tumbada")
AXES = ("mechanism", "cost", "similarity", "ambiguity")
STANCES = ("adopta", "rechaza")
REMOVES = inputs.MEMORY["review"]["removes"]
STANDING = ("Las supervivientes se parecerán: tres ideas de la misma familia en el mismo mercado "
            "ganan y pierden los mismos años; para la cartera cuentan como poco más de una.",
            "El listón de la celda sube tres ensayos de golpe.")


def reviewed(idea: dict) -> list[str]:
    """Why an idea's review is not one: no verdict of the three, or an axis left unsaid."""
    got = idea.get("review") or {}
    out = [] if got.get("verdict") in VERDICTS else [f"la revisión dice una de {', '.join(VERDICTS)}"]
    return out + [f"la revisión no dice nada de «{k}»" for k in AXES if not str(got.get(k, "")).strip()]


def stances(p: dict, attempts: list[dict]) -> list[str]:
    """The cell's closed failures the draft neither adopts nor rejects with a reason."""
    said = {f.get("project"): f for f in p["prior_failures"]}
    owed = queries.failures(attempts, *(p["cell"][c] for c in CELL))
    return [f"el fracaso previo de {a['project']} ({a['cause']}) ni se adopta ni se rechaza por escrito"
            for a in owed if said.get(a["project"], {}).get("stance") not in STANCES
            or not str(said[a["project"]].get("why", "")).strip()]


def check(p: dict, attempts: list[dict] = ()) -> list[str]:
    """Why a proposal cannot be accepted as written; empty when it can.

    Args:
        p: The director's draft: `cell`, `diagnosis`, `measures`, `departs`, `reviewer`,
            `prior_failures` and `ideas`.
        attempts: The memory's attempts table: the cell's closed failures come from it.

    Returns:
        Spanish sentences: not three ideas, a missing field, an idea in another direction than
        its cell (hard rule 13), a palette that draws from the idea's own family or from one
        alike (dossier §5), a question without its readings (hard rule 11), an idea without
        its hypothesis sheet or without its review, a reviewer that is the proposer, a
        previous failure of the cell left without a written stance.
    """
    out = [f"falta «{k}»" for k in ("cell", "diagnosis", "measures", "ideas") if not p.get(k)]
    out += ["falta «prior_failures» (vacío si la celda no tiene fracasos cerrados)"] \
        if "prior_failures" not in p else []
    if out:
        return out
    if not p.get("reviewer") or p["reviewer"] in PROPOSERS:
        out.append("sin revisión: «reviewer» nombra a quien revisó, y no es quien propone")
    out += stances(p, attempts)
    ideas = p["ideas"]
    if len(ideas) != 3 or len({i.get("name") for i in ideas}) != 3:
        out.append("tienen que ser tres ideas con nombres distintos")
    rules = inputs.CONFIG["palette"]
    fixed = inputs.CONFIG["taxonomy_family"][p["cell"]["family"]]
    banned = {fixed} | (set(rules["alike"]) if fixed in rules["alike"] else set())
    for i in ideas:
        name = i.get("name", "?")
        out += [f"{name}: falta «{k}»" for k in IDEA_KEYS if k not in i]
        if i.get("direction") != p["cell"]["direction"]:
            out.append(f"{name}: una sola dirección por plantilla, la de la celda "
                       f"({p['cell']['direction']})")
        if i.get("quarry") not in QUARRIES:
            out.append(f"{name}: la cantera es una de {', '.join(QUARRIES)}")
        same = banned & {f["family"] for f in i.get("palette", {}).get("families", [])}
        if same:
            out.append(f"{name}: la paleta usa {', '.join(sorted(same))}, igual que la condición "
                       "fija (§5: nunca dos iguales)")
        out += [f"{name}: una pregunta sin sus lecturas" for q in i.get("questions", [])
                if len(q.get("readings", [])) < 2]
        out += [f"{name}: {why}" for why in sheet.problems(i.get("sheet") or {}) + reviewed(i)]
    return out


def open_questions(idea: dict) -> list[dict]:
    """The idea's questions the owner has not answered yet."""
    return [q for q in idea["questions"] if not q.get("answer")]


def launchable(idea: dict) -> tuple[bool, str]:
    """Whether an idea may go to SQX, and why not: vetoed, a question still open (rule 11), or
    knocked down by the reviewer when `review.removes` lets its verdict take an idea out."""
    if idea.get("vetoed"):
        return False, "vetada"
    if REMOVES and idea.get("review", {}).get("verdict") == VERDICTS[-1]:
        return False, "tumbada por el revisor"
    waiting = len(open_questions(idea))
    return (False, f"{waiting} pregunta(s) sin contestar") if waiting else (True, "")


def stamp(p: dict, board: dict, now: datetime) -> dict:
    """Add what Python knows and the agent must not invent: the id, the cell's place on the
    board, the ideas already spent there, the provisional-costs mark, the two standing costs,
    each sheet's seal and whether the reviewer's verdict removes an idea or only annotates it."""
    key = tuple(p["cell"][c] for c in CELL)
    cell = next((c for c in board["cells"] if tuple(c[k] for k in CELL) == key), None)
    if cell is None:
        sys.exit(f"la celda {' '.join(key)} no está en el tablero: ni la prior la da por Alta ni lo medido la admite")
    return {**p, "id": f"{now:%Y%m%d-%H%M%S}-{key[0]}-{key[1]}-{key[2]}-{key[3]}",
            "created": now.isoformat(timespec="seconds"), "board": cell,
            "ideas_spent": cell["ideas_spent"], "provisional_costs": cell["provisional_costs"],
            "standing_costs": list(STANDING), "review_removes": REMOVES,
            "ideas": [{"vetoed": False, **copy.deepcopy(i),
                       **({"sheet_seal": sheet.seal(i["sheet"])} if "sheet" in i else {})}
                      for i in p["ideas"]]}


def save(p: dict) -> Path:
    """Write `<id>.json` and `<id>.md` under the proposals folder; returns the JSON's path."""
    out = store.proposals_dir()
    (out / f"{p['id']}.md").write_text(proposalmd.text(p), encoding="utf-8")
    return store.write(out / f"{p['id']}.json", p)


def listing() -> list[str]:
    """Every saved proposal's id, newest first."""
    return sorted((f.stem for f in store.proposals_dir().glob("*.json")
                   if f.stem[:8].isdigit()), reverse=True)


def load(proposal_id: str) -> dict:
    """One saved proposal."""
    return store.read(store.proposals_dir() / f"{proposal_id}.json")


def step(n: int, note: str) -> None:
    """Record which of the director's five steps is running, for the window."""
    store.write(store.proposals_dir() / "estado.json",
                {"step": n, "of": len(STEPS), "name": STEPS[n - 1], "note": note,
                 "at": datetime.now().isoformat(timespec="seconds")})


def own_idea_files(draft: dict) -> tuple:
    """`<SYMBOL>/<file>.md` of the idea files the draft's ideas came from."""
    return tuple("/".join(Path(i["idea_file"]).parts[-2:]) for i in draft.get("ideas", [])
                 if i.get("idea_file"))


def main() -> None:
    """Accept a draft (check, stamp, save, print its Markdown), or record the director's step."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("draft", nargs="?", type=Path, help="el borrador JSON del director")
    ap.add_argument("--step", type=int, choices=range(1, len(STEPS) + 1))
    ap.add_argument("--note", default="", help="con --step: una línea de lo que se decidió")
    a = ap.parse_args()
    if a.step:
        step(a.step, a.note)
        print(f"paso {a.step}/{len(STEPS)}: {STEPS[a.step - 1]}")
        return
    draft = store.read(a.draft)
    memory = inputs.memory(own_idea_files(draft))
    problems = check(draft, memory["attempts"])
    if problems:
        sys.exit("La propuesta no se acepta:\n- " + "\n- ".join(problems))
    board = many.run(inputs.scores(), memory, inputs.CONFIG, inputs.sweep())
    p = stamp(draft, board, datetime.now())
    path = save(p)
    print(proposalmd.text(p))
    print(f"\nPROPUESTA: {path}")


if __name__ == "__main__":
    main()
