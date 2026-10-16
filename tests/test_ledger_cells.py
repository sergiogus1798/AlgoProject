"""Known-answer tests: the per-cell counter and accumulated(extra=None)."""

import json

import pandas as pd

from ledger import cells, trials

REG = {
    "Test_A_1": {
        "name": "Test_A_1",
        "symbol": "XAUUSD",
        "timeframe": "H1",
        "template": "simple:long",
        "family": "breakout",
    },
    "Trade_A_2": {
        "name": "Trade_A_2",
        "symbol": "XAUUSD",
        "timeframe": "H1",
        "template": "simple:long",
        "family": "breakout",
    },
    "Test_B": {
        "name": "Test_B",
        "symbol": "XAUUSD",
        "timeframe": "H1",
        "template": "simple:long",
        "family": "",
    },
}


def setup(monkeypatch: object, tmp_path: object) -> None:
    """Point the counter at a tmp folder and the fake registry."""
    monkeypatch.setattr(cells, "FOLDER", tmp_path)
    monkeypatch.setattr(cells, "PROJECTS", tmp_path / "projects.csv")
    monkeypatch.setattr(cells, "EXTRAS", tmp_path / "extras.json")
    monkeypatch.setattr(cells.sources, "registry_projects", lambda: REG)
    monkeypatch.setattr(cells.sources, "templates", lambda: {})
    monkeypatch.setattr(cells, "SEAL", tmp_path / "seal.json")
    monkeypatch.setattr(cells, "JUDGEMENTS", tmp_path / "judgements.csv")
    monkeypatch.setattr(cells, "CRITERIA", tmp_path / "criteria.yaml")
    (tmp_path / "criteria.yaml").write_text("a")
    monkeypatch.setattr(cells, "built", lambda: {"Test_A_1": 100, "Trade_A_2": 100})


def test_two_projects_one_cell_test_and_trade_count(
    monkeypatch: object, tmp_path: object
) -> None:
    """Two projects, one cell: B = 2; a Test_ and a Trade_ both count."""
    setup(monkeypatch, tmp_path)
    for p in ("Test_A_1", "Trade_A_2"):
        cells.note(p, 40)
    cells.note("Test_A_1", 40)  # a re-run does not double-count
    cell = "XAUUSD_H1_long_breakout"
    assert cells.batches_screened(cell) == 2
    assert (
        cells.table()[cell]["generated"] == 200
        and cells.table()[cell]["batches_built"] == 2
    )


def test_unknown_family_and_unseen_cell(monkeypatch: object, tmp_path: object) -> None:
    """A project without family goes to `unknown`; an unseen cell has B = 0."""
    setup(monkeypatch, tmp_path)
    cells.note("Test_B", 1)
    assert cells.batches_screened("XAUUSD_H1_long_unknown") == 1
    assert cells.batches_screened("nothing") == 0


def test_accumulated_extra_none() -> None:
    """extra=None counts as 0 (it used to raise TypeError)."""
    frame = pd.DataFrame(
        {
            "n_scored": [10],
            "sharpe_mean": [0.1],
            "sharpe_std": [0.2],
            "score_unit": ["per_period"],
        }
    )
    assert trials.accumulated(frame, None)["n"] == 10
    assert trials.accumulated(pd.DataFrame(), None)["n"] == 0


def test_edits_since_seal(monkeypatch: object, tmp_path: object) -> None:
    """No seal: edits is None. After it, the same hash adds nothing; each different one counts once."""
    setup(monkeypatch, tmp_path)
    cell = "XAUUSD_H1_long_breakout"
    monkeypatch.setattr(cells, "_now", lambda: "2026-10-11T00:00:00+00:00")
    cells.note("Test_A_1", 40)
    assert cells.edits(cell) is None
    monkeypatch.setattr(cells, "_now", lambda: "2026-10-12T00:00:00+00:00")
    cells.seal()
    monkeypatch.setattr(cells, "_now", lambda: "2026-10-13T00:00:00+00:00")
    cells.note("Test_A_1", 40)  # same criteria.yaml as the seal
    assert cells.edits(cell) == 0
    (tmp_path / "criteria.yaml").write_text("b")
    cells.note("Test_A_1", 40)
    cells.note("Trade_A_2", 40)  # same new hash, other project: one edit
    assert cells.edits(cell) == 1
    (tmp_path / "criteria.yaml").write_text("c")
    cells.note("Trade_A_2", 40)
    assert cells.edits(cell) == 2
    monkeypatch.setattr(cells, "_now", lambda: "2026-10-14T00:00:00+00:00")
    cells.seal(again=True)  # S1: the owner reseals, the old seal kept
    assert cells.edits(cell) == 0
    assert len(json.loads(cells.SEAL.read_text())["previous"]) == 1


def test_batches_for_counts_the_current_batch_once(
    monkeypatch: object, tmp_path: object
) -> None:
    """B of the step-8 rule: a project not yet judged adds itself; once judged it is in the count;
    an unregistered project is 1."""
    setup(monkeypatch, tmp_path)
    cells.note("Test_A_1", 40)
    assert cells.batches_for("Trade_A_2") == 2 and cells.batches_for("Test_A_1") == 1
    cells.note("Trade_A_2", 40)
    assert cells.batches_for("Trade_A_2") == 2 and cells.batches_for("nobody") == 1


def test_ask_test_only_is_built_and_oos2_is_open(
    monkeypatch: object, tmp_path: object
) -> None:
    """A cell with only `Test_` projects is «construida»; one with oos2 rows is «oos2 abierto»."""
    setup(monkeypatch, tmp_path)
    monkeypatch.setattr(cells, "campaign_dir", lambda: tmp_path)
    book = {
        "XAUUSD_H1_simple_long": pd.DataFrame(
            {
                "segment": ["oos1", "oos1", "oos2"],
                "step": [8, 8, 17],
                "ts": ["2026-10-01T00"] * 3,
                "criterion": ["a", "b", "c"],
            }
        )
    }
    monkeypatch.setattr(cells.studymod, "studies", lambda: list(book))
    monkeypatch.setattr(cells.studymod, "read", lambda s: book[s])
    out = cells.ask("XAUUSD", "H1", direction="long")
    assert out["cell"]["oos1"]["screenings"] == 2 and out["verdict"].startswith(
        "oos2 abierto"
    )
    monkeypatch.setattr(cells.studymod, "studies", lambda: [])
    assert cells.ask("XAUUSD", "H1")["verdict"] == "construida, sin juzgar"
    assert cells.ask("EURUSD", "H1")["verdict"] == "sin probar"


def test_ask_direction_campaign_and_kinds(
    monkeypatch: object, tmp_path: object
) -> None:
    """The book is read off the study suffix for a direction; the campaign state is the cell's latest."""
    setup(monkeypatch, tmp_path)
    monkeypatch.setattr(cells, "campaign_dir", lambda: tmp_path)
    reg = {
        k: {**v, "kind": "test" if k.startswith("Test") else "trade"}
        for k, v in REG.items()
    }
    monkeypatch.setattr(cells.sources, "registry_projects", lambda: reg)
    row = {"template": "t", "symbol": "XAUUSD", "timeframe": "H1", "direction": "long"}
    (tmp_path / "ledger.jsonl").write_text(
        "\n".join(json.dumps({**row, "state": s}) for s in ("pending", "done")),
        encoding="utf-8",
    )
    frame = pd.DataFrame(
        {"segment": ["oos2"], "step": [17], "ts": ["2026-10-01"], "criterion": ["c"]}
    )
    monkeypatch.setattr(cells.studymod, "studies", lambda: ["XAUUSD_H1_simple_long"])
    monkeypatch.setattr(cells.studymod, "read", lambda s: frame)
    assert (
        cells.ask("XAUUSD", "H1", direction="short")["verdict"]
        != "oos2 abierto (1 filas)"
    )
    out = cells.ask("XAUUSD", "H1", direction="long")
    assert out["campaign"] == ["done"] and sorted(out["projects"]) == ["test", "trade"]
