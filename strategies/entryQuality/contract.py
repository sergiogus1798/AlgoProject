"""The two readings as the contract's tabs: the entry against random entries, and the delay."""

from core.study import blocks, result as envelope
from strategies.entryQuality import eratio, verdict

STATE = {"signal": "pass", "no_signal": "watch", "latency_fragile": "watch",
         "latency_robust": "pass"}
GLOSSARY = [
    {"term": "e(k)", "text": "Recorrido medio a favor entre recorrido medio en contra, k "
     "barras después de entrar, en unidades del ATR de la barra anterior. Una razón de medias, "
     "no una media de razones."},
    {"term": "Banda", "text": "El p5–p95 de e(k) con entradas al azar a las mismas horas y "
     "con los lados de la estrategia barajados."},
    {"term": "DCR", "text": "Qué parte de la esperanza bruta se entrega por entrar d barras "
     "tarde."}]


def reading(label: str) -> dict:
    """One reading's label and what it means, as a verdict block."""
    return blocks.verdict(label, STATE[label], verdict.MEANS[label])


def eratio_tab(found: dict, cfg: dict) -> dict:
    """Did price run further in favour than against, more than a random entry would have?"""
    real, bands = found["real"], found["bands"]
    k = list(range(1, len(real) + 1))
    sides = found["sides"]
    side_series = [{"label": f"{name} ({sides[f'n_{name}']})", "values": list(sides[name]),
                    "role": "sim"} for name in ("largos", "cortos") if name in sides]
    return envelope.tab("eratio", "3 · Calidad de la entrada", [
        reading(verdict.signal(real, bands)),
        {"kind": "lines", "title": "e(k) contra entradas al azar", "unit": "", "x": k,
         "series": [{"label": "e(k) real", "values": list(real), "role": "real"},
                    {"label": "p95 al azar", "values": list(bands["high"]), "role": "reference"},
                    {"label": "mediana al azar", "values": list(bands["median"]),
                     "role": "reference"},
                    {"label": "p5 al azar", "values": list(bands["low"]), "role": "reference"},
                    *side_series],
         "note": f"{bands['draws']} juegos de entradas al azar, emparejados por hora del día y "
                 f"por la proporción de largos y cortos. Máximo de e(k) en k={found['peak']}; "
                 f"duración mediana real {found['hold']}."},
        blocks.table("En algunos horizontes",
                     eratio.table(real, bands, cfg["eratio"]["marks"]).reset_index())],
        note="¿La entrada predice movimiento favorable, o daría igual entrar a cualquier hora "
             "a la que opera? El camino empieza en la barra siguiente a la entrada y nunca "
             "toca las salidas de la estrategia.")


def delay_tab(found: dict, cfg: dict) -> dict:
    """How much of the edge entering d bars late gives up, with the exits left where they were."""
    tf = cfg["run"]["timeframe"]
    return envelope.tab("delay", "4 · Lo que cuesta llegar tarde", [
        reading(verdict.latency(found["on_tf"], cfg["verdict"]["dcr_high"])),
        blocks.table(f"En barras de {tf}", found["on_tf"].reset_index(drop=True)),
        blocks.table("En minutos", found["on_m1"].reset_index(drop=True))],
        note="Tier 1: las mismas salidas, la entrada desplazada. Una barra de retraso que se "
             "lleva mucho del edge es fragilidad a la latencia, o información del futuro en la "
             "entrada.")
