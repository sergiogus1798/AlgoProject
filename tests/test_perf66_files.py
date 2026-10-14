"""Encargo 66, files no longer written (owner, 2026-10-13): the per-strategy page and the 18.5 detail."""

import json
from pathlib import Path

import pytest

from core.study import output
from studies.optimisation.marketSurfaces import report


def test_member_writes_only_the_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A strategy's result is its JSON; the page is drawn on demand (`/api/study/screen`), not stored."""
    monkeypatch.setattr(output.page, "page", lambda result, title, lede: "<h1/>")
    monkeypatch.setattr(output.markdown, "render", lambda result, title: "# T\n")
    result = {"strategy": "Strategy 1.2.3", "v": "ñ"}
    path = output.member(tmp_path, result, "T", "L")
    output.population(tmp_path, "pop", result, "T")
    assert json.loads(path.read_text()) == result
    assert sorted(p.name for p in (tmp_path / "estrategias").iterdir()) == [
        "Strategy 1.2.3.json"
    ]
    assert (tmp_path / "pop.html").is_file() and (tmp_path / "pop.md").is_file()


def test_market_surfaces_writes_no_detail_file() -> None:
    """The 159 MB `marketSurfaces_detalle.json` and the code that built its grids are gone."""
    here = Path(report.__file__).parent
    assert (
        not hasattr(report, "DETAIL") and not (here / "contract" / "grids.py").exists()
    )
    assert "_detalle" not in Path(report.__file__).read_text()
