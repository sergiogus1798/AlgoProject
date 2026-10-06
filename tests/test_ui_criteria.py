#!/usr/bin/env python3
"""The Criterios zone's daemon: the state step by step, and every write — a rule added, changed,
deleted, the stamp in the history, the freeze and its refusals — on a COPY of criteria.yaml."""

import json
import shutil
import sys
import tempfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ui.daemon.criteria import api, read

REAL = read.FILES["criteria"]
VERDICT = {"fact": "crossmarket.verdict.pass", "is": "pass", "else": "limbo"}
BOTH = {"all": [{"fact": "spp.verdict.pass", "is": "pass"},
                {"fact": "spp.summary.n_eff", "pass": ">= 20", "limbo": ">= 10"}]}


def http() -> TestClient:
    """A local app holding only the zone's router; never the real daemon."""
    app = FastAPI()
    app.include_router(api.ROUTER)
    return TestClient(app)


def rule(c: TestClient, **body: object) -> tuple[int, dict]:
    """One write through the route, as the window sends it."""
    r = c.post("/api/criteria/rule", json=body)
    return r.status_code, r.json()


def test_state_write_stamp_freeze() -> None:
    """Steps come in WORKFLOW's order with their rules worded; a write changes its own line,
    keeps every comment and is stamped with the rule before and after; a stale `was`, a bad
    test, a step without `cut` and frozen criteria are refused; the real file is not touched."""
    before = REAL.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        copy, log = Path(tmp) / "criteria.yaml", Path(tmp) / "history.jsonl"
        shutil.copy(REAL, copy)
        with mock.patch.dict(read.FILES, {"criteria": copy, "history": log}):
            c = http()
            state = c.get("/api/criteria").json()
            ns = [s["n"] for s in state["steps"]]
            assert ns[:5] == ["8", "10", "12", "14", "16"] and "6" not in ns and "20" in ns
            assert state["frozen"] is None and state["history"] == []
            assert [r["kind"] for r in state["build"]["rows"]] == ["Métrica SQX"] * 3
            eight = state["steps"][0]
            cfg = yaml.safe_load(before)["steps"]["8"]
            assert eight["cut"] == cfg["cut"] and len(eight["rows"]) == len(cfg["rules"])
            first = eight["rows"][0]
            assert first["tip"] == cfg["rules"][0]["fact"] and first["why"].startswith("R1")
            comments = sum(line.strip().startswith("#") for line in before.splitlines())

            # refused, and nothing written
            assert rule(c, n="8", at=0, rule=VERDICT, was={"fact": "otro"})[0] == 422
            assert rule(c, n="10", rule={"fact": "x", "pass": "grande"})[0] == 422
            assert rule(c, n="10", rule={"any": []})[0] == 422
            assert rule(c, n="17", rule=VERDICT)[0] == 422            # no `cut` in the file
            assert yaml.safe_load(copy.read_text()) == yaml.safe_load(before) and not log.exists()

            # added (a verdict, a compound), changed, deleted
            assert rule(c, n="10", rule=VERDICT) == (200, mock.ANY)
            assert rule(c, n="16", rule=BOTH)[0] == 200
            new = first["rule"] | {"pass": ">= 0.5"}
            assert rule(c, n="8", at=0, rule=new, was=first["rule"])[0] == 200
            assert rule(c, n="16", at=0, was=BOTH)[0] == 200
            text = copy.read_text(encoding="utf-8")
            got = yaml.safe_load(text)["steps"]
            had = yaml.safe_load(before)["steps"]["10"]["rules"]
            assert got["10"]["rules"] == had + [VERDICT] and got["16"]["rules"] == []
            assert got["8"]["rules"][0] == new and got["8"]["rules"][1:] == cfg["rules"][1:]
            assert sum(line.strip().startswith("#") for line in text.splitlines()) == comments
            lines = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
            assert [(h["step"], h["what"]) for h in lines] == [
                ("10", "añadida"), ("16", "añadida"), ("8", "cambiada"), ("16", "borrada")]
            assert lines[2]["before"] == first["rule"] and lines[2]["after"] == new
            assert lines[3]["after"] is None and all(h["at"] and h["by"] for h in lines)
            state = c.get("/api/criteria").json()
            ten = state["steps"][1]["rows"][-1]
            assert (ten["kind"], ten["passes"], ten["limbo"]) == ("Veredicto", "Aprobado",
                                                                  "Si no cumple")
            assert state["history"][0]["what"] == "borrada"           # newest first

            # the freeze: stamped, read back, and nothing is written after it
            assert c.post("/api/criteria/freeze").status_code == 200
            state = c.get("/api/criteria").json()
            assert state["frozen"]["on"] and state["frozen"]["changed"] is False
            assert state["history"][0]["what"] == "congelado"
            status, said = rule(c, n="10", at=0, was=VERDICT)
            assert status == 422 and "congelados" in said["detail"]
            assert c.post("/api/criteria/freeze").status_code == 422
            copy.write_text(copy.read_text(encoding="utf-8").replace('">= 0.5"', '">= 0.6"'),
                            encoding="utf-8")                         # edited by hand afterwards
            assert c.get("/api/criteria").json()["frozen"]["changed"] is True
            dev = yaml.safe_load(copy.read_text(encoding="utf-8"))["dev"]
            assert dev == yaml.safe_load(before)["dev"]               # `on:` survived the writes
    assert REAL.read_text(encoding="utf-8") == before


def test_labels() -> None:
    """A median band and a compound are worded; a fact SQX computed is told from the app's."""
    band = read.row({"fact": "gate.scorecard.forma_value", "near_median": 0.2,
                     "limbo_near_median": 0.5, "by": {"H4": {"near_median": 0.3}}})
    assert band["passes"] == "A ±20 % de la mediana" and band["limbo"] == "A ±50 % de la mediana"
    assert band["by"].startswith("H4: A ±30 %") and band["kind"] == "Test de la app"
    assert read.row({"fact": "spread.verdict_csv.pf_sqx_oos", "pass": ">= 1.1"})["kind"] == \
        "Métrica SQX"
    both = read.row(BOTH)
    assert both["kind"] == "Compuesto" and both["label"] == "Todas de 2"
    assert both["passes"].startswith("Todas:\n") and ">= 20" in both["passes"]


def test_by_rows() -> None:
    """The override rows rebuild `by`: empty keys dropped, empty texts omitted, unknown fields kept."""
    from ui.desktop.criteria.overrides import by_built, by_rows
    old = {"H4": {"pass": ">= 2.5", "limbo": ">= 1.65", "else": "limbo"}, "H1": {"pass": ">= 1"}}
    assert by_built(by_rows(old), old) == old
    got = by_built([("H4", ">= 3", ""), ("  ", "x", "y"), ("forex", "", ">= 1")], old)
    assert got == {"H4": {"else": "limbo", "pass": ">= 3"}, "forex": {"limbo": ">= 1"}}
    assert by_built([], old) == {}


if __name__ == "__main__":
    test_by_rows()
    test_state_write_stamp_freeze()
    test_labels()
    print("ok")
