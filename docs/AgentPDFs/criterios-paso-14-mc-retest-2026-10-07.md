# Pasos 13 y 14 — MC Retest: qué se calcula, con qué estadística y qué criterio hay cargado

**Fecha:** 2026-10-07 · **Para:** el dueño, que va a fijar los criterios él mismo · **Alcance:** sólo los pasos 13 (MC Retest en SQX) y 14 (análisis en Python).

**Qué es:** el documento de consulta del paso 14, con la misma forma que el del paso 8 (`puerta-is-oos-paso-08-especificacion-2026-10-06`) y el del paso 10 (`criterios-paso-10-otros-mercados-2026-10-06`). Explica desde cero la estadística que este paso añade, repasa **todos** los números que escribe el estudio (288 hechos por estrategia, no sólo el único que hoy lee el criterio), cita el criterio tal como está hoy en `pipeline/autopilot/criteria.yaml`, y cierra con lo que no cuadra y con las decisiones que te quedan.

**De dónde salen los números.** Todos los ejemplos son de la corrida `Trade_NIKKEI225_M30_volatilidadL` del 2026-10-04 (NIKKEI225, M30, largas): diez estrategias, siete tareas de MC Retest, 25.998 re-ejecuciones y 5.683.058 operaciones simuladas. Están **recalculados desde las re-ejecuciones** con el código del estudio y comparados con lo que quedó guardado: para las cuatro estrategias que seguimos de cerca, los hechos del veredicto, de la cola del estrés, de la tabla de costes y de las distribuciones que cito coinciden; para las otras seis he recalculado los números por tarea (percentiles, retenciones, proporciones) y el hecho que lee el criterio. Donde un ejemplo usa sólo el valor guardado, se dice. «Ilustrativo» quiere decir cuenta hecha a mano para enseñar, no medida.

**Ninguna línea de este documento está congelada.** El propio fichero de criterios lo dice: provisional hasta que una población sin ventaja haya recorrido la cadena.

---

## 0. En una página

**La pregunta del paso.** Si el mundo se parece al backtest pero no es idéntico —el spread es algo mayor, la orden entra un poco peor, el parámetro óptimo no era exactamente ése, las velas del broker no son las del histórico—, ¿la estrategia sigue ganando o sólo ganaba en esa foto exacta?

**Lo que hay cargado hoy** (una sola regla, sin banda de Limbo):

`mcRetest.stress.la_cola.profit_factor_p5.valor`

| | Pasa | Limbo | Falla |
|---|---|---|---|
| PF p5 del estrés | ≥ 1,0 | sólo si falta el dato | < 1,0 |

**Lo que sale en la corrida real:** 4 **Pasa**, 6 **Falla**, 0 Limbo.

**Las siete cosas que conviene saber antes de leer el resto:**

1. **«PF p5 ≥ 1,0» es lo mismo que «al menos el 95 % de las 500 re-ejecuciones del estrés acaban en beneficio».** Un profit factor es mayor que 1 exactamente cuando el neto es positivo, así que el percentil 5 del PF está por encima de 1 cuando como mucho 24 o 25 de las 500 re-ejecuciones pierden. Es una línea mucho más dura que el «70 % de las pruebas rentables» de Kaufman, que admitiría 150 perdedoras (apartado 2.6).
2. **La tarea de estrés hace toda la matanza.** Con la misma línea aplicada a cada tarea por separado fallarían: parámetros 3, salidas 2, spread 1, slippage 1, histórico 1, barra inicial 0. El estrés, 6. Las seis que mata el estrés incluyen a todas las que mataría cualquier otra tarea.
3. **El estrés no es «un poco de todo»: es sobre todo coste.** Cobra toda la ventana `build..oos1` al coste de `oos1` (un 56 % más caro que el del build) y encima sortea spread y slippage entre 0,5 y 2 veces ese coste. La re-ejecución mediana conserva el 62 % del beneficio del original (mediana de las diez); el percentil 5, en la mejor de las diez, el 43 %.
4. **Corrieron siete tareas, no ocho, y el estrés combina cinco perturbaciones, no seis.** La tarea de distancia mínima (MCR 4) no corre con órdenes a mercado, y el estrés no lleva ni distancia mínima ni barra inicial.
5. **El estudio tiene su propio veredicto, más duro, y el criterio no lo lee.** Con sus vetos (PF p5 > 1,10, CVaR del drawdown ≤ 25 %, retención de ejecución ≥ 0,70…) las diez quedan fuera: 9 `FAIL` y 1 `INCONCLUSIVE`. El hecho `mcRetest.verdict.pass` vale 0 para las diez, mientras la regla cargada aprueba a cuatro.
6. **Un percentil 5 sacado de 500 tiradas tiene error.** Su intervalo del 95 % va de la 17.ª a la 36.ª peor re-ejecución. Una de las seis que fallan, `3.9.284`, falla dentro de ese ruido: PF p5 = 0,984 con intervalo de 0,975 a 1,011.
7. **Nadie ha medido lo que este paso deja pasar ni lo que mata por error.** No existe una población sin ventaja que haya recorrido la cadena hasta aquí. Por eso el Council lo dejó en «sólo mata»: pasar no es evidencia, es «no está muerta». Y las diez estrategias de esta corrida son un sorteo que hoy fallaría el paso 8.

---

## 1. Qué son los pasos 13 y 14 y cómo deciden

### 1.1 Dónde están

El paso 12 (otros timeframes) deja sus supervivientes en el databank `CrossTF_Mothers`. El **paso 13** las vuelve a ejecutar en SQX cientos de veces, cada vez con algo cambiado. El **paso 14** es Python: lee todas esas re-ejecuciones, calcula sus números y aplica la regla de `criteria.yaml`. Lo que falla se borra del databank `MCR 8 Stress`, que es el que lee el paso siguiente (SPP, pasos 15 y 16). Los otros siete databanks de MC Retest conservan a todas: sirven para explicar, no para cortar.

En `docs/AgentPDFs/WORKFLOW.md` el paso 13 figura como hecho y el 14 como a medias.

### 1.2 El paso 13: las tareas de SQX

No es una tarea, son ocho, y las ocho leen **el mismo databank**: son ocho lecturas de una misma población. Las escribe `sqx/projects/mcretest.py` desde el catálogo `assets/_build.yaml` (bloque `mc_retest`). Cuatro cosas las definen a todas:

- **Un método por tarea.** Si una tarea mezclara dos perturbaciones no se podría saber cuál hizo el daño. Las tareas 1 a 7 llevan una sola; la 8 las junta a propósito.
- **No filtran nada.** Las condiciones de aceptación de SQX van apagadas. Con una viva, SQX no guardaría las estrategias que la incumplen y Python se quedaría sin saber qué tarea rompió a cuál.
- **Los rangos de coste salen de la ficha del activo**, no de los de fábrica de SQX (que son «de 1 a 5» y «de 0 a 5» y no significan nada para un índice). La regla es de `assets/RULES.md`: entre **0,5 y 2 veces** el coste del tramo.
- **Nunca `oos2`.** Las tareas 1 a 7 corren sobre el `build`; la 8, sobre `build..oos1`, y cobra toda la ventana al coste del último tramo, `oos1`.

El apartado 2.2 las recorre una a una. Aquí, la tabla de lo que **corrió de verdad** el 2026-10-04 según el manifiesto de la ingesta:

| tarea | sims | qué cambia | ventana |
|---|---|---|---|
| MCR 1 Bar | 200 | la barra en la que empieza el backtest | build |
| MCR 2 Spread | 200 | el spread | build |
| MCR 3 Slippage | 200 | el slippage | build |
| MCR 4 MinDist | — | no corrió (órdenes a mercado) | — |
| MCR 5 Params | 500 | los parámetros | build |
| MCR 6 Exits | 500 | los parámetros de salida | build |
| MCR 7 OHLC | 500 | las velas del histórico | build |
| MCR 8 Stress | 500 | cinco de las anteriores a la vez | build..oos1 |

El paso 14 tardó 105 segundos en Python para las diez estrategias.

### 1.3 Qué datos lee el paso 14

- **Las re-ejecuciones.** 10 estrategias × (200 + 200 + 200 + 500 + 500 + 500 + 500) = 26.000; llegaron 25.998, porque dos corridas de la tarea de histórico guardaron 499 en vez de 500 (`15.9.352` y `4.13.338`). De cada re-ejecución SQX guarda sus operaciones; el estudio reconstruye desde ellas 30 métricas (beneficio neto, profit factor, número de operaciones, drawdown en USD y en %, operación media, desviación…) y comprueba que cuadran con las de SQX: en esta corrida, ninguna celda sin cuadrar. De las 148 métricas que enseña SQX sólo esas 30 se pueden rehacer desde las operaciones.
- **El original de cada tarea.** El backtest sin perturbar, en la misma ventana y con el mismo coste que la tarea. Para las tareas 1 a 7 es el del `build` (2011-09-19 a 2019-12-31); para el estrés es **otro**: `build..oos1` (2011-09-19 a 2023-12-31) al coste de `oos1`.
- **Las operaciones de `oos1`** del databank (1.162 entre las diez), que sólo se usan para un número de apoyo (el PSR, apartado 3.9).
- **Los costes**, de la ficha de NIKKEI225:

| | build | oos1 |
|---|---|---|
| spread (puntos) | 304,11 | 474,91 |
| slippage (puntos) | 106,44 | 166,22 |
| comisión | 0 | 0 |

El spread del build equivale al 0,0174 % del precio medio (17.525,7), unos 3 puntos de índice. El de `oos1` es 1,56 veces el del build.

- **El tamaño de la posición.** Capital inicial de 100.000 USD y riesgo fijo de 1.000 USD por operación (stop a 4 ATR). Es decir, **1R = 1.000 USD = 1 % de la cuenta de SQX**. Te servirá para leer los drawdowns.

### 1.4 Los tres estados y el corte

| estado | qué significa | qué hace el workflow |
|---|---|---|
| **Pasa** | PF p5 del estrés ≥ 1,0 | sigue al paso 15 |
| **Limbo** | sólo si falta el dato | sigue, **marcada** |
| **Falla** | PF p5 del estrés < 1,0 | se **borra** de `MCR 8 Stress` |

### 1.5 Cómo se combinan las reglas

Como en todos los pasos: cada regla lee un hecho y da Pasa, Limbo o Falla, y el resultado de la estrategia es el de **su peor regla** (`pipeline/autopilot/criteria.py:99`). Aquí sólo hay una regla, así que no hay nada que combinar. La regla no declara línea de Limbo ni dice qué hacer si falta el dato; sin decirlo, un hecho que falta es Limbo.

### 1.6 Cuatro avisos

1. **En la corrida real el paso 14 no juzgó.** El resumen del piloto dice «2707 hechos; ninguno: el paso no tiene criterio»: el 2026-10-04 el paso aún no tenía regla. La de hoy se cargó después. Los veredictos de este documento los he calculado **en memoria** con `pipeline.autopilot.criteria` sobre los hechos de aquella corrida.
2. **Las diez estrategias son un sorteo.** El paso 8 de aquella corrida fue «10.000 → 10 por sorteo», sin mirar el veredicto. Con las reglas de hoy las diez fallan el paso 8 y las diez fallan el paso 10 (lo cuenta el documento del paso 10). Esta población enseña cómo trata el paso 14 a estrategias **sin ventaja demostrada**; no cómo trata a las que llegarían con mérito.
3. **Los hechos guardados son de las 16:38 y la carpeta del estudio se reescribió a las 22:14 con código más nuevo.** Hay hechos que hoy se llamarían de otra manera (apartado 5.6).
4. **`segment: oos1` en el criterio es una etiqueta, no lo que se lee.** El hecho de la regla sale de 500 re-ejecuciones sobre `build..oos1` entero.

### 1.7 Las estrategias que nos acompañan

Las mismas tres del documento del paso 10 —**C**, **E** y **F**— están en esta población y aquí sí hay una de cada lado de la regla. Añado `10.11.484` porque es la del ejemplo del primer informe (49,98; 45,74; 0,996).

| | **C** | **E** | **F** | `10.11.484` |
|---|---|---|---|---|
| nombre | `14.3.479` | `3.11.426` | `15.9.352` | — |
| neto del build (USD) | 13.239 | 22.508 | 2.944 | 20.297 |
| PF del build | 1,47 | 1,59 | 1,04 | 1,48 |
| operaciones del build | 189 | 135 | 224 | 154 |
| PF p5 del estrés | 0,846 | 1,081 | 0,706 | 1,069 |
| regla cargada | Falla | Pasa | Falla | Pasa |

---

## 2. Fundamentos de este paso

### 2.0 Lo que ya sabes del paso 8, en seis líneas

El documento del paso 8 (apartado 2, «La estadística mínima») enseña lo que aquí se da por sabido:

```
error estándar = desv / √n
t = media / (desv / √n) = s × √n            s = media / desv (Sharpe por operación)
Φ(t) = probabilidad de que una normal estándar quede por debajo de t
p = 1 − Φ(t)                                 lo que diría la teoría si no hubiera ventaja
```

`Φ(0) = 0,50`, `Φ(0,52) = 0,70`, `Φ(1,65) = 0,95`, `Φ(2,33) = 0,99`. Y dos advertencias de allí que aquí vuelven: una `p` teórica no es una tasa de falsos positivos **medida** (en el paso 8 se midió: t ≥ 1,65 deja pasar el 3,9 % de las estrategias sin ventaja; t ≥ 2,33, el 0,6 %), y la **potencia** es la otra mitad de un filtro: cuántas de las buenas deja vivas.

En este documento, cuando escribo «la t» de una estrategia me refiero a la simple, `media por operación / desviación × √n`, calculada con las cifras de SQX. No es la t del exceso sobre la deriva del paso 8.

Todo lo demás de este apartado es nuevo.

### 2.1 Qué es un MC Retest, y en qué se diferencia del otro Monte Carlo

Hay dos cosas muy distintas que se llaman «Monte Carlo» en este proyecto.

**El Monte Carlo de operaciones** (el de carteras, en `portfolio/`) coge la lista de operaciones que ya existe y la **baraja o la re-muestrea**. No vuelve a ejecutar nada. Si barajas las 135 operaciones de E, el beneficio final es siempre el mismo (22.508 USD: la suma no depende del orden); lo único que cambia es el camino, y por tanto el drawdown. Si en vez de barajar sacas 135 operaciones al azar **con repetición** de esas mismas 135 (bootstrap), entonces sí cambia el beneficio, pero sólo porque unas operaciones salen dos veces y otras ninguna. En los dos casos las operaciones son las que son: ninguna entra a otro precio ni en otra barra.

**El MC Retest** hace otra cosa: **vuelve a ejecutar el backtest entero**, de la primera barra a la última, con una pieza de la entrada cambiada. Si el spread es mayor, cada operación cuesta más. Si un parámetro se mueve un 10 %, la señal salta en otras barras: aparecen operaciones nuevas y desaparecen otras. Si se retocan las velas, un stop que no saltaba ahora salta. Cada re-ejecución es **otra historia posible** de la misma estrategia, no la misma historia recolocada.

La diferencia práctica:

| | Monte Carlo de operaciones | MC Retest |
|---|---|---|
| ¿se vuelve a ejecutar? | no | sí, entero |
| ¿cambian las operaciones? | no (sólo su orden o su peso) | sí |
| qué duda responde | ¿fue suerte el orden? ¿cuánto drawdown cabe? | ¿aguanta si el mundo no es el del backtest? |
| qué no puede ver | nada peor que la peor operación que ya ocurrió | nada fuera de los rangos que tú le das |

Con E se ve la diferencia en una cifra. Si re-muestreas sus 135 operaciones del build, el beneficio baila con una desviación de `1.004 × √135 = 11.666 USD` (lo he comprobado con 20.000 remuestreos: 11.710). Si en cambio re-ejecutas con el spread perturbado, la desviación entre las 200 re-ejecuciones es de **1.303 USD**; con los parámetros perturbados, 5.751; con todo a la vez, 9.986. Son números de naturaleza distinta: el primero mide **la suerte de la muestra**; los otros, **cuánto mueve el resultado la perturbación que elegiste**. Esta distinción decide todo el apartado 2.7.

### 2.2 Las ocho tareas, una a una

Para cada una: qué perturba, con qué rango real, cuántas re-ejecuciones, qué duda del mundo real representa, y qué le hizo a E (cuyo original del build gana 22.508 USD).

**MCR 1 — Barra inicial (el control).** 200 re-ejecuciones. El backtest empieza hasta 500 barras más tarde, al azar (`RandomizeStartingBar`, `MaxChange: 500`). No toca ni la estrategia ni el mercado ni el coste: sólo el punto de arranque. La duda que representa: ¿depende el resultado de la barra exacta en la que empezaste (indicadores que aún se están calentando, una primera operación que desplaza a las siguientes)? Para el estudio es además **el control**: lo que se mueva aquí es el ruido de fondo con el que se compara todo lo demás. En E: 23 resultados distintos entre los 200, desviación de 392 USD, percentil 5 de 22.506 (retiene el 100,0 %).

**MCR 2 — Spread.** 200 re-ejecuciones. El spread se sortea entre **152,055 y 608,22 puntos**, que es de 0,5 a 2 veces el del build (304,11). La duda: tu spread real no va a ser el de la ficha; puede ser el doble en una apertura o en una noticia. El tope de 2× es constante y no modela picos: un spread de 5-10 veces durante unos minutos queda fuera de la prueba, y esta población, que es de volatilidad, entra justo entonces. En E: percentil 5 de 19.846 USD (retiene el 88,2 %), mediana 21.969, las 200 en beneficio.

**MCR 3 — Slippage.** 200 re-ejecuciones. Slippage entre **53,22 y 212,88 puntos** (0,5 a 2 veces 106,44). La duda: la orden a mercado no entra al precio que viste. En E: percentil 5 de 20.581 (retiene el 91,4 %).

Cómo reparte SQX el sorteo dentro del rango (uniforme o no, uno por re-ejecución o uno por operación) no queda grabado en lo que se ingiere: **no medido**. Si fuera uniforme, el múltiplo medio sería 1,25.

**MCR 4 — Distancia mínima.** 100 re-ejecuciones previstas. Sólo tiene sentido con órdenes stop o limit (perturba la distancia mínima a la que el broker deja ponerlas). Con órdenes a mercado no hay nada que perturbar, y por regla del proyecto las entradas son a mercado: **no corrió**, y su método tampoco entra en el estrés.

**MCR 5 — Parámetros.** 500 re-ejecuciones. Todos los parámetros de la estrategia se mueven a la vez (`Probability: 100`), cada uno hasta un ±15 % (`MaxChange: 15`, `Symmetric: true`). La duda: el optimizador eligió un periodo de 23; ¿sigue funcionando con 20 o con 26, o el 23 era un pico aislado? Es la prueba clásica contra el sobreajuste. En E: percentil 5 de 5.918 (retiene el **26,3 %**), mediana 15.565 (69 %), 498 de 500 en beneficio. Es la tarea aislada que más daño le hace.

**MCR 6 — Salidas.** 500 re-ejecuciones. Sólo los parámetros de salida (stop, objetivo, etc.), hasta un ±30 %. La duda: ¿la ventaja está en la entrada, o sólo en una salida afinada al milímetro? En E: percentil 5 de 11.900 (retiene el 52,9 %). Un detalle: de las 500 re-ejecuciones sólo salen **16 resultados distintos** (entre 6 y 28 según la estrategia). Los parámetros de salida son pocos y van en escalones, así que el sorteo cae una y otra vez en las mismas combinaciones. No son 500 pruebas: son una rejilla de una veintena.

**MCR 7 — Histórico (OHLC).** 500 re-ejecuciones. Cada uno de los cuatro precios de cada vela se retoca con probabilidad del 30 %, hasta un 15 % del ATR de 14 barras, manteniendo las velas enlazadas; los huecos entre velas, igual (30 %, hasta 15 %). La duda: los datos de tu broker no son los del histórico; una vela con el máximo dos puntos más arriba, ¿cambia la señal? En E: percentil 5 de 21.956 (retiene el 97,5 %). Es la tarea que menos daña a casi todas.

**MCR 8 — Estrés combinado.** 500 re-ejecuciones. Cinco métodos a la vez: spread, slippage, parámetros (±15 %), salidas (aquí ±**15 %**, no el ±30 % de la tarea 6) e histórico. Y con dos diferencias de fondo respecto a las otras siete:

- **La ventana es `build..oos1`** (2011-09-19 a 2023-12-31), cuatro años más.
- **El coste es el de `oos1`** para toda la ventana, y los rangos se calculan sobre él: spread entre **237,455 y 949,82** puntos, slippage entre **83,11 y 332,44**.

Su original, por tanto, no es el del build. Para E es 39.364 USD (227 operaciones, PF 1,65). La duda que representa: todo lo anterior a la vez, que es como ocurre de verdad. En E: percentil 5 de 7.593 (retiene el 19,3 %), mediana 23.580 (59,9 %), 492 de 500 en beneficio.

**La precisión.** En la corrida, las tareas de spread, slippage, salidas, histórico y estrés se ejecutaron con datos de un minuto; las de barra inicial y parámetros, con el timeframe elegido (M30).

### 2.3 La distribución entre simulaciones y los percentiles

Una tarea de 500 re-ejecuciones te da 500 beneficios netos, 500 profit factors, 500 drawdowns. Eso es una **distribución**: no «el resultado», sino el abanico de resultados. Para resumirla se usan percentiles.

**El percentil 5 (p5)** es el valor por debajo del cual queda el 5 % de las re-ejecuciones. De 500, las 25 peores quedan por debajo; las otras 475, por encima. «p5 del PF = 1,08» se lee: *en 19 de cada 20 mundos perturbados el profit factor fue de 1,08 o más*.

**Cómo se calcula.** El estudio usa `np.percentile`, que interpola en línea recta entre dos re-ejecuciones vecinas:

```
1. Ordena los N valores de menor a mayor: x₁ ≤ x₂ ≤ … ≤ x_N
2. posición = 1 + (N − 1) × 0,05
3. Si la posición no es entera, interpola entre los dos vecinos
```

Con `N = 500`: posición = 1 + 499 × 0,05 = 25,95. Es decir, el p5 está entre la 25.ª y la 26.ª peor, al 95 % del camino hacia la 26.ª.

**Ejemplo, E, profit factor del estrés.** Ordenados los 500, el 25.º vale 1,0762 y el 26.º vale 1,0810:

```
p5 = 1,0762 + 0,95 × (1,0810 − 1,0762) = 1,0762 + 0,0046 = 1,0807
```

El hecho guardado es 1,08073. Coincide.

Con `N = 200` la posición es 1 + 199 × 0,05 = 10,95: entre la 10.ª y la 11.ª peor. Para el neto de E en la tarea de spread: 19.841,82 y 19.845,73, luego `p5 = 19.841,82 + 0,95 × 3,91 = 19.845,53`. Guardado: 19.845,5.

**La mediana (p50)** es el valor central: la mitad de las re-ejecuciones queda por debajo. Es «el mundo perturbado típico». Para E en el estrés, 23.580 USD.

**El percentil 95** se usa por el otro lado para el drawdown, donde lo malo es lo alto.

**Dos trampas de lectura:**

- **Un percentil no es un escenario.** El p5 del neto, el p5 del PF y el p95 del drawdown no ocurren en la misma re-ejecución. Cada uno se calcula ordenando su propia columna. La re-ejecución que tuvo el peor drawdown puede haber acabado ganando.
- **Los percentiles describen las perturbaciones que tú elegiste.** Si el rango de spread fuera de 0,5 a 3 veces, el p5 sería otro. No es una propiedad de la estrategia sola: es de la estrategia **con ese catálogo de perturbaciones**.

### 2.4 El error de un percentil 5, y el intervalo que da el estudio

500 re-ejecuciones son una muestra. Si SQX volviera a sortear otras 500, el p5 saldría algo distinto. ¿Cuánto?

**La idea.** Imagina que conocieras el p5 «de verdad» (el de infinitas re-ejecuciones). Por definición, cada re-ejecución tiene un 5 % de probabilidad de caer por debajo de él. Entonces el número de re-ejecuciones que caen por debajo, de `N`, es como tirar `N` veces una moneda trucada al 5 %: sigue una **binomial**.

```
media      = N × 0,05
desviación = √(N × 0,05 × 0,95)
```

Con `N = 500`: media 25, desviación √23,75 = **4,87**. Lo normal es que entre 16 y 35 re-ejecuciones caigan por debajo del p5 verdadero. Dicho al revés: **el p5 verdadero está, casi seguro, entre la 17.ª y la 36.ª peor de tus 500**.

Con `N = 200`: media 10, desviación √9,5 = **3,08**. El p5 verdadero está entre la 5.ª y la 17.ª peor de las 200.

**Lo que hace el código, exactamente** (`studies/breakage/mcRetest/verdict/fragility.py`, líneas 7 a 36):

```
ordenados = los N valores de menor a mayor
punto = np.percentile(ordenados, 5)
k_bajo = binom.ppf(0,025; N; 0,05)      → 16 con N = 500;  4 con N = 200
k_alto = binom.ppf(0,975; N; 0,05)      → 35 con N = 500; 16 con N = 200
desde = ordenados[k_bajo]               (contando desde 0: el 17.º y el 5.º)
hasta = ordenados[k_alto]               (el 36.º y el 17.º)
```

`binom.ppf(q; N; p)` es el número de «caras» que una binomial no supera con probabilidad `q`. El intervalo se llama «de estadísticos de orden»: no supone ninguna forma para la distribución, sólo cuenta posiciones. La cobertura exacta de ese par de posiciones es del **94,6 %** con 500 y del **95,0 %** con 200: en torno al 95 % nominal, y con 500 algo por debajo, porque las posiciones son enteras.

**Ejemplo, E, PF del estrés.** El 17.º peor de los 500 vale 1,0457; el 36.º, 1,1040. Hechos guardados: `intervalo_95_desde` = 1,04572, `hasta` = 1,10395. Coincide. Lectura: el p5 del PF es 1,08, y con otras 500 tiradas podría haber salido entre 1,05 y 1,10.

En percentiles, el intervalo con 500 va del 3,4 % al 7,2 %; con 200, del 2 % al 8 %. Con 1.000 re-ejecuciones iría de la posición 38 a la 65 (3,7 % a 6,4 %): doblar las tiradas no estrecha gran cosa.

**Lo que este intervalo NO cubre.** Sólo mide el error de haber hecho 500 tiradas y no infinitas. No dice nada de si los rangos elegidos (0,5 a 2 veces el coste, ±15 %) son los correctos, ni de la suerte del histórico (que el periodo 2011-2023 fuera favorable). Es un intervalo estrecho alrededor de una pregunta estrecha.

**Por qué importa para la regla.** La regla lee el **punto**, no el intervalo. Una estrategia con PF p5 = 0,984 falla aunque su intervalo llegue a 1,011. El apartado 4.5 cuenta cuántas están en ese caso (una).

### 2.5 La retención

**Qué es.** Cuánto del beneficio original conserva el mundo malo:

```
retención = beneficio p5 de la tarea / beneficio del original de esa tarea
```

En hechos: `mcRetest.tasks.<tarea>.p5` dividido entre `mcRetest.tasks.<tarea>.real`. El estudio no guarda el cociente como hecho; lo usa por dentro para las notas (apartado 2.9).

**Ejemplo, E:**

| tarea | p5 (USD) | original | retención |
|---|---|---|---|
| spread | 19.845,54 | 22.508,15 | 0,882 |
| slippage | 20.581,47 | 22.508,15 | 0,914 |
| parámetros | 5.918,17 | 22.508,15 | 0,263 |
| salidas | 11.900,45 | 22.508,15 | 0,529 |
| histórico | 21.955,94 | 22.508,15 | 0,975 |
| estrés | 7.592,81 | 39.364,02 | 0,193 |

**Cómo leerla.** 1,0 = el mundo malo gana lo mismo que el original. 0,5 = gana la mitad. 0 = queda a cero. Negativa = el mundo malo **pierde**.

**La trampa del denominador.** La retención es un cociente, y un cociente estalla cuando el denominador es pequeño. F gana en el estrés original sólo 3.855 USD; su p5 es −38.185. Retención: −38.185 / 3.855 = **−9,9**. No significa «diez veces peor que E»: significa que F casi no ganaba nada y que una pérdida corriente, dividida entre casi nada, da un número enorme. Para comparar estrategias con originales muy distintos la retención engaña; el profit factor p5 o la proporción de re-ejecuciones rentables no tienen ese problema. Si el original fuera negativo, el cociente cambiaría de signo y dejaría de tener sentido: el estudio sólo lo calcula cuando el original es positivo.

**Retención mediana.** La misma cuenta con la mediana en vez del p5 (`.median / .real`) dice cuánto se pierde en el mundo perturbado **típico**, no en el malo. Para E en el estrés: 23.580 / 39.364 = 0,599. Es la cifra que mejor describe lo que cuesta el estrés «de media».

### 2.6 Por qué «PF p5 ≥ 1,0» quiere decir «el 95 % de los mundos gana»

**El profit factor** es beneficio bruto dividido entre pérdida bruta:

```
PF = G / L           G = suma de las operaciones ganadoras
                     L = suma (en positivo) de las perdedoras
neto = G − L
```

De ahí sale directamente que `PF > 1` ocurre exactamente cuando `G > L`, es decir, cuando `neto > 0`. **Una re-ejecución tiene PF mayor que 1 si y sólo si acabó en beneficio.** Con el original del estrés de E: G = 100.066,73, L = 60.702,71; PF = 1,648; neto = 39.364,02.

Lo he comprobado en las 5.000 re-ejecuciones de estrés de las diez estrategias: no hay ninguna con PF menor que 1 y neto positivo, ni al revés.

Ahora une eso con el percentil. El p5 del PF está entre la 25.ª y la 26.ª peor re-ejecución de 500:

- Si pierden **24 o menos**, la 25.ª ya gana → p5 ≥ 1 → **Pasa**.
- Si pierden **26 o más**, la 26.ª todavía pierde → p5 < 1 → **Falla**.
- Si pierden exactamente 25, depende de la interpolación.

Es decir: **la regla cargada pide que al menos 475 de 500 re-ejecuciones del estrés (el 95 %) acaben en beneficio.** En la población real se cumple al pie de la letra:

| estrategia | pierden (de 500) | rentables | PF p5 | regla |
|---|---|---|---|---|
| `4.13.338` | 0 | 100,0 % | 1,154 | Pasa |
| `10.11.484` | 2 | 99,6 % | 1,069 | Pasa |
| `18.5.355` | 7 | 98,6 % | 1,053 | Pasa |
| E `3.11.426` | 8 | 98,4 % | 1,081 | Pasa |
| `3.9.284` | 29 | 94,2 % | 0,984 | Falla |
| `13.3.390` | 109 | 78,2 % | 0,903 | Falla |
| C `14.3.479` | 149 | 70,2 % | 0,846 | Falla |
| `16.5.352` | 157 | 68,6 % | 0,883 | Falla |
| `19.2.363` | 333 | 33,4 % | 0,780 | Falla |
| F `15.9.352` | 381 | 23,8 % | 0,706 | Falla |

**Cuánto más dura es que la línea de Kaufman.** Kaufman pide, para llamar robusta a una estrategia, que al menos el 70 % de las pruebas de parámetros sean rentables. El 70 % de 500 admite **150 perdedoras**; la regla cargada, 24 o 25. Con la línea de Kaufman aplicada al estrés, C (70,2 %: 351 de 500, una más que el mínimo de 350) pasaría por una sola re-ejecución, y `13.3.390` (78,2 %) con holgura; fallarían tres en vez de seis.

**Lo afilada que es la línea.** Supón que la proporción «verdadera» de mundos rentables de una estrategia fuera exactamente del 95 %. ¿Pasaría? La probabilidad de que le salgan 24 perdedoras o menos de 500 es del 47 %: una moneda al aire. Con un 97 % verdadero, pasa el 99 % de las veces; con un 93 %, el 3 %. La regla separa bien «93 % o menos» de «97 % o más»; entre medias decide el sorteo de SQX.

### 2.7 El argumento de Φ(t): por qué el 70 % puede no decir nada, y dónde vale de verdad

En el Council, Feynman dio el argumento que llevó al «sólo mata». Merece hacerse despacio, porque es correcto para una cosa y no para otra.

**El argumento.** Coge una estrategia con `n` operaciones, media `m` y desviación `d`. Si **re-muestreas** sus operaciones (bootstrap), el beneficio de cada remuestreo es una suma de `n` operaciones sacadas al azar:

```
media de la suma      = n × m
desviación de la suma = d × √n
P(suma > 0) ≈ Φ( n × m / (d × √n) ) = Φ( m × √n / d ) = Φ(t)
```

Es decir: **la proporción de remuestreos rentables es, aproximadamente, Φ de la propia t de la estrategia.** No aporta información nueva: es la t dicha de otra manera.

De ahí la aritmética:

- «70 % de los remuestreos rentables» ⇔ Φ(t) ≥ 0,70 ⇔ **t ≥ 0,52**.
- Todo lo que llega a este paso ha pasado una puerta de **t ≥ 1,65**, y Φ(1,65) = **0,95** (la t del paso 8 es la del exceso sobre la deriva, que es menor que la t simple; por eso la t simple de lo que llega es al menos 1,65).

Luego una línea del 70 % la pasaría todo lo que llega. Un filtro que aprueba a todos no distingue a nadie: pasar no cambia lo que sabías. Por eso el Council dijo que un «Pasa» aquí sería «una etiqueta sin contenido».

**Lo he comprobado** con las operaciones del build, 20.000 remuestreos por estrategia:

| estrategia | t | Φ(t) | remuestreos rentables |
|---|---|---|---|
| E | 1,93 | 97,3 % | 97,4 % |
| `10.11.484` | 1,63 | 94,8 % | 94,5 % |
| C | 1,58 | 94,3 % | 94,9 % |
| F | 0,23 | 59,0 % | 59,4 % |

La fórmula clava el resultado. Para el **remuestreo**, el argumento es exacto.

**Pero el MC Retest no remuestrea.** Aquí es donde hay que ser honrado. Una re-ejecución con el spread cambiado no es una muestra al azar de las operaciones: son las mismas operaciones, todas un poco más caras. Dos cosas cambian respecto al argumento:

1. **La dispersión no es la del muestreo.** La desviación entre re-ejecuciones depende de cuánto mueve el resultado la perturbación, no de `d × √n`. Para E (`d × √n` = 11.666 USD en el build):

| tarea | desviación entre re-ejecuciones (USD) |
|---|---|
| barra inicial | 392 |
| histórico | 891 |
| slippage | 897 |
| spread | 1.303 |
| salidas | 4.494 |
| parámetros | 5.751 |
| estrés | 9.986 |

2. **La media se desplaza.** El spread sorteado entre 0,5 y 2 veces el de la ficha es, de media, más caro que el de la ficha. El centro de las re-ejecuciones no es el original: queda por debajo.

La fórmula que sí describe lo que pasa es la misma, pero con los números de las re-ejecuciones:

```
proporción rentable ≈ Φ( mediana de las re-ejecuciones / desviación entre re-ejecuciones )
```

En el estrés de las diez:

| estrategia | Φ(t del original) | mediana / desv | Φ de eso | rentables reales |
|---|---|---|---|---|
| `4.13.338` | 99,9 % | 4,18 | 100,0 % | 100,0 % |
| `10.11.484` | 98,5 % | 2,38 | 99,1 % | 99,6 % |
| E | 99,7 % | 2,36 | 99,1 % | 98,4 % |
| `18.5.355` | 99,0 % | 2,20 | 98,6 % | 98,6 % |
| `3.9.284` | 98,4 % | 1,70 | 95,6 % | 94,2 % |
| `13.3.390` | 87,5 % | 0,94 | 82,6 % | 78,2 % |
| `16.5.352` | 68,9 % | 0,50 | 69,3 % | 68,6 % |
| C | 91,6 % | 0,43 | 66,7 % | 70,2 % |
| `19.2.363` | 62,6 % | −0,42 | 33,8 % | 33,4 % |
| F | 59,0 % | −0,68 | 24,7 % | 23,8 % |

La segunda es una aproximación normal: acierta en el centro y sirve para ordenar, no para predecir la proporción exacta. En la cola del 5 %, que es donde vive la regla, se queda corta: a `3.9.284` le da 95,6 % (Pasa) y saca 94,2 % (Falla); a E le predice 4,5 mundos perdedores y son 8. No la uses para decidir cerca de la línea. La primera, `Φ(t del original)`, falla por arriba en todas las débiles: a C le prometía un 92 % y saca un 70 %, porque el estrés le baja la mediana de 13.972 a 3.458 USD.

**Qué se saca en limpio:**

- **Donde la perturbación no desplaza la media ni dispersa** (barra inicial, y casi el histórico), casi todo sale rentable aunque la estrategia no valga nada. F, con una t de 0,23, tiene el 100 % de las re-ejecuciones de barra inicial en beneficio. Ahí una línea de «70 % rentables» no es que sea floja: es que no mide nada.
- **Donde la perturbación es un coste** (spread, slippage), el resultado es casi determinista: la estrategia gana si su margen por operación supera el coste añadido. F aguanta el 71 % de las re-ejecuciones de spread y el 88,5 % de las de slippage: **pasaría la línea de Kaufman en las dos**. Aquí el argumento de Feynman se queda corto: incluso una estrategia indistinguible de cero (t = 0,23) pasaría la línea del 70 % en las dos; y esa línea, de Kaufman, se pensó para pruebas de parámetros, no de coste.
- **En el estrés**, que desplaza mucho la media, la línea del 70 % sí separa: fallan tres de diez. Pero entre las cinco que llegan con t ≥ 1,65 en el original del estrés (`4.13.338`, `10.11.484`, E, `18.5.355`, `3.9.284`), **las cinco pasan el 70 % con holgura** (94 % o más). Para lo que de verdad llegaría a este paso, la conclusión del Council se sostiene en estos datos: el 70 % no cortaría a ninguna; el 95 % corta a una.

Cinco estrategias de un sorteo no son una medida. Pero la dirección es la del argumento.

### 2.8 El lado del drawdown

Hasta aquí, el lado del beneficio. El MC Retest también dice algo del drawdown, y aquí hay tres números con nombre propio.

**Qué drawdown mide el estudio.** `DrawdownPct` es la peor caída desde un máximo, en porcentaje **del capital más el máximo alcanzado** (`model/drawdown.py`, líneas 90 a 99), no del capital inicial. Para el original del estrés de E: caída de 6.903,86 USD desde una cuenta que estaba en unos 123.000 → 5,61 %. Sobre el capital inicial sería el 6,9 %. Este drawdown se mide entre cierres de operaciones: el fichero de simulación no lleva fechas ni flotante. No ve el MAE ni agrupa por días, así que no sirve para contrastar un límite diario, y el flotante real será mayor.

**El CVaR del drawdown.** «Valor en riesgo condicional»: la media de la cola mala. El estudio (`verdict/fragility.py`, líneas 57 a 75) hace:

```
borde = percentil 95 del drawdown entre las re-ejecuciones
CVaR  = media de los drawdowns que son ≥ borde
```

Con 500 re-ejecuciones, es la media de los 25 peores drawdowns. Para E en el estrés: borde 12,85 % (sobre el pico de la cuenta; en R, sobre el capital inicial, es el 15,7 % de abajo), CVaR **16,16 %**. La diferencia con el p95 es que el p95 te dice dónde empieza la cola y el CVaR cuánto de mala es por dentro. Si los 25 peores fueran todos de 13 %, CVaR y p95 casi coincidirían; que el CVaR sea 3,3 puntos mayor dice que la cola se alarga (el peor de los 500 fue del 27,3 %).

**Los tres números de referencia:**

- **1,95, medido.** El Council midió, sobre las estrategias robustas del proyecto, el cociente entre el percentil 95 del drawdown al **barajar** las operaciones y el drawdown observado: mediana **1,95**. Es una mediana: la mitad de las estrategias sale por encima. Lo he reproducido con las diez de esta corrida (operaciones del build, 3.000 barajas cada una): mediana **1,9**, con valores de 0,98 a 2,48. Cuadra.
- **2×, de Hill, Pruitt y Hill:** «espera la mitad del beneficio y el doble del drawdown».
- **3×, de Kaufman:** capitaliza la cuenta con tres veces el drawdown máximo del backtest.

El 1,95 da la razón al 2× para el caso de barajar. **Pero barajar es el Monte Carlo suave** (apartado 2.1): las operaciones son las mismas. Barajar, además, rompe las rachas: si las pérdidas llegan agrupadas por régimen, el 1,95 se queda corto. Bajo el estrés del MC Retest los cocientes son mayores:

| | p95 del drawdown ÷ original | CVaR ÷ original |
|---|---|---|
| mínimo de las diez | 2,12 | 2,43 |
| **mediana** | **2,64** | **3,20** |
| máximo | 4,86 | 5,59 |

Ninguna de las diez queda por debajo de 2. La mediana del CVaR, 3,2, está en el número de Kaufman. Lectura: **2× y 3× son medianas, no techos: la mitad de las estrategias los supera. Con 3× dejas fuera a media población; el máximo visto es 5,6×, y es de sólo diez estrategias.** (Diez estrategias de un sorteo; no es una calibración.)

**Ejemplo de tamaño, con E.** Recuerda: 1R = 1.000 USD.

| | USD | en R |
|---|---|---|
| drawdown del build, observado | 6.562 | 6,6 |
| build barajado, percentil 95 | 10.562 | 10,6 |
| regla del 2× | 13.124 | 13,1 |
| regla del 3× | 19.686 | 19,7 |
| estrés, original | 6.904 | 6,9 |
| estrés, re-ejecución mediana | 8.297 | 8,3 |
| estrés, percentil 95 | 15.683 | 15,7 |
| estrés, media de los 25 peores | 18.584 | 18,6 |
| estrés, el peor de los 500 | 27.407 | 27,4 |

Ahora pásalo a porcentaje de cuenta según lo que arriesgues por R:

```
drawdown en % de cuenta = drawdown en R × riesgo por R

al 1 % por R:    15,7 R × 1 %   = 15,7 %     → rompe un límite del 10 %
al 0,5 % por R:  15,7 R × 0,5 % =  7,8 %     → cabe el p95 (ver abajo)
riesgo máximo para que el p95 del estrés quepa en un 10 %:
                 10 % / 15,7 R = 0,64 % por R
para que quepa la media de los 25 peores:
                 10 % / 18,6 R = 0,54 % por R
```

«Cabe el p95» quiere decir que 25 de los 500 mundos lo superan: la media de esos 25 da 9,3 % (18,6 R × 0,5 %) y el peor 13,7 % (27,4 R × 0,5 %), que rompe el 10 %. Para que quepa el peor mundo: 10 % / 27,4 R = 0,36 % por R. En fondeo romper es perder la cuenta, así que dimensionar al p95 es aceptar 1 mundo de cada 20.

SQX mide el drawdown sobre el pico de la cuenta (12,85 %); la cuenta en R lo mide sobre el capital inicial (15.683 / 100.000 = 15,7 %). Una firma de fondeo mide sobre el balance inicial, así que usa 15,7 %.

Encaja con lo que midió el Council por otro camino: al 1 % por R, el 15 % de las supervivientes rompe un límite diario del 5 %; al 0,5 %, ninguna rompe ni el 5 % ni el 10 %.

**Un límite que no hay que olvidar** (Taleb, en el Council): barajar o remuestrear nunca produce una operación peor que la peor que ya hay en la muestra. El MC Retest sí puede, porque re-ejecuta; pero sólo dentro de los rangos que le das. Ninguno de los dos ve el día que no está en el histórico.

### 2.9 El veredicto propio del estudio: curvas, notas, vetos y nota compuesta

El estudio no se limita a dar percentiles: emite su propio veredicto. El criterio cargado no lo lee, pero sus piezas están entre los hechos y conviene saber de dónde sale cada cifra.

**La curva.** Todo se convierte a una nota de 0 a 100 con una línea recta (`verdict/scoring.py`, línea 18):

```
curva(valor; malo; bueno) = 100 × (valor − malo) / (bueno − malo)     recortado a [0, 100]
```

`malo` es el valor que puntúa 0 y `bueno` el que puntúa 100.

**Las cuatro notas** (`verdict/scoring.py`, líneas 57 a 80), con `retención = p5 / original` de cada tarea:

```
execution     = curva( la menor retención entre spread y slippage;  0,70;  1,0 )
specification = curva( la menor retención entre parámetros y salidas;  0;  1 )
data          = curva( retención del histórico;  0;  1 )
production    = la MENOR de tres curvas, todas sobre el estrés:
                  curva( beneficio p5;  0;  0,5 × beneficio original )
                  curva( CVaR del drawdown;  25;  5 )
                  curva( proporción con Sharpe por encima del azar;  0,5;  1,0 )
```

**Ejemplo completo: `10.11.484`** (de aquí salen el 49,98 y el 45,74 del primer informe).

*Ejecución.* Retención de spread: 17.251,54 / 20.297,24 = 0,8499. De slippage: 18.176,39 / 20.297,24 = 0,8955. La menor, 0,8499:

```
execution = 100 × (0,8499 − 0,70) / (1,0 − 0,70) = 100 × 0,1499 / 0,30 = 49,98
```

Lectura del 49,98: en el mundo malo de spread conserva el 85 % del beneficio; el estudio pone el cero en conservar el 70 % y el cien en conservarlo todo; el 85 % queda justo a mitad de camino.

*Producción.* Sobre el estrés (original 31.871,31; p5 7.289,37; CVaR 15,264 %; proporción con Sharpe por encima del azar 0,976):

```
curva 1 = 100 × 7.289,37 / (0,5 × 31.871,31) = 100 × 7.289,37 / 15.935,66 = 45,74
curva 2 = 100 × (15,264 − 25) / (5 − 25)     = 100 × 9,736 / 20           = 48,68
curva 3 = 100 × (0,976 − 0,5) / (1,0 − 0,5)  = 100 × 0,476 / 0,5          = 95,20
production = la menor = 45,74
```

Lectura del 45,74: el p5 del estrés es el 22,9 % del original; el estudio pone el cien en conservar la mitad; 22,9 / 50 = 0,457.

*Especificación.* Retención de parámetros 0,4543; de salidas 0,7245. La menor: **45,43**. *Datos.* Retención del histórico 0,9766: **97,66**.

**La nota compuesta** es una media con pesos fijos (`config.yaml`: producción 0,55; ejecución 0,20; especificación 0,20; datos 0,05):

```
compuesta = 0,55 × 45,74 + 0,20 × 49,98 + 0,20 × 45,43 + 0,05 × 97,66
          = 25,16 + 10,00 + 9,09 + 4,88 = 49,1
```

Guardado: 49,1. Y los escalones: ≥ 80 `STRONG`, ≥ 65 `ACCEPTABLE`, ≥ 50 `MARGINAL`, menos `FAIL`.

**Los vetos.** Por encima de la nota hay vetos (`verdict/gates.py`): si salta uno que «disqualifica», el veredicto es `FAIL` sea cual sea la nota.

| veto | salta si | nombre |
|---|---|---|
| beneficio p5 del estrés | ≤ 0 | `beneficio_no_robusto` |
| PF p5 del estrés | ≤ **1,10** | `beneficio_no_robusto` |
| CVaR del drawdown del estrés | > 25 % | `drawdown_insostenible` |
| operaciones del estrés | mediana < 50 % de las del original | colapso de operaciones |
| Sharpe frente al azar | las dos pruebas < 0,90 | `edge_indistinguible_de_cero` |
| retención de spread o slippage | < 0,70 | `ejecucion_fragil` |
| beneficio p5 de parámetros | ≤ 0 | `sobreajuste_de_parametros` |

Y avisos que no disqualifican pero se anotan: beneficio p5 de histórico o de salidas ≤ 0; y dos de datos, `tarea_sin_dispersion` (la barra inicial dio un solo resultado) y `tabla_de_niveles_corrupta` (SQX guardó menos re-ejecuciones de las pedidas). Un aviso de datos sin veto da `INCONCLUSIVE`: «la evidencia no bastó», que no es lo mismo que «falló».

**El veto del estudio frente a la regla cargada.** Son la misma medida con dos líneas distintas:

| | lee | línea | fallan (de 10) |
|---|---|---|---|
| `criteria.yaml` | PF p5 del estrés | < 1,0 | 6 |
| veto del estudio | PF p5 del estrés | ≤ 1,10 | 9 |

`10.11.484` es el caso que lo enseña. Su PF p5 es 1,0688. Para el criterio, **Pasa** (≥ 1,0). Para el estudio, veto: en la tabla «Qué saltó» queda `que_salto.veto.midio` = 1,06884 contra `que_salto.veto.contra` = 1,1. A E le pasa lo mismo: midió 1,0807 contra 1,1.

El 1,10 del estudio es un colchón del 10 % sobre el punto de equilibrio; no tiene medida detrás (es `gates.min_pf` en `config.yaml`). El 1,0 del criterio es el punto de equilibrio sin colchón.

### 2.10 Por qué «sólo mata», y los dos costes que nadie ha medido

**Qué decidió el Council.** Cuatro de cinco miembros: el paso 14 es **kill-only**. Falla quien pierde bajo estrés; quien no pierde, simplemente sigue. No hay «Pasa con mérito».

**La razón, con Bayes en una línea.** Un filtro cambia lo que sabes de una estrategia en la medida en que las buenas lo pasan más que las malas. Esa razón es el cociente de verosimilitud (LR):

```
LR = P(pasar | tiene ventaja) / P(pasar | no tiene ventaja)
apuestas después = apuestas antes × LR
```

Si casi todo lo que llega pasa —tenga ventaja o no—, las dos probabilidades son parecidas, `LR ≈ 1`, y pasar no mueve nada: sabes lo mismo que antes. Es lo que el apartado 2.7 sugiere para una línea del 70 % sobre estrategias con t ≥ 1,65. Taleb lo dijo así: «un Pasa con LR = 1 es una etiqueta sin contenido».

Fallar, en cambio, sí informa: una estrategia que pierde dinero en el 30 % de los mundos ligeramente perturbados no es una en la que quieras poner una cuenta, tenga o no ventaja en el papel. De ahí la asimetría: **el Falla se cree; el Pasa no se cuenta como evidencia.**

**Lo que el Council propuso como muerte:** PF bajo estrés < 1,0, **o** retención bajo la peor ejecución < 0,5. Hoy está cargada sólo la primera (apartado 5.2).

**Los dos costes sin medir:**

1. **Cuántas sin ventaja sobreviven.** Para saberlo hace falta una población nula —estrategias de entrada al azar, seleccionadas como las de verdad— que recorra la cadena hasta aquí. No existe. Feynman propuso justo esa prueba: «pasad los pasos 14 y 16 sobre monos seleccionados; si más del 90 % de los nulos pasa, la etiqueta está vacía». **No medido.**
2. **Cuántas con ventaja real mueren.** El estrés cobra hasta el doble del coste de `oos1`. Una estrategia con ventaja pequeña pero real por operación puede perder ahí en más del 5 % de los mundos y morir. Para medirlo hacen falta estrategias con ventaja conocida (sintéticas, con una ventaja inyectada). **No medido.**

Sin esos dos números no se puede decir si 1,0 es mejor línea que 0,95 o que 1,05. Se puede decir cuántas mata cada una en esta corrida (apartado 4.5), que es otra cosa.

---

## 3. Lo que calcula el estudio, pieza a pieza

El estudio (`studies/breakage/mcRetest/`) se hace cuatro preguntas: cuánto se rompe (fragilidad), de cuántas maneras (modos), por culpa de qué (atribución) y si lo que queda se distingue del azar (evidencia). De su carpeta de resultados, `pipeline/autopilot/facts.py` saca **288 hechos por estrategia** (2.707 filas entre las diez; no todas tienen todos). Se agrupan así:

| grupo (dentro de `mcRetest.`) | cuántos | apartado |
|---|---|---|
| `tasks`: la distribución por tarea | 77 | 3.1 |
| `levels` y `tasks`: la tabla tarea a tarea | 28 + 28 | 3.2 |
| `levels`: la tabla de SQX | 84 | 3.3 |
| `stress`: la distribución del estrés | 11 | 3.4 |
| `stress.la_cola` | 9 | 3.5 |
| `cost` | 18 | 3.6 |
| `verdict` y `verdict.que_salto` | 6 + 20 | 3.7 |
| `summary` y `verdict_csv` | 3 + 4 | 3.8 |

Los nombres de tarea dentro de los hechos son: `barra_inicial_control`, `spread`, `slippage`, `parametros`, `salidas`, `datos_historicos`, `estres_combinado`.

Sobre los rangos de la población: con diez estrategias, los percentiles 5 y 95 son prácticamente la segunda peor y la segunda mejor. Los doy junto a la mediana cuando el hecho es un número comparable entre estrategias; cuando depende del tamaño de cada una (USD), doy mínimo y máximo.

### 3.1 La distribución del beneficio, tarea a tarea

`mcRetest.tasks.<tarea>.real` · `.median` · `.p1` · `.p5` · `.p10` · `.p25` · `.p50` · `.p75` · `.p90` · `.p95` · `.p99`

**Qué mide.** El abanico del beneficio neto (USD) entre las re-ejecuciones de cada tarea, y al lado el del original (`real`). Once números por tarea, siete tareas.

**Cómo se calcula.** `real` es el neto del backtest sin perturbar de esa tarea. Los demás son `np.percentile` sobre el neto de las re-ejecuciones (apartado 2.3). `median` y `p50` son el mismo número guardado dos veces.

**Ejemplo, E, tarea de spread** (200 re-ejecuciones; recalculado, coincide):

| hecho | USD |
|---|---|
| `real` | 22.508,2 |
| `p1` | 19.625,6 |
| `p5` | 19.845,5 |
| `p25` | 20.745,1 |
| `p50` | 21.968,9 |
| `p75` | 23.091,2 |
| `p95` | 23.831,8 |
| `p99` | 23.953,1 |

Entre el peor 1 % y el mejor 1 % hay 4.300 USD: el spread, de la mitad al doble, mueve el resultado de E un ±10 %. El original (22.508) queda por encima de la mediana (21.969), como debe: el spread sorteado es de media más caro que el de la ficha.

**Cómo leerlo.** Lo útil es dividir entre `real`. La retención del p5 en la población (recalculada para las diez):

| estrategia | spread | slippage | parámetros | salidas |
|---|---|---|---|---|
| `4.13.338` | 0,92 | 0,95 | 0,49 | 0,61 |
| `18.5.355` | 0,92 | 0,95 | 0,26 | 0,60 |
| E `3.11.426` | 0,88 | 0,91 | 0,26 | 0,53 |
| `3.9.284` | 0,87 | 0,91 | 0,39 | 0,78 |
| `10.11.484` | 0,85 | 0,90 | 0,45 | 0,72 |
| `13.3.390` | 0,83 | 0,88 | 0,25 | 0,77 |
| C `14.3.479` | 0,71 | 0,80 | 0,17 | 0,88 |
| `16.5.352` | 0,47 | 0,61 | −1,23 | 0,17 |
| `19.2.363` | 0,00 | 0,32 | −5,19 | −2,12 |
| F `15.9.352` | −0,47 | −0,09 | −5,24 | −2,48 |

| estrategia | barra inicial | histórico | estrés |
|---|---|---|---|
| `4.13.338` | 0,95 | 0,98 | 0,43 |
| `18.5.355` | 0,94 | 0,90 | 0,17 |
| E `3.11.426` | 1,00 | 0,98 | 0,19 |
| `3.9.284` | 0,97 | 0,90 | −0,06 |
| `10.11.484` | 1,00 | 0,98 | 0,23 |
| `13.3.390` | 0,86 | 0,82 | −0,84 |
| C `14.3.479` | 0,76 | 0,90 | −0,61 |
| `16.5.352` | 1,00 | 0,22 | −1,93 |
| `19.2.363` | 1,00 | 0,90 | −7,11 |
| F `15.9.352` | 1,00 | −1,95 | −9,91 |

Y el resumen por tarea:

| tarea | retención p5 (mín · mediana · máx) | retención mediana (mediana de las 10) |
|---|---|---|
| barra inicial | 0,76 · 0,99 · 1,00 | 0,99 |
| slippage | −0,09 · 0,89 · 0,95 | 0,97 |
| histórico | −1,95 · 0,90 · 0,98 | 0,99 |
| spread | −0,47 · 0,84 · 0,92 | 0,95 |
| salidas | −2,48 · 0,60 · 0,88 | 0,93 |
| parámetros | −5,24 · 0,25 · 0,49 | 0,70 |
| estrés | −9,91 · −0,33 · 0,43 | 0,62 |

Tres lecturas:

- **Las tareas de coste aisladas apenas hacen daño a las que tienen margen.** Siete de diez conservan más del 70 % con spread y con slippage. Las tres que no (`16.5.352`, `19.2.363`, F) son las de PF original por debajo de 1,08: no tenían margen que perder.
- **Los parámetros son la tarea aislada más dura.** Ninguna de las diez conserva la mitad en el p5; la mejor, el 49 %. La re-ejecución mediana conserva el 70 %.
- **El estrés no se parece a ninguna otra.** La mediana de la retención p5 es negativa.

**Si la regla cargada (PF p5 ≥ 1,0) se aplicara a cada tarea por separado**, fallarían:

| tarea | fallan | quiénes |
|---|---|---|
| barra inicial | 0 | — |
| spread | 1 | F |
| slippage | 1 | F |
| histórico | 1 | F |
| salidas | 2 | F, `19.2.363` |
| parámetros | 3 | F, `19.2.363`, `16.5.352` |
| **estrés** | **6** | esas tres, C, `13.3.390`, `3.9.284` |

(`19.2.363` en spread tiene un PF p5 de 1,0000165: pasa por la quinta cifra decimal, con un beneficio p5 de 0,45 USD.) El estrés mata a todas las que mataría cualquier otra tarea y a tres más que ninguna tarea aislada mata. **El estrés hace toda la matanza; entre las aisladas, la de parámetros.**

**Tres detalles de los hechos:**

- `tasks.barra_inicial_control.*` sólo existe para 9 estrategias. En F la barra inicial dio un único resultado en las 200 re-ejecuciones y el estudio no dibuja una distribución de un solo punto.
- **El control no es un control limpio en todas.** En C, la barra inicial sola baja la mediana a 10.084 USD desde 13.239 (retención 0,76): sus re-ejecuciones tienen 188 operaciones en vez de 189 y un 24 % menos de beneficio. En `19.2.363` la mediana de la barra inicial es 1,67 veces el original. Para esas dos, «el ruido de fondo» no es pequeño.
- **En salidas hay de 6 a 28 resultados distintos entre 500**; en barra inicial, de 1 a 83 entre 200. Un p5 sobre 16 valores distintos es un escalón, no un percentil fino: en E, el p5 de salidas y el extremo bajo de su intervalo son el mismo número (11.900,45).

### 3.2 La tabla «tarea a tarea»

`mcRetest.levels.beneficio_p5_y_drawdown_cvar_tarea_a_tarea.<tarea>.backtest_original_usd` · `.beneficio_p5_usd` · `.mediana_monte_carlo_usd` · `.drawdown_cvar`

Los mismos cuatro números están guardados otra vez, idénticos, como `mcRetest.tasks.que_hizo_cada_tarea.<tarea>.*`.

**Qué mide.** Un resumen de cuatro columnas por tarea: el original, el p5, la mediana y el CVaR del drawdown. Las tres primeras repiten `tasks.<tarea>.real`, `.p5` y `.median`. Lo único nuevo es el **CVaR del drawdown de cada tarea**, no sólo el del estrés.

**Cómo se calcula.** El CVaR, como en el apartado 2.8 (`verdict/fragility.py`, líneas 57 a 75): media de los drawdowns (en %) que están en el percentil 95 o por encima.

**Ejemplo, E** (guardado; el del estrés y el de spread, recalculados):

| tarea | CVaR del drawdown (%) |
|---|---|
| original del build | 5,24 |
| barra inicial | 5,24 |
| histórico | 5,22 |
| slippage | 5,50 |
| spread | 5,61 |
| salidas | 6,30 |
| parámetros | 10,99 |
| estrés | 16,16 |

**Cómo leerlo.** Compáralo con el drawdown del original (5,24 % en el build; 5,61 % en el estrés). El coste casi no mueve la cola del drawdown de E; los parámetros la doblan; el estrés la triplica. En la población, la mediana del CVaR por tarea: barra inicial 6,5 %; histórico 5,8 %; slippage 5,9 %; spread 6,0 %; salidas 8,6 %; parámetros 15,7 %; estrés 23,3 %.

### 3.3 La tabla que guardó SQX

`mcRetest.levels.la_tabla_que_sqx_guardo_niveles_90_95_99.<tarea>.90` · `.95` · `.99`, cada uno cuatro veces: sin sufijo, `#2`, `#3` y `#4`

**Qué mide.** SQX, al acabar cada tarea, guarda su propia tabla de «niveles de confianza». El estudio la copia tal cual para poder compararla con lo que él recalcula. Cada tarea tiene cuatro filas con el mismo nombre de tarea, y por eso el recolector les pone sufijo. El orden es:

| sufijo | métrica |
|---|---|
| (ninguno) | drawdown en % |
| `#2` | beneficio neto |
| `#3` | número de operaciones |
| `#4` | profit factor |

**Cómo se calcula.** Lo calcula SQX, no el estudio. «Nivel 95» quiere decir: *el 95 % de las re-ejecuciones salió igual o mejor que esto*. Para el neto, el PF y las operaciones es el percentil 5; para el drawdown, el percentil 95. SQX toma una re-ejecución concreta de la lista ordenada, sin interpolar, y redondea el PF a dos decimales.

**Ejemplo, E, estrés** (guardado):

| nivel | drawdown % | neto | operaciones | PF |
|---|---|---|---|---|
| 90 | 11,44 | 11.338,1 | 122 | 1,13 |
| 95 | 12,83 | 7.604,5 | 110 | 1,08 |
| 99 | 17,91 | −2.267,3 | 91 | 0,98 |

El neto del nivel 95 de SQX, 7.604,5, es la 26.ª peor re-ejecución (7.604,35 al recalcular). El p5 del estudio, 7.592,81, es el interpolado entre la 25.ª y la 26.ª. Las dos cifras dicen lo mismo con 12 USD de diferencia.

**Cómo leerlo.** Sirve de comprobación cruzada, y para ver de un vistazo lo que SQX enseña en pantalla. **La trampa es leer una fila como un escenario**: «con un 95 % de confianza ganaré 7.604 con 110 operaciones, PF 1,08 y drawdown del 12,83 %» es falso. Son cuatro percentiles sacados cada uno de su columna; no hay ninguna re-ejecución que tenga los cuatro.

`datos_historicos` sólo tiene estos hechos para 8 estrategias: en las dos en que SQX guardó 499 re-ejecuciones en vez de 500 la tabla se da por corrupta y no se copia.

En la población, el PF del nivel 95 del estrés (`…estres_combinado.95#4`) tiene mediana 0,94 y va de 0,71 a 1,15: el mismo dibujo que el hecho de la regla, con dos decimales.

### 3.4 La distribución del estrés

`mcRetest.stress.estres_combinado_500_re_ejecuciones.real` · `.median` · `.p1` … `.p99`

**Qué mide.** Lo mismo que `tasks.estres_combinado.*`, guardado otra vez desde la pestaña del estrés. Son once hechos duplicados.

**Ejemplo, E** (recalculado, coincide):

| | USD |
|---|---|
| `real` (original, build..oos1 a coste de oos1) | 39.364,0 |
| `p1` | −2.272,5 |
| `p5` | 7.592,8 |
| `p25` | 17.680,5 |
| `p50` | 23.579,5 |
| `p75` | 30.114,4 |
| `p95` | 39.758,0 |
| `p99` | 48.590,8 |

**Cómo leerlo.** Fíjate en dónde cae el original: 39.364 está casi en el p95 (39.758). **El original de E es mejor que el 94,6 % de sus propias re-ejecuciones de estrés.** No es que el backtest fuera una carambola: es que el estrés, por construcción, casi siempre empeora (cuesta más, y los parámetros movidos rara vez mejoran un óptimo). En la población, el original está por encima de entre el 55,6 % y el 94,6 % de sus re-ejecuciones.

Población: `real` de 2.252 a 72.228 USD (mediana 24.634); `median` de −11.424 a 56.246 (mediana 16.671); `p5` de −38.185 a 31.418 (mediana −5.337).

### 3.5 La cola del estrés

Es la tabla de donde sale el hecho de la regla. Nueve hechos.

**3.5.1 El beneficio p5 y su intervalo**

`mcRetest.stress.la_cola.beneficio_p5.valor` · `.intervalo_95_desde` · `.hasta`

- **Qué mide.** El beneficio neto del mundo malo (p5) bajo estrés, con el intervalo del apartado 2.4.
- **Cómo se calcula.** `verdict/fragility.py`, líneas 7 a 36, sobre el neto de las 500 re-ejecuciones.
- **Ejemplo, E.** La 25.ª peor gana 7.373,45 y la 26.ª, 7.604,35: `7.373,45 + 0,95 × 230,90 = 7.592,81`. La 17.ª peor, 5.564,22; la 36.ª, 9.606,12. Guardado: 7.592,81 [5.564,22 · 9.606,12]. Coincide. Para C: −8.504,37 [−10.642,2 · −7.010,39]. Para F: −38.184,6 [−41.652,9 · −35.361,8].
- **Cómo leerlo.** Positivo: incluso el mundo malo gana. En USD de una cuenta de 100.000 con 1R = 1.000. Población: p5 −32.812 · mediana −5.337 · p95 +20.715. Seis de diez lo tienen negativo.

**3.5.2 El profit factor p5 y su intervalo** — el hecho de la regla

`mcRetest.stress.la_cola.profit_factor_p5.valor` · `.intervalo_95_desde` · `.hasta`

- **Qué mide.** El profit factor del mundo malo bajo estrés.
- **Cómo se calcula.** Igual, sobre el PF de las 500 re-ejecuciones. El PF de cada una es `G / L` de sus propias operaciones.
- **Ejemplo.** E: 1,0807 [1,0457 · 1,1040] (apartados 2.3 y 2.4). C: la 25.ª y la 26.ª valen 0,8430 y 0,8458 → `0,8430 + 0,95 × 0,0028 = 0,8456`; intervalo [0,8180 · 0,8638]; 149 de 500 por debajo de 1. F: 0,7057 [0,6795 · 0,7144]; 381 por debajo de 1.
- **Cómo leerlo.** ≥ 1: el 95 % de los mundos gana (apartado 2.6). El número en sí dice **por cuánto**: 1,08 es «en el mundo malo, 1,08 USD ganados por cada USD perdido». Población: p5 0,739 · mediana **0,943** · p95 1,121. El extremo bajo del intervalo: 0,718 · 0,932 · 1,095. El alto: 0,752 · 0,968 · 1,143. El ancho del intervalo va de 0,032 a 0,058.

**3.5.3 El CVaR del drawdown**

`mcRetest.stress.la_cola.drawdown_cvar.valor`

- **Qué mide.** La media de los 25 peores drawdowns (en %) de las 500 re-ejecuciones.
- **Cómo se calcula.** Apartado 2.8.
- **Ejemplo.** E: borde (p95) 12,85 %, 25 re-ejecuciones en la cola, media **16,16 %**. C: borde 14,52 %, CVaR 18,35 %. F: borde 46,11 %; los 25 peores van del 46,5 % al 65,9 %; media **52,26 %**.
- **Cómo leerlo.** Es la peor caída de los doce años, promediada sobre el 5 % de mundos peores. No es una pérdida diaria, con el tamaño de posición del backtest (1 % por R). El veto del estudio salta por encima del 25 %. Población: p5 15,7 % · mediana **23,3 %** · p95 50,6 %. Cuatro de diez superan el 25 % (`18.5.355` con 26,2 %; `13.3.390` con 32,4 %; `16.5.352` con 48,7 %; F con 52,3 %).

**3.5.4 Las operaciones bajo el agua**

`mcRetest.stress.la_cola.operaciones_bajo_el_agua.valor`

- **Qué mide.** Qué parte del tiempo, contado en operaciones, pasa la estrategia por debajo de su máximo anterior.
- **Cómo se calcula** (`verdict/fragility.py`, líneas 78 a 94). En cada re-ejecución: se acumula el resultado operación a operación; se lleva el máximo alcanzado hasta ese momento (que nunca baja de cero); se cuenta la fracción de operaciones tras las que la cuenta queda por debajo de ese máximo. El hecho es la **mediana** de esa fracción entre las 500.
- **Ejemplo ilustrativo.** Cinco operaciones: +100, −50, +30, +40, −10. Acumulado: 100, 50, 80, 120, 110. Máximo hasta el momento: 100, 100, 100, 120, 120. ¿Por debajo? no, sí, sí, no, sí. Bajo el agua: 3 de 5 = 0,60.
- **Ejemplo real.** E: 0,818 (recalculado desde las operaciones de las 500 re-ejecuciones: 0,8184; entre ellas va de 0,62 a 1,00). C: 0,952. F: 0,976.
- **Cómo leerlo.** Alto no es malo por sí solo: una estrategia que gana con pocas operaciones grandes pasa casi todo el tiempo esperando el siguiente máximo. Lo que dice es **qué vas a ver**: con E, tras cuatro de cada cinco operaciones la cuenta estará por debajo de su pico. Población: p5 0,81 · mediana **0,90** · p95 0,97. No tiene línea en ningún sitio.

**3.5.5 La proporción de re-ejecuciones rentables**

`mcRetest.stress.la_cola.p_beneficio_0.valor`

- **Qué mide.** La fracción de las 500 re-ejecuciones del estrés que acaban con beneficio neto mayor que cero. El primer informe dejaba esta lectura como «no comprobada»: **está confirmada en el código.**
- **Cómo se calcula.** `positive_share = media de (NetProfit > 0)` (`verdict/fragility.py`, líneas 127 a 144).
- **Ejemplo.** `10.11.484`: 498 de 500 → **0,996**. E: 492 de 500 → 0,984 (las ocho que pierden van de −9.855 a −334 USD). C: 351 de 500 → 0,702. F: 119 de 500 → 0,238.
- **Cómo leerlo.** Es el número más fácil de explicar de toda la tabla, y es **la misma información que la regla**: PF p5 ≥ 1 ⇔ este hecho ≥ 0,95, aproximadamente (apartado 2.6). Población: p5 0,28 · mediana **0,86** · p95 1,00.
- **Aviso.** En el código de hoy la fila se llama «Simulaciones rentables (%)» y va en porcentaje (99,6 en vez de 0,996). Cuando el piloto vuelva a recoger hechos, esta clave tendrá otro nombre y otra escala (apartado 5.6).

### 3.6 La clasificación del coste: qué tarea hace el daño

`mcRetest.cost.la_clasificacion.<tarea>.coste_usd` · `.sigmas_del_control` · `.dispersion_vs_control`

Seis tareas (todas menos el control), tres hechos cada una.

**Qué mide.** Cuánto beneficio cuesta cada perturbación, medido contra el ruido de fondo del control.

**Cómo se calcula** (`verdict/attribution.py`):

```
σ control            = desviación del neto entre las 200 re-ejecuciones de barra inicial
coste_usd            = mediana(control) − mediana(tarea)
sigmas_del_control   = coste_usd / σ control
dispersion_vs_control = desviación(tarea) / σ control
```

El estudio da por «real» un coste de 1 sigma o más (`attribution.min_control_sigma: 1.0`).

**Ejemplo, E.** σ control = 392 USD; mediana del control = 23.576,2.

| tarea | mediana | coste (USD) | en sigmas |
|---|---|---|---|
| parámetros | 15.564,5 | 8.011,7 | 20,4 |
| salidas | 19.831,9 | 3.744,2 | 9,6 |
| spread | 21.968,9 | 1.607,3 | 4,1 |
| slippage | 21.990,1 | 1.586,0 | 4,0 |
| histórico | 23.388,5 | 187,7 | 0,5 |
| estrés | 23.579,5 | −3,3 | −0,0 |

Comprobación de la primera fila: `23.576,2 − 15.564,5 = 8.011,7`; `8.011,7 / 392 = 20,4`. Coincide.

**Cómo leerlo.** La tabla ordena las causas: a E le duelen sus propios parámetros cinco veces más que el coste, y el histórico no le hace nada. Es la lectura más útil del estudio para **entender** una estrategia. Pero tiene cuatro trampas, y por eso no sirve de criterio:

1. **La fila del estrés no significa nada.** El control es del build (22.508 de original); el estrés es de otra ventana (39.364 de original). Restar sus medianas mezcla dos backtests. Que en E salga −3,3 es casualidad.
2. **Si el control casi no se mueve, las sigmas estallan.** En `10.11.484` la σ del control es de 51 USD: el spread «cuesta» 24 sigmas y el estrés tiene una dispersión de 190 veces el control. No es que sea frágil: es que el denominador es casi cero.
3. **Si el control desplaza la mediana, los costes salen negativos.** En C la mediana del control (10.084) queda muy por debajo del original, y todas las demás tareas «ganan» respecto a él: spread −2.172, slippage −2.360, salidas −4.210.
4. **Si el control no se mueve nada, no hay sigmas.** En F la σ es cero: `sigmas_del_control` y `dispersion_vs_control` no existen (por eso esos hechos sólo están para 9 estrategias).

Población, `sigmas_del_control` (mediana de las 9): parámetros 6,7; spread 2,4; slippage 1,6; estrés 1,3; salidas 1,3; histórico −1,3. Con las trampas de arriba, tómalo como orden de magnitud.

### 3.7 El veredicto del estudio

**3.7.1 Las cuatro notas y la compuesta**

`mcRetest.verdict.production` · `.execution` · `.specification` · `.data` · `.score` · `.pass`

- **Qué miden y cómo se calculan.** Apartado 2.9. `score` es la nota compuesta. `pass` vale 1 sólo si el veredicto del estudio es `STRONG` o `ACCEPTABLE` (nota ≥ 65 y ningún veto).
- **Ejemplo** (los cuatro, recalculados con el código del estudio; coinciden):

| | C | E | F | `10.11.484` |
|---|---|---|---|---|
| `production` | 0 | 38,58 | 0 | 45,74 |
| `execution` | 3,88 | 60,57 | 0 | 49,98 |
| `specification` | 17,02 | 26,29 | 0 | 45,43 |
| `data` | 89,83 | 97,55 | 0 | 97,66 |
| `score` | 8,7 | 43,5 | 0 | 49,1 |

  Las cuentas de E: producción `100 × 7.592,81 / (0,5 × 39.364,02) = 38,58` (las otras dos curvas dan 44,2 y 93,6); ejecución `100 × (0,8817 − 0,70) / 0,30 = 60,57`; especificación = retención de parámetros, 26,29; datos 97,55; compuesta `0,55 × 38,58 + 0,20 × 60,57 + 0,20 × 26,29 + 0,05 × 97,55 = 43,5`. Las de C: producción 0 porque su p5 del estrés es negativo; ejecución `100 × (0,7116 − 0,70) / 0,30 = 3,88`, es decir, a un pelo del veto de 0,70.
- **Cómo leerlo.** Cada nota dice de qué lado cojea: E cojea de especificación (parámetros); C, de producción y de ejecución. Población (p5 · mediana · p95): producción 0 · **0** · 42,5; ejecución 0 · **46,3** · 74,0; especificación 0 · **25,3** · 47,6; datos 9,9 · **90,2** · 97,8; compuesta 0,5 · **20,5** · 50,0. `pass`: 0 en las diez.

  Un detalle de `execution`: vale más que cero exactamente cuando la retención de spread y de slippage supera 0,70. No hay hecho que diga si supera 0,5.

**3.7.2 Qué saltó**

`mcRetest.verdict.que_salto.veto.midio` · `.veto.contra` (y `#2` … `#6`) · `.aviso.midio` · `.aviso.contra` (y `#2` … `#4`)

- **Qué mide.** La lista de vetos y avisos que saltaron para esa estrategia: lo que se midió y la línea contra la que se midió.
- **Cómo se calcula.** `verdict/gates.py`; primero los vetos, luego los avisos. Como todas las filas se llaman «veto» o «aviso», el recolector numera las repetidas.
- **Ejemplo.** E: un solo veto, `midio` = 1,0807 contra 1,1 (PF p5). C: tres vetos: −8.504,37 contra 0 (beneficio p5); 0,8456 contra 1,1 (PF p5); 0,646 contra 0,9 (Sharpe frente al azar). F: seis vetos (beneficio p5, PF p5, CVaR 52,26 contra 25, Sharpe 0,156 contra 0,9, ejecución −0,467 contra 0,7, parámetros −15.431,7 contra 0) y cuatro avisos (histórico, salidas, un único resultado en la barra inicial, 499 re-ejecuciones contra 500).
- **Cómo leerlo.** **No se puede leer como hecho comparable.** `veto.midio` es «lo que midió el primer veto que saltó», y el primer veto no es el mismo en todas: en E es un profit factor (1,08) y en C es un beneficio en USD (−8.504). Una mediana de población de ese hecho mezcla peras con manzanas. Sirve para leer una estrategia, no para escribir una regla. Nueve de diez tienen al menos un veto; la décima, `4.13.338`, sólo un aviso de datos.

### 3.8 El resumen y el CSV

`mcRetest.summary.composite` · `.stress_net_p5` · `.stress_cvar_dd_pct` — y los mismos en `mcRetest.verdict_csv.*`, más `mcRetest.verdict_csv.drop`

- **Qué miden.** Tres números ya vistos (la nota compuesta, el beneficio p5 del estrés y el CVaR del drawdown), guardados dos veces más: una desde el resumen del JSON y otra desde `verdict.csv`.
- **`verdict_csv.drop`** vale 1 cuando el CSV del estudio dice literalmente `DESCARTAR`. Este estudio escribe `FAIL`, no `DESCARTAR`, así que **vale 0 siempre**, también para las nueve que el estudio suspende. No lo uses.

### 3.9 Lo que el estudio calcula y no llega a los hechos

Está en la carpeta del estudio (`AlgoData/reports/<proyecto>/MCR_All/2026-10-04/mcRetest/`), no en `hechos.parquet`:

- **El veredicto en palabras** (`verdict.csv`, columna `verdict`): 9 `FAIL` y 1 `INCONCLUSIVE`. Y qué nota es la que más aprieta (`binding`).
- **La evidencia frente al azar.** Dos números. *(a)* La proporción de re-ejecuciones del estrés cuyo Sharpe por operación (`media / desviación`) supera el de un operador al azar con la misma huella (entre 0,007 y 0,018 para estas diez): E 0,968; `10.11.484` 0,976; C 0,646; F 0,156. No es `p_beneficio_0`: aquella cuenta las que ganan; ésta, las que ganan más que el azar. *(b)* El PSR de las operaciones de `oos1` del original: la probabilidad de que su Sharpe verdadero supere al del azar, corregida por asimetría y colas. E 0,985 (92 operaciones); `10.11.484` 0,966 (106); C 0,788 (98); F 0,638 (167). El veto `edge_indistinguible_de_cero` salta si **las dos** quedan por debajo de 0,90.
- **Los modos.** Cuántos resultados distintos dio cada tarea, si la tarea «discrimina» (al menos el 30 % de resultados distintos) y una prueba de si la distribución tiene dos jorobas (la prueba «dip» de Hartigan). Dos jorobas querría decir que hay dos regímenes: uno en el que la estrategia funciona y otro en el que no.
- **Los contrastes entre tareas**, con la delta de Cliff: la fracción de pares (una re-ejecución de A, una de B) en que A gana más, menos la fracción en que gana menos; va de −1 a +1. En E, histórico contra parámetros da +0,82: en nueve de cada diez pares la re-ejecución con el histórico movido gana más que la de parámetros movidos. Slippage contra spread, +0,02: le dan igual.
- **Dónde cae el original entre sus re-ejecuciones** (tres columnas de `verdict.csv`, añadidas después de recoger los hechos): `percentil_original_estres` (E: 94,6), `brecha_mediana_pct_estres` (E: −40,1 %, la mediana queda un 40 % por debajo del original) y `distancia_IQR_estres` (E: 1,27). El propio código las llama «métricas para criterios — sin umbral todavía».

---

## 4. El criterio cargado y por qué

### 4.1 Tal como está hoy en disco

```
"14":
  cut: MCR 8 Stress
  segment: oos1
  rules:
    # Council: kill-only. Surviving this is not evidence, only "not dead".
    - {fact: mcRetest.stress.la_cola.profit_factor_p5.valor, pass: ">= 1.0"}
```

Una regla. Sin línea `limbo`, sin `missing`. El comentario de cabecera del fichero añade que el paso 14 corta `MCR 8 Stress`, «el único de los ocho databanks de MCR que lee el SPP; los otros siete conservan a todas», y que todo es provisional hasta que una población nula haya recorrido la cadena.

### 4.2 La regla — PF p5 del estrés ≥ 1,0

| | línea | qué significa |
|---|---|---|
| **Pasa** | ≥ 1,0 | al menos el 95 % de las 500 re-ejecuciones del estrés gana |
| **Limbo** | — | sólo si el hecho falta |
| **Falla** | < 1,0 | más del 5 % pierde |

**La razón.**

- *De dónde sale la forma («sólo mata», sin Limbo):* del Council, cuatro de cinco (apartado 2.10).
- *De dónde sale el 1,0:* es el punto de equilibrio. Munger y Kahneman lo propusieron así («Falla si el PF bajo estrés es menor que 1»). **Convención**, no medida.
- *De dónde sale el percentil 5:* de ningún sitio escrito. El Council dijo «PF bajo estrés < 1»; no dijo de qué percentil. Kahneman habló de «menos del 50 % de las perturbaciones rentables», que sería la **mediana** del PF por debajo de 1; Karpathy, de la mediana ≥ 0,7 veces el nominal (y lo retiró). Leer el p5 es la interpretación más dura de las posibles: con la mediana fallarían dos de diez (F y `19.2.363`); con el p5 fallan seis.
- *Tasa de falsos positivos medida:* **no medida.** *Potencia medida:* **no medida.**

### 4.3 Lo que no está cargado

- **La segunda muerte del Council:** retención bajo la peor ejecución < 0,5. Se puede calcular (`tasks.spread.p5 / tasks.spread.real` y lo mismo con slippage) pero no hay un hecho con ese cociente, y `verdict.execution` corta en 0,70, no en 0,5.
- **Una banda de Limbo.** No hay.
- **El veredicto del estudio.** No se lee. Si se leyera (`verdict.pass`), fallarían las diez.
- **Nada del drawdown.** El CVaR existe como hecho y no tiene regla. Es coherente con que el drawdown, aquí, es una cuestión de tamaño de posición más que de vida o muerte (apartado 2.8).

### 4.4 Cómo sería el resultado ideal

Una estrategia que deja este paso sin dudas tendría, en la tabla de la cola del estrés:

- **PF p5 por encima de 1 con el intervalo entero por encima de 1** (`intervalo_95_desde` ≥ 1,0): la 17.ª peor de 500 ya gana, es decir, 16 perdedoras o menos, el 96,8 % o más rentables. Así el «Pasa» no depende del sorteo de SQX.
- **`p_beneficio_0` de 0,97 o más.**
- **Retención de spread y de slippage de 0,85 o más**, y de parámetros positiva y sin que la mediana se hunda.
- **p95 del drawdown del estrés por debajo de lo que cabe en tu cuenta con tu riesgo por R.** En esta población va de 2,1 a 4,9 veces el del original y la mejor tiene 2,66: no fijes 2,5× como línea, porque nadie lo cumple con holgura.

**El techo honrado.** La mejor de estas diez, `4.13.338` (PF del original 1,67; t de 3,25): PF p5 1,154; 100 % rentables; retención p5 del estrés **0,43**; retención mediana 0,78; p95 del drawdown 2,66 veces el original. Ninguna de las diez conserva la mitad del beneficio en el p5 del estrés, y ninguna conserva la mitad en el p5 de parámetros. Pedir «retención del estrés ≥ 0,5» sería pedir algo que aquí no ha hecho nadie. Y aun el resultado ideal sólo prueba una cosa: que la estrategia **no es frágil a estas perturbaciones**. No prueba que tenga ventaja; eso lo dicen las muestras nuevas (pasos 8, 10-12 y 20).

### 4.5 Si mueves este umbral

**La línea del PF p5** (recuento sobre las diez):

| línea | fallan | quién cambia respecto a 1,0 |
|---|---|---|
| ≥ 0,80 | 2 | se salvan C, `13.3.390`, `16.5.352`, `3.9.284` |
| ≥ 0,90 | 4 | se salvan `13.3.390` y `3.9.284` |
| ≥ 0,95 | 5 | se salva `3.9.284` |
| **≥ 1,00** | **6** | — |
| ≥ 1,05 | 6 | ninguna |
| ≥ 1,10 | 9 | mueren además E, `10.11.484`, `18.5.355` |

Entre 1,00 y 1,05 no hay nadie: la línea de hoy cae en un hueco de la población (0,984 por debajo; 1,053 por encima). Subirla al 1,10 del estudio cuesta tres de las cuatro que pasan.

**Usar el intervalo en vez del punto:**

| variante | pasan | limbo | fallan |
|---|---|---|---|
| hoy: el punto ≥ 1,0 | 4 | 0 | 6 |
| Falla sólo si `hasta` < 1,0 | 5 | 0 | 5 |
| Pasa si `intervalo_95_desde` ≥ 1,0; Falla si `hasta` < 1,0; Limbo entre medias | 4 | 1 | 5 |
| Pasa ≥ 1,0; Limbo de 0,9 a 1,0 | 4 | 2 | 4 |

La única estrategia cuyo intervalo cruza el 1 es `3.9.284` (0,975 a 1,011). Las cuatro que pasan tienen el extremo bajo por encima de 1 (el más justo, `18.5.355` con 1,035), y las otras cinco que fallan tienen el extremo alto por debajo (el más cercano, `13.3.390` con 0,926). **En esta población el ruido de las 500 tiradas decide una sola estrategia.**

**Cambiar de medida, a la proporción de rentables** (`p_beneficio_0`):

| línea | fallan | quiénes |
|---|---|---|
| ≥ 0,95 | 6 | las mismas que hoy |
| ≥ 0,90 | 5 | se salva `3.9.284` |
| ≥ 0,70 (Kaufman) | 3 | F, `19.2.363`, `16.5.352` |
| ≥ 0,50 (Kahneman) | 2 | F, `19.2.363` |

**Añadir la segunda muerte del Council** (retención de ejecución < 0,5): mataría a F (−0,47), `19.2.363` (0,00) y `16.5.352` (0,47). Las tres ya mueren por la regla de hoy: **coste añadido, cero; ganancia añadida en esta población, cero.** Con la línea del estudio (0,70) son las mismas tres; C se queda en 0,71.

**Cambiar de tarea.** Si en vez del estrés se leyera la peor de las tareas aisladas (PF p5 ≥ 1,0 en todas), fallarían tres (F, `19.2.363`, `16.5.352`) y se salvarían C, `13.3.390` y `3.9.284`.

**Lo que ninguna de estas tablas dice** es cuál de las líneas es mejor. Dicen cuántas mata cada una de diez estrategias sorteadas. Para elegir hace falta saber cuántas de las muertas tenían ventaja y cuántas de las vivas no, y eso no está medido.

---

## 5. Lo que no cuadra o no está medido

### 5.1 Tres líneas distintas para la misma medida

El PF p5 del estrés tiene tres umbrales según dónde mires: **1,0** en `criteria.yaml`; **1,10** en el veto del estudio (`gates.min_pf`); y «PF bajo estrés < 1» sin percentil en el Council. Con la primera pasan cuatro; con la segunda, una (y esa una queda `INCONCLUSIVE`). El hecho `verdict.pass` vale 0 para las cuatro que el criterio aprueba. Quien mire la ventana del estudio verá `FAIL` en estrategias que el piloto deja pasar.

### 5.2 La segunda muerte del Council no está cargada ni hay hecho para cargarla

«Retención bajo la peor ejecución < 0,5» está en el acta y no en el fichero. El estudio corta en 0,70 y sólo expone la nota (`verdict.execution`), que es 0 por debajo de 0,70 y no distingue 0,69 de 0,2.

### 5.3 `segment: oos1` no describe lo que se lee

El hecho de la regla sale de `build..oos1` (doce años) cobrado a coste de `oos1`. Las tareas 1 a 7 son sólo del build. Nada en este paso se calcula sobre `oos1` solo, salvo el PSR de apoyo.

### 5.4 «Ocho tareas» y «seis perturbaciones»

El catálogo define ocho tareas y la tarea 8 con seis métodos. En la corrida hubo siete tareas (sin MCR 4) y cinco métodos en el estrés: spread, slippage, parámetros, salidas e histórico. Faltan la distancia mínima (correcto: órdenes a mercado) **y la barra inicial**, que el glosario del estudio (`one.py`) sí nombra entre las del estrés. El estrés, además, mueve las salidas ±15 %, no el ±30 % de la tarea 6: la tarea 6 es más dura con las salidas que el estrés.

### 5.5 El estrés mide sobre todo el coste, y su original no es el del build

Tres cosas se suman en la tarea 8 y no se pueden separar: la ventana más larga, el coste de `oos1` (1,56 veces el del build) aplicado también a los años del build, y el sorteo de 0,5 a 2 veces sobre ese coste. Si el sorteo fuera uniforme, el spread medio del estrés sería unas 1,95 veces el del build (1,56 × 1,25). Es una decisión defendible («al mundo que tiene que sorprendernos no se le da el precio barato»), pero conviene saber que **la regla cargada es, en gran parte, una prueba de coste doble**. Cuánto del daño es coste y cuánto es parámetros: **no medido** (haría falta un estrés sin coste, o un estrés con el coste del build).

### 5.6 Los hechos guardados son más viejos que el estudio

`hechos.parquet` es de las 16:38 del 2026-10-04; la carpeta del estudio se reescribió a las 22:14 con código más nuevo. Consecuencias:

- `stress.la_cola.p_beneficio_0.valor` (fracción) hoy se llamaría de otra forma, por «Simulaciones rentables (%)», y vendría en porcentaje. Una regla escrita sobre el nombre viejo quedaría en Limbo para todas (dato ausente).
- Las tres columnas nuevas de `verdict.csv` (`percentil_original_estres`, `brecha_mediana_pct_estres`, `distancia_IQR_estres`) no están en los hechos.
- El hecho de la regla, `profit_factor_p5.valor`, no ha cambiado de nombre.

### 5.7 Hechos duplicados y hechos que no sirven

- `tasks.que_hizo_cada_tarea.*` es copia de `levels.beneficio_p5_y_drawdown_cvar_tarea_a_tarea.*` (28 hechos).
- `stress.estres_combinado_500_re_ejecuciones.*` es copia de `tasks.estres_combinado.*` (11).
- `summary.*` es copia de `verdict_csv.*` (3); `.median` es copia de `.p50` en cada distribución (8).
- `verdict_csv.drop` vale 0 siempre en este estudio (apartado 3.8).
- `verdict.que_salto.*` no es comparable entre estrategias (apartado 3.7.2).
- Los hechos con `#2`, `#3`, `#4` dependen del orden de las filas de una tabla: si el estudio cambia el orden, cambian de significado sin cambiar de nombre.

### 5.8 El control no siempre es un control

En F da un único resultado (el aviso `tarea_sin_dispersion`); en `10.11.484` casi no se mueve (σ de 51 USD) y las sigmas del coste se disparan; en C quita un 24 % del beneficio él solo; en `19.2.363` la mediana es 1,67 veces el original. La tabla de costes en sigmas (apartado 3.6) hereda los cuatro problemas, y su fila del estrés compara dos ventanas distintas.

### 5.9 La tarea de salidas es una rejilla, no 500 pruebas

De 6 a 28 resultados distintos entre 500. Sus percentiles y su intervalo son escalones.

### 5.10 La precisión del catálogo no es la de la corrida

La corrida usó datos de un minuto en spread, slippage, salidas, histórico y estrés. El `assets/_build.yaml` que hay hoy en el árbol de trabajo (sin confirmar en git) pone `precision: 1` (timeframe elegido) en todas, y conserva un comentario que dice «un minuto — lento y fino». La próxima corrida no será comparable con ésta en esas cinco tareas si eso se queda así. Si es intencionado, el comentario sobra; si no, es un cambio a medias.

### 5.11 El README del estudio

Dice que el estudio corre «después de que la estrategia haya sido aceptada». En el workflow corre en el paso 14 de 26, antes del SPP, del WFM y de `oos2`.

### 5.12 La población no es la que llegaría

Diez estrategias de un sorteo, que hoy fallan el paso 8 y el paso 10. Sólo cinco tienen una t ≥ 1,65 en el original del estrés. No existe ninguna corrida del paso 14 sobre estrategias que hayan pasado los pasos anteriores con las reglas de hoy.

### 5.13 El paso no juzgó en la corrida real

El 2026-10-04 no tenía regla. Nada se borró de `MCR 8 Stress`: las diez siguieron al SPP.

### 5.14 Lo que no está medido

- La tasa de falsos positivos del paso (cuántas sin ventaja sobreviven). No hay población nula hasta aquí.
- La potencia (cuántas con ventaja real mueren).
- Cuánto del daño del estrés es coste y cuánto es parámetros.
- Cómo sortea SQX dentro del rango de spread y de slippage (uniforme o no; por re-ejecución o por operación).
- La unidad del `MaxChange` de la tarea de histórico la he tomado de cómo la define SQX (porcentaje del ATR); no la he comprobado contra el código de SQX.
- Si 500 re-ejecuciones bastan: el intervalo dice que el p5 baila entre la 17.ª y la 36.ª peor; con 1.000 se estrecha poco.
- El cociente de drawdown bajo estrés (mediana 2,64) está medido sobre diez estrategias sorteadas, no sobre supervivientes.

### 5.15 Dónde este documento corrige al informe anterior y al encargo

- El informe del 2026-10-06 dice «ocho tareas» y «las seis perturbaciones a la vez»: corrieron siete, y el estrés combina cinco.
- Daba la lectura de `p_beneficio_0` como «no comprobada»: es la proporción de re-ejecuciones del estrés con neto mayor que cero, confirmado en el código y recalculado.
- «Cuatro tienen el PF p5 en 1,0 o más y seis no»: correcto.
- El argumento «70 % ⇔ t ≥ 0,52; lo que llega tiene Φ ≈ 95 %» es exacto para el **remuestreo** (comprobado) y no describe las re-ejecuciones del MC Retest: en las tareas de coste una estrategia con t de 0,23 supera el 70 %, y en el estrés una con t de 1,38 se queda en el 70 % justo (apartado 2.7).
- El 1,95 del drawdown es de **barajar** operaciones; bajo estrés el cociente es mayor (2,1 a 4,9).

---

## 6. Cierre

### 6.1 La regla, en una tabla

`mcRetest.stress.la_cola.profit_factor_p5.valor`

| regla | Pasa | Limbo | Falla | de dónde sale |
|---|---|---|---|---|
| PF p5 del estrés | ≥ 1,0 | sin dato | < 1,0 | Council (sólo mata) y convención |

### 6.2 El resultado sobre la población real

Calculado en memoria con `pipeline.autopilot.criteria.outcomes` sobre los hechos del 2026-10-04: **4 Pasa · 0 Limbo · 6 Falla.**

| estrategia | PF p5 | intervalo | regla | estudio (nota) |
|---|---|---|---|---|
| `4.13.338` | 1,154 | 1,135 – 1,174 | Pasa | INCONCLUSIVE (50,7) |
| E `3.11.426` | 1,081 | 1,046 – 1,104 | Pasa | FAIL (43,5) |
| `10.11.484` | 1,069 | 1,045 – 1,092 | Pasa | FAIL (49,1) |
| `18.5.355` | 1,053 | 1,035 – 1,072 | Pasa | FAIL (24,3) |
| `3.9.284` | 0,984 | 0,975 – 1,011 | Falla | FAIL (23,4) |
| `13.3.390` | 0,903 | 0,888 – 0,926 | Falla | FAIL (17,6) |
| `16.5.352` | 0,883 | 0,861 – 0,907 | Falla | FAIL (1,1) |
| C `14.3.479` | 0,846 | 0,818 – 0,864 | Falla | FAIL (8,7) |
| `19.2.363` | 0,780 | 0,765 – 0,797 | Falla | FAIL (4,5) |
| F `15.9.352` | 0,706 | 0,679 – 0,714 | Falla | FAIL (0,0) |

Las cuatro que pasan son cuatro de las cinco con t ≥ 1,65 en el original del estrés. La quinta, `3.9.284` (t de 2,15), es la que cae dentro del ruido.

### 6.3 Las decisiones que te quedan

Cada una con su coste en estrategias (sobre estas diez) al lado de lo que gana.

**1. ¿Se queda el PF p5 ≥ 1,0 como única muerte?**
Coste: mata 6 de 10; de las 5 con t ≥ 1,65, mata 1. Gana: es la lectura más simple («el 95 % de los mundos gana») y cae en un hueco de la población, así que moverla un poco no cambia nada. Alternativas: 0,95 (mata 5), 0,90 (mata 4), la línea de Kaufman del 70 % (mata 3), la de Kahneman del 50 % (mata 2). Cuál acierta más: no medido.

**2. ¿Una banda de Limbo para lo que cae dentro del ruido?**
Opción: Falla sólo si el extremo alto del intervalo (`…profit_factor_p5.hasta`) queda por debajo de 1,0. Coste: una estrategia más sigue viva (`3.9.284`), marcada o no. Gana: ninguna muerte depende del sorteo de 500 tiradas. Es el cambio más barato y el único que arregla un defecto concreto.

**3. ¿Se carga la segunda muerte del Council (retención de ejecución < 0,5)?**
Coste hoy: 0 (las tres que mataría ya mueren). Gana hoy: 0. Hace falta antes un hecho con el cociente. Tendría sentido si el estrés se suavizara (decisión 5), porque entonces sería la única prueba de coste dura.

**4. ¿Se alinea el veto del estudio (1,10) con el criterio (1,0), o al revés?**
Si el criterio sube a 1,10: mueren 3 de las 4 que pasan. Si el estudio baja a 1,0: la ventana y el piloto dicen lo mismo. Mientras sigan distintos, verás `FAIL` en pantalla en estrategias que el workflow deja seguir.

**5. ¿El estrés debe seguir cobrando toda la ventana a coste de `oos1` y además sortear hasta el doble?**
Es lo que hace que ninguna de las diez conserve la mitad del beneficio. Coste de suavizarlo: sobrevivirían más (cuántas, no medido: hay que volver a correr el paso 13). Gana: la regla dejaría de ser sobre todo una prueba de coste doble. Coste de dejarlo: puede estar matando ventajas pequeñas pero reales (no medido).

**6. ¿Se corre la población nula por los pasos 13 y 14?**
Coste: CPU del custodio (2.600 re-ejecuciones por estrategia), ninguna estrategia. Gana: los dos números que faltan para poder elegir cualquier línea de las de arriba con fundamento, y la respuesta a si un «Pasa» aquí dice algo.

**7. ¿Qué multiplicador de drawdown usas para dimensionar?**
No es un filtro, pero sale de este paso. Los datos: barajando, mediana 1,9 a 1,95 (el 2× de Hill, Pruitt y Hill); bajo estrés, mediana 2,64 en el p95 y 3,2 en el CVaR (el 3× de Kaufman). Con E: al 1 % por R el p95 del estrés es un 15,7 % de la cuenta; para que quepa en un 10 % hay que bajar a 0,64 % por R.

**8. Lo que hay que arreglar sin decidir nada:** el nombre del hecho `p_beneficio_0` antes de escribir una regla sobre él; la etiqueta `segment: oos1`; `verdict_csv.drop`; el glosario que pone la barra inicial en el estrés; el comentario de la precisión en `_build.yaml`.

### 6.4 El límite que no cambia

El MC Retest no trae ni una operación nueva del mercado. Todo lo que hace es volver a pasar el mismo histórico con las entradas retocadas. Por eso puede decirte que una estrategia es **frágil** —y eso se cree— pero no que **tiene ventaja**. Una estrategia sobreajustada a un periodo favorable, con margen de sobra para pagar el doble de spread y con parámetros en una meseta ancha, pasa este paso limpiamente. La evidencia de que gana de verdad sólo viene de datos que no vio: `oos1` en el paso 8, los otros mercados y timeframes en los pasos 10 a 12, y `oos2` en el 20. Este paso quita lo que se rompe al tocarlo. Nada más, y nada menos.
