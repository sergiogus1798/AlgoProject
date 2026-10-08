"""The words step 18 is read with: the state's labels and meanings, one line per statistic, the glossary."""

LABEL = {"pasa": "PASA — no descarta", "limbo": "LIMBO", "no_pasa": "NO PASA"}
STATE = {"pasa": "pass", "limbo": "watch", "no_pasa": "fail"}
STABLE = " · orden estable"

MEANING = {
    "pasa": "Elegir la mejor variante del pasado no lleva a algo que pierda fuera, y no "
            "perjudica más de lo que daría el ruido. No descarta: no dice que la madre tenga "
            "ventaja.",
    "estable": " Además el PBO queda por debajo del p5 de su nulo con el exceso neto y con el "
               "bruto: el orden entre variantes se repite más de lo que daría el azar, y no "
               "por los costes.",
    "limbo": "La variante elegida pierde fuera de muestra en el {got:.1%} de las "
             "particiones, más que el p{pct:g} de su propio nulo ({top:.1%}), sin llegar al "
             "{fail:.0%}: pierde más veces de lo que saldría de elegir entre variantes "
             "iguales, todas con el Sharpe mediano del panel.",
    "perdida": "La variante elegida pierde fuera de muestra en el {got:.1%} de las "
               "particiones (corte: {fail:.0%}): elegida la mejor del pasado, típicamente "
               "pierde.",
    "p95": "El PBO ({got:.1%}) llega al p95 de su propio nulo ({p95:.1%}): elegir perjudica "
           "más allá del ruido.",
    "sin_dato": "Sin dato: quedan {n} variantes tras los filtros, menos de {need}. No hay "
                "nada que juzgar."}

# One line per statistic shown (the owner reads none without it).
WHAT = {
    "pbo": "Fracción de las 12.870 particiones en que la variante elegida dentro queda en la "
           "mitad mala fuera. Sin nada que elegir ronda el 50 % con un margen ancho: sólo se "
           "lee contra su nulo.",
    "pbo_bruto": "El mismo PBO antes de costes. Las variantes que operan más pagan más en "
                 "todas las mitades y eso fabrica un orden que no es de la lógica.",
    "beta": "Pendiente de la recta «Sharpe fuera de la elegida» contra «su Sharpe dentro», "
            "un punto por partición. Negativa por construcción (el balancín): se lee contra "
            "el nulo.",
    "r2": "Cuánto de la dispersión del Sharpe fuera explica esa recta (R² ajustado).",
    "p_perdida": "Fracción de particiones en que la elegida tiene Sharpe ≤ 0 fuera. Las "
                 "columnas del nulo son la pérdida que sale sólo del balancín, con todas las "
                 "variantes al Sharpe mediano del panel: por encima de su p95 es LIMBO.",
    "hc": "Recorte del Sharpe: 1 − mediana del Sharpe fuera / mediana del Sharpe dentro de "
          "la elegida. Lo que hay que descontar al backtest por haber elegido el mejor punto; "
          "cota pesimista.",
    "p": "Fracción de sorteos del nulo con un valor igual o menor que el real, contando el "
         "real. Cerca de 0: por debajo del ruido; cerca de 1: por encima.",
    "primer_orden": "F_elegir ≤ F_azar en todo listón (con la tolerancia de la "
                    "configuración): sea cual sea el mínimo exigido, elegir deja menos veces "
                    "por debajo.",
    "segundo_orden": "La misma comparación sobre lo acumulado desde abajo: lo prefiere "
                     "cualquiera con aversión al riesgo.",
    "brecha": "El mayor exceso de F_elegir sobre F_azar; 0 o negativo es dominancia estricta.",
    "puesto_mediano": "Puesto relativo de la madre fuera de muestra entre las variantes, "
                      "mediana de las particiones (0,5 = en el medio).",
    "sobre_mediana": "Fracción de particiones en que la madre queda por encima de la mitad "
                     "de sus variantes fuera.",
    "madre_perdida": "Fracción de particiones en que la madre tiene Sharpe ≤ 0 fuera.",
    "duplicados": "Variantes cuya lista de operaciones es idéntica, operación por operación, "
                  "a la de otra: dice cuántos parámetros actúan de verdad.",
    "potencia": "Fracción de sorteos, con ese Sharpe anual plantado en el {share:.0%} de las "
                "variantes, en que el PBO cae bajo el p5 del nulo: qué diferencia real ve el "
                "CSCV en esta madre. Sin nada plantado sería un 5 %.",
    "seleccion": "Fracción de las particiones en que cada variante sale elegida. Muchas "
                 "variantes con poco peso: no hay una mejor estable."}

NOTE = {
    "nulo": "Cada sorteo iguala todas las variantes al Sharpe mediano del panel, remuestrea "
            "las semanas con reposición (bloques de {weeks} semanas de media, las mismas "
            "para todas) y pasa el CSCV entero. La línea es el PBO real.",
    "logit": "λ = ln(ω / (1 − ω)), con ω el puesto relativo fuera de la elegida. A la "
             "izquierda de 0 la elegida quedó en la mitad mala: el PBO es esa fracción.",
    "nube": "Un punto por partición (se dibujan {shown} de {total}; la recta usa todas). "
            "Sharpe anualizado con √52.",
    "curvas": "Función de distribución del Sharpe fuera de muestra: de la elegida, de todas "
              "las variantes (elegir al azar) y de la madre. Más a la derecha y más abajo es "
              "mejor.",
    "madre": "La madre se eligió mirando build, que cae dentro en muchas particiones: su "
             "lectura sale algo inflada a su favor. Sólo se anota.",
    "coste": "Lo que costó la corrida. La cola reparte entre procesos el CSCV real, el nulo "
             "sobre neto y sobre bruto y cada Sharpe plantado."}

GLOSSARY = [
    {"term": "CSCV", "text": "Combinatorially Symmetric Cross-Validation, de Bailey, Borwein, "
     "López de Prado y Zhu («The Probability of Backtest Overfitting»): el histórico se corta "
     "en 16 bloques y cada una de las 12.870 formas de tomar 8 como «dentro» elige la mejor "
     "variante por Sharpe y la puntúa en los otros 8."},
    {"term": "Celdas", "text": "Exceso semanal de cada variante: la suma del resultado de sus "
     "operaciones que cierran esa semana menos la deriva del mercado cobrada durante cada "
     "operación. Neto de costes; el bruto se usa sólo para la etiqueta «orden estable»."},
    {"term": "Nulo", "text": "El mismo panel sin nada que elegir: todas las variantes con el "
     "mismo Sharpe (el mediano del panel) y las semanas remuestreadas con reposición "
     "(remuestreo estacionario de Politis y Romano). Da el margen de error que el artículo "
     "no trae."},
    {"term": "Balancín", "text": "Dentro y fuera son las dos mitades del mismo total: una "
     "variante alta dentro tiene que salir algo más baja fuera. Por eso β es negativa y hay "
     "pérdida fuera aunque no haya sobreajuste."},
    {"term": "Orden estable", "text": "El PBO queda en o bajo el p5 de su nulo con el exceso "
     "neto y con el bruto."},
    {"term": "Dominancia", "text": "Se compara el Sharpe fuera de la elegida (uno por "
     "partición) con el de TODAS las variantes en todas las particiones, que es elegir al "
     "azar."}]
