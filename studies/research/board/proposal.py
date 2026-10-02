#!/usr/bin/env python3
"""A director's proposal: checked, stamped with the board's facts, saved as JSON and Markdown."""

import argparse
import copy
import sys
from datetime import datetime
from pathlib import Path

from studies.research.board import inputs, many, proposalmd, store
from studies.research.board.inputs import CELL

QUARRIES = ("perfil", "libros", "propia")
STEPS = ("leer el tablero", "elegir la celda", "pedir tres ideas al ideaExpert",
         "preparar la paleta de cada idea", "escribir la propuesta")
IDEA_KEYS = ("name", "rule", "mechanism", "direction", "quarry", "palette", "custom_blocks",
             "custodian_hours", "failure", "questions")
STANDING = ("Las supervivientes se parecerán: tres ideas de la misma familia en el mismo mercado "
            "ganan y pierden los mismos años; para la cartera cuentan como poco más de una.",
            "El listón de la celda sube tres ensayos de golpe.")


def check(p: dict) -> list[str]:
    """Why a proposal cannot be accepted as written; empty when it can.

    Args:
        p: The director's draft: `cell`, `diagnosis`, `measures`, `departs` and `ideas`.

    Returns:
        Spanish sentences: not three ideas, a missing field, an idea in another direction than
        its cell (hard rule 13), a palette that draws from the idea's own family or from one
        alike (dossier §5), a question without its readings (hard rule 11).
    """
    out = [f"falta «{k}»" for k in ("cell", "diagnosis", "measures", "ideas") if not p.get(k)]
    if out:
        return out
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
    return out


def open_questions(idea: dict) -> list[dict]:
    """The idea's questions the owner has not answered yet."""
    return [q for q in idea["questions"] if not q.get("answer")]


def launchable(idea: dict) -> tuple[bool, str]:
    """Whether an idea may go to SQX, and why not: vetoed, or a question still open (rule 11)."""
    if idea.get("vetoed"):
        return False, "vetada"
    waiting = len(open_questions(idea))
    return (False, f"{waiting} pregunta(s) sin contestar") if waiting else (True, "")


def stamp(p: dict, board: dict, now: datetime) -> dict:
    """Add what Python knows and the agent must not invent: the id, the cell's place on the
    board, the ideas already spent there, the provisional-costs mark and the two standing costs."""
    key = tuple(p["cell"][c] for c in CELL)
    cell = next((c for c in board["cells"] if tuple(c[k] for k in CELL) == key), None)
    if cell is None:
        sys.exit(f"la celda {' '.join(key)} no está en el tablero: ni la prior la da por Alta ni lo medido la admite")
    return {**p, "id": f"{now:%Y%m%d-%H%M%S}-{key[0]}-{key[1]}-{key[2]}-{key[3]}",
            "created": now.isoformat(timespec="seconds"), "board": cell,
            "ideas_spent": cell["ideas_spent"], "provisional_costs": cell["provisional_costs"],
            "standing_costs": list(STANDING),
            "ideas": [{"vetoed": False, **copy.deepcopy(i)} for i in p["ideas"]]}


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
    problems = check(draft)
    if problems:
        sys.exit("La propuesta no se acepta:\n- " + "\n- ".join(problems))
    board = many.run(inputs.scores(), inputs.memory(), inputs.CONFIG, inputs.sweep())
    p = stamp(draft, board, datetime.now())
    path = save(p)
    print(proposalmd.text(p))
    print(f"\nPROPUESTA: {path}")


if __name__ == "__main__":
    main()
