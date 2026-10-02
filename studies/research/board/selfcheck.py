#!/usr/bin/env python3
"""The profile examines itself: did high-score cells give more survivors than low-score ones?"""

import pandas as pd
from scipy.stats import fisher_exact

from studies.research.board import inputs, store
from studies.research.board.inputs import CELL
from studies.research.memory import queries


def closed_runs(attempts: list[dict], scores: pd.DataFrame) -> pd.DataFrame:
    """Every closed attempt with the profile score of its cell.

    Returns:
        Columns `project`, the cell, `score`, `survived` (bool). Dev draws, failed, incomplete
        and unknown runs are left out, and so is a run whose cell the profile never measured.
    """
    rows = [{"project": a["project"], **dict(zip(CELL, queries.cell(a))),
             "survived": a["outcome"] == "survivors"}
            for a in attempts if queries.conclusive(a, include_dev=False)]
    frame = pd.DataFrame(rows, columns=["project", *CELL, "survived"])
    return frame.merge(scores[[*CELL, "score"]], on=CELL)


def judge(runs: pd.DataFrame, cfg: dict) -> dict:
    """The decision: keep the profile's weight on the board, or reduce it.

    High and low are the two halves of the closed runs around their median score. The profile
    is kept when the high half survived more often; the Fisher p says how sure that is. The
    cost is what following the profile (running only the high half) would have saved in runs
    and lost in runs that did give survivors.

    Args:
        runs: `closed_runs`.
        cfg: The config's `selfcheck` section.

    Returns:
        `enough` False with `closed` and `needed` when there are too few runs; otherwise the
        two rates, `p`, `decision` (`mantener` | `reducir`), `runs_saved`, `survivor_runs_lost`.
    """
    if len(runs) < cfg["min_closed"]:
        return {"enough": False, "closed": int(len(runs)), "needed": cfg["min_closed"]}
    high = runs["score"] > runs["score"].median()
    table = [[int((high & runs["survived"]).sum()), int((high & ~runs["survived"]).sum())],
             [int((~high & runs["survived"]).sum()), int((~high & ~runs["survived"]).sum())]]
    rate_high = table[0][0] / max(sum(table[0]), 1)
    rate_low = table[1][0] / max(sum(table[1]), 1)
    p = float(fisher_exact(table, alternative="greater")[1])
    return {"enough": True, "closed": int(len(runs)), "median_score": float(runs["score"].median()),
            "high": {"runs": sum(table[0]), "with_survivors": table[0][0], "rate": rate_high},
            "low": {"runs": sum(table[1]), "with_survivors": table[1][0], "rate": rate_low},
            "p": p, "proven": p <= cfg["alpha"],
            "decision": "mantener" if rate_high > rate_low else "reducir",
            "runs_saved": sum(table[1]), "survivor_runs_lost": table[1][0]}


def text(got: dict, weight: float) -> str:
    """The reading in Spanish, ending in the decision and its cost."""
    if not got["enough"]:
        return (f"Examen del perfil: hay {got['closed']} corridas cerradas y hacen falta "
                f"{got['needed']}. Todavía no se puede saber si el perfil orienta; el peso de la "
                f"señal en el tablero se queda en {weight:.2f}.")
    h, low = got["high"], got["low"]
    sure = "probado" if got["proven"] else "sin probar: la diferencia cabe en el azar"
    what = (f"MANTENER el peso de la señal ({weight:.2f})" if got["decision"] == "mantener" else
            f"REDUCIR el peso de la señal: de {weight:.2f} a {weight / 2:.2f} en "
            "studies/research/board/config.yaml (weights.signal)")
    return "\n".join([
        f"Examen del perfil sobre {got['closed']} corridas cerradas, partidas por la puntuación "
        f"mediana ({got['median_score']:.1f}):",
        f"  puntuación alta: {h['with_survivors']}/{h['runs']} dieron supervivientes "
        f"({h['rate']:.0%})",
        f"  puntuación baja: {low['with_survivors']}/{low['runs']} dieron supervivientes "
        f"({low['rate']:.0%})",
        f"  p de Fisher (una cola, alta > baja): {got['p']:.3f} — {sure}.",
        f"Decisión: {what}.",
        f"Coste de haber seguido el perfil (sólo la mitad alta): {got['runs_saved']} corridas "
        f"ahorradas, {got['survivor_runs_lost']} corridas con supervivientes perdidas."])


def main() -> None:
    """Judge the closed runs, print the reading, leave it as selfcheck.json."""
    cfg = inputs.CONFIG
    got = judge(closed_runs(inputs.memory()["attempts"], inputs.scores()), cfg["selfcheck"])
    store.write(store.board_dir() / "selfcheck.json", got)
    print(text(got, cfg["weights"]["signal"]))


if __name__ == "__main__":
    main()
