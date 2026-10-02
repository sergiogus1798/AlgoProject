"""One strategy's SPP reconnaissance and its design brief, as the contract's data."""

import time
from pathlib import Path

import pandas as pd

from core.study import identity, output, result as envelope
from studies.breakage.spp import contract, run as reading
from studies.breakage.spp.inputs import config, export
from studies.breakage.spp.model import combine

MODULE = "studies.breakage.spp"
COMBINED = "IS + OOS1 combinado"
GLOSSARY = [
    {"term": "n_eff", "text": "Cuántas tuplas de parámetros dieron un resultado distinto; "
     "el nulo del máximo se calcula sobre ellas, no sobre las filas."},
    {"term": "Banda", "text": "Mediana ± el porcentaje configurado de su propio valor: el "
     "rango que la SPP habría dado con otra combinación de parámetros."},
    {"term": COMBINED, "text": "Los dos SPP no comparten tuplas (solo 6 de ~11.600 en "
     "Strategy 17.9.39): aquí se recomponen sus componentes aditivos cuando se puede (Net "
     "Profit, PF, Max Drawdown, Ret/DD) y se agrupan como una sola muestra cuando no "
     "(Sharpe, Sortino)."}]


def _paired(directory: Path) -> tuple[Path | None, Path | None]:
    """This export and its IS/OOS pair, always ordered (is_dir, oos_dir)."""
    project, databank = directory.parents[2].name, directory.parents[1].name
    mate = config.other(project, databank)
    return (directory, mate) if databank.upper().endswith("_IS") else (mate, directory)


def _side(directory: Path | None, strategy: str) -> tuple[pd.DataFrame | None, pd.Series | None]:
    """(without-θ0 population, real row) of one window's grid, or (None, None) with no export."""
    if directory is None:
        return None, None
    grid = export.grid(directory, strategy)
    return export.without_original(grid), grid.loc[-1]


def _periods(is_pop: pd.DataFrame | None, is_real: pd.Series | None,
            oos_pop: pd.DataFrame | None, oos_real: pd.Series | None) -> list[tuple]:
    """One entry per period the data supports: values by metric, real by metric, is-combined."""
    cols = [c for c, _, _ in combine.METRICS]
    out = []
    if is_pop is not None:
        out.append(("Solo IS", {c: is_pop[c].to_numpy(float) for c in cols},
                    {c: float(is_real[c]) for c in cols}, False))
    if oos_pop is not None:
        out.append(("Solo OOS1", {c: oos_pop[c].to_numpy(float) for c in cols},
                    {c: float(oos_real[c]) for c in cols}, False))
    if is_pop is not None and oos_pop is not None:
        out.append((COMBINED, combine.population(is_pop, oos_pop),
                    combine.real_combined(is_real, oos_real), True))
    return out


def _trades_real(is_dir: Path, oos_dir: Path, strategy: str) -> dict | None:
    """Sharpe/Sortino of the real concatenated trades, None when either side lacks the export."""
    a, b = export.trades(is_dir, strategy), export.trades(oos_dir, strategy)
    if a is None or b is None:
        return None
    return combine.real_from_trades(pd.concat([a, b], ignore_index=True))


def run(strategy: str, directory: Path, cfg: dict) -> dict:
    """The reading and its design brief, as the contract dict.

    Args:
        strategy: Which strategy.
        directory: The export's `spp/` folder the report was pointed at — either SPP_IS or
            SPP_OOS; the design brief still comes from exactly this one, unchanged.
        cfg: What config.load() returned.

    Returns:
        The contract dict the window paints: panel 1 (histograms per period), panel 2 (IS
        against OOS1 overlaid) when both exports exist, and the noise verdict. Its summary
        carries `brief`, the `design_brief.json` the fabrication stage consumes — computed
        exactly as before, independent of the new panels.
    """
    started = time.time()
    found = reading.read(directory, strategy, cfg)
    brief = reading.brief(found, cfg)

    is_dir, oos_dir = _paired(directory)
    is_pop, is_real = _side(is_dir, strategy)
    oos_pop, oos_real = _side(oos_dir, strategy)
    periods = _periods(is_pop, is_real, oos_pop, oos_real)
    if len(periods) == 3:
        extra = _trades_real(is_dir, oos_dir, strategy)
        if extra:
            periods[2][2].update(extra)

    tabs = [contract.panel1(periods, cfg["panel1"]["band_share"])]
    notes = [{"code": "sin_emparejar", "state": "info",
              "text": "Una tirada SPP ancha no empareja y nunca emparejará: entre la IS y la OOS "
                      "de Strategy 17.9.39 hubo 6 tuplas en común de ~11.600. El periodo "
                      "combinado recompone lo que se puede (Net Profit, PF, Max Drawdown, "
                      "Ret/DD) y agrupa el resto (Sharpe, Sortino) como una sola muestra."}]
    if is_pop is not None and oos_pop is not None:
        tabs.append(contract.panel2(is_pop, oos_pop, is_real, oos_real))
    else:
        notes.append({"code": "sin_oos", "state": "info",
                      "text": "Solo hay export de un lado (IS u OOS) de este proyecto: no hay "
                              "con qué solapar IS y OOS1."})
    ident = output.identify(directory, [strategy])[strategy]
    return envelope.envelope(
        MODULE, strategy, ident, cfg, started, tabs, contract.verdict(found),
        notes + identity.warning(ident), GLOSSARY,
        summary={"verdict": brief["verdict"], "n_eff": brief["n_eff"],
                "live": len(brief["parameters"]), "frozen": len(brief["frozen"]),
                "brief": brief})
