"""Step 13's T1 chain in the autopilot: its order on both routes, and the refusal of a reserved leg."""

from pathlib import Path

import pandas as pd
import pytest

from pipeline.autopilot import neighbours

LEGS = ["WFC 1 IS", "WFC 2 OOS1"]


def _ran(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    live_on: bool,
    legs: list[str] = LEGS,
) -> list[str]:
    """What `neighbours.run` launches for one mother, as short words in order."""
    seen = []
    monkeypatch.setattr(neighbours, "DATA", tmp_path)
    monkeypatch.setattr(
        neighbours.survivors,
        "about",
        lambda p: {
            "symbol": "XAUUSD",
            "timeframe": "H1",
            "feed": "XAUUSD_M1",
            "family": None,
        },
    )
    monkeypatch.setattr(
        neighbours.inputs, "load", lambda: {"neighbours": {"legs": legs}}
    )
    monkeypatch.setattr(neighbours.closing, "copies", lambda mothers, folder: folder)
    monkeypatch.setattr(neighbours.live, "mine", lambda role: live_on)
    monkeypatch.setattr(
        neighbours.variants,
        "wire",
        lambda p, r, markets=True: seen.append(f"wire{'' if markets else '-'}"),
    )
    monkeypatch.setattr(
        neighbours.stage, "just", lambda cfx, on: seen.append("just " + "+".join(on))
    )
    monkeypatch.setattr(
        neighbours.call,
        "run",
        lambda argv: seen.append(
            argv[1].rsplit(".", 1)[-1]
            + (
                " retest"
                if "--work" in argv
                and "--out" not in argv
                and "neighbourbatch" in argv[1]
                else ""
            )
        ),
    )
    monkeypatch.setattr(neighbours.projdisk, "snapshot", lambda folder: folder)
    monkeypatch.setattr(neighbours.projdisk, "counts", lambda folder: {})
    monkeypatch.setattr(neighbours.projdisk, "compare", lambda *a: "nada perdido")
    monkeypatch.setattr(
        neighbours.closing,
        "export",
        lambda p, r, tag, banks: seen.append(f"export {tag} " + "+".join(banks)),
    )
    monkeypatch.setattr(neighbours.closing, "clear", lambda p: seen.append("clear"))
    said = neighbours.run(
        "P", "custodian", pd.DataFrame([{"strategy": "S", "file": "S.sqx"}]), "stamp"
    )
    assert all(
        f"{phase} " in said for phase in ("make", "execute", "export", "measure")
    )
    return seen


def test_restart_route_stages_the_two_legs_and_never_exports_oos2(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Rule 5, the legs without markets, only two switched on, then make → retest → export → measure → clear."""
    assert _ran(monkeypatch, tmp_path, False) == [
        "assets",
        "wire-",
        "just WFC 1 IS+WFC 2 OOS1",
        "neighbourbatch",
        "neighbourbatch retest",
        "export neighbours WFC_Build+WFC_OOS1",
        "t1",
        "clear",
    ]


def test_live_route_leaves_the_task_flags_alone(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Live, the start's own projectXML picks the legs: nothing is staged on the file."""
    assert "just WFC 1 IS+WFC 2 OOS1" not in _ran(monkeypatch, tmp_path, True)


def test_a_reserved_leg_is_refused_before_anything_runs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """`WFC 3 OOS2` in `neighbours.legs` stops the step: oos2 is reserved."""
    with pytest.raises(SystemExit, match="WFC 3 OOS2"):
        _ran(monkeypatch, tmp_path, False, [*LEGS, "WFC 3 OOS2"])
