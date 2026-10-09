# Paso 25 — Edge por coste, por estrategia: qué se calcula, con qué cuenta y qué criterio hay cargado

**Fecha:** 2026-10-08 · **Para:** el dueño, que va a fijar los criterios él mismo · **Alcance:** sólo el paso 25 (`studies/readings/edgeCost/` leído sobre la versión con stop que deja el paso 24) y lo que el autopiloto hace con él. El paso 8 aparece únicamente para decir qué comparten.

**Qué es:** el documento de consulta del paso 25, con la misma forma que el del paso 16 (`criterios-paso-16-spp-2026-10-07`). Explica desde cero la cuenta, repasa lo que el estudio escribe, cita el umbral cargado y cierra con lo que no cuadra y con las decisiones que te quedan.

**Commit descrito:** `b2b4c8c`. La carpeta del estudio (`studies/readings/edgeCost/`), el repreciado (`engines/market/reprice.py`) y su test (`tests/test_edgecost.py`) **no tienen cambios sin confirmar**. Sí los tienen, y los describo tal como están hoy en disco: `pipeline/autopilot/facts.py`, `pipeline/autopilot/judge.py`, `pipeline/autopilot/README.md`, `ui/daemon/workflow/sources.py`, `ui/daemon/workflow/steps.py`, `ui/daemon/workflow/tests.py` y `.claude/skills/workflow-simple/steps.md`; y otros cinco de `pipeline/autopilot/` (`blind.py`, `plan.py`, `run.py`, `tailrun.py`, `variants.py`) que no tocan el paso 25.

**De dónde salen los números.** De la corrida `Trade_NIKKEI225_M30_volatilidadL` del 2026-10-04 (NIKKEI225, M30, largas, diez madres): su cosecha del paso 25, `AlgoData/harvest/…/Stop_p90/2026-10-04/` (3.331 operaciones de las diez versiones con stop, 1.274 de ellas en `oos1`), y la cosecha de la puerta, `…/Results/2026-10-04/` (las mismas diez madres sin stop). **El código cambió después de esa corrida:** el 2026-10-07 (encargo 44) el estudio se redefinió entero. Por eso hay dos juegos de cifras y los separo siempre:

- **«Lo que la corrida guardó»**: los diez JSON de `AlgoData/reports/…/Stop_p90/2026-10-04/edgeCost/estrategias/`, hechos con la definición vieja.
- **«Con el código de hoy»**: las mismas operaciones pasadas en memoria por `edgeCost.costs.per_trade` y `edgeCost.one.measure` tal como están en el commit. No he escrito nada en `AlgoData` ni he tocado SQX.

Lo que el estudio no calcula —el error de muestreo, la mediana, el reparto del coste, la comparación con y sin stop— lo he calculado yo y va marcado **«calculado por mí»**; los scripts están en la carpeta temporal `scratchpad/paso25/` (`b_recompute.py`, `c_parts.py`). «Juguete» quiere decir cuenta inventada para enseñar, no medida.

**Ninguna línea de este documento está congelada.**

**Revisado por dos miembros del Council (Feynman, Taleb) el 2026-10-08; correcciones aplicadas.** Las cifras marcadas **«calculado por el revisor»** son suyas y las he reproducido con su script (`scratchpad/review/p25t/t.py`): salen de un remuestreo **por semanas enteras** (las 203 semanas de `oos1`, 4.000-5.000 tiradas, semilla 1), con las diez estrategias y las dos versiones —con y sin stop— remuestreadas a la vez, para respetar que operan las mismas semanas.

---

## 0. En una página

**La pregunta del paso.** La versión que de verdad se va a operar —la madre con el stop del paso 24 puesto—, ¿sigue ganando, antes de costes, varias veces lo que paga en costes? O dicho al revés: ¿cuánto puede encarecerse el coste antes de que deje de ganar?

**Lo que hay cargado hoy.** Un umbral de **2,0** con acción **`mark`** (sólo marca, no elimina), en `ledger/thresholds.yaml:198-216`. En `pipeline/autopilot/criteria.yaml` **no hay paso 25**: ninguna regla, ningún corte. El autopiloto calcula el número de cada versión, lo deja en un JSON y pasa todas a la lista de finalistas del paso 26.

**Lo que sale en la corrida real.**

| | por encima de 2 | por debajo de 2 |
|---|---|---|
| lo que la corrida guardó (definición vieja, `build`+`oos1` juntos, en spreads de hoy) | 9 de 10 | 1 |
| con el código de hoy (sólo `oos1`, sobre el coste pagado), versión con stop | **5 de 10** | 5 |
| con el código de hoy, las mismas madres **sin** stop | 9 de 10 | 1 |

**«5 de 10» lleva su propio error, y es grande.** Con otro `oos1` igual de válido habrían salido **entre 2 y 8** por encima de 2 (intervalo del 95 %; sale exactamente 5 en una de cada cuatro tiradas; calculado por el revisor). Y no son diez ensayos independientes: son diez estrategias largas de la misma familia sobre el mismo índice, que comparten el **29 %** de sus barras de entrada. Cada vez que este documento dice «5 de 10», léase «entre 2 y 8».

**Y las diez no se eligieron a ciegas.** Salieron de un sorteo entre las 3.148 que no fallaban el paso 8 aquel día, y **todas** ellas tenían neto positivo en `oos1` (en la población de 10.000, el 59,5 %; calculado por el revisor). Neto positivo es edge mayor que 1: que las madres sin stop lo tengan sale **por construcción**, y todos los edges de este documento están sesgados al alza en una cantidad que no está medida (apartado 5.12).

Dos de las diez versiones con stop **pierden dinero neto en `oos1`** (`13.3.390`: −1.825 USD; `19.2.363`: −2.024 USD). Sin stop ganaban +5.342 y +2.311.

**Las doce cosas que conviene saber antes de leer el resto:**

1. **La fila del paso en `WORKFLOW.md` y el encargo que me diste describen un estudio que ya no existe.** «Bruto reconstruido de `Profit/Loss` + comisión + coste de spread modelado, en spreads de hoy, media y mediana, y `c*`» era la definición hasta el 2026-10-06. Desde el encargo 44 el estudio escribe **un solo número**: `edge = media(P/L + coste) / media(coste)`, sólo `oos1`, con el coste que el repreciado común cobra. **No hay mediana, ni número de operaciones, ni desglose por coste** (`studies/readings/edgeCost/one.py:34-38`, `README.md:12-13`). El `c*` no ha desaparecido: es ese mismo número (apartado 2.4).
2. **El umbral 2,0 se fijó en otra unidad, y el listón se ha movido dos veces sin que nadie lo decidiera.** Se puso el 2026-09-26 como «2-3 spreads por operación». Hoy el denominador ya no es el spread: es spread + doble deslizamiento + swap + comisión. En el NIKKEI de `oos1` el spread es el **50 %** de ese coste (calculado por mí), así que «2» de hoy son entre 3,5 y 4,5 spreads **de hoy**, según cuánto swap pague la estrategia (unos 3,7 en la cuenta antigua, que no devolvía el swap al bruto). Medido en el spread de hoy, la vara es el doble de alta. **Medido en dinero, no:** el 2026-09-29, el día que confirmaste el umbral, la ficha cobraba en `oos1` un spread de 915,5 puntos, y hoy 474,91; «2 spreads» de entonces y «2 costes» de hoy son 18,3 y 18,9 puntos de precio por operación (calculado por el revisor). La definición subió el listón al doble y la recalibración del spread del 2026-10-04 lo bajó a la mitad; en este activo y tramo se compensan. En otro no tiene por qué.
3. **El número tiene un error de muestreo enorme con las operaciones que hay.** Con 72 a 211 operaciones en `oos1`, el error típico del edge va de **1,1 a 2,9 unidades** (calculado por mí). Ninguna de las diez tiene un intervalo del 95 % que quede entero por encima de 2; sólo **una** (`3.11.426`) lo tiene entero por encima de 1. Comparar 1,79 con 2,0 es comparar ruido.
4. **El stop baja el edge en ocho de las diez y lo sube en dos, pero sólo en dos la bajada se distingue del ruido.** Hecha la cuenta emparejada (calculado por el revisor): `13.3.390` y `19.2.363`, las dos que pasan de ganar a perder. En conjunto el edge baja 0,74 unidades, con un intervalo de −1,47 a +0,01: apunta a que el stop cuesta, sin demostrarlo. «Ocho de diez bajan» no es una prueba (p = 0,11) (apartado 3.6).
5. **El README y el manual dicen que una versión con stop se rechaza. El código de hoy la precia**, y bien: sobre las 1.274 operaciones de `oos1` (450 cerradas por stop), el P/L repreciado coincide con el de SQX a 0,02 USD por operación (calculado por mí). También dicen que rechaza forex; tampoco: USDJPY sale, a 0,01 USD.
6. **Si mañana escribes una regla para el paso 25 en `criteria.yaml`, leerá las estrategias equivocadas.** El extractor de hechos (`pipeline/autopilot/facts.py:211`) pide para `edgeCost` sólo los resultados «de población» —los del paso 8—, no los JSON por estrategia del paso 25. En esta corrida devuelve 40.000 filas de 10.000 estrategias sin stop, y ninguna de las diez versiones con stop. El autopiloto ya no corre ese `edgeCost` de población en el paso 8, pero la ventana todavía lo ofrece entre las pruebas del 8 (`ui/daemon/results/catalogue.py:38`, `ui/daemon/workflow/tests.py:33-37`): lo que deje una corrida lanzada desde ahí es lo que leería el 25.
7. **El 25 y la regla R5c del paso 8 son hoy la misma cuenta** (lo ata un test), pero el 8 la lee sobre la madre sin stop, la acompaña de una t y corta; el 25 la lee sobre la versión con stop, sola, y no corta. Consecuencia: en una corrida normal, toda madre que llega al 25 ya fue elegida por tener ese mismo número alto en ese mismo tramo. El 25 no es una segunda medida independiente; lo único nuevo que aporta es lo que cambia el stop.
8. **Hay un corte que nadie llama corte.** Una madre que no tiene variante del paso 24 al percentil 90 se queda fuera del paso 25 y de `finalistas.json`, con su nombre en el mensaje (`pipeline/autopilot/traded.py:52`, `finalists.py:39`). En esta corrida no le pasó a ninguna.
9. **Una o dos operaciones deciden el veredicto de varias.** Quitando sólo la mejor operación de cada una, siguen cinco por encima de 2 (dos de ellas en 2,02 y 2,09), pero las de neto positivo pasan de 8 a 6. Quitando las dos mejores quedan tres por encima de 2; quitando las cinco mejores, una (calculado por el revisor; apartado 2.3).
10. **El edge no descuenta la subida del mercado.** Las diez son largas y el NIKKEI subió un 42 % en `oos1`. Por años, el edge conjunto fue 2,95 / 3,20 / **−0,59** / 3,36: negativo en 2022, el único año en que el índice cayó (calculado por el revisor; apartado 5.14).
11. **El coste del denominador es un supuesto, y ya se ha movido.** Un spread medio y un deslizamiento fijos, iguales en una barra tranquila y en una salida por stop. El spread del NIKKEI en FTMO pasó de 487 puntos de media en 2025 a 920 en 2026: un coste multiplicado por casi 2 no es un caso extremo, ya ocurrió (apartado 2.4).
12. **El error del punto 3 no viene de las rachas.** Remuestreando semanas enteras sale igual que remuestreando operaciones sueltas (calculado por el revisor). Lo que ese error no recoge es otra cosa: cómo se eligieron las diez, que se parecen entre sí, y que `oos1` son cuatro años con uno solo malo.

---

## 1. Qué es el paso y cómo decide

### 1.1 Dónde está

Familia «Cierre», después de la estructura (23) y del stop (24), justo antes de la validación en MetaTrader 5 (26). Es el último número que se calcula en Python antes de que la estrategia salga hacia MT5.

El stop del paso 24 es `SL = X · ATR(20)`, con X = el percentil 90 del MAE/ATR de las operaciones ganadoras del `build`; la misma regla para todas (`ledger/thresholds.yaml:1133-1138`, tuya, 2026-09-30). Poner un stop cambia las operaciones: algunas que antes se recuperaban ahora cierran en pérdida, y al quedar libre la estrategia puede abrir alguna entrada más. El paso 25 vuelve a hacer la cuenta del coste **con esas operaciones nuevas**.

### 1.2 La mecánica, en cinco movimientos

Lo lanza el autopiloto (`pipeline/autopilot/tail.py:159`, acción `edge` → `traded.edge`, `pipeline/autopilot/traded.py:110-129`):

1. **Elige la versión.** De la rejilla de stops del paso 24 (la segunda pasada más reciente, `AlgoData/atrCalculator/<proyecto>/<lote>/pass2/manifest.parquet`) toma, para cada madre, la variante con `percentile == 90` y `step == 0` (`traded.py:46-47`). No elige nada: el percentil es tuyo y el X lo calculó el paso 24.
2. **Monta una cosecha propia**, `AlgoData/harvest/<proyecto>/Stop_p90/<día>/` (`traded.py:72-107`): las operaciones de esas variantes en el mercado principal, etiquetadas `IS` (tramo `build`) y `OOS` (tramo `oos1`). `oos2` no entra. Cada fila lleva la **identidad de la madre**, no la del fichero con stop.
3. **Lanza el estudio una vez por madre**: `python3 -m studies.readings.edgeCost.report --project P --databank Stop_p90 --feed F --strategy "<nombre de la madre>"` (`traded.py:125-127`).
4. **El estudio** se queda con las filas `OOS`, las precia con el repreciado común a los costes de `oos1` de la ficha del activo, y divide (apartado 3).
5. **Escribe** `AlgoData/reports/<proyecto>/Stop_p90/<día>/edgeCost/estrategias/<madre>.json` y `.html`. Después el autopiloto escribe `finalistas.json` con **todas** las madres que tienen stop.

### 1.3 Cómo decide

No decide. El estudio compara el número con el umbral y pone una etiqueta («por encima del umbral» / «por debajo del umbral», `one.py:81-86`). Con `action: mark` la etiqueta sólo colorea. Con `action: drop`, lo único que cambia es la palabra DESCARTAR en el `verdict.csv` del modo población (`many.py:36`) — fichero que el paso 25, que corre en modo `--strategy`, **no escribe** (`report.py:36-45`). Es decir: hoy, ni cambiando `mark` por `drop` el paso 25 eliminaría a nadie.

### 1.4 Las estrategias que nos acompañan

Las diez madres de `Trade_NIKKEI225_M30_volatilidadL`, las mismas del dossier del paso 16. Como allí: salieron de un sorteo en el paso 8 y los pasos intermedios no tenían reglas aquel día, así que **no son un ensayo justo del paso**; sirven para ver qué aspecto tienen los números.

**El sorteo no fue a ciegas de `oos1`.** No se hizo entre las 10.000 sino entre las 3.148 que no fallaban el paso 8 aquel día (3.146 en Limbo y 2 en Pasa; `AlgoData/autopilot/…/20261004-154759/paso-8/verdict.csv`), y la puerta de entonces mataba a toda estrategia con neto de `oos1` negativo. Cruzado con el `scorecard.parquet` de la puerta: en la población entera el 59,5 % tiene neto positivo en `oos1`; en el bombo de 3.148, el **100 %** (calculado por el revisor; lo he comprobado). Por tanto las diez madres sin stop tienen edge mayor que 1 en `oos1` por construcción: ese tramo ya se usó para elegirlas. La versión con stop comparte la mayoría de sus operaciones y hereda parte del sesgo. La existencia del sesgo está demostrada; su tamaño no está medido.

---

## 2. Fundamentos

### 2.1 Neto, coste y bruto de una operación

- **Neto** (`pnl`): lo que la operación deja en la cuenta, ya cobrados los costes. Es el `Profit/Loss` de SQX.
- **Coste** (`cost`): lo que se pagó por hacerla.
- **Bruto**: lo que dejó el movimiento del precio antes de cobrar. `bruto = neto + coste`.

El coste tiene cuatro piezas (`engines/market/reprice.py:118`):

`coste = valor × (spread + 2 × deslizamiento) + swap + comisión`, con `valor = valor del punto × lotes`.

- El **spread** se paga una vez (al entrar se compra más caro que la apertura de la barra).
- El **deslizamiento** se paga dos veces, al entrar y al salir.
- El **swap** se paga por cada noche que la operación cruza (la noche triple cuenta 3).
- La **comisión**, una vez, al abrir.

**Ejemplo real hecho a mano** (`Strategy 3.11.426`, versión con stop, larga, 67,91 lotes, costes de `oos1` del NIKKEI: spread 4,7491, deslizamiento 1,6622, swap largo −4,78 % anual, comisión 0; valor del punto 0,063137):

- valor = 0,063137 × 67,91 = 4,2876 USD por punto de precio.
- Entra el 2020-02-05 11:30. Apertura de esa barra: 23.621,00. Precio de entrada = 23.621,00 + 4,7491 + 1,6622 = **23.627,41** (el que SQX exportó).
- Sale el 2020-02-06 02:30 por «Exit After X Bars». Apertura de esa barra: 23.675,27. Precio de salida = 23.675,27 − 1,6622 = **23.673,61** (el de SQX).
- Movimiento cobrado: 4,2876 × (23.673,61 − 23.627,41) = 4,2876 × 46,20 = 198,09 USD.
- Swap de una noche: 4,2876 × 23.627,41 × 4,78 / 100 / 360 = 13,45 USD.
- **Neto** = 198,09 − 13,45 = **184,64** (SQX: 184,63).
- **Coste** = 4,2876 × (4,7491 + 2 × 1,6622) + 13,45 = 34,62 + 13,45 = **48,07**.
- **Bruto** = 184,64 + 48,07 = **232,71**. Comprobación: es lo que habría dejado ir de apertura a apertura sin pagar nada, 4,2876 × (23.675,27 − 23.621,00) = 232,69.

Esta operación ganó, antes de costes, 4,8 veces lo que pagó.

### 2.2 El edge: un cociente de medias

Una operación sola no dice nada. El estudio hace la cuenta con todas:

`edge = (bruto medio por operación) / (coste medio por operación)`

**Juguete.** Cinco operaciones con el mismo coste, 20:

| operación | bruto | coste | neto |
|---|---|---|---|
| 1 | −50 | 20 | −70 |
| 2 | −50 | 20 | −70 |
| 3 | −50 | 20 | −70 |
| 4 | −50 | 20 | −70 |
| 5 | +400 | 20 | +380 |
| **media** | **+40** | **20** | **+20** |

edge = 40 / 20 = **2**. Lectura: por cada dólar pagado en costes, el precio dejó dos; uno se lo quedan los costes y el otro es tuyo. Con edge = 1 la estrategia empata; por debajo de 1, pierde. De hecho `neto medio = coste medio × (edge − 1)`.

**Por qué «media de brutos entre media de costes» y no «media de los cocientes».** Los lotes cambian de una operación a otra (en `3.11.426`, de 16 a 112, con 67 de media). El cociente de medias pesa cada operación por su dinero, que es como pesa en la cuenta. La media de los cocientes daría el mismo peso a una operación de 20 lotes que a una de 70.

### 2.3 Media y mediana, y por qué difieren

La **media** reparte el total entre todas. La **mediana** es la operación de en medio cuando se ordenan: la mitad queda por debajo y la mitad por encima.

En el juguete, la media del bruto es +40 y la mediana es −50. Las dos son ciertas y cuentan cosas distintas: **la operación típica pierde**; el dinero lo trae una sola. Esto es una distribución **asimétrica**: muchas pérdidas pequeñas y parecidas, pocas ganancias grandes. Es exactamente la forma que fabrica un stop: recorta todas las pérdidas al mismo tamaño y deja correr las ganancias.

**En los datos reales** (versión con stop, `oos1`, calculado por mí):

| estrategia | bruto medio | bruto mediano | las 5 mejores operaciones, sobre el bruto total |
|---|---|---|---|
| `3.11.426` | +225 | +201 | 56 % |
| `14.3.479` | +38 | **−125** | **184 %** |

En `14.3.479` las cinco mejores operaciones de 115 suman casi el doble de todo el bruto: sin ellas, la estrategia pierde antes de pagar un céntimo de coste. La media (+38) no lo enseña; la mediana (−125) sí.

**Qué le pasa al veredicto si se quitan las mejores operaciones** (versión con stop, `oos1`; calculado por el revisor: se quitan las de mayor bruto y se rehace el cociente):

| estrategia | edge | sin la mejor | sin las 2 mejores | sin las 5 mejores | la mejor, en veces el coste medio |
|---|---|---|---|---|---|
| `3.11.426` | 5,92 | 4,92 | 4,23 | 2,76 | 96 |
| `4.13.338` | 3,99 | 3,38 | 2,82 | 1,66 | 87 |
| `10.11.484` | 3,34 | 2,64 | 2,10 | 0,89 | 82 |
| `18.5.355` | 2,86 | 2,02 | 1,54 | 0,19 | 87 |
| `16.5.352` | 2,46 | 2,09 | 1,76 | 0,84 | 75 |
| `3.9.284` | 1,79 | 1,42 | 1,08 | 0,22 | 65 |
| `15.9.352` | 1,19 | 0,95 | 0,73 | 0,12 | 52 |
| `14.3.479` | 1,05 | 0,28 | −0,23 | −0,93 | 88 |
| `13.3.390` | 0,29 | −0,72 | −1,61 | −3,88 | 72 |
| `19.2.363` | −0,30 | −1,18 | −2,02 | −3,84 | 65 |

Por encima de 2: 5 → 5 (dos de ellas en 2,02 y 2,09) → 3 → 1. Con neto positivo: 8 → **6** quitando **una** operación (`15.9.352` y `14.3.479` pasan a perder) → 6 → 2. Quitar la **peor** operación no cambia ningún recuento: el stop acota la pérdida, así que todo el veredicto cuelga de la cola de ganancias. En `14.3.479` una sola operación es el 73 % del bruto total. Dicho corto: el «pasa / no pasa» contra 2 depende de dos operaciones en dos de las cinco que pasan, y el signo del neto depende de una sola en dos de las ocho que ganan.

**Qué había y qué hay.** La definición vieja publicaba `edge_median` = bruto **mediano** / coste medio, precisamente por esto. La definición de hoy **no publica ninguna mediana**. Una mediana negativa con una media positiva no es un defecto por sí sola —toda estrategia de tendencia con stop la tiene—; lo que avisa es que el resultado depende de pocas operaciones, y por tanto que su error de muestreo es grande (2.5).

### 2.4 El `c*` de breakeven: cuánto puede encarecerse el coste

Pregunta: si multiplico **todos** los costes por k y las operaciones no cambian, ¿con qué k el neto llega a cero?

`neto medio con costes × k = bruto medio − k × coste medio`

Se anula cuando `k* = bruto medio / coste medio`. **Es el edge.** Por eso el estudio de hoy no escribe un `c*` aparte: el propio edge es el múltiplo de breakeven, y en dinero `c* = k* × coste medio = bruto medio`.

**A mano, con `3.11.426`** (versión con stop, `oos1`): bruto medio 224,91 USD, coste medio 37,96 USD.

- k* = 224,91 / 37,96 = **5,92**. El coste puede multiplicarse por casi 6 antes de empatar, **según la estimación puntual**: ese 5,92 tiene un intervalo de 1,7 a 10,4 (apartado 2.5).
- En dinero: empata cuando el coste por operación llega a 224,91 USD (hoy 37,96).
- Con el coste un 25 % más caro (k = 1,25, el múltiplo que usa la puerta del paso 8): neto medio = 224,91 − 1,25 × 37,96 = 177,46 USD por operación. Con k = 2: 148,99. Con k = 5,92: 0.

**A mano, con `14.3.479`:** 38,18 / 36,46 = **1,05**. Un 5 % más de coste y empata.

**Tres avisos sobre lo que `k*` supone:**

- Que **los cuatro costes suben juntos** y en la misma proporción. Antes había un breakeven por coste («cuál muerde primero»); ya no (`README.md:41-42`).
- Que **las operaciones no cambian** al encarecerse el coste. Con stop eso es sólo aproximado: un spread mayor sube el precio de entrada y con él el nivel del stop, que se toca un poco antes. `k*` es una cuenta de primera aproximación, no una simulación. No está medido cuánto se desvía.
- Que **el coste de partida es un supuesto**: un spread medio y un deslizamiento fijos, iguales en una barra tranquila y en una salida por stop (`engines/market/reprice.py:109-118`). La calibración del proyecto (600 operaciones reales de FTMO, Hantec y FundingPips, `assets/RULES.md:92-99`) da 1,33 veces el spread por ida y vuelta, con un intervalo hasta 1,72, y la cola son justamente los stops ejecutados con el spread abierto; el modelo cobra 1,7: holgado frente a la media, igual al extremo alto. Y el spread del NIKKEI en FTMO fue de 487 puntos de media en 2025 y de 920 en 2026 (`knowhow/costs/funded-tick-spread-vs-price.md:17`): un k de casi 2 **ya pasó**, en un año.

**Qué queda si el coste se mueve** (calculado por el revisor, sobre la estimación puntual): con spread y deslizamiento × 1,5 conservan neto positivo 6 de 10; × 2, 5; × 3, 4. Y si el deslizamiento de más cayera **sólo en las salidas por stop** (450 de 1.274), el neto llega a cero con 0,2 spreads de más en `14.3.479`, 0,8 en `15.9.352`, 5,6 en `3.9.284`, y entre 10,6 y 25,9 en las cinco que pasan. Las cinco de arriba tienen margen de coste amplio; lo que no tienen firme es el numerador.

### 2.5 El error de muestreo

El edge se calcula con una muestra: las operaciones que hubo en `oos1`. Con otra muestra igual de buena saldría otro número. El **error típico** dice cuánto baila.

**La cuenta.** El coste por operación **sí varía**: va con los lotes (su desviación típica es del 30 al 46 % de su media, y en la corrida va de 8 a 222 USD). Pero el bruto baila de 13 a 25 veces el coste medio, así que a efectos del error típico el coste se puede tratar como fijo (la cuenta completa, con la variación del coste, da lo mismo hasta la segunda cifra). Así que, muy aproximadamente:

`error típico del edge ≈ (desviación típica del bruto / coste medio) / √n`

**A mano, con `3.11.426`:** desviación típica del bruto 810,9 USD, coste medio 37,96, n = 92.

- 810,9 / 37,96 = 21,4. Una sola operación «baila» 21 veces el coste.
- √92 = 9,6.
- error típico ≈ 21,4 / 9,6 = **2,23**.
- Intervalo aproximado del 95 %: 5,92 ± 2 × 2,23 → **de 1,5 a 10,4**.

El edge de la mejor estrategia de la corrida es «algo entre 1,5 y 10». Eso es lo que se sabe.

**La regla de bolsillo.** En las diez versiones, la desviación del bruto es entre 13 y 25 veces el coste (calculado por mí). Con 20 veces:

| operaciones en `oos1` | error típico del edge |
|---|---|
| 50 | 2,8 |
| 100 | 2,0 |
| 200 | 1,4 |
| 400 | 1,0 |
| 1.600 | 0,5 |

Para que el error baje a la mitad hacen falta cuatro veces más operaciones. Con 100 operaciones, un edge medido de 2 y uno de 0 no se distinguen.

**Cómo lo he comprobado.** Con un remuestreo (*bootstrap*): de las n operaciones de una estrategia saco n al azar con repetición, recalculo el edge, y lo repito 10.000 veces (semilla 0). El 2,5 % más bajo y el 2,5 % más alto de esos 10.000 edges dan el intervalo. Supuesto: las operaciones son independientes entre sí. Comprobado remuestreando semanas enteras en vez de operaciones sueltas: el error sale igual (2,17 frente a 2,23 en `3.11.426`; iguales en las diez; calculado por el revisor), y la correlación entre el bruto de una operación y el de la siguiente va de −0,13 a +0,03. En este tramo las rachas no agrandan el error. La fórmula de arriba y el remuestreo coinciden (2,23 frente a un intervalo 1,68 – 10,38). La tabla completa está en 3.5.

**El estudio no calcula nada de esto.** Escribe el edge sin error, sin intervalo y sin el número de operaciones.

**Lo que este error no cubre.** Mide cuánto baila el número entre operaciones *dentro* de 2020-2023. No recoge tres cosas, y las tres pesan más: que las diez se eligieron mirando ese mismo tramo (1.4), que las diez se parecen entre sí (3.5) y que `oos1` son cuatro años con uno solo malo (5.14). El intervalo supone que los próximos años se parecen a la mezcla de 2020-2023.

---

## 3. Lo que calcula el estudio, pieza a pieza

### 3.1 Qué operaciones entran

Sólo las filas con `sample == "OOS"` (`studies/readings/edgeCost/costs.py:64`), que en la cosecha del paso 25 son las del tramo `oos1` (`traded.py:18`). El `build` está en la cosecha pero **no se lee**; `oos2` ni siquiera está. Para el NIKKEI, `oos1` es 2020-2023: las operaciones van del 2020-01-08 al 2023-12-29.

En la corrida: 1.274 operaciones de las diez versiones. Por cómo cerraron: 454 «Exit After X Bars», **450 por stop**, 242 por señal de salida, 128 por cierre de viernes.

### 3.2 A qué costes

Los del tramo `oos1` de la ficha del activo (`costs.py:65` → `reprice.costs(feed, "oos1")`, `reprice.py:30-50`). Para el NIKKEI hoy:

| coste | valor | de dónde sale (ficha y `assets/RULES.md:92-99`, `224-232`) |
|---|---|---|
| spread | 474,91 puntos = 4,7491 de precio | 0,0174 % del precio medio de `oos1`: el spread medio de la firma **más ancha** de FTMO / Hantec / FundingPips, **sin factor de seguridad** |
| deslizamiento | 166,22 puntos por lado | el **35 %** del spread (tuyo, 2026-10-04); SQX lo cobra a la entrada y a la salida |
| swap largo | −4,78 % anual | el peor de FTMO y Hantec, leído el 2026-10-01; noche triple el viernes |
| comisión | 0 | cero en índices (tuyo, 2026-09-29) |

Un viaje de ida y vuelta cuesta, pues, **1,7 spreads** antes de swap.

> **Ojo con la política que tengo apuntada de ti** («% + un poco de spread, factor 1,25, spread de Darwinex»). La ficha de hoy dice otra cosa: el spread es el de la firma más ancha y **sin factor** (`ledger/thresholds.yaml:1030-1038`, `spread.safety.factor` = 1,0, tuyo, 2026-10-04: «sin factor sobre el spread (era 1,25 desde 2026-09-27)»); el margen va en el deslizamiento del 35 %. El 1,25 sobrevive en dos sitios: el spread del crudo, y el múltiplo k de la t de la regla R5c del paso 8 (`studies/screening/gate/config.yaml:78`). **En el paso 25 no hay ningún 1,25.** (`assets/RULES.md:255,287` todavía llama a Darwinex «the spread reference» y cita su comisión del 0,005 %: está desfasado respecto de la ficha.)

**Reparto del coste en `oos1`, las diez versiones juntas (calculado por mí):** spread 50,3 % · deslizamiento 35,2 % · swap 14,4 % · comisión 0 %. El swap pesa distinto según cuánto aguante cada una: del 3 % del coste (`14.3.479`, 0,06 noches por operación) al 25 % (`16.5.352`, 0,72 noches).

### 3.3 Cómo se precia cada operación

El estudio **no usa el `Profit/Loss` de SQX**. Vuelve a calcular el neto y el coste de cada operación desde las aperturas de barra, con el repreciado común (`costs.py:47` → `reprice.real`, `reprice.py:162-208`):

- **Entrada:** apertura de la barra de entrada + spread + deslizamiento (`reprice.py:110`).
- **Salida normal** (por barras, señal, viernes): apertura de la barra de salida − deslizamiento (`reprice.py:111`).
- **Salida por stop:** el **precio de cierre que exportó SQX**, no la apertura de la barra —el stop se toca dentro de la barra— (`reprice.py:190-197`). Si ese precio cae fuera del rango de su barra por más de spread + deslizamiento, el estudio se niega y nombra las estrategias (`reprice.py:198-204`).

**Ejemplo real de salida por stop** (`3.11.426`, 36,40 lotes): entra el 2020-04-07 03:30 a 19.066,27 + 6,4113 = 19.072,68; el stop salta en la barra de las 05:00 (apertura 18.949,27, mínimo 18.744,47) a **18.815,01**, que es el precio de SQX y está dentro de la barra. Neto = 0,063137 × 36,40 × (18.815,01 − 19.072,68) = **−592,17** (SQX: −592,17). Coste = 2,2982 × 8,0735 = 18,55. Bruto = −573,62.

**¿Reproduce a SQX?** Calculado por mí sobre la corrida: en las 1.274 operaciones de `oos1` con stop, la mayor diferencia entre el neto repreciado y el `Profit/Loss` de SQX es de **0,02 USD**; en las 1.162 de las madres sin stop, también 0,02. Dicho de otro modo: en este activo, el paso 25 de hoy da el mismo neto que SQX y además sabe cuánto de él fue coste.

En las otras dos cosechas de paso 25 que hay en disco, de un vistazo: USDJPY M30 (forex, 1.099 operaciones) 0,01 USD; USA500 H1 (464 operaciones) hasta 0,47 USD, en una operación de 46,31 lotes: dentro de la tolerancia que documenta `reprice.py:84` (0,02 + 2 × tick × valor del punto × lotes = 0,95 USD ahí; es el redondeo al tick de la entrada y de la salida). Ninguna de las 464 se sale de esa tolerancia.

### 3.4 La cuenta y lo que escribe

`one.measure` (`one.py:24-38`):

- `gross = pnl + cost`, por operación.
- `mean_gross`, `mean_cost`, y `edge_mean = mean_gross / mean_cost`.
- `by_hour`, `by_dow`: el bruto medio por hora y por día de la semana de **entrada**. Es un dibujo para mirar, no entra en ningún veredicto.

Lo que queda en el JSON de cada estrategia (`one.py:87-89`): la etiqueta contra el umbral, dos pestañas (los tres números; las dos gráficas), el aviso de costes provisionales si la ficha lleva alguno, y **un único hecho**: `summary.edge_mean`.

**Lo que no escribe:** número de operaciones, mediana, error, el neto, cuántas cerraron por stop, y nada del `build`.

### 3.5 Los diez resultados, con el código de hoy

Versión con stop, `oos1`. Las tres primeras columnas numéricas son las del estudio; el resto, calculado por mí (error típico: método delta para un cociente de medias, que incluye la covarianza entre bruto y coste; intervalo y «remuestras con edge < 2»: remuestreo de 10.000 tiradas, operaciones independientes).

| estrategia | n | bruto medio | coste medio | **edge** | error típico | intervalo 95 % | remuestras con edge < 2 | neto `oos1` (USD) |
|---|---|---|---|---|---|---|---|---|
| `3.11.426` | 92 | 224,91 | 37,96 | **5,92** | 2,23 | 1,68 a 10,38 | 3,5 % | +17.199 |
| `4.13.338` | 134 | 170,89 | 42,85 | **3,99** | 1,80 | 0,47 a 7,59 | 13,6 % | +17.157 |
| `10.11.484` | 112 | 125,20 | 37,53 | **3,34** | 1,76 | −0,03 a 6,80 | 22,7 % | +9.819 |
| `18.5.355` | 98 | 121,56 | 42,46 | **2,86** | 2,37 | −1,73 a 7,38 | 35,7 % | +7.752 |
| `16.5.352` | 194 | 104,80 | 42,64 | **2,46** | 1,78 | −0,98 a 5,98 | 40,5 % | +12.060 |
| `3.9.284` | 170 | 71,29 | 39,81 | 1,79 | 1,23 | −0,60 a 4,19 | 57,5 % | +5.351 |
| `15.9.352` | 211 | 55,08 | 46,21 | 1,19 | 1,07 | −0,86 a 3,36 | 77,2 % | +1.872 |
| `14.3.479` | 115 | 38,18 | 36,46 | 1,05 | 1,21 | −1,12 a 3,60 | 79,5 % | +198 |
| `13.3.390` | 72 | 10,51 | 35,86 | 0,29 | 2,86 | −5,42 a 5,94 | 72,3 % | **−1.825** |
| `19.2.363` | 76 | −6,22 | 20,41 | **−0,30** | 2,26 | −4,59 a 4,14 | 84,9 % | **−2.024** |

Cómo leerla:

- **Cinco de diez** quedan por encima de 2. La etiqueta del estudio sería «por encima del umbral» para ellas y «por debajo» para las otras cinco. Ese recuento es tan incierto como cada edge: remuestreando semanas enteras para las diez a la vez, va **de 2 a 8** (95 %; mediana 5); «por encima de 1» va de 4 a 9 (calculado por el revisor).
- **Las diez no son diez pruebas independientes.** Mismo índice, misma dirección, misma familia: el 29 % de las operaciones entra en la misma barra que otra de las diez (1.034 barras de entrada distintas para 1.274 operaciones); la correlación media del neto semanal entre pares es 0,16 y la máxima 0,74 (calculado por el revisor).
- **Ningún intervalo queda entero por encima de 2.** El de `3.11.426` es el único que queda entero por encima de 1 (el punto muerto).
- «Remuestras con edge < 2» **no es un p-valor**: es cuántas de las 10.000 muestras rehechas dan menos de 2. Sirve para ver que `16.5.352` (2,46, «pasa») y `3.9.284` (1,79, «no pasa») están, a efectos de lo que se puede saber, en el mismo sitio.
- El edge negativo de `19.2.363` significa que el precio, **antes de costes**, ya fue en contra.

### 3.6 Qué cambia al poner el stop

Las mismas diez madres, `oos1`, código de hoy; **sin stop** (cosecha `Results`, la de la puerta) frente a **con stop** (`Stop_p90`). Calculado por mí.

| estrategia | n sin → con | cerradas por stop | edge sin stop | edge con stop | neto sin → con (USD) |
|---|---|---|---|---|---|
| `3.11.426` | 92 → 92 | 35 % | 6,47 | 5,92 | 19.670 → 17.199 |
| `4.13.338` | 126 → 134 | 38 % | 4,91 | 3,99 | 22.721 → 17.157 |
| `10.11.484` | 106 → 112 | 39 % | 4,65 | 3,34 | 14.769 → 9.819 |
| `13.3.390` | 58 → 72 | 38 % | 3,37 | **0,29** | 5.342 → −1.825 |
| `19.2.363` | 66 → 76 | 54 % | 2,71 | **−0,30** | 2.311 → −2.024 |
| `3.9.284` | 164 → 170 | 25 % | 2,50 | 1,79 | 10.197 → 5.351 |
| `14.3.479` | 98 → 115 | 39 % | 2,27 | 1,05 | 4.690 → 198 |
| `18.5.355` | 98 → 98 | 30 % | 2,25 | 2,86 | 5.392 → 7.752 |
| `16.5.352` | 187 → 194 | 26 % | 2,09 | 2,46 | 9.005 → 12.060 |
| `15.9.352` | 167 → 211 | 42 % | 1,70 | 1,19 | 5.626 → 1.872 |

Lo que se ve:

- **Sin stop, 9 de 10 por encima de 2; con stop, 5 de 10.** El stop baja el edge en ocho y lo sube en dos. La diferencia de recuentos (4) tiene un intervalo de −1 a 4, y el recuento «bajan» va de 5 a 10 (calculado por el revisor): tampoco estos recuentos son firmes.
- **Entre el 25 % y el 54 % de las operaciones de `oos1` cierran por stop.** El stop es el percentil 90 del MAE de las *ganadoras* del `build`: a las ganadoras apenas las toca, pero las perdedoras suelen ir más lejos en contra, y a esas las corta. Si eso es mucho o poco es asunto del paso 24, no de éste; aquí sólo se ve el efecto.
- **Hay más operaciones con stop** (hasta 44 más en `15.9.352`): al cerrar antes, la estrategia queda libre para entrar otra vez.
- **El coste medio casi no cambia** (baja entre 0,1 y 3,2 USD por operación). Lo que cambia es el bruto. El stop no hace la estrategia más cara de operar; le quita movimiento a favor.
- **La cuenta emparejada** (calculado por el revisor: las mismas semanas remuestreadas para las dos versiones, de modo que el ruido común se cancela):
  - Por estrategia, la diferencia de edge (con stop − sin stop) sólo excluye el cero en **dos**: `13.3.390`, −3,08 (95 %: −5,12 a −1,01), y `19.2.363`, −3,01 (−5,47 a −0,18). Son las dos que pasan de ganar a perder. En las otras ocho el intervalo cruza el cero.
  - Las diez juntas: edge 3,07 → 2,33, diferencia **−0,74** (95 %: −1,47 a +0,01). Neto conjunto 99.724 → 67.559 USD, diferencia −32.165 (95 %: −67.433 a +1.972). Apunta a que el stop cuesta; no lo demuestra.
  - «Ocho de diez bajan» no se sostiene como prueba: aun suponiéndolas independientes —y no lo son—, 8 de 10 en una prueba de signos da p = 0,11.
- **No todas comparten sus entradas.** Seis de las diez comparten casi todas (de 124 de 134 a 98 de 98). En cuatro, entre el 15 % y el 26 % de las operaciones de la versión con stop son entradas que la madre no hizo: `15.9.352` (163 comunes de 211), `13.3.390` (56 de 72), `19.2.363` (56 de 76, y 10 entradas de la madre desaparecen), `14.3.479` (98 de 115) (calculado por el revisor). En ésas el stop no sólo recorta operaciones: cambia cuáles hay. Las dos que pasan a perder están entre las que menos comparten.
- **La comparación no es limpia.** La columna «sin stop» está condicionada a neto positivo en `oos1` (así se eligieron las madres, 1.4) y la columna «con stop» no. Parte de la caída es regresión a la media y no efecto del stop. No está medido cuánto.

### 3.7 Lo que la corrida guardó (definición vieja)

Los diez JSON del 2026-10-04 se hicieron con el código anterior. Sus hechos son otros: `n`, `edge_mean`, `edge_median`, `breakeven_multiple`, `breakeven_all`, `bites_first`, `reconcile`. Y su cuenta también:

- **Bruto** = `Profit/Loss` + comisión + el spread **medido** en el precio de relleno contra la barra.
- **Denominador** = el spread **de hoy** de la ficha + comisión. Sin deslizamiento y sin swap.
- **Muestra** = `build` y `oos1` **juntos**.
- `edge_median` = bruto mediano / coste medio. `breakeven_multiple` = el mismo `edge_mean`. `breakeven_all` = el múltiplo de **todos** los costes (con deslizamiento y swap) que deja el neto en cero.

| estrategia | n (IS+OOS) | `edge_mean` guardado | `edge_median` guardado | `breakeven_all` guardado | edge de hoy (3.5) |
|---|---|---|---|---|---|
| `3.11.426` | 232 | 10,16 | 6,66 | 5,30 | 5,92 |
| `4.13.338` | 338 | 11,67 | 2,12 | 5,50 | 3,99 |
| `10.11.484` | 271 | 7,00 | 0,77 | 3,83 | 3,34 |
| `18.5.355` | 260 | 8,49 | 6,43 | 3,93 | 2,86 |
| `16.5.352` | 511 | 2,25 | −2,84 | 1,21 | 2,46 |
| `3.9.284` | 397 | 5,89 | −0,70 | 3,08 | 1,79 |
| `15.9.352` | 500 | 1,87 | −6,65 | 1,08 | 1,19 |
| `14.3.479` | 321 | 3,66 | −3,78 | 2,11 | 1,05 |
| `13.3.390` | 251 | 3,98 | −4,96 | 1,90 | 0,29 |
| `19.2.363` | 250 | 2,40 | −4,05 | 1,38 | −0,30 |

Con aquella definición, **9 de 10** pasaban el 2,0. Dos razones para la diferencia, las dos de fondo:

1. **El denominador era la mitad.** Sólo spread. El `breakeven_all` guardado, que ya contaba todos los costes, es más o menos la mitad del `edge_mean` guardado en todas.
2. **Entraba el `build`.** `13.3.390` y `19.2.363` tienen un `breakeven_all` de 1,90 y 1,38 con el `build` dentro, y 0,29 y −0,30 con sólo `oos1`: lo bueno estaba en el tramo donde se construyeron.

Seis de las diez tenían la mediana negativa ya entonces.

---

## 4. El criterio cargado y por qué

### 4.1 Tal como está hoy en disco

**El umbral** (`ledger/thresholds.yaml:198-216`; el estudio lo lee de ahí, `config.yaml:10-11`):

| clave | valor | quién y cuándo | por qué, según el ledger |
|---|---|---|---|
| `edgeCost.min_edge_spreads` | **2,0** | agente, 2026-09-26 | «orden de magnitud de partida del encargo 11 (2-3 spreads por operación); fijado antes de mirar resultados. Confirmado como umbral definitivo por el dueño (OPEN.md §48, 2026-09-29)» |
| `edgeCost.action` | **`mark`** | agente, 2026-09-26 | «mark (no elimina) frente a drop (elimina en curate). Confirmado como acción definitiva por el dueño» |

**Las reglas del autopiloto:** `pipeline/autopilot/criteria.yaml` tiene pasos 8, 10, 11.5, 12, 14, 16, 16.5, 17, 18, 18.5 y 19. **No tiene 25.** El plan (`tail.py:159-160`) ejecuta el paso y, como no hay reglas, no llama al juez; lo siguiente es escribir los finalistas.

**El único filtro de hecho:** tener stop. `traded.stops` (`traded.py:43-52`) deja fuera, por su nombre, a la madre sin lote del paso 24, ausente de él, o sin el percentil 90; si no queda ninguna, el paso se para limpio («no hay versión que operar», `traded.py:120-122`).

### 4.2 Qué comparte hoy el 25 con el 8, y qué no

El paso 8 se rediseñó con el encargo 44 y el `edgeCost` se redefinió para ser **el mismo número** que la puerta.

**Comparten:**

- La fórmula. `gate.scorecard.edge_mean_oos` (`studies/screening/analysis/onepass.py:11-21`) y `edgeCost.edge_mean` son `media(pnl + coste) / media(coste)` por estrategia. `tests/test_edgecost.py:38-57` comprueba que dan lo mismo sobre las mismas operaciones.
- El repreciado (`engines/market/reprice.py`) y los costes de `oos1` de la ficha.
- El tramo: sólo `oos1`.
- El 2 como línea de «pasa».

**No comparten:**

| | paso 8 (regla R5c) | paso 25 |
|---|---|---|
| sobre qué operaciones | la madre **sin** stop | la madre **con** el stop del paso 24 |
| quién lo calcula | la puerta, nivel 1b, para toda la población | `edgeCost.report --strategy`, madre a madre |
| con qué se acompaña | la t del exceso con el coste × 1,25 (`t_exceso_k`) | nada |
| las líneas | Pasa con edge ≥ 2 **y** t(k) ≥ 1,65; Limbo con edge entre 1,25 y 2 o t(k) baja; **Falla** con edge < 1,25 (`criteria.yaml:90-94`) | una sola línea, 2,0, que sólo marca |
| consecuencia | corta el databank | ninguna |
| de dónde sale el 2 | de `criteria.yaml` | de `ledger/thresholds.yaml` — son **dos sitios distintos**: mover uno no mueve el otro |

**Consecuencia de compartir número y tramo.** En una corrida normal el paso 8 ya ha dejado pasar sólo a las madres con edge ≥ 1,25 (Limbo) o ≥ 2 (Pasa) en `oos1`. El edge del paso 25 se mide sobre esas mismas operaciones más el efecto del stop: llega sesgado al alza y no confirma nada que el paso 8 no hubiera exigido ya. Un tramo que no se haya usado para elegir sólo queda en `oos2`.

**El `edgeCost` «de población» del paso 8.** El autopiloto ya no lo corre: los estudios del 8 son hoy la puerta, más `monkey` y `entryQuality` (`ui/daemon/workflow/steps.py:30-32`, `82`), y el comentario de `criteria.yaml:68` da `edgeCost.*` por fuera. Pero **la ventana todavía lo ofrece** entre las pruebas del paso 8: `ui/daemon/results/catalogue.py:38` lo archiva bajo «8» y `ui/daemon/workflow/tests.py:33-37` añade al paso todo lo archivado bajo su número. `.claude/skills/workflow-simple/steps.md:12` también lo lista. Se puede seguir lanzando a mano, y lo que deje esa corrida es lo que `facts.py:211` leería para el 25 (5.5).

### 4.3 Lo que diría una regla, sobre la corrida real

Sin proponer ninguna: esto es lo que saldría con las líneas que ya existen en el proyecto, aplicadas a la tabla 3.5.

| línea | versiones que quedarían por debajo, de 10 |
|---|---|
| edge ≥ 2 (el umbral cargado) | 5 (`3.9.284`, `15.9.352`, `14.3.479`, `13.3.390`, `19.2.363`) |
| edge ≥ 1,25 (el suelo de Falla de R5c) | 4 (las mismas menos `3.9.284`) |
| edge ≥ 1 (neto positivo en `oos1`) | 2 (`13.3.390`, `19.2.363`) |

Y con el error delante: una línea que exigiera que el intervalo del 95 % quedase entero por encima de 1 dejaría pasar a **una**; por encima de 2, a **ninguna**. No es un argumento contra esas diez, es la medida de lo poco que 100 operaciones dicen sobre un cociente.

Los tres recuentos de la tabla llevan el mismo error que «5 de 10»: de 2 a 8 por encima de 2, de 4 a 9 por encima de 1 (95 %, remuestreo por semanas; calculado por el revisor). Y dependen de muy pocas operaciones: quitando la mejor de cada una, las de neto positivo bajan de 8 a 6 (2.3).

---

## 5. Lo que no cuadra o no está medido

### 5.1 `WORKFLOW.md` describe la definición vieja

`docs/AgentPDFs/WORKFLOW.md:33` (paso 8) y `:55` (paso 25) hablan del bruto reconstruido de `Profit/Loss` + comisión + spread modelado, en spreads de hoy, media y mediana, y `c*`. El código: `one.py:34-38` y `README.md:12-13` («no median, no trade count and no per-cost breakdown»). El manual (`AlgoData/manual-fuentes/50-edge-por-coste.md:16-19`) sí recoge el cambio.

### 5.2 El umbral se llama «spreads» y ya no mide spreads

`edgeCost.min_edge_spreads` (`ledger/thresholds.yaml:198-206`) conserva el nombre y el porqué de cuando el denominador era el spread. Hoy el denominador es el coste entero. En el NIKKEI de `oos1` el spread es el 50,3 % del coste (calculado por mí), así que 2,0 de hoy son unos 4 spreads **de hoy**: 3,5 en una estrategia que casi no pernocta, 4,5 en una que pernocta mucho. En la cuenta antigua, que no devolvía el swap al bruto, la línea de hoy equivale a un «edge antiguo» de unos 3,7 (calculado por el revisor).

Pero el spread de la ficha también cambió. El 2026-09-29, el día en que el ledger dice que confirmaste el 2,0, `spread_oos` del NIKKEI era **915,5** puntos (`git show 2c2ff2b:assets/symbols/NIKKEI225.yaml`); desde la recalibración del 2026-10-04 es **474,91**. En puntos de precio por operación, en `oos1`: «2 spreads» del 29-09 = 2 × 9,155 = **18,3**; «2 costes» de hoy = 2 × (4,7491 + 2 × 1,6622 + ≈ 1,36 de swap) ≈ **18,9** (calculado por el revisor). En dinero, el listón quedó casi donde estaba.

Lo que sí pasó sin que nadie lo decidiera: el listón se movió **dos veces** —la definición lo subió al doble y la recalibración del spread lo bajó a 0,52— y en este activo y tramo las dos cosas se compensan. En otro activo no tiene por qué. Lo confirmaste en la unidad antigua y con el spread antiguo.

### 5.3 El README y el manual dicen que la versión con stop se rechaza

`studies/readings/edgeCost/README.md:38-39` («a step-25 version whose stop closes a trade inside a bar is refused») y el manual (`50-edge-por-coste.md:76-78`, «Pendiente de decisión del dueño»). El código la precia desde la oleada 5 del encargo 44 (`reprice.py:190-197`; el propio `costs.py:5` lo dice). Medido: 450 salidas por stop en `oos1`, a 0,02 USD de SQX. El mensaje de error que cita el manual tampoco es el que da el código (`reprice.py:200-204`).

### 5.4 Dicen que rechaza forex

`README.md:40` y manual `:33`. `reprice.costs` trata el swap en puntos de las fichas de forex (`reprice.py:43-50`). USDJPY M30: 1.099 operaciones repreciadas a 0,01 USD de SQX.

### 5.5 El extractor de hechos del paso 25 lee el paso 8

`pipeline/autopilot/facts.py:211`: `sources.results(project, study, False if study == "edgeCost" else None)`. `False` quiere decir «sólo corridas de población» (`ui/daemon/workflow/sources.py:66-67`, `96-100`). Los resultados del paso 25 son por estrategia y no llevan manifiesto, así que quedan fuera. Comprobado sobre la corrida: `facts.gather(P, "25")` devuelve 40.000 filas `edgeCost.verdict_csv.*` de 10.000 estrategias —la población del paso 8, con la definición vieja— y ninguna de `Stop_p90`. La ficha `knowhow/eng/step25-reads-a-harvest-of-the-traded-version.md` ya lo avisa. Mientras el paso 25 no tenga reglas no hace daño; el día que las tenga, juzgará a quien no es. Y como el autopiloto ya no corre `edgeCost` de población en el paso 8, en una corrida nueva `gather` no encontrará nada —todo hecho ausente, es decir, Limbo—, **salvo que alguien lance a mano el `edgeCost` de población desde la ventana**, que aún lo ofrece (4.2): entonces leerá esa corrida.

### 5.6 `pipeline/autopilot/README.md` anuncia hechos que ya no existen

Líneas 115-117: `edgeCost.verdict_csv.edge_mean`, `edge_median` («in units of today's spread + commission, IS+OOS pooled») y `n`. Hoy `verdict.csv` lleva `identity, edge_mean, verdict` (`report.py:51-52`), y del paso 25 sólo sale `summary.edge_mean`.

### 5.7 `action: drop` no haría nada en el paso 25

`drop` sólo cambia la columna `verdict` del `verdict.csv` de población (`many.py:36`). El paso 25 corre con `--strategy` y no escribe ese fichero (`report.py:36-45`). No hay camino por el que el paso 25 quite una estrategia de un databank.

### 5.8 Dos «2» en dos ficheros

El 2 de R5c vive en `criteria.yaml:93`; el del paso 25, en `ledger/thresholds.yaml:199`. Nada los ata.

### 5.9 La ayuda del comando

`report.py:23`: `--databank` es «the harvest's build databank name». En el paso 25 se le pasa `Stop_p90`, que no es un databank de SQX sino el nombre de la cosecha.

### 5.10 Lo que no está medido

- **El error del edge.** El estudio no lo da; las cifras de 3.5 son mías. Las rachas no lo agrandan en este tramo (2.5); lo que no recoge está en 5.12 a 5.14.
- **La diferencia emparejada con y sin stop**: el estudio no la calcula; la hizo el revisor (3.6). Lo que sigue sin medir es cuánto de esa caída es regresión a la media.
- **Cuánto se aparta `k*` de la realidad** cuando un coste mayor mueve el propio stop (2.4).
- **Cortos y comisión distinta de cero**: el repreciado los declara sin verificar contra SQX (`reprice.py:85-90`). Esta corrida es larga y sin comisión, así que no los prueba. Salidas por *profit target*: tampoco (`reprice.py:25`, `181`).
- **El edge en el `build` y en `oos2`** de la versión con stop: el estudio no los lee. `oos2` es tuyo y no lo he tocado.
- **Operaciones al año.** En `oos1` (cuatro años) las versiones con stop hacen de 18 a 53 al año; siete de diez, menos de 35. Tu suelo de 35 se mide en el `build` (R4a), no aquí; lo digo sólo porque es la razón de que el error de 3.5 sea tan ancho.
- **Una corrida hecha con el código de hoy.** No hay ninguna con paso 25 posterior al 2026-10-07. Todo lo de «código de hoy» es recálculo en memoria sobre la cosecha del 2026-10-04.

### 5.11 Dónde este documento corrige al encargo que lo pidió

El encargo pedía explicar el bruto como `Profit/Loss` + comisión + spread modelado, el edge «en spreads de hoy», media y mediana, y el `c*` con su fórmula. Están explicados (2.3, 2.4, 3.7), pero como **lo que había**: el código de hoy no hace ninguna de las cuatro cosas de esa manera. Y pedía respetar «factor 1,25, spread de Darwinex»: la ficha de hoy no lleva ni lo uno ni lo otro (3.2).

### 5.12 Las diez se eligieron mirando `oos1` (sesgo de selección)

Las madres salieron de las 3.148 que no fallaban el paso 8, todas con neto de `oos1` positivo (100 %, frente al 59,5 % de la población; calculado por el revisor). El edge mayor que 1 sin stop sale por construcción, el «9 de 10 por encima de 2» sin stop está inflado por lo mismo, y la versión con stop hereda parte. Con las reglas de hoy pasa igual y más fuerte: R5c exige ese mismo edge en ese mismo tramo (4.2). El paso 25 lee un tramo que ya se gastó en elegir. Cuánto infla, no está medido.

### 5.13 «5 de 10» no es un hecho, y las diez no son independientes

El recuento por encima de 2 va de 2 a 8 (95 %) remuestreando semanas; por encima de 1, de 4 a 9. Las diez comparten el 29 % de sus barras de entrada y sus netos semanales se correlacionan hasta 0,74 (calculado por el revisor). Diez estrategias de una familia sobre un índice son bastante menos que diez pruebas; cuántas «efectivas», no está medido.

### 5.14 El edge incluye la subida del índice, y `oos1` tiene un solo año malo

El NIKKEI pasa de 23.477 a 33.287 en `oos1` (+42 %; por años +17 %, +5 %, −11 %, +28 %; lo he comprobado con las barras M30). Edge conjunto de las diez con stop, por año: 2020 **2,95** · 2021 **3,20** · 2022 **−0,59** · 2023 **3,36** (calculado por el revisor). En 2022 ocho de las diez quedan por debajo de 1 y otra en 1,00. El paso 8 de aquel día sí midió el exceso sobre la deriva (`drift_excess_t`): de 0,15 a 2,06 en las diez, y sólo dos llegan a 1,65 (`10.11.484` y `3.11.426`). El paso 25 no descuenta nada: su bruto es el movimiento del precio entero. El remuestreo baraja operaciones o semanas dentro de esos cuatro años; no dice qué pasaría con otra secuencia de años. Es una advertencia, no una medida.

### 5.15 El coste es un supuesto calibrado, no una medida por operación

Spread y deslizamiento planos, iguales para todas las operaciones y para las salidas por stop (2.4). El estudio no lee el spread real de cada minuto ni distingue el coste de una salida por stop, que es donde la calibración del propio proyecto sitúa la cola.

### 5.16 Una o dos operaciones deciden

Tabla de 2.3: sin la mejor operación, dos de las ocho que ganan pasan a perder; sin las dos mejores, sólo tres de cinco siguen por encima de 2. El estudio no publica nada que lo deje ver (ni mediana, ni el peso de la mejor operación).

---

## 6. Cierre

### 6.1 Lo que hay, en una tabla

| pieza | hoy |
|---|---|
| qué se mide | bruto medio / coste medio pagado, por versión con stop |
| tramo | sólo `oos1` |
| costes | los de `oos1` de la ficha: spread + 2 × deslizamiento + swap + comisión |
| umbral | 2,0 (`ledger`), fijado cuando la unidad era el spread |
| acción | `mark`; y `drop` no tendría efecto |
| regla en `criteria.yaml` | ninguna |
| corte | ninguno, salvo «sin stop del paso 24, fuera» |
| error del número | no se calcula; de 1 a 3 unidades con 70-210 operaciones |

### 6.2 El resultado sobre la población real

Con el código de hoy: 5 de 10 por encima de 2, 4 por debajo de 1,25, 2 con neto negativo en `oos1`. Las diez irían a `finalistas.json`. Ese «5 de 10» va de 2 a 8 con otro `oos1` igual de válido (95 %, remuestreo por semanas; calculado por el revisor), las diez comparten el 29 % de sus barras de entrada, y se eligieron entre estrategias que ya ganaban en `oos1`: la cifra describe esta corrida, no mide el paso.

### 6.3 Las decisiones que te quedan

1. **¿El paso 25 corta, o sólo informa?** Hoy sólo informa, y dos versiones que pierden en `oos1` con el stop puesto siguen hacia MT5. *Si corta:* ganas no gastar la validación de MT5 en ellas; cuesta, en esta corrida, entre 2 y 5 de 10 según la línea (recuentos que con otro `oos1` irían de 1 a 6 y de 2 a 8), y hay que arreglar antes el extractor (5.5) y dar al paso un camino para borrar (5.7). *Si no corta:* no cuesta nada, y el número queda como una anotación que nadie está obligado a mirar.
2. **¿En qué unidad quieres el 2, y atado a qué?** Dejarlo en 2 veces el coste entero es, en el NIKKEI, pedir unos 4 spreads **de hoy** (3,5 a 4,5 según el swap); en dinero es casi lo mismo que confirmaste, porque el spread de la ficha bajó a la mitad desde entonces (18,3 frente a 18,9 puntos por operación; calculado por el revisor). Es decir: hoy el listón depende de dos cosas que se mueven solas, la definición del coste y la calibración de la ficha. *Fijarlo en múltiplos del coste* gana que acompaña a cada activo; cuesta que cada recalibración de costes lo mueve sin que lo decidas. *Fijarlo en otra unidad* (puntos, % del precio) gana estabilidad; cuesta una cifra por activo. En cualquier caso el nombre `min_edge_spreads` y su porqué en el ledger están desfasados.
3. **¿Una línea, o las tres del paso 8?** El 8 tiene Pasa / Limbo / Falla (2 y 1,25) y una t al lado. El 25 tiene una línea sola. Igualarlos *gana* coherencia y un Limbo donde hoy hay un sí/no sobre ruido; *cuesta* decidir qué se hace con un Limbo a un paso de MT5.
4. **¿Quieres el error al lado del número?** Hoy el estudio da 1,79 sin decir que podría ser −0,6 o 4,2. Pedir el número de operaciones y un intervalo *gana* no leer decimales que no existen; *cuesta* aceptar que, con un `oos1` de cuatro años, casi ninguna estrategia podrá demostrar por sí sola que supera el 2.
5. **¿Vuelve la mediana?** Se quitó con el encargo 44. *Gana:* ver de un vistazo si el resultado lo sostienen cinco operaciones (`14.3.479`). *Cuesta:* un segundo número que con stop sale negativo en casi todas las de tendencia y que hay que saber leer.
6. **¿Sobre qué tramo?** Sólo `oos1` es la decisión del encargo 44. Con `build` dentro habría el doble o el triple de operaciones y la mitad de error, pero `13.3.390` y `19.2.363` enseñan lo que eso tapa: su ventaja estaba en el `build`. *Mantener sólo `oos1`* cuesta precisión; *añadir el `build`* cuesta honestidad. Pero `oos1` tampoco está limpio: el paso 8 ya elige por este mismo número en este mismo tramo (4.2, 5.12), así que el 25 no confirma nada sobre datos nuevos; sólo mide lo que cambia el stop. El único tramo sin usar es `oos2`, que sigue reservado y es decisión tuya.
7. **¿Es el paso 25 quien debe decir que el stop hace daño?** La tabla 3.6 es más una pregunta para el paso 24 que una criba de estrategias. La cuenta emparejada, que el estudio no hace, dice que el stop daña de forma distinguible a dos de diez y que el conjunto baja 0,74 con un intervalo que roza el cero (calculado por el revisor). *Incorporarla* gana saber qué versiones empeoran de verdad con el stop; *cuesta* una segunda cosecha por madre (sin stop) y aceptar que con diez estrategias parecidas la respuesta de conjunto queda «al borde».

### 6.4 El límite que no cambia

El edge por coste es un cociente de medias sobre un centenar de operaciones con colas largas. Dice bien dos cosas: si la estrategia paga más de lo que saca (edge por debajo de 1) y, a grandes rasgos, si le sobra margen (5 no es 1,5). No distingue 1,8 de 2,2, con este tramo ni con uno el doble de largo. Ningún umbral arregla eso; sólo más operaciones. Y más operaciones del mismo tramo no arreglan lo otro: que el tramo ya se usó para elegir, que las estrategias se parecen, y que cuatro años con uno solo bajista no dicen cómo va una estrategia larga cuando el índice cae.
