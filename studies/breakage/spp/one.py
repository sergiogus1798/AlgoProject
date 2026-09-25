"""One strategy's SPP reconnaissance and its design brief, as the contract's data."""

import time
from pathlib import Path

from core.study import output, result as envelope
from studies.breakage.spp import contract, run as reading

MODULE = "studies.breakage.spp"
GLOSSARY = [
    {"term": "n_eff", "text": "Cuántas tuplas de parámetros dieron un resultado distinto; "
     "el nulo del máximo se calcula sobre ellas, no sobre las filas."},
    {"term": "η²", "text": "Qué parte de la varianza de una métrica explica un parámetro. Es "
     "por métrica, y está sesgada hacia arriba en un parámetro inerte."},
    {"term": "Test de duplicados", "text": "Si cambiar un parámetro, con el resto fijo, deja "
     "el backtest idéntico. Es la prueba de que un parámetro está muerto."},
    {"term": "Meseta", "text": "El tramo contiguo de niveles cuyo resultado queda por encima "
     "de una parte del mejor; su centro es lo que se despliega, no el argmax."}]


def run(strategy: str, directory: Path, cfg: dict) -> dict:
    """The reading and its design brief, as the contract dict.

    Args:
        strategy: Which strategy.
        directory: The export's `spp/` folder.
        cfg: What config.load() returned.

    Returns:
        The contract dict the window paints. Its summary carries `brief`, the
        `design_brief.json` the fabrication stage consumes — the contract with
        `sqx.variants`, which stays exactly as it was.
    """
    started = time.time()
    found = reading.read(directory, strategy, cfg)
    brief = reading.brief(found, cfg)
    return envelope.envelope(
        MODULE, strategy, output.identify(directory.parent, [strategy])[strategy], cfg, started,
        [contract.influence(found), contract.plateaus(found), contract.design(brief)],
        contract.verdict(found),
        [{"code": "sin_emparejar", "state": "info",
          "text": "Una tirada SPP ancha no empareja y nunca emparejará: entre la IS y la OOS "
                  "de Strategy 17.9.39 hubo 6 tuplas en común de ~11.600. Nada de aquí "
                  "compara dos ventanas; para eso existen las variantes."}],
        GLOSSARY, summary={"verdict": brief["verdict"], "n_eff": brief["n_eff"],
                           "live": len(brief["parameters"]), "frozen": len(brief["frozen"]),
                           "brief": brief})
