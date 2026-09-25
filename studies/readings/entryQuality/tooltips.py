"""One sentence per config.yaml knob, for the window's configuration drawer."""

TIPS = {
    "run.sample": "Qué muestra se lee, por su Sample type.",
    "run.feed": "El feed de barras sobre el que se recorre cada entrada.",
    "run.timeframe": "La rejilla sobre la que se construyó la estrategia; el retraso también "
                     "se mide en M1.",
    "run.atr": "Periodo del ATR por el que se divide cada recorrido, leído en la barra "
               "anterior a la entrada.",
    "eratio.horizon": "Barras que se recorren hacia delante desde cada entrada.",
    "eratio.marks": "Los horizontes que enseña la tabla.",
    "eratio.draws": "Juegos de entradas al azar detrás de la banda del 5-95 %.",
    "eratio.seed": "Semilla de esos juegos, para que dos lecturas coincidan.",
    "delay.bars": "Retrasos, en barras de la propia estrategia.",
    "delay.minutes": "Los mismos retrasos, en minutos.",
    "verdict.dcr_high": "Parte de la esperanza bruta que una barra de retraso puede llevarse "
                        "antes de llamarlo frágil a la latencia."}
