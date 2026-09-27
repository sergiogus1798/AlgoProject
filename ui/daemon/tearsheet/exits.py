"""P&L and expectancy by exit reason as a contract result: tabs «IS» and «OOS», each on its own."""

from datetime import datetime

import pandas as pd

from core.study import blocks, result
from ui.daemon.tearsheet import tradestats
from ui.daemon.tearsheet.sheet import MODULE, SAMPLE


def tab(sample: str, trades: pd.DataFrame, day: str) -> dict:
    """One sample's exits: the table per exit type and one cumulative line per type.

    Args:
        sample: "IS" or "OOS".
        trades: Its trades, ascending in close time.
        day: The cosecha's day, for the note.

    Returns:
        A contract tab. Exit types are spelled as the export writes them, with no renaming
        table that could drop a type nobody listed.
    """
    rows = tradestats.by_exit(trades)
    pnl = trades["Profit/Loss"]
    note = (f"Por tipo de salida de la columna «Close type» de trades.parquet. Las filas suman "
            f"{int(rows['ops'].sum())} operaciones y {rows['neto'].sum():.2f} de P&L neto: las "
            f"{len(trades)} operaciones y los {pnl.sum():.2f} de toda la muestra. «ops» cuenta "
            "operaciones; «neto» y «medio», su P&L sumado y medio; «% gan.», las de P&L > 0; "
            "MAE y MFE medios en dinero, tal como los exporta SQX.")
    if len(rows) == 1:
        note += f" Esta muestra sale por un solo tipo: «{rows['salida'].iloc[0]}»."
    table = blocks.table("Resultado por tipo de salida", rows, note, digits=12)
    x, paths = tradestats.exit_paths(trades)
    lines = {"kind": "lines", "title": "P&L acumulado por tipo de salida", "unit": "$", "x": x,
             "series": [{"label": t, "values": v, "role": "real"} for t, v in paths.items()],
             "note": "Cada línea acumula solo el P&L de las operaciones que cerraron por ese "
                     "tipo, a lo largo de todas las operaciones de la muestra por fecha de "
                     "cierre; entre dos de las suyas se queda plana."}
    tab_note = (f"{SAMPLE[sample]}, {len(trades)} operaciones, cosecha {day}. Solo esta "
                "muestra: nada mezcla IS y OOS.")
    return result.tab(sample, SAMPLE[sample], [table, lines], note=tab_note)


def build(data: dict) -> dict:
    """The exits of one strategy, IS and OOS apart.

    Args:
        data: What `harvest.read` returned.

    Returns:
        A contract result (validated); a sample without trades has no tab.
    """
    tabs = [tab(s, t, data["day"]) for s in ("IS", "OOS")
            if not (t := data["trades"][data["trades"]["sample"] == s]).empty]
    return blocks.validate({
        "module": MODULE, "strategy": data["strategy"], "identity": data["identity"],
        "computed_at": datetime.now().isoformat("T", "seconds"), "verdict": None,
        "tabs": blocks.plain(tabs), "warnings": [], "glossary": [], "harvest_day": data["day"]})
