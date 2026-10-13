"""Where a run's wall clock went: `fases.csv` (`core.phases`) folded into one row per action, SQX apart from everything around it."""

from pathlib import Path

import pandas as pd

from core.phases import COLUMNS

# A phase's own seconds (its children taken out) go to one column; a name not listed is `resto`:
# the Python of the action itself — the studies, the judge, the configurators.
BUCKETS = {"sqx": "sqx", "start": "arranque", "ready": "arranque", "stop": "parada",
           "sync": "sync", "snapshot": "copias", "restore": "copias", "compare": "copias",
           "fill": "copias", "execute.sqx": "sqx", "execute.sync": "sync"}
ORDER = ["sqx", "arranque", "parada", "export", "sync", "copias", "resto"]
SLACK = 0.05    # s: a child written by a subprocess may end a hair after its parent's clock


def own(rows: pd.DataFrame) -> pd.DataFrame:
    """Each phase with its direct children's seconds taken out, and the action it ran inside.

    Args:
        rows: `fases.csv` — began (epoch s), seconds, phase, detail, pid.

    Returns:
        The same rows by start, plus `own` (s), `bucket` and `action` (the detail of the
        enclosing `accion` row).
    """
    rows = rows.sort_values(["began", "seconds"], ascending=[True, False]).reset_index(drop=True)
    end = rows["began"] + rows["seconds"]
    parent = []
    for i in rows.index:
        inside = [j for j in rows.index[:i] if end[j] + SLACK >= end[i]]
        parent.append(inside[-1] if inside else -1)
    rows["own"] = rows["seconds"] - rows["seconds"].groupby(parent).sum().reindex(
        rows.index, fill_value=0.0)
    top = []
    for i, p in enumerate(parent):
        top.append(i if p == -1 else top[p])
    rows["action"] = rows["detail"].iloc[top].to_numpy()
    rows["bucket"] = [("export" if name.startswith("export") else BUCKETS.get(name, "resto"))
                      for name in rows["phase"]]
    return rows


def table(csv: Path) -> str:
    """The markdown the autopilot writes as `tiempos.md`: one row per action, seconds per
    column, the total, and the twelve largest single phases."""
    rows = own(pd.read_csv(csv, names=COLUMNS))
    wide = rows.pivot_table(index="action", columns="bucket", values="own", aggfunc="sum",
                            fill_value=0.0, sort=False).reindex(columns=ORDER, fill_value=0.0)
    wide.loc["TOTAL"] = wide.sum()
    lines = ["| acción | total | " + " | ".join(ORDER) + " |", "|---|" + "---|" * (len(ORDER) + 1)]
    lines += [f"| {name} | {r.sum():.0f} | " + " | ".join(f"{v:.0f}" for v in r) + " |"
              for name, r in wide.iterrows()]
    total = wide.loc["TOTAL"]
    big = rows[rows["phase"] != "accion"].nlargest(12, "own")
    return "\n".join(
        [f"# Tiempos · {csv.parent.parent.name} · {csv.parent.name}", "",
         "Segundos de reloj. `sqx` es SQX calculando (de `action=start` a «Project finished»); "
         "el resto de columnas es todo lo demás.", "", *lines, "",
         f"SQX {total['sqx'] / 60:.1f} min · todo lo demás "
         f"{(total.sum() - total['sqx']) / 60:.1f} min "
         f"({100 * (1 - total['sqx'] / total.sum()):.0f} % del total).", "",
         "## Las doce fases más largas", "", "| acción | fase | cuál | s |", "|---|---|---|---|",
         *(f"| {r.action} | {r.phase} | {r.detail} | {r.own:.0f} |" for r in big.itertuples()),
         ""])
