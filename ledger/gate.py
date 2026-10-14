"""The one-way door: who may look at a reserved segment, and when 17-19 may be read.

Shut only for an agent that decides alone. Owner, 2026-09-28: a human -- at the window, at a
terminal, or steering a session -- may look at any segment at any time; whether an autonomous
agent that makes the development decisions should still be held to the door is left open, so
the door stays built and such an agent opts in by setting `ALGO_AUTONOMOUS=1`.
"""

import hashlib
import json

import pandas as pd
import yaml

from core import assetdata
from core.paths import DATA, ROOT

# Which workflow step each name in `_policy.yaml`'s `reserved_for` refers to. The policy
# file names tests, not numbers, and the numbers are what a caller has. A name here that the
# policy does not list is refused on the reserved segment all the same: `BlindJoint` (step 20's
# SPA on oos2) is only the word the owner would add, not a permission.
STEPS = {
    "WFC": 17,
    "CSCV": 18,
    "MarketSurfaces": 18.5,
    "WFM": 19,
    "BlindJoint": 20,
    "ATRStop": 24,
}
BLIND = (17, 18, 19)
AUTONOMOUS = assetdata.AUTONOMOUS
enforced = assetdata.enforced  # the door is shut only for an autonomous agent
# `seal` (encargo 48): the seal inside the study, shut for everyone, human or not.
CRITERIA = ROOT / "pipeline" / "autopilot" / "criteria.yaml"
CALIBRATION = DATA / "ledger" / "wfc_calibration.json"
JUDGED = (
    17,
)  # the steps whose reading of a reserved segment needs a written, calibrated criterion


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
    return {
        name: [STEPS[t] for t in spec["reserved_for"]]
        for name, spec in segments.items()
        if spec.get("reserved_for")
    }


def allow(step: float, segment: str, symbol: str) -> None:
    """Refuse a search that would spend a segment it has no claim on.

    Args:
        step: Workflow step, 1 to 25.
        segment: The segment the search reads -- "build", "oos1", "oos2", or several joined by
            "+" ("oos1+oos2", step 26).
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
    held = reserved(symbol)
    for part in segment.split(
        "+"
    ):  # step 26 reads "oos1+oos2": any reserved part binds
        allowed = held.get(part)
        if allowed is not None and step not in allowed:
            names = [n for n, s in STEPS.items() if s in allowed]
            raise PermissionError(
                f"ledger: el paso {step} no puede mirar `{part}` de {symbol}: está "
                f"reservado para {', '.join(names)}. Cada mirada lo gasta "
                f"(assets/_policy.yaml, WORKFLOW.md §la puerta de un solo sentido)"
            )


def criteria_hash(step: dict | None) -> str:
    """sha256 of a canonical dump of one `criteria.yaml` entry: the value the calibration signs."""
    return hashlib.sha256(
        json.dumps(step, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def seal(step: float, segment: str, symbol: str) -> None:
    """Refuse a read of a reserved segment unless the step may and its criterion is written and calibrated.

    Args:
        step: Workflow step, as in `allow`.
        segment: The segment read, or several joined by "+".
        symbol: The asset.

    Raises:
        PermissionError: A part of `segment` is reserved and (a) this step is not in its
            `reserved_for`, or (b) the step is in `JUDGED` and `criteria.yaml` has no rules for
            it, or `CALIBRATION` is missing, was written for another entry "17" (`criteria_hash`) or has `abre` other than true.

        Unlike `allow` this does not look at `ALGO_AUTONOMOUS`: a human is shut out too, until
        the owner's rule is written and measured against a null (owner, 2026-10-07).
    """
    held = reserved(symbol)
    for part in segment.split("+"):
        allowed = held.get(part)
        if allowed is None:
            continue
        if step not in allowed:
            raise PermissionError(
                f"ledger: el paso {step} no puede mirar `{part}` de {symbol}: "
                f"no está en su reserva (assets/_policy.yaml)"
            )
        if step not in JUDGED:
            continue
        entry = (
            yaml.safe_load(CRITERIA.read_text(encoding="utf-8"))
            .get("steps", {})
            .get(str(int(step)), {})
            or {}
        )
        rules = entry.get("rules")
        if not rules:
            raise PermissionError(
                f"ledger: `{part}` sellado: criteria.yaml no tiene regla "
                f"para el paso {step}"
            )
        found = (
            json.loads(CALIBRATION.read_text(encoding="utf-8"))
            if CALIBRATION.exists()
            else {}
        )
        if found.get("criteria_sha256") != criteria_hash(entry):
            raise PermissionError(
                f"ledger: `{part}` sellado: no hay calibración registrada para "
                f"este criteria.yaml ({CALIBRATION})"
            )
        if found.get("abre") is not True:
            raise PermissionError(
                f"ledger: `{part}` sellado: la calibración registrada el "
                f"{found.get('fecha')} no abre el bloque (abre: false)"
            )


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
            f"decisión de correrlo, y el oos2 es la última bala"
        )
