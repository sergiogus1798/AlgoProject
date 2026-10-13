"""Encargo 66: a member's clock and commission are frozen in its manifest, never read live."""

import json
import os
import stat
from pathlib import Path

import pytest

from core.archive import manifest, read
from portfolio.common.construct.inputs import backfill


def _version(tmp: Path, created: str, use: object, extra: dict | None = None) -> Path:
    """A fake version folder: manifest, card and an empty strategy file."""
    v = tmp / "v"
    (v / "asset").mkdir(parents=True)
    (v / "asset" / "card.json").write_text(json.dumps({"costs": {"commission": {"use": use}}}))
    (v / "manifest.json").write_text(json.dumps({"registry": {"created": created}, "asset": {"symbol": "X"}, **(extra or {})}))
    (v / "strategy.sqx").write_text("")
    return v


def test_frozen_written_and_read_back(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """See the name."""
    use = {"build": {"method": "SizeBased", "value": 5.0}}
    monkeypatch.setattr(manifest.assetdata, "load", lambda s: {"costs": {"commission": {"use": use}}})
    got = manifest.frozen("EETUS", "X")
    assert read.frozen(got, "a" * 64) == ("EETUS", use)
    monkeypatch.setattr(manifest.assetdata, "load", lambda s: {"costs": {"commission": {"use": {}}}})
    assert read.frozen(got, "a" * 64) == ("EETUS", use)          # a card change later moves nothing


def test_missing_fields_raise_naming_member_and_command() -> None:
    """No fallback: the message names the member and the backfill."""
    with pytest.raises(KeyError, match=r"abcdefabcdef.*inputs\.backfill"):
        read.frozen({"step": "16.5"}, "abcdefabcdef" + "0" * 52)


def test_backfill_dry_run_writes_nothing_and_yes_fills(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """See the name."""
    monkeypatch.setattr(backfill.feeds, "timezone", lambda feed: "EETUS")
    monkeypatch.setattr(backfill.manifest, "feed_of", lambda sqx: "X_M1")
    use = {"build": {"method": "SizeBased", "value": 5.0}}
    new = _version(tmp_path, "2026-10-05 10:00", use)
    before = (new / "manifest.json").read_bytes()
    fields, why = backfill.plan(new)
    assert fields == {"clock": "EETUS", "commission": use} and (new / "manifest.json").read_bytes() == before
    backfill.write(new, fields)
    assert read.frozen(json.loads((new / "manifest.json").read_text()), "i" * 64) == ("EETUS", use)
    assert stat.S_IMODE(os.stat(new).st_mode) == 0o555
    os.chmod(new, 0o755)
    assert backfill.plan(new)[1] == "ya congelado"


def test_backfill_refuses_what_it_cannot_establish(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """An older project on an unmapped feed or a scalar card is listed, not filled; the mapped old feed gets today's clock."""
    monkeypatch.setattr(backfill.manifest, "feed_of", lambda sqx: "X_M1")
    monkeypatch.setattr(backfill.feeds, "timezone", lambda feed: "EETUS")
    old = _version(tmp_path, "2026-09-29 22:05", {"build": {"method": "SizeBased", "value": 5.0}})
    assert backfill.plan(old)[0] is None and "reloj" in backfill.plan(old)[1]
    scalar = _version(tmp_path / "s", "2026-10-05 10:00", 8.0) if (tmp_path / "s").mkdir() is None else None
    assert backfill.plan(scalar)[0] is None
    monkeypatch.setattr(backfill.manifest, "feed_of", lambda sqx: "USDJPY_DukasM1_the5ers")
    monkeypatch.setattr(backfill.feeds, "timezone", lambda feed: {"USDJPY_M1": "EETUS"}[feed])   # KeyError if not mapped
    assert backfill.plan(old)[0]["clock"] == "EETUS"
