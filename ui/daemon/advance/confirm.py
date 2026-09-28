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
    return text
