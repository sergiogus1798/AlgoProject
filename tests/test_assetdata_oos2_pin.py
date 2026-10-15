"""T-2: a run that pinned oos2 keeps its `to` when the monthly roll moves the policy."""

import json
from datetime import date

import pytest

from core import assetdata


def test_pin_keeps_the_window_the_run_started_with(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """After `pin_oos2`, a policy that now says another `to` is not what `load` returns."""
    monkeypatch.setenv(assetdata.OOS2_PIN, "{}")
    now = assetdata.load("XAUUSD")["segments"]["oos2"]["to"]
    assetdata.pin_oos2("XAUUSD")
    later = {"XAUUSD": "2099-01-31"}
    assert assetdata.load("XAUUSD")["segments"]["oos2"]["to"] == now
    monkeypatch.setenv(assetdata.OOS2_PIN, json.dumps(later))
    assert assetdata.load("XAUUSD")["segments"]["oos2"]["to"] == date(2099, 1, 31)
