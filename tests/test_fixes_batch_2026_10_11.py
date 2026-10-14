"""Six small fixes: idea hypotheses count, literature overlap per segment, block install, clock names, find."""

from pathlib import Path

import re

import pytest

from sqx.blocks import install as inst
from sqx.inspect import vocabulary
from sqx.projects import buildcensus
from studies.research.literature import selection
from studies.research.memory import ideas

ATTRS = ' category="signals"'


@pytest.mark.parametrize(
    "text,n",
    [
        ("Hipótesis medidas: **24**", 24),
        ("3. **Hipótesis medidas en total**: 68 sobre build", 68),
        ("Hipótesis medidas en total: 68", 68),
    ],
)
def test_hypotheses_wordings(text: str, n: int) -> None:
    """Both wordings of the hypotheses count are read."""
    assert int(ideas.HYPOTHESES.search(text).group(1)) == n


def test_hypotheses_same_line_only() -> None:
    """The number must sit on the same line."""
    assert ideas.HYPOTHESES.search("Hipótesis medidas en total\n12 cosas") is None


def test_overlap_per_segment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Overlap reads the segment asked for; an undecided one says so."""
    monkeypatch.setattr(selection.assetdata, "load", lambda s: s)
    wins = {
        "build": (0, 4_000_000_000_000),
        "oos1": (1_700_000_000_000, 1_750_000_000_000),
    }

    def window(d: str, seg: str) -> tuple[int, int]:
        """A fake assetdata.window."""
        if seg not in wins:
            raise ValueError(seg)
        return wins[seg]

    monkeypatch.setattr(selection.assetdata, "window", window)
    assert selection.overlap(1990, 2000, ["X"], "oos1").startswith(
        "no: sample 1990-2000 is outside oos1"
    )
    assert selection.overlap(2000, 2001, ["X"], "oos2").startswith("not decided")
    assert selection.overlap(None, 2001, ["X"], "oos2") == "not stated in source"


def _store(tmp_path: Path) -> Path:
    """A one-block store."""
    p = tmp_path / "customBlocks.xml"
    p.write_text('<CustomBlocks><Item key="CBlock_A" /></CustomBlocks>')
    return p


def test_install_refuses_broken_and_keeps_bytes(tmp_path: Path) -> None:
    """A broken XML is refused and the store is untouched."""
    store = _store(tmp_path)
    before = store.read_bytes()
    for bad in (
        '<CustomBlocks><Item key="CBlock_B"',
        '<X><Item key="NotCustom" /></X>',
        '<X><Group name="g" /></X>',
    ):
        f = tmp_path / "b.xml"
        f.write_text(bad)
        with pytest.raises(SystemExit):
            inst.validate(f, store, "key")
        assert store.read_bytes() == before


def test_install_writes_atomically(tmp_path: Path) -> None:
    """A good install lands and leaves no temp file."""
    store = _store(tmp_path)
    (tmp_path / "user" / "settings").mkdir(parents=True)
    dest = tmp_path / inst.CUSTOM_REL
    dest.write_bytes(store.read_bytes())
    f = tmp_path / "b.xml"
    f.write_text('<X><Item key="CBlock_B" /></X>')
    assert inst.install(f, tmp_path) == {"added": ["CBlock_B"], "replaced": []}
    assert "CBlock_B" in dest.read_text() and not list(dest.parent.glob("*.tmp"))


@pytest.mark.parametrize(
    "key",
    [
        "CBlock_TimeBreakoutLong",
        "CBlock_TimeBreakoutLong_2",
        "SessionHigh",
        "SessionLow",
        "SessionOpen",
        "Sig.SessionLow",
        "SessionClose",
        "VolumeProfileCustomHours",
        "VolumeProfileCustomHoursMultiSession",
    ],
)
def test_clock_names(key: str) -> None:
    """The forbidden session and custom-hours blocks are clock."""
    assert buildcensus.kind(key, ATTRS) == "clock"


def test_ordinary_blocks_stay() -> None:
    """Ordinary blocks keep their category kind."""
    assert buildcensus.kind("RSI", ATTRS) == "condition"
    assert buildcensus.kind("CBlock_Keltner", ' category="indicators"') == "value"


def test_find_matches_category_and_help() -> None:
    """find() looks at category and help too."""
    vocab = {
        "native": {"A": {"display": "A", "category": "Momentum Bands", "help": ""}},
        "custom": {
            "B": {"display": "B", "category": "x", "help": "breaks the Donchian"}
        },
        "groups": {},
    }
    assert [r["key"] for r in vocabulary.find(vocab, "bands")] == ["A"]
    assert [r["key"] for r in vocabulary.find(vocab, "donchian")] == ["B"]


def test_no_repo_palette_has_session_close_or_custom_hours() -> None:
    """Owner, 2026-10-13: no repo palette lists the three new clock blocks."""
    from core import paths

    bad = [
        p.name
        for p in (paths.ROOT / "sqx/blocks/palettes").glob("*.yaml")
        if re.search(
            r"^\s*(SessionClose|VolumeProfileCustomHours\w*):", p.read_text(), re.M
        )
    ]
    assert not bad, bad
