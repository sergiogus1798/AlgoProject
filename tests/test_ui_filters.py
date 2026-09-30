"""The databank filters re-filter from the whole databank: loosening brings strategies back."""

import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ui.daemon.filters import api, discards, evaluate, ledgerrow, view  # noqa: E402

P, D = "Test_UiFilters", "Results"
SHARPE = "Sharpe Ratio (OOS)"
LEDGER: list[dict] = []


def fake(root: Path) -> dict:
    """Point the log at a scratch folder and the ledger at a list: nothing real is written.
    Returns the fake table, which a test may change as SQX would."""
    table = {"columns": [{"key": "name", "kind": "name"},
                         {"key": SHARPE, "kind": "metric", "sample": "OOS"}],
             "rows": [{"identity": f"id{i}", "name": f"S{i}", "values": [f"S{i}", i / 10]}
                      for i in range(20)]
             + [{"identity": "idN", "name": "SN", "values": ["SN", None]}]}
    metrics = evaluate.offered(table, {}, set())
    discards.root = lambda: root
    discards.folder = lambda p, d: root / p / d.replace(" ", "_")
    api.context = lambda p, d: (table, {}, metrics)
    api.tablemod = SimpleNamespace(table=lambda p, d: table)
    api.refused = lambda p, d: None
    ledgerrow.placed = lambda p, d: (8, "build")
    ledgerrow.log = lambda *a: LEDGER.append(a) or {"study": "S", "step": 8, "segment": "oos1"}
    return table


def apply(value: float | None) -> dict:
    """«Aplicar» Sharpe OOS > value; None applies no condition."""
    rows = [] if value is None else [api.Row(metric=SHARPE, op=">", value=str(value))]
    return api.applied(api.Apply(project=P, databank=D, rows=rows))


def below(x: float) -> set[str]:
    """The identities a `Sharpe > x` filter hides."""
    return {f"id{i}" for i in range(20) if i / 10 <= x}


def main() -> None:
    """Tighten, discard by hand, loosen, preview, lift, clear, and read an old log."""
    with tempfile.TemporaryDirectory() as tmp:
        fake(Path(tmp))
        tight = apply(1)
        assert set(tight["hidden_ids"]) == below(1) and tight["blank"] == 1, tight
        assert api.discarded(api.Discard(project=P, databank=D, identities=["id15"]))["n_out"] == 9
        loose = apply(0.5)
        back = below(1) - below(0.5)
        assert set(loose["hidden_ids"]) == below(0.5) | {"id15"}, loose["hidden_ids"]
        assert loose["hidden"] < tight["hidden"] and not back & set(loose["hidden_ids"])
        assert {r["identity"] for r in discards.live(P, D)} == set(loose["hidden_ids"])
        assert [s["died"] for s in loose["steps"]] == [6, 1], loose["steps"]
        assert loose["conditions"] == [{"metric": SHARPE, "op": ">", "value": 0.5}]
        assert len(LEDGER) == 3, "one row per applied filter and per deletion"

        size = discards.log_file(P, D).stat().st_size
        assert apply(0.5)["same"] and len(LEDGER) == 3, "the same filter is not logged again"
        seen = api.preview(api.Apply(project=P, databank=D, rows=[
            api.Row(metric=SHARPE, op=">", value="1.4")]))
        assert (seen["n_out"], seen["visible"]) == (6, 5), seen
        assert discards.log_file(P, D).stat().st_size == size and len(LEDGER) == 3

        lifted = apply(None)
        assert lifted["hidden_ids"] == ["id15"] and len(LEDGER) == 3, "no conditions: no row"
        assert [(s["entered"], s["passed"]) for s in lifted["steps"]] == [(21, 20)], \
            "with no filter in force a deletion counts from the whole table"
        assert api.clear(api.Bank(project=P, databank=D))["hidden"] == 0

        text = f"{evaluate.named(SHARPE)} > 0.8"
        discards.append(P, D, [{"applied": True, "origin": "filter", "expression": text,
                                "ts": "t", "n_in": 21, "n_out": 21}])
        old = api.state_of(P, D)
        assert old["stale"] == text and old["hidden"] == 0 and old["steps"] == []
        assert old["conditions"] == [{"metric": SHARPE, "op": ">", "value": 0.8}]
        assert view.recovered("Columna inventada > 1", []) == []
        discards.append(P, D, [{"clear": True, "cut": True, "ts": "t"}])
        assert discards.live(P, D) == [] and not discards.stale(P, D)
    changed()
    print("ok: loosening brings rows back, manual deletions stay, live == hidden, "
          "one ledger row per applied filter")


def changed() -> None:
    """The databank moves under a filter: a re-apply is not `same`, it hides the newcomer and
    forgets the strategy SQX deleted; a truncated log does not take the state down."""
    with tempfile.TemporaryDirectory() as tmp:
        table = fake(Path(tmp))
        apply(1)
        api.discarded(api.Discard(project=P, databank=D, identities=["id19"]))
        rows = table["rows"]
        rows[:] = [r for r in rows if r["identity"] not in ("id0", "id19")]
        rows.append({"identity": "idNew", "name": "SNew", "values": ["SNew", 0.2]})
        seen = api.preview(api.Apply(project=P, databank=D, rows=[
            api.Row(metric=SHARPE, op=">", value="1")]))
        assert seen["visible"] == 20 - 11 == seen["n_out"] - 0, seen
        again = apply(1)
        assert "same" not in again, "the table changed: a re-apply must write"
        hidden = set(again["hidden_ids"])
        assert "idNew" in hidden and "id0" not in hidden and len(LEDGER) >= 1
        assert apply(1).get("same"), "now it is the same judgement"
        discards.append(P, D, [{"clear": True, "ts": "t"}, {"identity": "idX", "name": "X"}])
        state = api.state_of(P, D)
        assert state["orphans"] == 1 and state["hidden"] == 0, state


if __name__ == "__main__":
    main()
