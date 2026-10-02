"""The Spanish the study speaks: each null model's name and argument, the checks, the glossary."""

# The two tests the owner renamed 2026-09-30: no "1A"/"1B" anywhere a reader sees, ever. The
# internal keys ("random", "paired") stay — renaming them is a bigger change for no reader-facing
# gain — only the words a person reads change. Timing Alpha carries no decision criterion yet
# (owner, 2026-09-30): it is read, not judged.
TEST_1A = "Entrada aleatoria"
TEST_1B = "Timing Alpha"

# What each model is called on screen. The registry keys stay as they are — they are the
# contract trade_models.MODELS, config.yaml and every docstring share — and this is the only
# place a reader's name for one lives.
NAMES = {"segment_permute": "Shuffled Sequence", "resampled_holds": "Resampled Sequence",
         "fitted_holds": "Fitted Distributions Sequence", "block_shift": "Calendar Shift",
         "regime_strata": "Regime Strata"}

# One paragraph per model, written as a ladder: each says what it adds over the one before it,
# because that difference is the only reason to run more than one. The first three are the same
# family — the rhythm re-laid anywhere in the sample — and Calendar Shift is the one that is not.
EXPLAINED = {
    "segment_permute": (
        "<b>El punto de partida.</b> Coge la secuencia real de duraciones y esperas, "
        "<b>baraja su orden</b>, y la extiende desde una vela al azar de toda la muestra. "
        "Las duraciones y los huecos siguen siendo <i>exactamente los mismos</i> en conjunto "
        "— ni uno más ni uno menos — así que el tiempo total en mercado es idéntico al real. "
        "Lo que se destruye es el orden, las rachas y el calendario.<br><br>"
        "Contesta: <i>¿este mismo ritmo de operar, colocado en cualquier punto de la "
        "ventana del backtest, habría ganado lo mismo?</i> Una tirada puede caer en un tramo "
        "bueno y heredar su régimen, y por eso suele ser algo más difícil de batir que "
        "Calendar Shift — aunque no siempre. <b>La ventana es la del backtest</b>, no la del "
        "fichero de velas: si el backtest va de 2008 a 2022, ninguna simulación opera en "
        "2007 ni en 2023."),
    "resampled_holds": (
        "<b>La misma idea que Shuffle sequence, con reemplazo.</b> En vez de barajar el "
        "conjunto real de duraciones y esperas — cada una usada exactamente una vez —, las "
        "<b>sortea con reemplazo</b>: en una tirada dada, una duración real puede salir dos "
        "veces y otra ninguna. Consecuencia directa: el <b>tiempo total en mercado ya no es "
        "fijo</b> de tirada en tirada, mientras que en Shuffle sequence sí lo es.<br><br>"
        "Contesta: <i>¿el ritmo de operar de esta estrategia, leído como una población de "
        "duraciones posibles y no como esta lista concreta, vale algo?</i> Medido sobre estos "
        "datos da casi lo mismo que Shuffle sequence (σ dentro del 2%, p dentro de 0,005): una "
        "vez que la colocación es libre, dónde cae la tirada pesa mucho más que si el conjunto "
        "exacto de duraciones se conserva o no."),
    "fitted_holds": (
        "<b>Lo que añade sobre Resampled Sequence:</b> las duraciones ya <b>ni siquiera "
        "salen de las reales</b>. Se ajusta una distribución a ellas — binomial negativa si "
        "están sobredispersas, Poisson si no — y se sortean duraciones nuevas de esa "
        "distribución.<br><br>"
        "Contesta: <i>¿un sistema con esta</i> forma <i>de duraciones, entrando al azar, "
        "habría ido igual?</i> Es el único de los tres primeros que se separa de verdad de "
        "los otros dos, porque cambia el objeto medido y no solo su colocación. "
        "<b>Cuidado con esta flota</b>: sus duraciones son casi constantes, ninguna "
        "distribución las describe, y el panel imprime la dispersión y el KS al lado — si el "
        "ajuste no pega, este modelo es una afirmación sobre la distribución equivocada."),
    "block_shift": (
        "<b>Este no pertenece a la familia de los tres anteriores, y esa es toda la razón "
        "de que exista.</b> Los tres de arriba levantan la tirada entera y la sueltan en "
        "cualquier punto de los 22 años: cambian a la vez <i>cuándo</i> entra, el <i>orden</i> "
        "de las operaciones, su <i>calendario</i> y el <i>régimen de mercado</i> en que "
        "viven. Si uno de ellos da un p bajo, no sabes a cuál de esas cuatro cosas "
        "atribuirlo.<br><br>"
        "Calendar Shift mueve <b>cada operación por separado</b>, un número entero de "
        "semanas, y solo <b>dentro de su propio semestre</b> y cayendo en <b>el mismo día de "
        "la semana y a la misma hora</b>. Conserva por tanto tres cosas que los otros "
        "destruyen: el régimen (una operación de 2011 se compara contra 2011, no contra "
        "2020), el calendario (los huecos de fin de semana, las sesiones y el cierre del "
        "viernes son idénticos) y las rachas (una agrupación de operaciones sigue agrupada). "
        "<b>Es el único que cambia exactamente una cosa</b> — cuándo entra — y por eso el "
        "único cuyo p bajo se puede atribuir al acierto en el momento de entrar y a nada "
        "más. Es la `p` que sale en el Resumen.<br><br>"
        "El precio de esa precisión: al restringir tanto la colocación suele salirle una "
        "distribución algo más estrecha y un p algo más bajo — medido sobre 8 pares "
        "estrategia×mercado, <b>el p más bajo en 7 de ellos</b>, y la distribución más "
        "estrecha en 5. No es sistemáticamente el más exigente, es el <b>atribuible</b>. Así "
        "que <b>una estrategia que aguanta los cuatro dice bastante más que una que solo "
        "aguanta este</b>."),
    "regime_strata": (
        "<b>Opcional: sólo corre si lo añades a <code>nulls.models</code>.</b> Cada operación, "
        "con su duración, se recoloca en una vela al azar de <b>su mismo estado de "
        "régimen</b>: cuantil de ATR por signo de la tendencia reciente, leídos antes de que "
        "abra la vela. Fija el régimen por estado y no por un bloque de calendario de "
        "longitud arbitraria. Día, hora, orden y rachas quedan libres; si dos operaciones caen "
        "una encima de otra, la posterior se descarta.<br><br>Contesta: <i>¿entrando en velas "
        "del mismo tipo de mercado, pero en otro momento, habría ganado lo mismo?</i>"),
}

# The "?" of the KS warning (owner, 2026-09-30): what the test is and what its rejection costs.
KS_HELP = ("Kolmogorov–Smirnov compara la distribución ajustada a las duraciones con las "
           "duraciones reales. Si rechaza (p por debajo de alpha), el nulo de entrada aleatoria "
           "que sortea de esa distribución (Fitted Distributions Sequence) no reproduce las "
           "duraciones reales, y sus p-valores son cuestionables. Los otros modelos reutilizan "
           "las duraciones reales y no se ven afectados.")

# One line per model, for the list under the Entrada aleatoria tab; EXPLAINED is the long form.
SHORT = {
    "segment_permute": "Baraja el orden de las duraciones y esperas reales y las coloca desde "
                       "una vela al azar: mismo tiempo en mercado, otro momento.",
    "resampled_holds": "Como Shuffled Sequence, pero sortea las duraciones y esperas con "
                       "reemplazo: el tiempo total en mercado cambia de tirada en tirada.",
    "fitted_holds": "Sortea duraciones nuevas de una distribución ajustada a las reales "
                    "(binomial negativa o Poisson). Solo vale si el ajuste pega (KS).",
    "block_shift": "Mueve cada operación semanas enteras dentro de su semestre, mismo día y "
                   "hora: cambia solo cuándo entra. Es el p del resumen.",
    "regime_strata": "Recoloca cada operación en una vela al azar de su mismo régimen de "
                     "volatilidad y tendencia."}

# The report is read in Spanish; model/trade_models.RANDOMISES is code, and stays English.
RANDOMISES = {"segment_permute": "cuándo entra, el orden, las rachas y el régimen",
              "resampled_holds": "lo anterior, y además qué duraciones ocurren y el tiempo "
                                 "total en mercado",
              "fitted_holds": "lo anterior, y además las duraciones mismas, sacadas de una "
                              "distribución ajustada",
              "block_shift": "sólo cuándo entra, dentro de su semestre y en su día y hora",
              "regime_strata": "cuándo entra, dentro de velas de su mismo cuantil de "
                               "volatilidad y signo de tendencia; libera día, hora y rachas"}
DIAGNOSTICS = [("convention", "convención de fill", "la que reprodujo los precios de SQX"),
               ("fill_error", "error de fill (ATR)", "0 = las velas son las del backtest"),
               ("fill_offset", "spread de entrada (ATR)", "constante; lo paga también cada nulo"),
               ("on_open_price", "entradas al precio de su vela", "1,00 = ningún fill intravela"),
               ("on_bar_open", "entradas selladas en apertura", "sólo el reloj; no dispara nada"),
               ("off_grid", "operaciones que no ocupan ninguna vela",
                f"fuera de {TEST_1A}, {TEST_1B} y Exposición; dentro del beneficio"),
               ("calendar_kept", "calendario conservado", "1,00 en block_shift"),
               ("friday_exit", "salidas por cierre de viernes", "el nulo las reproduce"),
               ("atr_ratio", "volatilidad en las entradas", "1,00 = la media del mercado"),
               ("bar_cap", "salidas por tope de barras", "el resto salen por señal"),
               ("hold_median", "duración mediana (barras)", ""),
               ("point_value", "valor del punto medido", "de los propios trades, no supuesto"),
               ("cost_rate", "coste por operación", "fracción del precio")]


# What every number on the page means, in the owner's own terms. Plain text: the window prints it.
GLOSSARY = [
    {"term": "KS (Kolmogorov–Smirnov)", "text": KS_HELP},
    {"term": "El estadístico (mean_r)", "text": "Retorno logarítmico medio por operación, ya "
     "descontado el coste, dividido por el ATR mediano del mercado. Esa constante es la misma "
     "para el real y para los aleatorios, así que no mueve ningún p: sólo pone oro, plata y "
     "petróleo en el mismo eje."},
    {"term": "p-valor", "text": "Qué fracción de los backtests aleatorios igualó o superó al "
     "real. 0,03 son 3 de cada 100. No es la probabilidad de que la estrategia funcione."},
    {"term": "Ventaja", "text": "Real menos la mediana de los aleatorios: el tamaño del efecto, "
     "lo que hay que mirar cuando el p sale ajustado."},
    {"term": TEST_1B, "text": "Cada operación contra la media exacta de todas las ventanas de "
     "su misma duración en su mismo tramo. El coste se cancela: no dice si gana dinero, sólo si "
     "sus entradas eligen momento. Sin criterio de decisión propio todavía (2026-09-30): se lee, "
     "no se juzga."},
    {"term": f"$ acumulado ({TEST_1B})", "text": "Cuánto de lo que ganó la estrategia lo puso "
     "el momento de entrar, y no el simple hecho de estar dentro del mercado."},
    {"term": f"Sensibilidad de {TEST_1B}", "text": "El mismo test con ventanas centradas de "
     "±3, ±6 y ±12 meses y con semestres fijos. Un p que aguanta las cuatro no depende de esa "
     "elección."},
    {"term": "A y E (Exposición)", "text": "A es el exceso por vela sobre la vela media del mercado, "
     "definido siempre; E es el mismo cociente y sale con su intervalo de Fieller, no acotado "
     "cuando la deriva del mercado no se distingue de cero."},
    {"term": "Los modelos", "text": "No hay una única forma correcta de convertir un backtest "
     "en uno aleatorio. Se corren varios; decide Calendar Shift, el único que cambia "
     "exactamente una cosa."},
    {"term": "Sin veredicto por mercado", "text": "Ningún mercado se oculta por fallar una "
     "comprobación. El único veredicto del estudio es la amplitud, sobre todos a la vez."}]
