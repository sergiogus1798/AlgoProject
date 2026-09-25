"""One strategy through the gate, as the contract's data: every screen, its number, where it died."""

import time

import pandas as pd

from core.study import blocks, result as envelope

MODULE = "gate"


def run(identity: str, scores: pd.DataFrame, cfg: dict) -> dict:
    """What every screen measured on one strategy, read off the scorecard.

    Args:
        identity: The strategy's identity, the scorecard's index.
        scores: What cascade.run() returned.
        cfg: What inputs.config() returned.

    Returns:
        The contract dict: MANTENER or DESCARTAR with the screen that decided it, and one
        row per screen. A screen after the one that killed it was not run on it.
    """
    started = time.time()
    r = scores.loc[identity]
    names = [s["name"] for s in cfg["screens"]]
    kind = {s["name"]: s["kind"] for s in cfg["screens"]}
    died = r["died_at"] if isinstance(r["died_at"], str) and r["died_at"] else None

    def state(name: str) -> str:
        """pass, fail, or none for a screen this strategy never reached."""
        got = r[f"{name}_passed"]
        return "none" if pd.isna(got) else "pass" if bool(got) else (
            "fail" if kind[name] == "hard" else "watch")

    parts = [{"label": n, "state": state(n), "value": r[f"{n}_value"],
              "note": r[f"{n}_note"] if isinstance(r[f"{n}_note"], str) else ""}
             for n in names]
    said = blocks.verdict(
        "MANTENER" if r["survives"] else "DESCARTAR", "pass" if r["survives"] else "fail",
        "Pasó todas las cribas duras." if r["survives"] else
        f"Murió en {died}: {r[f'{died}_note']}", None, parts)
    table = blocks.table("Cada criba", pd.DataFrame(
        [[n, kind[n], p["value"], {"pass": "pasa", "fail": "muere", "watch": "avisa",
                                   "none": "no llegó"}[p["state"]], p["note"]]
         for n, p in zip(names, parts)], columns=["criba", "tipo", "valor", "resultado",
                                                  "qué midió"]),
        "Las cribas blandas (familia, redundancia) informan y no eliminan.")
    name = r["strategy"] if isinstance(r["strategy"], str) else r["strategy_build"]
    return envelope.envelope(MODULE, name, identity, cfg, started,
                             [envelope.tab("screens", "Las cribas, una a una", [table])], said,
                             summary={"survives": bool(r["survives"]), "died_at": died or ""})
