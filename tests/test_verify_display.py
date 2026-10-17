"""MT5 Bridge display: percentages in Spanish format, firm names and verdict parts polished."""

from mt5.verify.display import percent, polish


def test_polish() -> None:
    """`polish` names the firms, capitalises labels and adds a shown percentage to verdict parts."""
    assert percent(0.9673366, 2) == "96,73%"
    res = {
        "summary": {"firms": {"ftmo": {"state": "pass"}, "hantec": {"state": "fail"}}},
        "tabs": [
            {"name": "resumen", "blocks": []},
            {
                "blocks": [
                    {"kind": "table", "columns": ["parámetro"], "rows": [["spread"]]},
                    {
                        "kind": "verdict",
                        "parts": [
                            {"label": "1 · operaciones", "value": 0.9422},
                            {"label": "2 · diferencia", "value": 0.03},
                        ],
                    },
                ]
            },
        ],
    }
    out = polish(res, {"ftmo": "FTMO", "hantec": "Hantec"})
    assert [b["text"] for b in out["tabs"][0]["blocks"]] == [
        "FTMO: validada",
        "Hantec: no validada",
    ]
    assert out["tabs"][1]["blocks"][0]["rows"][0][0] == "Spread"
    parts = out["tabs"][1]["blocks"][1]["parts"]
    assert parts[0]["label"] == "1 · Operaciones" and parts[0]["shown"] == "94,22%"
    assert "shown" not in parts[1]
