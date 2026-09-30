"""The one-way door: who may look at a reserved segment, and when 17-19 may be read.

Shut only for an agent that decides alone. Owner, 2026-09-28: a human -- at the window, at a
terminal, or steering a session -- may look at any segment at any time; whether an autonomous
agent that makes the development decisions should still be held to the door is left open, so
the door stays built and such an agent opts in by setting `ALGO_AUTONOMOUS=1`.
"""

import pandas as pd

from core import assetdata

# Which workflow step each name in `_policy.yaml`'s `reserved_for` refers to. The policy
# file names tests, not numbers, and the numbers are what a caller has. A name here that the
# policy does not list is refused on the reserved segment all the same: `BlindJoint` (step 20's
# SPA on oos2) is only the word the owner would add, not a permission.
STEPS = {"WFC": 17, "CSCV": 18, "MarketSurfaces": 18.5, "WFM": 19, "BlindJoint": 20,
         "ATRStop": 24}
BLIND = (17, 18, 19)
AUTONOMOUS = assetdata.AUTONOMOUS
enforced = assetdata.enforced      # the door is shut only for an autonomous agent


def reserved(symbol: str) -> dict[str, list[int]]:
    """Which segments this asset reserves, and for which steps.

    Args:
        symbol: Asset as `assets/symbols/` spells it.

    Returns:
        {segment: allowed steps}. Read from `assets/_policy.yaml` every call rather than
        cached: the reservation is the owner's declaration and a stale copy of it is worse
        than none.
    """
    segments = assetdata.load(symbol)["segments"]
    return {name: [STEPS[t] for t in spec["reserved_for"]]
            for name, spec in segments.items() if spec.get("reserved_for")}


def allow(step: int, segment: str, symbol: str) -> None:
    """Refuse a search that would spend a segment it has no claim on.

    Args:
        step: Workflow step, 1 to 25.
        segment: The segment the search reads -- "build", "oos1", "oos2".
        symbol: The asset.

    Raises:
        PermissionError: Only under `enforced()`: the segment is reserved and this step is
            not one it is reserved for. A human is never refused; the row is still written,
            so the ledger keeps counting how often each segment was read.

        ⚠️ The policy names the tests, so a step not listed there is refused even when it
        seems harmless. If the CSCV should be allowed to read the reserved stretch, the
        fix is to add it to `reserved_for` in `_policy.yaml`, which is the owner's file --
        not to widen this check.
    """
    if not enforced():
        return
    allowed = reserved(symbol).get(segment)
    if allowed is not None and step not in allowed:
        names = [n for n, s in STEPS.items() if s in allowed]
        raise PermissionError(
            f"ledger: el paso {step} no puede mirar `{segment}` de {symbol}: está "
            f"reservado para {', '.join(names)}. Cada mirada lo gasta "
            f"(assets/_policy.yaml, WORKFLOW.md §la puerta de un solo sentido)")


def done(frame: pd.DataFrame) -> dict[int, bool]:
    """Which of the three blind steps this study has actually run.

    Args:
        frame: What `study.read` returned.

    Returns:
        {step: whether it has a row}. Presence in the ledger is the definition of "run":
        a step that produced results without recording them did not happen, as far as
        anything downstream is concerned.
    """
    seen = set(frame["step"]) if len(frame) else set()
    return {step: step in seen for step in BLIND}


def allow_read(frame: pd.DataFrame) -> None:
    """Refuse to serve 17, 18 and 19 until all three have been run.

    Args:
        frame: What `study.read` returned.

    Raises:
        PermissionError: Only under `enforced()`: one of them is missing.

        The owner's rule of 2026-09-23, lifted for humans on 2026-09-28: reading the correlation and the CSCV before
        deciding whether to run the matrix contaminates that decision, and the matrix is
        the only test left with untouched data behind it. So step 20 is blind by
        construction, not by discipline.
    """
    if not enforced():
        return
    pending = [step for step, ran in done(frame).items() if not ran]
    if pending:
        raise PermissionError(
            f"ledger: el paso 20 es ciego hasta que 17, 18 y 19 estén los tres hechos; "
            f"faltan {pending}. Mirar dos antes de correr el tercero contamina la "
            f"decisión de correrlo, y el oos2 es la última bala")
