#!/usr/bin/env python3
"""A Simple Strategy carries its idea family (owner, 2026-10-12): the refusal, the registry column,
an old registry without it, `_family` resolving, the resume command passing it."""

import csv
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import assetmarkets
from pipeline.autopilot.resume import builder_argv
from sqx.projects import registry
from studies.research.memory import sources

OLD = [
    "name",
    "kind",
    "install",
    "created",
    "purpose",
    "symbol",
    "timeframe",
    "template",
    "workflow",
    "retired",
    "archive",
    "acceptance",
]
DONE = {
    "project": "Test_new",
    "install": "SQX_w2",
    "timeframe": "H1",
    "acceptance": {"mode": "m", "sample": "s", "conditions": []},
}


def fake(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A registry file in the pre-family shape, both readers pointed at it."""
    path = tmp_path / "registry.csv"
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=OLD)
        w.writeheader()
        w.writerow(
            {
                "name": "Test_old",
                "install": "SQX_w2",
                "template": "simple:long",
                "symbol": "X",
            }
        )
    monkeypatch.setattr(registry, "project_registry", lambda: path)
    monkeypatch.setattr(sources, "project_registry", lambda: path)
    return path


def test_refusal_lists_the_table_and_acceptance_reads_it() -> None:
    """A missing or unknown family is refused with the valid values; every table row is accepted."""
    for bad in (None, "", "ruptura"):
        msg = registry.check_family(bad)
        assert msg and all(k in msg for k in assetmarkets.expected_sign())
    assert all(registry.check_family(k) is None for k in assetmarkets.expected_sign())
    assert "breakout" in assetmarkets.expected_sign()


def test_old_row_without_the_column_reads_and_survives_a_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An old file reads (no `family` key); the next record adds the column, old rows empty."""
    path = fake(tmp_path, monkeypatch)
    assert "family" not in registry.rows()[0] and sources.family_of("Test_old") == ""
    registry.record(DONE, "p", "X", "simple:long", "breakout")
    by = {r["name"]: r for r in registry.rows()}
    assert by["Test_old"]["family"] == "" and by["Test_new"]["family"] == "breakout"
    assert path.read_text().splitlines()[0].endswith(",family")


def test_family_resolves_from_the_registry_when_there_is_no_template(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Template archetype first, else the registry's family, else none."""
    fake(tmp_path, monkeypatch)
    registry.record(DONE, "p", "X", "simple:long", "breakout")
    assert (
        sources.family_of("Test_new") == "breakout"
        and sources.family_of("Test_unknown") == ""
    )
    monkeypatch.setattr(sources, "templates", lambda: {"t1": {"archetype": "momentum"}})
    registry.record(
        {**DONE, "project": "Test_tpl"},
        "p",
        "X",
        "/x/templates/library/t1/template.sqx",
    )
    assert sources.family_of("Test_tpl") == "momentum"


def test_resume_passes_the_family() -> None:
    """store-resume rebuilds a Simple Strategy with the family its row holds."""
    row = {
        "template": "simple:long",
        "purpose": "p",
        "symbol": "X",
        "timeframe": "H1",
        "family": "session",
    }
    argv = builder_argv("Test_x", row, 1, "custodian")
    assert argv[argv.index("--family") + 1] == "session"
    assert "--family" not in builder_argv(
        "Test_x", {**row, "family": ""}, 1, "custodian"
    )


def test_recreating_an_old_project_needs_no_family_but_a_new_name_does(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A name with a registry row and no family is accepted on recreate (store-resume); a new one is refused."""
    fake(tmp_path, monkeypatch)
    assert registry.check_family(None, True, "Test_old") is None
    assert registry.check_family(None, True, "Test_brand_new")
    assert registry.check_family("", True, "Test_old") is None
