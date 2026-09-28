"""No raw key and no scientific number on screen: the rail's config line, the filter labels, the knob sentences."""

import importlib
import os
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from core.paths import ROOT  # noqa: E402
from ui.daemon.filters import evaluate  # noqa: E402
from ui.daemon.results import knobs  # noqa: E402
from ui.daemon.results.catalogue import STUDIES  # noqa: E402
from ui.desktop.workspace.railrow import readable  # noqa: E402
from ui.text.glossary import knob  # noqa: E402

RAW = ("nulls.draws", "run.blocks", "ingest.capital", "=None", "e-05", "e+06", "_")


def test_rail_line() -> None:
    """The one-line config a test carries reads as words: labelled knobs, numbers in full."""
    got = readable("nulls.draws=2500 · run.blocks=None · ingest.capital=1e-05 (+9)")
    assert got == ("Nulos › Corridas 2 500 · Ejecución › Bloques — · Ingesta › Capital "
                   "0.00001 · y 9 más"), got
    assert readable("sin configuración") == "sin configuración"
    assert knob("presencia.kind") == "Presencia › Tipo"


def test_filter_words() -> None:
    """Every kind of filterable column has words, and the criterion writes no `:g` number."""
    cases = {"crossTF.H1.p": "Cross-timeframe · H1 · p",
             "mcRetest.stress_net_p5": "MC Retest · Neto p5 bajo estrés",
             "spread.operaciones": "Spread real de Darwinex · Operaciones",
             "Net profit (IS)": "Beneficio neto IS",
             "dist:monkey/Sharpe [R]": "Distribución · Test del mono · Sharpe [R]"}
    for key, words in cases.items():
        assert evaluate.named(key) == words, (key, evaluate.named(key))
    text = evaluate.expression([{"metric": "crossTF.H1.p", "op": "<", "value": 0.00001},
                                {"metric": "Net profit (OOS)", "op": "entre",
                                 "value": [0.0, 2_000_000.0]}])
    assert text == ("Cross-timeframe · H1 · p < 0.00001 AND Beneficio neto OOS entre 0 y "
                    "2000000"), text
    assert not any(r in text for r in RAW), text


def test_every_knob_has_a_sentence() -> None:
    """Every knob the drawer shows carries its study's sentence: the loaded configs, and the
    raw config.yaml of a study the daemon has no loader for."""
    missing = [f"{k} {x['key']}" for k in knobs.LOADERS
               for s in knobs.sections(k)["sections"] for x in s["knobs"] if not x["tip"]]
    for key, row in STUDIES.items():
        folder = ROOT / Path(*row[1].split("."))
        if key in knobs.LOADERS or not (folder / "config.yaml").exists():
            continue
        tips = importlib.import_module(f"{row[1]}.tooltips").TIPS
        cfg = yaml.safe_load((folder / "config.yaml").read_text())
        missing += [f"{key} {d}" for d, _ in knobs._leaves(cfg, "") if not knobs._tip(tips, d)]
    assert not missing, "\n".join(missing)


if __name__ == "__main__":
    for test in (test_rail_line, test_filter_words, test_every_knob_has_a_sentence):
        test()
    print("ok: raíl, filtros y frases de los mandos en palabras")
