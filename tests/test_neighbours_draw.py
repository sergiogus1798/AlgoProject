"""Step 14's T1 draw (`sqx.variants.neighbours`) and its batch: classes, bounds, determinism, de-dup."""

import zipfile
from pathlib import Path

import pandas as pd
import pytest

from sqx.variants import manifest, neighbourbatch, neighbours
from sqx.variants.build import rewrite

FIXTURE = Path(__file__).parent / "fixtures" / "strategy.sqx"
CFG = {
    "n": 400,
    "entry_pct": 15,
    "exit_pct": 30,
    "seed": 0,
    "int_floor": 1,
    "fixed": [
        r"(Shift|Shf)\d*$",
        r"(Method|Mth|Mode|Mde|Type|AppliedPrice|AppPrc|Fld|Str)\d*$",
    ],
}
# name, type, value, paramType
VARIABLES = [
    ("MagicNumber", "int", "11111", ""),
    ("LongEntrySignal", "boolean", "false", ""),
    ("RSIPeriod1", "int", "20", "ParamTypePeriod"),
    ("RSILevel1", "double", "50", "ParamTypeConstant"),
    ("RSIShift1", "int", "1", "ParamTypeShift"),
    ("MACDShf1", "int", "1", "ParamTypeOtherParam"),  # a shift only by its name
    (
        "CBlock_WssShfInt1",
        "int",
        "100",
        "ParamTypeOtherParam",
    ),  # «Shf» is the block's name
    ("MAMethod1", "int", "2", "ParamTypeOtherParam"),
    ("ExitAfterBars1", "int", "30", "ParamTypeExitUsed"),
    ("StopLossCoef1", "double", "4", "ParamTypeExitUsed"),
]


def portfolio(variables: list[tuple[str, str, str, str]]) -> str:
    """A strategy definition holding only its variables, as SQX spells each one."""
    return "".join(
        f"<variable><id>{n}</id><name>{n}</name><type>{t}</type><value>{v}</value>"
        + (f"<paramType>{k}</paramType>" if k else "<paramType />")
        + "</variable>"
        for n, t, v, k in variables
    )


def test_classes_move_what_sqx_typed_and_leave_shifts_and_selectors() -> None:
    """Entry and exit by SQX's own type; no MagicNumber, boolean, shift or selector."""
    assert neighbours.classes(portfolio(VARIABLES), CFG) == {
        "RSIPeriod1": "entry",
        "RSILevel1": "entry",
        "CBlock_WssShfInt1": "entry",
        "ExitAfterBars1": "exit",
        "StopLossCoef1": "exit",
    }


def test_every_neighbour_stays_inside_its_class_bounds() -> None:
    """Entry within 15 %, exits within 30 % and using more than 15 %; ints whole; fixed absent."""
    drawn, _ = neighbours.draw(portfolio(VARIABLES), "Strategy 1.2.3", CFG)
    table = pd.DataFrame(drawn)
    assert list(table.columns) == [
        "RSIPeriod1",
        "RSILevel1",
        "CBlock_WssShfInt1",
        "ExitAfterBars1",
        "StopLossCoef1",
    ]
    assert (
        table["RSIPeriod1"].between(17, 23).all() and table["RSIPeriod1"].nunique() == 7
    )
    assert table["RSILevel1"].between(42.5, 57.5).all()
    assert table["CBlock_WssShfInt1"].between(85, 115).all()
    assert table["ExitAfterBars1"].between(21, 39).all()
    assert table["StopLossCoef1"].between(2.8, 5.2).all()
    assert (table["ExitAfterBars1"] > 35).any() and (table["StopLossCoef1"] < 3.3).any()
    whole = ["RSIPeriod1", "CBlock_WssShfInt1", "ExitAfterBars1"]
    assert (table[whole] == table[whole].round()).all().all()
    assert (
        len(table.drop_duplicates()) == len(table) > 390
    )  # all parameters at once: no grid


def test_the_draw_repeats_and_each_mother_has_her_own() -> None:
    """Same mother and seed, same neighbours; another name or seed, another draw."""
    text = portfolio(VARIABLES)
    first, _ = neighbours.draw(text, "Strategy 1.2.3", CFG)
    assert first == neighbours.draw(text, "Strategy 1.2.3", CFG)[0]
    assert first != neighbours.draw(text, "Strategy 9.9.9", CFG)[0]
    assert first != neighbours.draw(text, "Strategy 1.2.3", CFG | {"seed": 7})[0]


def test_duplicates_after_rounding_are_dropped_and_counted() -> None:
    """A period of 3 has no neighbour within 15 %; a 5-bar exit has two within 30 %."""
    period = portfolio([("StochDPeriod1", "int", "3", "ParamTypePeriod")])
    assert neighbours.draw(period, "S", CFG) == ([], 400)
    bars = portfolio([("ExitAfterBars1", "int", "5", "ParamTypeExitUsed")])
    drawn, dropped = neighbours.draw(bars, "S", CFG)
    assert sorted(d["ExitAfterBars1"] for d in drawn) == [4.0, 6.0] and dropped == 398


def test_an_integer_never_drops_below_the_floor() -> None:
    """A period of 1 moved 80 % rounds to 0, 1 or 2: 0 is clamped to 1, which is the mother."""
    one = portfolio([("Period1", "int", "1", "ParamTypePeriod")])
    drawn, _ = neighbours.draw(one, "S", CFG | {"entry_pct": 80})
    assert [d["Period1"] for d in drawn] == [2.0]


def test_the_batch_on_disk_is_the_plan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two mothers through `make`: neighbour 0 is the mother to the value, the rest hold their tuple."""
    mothers = tmp_path / "mothers"
    mothers.mkdir()
    for name in ("Strategy A", "Strategy B"):
        (mothers / f"{name}.sqx").write_bytes(FIXTURE.read_bytes())
    monkeypatch.setattr(
        neighbourbatch.inputs,
        "load",
        lambda: {"neighbours": CFG | {"n": 20, "shape": "minimal"}},
    )
    rows = neighbourbatch.make(mothers, tmp_path / "work")  # raises unless disk == plan
    table = manifest.read(tmp_path / "work")
    assert list(table["variant_id"][:2]) == ["M000N0000", "M000N0001"]
    assert set(table["strategy"]) == {"Strategy A", "Strategy B"} and len(table) == len(
        rows
    )
    assert table.groupby("strategy")["origin"].sum().tolist() == [1, 1]
    with zipfile.ZipFile(FIXTURE) as z:
        source = rewrite.values(z.read(rewrite.PORTFOLIO).decode("utf-8"))
    for row in table[table["neighbour"] <= 1].to_dict("records"):
        with zipfile.ZipFile(tmp_path / "work" / "sqx" / row["file"]) as z:
            held = rewrite.values(z.read(rewrite.PORTFOLIO).decode("utf-8"))
        assert rewrite.SETTINGS in z.namelist() and "orders.bin" not in z.namelist()
        assert held["MagicNumber"] == source["MagicNumber"]
        moved = {k: float(v) for k, v in held.items() if v != source[k]}
        assert bool(moved) == (row["neighbour"] == 1)
        assert all(row[f"param_{k}"] == v for k, v in moved.items())
    a, b = (
        table[table["strategy"] == s].filter(like="param_").to_numpy()
        for s in ("Strategy A", "Strategy B")
    )
    assert (a[0] == b[0]).all() and (
        a[1:] != b[1:]
    ).any()  # same mother, her own draw each
