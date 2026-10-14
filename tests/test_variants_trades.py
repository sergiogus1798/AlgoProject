"""Known-answer test for `varianttrades.gather` and the brief guard of `inputs` (encargo 48 F)."""

import json
from pathlib import Path

import pandas as pd
import pytest

from sqx.variants import inputs, varianttrades

LEGS = [{"segment": s, "databank": f"bank_{s}"} for s in ("build", "oos1", "oos2")]


def test_gather_joins_the_legs_and_names_the_market(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Three legs in, one file out: leg and market columns, collision suffix gone, folders removed."""
    monkeypatch.setattr(varianttrades.legmod, "legs", lambda: LEGS)
    monkeypatch.setattr(
        varianttrades, "export_dir", lambda p, db, day, tag: tmp_path / "raw" / db
    )
    monkeypatch.setattr(varianttrades, "main_feed", lambda project: "XAUUSD_M1")
    for leg in LEGS:
        folder = tmp_path / "raw" / leg["databank"]
        folder.mkdir(parents=True)
        pd.DataFrame(
            {
                "strategy": ["P00001(1)", "P00001"],
                "Symbol": ["XAUUSD_M1", "XAGUSD_M1"],
                "block": [1, 0],
                "Size": [1.0, 2.0],
            }
        ).to_parquet(folder / "trades.parquet")
    n = varianttrades.gather(
        tmp_path, "P", "2026-01-01"
    )  # the fake folder has no day level to search
    got = pd.read_parquet(tmp_path / varianttrades.OUT)
    assert n == 6 and set(got["leg"]) == {"build", "oos1", "oos2"}
    assert set(got["variant_id"]) == {"P00001"} and "strategy" not in got
    assert sorted(set(got["market"])) == ["Main", "XAGUSD_M1"]
    assert set(got.loc[got["market"] == "Main", "Symbol"]) == {
        "XAUUSD_M1"
    }  # by feed, not by block
    assert not (tmp_path / "raw" / "bank_build").exists()


def test_a_brief_from_the_oos_spp_is_refused(tmp_path: Path) -> None:
    """The box is drawn on build only: a brief whose source is an `SPP_OOS` export stops."""
    path = tmp_path / "brief.json"
    path.write_text(json.dumps({"source": "/x/raw/P/SPP_OOS/2026-10-07/spp"}))
    with pytest.raises(SystemExit):
        inputs.brief(path)
    path.write_text(json.dumps({"source": "/x/raw/P/SPP_IS/2026-10-07/spp"}))
    assert inputs.brief(path)["source"].endswith("spp")
