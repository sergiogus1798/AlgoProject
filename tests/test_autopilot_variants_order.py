"""Step 16.5's order of work: live, every pilot first on the main market alone; restart, as it was."""

import json
from pathlib import Path

import pytest

from pipeline.autopilot import variants


def _ran(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, live_on: bool) -> list[str]:
    """What `variants.run` launches for two mothers, as short words in order."""
    seen = []
    for name in ("A", "B"):
        (tmp_path / f"design_brief_{name}.json").write_text(json.dumps({"strategy": name}))
    monkeypatch.setattr(variants, "briefs", lambda p: sorted(tmp_path.glob("design_brief_*.json")))
    monkeypatch.setattr(variants, "variants_dir", lambda p, m: tmp_path / m)
    monkeypatch.setattr(variants.live, "mine", lambda role: live_on)
    monkeypatch.setattr(variants, "wire",
                        lambda p, r, markets=True: seen.append(f"wire{'' if markets else '-'}"))
    monkeypatch.setattr(variants, "_py", lambda mod, *a: seen.append(
        mod.rsplit(".", 1)[-1] + (".clear" if "--clear" in a else "")))
    variants.run("P", "custodian")
    return seen


def test_live_runs_every_pilot_first_without_the_extra_markets(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Live: the legs without markets, both pilots, the legs rewired, then each batch."""
    mother = ["execute", "equity", "collect", "execute.clear"]
    assert _ran(monkeypatch, tmp_path, True) == [
        "wire-", "make", "make", "wire", *mother, *mother, "mothertrades"]


def test_the_restart_route_keeps_its_order(monkeypatch: pytest.MonkeyPatch,
                                           tmp_path: Path) -> None:
    """Restart: one wiring, then make and its batch mother by mother."""
    mother = ["make", "execute", "equity", "collect", "execute.clear"]
    assert _ran(monkeypatch, tmp_path, False) == ["wire", *mother, *mother, "mothertrades"]
