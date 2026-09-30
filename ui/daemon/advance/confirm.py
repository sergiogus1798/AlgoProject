"""The confirmation «Continuar workflow» shows before it deletes anything (encargo 22 §7.2)."""


def text(pre: dict, project: str, databank: str) -> str:
    """The literal sentence the owner confirms.

    Args:
        pre: What `preflight.check` returned, ok.
        project: Project name.
        databank: The databank being cut.

    Returns:
        «Se van a borrar N estrategias de <databank> en <proyecto> sobre <install>, y después
        se lanzará <tarea>», N with the Spanish thousands dot; when one identity has several
        files, how many files go, in parentheses after it.
    """
    n = f"{pre['n']:,}".replace(",", ".")
    text = (f"Se van a borrar {n} estrategias de {databank} en {project} sobre "
            f"{pre['install']}, y después se lanzará {pre['task']}")
    if pre["files"] > pre["n"]:
        text += (f" ({pre['files']} ficheros: SQX guarda algunas repetidas con otro nombre, y "
                 "se borran todas las copias)")
    if pre.get("n_out"):
        text += "." + held_note(pre["output"], pre["n_out"])
    return text


def held_note(output: str, held: int) -> str:
    """The warning for a retest whose output databank is not empty.

    Args:
        output: The task's output databank.
        held: The strategies it holds on disk now.

    Returns:
        One sentence: SQX adds the new results beside the old ones — a strategy retested
        again is saved as «Nombre(1)» — unless a «Clear databanks» task empties it first,
        which is the project's configuration and not the window's (📓 2026-09-29).
    """
    return (f"\n⚠ «{output}» ya tiene {held:,} estrategias".replace(",", ".")
            + ": SQX añade las nuevas a su lado (una repetida se guarda como «Nombre(1)») "
            "salvo que una tarea «Clear databanks» del proyecto lo vacíe antes; los "
            "análisis leerán las dos.")
