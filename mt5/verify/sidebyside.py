"""Every SQX entry beside the MT5 trade each firm's EA opened for it: one row per entry, one set of columns per firm."""
import pandas as pd

from core.study import blocks
from mt5.verify import firms

ROWS = 500          # the table's last N entries: a whole history is thousands of rows


def table(pieces: dict[str, dict]) -> dict:
    """The side-by-side trades table (owner, 2026-09-30: paired by entry time).

    Args:
        pieces: {firm: `judge.firm_result`}, each with its `pairs` (its own SQX retest,
            shifted to the firm's server clock, each row with the MT5 trade of the same side
            that opened within the entry tolerance, or none) and its clock shift `hours`.

    Returns:
        A "table" block: the entry in SQX's feed clock and its side, then per firm the USD
        P&L of its SQX retest as SQX booked it, the MT5 entry in its server's clock and the
        MT5 P&L as MT5 booked it — empty when the EA opened nothing there. USD is shown; the
        criteria compare points (`compare.in_points`). `firm_columns` lets the window drop a firm's three
        columns when its light is off. Each firm's SQX retest carries its own costs, so the
        rows are the union of their entries, keyed on the unshifted open time and side.
    """
    frames = []
    for firm, piece in pieces.items():
        p, label = piece["pairs"], firms.label(firm)
        frames.append(pd.DataFrame({
            "entrada SQX": pd.to_datetime(p["Open time"]) - pd.Timedelta(hours=piece["hours"]),
            "tipo": p["Type"], f"{label} · P&L SQX": p["Profit/Loss USD"],
            f"{label} · entrada MT5": pd.to_datetime(p["Open time_mt5"]).dt.strftime(
                "%Y-%m-%d %H:%M").fillna(""),
            f"{label} · P&L MT5": p["Profit/Loss USD_mt5"]}).set_index(["entrada SQX", "tipo"]))
    merged = pd.concat(frames, axis=1).sort_index().tail(ROWS).reset_index()
    merged["entrada SQX"] = merged["entrada SQX"].dt.strftime("%Y-%m-%d %H:%M")
    out = blocks.table("Operaciones de SQX y de MT5, lado a lado", merged,
                       f"Una fila por entrada de SQX (las últimas {ROWS} como mucho), en la hora "
                       "de su feed. Cada empresa: el P&L de su retest de SQX con sus costes, y la "
                       "operación de su EA en MT5 que abrió en la misma dirección dentro de la "
                       "tolerancia de entrada, en la hora de su servidor. Vacío = el EA no abrió "
                       "esa operación.")
    out["firm_columns"] = {firm: [2 + 3 * i, 3 + 3 * i, 4 + 3 * i]
                           for i, firm in enumerate(pieces)}
    return out
