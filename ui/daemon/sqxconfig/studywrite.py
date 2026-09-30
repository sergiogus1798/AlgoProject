"""One value of a WFC or CSCV study file written from the window, comments kept, the ledger stamped."""

from datetime import date
from math import isclose

from core.assetyaml import read, write
from ui.daemon.sqxconfig import studies
from ui.daemon.sqxconfig.write import coerce

OWNER = "dueño"   # who a write from the window is, in the words the ledger already uses


def _listed(name: str, path: list) -> dict:
    """The field the zone listed at this path, or ValueError: nothing else is written."""
    found = [f for sec in studies.PARTS for f in studies.fields(sec)
             if f["file"] == name and f["path"] == list(path)]
    if not found:
        raise ValueError(f"{name}:{path} no es un valor que esta zona enseñe.")
    return found[0]


def _typed(current: object, new: object) -> object:
    """A number keeps the type the file gives it: a count stays an int, a share a float.

    Args:
        current: What the file holds.
        new: The value coerced from what was typed.

    Returns:
        5000 for «5000.0» where a count stood (5000.5 is refused), 1.0 for «1» where a
        fraction stood — the loaders hold a `--set` override to the type in the file.
    """
    if isinstance(current, bool) or isinstance(new, bool):
        return new
    if isinstance(current, int) and isinstance(new, float):
        if not new.is_integer():
            raise ValueError(f"{new} no es un número entero, y aquí va una cuenta.")
        return int(new)
    if isinstance(current, float) and isinstance(new, int):
        return float(new)
    return new


def _pair(name: str, doc: object, path: list, new: object) -> str:
    """The checks across two values; returns a note for the status line, or raises.

    Args:
        name: The file.
        doc: The file as read, before the write.
        path: What is written.
        new: Its new value.

    Returns:
        "" or the sentence to add to the status line. The strata shares are only warned:
        moving one share breaks the sum until the next one is moved, and refusing would
        make the three impossible to edit one at a time.
    """
    if name == "thresholds" and path[-1] == "value" and doc["thresholds"][path[1]]["key"] == "cscv.blocks":
        if new % 2:
            raise ValueError(f"{new} es impar: el CSCV parte el historial en dos mitades iguales.")
    if name == "sppdesign" and path[-1] in ("min_levels", "max_levels"):
        levels = {**doc["design"], path[-1]: new}
        if levels["min_levels"] > levels["max_levels"]:
            raise ValueError(f"min_levels {levels['min_levels']} quedaría por encima de "
                             f"max_levels {levels['max_levels']}.")
    if (name, path) in (("sppdesign", ["design", "n_target"]), ("variants", ["minimum", "variants"])):
        cap = new if name == "sppdesign" else read(studies.FILES["sppdesign"])["design"]["n_target"]
        floor = new if name == "variants" else read(studies.FILES["variants"])["minimum"]["variants"]
        if cap < floor:
            return f" — ojo: el máximo de variantes ({cap}) queda por debajo del mínimo ({floor})"
    if name == "sppdesign" and path[:2] == ["design", "strata"]:
        total = sum({**doc["design"]["strata"], path[-1]: new}.values())
        if not isclose(total, 1.0):
            return f" — ojo: los tres estratos suman {total:g}, no 1"
    return ""


def _stamp(row: object, old: object, new: object) -> None:
    """A threshold changed from the window says who, when and, proposed, why.

    The proposed why names the date and the value it replaced, so the ledger still tells a
    number set before the results from one moved after them; the owner edits it beside. The
    old why is not quoted inside the new one: nested, it grew by a level at every change.
    """
    today = date.today()
    was = f"{old} (fijado por {row['set_by']} el {row['set_on']})"
    extra = f"{studies.blocks_help(new)}; " if row["key"] == "cscv.blocks" else ""
    row["why"] = f"{extra}cambiado desde la ventana el {today.isoformat()}, antes {was}"
    row["set_by"], row["set_on"] = OWNER, today


def set_field(name: str, path: list, value: object) -> dict:
    """Write one value of one study file, the only line that changes being its own.

    Args:
        name: A key of `studies.FILES`.
        path: As the zone listed it.
        value: What the window sent.

    Returns:
        {file, path, value, where, note, reload}: `where` the file relative to the repo, for
        the status line, `note` what the write implies (a ledger row stamped, a sum off, the
        cap under the floor), and `reload` when other editors now show a stale value.
    """
    if name not in studies.FILES:
        raise ValueError(f"{name} no es un fichero de estudio de esta zona.")
    kind = _listed(name, path)
    file = studies.FILES[name]
    doc = read(file)
    node = doc
    for key in path[:-1]:
        node = node[key]
    old = node[path[-1]]
    if path[-1] == "why":
        # Written as the text typed: through YAML, «no» would become False and «a: b» a map.
        new = str(value).strip()
        if not new:
            raise ValueError("El porqué no puede quedar vacío: es lo que dice por qué el umbral vale eso.")
    else:
        new = _typed(old, coerce(kind, old, value))
    note = _pair(name, doc, list(path), new)
    node[path[-1]] = new
    if name == "thresholds" and path[-1] == "value" and new != old:
        _stamp(node, old, new)
        note += f" — Ledger sellado: {OWNER}, {date.today().isoformat()}; revisa el porqué"
    write(file, doc)
    # A stamp changes the row's why beside it, and `batch` is shown in both sections: the
    # window re-reads the zone so no editor keeps showing what the file no longer says.
    stale = name == "batch" or (name == "thresholds" and path[-1] == "value")
    return {"file": str(file), "path": list(path), "value": new, "reload": stale,
            "where": studies.REL[name], "note": note}
