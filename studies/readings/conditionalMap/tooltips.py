"""One sentence per config.yaml knob, for the window's configuration drawer."""

TIPS = {
    "run.symbol": "El activo, para leer su tramo de construcción.",
    "run.feed": "El feed de barras sobre el que se sitúa cada entrada.",
    "run.timeframe": "La rejilla sobre la que se construyó la estrategia.",
    "run.sample": "Qué muestra se clasifica celda a celda, por su Sample type.",
    "volatility.atr_period": "Días de rango verdadero diario sobre los que se corta el "
                             "tercil de volatilidad realizada.",
    "trend.window": "Días detrás de cada entrada sobre los que se mide el ratio de "
                    "eficiencia (tendencia contra ruido).",
    "sessions.asia": "Zona y horas locales de Tokio (apertura, cierre) que definen Asia.",
    "sessions.london": "Zona y horas locales de Londres.",
    "sessions.new_york": "Zona y horas locales de Nueva York.",
    "bootstrap.resamples": "Remuestreos detrás del intervalo de cada celda.",
    "bootstrap.confidence": "Cobertura de ese intervalo.",
    "bootstrap.seed": "Semilla del remuestreo, para que dos lecturas coincidan."}
