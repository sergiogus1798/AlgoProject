# Paso 22 — Mapa condicional: qué clasifica, con qué fórmulas, qué se lee en cada celda y qué criterio hay cargado

**Fecha:** 2026-10-08 · **Para:** el dueño, que va a fijar los criterios él mismo · **Alcance:** sólo el paso 22 de `docs/AgentPDFs/WORKFLOW.md` — `studies/readings/conditionalMap/` entero, la pieza de `engines/regimes/` que usa, su capítulo del manual (`53-mapa-condicional.md`) y lo que el autopiloto hace con el paso.

Revisado por dos miembros del Council (Feynman, Taleb) el 2026-10-08; correcciones aplicadas. Las cifras que aportaron los revisores van marcadas «(calculado por el revisor)».

**Qué es:** el documento de consulta del paso 22, con la misma forma que el del paso 16 (`criterios-paso-16-spp-2026-10-07`). Explica desde cero cómo se define cada estado del mercado, cómo cae una operación en una celda, qué número sale de cada celda y con qué incertidumbre, cuántas celdas se miran a la vez y qué supone eso, y qué hay cargado hoy como criterio (nada). Cierra con lo que no cuadra y con las decisiones que te quedan.

**De dónde salen los números.** Los ejemplos son de la corrida del autopiloto `Test_USDJPY_M30_doubleROCLong / 20261006-201740` (USDJPY, M30, largas): el paso 22 corrió el 2026-10-06 de 21:35:08 a 21:35:16 sobre las tres madres que quedaban — `Strategy 10.23.380`, `3.13.366` y `4.25.395` — leyendo la cosecha `harvest/Test_USDJPY_M30_doubleROCLong/Results/2026-10-06`. Es la corrida más reciente con salidas del paso y está hecha con el código actual (el último cambio del módulo es del 2026-10-04). **He recalculado los seis mapas** (tres madres × dos muestras) con el código del estudio desde la cosecha y las barras: las seis tablas «Celda a celda» guardadas coinciden con las recalculadas, cifra a cifra. Para un punto concreto (§5.1) cito además lo guardado en `Test_USA500_H1_indicesIBS` (2026-10-06) y `Test_NIKKEI225_M30_simpleL_live` (2026-10-05). Todo lo que el estudio no publica y he medido yo va marcado **«calculado por mí»**, con sus tiradas, sus supuestos y su script en `scratchpad/paso22/` (`recalc.py`, `null.py`, `null_realmean.py`, `extra.py`, `drift.py`). En la carpeta de informes de ese día hay otras tres madres (`14.22.275`, `8.16.266`, `9.23.278`, de las 16:55): son de una corrida anterior del mismo día cuya cosecha se sobrescribió, así que no se pueden recalcular y no las uso.

**El commit que describo:** `b2b4c8c`. **Cambios sin confirmar en ficheros del paso:** ninguno en `studies/readings/conditionalMap/`, `engines/regimes/`, `tests/test_conditionalmap.py`, `pipeline/autopilot/tail.py` ni `pipeline/autopilot/closing.py`. Sí los hay en `bin/workflow.sh`, `pipeline/autopilot/tailrun.py` y `ui/daemon/results/forproject.py`; describo el árbol de trabajo tal como está hoy, y las líneas que cito de esos tres son las del árbol, no las del commit.

**Ninguna línea de este documento está congelada.** El paso no tiene criterio que congelar: no juzga.

---

## 0. En una página

**La pregunta del paso.** No «¿qué filtro añado?», sino «¿de qué depende que esta estrategia gane?». Se etiqueta cada operación con el estado del mercado en el momento de entrar y se mira si el resultado cambia de un estado a otro.

**Lo que hay cargado hoy:** **nada.** `pipeline/autopilot/criteria.yaml` no tiene entrada para el paso 22, `pipeline/autopilot/facts.py` no publica ningún hecho suyo, `ledger/thresholds.yaml` no tiene ninguna clave suya, y el resultado sale con `verdict: null`. El autopiloto lo corre (8 segundos para tres madres), guarda un JSON y un HTML por madre y sigue. Nada posterior lo lee.

**Lo que salió en la corrida real** (recalculado por mí; coincide con lo guardado):

| madre | ops OOS1 | P&L medio OOS1 | celdas con ≥ 30 ops (de 50) | intervalo fuera del cero | ops Completa | P&L medio Completa | celdas con ≥ 30 ops (de 50) | intervalo fuera del cero |
|---|---|---|---|---|---|---|---|---|
| 10.23.380 | 402 | −61,20 USD | 19 | 0 | 1.138 | +45,81 USD | 33 | 3 |
| 3.13.366 | 331 | +0,89 USD | 16 | 1 | 933 | +80,22 USD | 29 | 3 |
| 4.25.395 | 240 | +67,75 USD | 13 | 0 | 660 | +119,76 USD | 27 | 5 |

En total el mapa enseñó 137 celdas de 300 posibles y en 12 el intervalo no toca el cero (las 12 por arriba). **Cuántas cabía esperar si el resultado no dependiera en absoluto de la celda: 12,6** (calculado por mí, §5.2; barajando el resultado entre las operaciones 1.000 veces por mapa y **conservando la media real de cada estrategia**: con media cero el azar daría 6,3, calculado por el revisor rehaciendo la cuenta con el código del estudio). El recuento de celdas con el cero fuera (12) no se distingue del que da el azar. Es una prueba de recuento con poca potencia, no un veredicto por celda: supone operaciones intercambiables, y el azar da entre 7 y 18 el 90 % de las veces (calculado por el revisor con el mismo nulo, suponiendo los seis mapas independientes). Por muestras: en OOS1, 1 celda frente a 2,7 esperadas; en la Completa, 11 frente a 9,8 (calculado por el revisor). Comparando cada celda con el resto de su estrategia y corrigiendo por todas las celdas enseñadas, ningún mapa baja de p = 0,13 (calculado por el revisor, §5.10).

**Las diez cosas que conviene saber:**

1. **Son 50 celdas por muestra y 100 por estrategia, no «tres cortes».** Volatilidad × tendencia (9), sesión × día (30), sesión sola (6) y día solo (5), todo dos veces: una con OOS1 y otra con la muestra «Completa» (build + OOS1). El aviso del propio estudio y el manual hablan de «tres cortes y varias celdas».
2. **El código no aplica ninguna corrección por mirar tantas celdas.** Sólo lo avisa con un texto fijo. Con una estrategia sin ninguna ventaja, la probabilidad de ver al menos una celda «significativa» es del 41–56 % en OOS1, del 69–78 % en la Completa y, mirando las dos, entre esos 69–78 % (la Completa sola) y el 82–90 % que sale de tratarlas como independientes, que no lo son porque las operaciones de OOS1 están dentro de la Completa (calculado por mí, §5.2; el revisor confirma que las operaciones de OOS1 son el 35–36 % de la Completa: 402 de 1.138, 331 de 933, 240 de 660).
3. **Los cortes de volatilidad están en unidades de precio y se congelan sobre `build`; en los índices eso deja el eje de volatilidad sin sentido.** En USA500 el 99,7 % de los días de `oos1` cae en «alta»; en NIKKEI225, el 95,9 %; en USDJPY el 76 % cae en «baja» (calculado por mí, §5.1). Los mapas guardados de USA500 y NIKKEI lo confirman: en OOS1 sólo tiene operaciones la fila «alta». Dividir el ATR por el precio no lo arregla (§5.1). Medido en 4 de los 27 activos de la política: en los cuatro la fila «media» se queda con menos del 9 % de los días de `oos1` (USDJPY 7,5 %, XAUUSD 8,8 %, NIKKEI225 4,0 %, USA500 0,3 %): fuera de `build` el eje de volatilidad tiene una o dos filas, no tres, en todos los activos medidos (calculado por el revisor a partir de `drift.out`). Los otros 23 no están medidos.
4. **La «tendencia» no tiene signo.** El ratio de eficiencia vale lo mismo para una subida recta que para una caída recta. En una plantilla de largos, «tendencia alta» mezcla los dos casos.
5. **El intervalo de cada celda es contra el cero, no contra el resto de la estrategia.** En la muestra Completa la estrategia gana de media (se construyó ahí), así que muchas celdas excluyen el cero simplemente porque la estrategia gana, no porque dependan del estado. En estas madres el P&L medio de `build` es +104, +124 y +150 USD y el de OOS1 −61, +1 y +68; `build` pone dos de cada tres operaciones de la Completa, y 11 de las 12 celdas con el cero fuera están ahí (calculado por el revisor).
6. **El suelo de 30 operaciones es prestado de otro test** (el p-valor de la puerta OOS). Con 30 operaciones el intervalo de estas madres mide ±348 a ±491 USD de ancho a cada lado, frente a un P&L medio por operación de 46 a 120 USD: una celda de 30 no puede distinguir nada (calculado por mí, §5.4).
7. **Una celda no son N operaciones independientes.** La celda más llamativa de la corrida (`3.13.366`, OOS1, volatilidad alta × tendencia alta: +386,83 USD, intervalo 75,62 a 751,82) tiene 32 operaciones, pero el 94 % son de 2022, vienen de 9 episodios de mercado y tres operaciones suman el 68 % de su ganancia. La misma celda en sus dos hermanas da −78 y +133 (§3.11).
8. **41 de las 50 celdas son de reloj o calendario** (sesión y día de la semana). La regla dura 15 prohíbe al constructor esos bloques; **mientras se lea como prohibición para el constructor y para las plantillas, ninguna de esas 41 puede ser condición de entrada**. Si se leyera sólo como lo que el constructor sortea, una condición horaria fija en plantilla no está prohibida expresamente: es una pregunta tuya pendiente (§6, decisión 9). Sólo las 9 de volatilidad × tendencia tienen traducción a bloques permitidos (§5.9). De las 12 celdas con el cero fuera de esta corrida, 8 son de estas 41 (calculado por el revisor).
9. **El camino que el aviso promete no existe.** «Un filtro nuevo se anota en el ledger y se revalida sobre datos que no se hayan mirado»: no hay ninguna clave del mapa en `ledger/thresholds.yaml`, ningún comando que apunte la hipótesis, y no hay asignado ningún tramo de datos donde revalidarla. `oos2` no tiene reserva dura para ti (dueño, 2026-09-28; `WORKFLOW.md:146-155`): lo leen 17, 18, 18.5, 19 y 24 (y el 20), la reserva rige sólo para un agente autónomo, y cada mirada queda contada en el ledger; gastarlo aquí es decisión tuya (§6, decisión 10).
10. **Mirar el mapa ya es seleccionar, y `oos1` no llega virgen.** El paso no filtra, pero si después de mirarlo te quedas con una madre y no con otra, esa elección es una selección hecha sobre `oos1` que hoy no se apunta en ningún sitio. Además `oos1` ya sirvió para elegir a estas madres en los pasos 7 a 16 (`WORKFLOW.md:144`) (§5.11).

---

## 1. Qué es el paso y cómo decide

### 1.1 La mecánica en cuatro pasos

1. **Lee** las operaciones de una estrategia de la cosecha que dejó la puerta OOS del paso 8 (`trades.parquet`: hora de apertura, P&L y tipo de muestra de cada operación) y las barras del feed.
2. **Calcula dos series diarias** del mercado: la volatilidad (ATR de 20 días) y la tendencia (ratio de eficiencia de 20 días), ambas tal como estaban **al cierre del día anterior**.
3. **Etiqueta** cada operación con cuatro cosas: el tercil de volatilidad y el de tendencia del día en que entra, la sesión de mercado de la hora en que entra y el día de la semana.
4. **Agrupa** las operaciones por etiqueta y, de cada grupo («celda») con al menos 30 operaciones, escribe cuatro números: cuántas son, el P&L medio, un intervalo del 95 % para ese medio y la proporción de ganadoras.

### 1.2 Cómo decide

**No decide.** El resultado no lleva veredicto (`one.py:86-91` pasa sólo pestañas, avisos y resumen; el JSON guardado dice `"verdict": null`), todos sus bloques van con `state: "info"`, y el catálogo de la ventana lo declara «describe» (`ui/daemon/results/catalogue.py:89`). El autopiloto no lo juzga porque `criteria.yaml` no le da reglas (§4).

### 1.3 Por qué «fabrica hipótesis, no filtra»

Un test contrasta **una** pregunta escrita de antemano («¿gana más que entrar al azar?»). El mapa hace lo contrario: no trae pregunta, parte la muestra de cien maneras y enseña lo que sale. Lo que sale de ahí es una **sospecha** («parece que pierde los viernes»), y una sospecha encontrada mirando los datos no se puede dar por comprobada con esos mismos datos: se eligió precisamente porque en ellos destacaba. Por eso el módulo se impone tres reglas (README del módulo, §«The three rules»): no mirar al futuro al etiquetar, no enseñar celdas pequeñas, y no dejar salir ningún filtro. §2.5 explica con números por qué la tercera regla no es prudencia sino aritmética.

---

## 2. Fundamentos: lo que hace falta para leer el mapa

### 2.1 La vela diaria

El estado del mercado se define sobre velas **de un día**, opere la estrategia en M30 o en H1. El estudio las fabrica juntando las barras del feed por día de calendario del reloj del feed: apertura de la primera barra, máximo, mínimo y cierre de la última (`engines/regimes/regime.py:19-21`).

El reloj del feed no es el de aquí. Los feeds actuales (`USDJPY_M1`) van en «EETUS», que es la hora de Nueva York más siete horas. La medianoche del feed son las 17:00 de Nueva York: **un «día» del feed es una jornada de divisas entera**, de las 17:00 de Nueva York a las 17:00 del día siguiente. El «lunes» del feed empieza el domingo a las 17:00 de Nueva York.

### 2.2 La volatilidad: rango verdadero y ATR

**Rango verdadero de un día** = la mayor de tres distancias: máximo − mínimo; |máximo − cierre de ayer|; |mínimo − cierre de ayer|. Las dos últimas existen para contar los huecos.

Ejemplo a mano, en yenes por dólar:

| día | máximo | mínimo | cierre | cierre de ayer | máx − mín | \|máx − ayer\| | \|mín − ayer\| | rango verdadero |
|---|---|---|---|---|---|---|---|---|
| A | 150,80 | 150,00 | 150,50 | 150,20 | 0,80 | 0,60 | 0,20 | **0,80** |
| B (abre con hueco) | 151,90 | 151,20 | 151,60 | 150,50 | 0,70 | 1,40 | 0,70 | **1,40** |

El día B se movió 1,40 desde el cierre anterior aunque su vela sólo mida 0,70.

**ATR** («rango verdadero medio») es una media de esos rangos que da más peso a los días recientes. La cuenta de cada día es:

> ATR de hoy = ATR de ayer + (rango verdadero de hoy − ATR de ayer) / 20

Si el ATR de ayer era 1,00 y hoy el rango es 1,40: 1,00 + 0,40 / 20 = **1,02**. Cada día mueve la media una vigésima parte de la sorpresa.

**«20 días» no es una ventana de 20 días.** Es una memoria que se apaga poco a poco: el día de hoy pesa un 5 %, el de ayer un 4,75 %, y así. Los últimos 20 días suman el 64 % del peso y hace falta retroceder unos 13,5 días para que un día pese la mitad que hoy. El código lo hace con `ewm(alpha=1/20, adjust=False, min_periods=20)` (`engines/regimes/regime.py:40-44`): no tiene ningún parámetro ajustado, y por eso se eligió («una definición de régimen con mandos es un sitio donde seguir eligiendo hasta que las celdas digan algo», docstring de la función).

**Con datos reales** (USDJPY, recalculado por mí): la serie que lee una entrada del 2018-01-02 vale 0,6190; ese día el rango fue 112,790 − 112,055 = 0,735, así que la del 2018-01-03 es 0,6190 + (0,735 − 0,6190) / 20 = **0,6248**, que es lo que da el código. Está en yenes: 0,62 son 62 pips de rango diario medio.

Dos advertencias de vocabulario. La fila del WORKFLOW dice «volatilidad realizada»; lo que se calcula es el ATR, que es una medida de **rango**, no la desviación típica de los rendimientos que suele llamarse así. Y el ATR está **en unidades de precio**, no en porcentaje: si el precio se duplica, el ATR se duplica aunque el mercado esté igual de tranquilo (§5.1).

### 2.3 La tendencia: el ratio de eficiencia de Kaufman

> ratio = |cierre de hoy − cierre de hace 20 días| / suma de los 20 movimientos diarios en valor absoluto

Es «cuánto avancé» dividido por «cuánto caminé». Vale 1 si los 20 días fueron todos en la misma dirección, y cerca de 0 si el precio fue y vino para acabar donde empezó (`studies/readings/conditionalMap/regime.py:84-87`).

Ejemplo a mano con una ventana de 5 días en vez de 20:

| serie de cierres | avance neto | camino recorrido | ratio |
|---|---|---|---|
| 100 → 101 → 100,5 → 102 → 101,5 → 103 | \|103 − 100\| = 3 | 1 + 0,5 + 1,5 + 0,5 + 1,5 = 5 | **0,60** |
| 100 → 101 → 100 → 101 → 100 → 100,5 | 0,5 | 1 + 1 + 1 + 1 + 0,5 = 4,5 | **0,11** |
| 103 → 101,5 → 102 → 100,5 → 101 → 100 | \|100 − 103\| = 3 | 5 | **0,60** |

La tercera fila es la primera al revés: una **caída** igual de limpia da el mismo 0,60. **El ratio no sabe si el mercado sube o baja**; sólo si va recto. Aquí la ventana sí es dura: exactamente los últimos 20 cierres.

### 2.4 Terciles, y qué quiere decir «congelados»

Partir en terciles es ordenar todos los valores y cortar en dos puntos para que quede un tercio en cada trozo. Con nueve valores 1, 2, …, 9, los cortes caen en 3,67 y 6,33: «baja» son 1-2-3, «media» 4-5-6, «alta» 7-8-9.

La pregunta que importa es **con qué valores se calculan los cortes**. Hay dos formas malas:

- Con los valores de **la muestra que se está leyendo** (los días de OOS1): cada operación quedaría etiquetada con información de días posteriores a ella. Es mirar al futuro.
- Con los valores de **los días en que la estrategia operó**: los cortes dependerían de la estrategia.

El estudio hace otra cosa: calcula los dos cortes **una sola vez, con todos los días del tramo `build` del activo**, y los deja fijos (`regime.py:101-102`). Para USDJPY, `build` va de 2008-01-01 a 2018-01-01: 2.613 días con dato, y los cortes son **0,8115 y 1,1073** para la volatilidad y **0,1298 y 0,2764** para la tendencia. Cualquier operación, de cualquier año, se compara con esos cuatro números.

Dos consecuencias que no son obvias:

1. **Un tercio de los días no es un tercio de las operaciones.** Los cortes reparten los *días* de `build` a partes iguales; si la estrategia opera más cuando hay movimiento, sus operaciones no se reparten igual.
2. **Fuera de `build` los días no tienen por qué repartirse a tercios.** Si el mercado estuvo más tranquilo después, casi todo caerá en «baja» (§5.1).

A tu pregunta de si los cortes se fijan con datos que la estrategia ya vio: **sí, a propósito.** `build` es justo el tramo donde se generó la estrategia. Para una operación de OOS1 eso es limpio en los cortes (se conocían antes de que empezara OOS1), no en la muestra: `oos1` ya se usó para elegir estas madres (§5.11). Para una operación de `build` dentro de la muestra «Completa» no lo es del todo: una entrada de 2009 se clasifica con cortes que incluyen los días de 2010 a 2017.

### 2.5 El intervalo por bootstrap

De una celda con N operaciones conocemos su P&L medio. La pregunta es cuánto habría cambiado ese medio con otras N operaciones «del mismo tipo». El bootstrap lo contesta sin fórmulas: fabrica muchas celdas alternativas **sorteando N operaciones de la propia celda, con reposición** (una misma operación puede salir dos veces y otra ninguna), y mira cuánto baila el medio.

Ejemplo de juguete, una celda de 5 operaciones (el estudio no la enseñaría: pide 30): +300, −100, −100, +200, −50. Medio = **+50**.

| sorteo | operaciones que salen | medio |
|---|---|---|
| 1 | −100, −100, −50, +300, −100 | −10 |
| 2 | +300, +200, +300, −50, −100 | +130 |
| 3 | −100, −50, −50, −100, +200 | −20 |
| … 9.999 sorteos | | |

Se ordenan los 9.999 medios y se toman el que deja el 2,5 % por debajo y el que deja el 2,5 % por encima: ése es el **intervalo percentil al 95 %** (`core/surface/dedupe.py:87-91`; los mandos, `config.yaml:24-27`: 9.999 remuestreos, 95 %, semilla 0 para que dos lecturas den lo mismo).

Cómo se lee: si el intervalo va de −584 a +105, el dato es compatible con que la celda pierda y con que gane; **no dice nada**. Si va de +76 a +752, el cero queda fuera: con sólo esa celda delante, diríamos que gana.

Tres cosas que el intervalo **no** hace, y que vuelven en §5:

- Compara el medio de la celda **con cero**, no con el medio del resto de la estrategia.
- Supone que las operaciones de la celda son **independientes** entre sí. Las de un mismo episodio de mercado no lo son.
- Vale para **una** celda mirada sola. Lo siguiente es qué pasa al mirar muchas.

### 2.6 Mirar muchas celdas a la vez

Un intervalo del 95 % se equivoca, por construcción, una vez de cada veinte: en una estrategia sin ninguna ventaja, una celda cualquiera tendrá el cero fuera de su intervalo el 5 % de las veces. Con una celda es un riesgo asumible. Con K celdas, la probabilidad de que **alguna** lo tenga fuera (si fueran independientes) es 1 − 0,95^K:

| celdas miradas (K) | celdas «significativas» esperadas por azar (0,05 × K) | probabilidad de ver al menos una |
|---|---|---|
| 1 | 0,05 | 5 % |
| 5 (los días de la semana) | 0,25 | 23 % |
| 9 (volatilidad × tendencia) | 0,45 | 37 % |
| 16 | 0,80 | 56 % |
| 30 (sesión × día) | 1,5 | 79 % |
| 50 (un mapa entero) | 2,5 | 92 % |
| 100 (las dos muestras) | 5 | 99,4 % |

Y lo que hace daño no es que aparezca, sino **elegirla**: quien mira el mapa se va derecho a la celda más extrema, que es exactamente la que el azar fabrica. Un filtro construido sobre ella «mejora» el backtest con toda seguridad y no mejora nada fuera de él.

**La corrección habitual** (que el código *no* aplica, §4) se llama Bonferroni: para que el riesgo conjunto siga siendo del 5 % con K celdas, a cada una se le exige el listón del 5 % / K. Con 16 celdas, cada celda tendría que pasar un listón del 0,31 % en vez del 5 %; el intervalo de cada una pasaría del 95 % al 99,69 %, bastante más ancho.

---

## 3. Lo que calcula, pieza a pieza

### 3.1 Lo que lee

| entrada | de dónde | qué usa |
|---|---|---|
| operaciones | `harvest/<proyecto>/<databank>/<día>/trades.parquet` | `Open time`, `Profit/Loss`, `Sample type`, `identity` (`inputs.py:62-64`) |
| nombre → identidad | `metrics.parquet` de la misma cosecha | la fila cuyo `strategy` coincide exactamente (`inputs.py:39-40`) |
| barras | `core.barstore.read(feed, timeframe)` | para fabricar la vela diaria (`one.py:31-33`) |
| tramo `build` | `assets/_policy.yaml` vía `core.assetdata.window` | las dos fechas entre las que se miden los cortes (`regime.py:27-29`) |

En la corrida: 1.138, 933 y 660 operaciones por madre, todas compras, con `Sample type` `IST` (build) u `OOS1`; la última abre el 2022-12-28. **No hay ninguna operación de `oos2`**: la cosecha no lo recoge.

El P&L es el de la columna `Profit/Loss` de SQX, **en USD y con el tamaño de cada operación**, que no es fijo: en estas madres va de 0,65 a 16,76 lotes (calculado por mí desde la cosecha). El mapa no lo normaliza. Consecuencia: el tamaño mediano por año va de 2,5 lotes (2008) a 6,5 (2012, 2019, 2021) y cae a 3,0 en 2022 (calculado por el revisor desde la cosecha), así que el P&L medio en USD de una celda depende también de qué años la llenan, no sólo de cómo fue el mercado (§5.13).

### 3.2 La volatilidad de cada día

`regime.volatility` (`regime.py:69`) llama a `engines.regimes.regime.atr` con periodo 20 (`config.yaml:17`). La serie ya viene **retrasada un día** desde el motor (`.shift(1)`, `engines/regimes/regime.py:44`): el valor del día D es el ATR al cierre de D−1. Los primeros 20 días de la historia no tienen valor.

### 3.3 La tendencia de cada día

`regime.efficiency` (`regime.py:84-87`) con ventana 20 (`config.yaml:21`), retrasada un día por `_shift` (`regime.py:55`). Los primeros 21 días no tienen valor.

**Por qué el retraso.** La vela del día D se fabrica con la jornada entera; una operación que entra a las 05:00 no conoce todavía ni el máximo ni el cierre de ese día. El README recoge el caso que lo destapó (revisión del 2026-09-26): en un día real, el 79 % de las barras, incluida la que marcó el máximo, eran posteriores a la entrada. `tests/test_conditionalmap.py` comprueba que una barra que llega después de la entrada, el mismo día, no mueve ni la volatilidad ni la tendencia de ese día. El retraso es de una fila, es decir, de un día **de mercado**: el lunes lee el viernes.

### 3.4 Los cortes

`regime.frozen_edges` (`regime.py:101-102`): los cuantiles 1/3 y 2/3 de los valores de la serie entre las dos fechas de `build`, ambas incluidas. Para USDJPY (recalculado por mí, coincide con la nota guardada en el JSON):

| serie | corte bajo | corte alto | días de `build` usados |
|---|---|---|---|
| ATR(20), en yenes | 0,8115 | 1,1073 | 2.613 |
| ratio de eficiencia a 20 días | 0,1298 | 0,2764 | 2.613 |

Las dos series apenas se parecen entre sí (correlación de rangos +0,04 en toda la historia, −0,03 dentro de `build`; calculado por mí y por el revisor), así que los nueve cruces de `build` tienen entre 244 y 327 días cada uno: los dos ejes no repiten la misma información.

### 3.5 Cómo cae una operación en su celda de volatilidad × tendencia

1. Se toma la hora de apertura y se le quita la hora: queda el **día del feed** en que entra (`inputs.py:66`).
2. Se busca el valor de cada serie en ese día (`regime.py:117`).
3. Se compara con los dos cortes (`np.digitize`, `regime.py:118`): menor que el corte bajo → «baja»; entre los dos → «media»; igual o mayor que el alto → «alta».
4. Si ese día no tiene valor (no está en las barras, o cae en el arranque de la serie), la operación recibe −1 y **no entra en ninguna celda** de esta vista (`regime.py:119`). No da error.

Ejemplo con días reales: una operación que entrase el 2018-01-03 a cualquier hora leería ATR = 0,6248 (menor que 0,8115 → **baja**) y ratio = 0,0253 (menor que 0,1298 → **baja**): celda baja × baja.

En la corrida ninguna operación quedó con −1. El resumen cuenta las «clasificadas» sólo de OOS1 (`one.py:85`; 402 de 402, 331 de 331, 240 de 240); en la Completa nada las cuenta (0 sin clasificar, comprobado a mano por el revisor).

### 3.6 La sesión

Cada entrada se pasa del reloj del feed a UTC (`sessions.py:37-41`; para EETUS, restando 7 horas y leyendo el resultado como hora de Nueva York) y de UTC a la hora local de tres ciudades. Las horas son las que fijaste el 2026-09-26 (`config.yaml:34-37`): Tokio 9–18, Londres 8–17, Nueva York 8–17, cada una **en su hora local**, de modo que el cambio de hora de cada ciudad mueve sus bordes en su fecha. Según cuáles estén abiertas (`sessions.py:55-63`):

| abiertas | etiqueta | duración aproximada (invierno) |
|---|---|---|
| sólo Tokio | Asia | 8 h |
| Tokio y Londres | Solape Asia-Londres | 1 h |
| sólo Londres | Londres | 4 h |
| Londres y Nueva York | Solape Londres-NY | 4 h |
| sólo Nueva York | Nueva York | 5 h |
| ninguna | Fuera de sesión | 2 h |

Ejemplo: una entrada a las 03:30 del feed un día de invierno son las 20:30 de la víspera en Nueva York, la 01:30 UTC y las 10:30 en Tokio → **Asia**. Las seis franjas duran muy distinto, así que tienen muy distinto número de operaciones aunque la estrategia entrase a todas horas por igual. Una hora que el cambio de horario repite o salta queda sin sesión y se cuenta aparte (0 en esta corrida).

### 3.7 El día de la semana

El nombre del día **del feed** en que entra la operación (`inputs.py:70`), de lunes a viernes (`cells.py:13`). Recuerda §2.1: el «lunes» del feed empieza el domingo a las 17:00 de Nueva York, así que coincide con la jornada de divisas, no con el día natural de ninguna ciudad. Una operación con día de feed sábado o domingo no entraría en ninguna celda de día y nada lo avisaría; en esta corrida no hay ninguna.

### 3.8 Las cuatro vistas: 50 celdas por muestra

| vista | celdas | dónde se calcula | pestaña |
|---|---|---|---|
| volatilidad × tendencia | 3 × 3 = **9** | `cells.grid`, `cells.py:49-61` | «Volatilidad x tendencia en la entrada» |
| sesión × día | 6 × 5 = **30** | `cells.session_by_weekday`, `cells.py:102-114` | «Sesión y día de la semana» |
| sesión sola | **6** | `cells.by_label`, `cells.py:77-85` | la misma |
| día solo | **5** | `cells.by_label` | la misma |
| | **50** | | |

Las tres últimas no son independientes: «Asia» es la suma de las cinco celdas «Asia × día». Una misma racha de buenas operaciones puede encender una celda cruzada, su sesión y su día a la vez.

### 3.9 Lo que se lee en cada celda

`cells.cell_stats` (`cells.py:28-32`):

| número | qué es | fórmula |
|---|---|---|
| `operaciones` | cuántas operaciones tiene la celda | recuento |
| `pnl_medio` | lo que gana de media cada una, en USD | suma / recuento |
| `ci_baja`, `ci_alta` | el intervalo del 95 % de ese medio | bootstrap percentil, §2.5 |
| `acierto` | proporción de ganadoras | operaciones con P&L > 0 / recuento |

El acierto no lleva intervalo. En la pestaña de volatilidad × tendencia la tabla «Celda a celda» trae las siete columnas (`contract.py:87-90`). En la de sesión y día, el intervalo sólo va en las barras del gráfico (`contract.py:116-117`); **las tablas «Sesión a sesión» y «Día a día» no lo llevan** (`contract.py:127-129`), y las celdas cruzadas de sesión × día no tienen tabla: sólo el color y el medio en la rejilla.

### 3.10 El suelo de 30 operaciones

Una celda con menos de 30 operaciones no calcula nada (`cells.py:28-29`). El 30 no está escrito en el módulo: se lee de `engines/nulls/config.yaml:42` (`verdict.min_trades`, el mínimo por debajo del cual la puerta OOS no calcula su p-valor) para que los dos suelos no puedan separarse sin querer (`cells.py:11`). Desde el 2026-10-01 la celda no queda en blanco: la rejilla escribe «< 30 ops», la nota de debajo cuenta cuántas son (`contract.py:63-72`), y una sesión o un día sin barra se nombra con sus operaciones. Si ninguna celda de una vista llega al suelo, el mapa de esa vista no se pinta y un aviso lo dice (`contract.py:75-79`).

### 3.11 Las dos muestras

`one.samples` (`one.py:57-66`) calcula todo dos veces en la misma pasada:

- **OOS1** — sólo las operaciones con `Sample type` igual a `run.sample`. Es con la que abre la ventana.
- **Completa** — todas las de la cosecha: `build` + OOS1.

Los cortes son los mismos en las dos. La razón de la Completa es aritmética: 240 a 402 operaciones repartidas en 30 casillas de sesión × día no llenan casi ninguna.

Ejemplo real completo, `Strategy 3.13.366`, vista de volatilidad × tendencia (recalculado por mí; idéntico a lo guardado):

**OOS1 — 331 operaciones, P&L medio +0,89 USD.** Recuento por celda (filas volatilidad baja/media/alta; columnas tendencia baja/media/alta): `[107, 78, 61]`, `[2, 3, 13]`, `[17, 18, 32]`. Cinco de las nueve celdas no llegan a 30.

| volatilidad | tendencia | operaciones | P&L medio | intervalo 95 % | acierto |
|---|---|---|---|---|---|
| baja | baja | 107 | −84,20 | −272,60 a 102,91 | 0,421 |
| baja | media | 78 | −93,32 | −321,40 a 118,49 | 0,436 |
| baja | alta | 61 | −28,97 | −288,86 a 226,18 | 0,574 |
| alta | alta | 32 | **+386,83** | **75,62 a 751,82** | 0,656 |

**Completa — 933 operaciones, P&L medio +80,22 USD.** Las nueve celdas llegan al suelo.

| volatilidad | tendencia | operaciones | P&L medio | intervalo 95 % | acierto |
|---|---|---|---|---|---|
| baja | baja | 170 | −132,43 | −290,41 a 24,40 | 0,400 |
| baja | media | 133 | 43,65 | −144,60 a 235,30 | 0,451 |
| baja | alta | 135 | **218,28** | **14,94 a 429,78** | 0,600 |
| media | baja | 67 | 32,07 | −261,64 a 319,12 | 0,448 |
| media | media | 69 | 222,24 | −40,88 a 495,72 | 0,551 |
| media | alta | 76 | 142,77 | −102,35 a 396,70 | 0,474 |
| alta | baja | 98 | 63,69 | −129,17 a 259,48 | 0,541 |
| alta | media | 96 | 59,97 | −151,87 a 271,83 | 0,469 |
| alta | alta | 89 | **244,45** | **51,52 a 453,20** | 0,607 |

La tentación es evidente: «esta estrategia gana con volatilidad alta y tendencia alta, y pierde cuando todo está quieto». Antes de creérsela, tres medidas **calculadas por mí** sobre la celda alta × alta de OOS1:

| medida | valor |
|---|---|
| días distintos en que caen sus 32 operaciones | 29 |
| episodios de mercado (rachas seguidas de días en esa celda) | **9** |
| parte de las operaciones que son de un solo año | **94 % (2022)** |
| parte de la ganancia total de la celda que ponen sus 3 mejores operaciones | **68 %** (la mayor, 3.899 USD de 12.378) |
| la misma celda en `10.23.380` (38 ops, 95 % de 2022) | −78,35 USD, intervalo −284,11 a 136,43 |
| la misma celda en `4.25.395` (34 ops) | +132,73 USD, intervalo −526,00 a 800,96 |
| si se le aplicase la corrección de §2.6 con las 16 celdas que enseña este mapa | no pasa: su p-valor es p ≈ 0,03 (aproximación normal) o ≈ 0,015 (bootstrap del estudio, 200.000 remuestreos, bilateral; calculado por el revisor), y en los dos casos queda por encima del listón de 0,0031. Con 16 celdas es el recuento más favorable: con las 100 de la estrategia el listón sería 0,0005 y con las 45 enseñadas en las dos muestras de esa madre, 0,0011. Comparada con el resto de la estrategia y no con cero, la celda da p conjunto 0,30 (calculado por el revisor, §5.10) |

Lo que el mapa llama «volatilidad alta y tendencia alta en OOS1» es, en la práctica, «el año 2022 del yen», y tres hermanas de la misma plantilla dan en esa celda +387, −78 y +133.

### 3.12 Lo que escribe

`report.py:33-35`: imprime el mapa en Markdown y guarda, bajo `reports/<proyecto>/<databank>/<día>/conditionalMap/estrategias/`, un `<estrategia>.json` (lo que pinta la ventana) y un `.html`. El JSON lleva: las dos pestañas con sus bloques marcados por muestra, el aviso de comparaciones múltiples (`contract.py:8-14`), el glosario, `verdict: null` y un resumen de cuatro cifras (`one.py:90-91`): operaciones de la muestra, cuántas quedaron clasificadas, el nombre de la muestra y las operaciones de la Completa. **No escribe ningún número por celda fuera de las tablas**, ningún hecho para el autopiloto y ninguna fila en el ledger.

Tarda de 1,9 a 2,5 segundos por estrategia según el propio JSON (`wall_s`: 2,50 / 2,17 / 1,89).

---

## 4. El criterio cargado y por qué

### 4.1 Reglas: ninguna

| dónde se buscaría | qué hay |
|---|---|
| `pipeline/autopilot/criteria.yaml` | entradas para los pasos 8, 10, 11.5, 12, 14, 16, 16.5, 17, 18, 18.5 y 19. **Ninguna para el 22.** |
| `pipeline/autopilot/facts.py` | ningún hecho del mapa |
| `ledger/thresholds.yaml` | ninguna clave del mapa; el suelo de 30 es el de `engines/nulls` |
| el resultado | `verdict: null` |

Es coherente con la definición del paso: un mapa que fabrica sospechas no tiene nada que aprobar o suspender.

### 4.2 Lo que hace el autopiloto con él

1. `bin/workflow.sh:81` lanza el autopiloto con `--panel 22=Results`: el databank cuya cosecha lee el mapa viene fijado en el comando único.
2. `pipeline/autopilot/tail.py:15` lo declara paso «de panel» junto al 21, y `tail.py:144-150` lo planifica después del paso 20 como acción de tipo `reading`. **Sin `--panel 22=…` el autopiloto para limpio** en el 22 con el mensaje «falta --panel 22=<databank>» (`tail.py:147-149`); no elige el databank por ti.
3. `pipeline/autopilot/closing.py:19-25` lo corre: una llamada por madre superviviente, con el mismo comando que arma el botón de la ventana (`ui/daemon/runner/readings.py:62-71`), que le pasa el activo, el feed y el timeframe del proyecto con `--set` (`ui/daemon/results/forproject.py:11-13`). Sin eso correría con los del `config.yaml` (USDJPY, H1).
4. Como `criteria.yaml` no le da reglas, **no hay juicio** después. El paso queda «hecho» y el autopiloto sigue con el 23.

En la corrida: `22 | reading | 8 s | conditionalMap sobre Results: 3 madre(s)`.

### 4.3 Las negativas y comprobaciones que sí existen

| situación | qué pasa | dónde |
|---|---|---|
| el databank no tiene cosecha | no corre; dice «necesita la cosecha de este databank» | `readings.py:64-65` |
| la cosecha mezcla varios timeframes | no corre; pide correrlo a mano con `run.timeframe` | `readings.py:66-68` |
| el activo no tiene tramo `build` decidido | se detiene con el error de `core.assetdata` | `regime.py:27-28` |
| el nombre de la estrategia no está en la cosecha | falla (índice vacío), sin mensaje propio | `inputs.py:40` |
| una celda con menos de 30 operaciones | no enseña P&L; lo dice | `cells.py:28-29`, `contract.py:63-72` |

`tests/test_conditionalmap.py` comprueba: que los cortes no cambian aunque cambien los datos de fuera de `build`; que una barra posterior a la entrada no mueve la etiqueta del día; que una celda de 29 operaciones no produce estadísticos y una de 30 sí; que el selector ofrece las dos muestras y que la rejilla escribe «< 30 ops»; y una tabla de horas de sesión con sus cambios de horario.

---

## 5. Lo que no cuadra o no está medido

### 5.1 Los cortes de volatilidad congelados no viajan fuera de `build` — y en los índices dejan el eje vacío

**Calculado por mí** (`drift.py`: las mismas series y los mismos cortes del estudio, aplicados a todos los días de `oos1` de cada activo; no usa ninguna estrategia):

| activo | cortes de volatilidad (sobre `build`) | días de `oos1` en baja / media / alta | precio medio en `build` → `oos1` |
|---|---|---|---|
| USDJPY | 0,81 / 1,11 | **76 %** / 8 % / 16 % | 98,9 → 113,5 |
| XAUUSD | 16,66 / 20,91 | 34 % / 9 % / 57 % | 1.265 → 1.607 |
| USA500 | 16,81 / 24,99 | 0 % / 0,3 % / **99,7 %** | 2.181 → 3.968 |
| NIKKEI225 | 249,2 / 317,6 | 0,1 % / 4 % / **95,9 %** | 17.526 → 27.369 |

La tendencia, que es un cociente sin unidades, sí viaja: en los cuatro activos los días de `oos1` se reparten 30–38 % por tercil.

La causa es doble. Una parte es que el ATR está en puntos de precio y los cortes son puntos fijos. La otra es que la volatilidad de `oos1` fue de verdad distinta de la de `build`: con el ATR dividido por el precio (medido en `drift.py`, no es del estudio) los días de `oos1` siguen sin repartirse a tercios — USDJPY 79 / 12 / 9 %, USA500 6 / 21 / 74 %, NIKKEI225 8 / 58 / 34 %, XAUUSD 56 / 34 / 10 % (calculado por el revisor, reproduciendo `drift.py` con cortes sobre `build`). Un corte congelado sobre `build`, en las unidades que sea, no reparte `oos1` a tercios en ninguno de los cuatro activos medidos. Sobre la parte de las unidades: un índice que casi dobla su precio dobla su ATR en puntos aunque no esté más nervioso, y todos sus días posteriores quedan por encima del corte alto. **Lo confirma lo guardado**: en los tres mapas de `Test_USA500_H1_indicesIBS` y en los de `Test_NIKKEI225_M30_simpleL_live`, la rejilla de OOS1 sólo tiene números en la fila «alta»; las otras dos filas dicen «< 30 ops» enteras. En USDJPY ocurre al revés (2018–2022, con 2022 como el año de volatilidad alta): en OOS1 la fila «media» tiene 6, 7 y 17 operaciones en `10.23.380`.

Consecuencia: en OOS1 el mapa de volatilidad × tendencia **no es de 9 celdas**; es de 2 a 3 en los índices (de los 13 mapas guardados de USA500 y NIKKEI225, 12 tienen las 3 celdas de la fila «alta» y uno, `Strategy 5.13.334` de USA500, sólo 2; calculado por el revisor) y de 4 en el yen, y la fila que queda no compara volatilidades sino tendencias dentro de una sola.

La cabecera de `regime.py:3-6` recuerda que el encargo 14 admitía dos lecturas — ventana que crece con el tiempo, o el tramo `build` — y que el módulo tomó la segunda (`build`), «la más sencilla». La otra lectura no está implementada ni medida. El ATR dividido por el precio tampoco está implementado; lo he medido aparte y el resultado está en el párrafo anterior.

### 5.2 Comparaciones múltiples: el código avisa y no corrige

**Lo que hace el código:** añade a cada resultado un aviso de texto fijo (`contract.py:8-14`) y lo repite en la cabecera del informe (`report.py:26-28`). No ajusta ningún intervalo; cuenta las celdas bajo el suelo (`contract.py:65-72`, y `contract.py:120` en las barras), no las que excluyen el cero ni las esperadas por azar; y no marca ninguna.

**Calculado por mí, primera simulación** (`null.py`): ¿cuántas celdas tendrían el cero fuera de su intervalo si la estrategia no tuviese ventaja y su resultado no dependiese de la celda? Para cada madre y muestra: se resta al P&L su media (queda una estrategia de media cero con la misma forma de ganancias y pérdidas), se baraja entre las operaciones dejando las etiquetas de celda como están (mismos tamaños, mismos solapes entre vistas), y se cuentan las celdas de ≥ 30 operaciones cuyo intervalo excluye el cero. 1.000 barajadas por mapa; intervalo percentil con 999 remuestreos (el estudio usa 9.999). Supuesto: operaciones intercambiables.

| madre · muestra | celdas enseñadas | «significativas» por azar (media) | prob. de ≥ 1 | prob. de ≥ 2 | prob. de ≥ 3 |
|---|---|---|---|---|---|
| 10.23.380 · OOS1 | 19 | 0,89 | 56 % | 22 % | 8 % |
| 10.23.380 · Completa | 33 | 1,64 | 78 % | 46 % | 24 % |
| 3.13.366 · OOS1 | 16 | 0,61 | 43 % | 14 % | 4 % |
| 3.13.366 · Completa | 29 | 1,33 | 72 % | 38 % | 16 % |
| 4.25.395 · OOS1 | 13 | 0,56 | 41 % | 11 % | 3 % |
| 4.25.395 · Completa | 27 | 1,30 | 69 % | 36 % | 16 % |

Mirando las dos muestras de una madre, la probabilidad de al menos una celda «significativa» sin que haya nada sale entre la de la Completa sola (78 %, 72 % y 69 %) y el 90 %, 83 % y 82 % que resulta de tratar las dos muestras como independientes (`null.py:48`: barajadas independientes); no lo son, porque las operaciones de OOS1 están dentro de la Completa, así que la cifra real es algo menor que la publicada. La tasa por celda sale donde debe (3,8–5,0 %), algo más alta en las celdas de 30 a 49 operaciones (5,0–6,9 %): el intervalo es un poco estrecho de más justo en las celdas pequeñas. Medido de frente por el revisor (3.000 celdas simuladas sacando operaciones al azar de cada madre, 999 remuestreos): con 30 operaciones independientes el intervalo «del 95 %» cubre el 92–93 %; con 50, el 93,5–94,2 %; con 100, el 94,0–94,5 %. El defecto existe y es de unos 2 puntos en el suelo; el P&L de estas madres no es de cola gruesa (curtosis en exceso 1,9 a 3,9, calculado por el revisor).

**Segunda simulación** (`null_realmean.py`), que es la que se compara con lo observado: lo mismo **sin restar la media**. La estrategia conserva su resultado real; sólo se rompe el vínculo entre celda y resultado.

| madre · muestra | celdas con el cero fuera, observadas | esperadas si la celda no importase | prob. de ver tantas o más |
|---|---|---|---|
| 10.23.380 · OOS1 | 0 de 19 | 1,31 | 100 % |
| 10.23.380 · Completa | 3 de 33 | 2,63 | 49 % |
| 3.13.366 · OOS1 | 1 de 16 | 0,62 | 43 % |
| 3.13.366 · Completa | 3 de 29 | 3,39 | 69 % |
| 4.25.395 · OOS1 | 0 de 13 | 0,73 | 100 % |
| 4.25.395 · Completa | 5 de 27 | 3,96 | 35 % |
| **total** | **12 de 137** | **12,6** | |

**Lectura:** el recuento de celdas «buenas» de esta corrida (12) es el que sale solo cuando el estado del mercado no influye en nada, siempre que la estrategia conserve su media real (con media cero se esperarían 6,3; calculado por el revisor). Lo que se contrasta es un recuento por mapa (probabilidad de ver tantas o más: 35 %–100 %), no cada celda; y el nulo baraja operaciones como intercambiables, sin la persistencia de estado de §5.5. Es una medición sobre tres madres de una plantilla; no dice que el mapa no pueda encontrar nunca nada, dice que aquí no encontró.

### 5.3 En la muestra Completa, «el cero queda fuera» no significa «depende del estado»

La segunda tabla lo enseña: sin que la celda importe, en la Completa se esperan 2,6 a 4,0 celdas con el cero fuera, frente a 1,3 a 1,6 con media cero. La diferencia es sólo que en la Completa la estrategia gana de media (+46 a +120 USD por operación) porque incluye el tramo donde se construyó. Una celda grande hereda esa media y con suficientes operaciones su intervalo se despega del cero. El mapa no calcula en ningún sitio la comparación que contestaría a la pregunta del paso — **la celda contra el resto de la estrategia**.

El glosario lo advierte de palabra (`contract.py:31-34`: «lo que se vea ahí puede ser parte de lo que la construcción ajustó»), pero la rejilla de la Completa usa los mismos colores y el mismo intervalo que la de OOS1.

### 5.4 El suelo de 30 no sale de ninguna cuenta sobre una celda

El 30 es el mínimo con el que la puerta OOS calcula un p-valor contra entradas al azar. Para el medio de una celda significa esto (**calculado por mí**: 1,96 × desviación típica del P&L en OOS1 / √N):

| madre | desviación típica del P&L (OOS1) | medio ancho del intervalo con 30 ops | con 100 ops | P&L medio (OOS1 / Completa) |
|---|---|---|---|---|
| 10.23.380 | 974 USD | ±348 | ±191 | −61 / +46 |
| 3.13.366 | 1.021 USD | ±365 | ±200 | +1 / +80 |
| 4.25.395 | 1.373 USD | ±491 | ±269 | +68 / +120 |

Una celda de 30 operaciones sólo se despega del cero si su medio es **entre cuatro y ocho veces** el medio de la estrategia en la muestra Completa (y en OOS1 la comparación es peor todavía: dos de las tres madres apenas ganan o pierden ahí). O no dice nada, o dice algo enorme, y lo enorme con 30 operaciones es casi siempre un puñado de operaciones grandes (§3.11). Lo que falta para poder escribir un suelo propio: decidir qué diferencia entre celda y resto merece la pena detectar, y con qué probabilidad.

### 5.5 Las operaciones de una celda no son independientes

El bootstrap sortea operaciones sueltas. Pero el estado del mercado dura: la etiqueta de volatilidad cambia de media cada **34 días de mercado**, la de tendencia cada 3,5 (calculado por mí sobre toda la historia de USDJPY). Las operaciones de una celda de volatilidad vienen en rachas largas del mismo periodo y comparten suerte. En OOS1 las celdas de volatilidad «alta» son casi un solo año (§3.11); en la Completa, la celda alta × alta de `3.13.366` reparte sus 89 operaciones en 37 episodios y 7 años, con el 34 % en 2022. El estudio no remuestrea por episodios. Medido por el revisor remuestreando por meses enteros en vez de por operaciones (4.999 remuestreos): el intervalo apenas cambia de ancho (entre 0,80 y 1,30 veces el del estudio, mediana 0,98 a 1,02 en las 137 celdas) y 2 de las 12 celdas con el cero fuera dejan de excluirlo (`3.13.366` Completa baja × alta: de 15 a 430 pasa a −11 a 432; `4.25.395` Completa Asia × martes: de 22 a 706 pasa a −5 a 713). Límite de la medida: racimos de un mes, no de episodio; con 10 meses (la celda alta × alta de OOS1) el propio remuestreo por racimos es poco fiable. El problema de estas celdas no es que el intervalo sea estrecho, sino que describe un periodo y no un estado: el intervalo de la celda alta × alta de OOS1 es correcto como resumen de 2022 y no dice nada de otro año de volatilidad alta.

### 5.6 La tendencia sin signo

§2.3. El `config.yaml:21-22`, el glosario y el manual describen bien la fórmula; ninguno advierte de que una caída recta y una subida recta dan la misma etiqueta. Para una plantilla de una sola dirección (regla dura 13) la celda «tendencia alta» mezcla el viento a favor con el viento en contra.

### 5.7 La documentación frente al código

| dónde | qué dice | qué hace el código |
|---|---|---|
| `docs/AgentPDFs/WORKFLOW.md:52` | «volatilidad realizada, tendencia, día de la semana» | la fila describe tres ejes y anota la sesión sólo en la columna de estado («✅ sesión…»); la sesión da 36 de las 50 celdas. La volatilidad es un ATR en unidades de precio, no una volatilidad realizada (`engines/regimes/regime.py:40-44`); el mismo término «realised» está en el docstring de `conditionalMap/regime.py:59`, donde también habría que corregirlo |
| `WORKFLOW.md:141-143` | el paso 22 lee `build` «sólo para congelar sus cortes de tercil» | la muestra Completa lee también el **P&L** de las operaciones de `build` y las enseña celda a celda (`one.py:65-66`) |
| `contract.py:10-12` y manual `53`, líneas 3-5 | «con tres cortes y varias celdas por cada uno» | cuatro vistas, 50 celdas por muestra, 100 por estrategia (§3.8) |
| manual `53`, líneas 7-9; `contract.py:13-14`; README:39-41 | una celda que diga algo «se anota como candidata en `ledger/thresholds.yaml` y se revalida sobre datos que no se hayan mirado» | no hay clave del mapa en el ledger, ni comando que la apunte, ni tramo de datos asignado para revalidar |
| manual `53`, líneas 44 y 51; `config.yaml:32-33`; README:58-61 | feeds `XAUUSD_DukasM1_Infinox`, `USDJPY_DukasM1_the5ers`; «EET para Infinox, Asia/Jerusalem para the5ers» | desde el 2026-10-01 los feeds son `<ACTIVO>_M1` en EETUS; `feeds.timezone("USDJPY_M1")` devuelve `EETUS`. Los ejemplos del manual (cortes de XAUUSD 16,6062 / 20,7802; las tablas de `XAU_ISOOS_ejemplo` y `USDJPY_emaCross_H1`) son de los feeds anteriores |
| `pipeline/autopilot/tail.py:12-14` | el databank de 21 y 22 «no se elige aquí (regla dura 11)» | cierto en `tail.py`, pero `bin/workflow.sh:81` lo fija siempre a `Results` |
| `regime.py:66-67` (docstring) | los primeros «atr_period + 1» valores no existen | son `atr_period` (20); sin efecto práctico |

### 5.8 Detalles menores

- **Seis velas diarias de domingo** en 23 años del feed de USDJPY (calculado por mí): velas diminutas que entran en el ATR como un día más. Efecto inapreciable con seis; no medido en otros feeds.
- **El extremo superior de la rodaja de `build` es la marca 2018-01-01 00:00** (`assetdata.window` devuelve el instante final de 2017, `core/assetdata.py:161-163`), es decir el primer día de `oos1` (`regime.py:101`, extremos incluidos); sólo cuenta si ese día tiene vela, y en USDJPY no la tiene (festivo): la rodaja acaba el 2017-12-29, con 2.613 días (calculado por el revisor). Como la serie va retrasada un día, no hay fuga de información.
- **Un día sin dato no da error**: la operación desaparece de la vista de volatilidad × tendencia y sólo se nota en la cifra «clasificadas» del resumen, que cuenta únicamente la muestra de cabecera (OOS1, `one.py:85`). Un feed equivocado se vería como un mapa de celdas «< 30 ops», no como un fallo (el manual lo dice).
- **El raíl da el paso por hecho con una madre.** `tail.py:67-68` lo advierte para los pasos 17–19; el 22 se planifica con la misma función, así que si una madre falla a medias el paso puede figurar como hecho.
- **Cada madre se lee por separado.** No hay vista de población: con M madres se miran 100 × M celdas, y nada suma lo que comparten hermanas de una misma plantilla (el ejemplo de §3.11 se ve sólo poniendo los tres mapas juntos a mano).

### 5.9 La regla dura 15 y las celdas de calendario

La regla 15 prohíbe al constructor cualquier bloque que lea el reloj o el calendario — `BarTime`, `CurrentTime`, día de la semana, día del mes — «en cualquier estudio o generación». El mapa es Python y puede *mirar* el día y la hora de cada operación sin romperla: tal como yo leo la regla —y te toca confirmarlo, porque su texto dice «en cualquier estudio o generación»—, habla de lo que el constructor puede sortear, no de lo que un estudio puede leer. Sobre lo que se puede **hacer** con lo que el mapa enseñe, la lectura estricta (la regla alcanza al constructor y a las plantillas) limita así:

| vista | celdas | ¿traducible a una condición del constructor? |
|---|---|---|
| día de la semana | 5 | **no** — es calendario |
| sesión | 6 | **no** — es reloj |
| sesión × día | 30 | **no** — las dos cosas |
| volatilidad × tendencia | 9 | sí en principio: ATR y ratio de eficiencia son indicadores, no reloj. No he verificado que SQX tenga el bloque del ratio de eficiencia sobre velas diarias en una estrategia de M30 |

Es decir, mientras la regla 15 se lea como prohibición para el constructor y para las plantillas, ninguna de las 41 celdas de reloj o calendario de cada muestra puede ser condición de entrada. Si se leyera sólo como lo que el constructor sortea, una condición horaria fija en una plantilla (condición «fija» de la regla 14) no está prohibida expresamente: pregunta pendiente (§6, decisión 9). De las 12 celdas con el cero fuera de esta corrida, 8 son de sesión o día y 4 de volatilidad × tendencia (calculado por el revisor): dos tercios de lo que el mapa «encendió» no se podría usar con la lectura estricta. Lo que sí cabe hacer con una celda de día de la semana, sin tocar la regla:

1. **Anotarla en la ficha como descripción**: «el 49 % de las operaciones de `3.13.366` entra en la franja de Asia» (455 de 933). Es un dato de cómo opera, útil para saber cuándo está expuesta y con qué otras estrategias coincide en una cartera. Para eso no hace falta que sea significativa.
2. **Tratarla como pista de una causa que no sea el calendario.** Un mal viernes puede ser el coste de quedarse abierta el fin de semana, y un mal miércoles la noche de swap triple; ésas son hipótesis sobre **costes y duración**, que tienen sus propios estudios y no necesitan bloque de reloj. El mapa no distingue una causa de otra: sólo ve la entrada.
3. **No hacer nada**, que con los números de §5.2 es lo que corresponde en esta corrida.

Lo que no cabe con la lectura estricta: excluir el día en el constructor (regla 15), ni recortarlo a mano en el EA exportado — eso sería una estrategia distinta de la que pasó los pasos 6 a 21, sin validar.

Y aun para las 9 celdas traducibles: una condición de volatilidad o de tendencia ocuparía una de las dos condiciones de entrada que permite la regla 14, pediría plantilla nueva y construcción nueva, y el resultado tendría que recorrer el workflow entero.

### 5.10 El recuento de celdas no es la cuenta que contesta la pregunta del paso (revisor)

«Cuántas celdas excluyen el cero» no es la cuenta que contesta «¿depende de la celda?» (lo reconoce §5.3), y el 12,6 tiene dispersión: el azar da entre 7 y 18 celdas el 90 % de las veces (calculado por el revisor, mismo nulo, 1.000 barajadas, seis mapas supuestos independientes; la dispersión real es mayor porque las tres madres son hermanas del mismo mercado y OOS1 está dentro de la Completa). La suma mezcla además dos muestras de naturaleza distinta: OOS1 tiene 1 celda observada frente a 2,7 esperadas (desviación típica 1,6) y la Completa 11 frente a 9,8 (desviación típica 2,8); 11 de las 12 están en la Completa. La cuenta adecuada compara cada celda con el resto de su estrategia y toma el máximo de todas las celdas enseñadas contra su barajado (p conjunto por mapa; calculado por el revisor): `10.23.380` OOS1 0,86 · Completa 0,79; `3.13.366` OOS1 0,30 · Completa 0,13; `4.25.395` OOS1 0,53 · Completa 0,66. Ninguno baja de 0,05; la conclusión del apartado 0 se sostiene también con esta cuenta.

### 5.11 Mirar el mapa ya es seleccionar, y `oos1` no llega virgen (revisor)

«El paso no filtra» es cierto del código y no de la persona. El mapa se pinta en la ventana (`ui/daemon/results/catalogue.py:89`, `ui/daemon/runner/readings.py:62-71`); si quien lo mira se queda con una madre y no con otra, esa elección es una selección hecha sobre `oos1` que no deja fila en ningún ledger y no tiene datos donde comprobarse. Tampoco llega `oos1` sin tocar al paso 22: `WORKFLOW.md:144` lo asigna a los pasos 7 a 16, de modo que las madres que llegan aquí ya se eligieron con esas mismas operaciones. Por eso la pestaña «OOS1» del mapa no es una muestra sin tocar.

### 5.12 Cobertura de activos del eje de volatilidad (revisor)

Sólo se midieron 4 de los 27 activos de `assets/_policy.yaml`; «en los índices» generaliza desde dos (USA500, NIKKEI225). XAUUSD, que el apartado 0 no citaba, deja la fila «media» con el 8,8 % de los días de `oos1`. Lo común a los cuatro medidos es que la fila «media» casi desaparece (USDJPY 7,5 %, XAUUSD 8,8 %, NIKKEI225 4,0 %, USA500 0,3 %; calculado por el revisor a partir de `drift.out`). Los otros 23 no están medidos.

### 5.13 El P&L en USD pesa cada año por su tamaño (revisor)

El tamaño mediano por año va de 2,5 lotes (2008) a 6,5 (2012, 2019, 2021) y cae a 3,0 en 2022; la mediana en `build` es de 3,5 a 4,1 lotes y en OOS1 de 4,5 a 5,6 (calculado por el revisor desde la cosecha). El P&L medio de una celda pesa cada año por su tamaño: una celda hecha de 2019–2021 pesa por operación el doble que una hecha de 2008 o de 2022.

---

## 6. Cierre: las decisiones que te quedan

Ninguna es urgente para el código: el paso no descarta nada. Para quien lo lee sí hay una cosa que saber hoy: si después de mirar el mapa te quedas con una madre y no con otra, o decides probar un filtro, eso es una selección hecha sobre `oos1`; hoy no se apunta en ningún sitio y no hay datos reservados para comprobarla. Además `oos1` ya se usó para elegir a estas madres en los pasos 7 a 16: la pestaña «OOS1» del mapa no es una muestra sin tocar (§5.11).

| # | decisión | qué ganas | qué cuesta |
|---|---|---|---|
| 1 | **Qué puede salir del paso 22.** Hoy: nada, y el camino «ledger + revalidar» no existe. O se deja así por escrito (el mapa es sólo ficha), o se define el camino: dónde se apunta la hipótesis y en qué datos se revalida | que una celda llamativa no acabe convertida en filtro por la puerta de atrás | si se define el camino, hay que decir de dónde salen los datos no mirados: `oos2` no tiene reserva dura para ti (2026-09-28; `WORKFLOW.md:146-155`): lo leen 17, 18, 18.5, 19 y 24, y gastarlo aquí es decisión tuya; cada mirada queda contada en el ledger (ver decisión 10) |
| 2 | **Las vistas de calendario** (41 de 50 celdas) con la regla 15 vigente: mantenerlas como descripción, o quitarlas del mapa | si se quitan, el mapa pasa de 100 celdas por estrategia a 18 y la probabilidad de espejismo baja con ellas (§2.6) | se pierde la descripción de cuándo opera cada estrategia, que sirve para cartera y fondeo |
| 3 | **La muestra Completa**: mantenerla junto a OOS1, o dejar sólo OOS1 | con sólo OOS1 desaparecen las celdas que excluyen el cero porque la estrategia se construyó ahí (§5.3) | en OOS1 casi no hay celdas: 13 a 19 de 50 en esta corrida, y de sesión × día 0 a 4 de 30 |
| 4 | **El eje de volatilidad** (§5.1): cortes fijos en puntos sobre `build` (hoy), cortes que avanzan con el tiempo (la otra lectura del encargo 14), o volatilidad relativa al precio | un eje que en OOS1 tenga más filas con días en los índices. Ojo: con la volatilidad relativa los índices pasan de 0 / 0,3 / 99,7 % a 6 / 21 / 74 % (USA500): hay tres filas con días, pero no tres tercios (calculado por el revisor) | cualquier cambio añade un mando al estudio — justo lo que el diseño quiso evitar — y deja sin comparación los mapas ya guardados |
| 5 | **La tendencia con o sin signo** (§5.6) | con signo, una plantilla de largos distingue tendencia a favor y en contra | pasa de 3 a 5 o 6 estados: más celdas, cada una más pequeña |
| 6 | **El suelo de celda** (§5.4): 30 prestado, o uno derivado de la diferencia que quieras poder detectar | celdas que, cuando hablan, pueden decir algo | con un suelo más alto quedan menos celdas todavía; en OOS1 puede no quedar ninguna |
| 7 | **Que el mapa diga cuántas celdas cabía esperar por azar**, o que corrija los intervalos (§5.2) | el lector ve «3 fuera del cero, esperadas 2,6» en vez de tres colores fuertes | hay que elegir el método (el de §5.2 es una medición mía, no una regla) y cuesta cómputo: mil barajadas por mapa frente a los 2,5 s de hoy |
| 8 | **Si el paso sigue en la cola del autopiloto.** Hoy cuesta 8 s y nada lo lee después | quitarlo simplifica la cola (tu vara: menos piezas) | se pierde el mapa guardado por madre; seguiría disponible desde la ventana |
| 9 | **Alcance de la regla 15 sobre una condición horaria fija.** El texto dice «no time blocks … in any study or generation». Abierta: ¿prohíbe también usar como filtro una condición horaria o de calendario *fija* en una plantilla (condición «fija» de la regla 14), o sólo lo que el constructor sortea? Hoy el apartado 0 y §5.9 parten de la lectura estricta; los dos lectores del dossier (revisores) señalan que es una lectura, no un hecho comprobado contigo | si sólo alcanza al sorteo, las 41 celdas de reloj dejan de estar vetadas como filtro y la decisión 2 cambia de planteamiento | si alcanza también a lo fijo, no cambia nada de lo escrito; la respuesta no está dada aquí |
| 10 | **Alcance de «`oos2` reservado».** `WORKFLOW.md:146-155` dice que lo leen 17, 18, 18.5, 19 y 24 (y el 20, línea 50), que un humano puede mirar cualquier tramo (2026-09-28) y que la reserva rige sólo para un agente autónomo (`core.assetdata.enforced()`), con cada mirada contada en el ledger. Abierta: si el camino de la decisión 1 puede usar `oos2` como datos no mirados | datos reales para revalidar una hipótesis del mapa | cada mirada engorda el recuento del ledger (Sharpe desinflado); la respuesta no está dada aquí |

**La decisión que sí puedo darte cerrada, sobre esta corrida:** de los seis mapas de `Test_USDJPY_M30_doubleROCLong` no sale ningún filtro que poner al generar, ninguno para cribar un databank y ninguna hipótesis que merezca apuntarse. Coste en estrategias: cero, porque el paso no descarta. El recuento de 12 celdas con el cero fuera no se distingue del que da el azar conservando la media real (12,6; con media cero serían 6,3; calculado por el revisor); la única llamativa en OOS1 es el año 2022 visto por una de tres hermanas. «Esto apenas ayuda» es aquí la lectura correcta, y lo es por tres razones medibles: demasiadas celdas para tan pocas operaciones, un eje de volatilidad que fuera de `build` se queda en una fila, y una mayoría de celdas que la regla 15, leída en sentido estricto, no deja usar (decisión 9).
