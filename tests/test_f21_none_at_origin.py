"""Encargo 68 F21: a value that can be missing raises (or refuses) where it goes missing, with what to run."""

from pathlib import Path
from typing import Any

import pytest

from core import assetdata
from pipeline.autopilot import survivors
from sqx.databank import find
from studies.research.profilePower import one as power
from ui.daemon.launch import liverun
from ui.daemon.portfolios import correlation
from ui.daemon.results import catalogue
from ui.daemon.runner import table
from ui.daemon.strategy import archive_view
from ui.daemon.workflow import run as wrun


def test_study_of_without_template_says_which_project(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A project with no template has no family to sign the ledger under."""
    monkeypatch.setattr(
        survivors,
        "about",
        lambda p: {"symbol": "X", "timeframe": "H1", "feed": "X_M1", "family": None},
    )
    with pytest.raises(ValueError, match="Test_none"):
        survivors.study_of("Test_none")


def test_profile_power_without_draws_raises() -> None:
    """No draws left no first chunk, and the old code crashed on `cast(dict, None)`."""
    with pytest.raises(ValueError, match="leave no chunk"):
        power.tested(
            {},
            {},
            {"nulls": {"draws": 0}},
            {},
            "long",
            {"cut": 0.05, "chunk": 10},
            5,
            None,
        )  # type: ignore[arg-type]


def test_pair_without_universe_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """The route turns the error into its callout; the assert it replaces was a 500 under -O."""
    monkeypatch.setattr(correlation, "universe", lambda pool, firm: (None, None))
    with pytest.raises(FileNotFoundError, match="Calcular parejas"):
        correlation.pair("p", "a", "b")


def test_gate_without_harvest_is_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """No harvest folder means no gate report judged it."""
    monkeypatch.setattr(archive_view.harvest, "newest", lambda project, databank: None)
    assert archive_view.gate("P", "B", "i", "2026-01-01") is None


def test_top_of_unknown_databank_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """An unknown databank names itself instead of a TypeError on None[1]."""
    monkeypatch.setattr(find, "install_of", lambda project, databank: None)
    with pytest.raises(FileNotFoundError, match="Test_x / Bank"):
        find.top_of("Test_x", "Bank")


def test_role_by_config_without_config_raises() -> None:
    """blindJoint's role is read from its config; none given is an error, not a TypeError."""
    with pytest.raises(ValueError, match="blindJoint"):
        catalogue.role("blindJoint", None)


def test_symbol_of_unknown_feed_names_it() -> None:
    """The feed and the files to check, not a None handed to `assetdata.load`."""
    with pytest.raises(ValueError, match="NO_SUCH_M1"):
        assetdata.symbol_of("NO_SUCH_M1")


def test_plan_without_asset_refuses(monkeypatch: pytest.MonkeyPatch) -> None:
    """A one-strategy study over a databank needs the asset: the rail gets a sentence."""
    monkeypatch.setattr(
        table, "STUDIES", {"k": {"plan": 1, "many": False, "one": True}}
    )
    ctx: Any = {"project": "Test_a", "asset": None, "blind": {"sealed": False}}
    got = wrun.plan({"n": "7", "feeds": "x"}, "k", ctx, "Bank", [])
    assert isinstance(got, str) and "activo" in got


def test_close_failed_with_unreadable_project_raises(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A refusal from `preflight.tasks` was read as a listing; now it stops with its reason."""
    monkeypatch.setattr(liverun.exiting, "stop", lambda role, project: "stopped")
    monkeypatch.setattr(liverun.live, "stop", lambda role, export=False: None)
    monkeypatch.setattr(
        liverun.preflight, "tasks", lambda project: {"refuse": "no está en w1"}
    )
    with pytest.raises(RuntimeError, match="no está en w1"):
        liverun.close("w1", "Test_a", {"n": "6", "steps": [], "since": 0.0})
