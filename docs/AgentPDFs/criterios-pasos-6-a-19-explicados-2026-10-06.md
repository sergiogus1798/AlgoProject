# Los criterios del workflow, paso a paso: del build (6) a la Walk Forward Matrix (19)

**Fecha:** 2026-10-06 · **Para:** el dueño, que va a fijar los criterios él mismo · **Alcance:** pasos 6 a 19. Del 20 en adelante queda fuera a propósito.

**Qué es:** un documento de consulta. Para cada prueba del workflow dice qué se calcula, qué criterio dejó puesto la «avanzadilla» (el juego provisional del Council, cargado el 2026-10-04) y por qué, y cómo sería un resultado ideal. Los criterios se citan **tal como están hoy en disco** (`pipeline/autopilot/criteria.yaml` y `assets/_study.yaml`); donde el fichero no coincide con lo que acordó el Council, se dice en una línea.

---

## 0. Cómo leer este informe

### Los tres estados

Cada regla de `criteria.yaml` lee **un dato** de la estrategia (un «hecho», con nombre en `este formato`) y da uno de tres resultados:

| estado | qué significa | qué hace el workflow |
|---|---|---|
| **PASA** | cumple la línea exigente | sigue al paso siguiente |
| **LIMBO** | ni prueba ni condena: en observación | sigue al paso siguiente, **marcada** |
| **NO PASA** | claramente mala | se **borra** del databank que lee la siguiente tarea de SQX (el «corte» del paso) |

Tres detalles de la gramática que conviene tener presentes:

- El resultado de una estrategia es el de **su peor regla**. Una sola regla en NO PASA la saca.
- Un dato que **falta** es LIMBO, salvo que la regla diga otra cosa (`missing: fail`, por ejemplo).
- Un paso **sin reglas** deja pasar a todas.

Un aviso sobre el estado actual del fichero: el modo de desarrollo sigue encendido (`dev: on: true`, `sample: 3`, `at: ["8"]`). Mientras lo esté, en el paso 8 el piloto automático se queda con **3 estrategias sorteadas** entre las que superan las reglas, no con todas. Está pensado para probar el workflow, no para seleccionar; el propio fichero dice que se apaga (`on: false`) «cuando los criterios sean los de verdad».

### La idea central del Council

Sólo una prueba que lee **datos nuevos** puede dar un PASA con contenido. En el tramo que cubre este informe hay dos:

1. **Paso 8** — el tramo `oos1`, que el generador no vio.
2. **Pasos 10 y 12 juntos** — otros mercados y otros timeframes. Comparten el mismo calendario, así que cuentan como **una sola prueba conjunta**, no como dos.

(La tercera muestra nueva es `oos2`, en el paso 20, fuera de este informe.)

Todo lo demás —MC Retest, SPP, WFC, CSCV, superficies, WFM— **relee las mismas operaciones** de otra manera. Esas pruebas pueden matar una estrategia o dejar una anotación, pero no pueden «confirmar» nada: un PASA ahí se contaría como una segunda evidencia cuando no lo es. Por eso el Council las dejó en «sólo mata» (paso 14) o «sólo anota» (16 a 19). La votación final fue unánime en este punto.

### Los tramos de datos

```
XAUUSD y forex:   |---------- build ----------|---- oos1 ----|-- oos2 --|
                  2008                     2017 2018      2022 2023   2026
                        10 años                  5 años        3,75 años

NIKKEI225:        |-------- build --------|--- oos1 ---|- oos2 -|
                  2011-09              2019 2020    2023 2024  2026
                        8,3 años             4 años      2,75 años
```

`build` es lo único que ve el generador. `oos1` lo leen los pasos 7 a 16. `oos2` queda para el WFC, el CSCV, las superficies, la WFM y el paso 20.

### Glosario mínimo

- **Sharpe por operación (s):** beneficio medio por operación dividido por su dispersión. Mide cuánta señal hay por operación.
- **Estadístico t:** `media / desviación × √n`, o lo que es lo mismo `s × √n`. Dice a cuántos «errores estándar» está el beneficio medio de cero. Con t = 2,33, una estrategia sin ventaja sólo llegaría ahí por suerte 1 vez de cada 100 (en teoría); con t = 1,65, 5 de cada 100.
- **`drift_excess_t`:** la misma t, pero después de **restar a cada operación lo que el mercado se movió solo** mientras estuvo abierta (la deriva), y contando menos operaciones efectivas si están correlacionadas entre sí. Se resta la deriva porque un largo en un índice que sube gana aunque la entrada no valga nada: «los largos en índices ganan el 51 % de las veces con cualquier regla».
- **Tasa de falsos positivos:** de cada 100 estrategias **sin** ventaja, cuántas pasan la línea. Es lo que cuesta cada línea en basura admitida.
- **Potencia:** de cada 100 estrategias **con** ventaja real, cuántas pasan la línea. Es lo que cuesta en buenas perdidas.
- **LIMBO:** el estado intermedio de arriba. Según el Council, sólo lo resuelve una muestra nueva (pasos 10, 12 o 20); operar en real sólo puede matarlo, no promoverlo.
- **Profit factor (PF):** ganancias brutas divididas por pérdidas brutas. 1,0 = ni gana ni pierde.
- **«PF de suerte»:** el PF que una estrategia **sin ventaja** alcanza una vez de cada veinte sólo por azar. Depende de cuántas operaciones tiene: con pocas, el azar llega más alto.
- **R:** el riesgo por operación del sizing (1.000 USD en la doctrina). «−3R» es perder tres veces ese riesgo.
- **Percentil:** el p5 de una lista es el valor por debajo del cual queda el 5 % peor.
- **Intervalo de confianza (IC):** el rango donde, con un 95 % de seguridad, está el valor verdadero. Si el intervalo incluye el cero, no se ha demostrado nada.
- **z:** distancia de un resultado a la media de sus «monos» (entradas al azar), medida en desviaciones de esos monos. Se lee como la t.
- **`z_new`:** la z de una hermana en otro timeframe **después de quitar lo que ya explica su madre**. Si la madre tuvo suerte, la hermana la hereda; `z_new` descuenta esa herencia.
- **Número efectivo de mercados:** cuántos mercados independientes hay de verdad en una lista. Trece pares de divisas que se mueven juntos valen por unos cuatro o cinco.
- **PBO:** probabilidad de sobreajuste. De todas las maneras de partir la historia en dos mitades, en qué fracción el mejor juego de parámetros de una mitad queda por debajo de la mediana en la otra. Ruido puro da en torno a 0,5.
- **Persistencia / rho:** correlación de rangos (Spearman) entre lo bien que fue algo en un tramo y lo bien que fue en el siguiente. 0 = no se parece en nada; 1 = el orden se conserva entero.
- **Lift por cada 1.000:** de cada 1.000 estrategias que pasan un criterio en `oos1`, cuántas **más** acaban en positivo en `oos2` que entre las rechazadas, a igual número de operaciones. Es la medida de cuánto «enriquece» un criterio.

---

## 1. Paso 6 — El build en SQX: qué acepta el generador

### Qué se hace aquí

SQX genera estrategias con su búsqueda genética sobre el tramo `build` y guarda en el databank las que cumplen unas **condiciones de aceptación** («Ranking» de la tarea Build). Esas condiciones las escribe el builder desde `assets/_study.yaml`; no hay filtro por omisión, y si falta un valor para el activo o el timeframe el builder se niega. Sólo leen el tramo de construcción (in-sample): un filtro del build nunca lee OOS, porque seleccionar con él lo gasta.

El databank guarda como máximo 10.000 estrategias y un proyecto `Trade_` construye durante 180 minutos; lleno, una nueva entra sólo si mejora a la peor.

### Qué calculamos y qué resultado sale

Cuatro condiciones, todas sobre el in-sample:

- **Número de operaciones (`NumberOfTrades`)**, con suelo y techo. En el fichero se declaran **por año** y el builder los convierte a totales multiplicando por los años del `build` del activo. Ejemplo real: NIKKEI225 M30 tiene 8,28 años de build, suelo 13 y techo 75 por año, así que SQX recibe `108 ≤ NumberOfTrades ≤ 621`. En la corrida del 2026-10-04 las estrategias guardadas tienen entre 108 y 621 operaciones in-sample: la condición se cumple al 100 %.
- **Profit factor (`ProfitFactor`)** mínimo.
- **Beneficio neto (`NetProfit`)** estrictamente mayor que un valor.
- La muestra (`sample: IS`), que no admite otro valor.

Qué se sabe de este paso, medido en el proyecto:

- **Cualquier filtro de IS metido dentro del build da entre un 70 y un 98 % menos de estrategias robustas por minuto** que construir sin filtrar. Por ejemplo, con un suelo de 35 operaciones al año salen 5,4 robustas por minuto contra 32,4 del control; con PF ≥ 1,5 y Ret/DD ≥ 5, 0,6 contra 35,8. Poner el filtro dentro o aplicarlo después da lo mismo.
- El ruido entre dos corridas del genético (unos 16 puntos porcentuales) es mayor que el efecto de cambiar el objetivo de la búsqueda.
- Una población sin seleccionar conserva fuera de muestra, de mediana, el **45 %** de su Sharpe.
- El techo de 75 operaciones al año sí separa: por debajo las poblaciones dan entre 1,4 y 2,8 veces lo que da el azar; por encima, 0,41 veces.

### El criterio puesto y por qué

Lo que hay hoy en `assets/_study.yaml` (propuesta de agente del 2026-10-04, provisional):

| condición | valor en disco | por qué |
|---|---|---|
| operaciones/año, suelo | 10 (H1, M30, H4) · índices 13-16 · crudos 15 | sólo garantiza que haya estadística que leer; en índices y crudo sube porque su build es más corto y el total no debe bajar de unas 100 operaciones (Tharp: 100 o más) |
| operaciones/año, techo | 75 (H1, M30) · 100 (H4, «no recalibrado») | por encima de 75 las poblaciones rinden 0,41 veces el azar (medido) |
| PF in-sample | ≥ 1,0 | «sólo no perder» |
| beneficio neto in-sample | > 0 | ídem |

**No hay PASA en este paso**, y el paso 6 no tiene entrada en `criteria.yaml`: el piloto automático no lo juzga. La razón del Council es que el in-sample no puede probar nada: con 20 operaciones al año durante 10 años, una estrategia sin ventaja alcanza **PF 1,36** una vez de cada veinte; con 30 al año, 1,29; con 50, 1,21; con 75, 1,17. Un PF ≥ 1,0 «no significa nada» (Karpathy).

**Diferencia con lo que acordó el Council.** El Council puso el descarte en menos de 20 operaciones al año (15 en H4). En disco, el suelo **del build** es 10 (13-16 en índices): el corte en 20 no está en el generador sino en el paso 8, donde `gate.scorecard.is_trades_per_year` por debajo de 20 es NO PASA (15 en H4). El efecto final es el mismo; cambia dónde se gasta la CPU. El techo de H4 en el build es 100, no 75.

### Cómo sería el resultado ideal

Para una estrategia suelta no existe «resultado ideal» en este paso: nada de lo que se ve aquí es evidencia. Lo ideal es de la **población**:

- entre 35 y 75 operaciones al año (20-35 queda en LIMBO) y al menos 100 en total;
- PF in-sample por encima del PF de suerte de su frecuencia (≥ 1,29 a 30/año y ≥ 1,21 a 50/año con 10 años de build; con los 8,3 años de NIKKEI225 la línea sube algo: no medido), sabiendo que eso sólo dice «no es obviamente azar», no «tiene ventaja»;
- construida sin filtros apretados, que es lo que más robustas da por minuto.

Techo honesto: el único filtro de IS que se ha visto replicar es «Sharpe IS ≥ 0,6 aplicado después del build». Los builds largos (180 minutos, con el databank lleno) **no se han medido**.

---

## 2. Paso 7 — El retest en oos1

### Qué se hace aquí

Una tarea propia de SQX vuelve a correr todas las estrategias del build sobre el tramo `oos1`, **con los costes de ese tramo** (SQX sólo admite un spread y un slippage por backtest, y en años el precio cambia mucho; por eso build y retest son dos tareas y dos databanks). Desde el 2026-10-02 va a «timeframe elegido», no a un minuto.

### Qué calculamos y qué resultado sale

No se calcula ningún criterio. Sale un segundo databank (`OOS`) con las mismas estrategias y sus operaciones en `oos1`. Es la materia prima del paso 8, que casa los dos databanks por la identidad de la estrategia.

Un detalle con consecuencias: SQX puede **tirar** una estrategia del databank de retest por sus propias banderas rojas (demasiadas operaciones ambiguas, por ejemplo). Esa decisión se respeta: es la criba `presencia` del paso 8.

### El criterio puesto y por qué

Ninguno. El paso 7 no tiene entrada en `criteria.yaml` y el Council no lo trató: es una ejecución, no una prueba.

### Cómo sería el resultado ideal

Que la población llegue **sin seleccionar** por nada que mire `oos1`. Si las condiciones del build ya hubieran leído el fuera de muestra, todo el paso 8 se leería como inerte: medido sobre una población así, 229 de 231 ganaban fuera de muestra y el mono no mataba a nadie. Sobre una población sin seleccionar, las mismas cribas dejan 45 de 120.

---

## 3. Paso 8 — La puerta OOS en Python

### Qué se hace aquí

Python cosecha los dos databanks (build y OOS), calcula decenas de números por estrategia y el piloto automático aplica las reglas del paso 8 de `criteria.yaml`. El corte se aplica sobre el databank `OOS`. Los estudios que corren aquí son la puerta (`gate`), el edge por coste (`edgeCost`), el spread real (`spread`), el snooping (`snoopingScreen`), la calidad del feed (`feedQuality`) y, como lecturas adicionales, el mono (`monkey`), la forma del beneficio (`profitShape`) y la calidad de la entrada (`entryQuality`).

Hay que distinguir dos cosas que se llaman parecido:

- **La cascada propia de la puerta** (`studies/screening/gate/config.yaml`): ocho cribas en orden con umbrales **deliberadamente laxos** (tu decisión del 2026-09-23: «para ver cuánto mata cada una»). Da su propio veredicto, que el piloto automático **no usa**.
- **Las reglas de `criteria.yaml`**, que leen los números que deja la puerta (`gate.scorecard.*`) y son las que cortan.

Consecuencia práctica: los números de una criba sólo existen para quien llegó vivo a ella en la cascada. En la corrida de ejemplo, `forma_value` existe para 3.979 de 10.000 estrategias; a las demás esa regla les da LIMBO por dato que falta.

### Qué calculamos y qué resultado sale

Los ejemplos son de `Trade_NIKKEI225_M30_volatilidadL`, corrida del 2026-10-04: 10.000 estrategias con ficha de la puerta, `oos1` de 4 años.

**La estrategia de ejemplo, `Strategy 4.9.301`** (una de las dos que pasan todas las reglas de hoy):

| dato | valor |
|---|---|
| `gate.scorecard.drift_excess_t` | 2,54 |
| `gate.scorecard.trade_t` | 2,89 |
| operaciones/año en IS · en oos1 | 39,7 · 49,0 |
| operaciones en oos1 | 196 |
| neto oos1 según SQX · al spread real con slippage | 38.465 · 32.195 USD |
| PF en IS · en oos1 | 1,28 · 1,79 |
| `edgeCost.verdict_csv.edge_mean` | 7,6 |
| peor día · peor MAE de una operación | −2,21R · −2,62R |
| drawdown oos1 / drawdown IS | 0,54 |
| años de oos1 en positivo | 4 de 4 |
| concentración en el mejor trimestre | 0,21 |

Y el contraejemplo, `Strategy 8.4.275`: tiene la **mejor t de toda la población** (3,14), PF 2,61 en oos1 y un peor día de −1,78R, y es NO PASA porque opera 16,7 veces al año en IS (menos de 20) y sólo tiene 96 operaciones en oos1. Ojo: 3,14 es menos de lo que da el azar como máximo de 10.000 estrategias sin ventaja (≈ 3,7, cálculo del Council), y un PF de 2,61 con 96 operaciones es PF de suerte. No es una buena estrategia perdida: es el máximo de un sorteo.

**Los datos que leen las reglas:**

- **`gate.scorecard.presencia_passed`** — 1 si la estrategia sigue en el databank de retest. Si SQX la tiró, 0.
- **`gate.scorecard.sanidad_passed`** — 1 si tiene al menos 20 operaciones en oos1 y no es un clon de otra (su lista de operaciones no repite la de otra).
- **`gate.scorecard.estaticas_value`** — el beneficio neto en oos1 según SQX. Mediana de la población: +2.673 USD; 5.946 de 10.000 están en positivo.
- **`spread.verdict_csv.neto_con_slippage_real_oos`** — *(su regla, R2b, se retiró el 2026-10-06: comparaba con el spread de Darwinex anterior a la recalibración de costes del 2026-10-04; el dato se sigue calculando, ya no juzga)* el mismo neto, pero devolviendo el spread plano que cobró SQX y cobrando, operación a operación, el **spread real de Darwinex** en ese minuto, con el slippage real. Mediana: −1.672 USD; sólo 4.354 siguen en positivo. En este activo el spread plano de SQX quedaba en el percentil 10 del real: el coste verdadero es más alto que el del backtest, y el PF mediano baja de 1,06 a 0,97.
- **`gate.scorecard.drift_excess_t`** — la t de la operación media en oos1, descontada la deriva (ver glosario). Mediana de la población: −0,05; el 50 % central va de −0,71 a +0,60; máximo 3,14. Es decir, la población entera es indistinguible de cero y sólo la cola derecha interesa. 44 estrategias llegan a 2,33 y otras 281 quedan entre 1,65 y 2,33. Pero con tasas de falsos positivos del 0,6 % (2,33) y del 3,9 % (1,65), entre 10.000 estrategias sin ventaja cabría esperar unas 60 y unas 390 respectivamente, y esas tasas nulas están a su vez sobrestimadas de 2 a 4 veces: lo esperado por azar a 2,33 está entre 15 y 60. Las 44 (y las 325 de 1,65) no se distinguen del azar: la t enriquece la lista, no identifica ganadoras. Las dos que PASAN son candidatas, no hallazgos.
- **`gate.scorecard.trade_t`** — la t sin descontar la deriva (mediana +0,27, máximo 3,49). No la lee ninguna regla; está para comparar. La diferencia entre las dos es lo que el mercado regaló por subir.
- **`gate.scorecard.is_trades_per_year`** y **`gate.scorecard.oos_trades_per_year`** — operaciones al año en cada tramo. Mediana en IS: 30,8.
- **`spread.verdict_csv.operaciones_oos`** — operaciones en oos1. Mediana 155.
- **`edgeCost.verdict_csv.edge_mean`** — el beneficio **bruto** medio por operación (reconstruido como beneficio + comisión + coste del spread) dividido por el coste de ida y vuelta modelado hoy. Un 2 quiere decir que el bruto es el doble del coste, o sea, que la estrategia seguiría sin perder si el coste se duplicara. Mediana: 3,9.
- **`gate.scorecard.forma_value`** — peor caída en oos1 dividida por la peor caída en IS. Por debajo de 1, fuera de muestra cayó menos que dentro.
- **`gate.scorecard.degradacion_years_positive`** — cuántos años naturales de oos1 acabaron en positivo.
- **`gate.scorecard.degradacion_concentration`** — qué parte del beneficio de oos1 vino de su mejor trimestre. Por encima de 1, fuera de ese trimestre pierde.
- **`gate.scorecard.oos_worst_day_r`** — el peor día, flotante incluido, en R. Mediana −3,2R.
- **`gate.scorecard.oos_worst_trade_mae_r`** — la peor excursión en contra de una sola operación, en R. Mediana −3,7R. La doctrina no lleva stop, y este número es lo que eso cuesta.
- **`gate.scorecard.oos_dd_over_net_year`** — peor caída flotante dividida por el neto de un año: cuántos años de beneficio cuesta el peor bache. Vale infinito si el neto no es positivo.

**Los estudios que sólo anotan:**

- **El mono (trader al azar), `monkey.nulls_csv.p_*`.** Recoloca las operaciones de la estrategia al azar sobre las mismas barras, unas 2.000-2.500 veces, con los mismos costes, y mira en qué percentil queda la real. Tiene cuatro «peldaños» —al azar sólo el momento de entrar (`timing`), más la duración, más el tamaño, o todo (`free`)— y cinco estadísticos (neto, PF, Ret/DD, Sharpe, drawdown). Un p de 0,05 significa que sólo el 5 % de los monos lo hizo mejor. Mediana de `p_timing_sharpe` en la población: 0,28.
- **Corrección por búsqueda (FDR y snooping).** La criba `familia` de la puerta aplica Benjamini-Hochberg: de las que baten al mono, cuántas habría dado el azar. `snoopingScreen` pregunta otra cosa: descontada la búsqueda entera, ¿alguna bate a comprar y mantener a igual riesgo? La primera vez que se midió (XAUUSD, 115 estrategias), 4 tenían más Sharpe que el oro y el test no nombró a **ninguna**.
- **Forma del beneficio (`profitShape`).** Tres lecturas sobre la lista de operaciones: si el resultado sobrevive a quitarle sus mejores operaciones y su mejor año, si las operaciones son independientes entre sí, y si la media cambió en algún punto de la muestra.
- **Calidad de la entrada (`entryQuality`).** Sin mirar las salidas: si tras entrar el precio corre más a favor que en contra, más que una entrada al azar a las mismas horas (e-ratio), y cuánto se pierde por entrar unas barras tarde.
- **Calidad del feed (`feedQuality`).** Qué operaciones tocan una anomalía del histórico (picos, barras congeladas, huecos) y si esas operaciones ganan más de lo que tocaría por azar.
- **Redundancia.** Agrupa por la lógica de la estrategia (sus bloques, ignorando parámetros). Sólo entre el 52 y el 58 % de las supervivientes de la puerta son estructuras distintas.

En los hechos guardados de la corrida de ejemplo sólo aparecen `gate`, `edgeCost`, `monkey` y `spread`; de `snoopingScreen`, `feedQuality`, `profitShape` y `entryQuality` no hay hechos en ese fichero.

### El criterio puesto y por qué

Las reglas del paso 8 tal como están hoy. La columna «origen» distingue lo que puso el Council de lo que ya estaba (la propuesta de agente del 2026-10-04, que el Council **no examinó** regla a regla).

| regla (hecho) | PASA | LIMBO | NO PASA | origen |
|---|---|---|---|---|
| `presencia_passed` | = 1 | — | 0 o sin dato | previa |
| `sanidad_passed` | = 1 | — | 0 o sin dato | previa |
| `estaticas_value` (neto oos1) | > 0 | sin dato | ≤ 0 | previa; el Council la mantiene |
| ~~`neto_con_slippage_real_oos`~~ | — | — | — | **retirada el 2026-10-06** |
| `drift_excess_t` en M30 | ≥ 2,33 | 1,65 a 2,33 | < 1,65 | **Council** |
| `drift_excess_t` en H4 | ≥ 2,5 | 1,65 a 2,5 | < 1,65 | **Council**, «dudosa» |
| `drift_excess_t` en H1 | inalcanzable (`>= 1000`) | ≥ 1,65 | < 1,65 | **Council** |
| `is_trades_per_year`, suelo | ≥ 35 | 20 a 35 (H4: 15 a 35) | por debajo | **Council** |
| `is_trades_per_year`, techo | ≤ 75 (H4: ≤ 50) | H4: 50 a 65 | por encima | **Council** (H4: previa, «no recalibrado») |
| `oos_trades_per_year` | ≥ 15 | 10 a 15 | < 10 | previa |
| `operaciones_oos` | ≥ 100 | < 100 | nunca | **Council** |
| `edge_mean` | ≥ 2 | 1,25 a 2, o sin dato | < 1,25 | **Council** (banda del paso 25) |
| `forma_value` | ≤ 1,25 | el resto | nunca | previa, «no recalibrada» |
| `degradacion_years_positive` | ≥ 3 | el resto | nunca | previa |
| `degradacion_concentration` | ≤ 0,5 | hasta 1.000 | por encima de 1.000 (en la práctica nunca descarta) | previa |
| `oos_worst_day_r` | ≥ −3 | −3 a −5 | < −5 | previa |
| `oos_worst_trade_mae_r` | ≥ −3 | −3 a −5 | < −5 | previa |
| `oos_dd_over_net_year` | ≤ 1,5 | hasta 1.000 | infinito (neto ≤ 0) | previa |

**Por qué cada una de las del Council:**

**La t con deriva descontada (2,33 / 1,65).** Es la única prueba de la cadena con tasa de falsos positivos medida. Con estrategias sin ventaja, t ≥ 1,65 la pasa el **3,9 %** (5,8 % en la peor celda) y t ≥ 2,33 el **0,6 %** (1,1 % en la peor). Y es la que más enriquece: de cada 1.000 que pasan 1,65, 396 acaban en positivo en `oos2` contra 322 de las rechazadas; a igual número de operaciones, pasan de 322 a unas 374 (+52, IC de +24 a +83), porque la cifra bruta, 396, incluye lo que sólo se debe a que las que pasan operan menos; con 2,33, 481 contra 364 (**+103**, IC de +31 a +175, pero apoyado en sólo 18 celdas). Por eso 2,33 es la línea de PASA y por debajo de 1,65 se descarta.

**H1 como mucho en LIMBO.** El lift se reparte muy desigual por timeframe: +81 por cada 1.000 en M30 y **+19 en H1, que es prácticamente cero**. La persistencia de `oos1` a `oos2` cuenta lo mismo: 0,084 en M30 y 0,026 en H1, indistinguible de cero. El Council decidió que una H1 no puede PASAR sólo con el paso 8 y que la promueva una muestra nueva (pasos 10, 12 o 20). Se codificó con una línea de PASA inalcanzable. Munger pidió atarlo a la muestra nueva y no a la etiqueta del timeframe, porque el +19 no tiene intervalo publicado y el +81 de M30 descansa en pocas celdas.

**H4 a 2,5.** H4 es más ruidoso (peor celda: 8,9 % y 1,7 % de falsos positivos), y de ahí la línea más alta. El paquete de evidencia la da por dudosa y H4 no se ha recalibrado. La evidencia proponía 1,9 para el LIMBO de H4; en disco el LIMBO de H4 está en 1,65.

**Operaciones por año en IS (35 / 20 / 75).** Tu suelo de trabajo de 35 quedó como línea de PASA, **no de descarte**. Usado como descarte pierde el **81 %** de las estrategias robustas (51 % con suelo 20, 63 % con 25, 74 % con 30, 86 % con 40, 92 % con 50) sin mejorar nada. El descarte cargado hoy está en 20/año: pierde el 51 % de las robustas (63 % con 25, 74 % con 30) sin mejorar la calidad por operación. Bajar el suelo duro es una decisión tan válida como subirlo a 35. Además: las robustas que quita pasan `oos2` igual que el resto de su banda (17,1 contra 16,8 por cada 1.000). El coste del suelo está en el número de estrategias, no en su calidad. El suelo duro de 20 (15 en H4) viene de Tharp (100 operaciones como mínimo) y de que por debajo no hay estadística. El techo de 75 es el medido. Kahneman matizó que el suelo **no** es redundante con la t: con una ventaja pequeña y realista, la misma t vale la mitad con 20 operaciones al año que con 75. Disidencia que quedó: Munger dejaría pasar una estrategia de 20 a 35 al año si su t llega a 2,33; el resto la mantiene en LIMBO.

**Menos de 100 operaciones en oos1 = LIMBO.** Propuesta de Feynman: es un suelo de «legibilidad». Con menos de 100 el resultado no es negativo, es ilegible. Retiró su propuesta anterior de exigir 200, porque la t ya lleva dentro el número de operaciones.

**Edge por coste (2 / 1,25).** Kaufman: una estrategia que muere cuando el coste sube un 25 % no merece la cartera. Carver pediría 3 (costes no mayores que un tercio del bruto); el Council se quedó en 2 porque los costes del proyecto ya van inflados. Dos avisos: el lift medido de este criterio es sólo +34 («la prueba anota», Munger), y esta banda es la del paso 25 leída aquí porque `edgeCost` ya corre en el paso 8 — decisión del coordinador, no del Council. El comentario final del paso 8 en `criteria.yaml` sigue diciendo que el edge por coste va «sin regla»; la regla está unas líneas más arriba.

**El mono, sólo anotar.** Davey pide que al menos el 70 % de los monos lo haga peor. Lo medido aquí contradice que sirva para separar: pasar el mono al 5 % deja 301 ganadoras en `oos2` por cada 1.000 contra 296 de las que no lo pasan (lift +5). El Council se quedó con la medición.

**Las reglas previas que el Council no examinó.** R1, R2b (retirada el 2026-10-06), R5, R6-R8, R9 y el drawdown sobre neto anual vienen de la recalibración de agente del 2026-10-04 (116 celdas, 405.866 estrategias). R6, R7 y R8 se dejaron de modo que nunca descarten. Sobre R9 (el riesgo flotante) hay una objeción de Taleb en la primera ronda que no llegó al consenso final: con 175 operaciones la «regla de tres» sólo acota la probabilidad de una pérdida peor que la peor vista en 3/175 = 1,7 % por operación, así que el peor día y el peor MAE deberían anotar, no cortar. En disco siguen cortando por debajo de −5R.

**Lo que cuesta el juego de reglas, medido.** Aplicando hoy el fichero a los hechos guardados de NIKKEI225 M30 (11.548 identidades, de las que 10.000 tienen ficha de la puerta):

| | PASA | LIMBO | NO PASA |
|---|---|---|---|
| antes del Council | 2 | 3.742 | 7.804 |
| con las reglas de hoy | 2 | 167 | 11.379 |
| las mismas reglas si fuera H1 | 0 | 169 | 11.379 |

Hoy el fichero descarta el 98,5 % de esta población, frente al 734 por mil de la calibración: es bastante más estricto. En esta celda quedan 2 PASA y 167 LIMBO.

La regla de edge por coste no cambia el total: las que mata ya estaban muertas por otra regla. Por regla suelta, las que más descartan son la t (9.674 por debajo de 1,65), el neto al spread real (5.646) y el neto de SQX (3.912); el suelo de 20 operaciones al año descarta 2.241 y deja 3.557 en LIMBO entre 20 y 35.

### Cómo sería el resultado ideal

Una estrategia en **M30**, entre 35 y 75 operaciones al año, con:

- `drift_excess_t` ≥ 2,33 y al menos 100 operaciones en oos1 (mejor 200);
- neto positivo también al spread real;
- edge por coste ≥ 2 (≥ 3 si se sigue a Carver);
- peor día por encima de −3R (las robustas tienen de mediana entre −1,8R y −2,3R);
- todos los años de oos1 en positivo y concentración por debajo de 0,5.

El techo honesto es lo más importante de este informe:

- **Ninguna estrategia es significativa por sí sola.** La mejor t entre 118.235 estrategias fue 3,57; descontada la búsqueda harían falta unos 3,7. Para llegar a 3,7 con un Sharpe por operación de 0,15 hacen falta unas 609 operaciones: unos 12 años a 50 al año.
- **El paso 8 no puede llegar al 80 % de potencia con ninguna frecuencia permitida**: haría falta operar 89 veces al año y el techo es 75. Con 0,15 de Sharpe por operación y cinco años de oos1 (XAUUSD y forex), la potencia a t ≥ 2,33 es del 18 % operando 20 veces al año y del 50 % operando 50; con los cuatro años de NIKKEI225 la potencia es menor (≈ 16 % y ≈ 42 %, cálculo del Council) y harían falta unas 112 operaciones al año en vez de 89 para el 80 %.
- Y 0,15 es optimista: la dispersión medida de la ventaja real es de unos 0,02. Con una ventaja de 0,04 y 200 operaciones, la probabilidad de llegar a 2,33 es del 3,9 % (Kahneman).
- **Pasar no es validar.** El grupo PASA gana en `oos2` el 48 % de las veces; un 60 % de lo que pasa 1,65 acaba en negativo en `oos2`; y el neto por operación en `oos2` es negativo en todos los grupos (de −0,013R en PASA a −0,055R en NO PASA).

La frase del Council: la población queda **«enriquecida y dimensionada, no validada»** — a igual número de operaciones, pasa de 322 a unas 374 ganadoras por cada 1.000 (+52). La cifra bruta, 396, incluye lo que sólo se debe a que las que pasan operan menos.

---

## 4. Pasos 9 y 10 — Otros mercados

### Qué se hace aquí

El paso 9 retestea en SQX las supervivientes en los mercados que `assets/_markets.yaml` declara para el activo, cada uno en su ventana y con sus costes, **sin ninguna condición de aceptación** (con una viva, SQX no escribiría las que fallan y Python se quedaría sin la mitad de la evidencia). El paso 10 lo lee en Python. Los mercados se fijan antes de mirar ningún resultado y ninguno se descarta nunca.

Los mercados van en dos grupos: `family` (los parientes: los otros índices para un índice, los otros pares para un par) y `structural` (los lejanos). Para NIKKEI225 son 11: ocho de familia (siete índices y USDJPY, porque «yen débil y Nikkei al alza son el mismo trade») y tres estructurales.

### Qué calculamos y qué resultado sale

Por mercado, la misma `excess_t` del paso 8 (t con la deriva descontada), y a partir de ahí:

- **`crossmarket.verdict_csv.excess_t_pooled`** — todos los mercados leídos como **una sola prueba**: se suma por semanas el exceso de todos y se calcula la t de esa serie semanal. Dos mercados que son el mismo trade caen en las mismas semanas, así que su parecido ya está dentro de la dispersión y no hace falta suponer que son independientes.
- **`crossmarket.verdict_csv.excess_t_vs_main_half`** — el cociente «t en el mercado / t en el original» que alcanza **al menos la mitad** de los mercados. Si vale 0,5, la mitad de los mercados llega a la mitad de lo que hizo el original. No está definido si el original no es positivo.
- **`crossmarket.verdict_csv.excess_t_stouffer`** — la suma de las t dividida por la raíz del número de mercados. Supone que son independientes, y no lo son.
- **`crossmarket.verdict_csv.markets_effective`** — el número efectivo de mercados, sacado de las correlaciones semanales.
- Para leer: cuántos mercados ganan (`net_positive`), el PF mediano y el peor, y las mismas cuentas por grupo (`family_…`, `structural_…`).

Ejemplo real, las 10 estrategias que siguieron en la corrida de NIKKEI225. Ojo: eran un **sorteo al azar** del modo de desarrollo, no las mejores por t.

| | mínimo | mediana | máximo |
|---|---|---|---|
| `excess_t_pooled` | −6,19 | −2,93 | −1,28 |
| `excess_t_vs_main_half` | −10,39 | −1,14 | −0,11 |
| mercados en positivo (de 11) | 0 | 4 | 6 |
| PF mediano entre mercados | 0,80 | 0,96 | 1,06 |

La mejor de las diez, `Strategy 3.11.426`, traía una t de 2,05 en su mercado; fuera de él, la t conjunta es −1,28 y sólo 4 de 11 mercados ganan. Con las reglas de hoy, **las diez serían NO PASA**. Diez de diez tan negativas no parece mala suerte: sugiere que la t conjunta no está centrada en cero (costes, sesgo de la deriva). Hasta medirla con una población nula, la línea de 1,0 no debería usarse para descartar con confianza (cálculo del Council).

### El criterio puesto y por qué

| regla (hecho) | PASA | LIMBO | NO PASA |
|---|---|---|---|
| `excess_t_vs_main_half` | ≥ 0,5 | > 0, o sin dato | ≤ 0 |
| `excess_t_pooled` | ≥ 2,33 | 1,0 a 2,33 | < 1,0 |

Las dos del Council. Para pasar hacen falta ambas.

- **«La mitad de los mercados a la mitad del original»** la pasa entre el 0,4 y el 6 % de las estrategias sin ventaja con suerte. Es la formulación en grupo que pide Katz: con los mismos parámetros en una cesta, que fallen 1 o 2 de 9 es lo esperado, y la prueba es de conjunto, no un selector de mercados.
- **La t conjunta a 2,33** tiene unos falsos positivos del 0,7 % (Munger). Es además el único punto de la cadena donde se gana potencia de verdad: con transferencia completa sobre unos 4,4 mercados efectivos de forex la t esperada sería 5,0, y con media transferencia, 2,5 (Feynman). Por debajo de 1,0 se descarta.
- **Stouffer, prohibido como criterio.** Como los mercados no son independientes, «Stouffer ≥ 1,65» deja pasar entre el 5 y el 24 % de estrategias que no ganan nada.
- **Mercados efectivos.** Los 13 pares de forex valen por 4,1-4,7 mercados; los 7 índices, por 1,6-1,9; los 12-13 metales y crudos, por 3,0-3,6. Por eso Munger propuso que en índices se exigiera t conjunta ≥ 2,9 y que la prueba sólo anotara; **eso no está en disco**: la regla es la misma para todas las clases.

Dos notas neutras. Primera: el hecho `markets_effective` de la corrida de NIKKEI225 marca entre 9,2 y 10,1 sobre 11 mercados, lejos del 1,6-1,9 de la evidencia para los índices; son dos mediciones distintas y **no he podido conciliarlas**. Segunda: el código calcula además una versión «ciega» de la t (`excess_blind_t_pooled`), sin el sesgo por lado del término de deriva, y la señala como la adecuada para poner una línea; la regla de hoy lee la versión sin corregir.

### Cómo sería el resultado ideal

Una t conjunta ≥ 2,33 con al menos la mitad de los mercados a 0,5 veces el original o más, fallando como mucho 1 o 2 de 9, y que el resultado no dependa sólo del grupo de familia. En forex, donde hay mercados efectivos de sobra, una estrategia con ventaja real que se transfiere debería acercarse a una t de 2,5 a 5. Esas cifras suponen una ventaja de 0,15 por operación, que es optimista: con 0,04, la t conjunta esperada es 1,3 (transferencia completa) o 0,7 (media), así que una ventaja real y modesta cae en LIMBO o en NO PASA (< 1,0) (cálculo del Council).

Techo honesto: para índices, la evidencia da 1,6-1,9 mercados efectivos, pero la corrida de NIKKEI225 da 9,2-10,1. No están conciliadas: no se debe concluir todavía que la prueba aporte poco ni que aporte mucho en índices; y Kaufman recuerda que un especialista de un solo mercado puede ser legítimo. No hay tasa de falsos positivos medida para la combinación exacta de las dos reglas sobre una población nula que haya recorrido la cadena.

---

## 5. Pasos 10.5, 11 y 12 — Otros timeframes

### Qué se hace aquí

- **10.5:** de cada estrategia («madre») se fabrican **hermanas escaladas**: la misma lógica en otro timeframe con los periodos y las salidas por barras divididos por la razón entre timeframes (una media de 20 horas sigue siendo de 20 horas). Una madre M30 da hermanas en H1 y H4; una H1, en M30 y H4.
- **11:** SQX retestea cada timeframe en su propia tarea y su propio databank, sólo en `oos1`.
- **12:** Python lee cada celda contra los monos de su propio timeframe.

**Por qué D1 va aparte.** Desde H1, dividir por 24 mueve los parámetros entre un 140 y un 586 % y todos los periodos chocan con el mínimo del generador: la hermana D1 es otra estrategia. La doctrina la mantiene como tarea propia (motor MetaTrader 4, sin crosschecks), y la calibración del 2026-10-02 corrió sin ella por orden tuya («quítalo»). No entra en la lectura de este paso.

También se corre la madre **sin escalar** en el otro timeframe. Eso pregunta si el mercado se parece a sí mismo a otra escala, no dice nada de la estrategia y no se puntúa.

### Qué calculamos y qué resultado sale

- **`z`** de cada celda: su estadístico menos la media de sus monos, dividido por la dispersión de éstos. Contra una estrategia que no gana ni pierde, 1,65 y 2,33 son las líneas del 5 % y del 1 %.
- **`z_new`** de cada hermana: `(z − ρ × z_madre) / √(1 − ρ²)`, donde ρ es la correlación entre el beneficio mensual de la hermana y el de la madre. En llano: la hermana relee el mismo activo en los mismos años, así que se parece a su madre aunque no haya ventaja (ρ de 0,5 a 0,95 entre timeframes contiguos, de 0,3 a 0,7 con H4). `z_new` es lo que la hermana aporta **de nuevo**.
- **`crossTF.combined.z_new`** — la suma de las `z_new` de las hermanas utilizables de una madre, dividida por la raíz de cuántas son. Es el dato que lee la regla. Es una combinación tipo Stouffer: supone hermanas independientes entre sí y no lo son (comparten calendario). Su 2,33 no tiene tasa de falsos positivos medida; un PASA aquí no promueve por sí solo.
- **`crossTF.combined.n_tested`** — cuántas hermanas entraron en la suma.
- **`crossTF.reading.*`** — la lectura de cada hermana, una de seis: no escalable, muda (sin operaciones), sin datos (menos de 30 operaciones), sobrevive, heredada (ganó, pero no más de lo que su madre predice) o falla (perdió).

Ejemplo real, las mismas 10 madres: `z_new` combinada entre −2,81 y +1,72, mediana −0,05. La mejor, `Strategy 3.11.426`, da 1,72 con una sola hermana utilizable. Dos madres no tienen ninguna hermana utilizable y su dato falta. Ninguna llega a 2,33: **las diez quedan en LIMBO**.

### El criterio puesto y por qué

| regla (hecho) | PASA | LIMBO | NO PASA |
|---|---|---|---|
| `crossTF.combined.z_new` | ≥ 2,33 | todo lo demás, incluido el dato que falta | nunca |

Es del Council.

- **La z sin corregir no cuenta nunca.** Una hermana sin ventaja de una madre que tuvo suerte supera z = 1,65 entre el 17 y el 31 % de las veces, no el 5 %. Con `z_new`, entre el 2,7 y el 6,3 %.
- **Nunca descarta**, porque la prueba tiene poca potencia y es frágil: un 23 % de las hermanas H1→H4 y un 53 % de las M30→H4 llevan algún periodo recortado al mínimo, y el stop en H4 es físicamente el doble de ancho. Feynman: el mínimo de 30 operaciones equivale a un 20 % de potencia; es un suelo de estimabilidad, no una prueba.
- **Los pasos 10 y 12 son una sola actualización.** Leen los mismos años de calendario. El Council acordó contarlos como una prueba conjunta: «resuelve un LIMBO, no certifica» (Munger).

El Council manejó también una banda de LIMBO entre 1,65 y 2,33. En disco no hace falta: todo lo que no llega a 2,33 es LIMBO.

### Cómo sería el resultado ideal

`z_new` combinada ≥ 2,33 con las dos hermanas utilizables, sin periodos recortados y con más de 120 operaciones cada una (Feynman: con menos de 121, LIMBO). Para una H1 que llegó en LIMBO del paso 8, éste y el 10 son la vía de promoción.

Techo honesto: la lectura de este paso sigue marcada en su propio README como propuesta de agente pendiente de tu aprobación.

---

## 6. Pasos 13 y 14 — MC Retest

### Qué se hace aquí

A diferencia de un Monte Carlo que reordena operaciones ya hechas, aquí SQX **vuelve a correr el backtest entero** cientos de veces contra una entrada perturbada. La pregunta no es si la ventaja es real, sino **qué la rompe**. Son ocho tareas, cada una perturba una sola cosa (para poder atribuir el daño), todas leen la misma población y todas llevan la aceptación apagada.

| tarea | qué perturba | simulaciones | tramo |
|---|---|---|---|
| MCR 1 Bar | la barra en la que empieza el backtest (hasta 500 barras). Es el control, no una prueba | 200 | build |
| MCR 2 Spread | el spread, dentro del rango medido del activo | 200 | build |
| MCR 3 Slippage | el deslizamiento de cada ejecución | 200 | build |
| MCR 4 MinDist | la distancia mínima a la que el bróker deja poner una orden pendiente. Sólo se configura si hay órdenes stop o limit | 100 | build |
| MCR 5 Params | los parámetros de la estrategia, ±15 % | 500 | build |
| MCR 6 Exits | los parámetros de las salidas, ±30 %. Sólo si alguna estrategia lleva stop, objetivo, trailing o salida por barras | 500 | build |
| MCR 7 OHLC | el propio histórico: mueve apertura, máximo, mínimo y cierre de un 30 % de las barras, hasta un 15 % del ATR | 500 | build |
| MCR 8 Stress | las seis perturbaciones a la vez | 500 | build + oos1 |

En la corrida de ejemplo MCR 4 no corrió: todo va a mercado.

### Qué calculamos y qué resultado sale

De la tarea de estrés, «la cola»:

- **`mcRetest.stress.la_cola.profit_factor_p5.valor`** — el PF del 5 % peor de las 500 re-ejecuciones. Es decir: en 19 de cada 20 mundos perturbados, el PF fue al menos éste. Es el dato que lee la regla. Va con su intervalo (`.intervalo_95_desde`, `.hasta`).
- **`mcRetest.stress.la_cola.beneficio_p5.valor`** — lo mismo con el beneficio neto.
- **`mcRetest.stress.la_cola.drawdown_cvar.valor`** — la media del 5 % de peores drawdowns, en %. Es la caída que la cuenta tiene que poder aguantar.
- **`mcRetest.stress.la_cola.p_beneficio_0.valor`** — por el nombre, la fracción de re-ejecuciones que acaba en positivo (interpretación no comprobada en el código).
- **`mcRetest.stress.la_cola.operaciones_bajo_el_agua.valor`** — qué parte de las operaciones se pasa por debajo del máximo anterior.

El estudio da además sus propias notas (`mcRetest.verdict.data`, `.execution`, `.specification`, `.production` y una compuesta), que ninguna regla lee.

Ejemplo real, las 10 estrategias:

| | mínimo | mediana | máximo |
|---|---|---|---|
| PF p5 bajo estrés | 0,71 | 0,94 | 1,15 |
| beneficio p5 (USD) | −38.185 | −5.337 | +31.418 |
| drawdown CVaR (%) | 15,3 | 23,3 | 52,3 |

Cuatro tienen el PF p5 en 1,0 o más y seis no.

### El criterio puesto y por qué

| regla (hecho) | PASA | LIMBO | NO PASA |
|---|---|---|---|
| `mcRetest.stress.la_cola.profit_factor_p5.valor` | ≥ 1,0 | sin dato | < 1,0 |

Es del Council, y es **sólo para matar**: superarla no es evidencia, sólo «no está muerta». El corte se aplica sobre el databank «MCR 8 Stress», que es el que lee el SPP.

Por qué no hay un PASA con contenido:

- El criterio de los libros —Kaufman: aceptar si el 70 % o más de las pruebas son rentables— es **vacío** en este punto de la cadena. Feynman lo mostró así: una re-ejecución sale rentable con una probabilidad de aproximadamente Φ(t). Pedir un 70 % equivale a pedir t ≥ 0,52, y todo lo que llega aquí ya trae t ≥ 1,65, que da en torno al 95 %. Pasaría casi todo. Pero la regla cargada no es el 70 % de Kaufman: PF p5 ≥ 1,0 pide en la práctica que el 95 % de los mundos perturbados sean rentables. Mata a 6 de 10 en el ejemplo, así que sí discrimina, pero no se sabe cuántas sin ventaja sobreviven. Tampoco se sabe cuántas estrategias con ventaja mueren aquí: matar también tiene coste, y no está medido.
- Taleb: remuestrear no puede crear una cola peor que la de la propia muestra; un PASA sin capacidad de discriminar «es una etiqueta sin contenido» y alguien acabará dimensionando sobre ella.
- Karpathy retiró en la ronda final su convención de PASA (PF mediano bajo perturbación ≥ 0,7 veces el nominal) hasta que una población nula haya corrido la prueba.

Lo que el Council quería matar además y **no está expuesto como hecho**: la retención bajo peor ejecución (descartar si conserva menos de la mitad). Tampoco hay ninguna tasa de falsos positivos medida para este paso.

### Cómo sería el resultado ideal

PF p5 bajo estrés claramente por encima de 1,0, con el extremo bajo de su intervalo también por encima; beneficio p5 positivo; y un drawdown CVaR que quepa en la cuenta. Como referencia de tamaño: el drawdown del percentil 95 reordenado es de mediana 1,95 veces el del backtest, así que el doble cubre sólo a la mitad de las estrategias (1,95 es una mediana); Kaufman capitaliza con 3 veces el máximo drawdown.

Techo honesto: en la muestra de ejemplo, 6 de 10 estrategias sorteadas al azar mueren aquí. No se sabe cuántas estrategias **sin** ventaja sobrevivirían: no medido.

---

## 7. Pasos 15 y 16 — SPP

### Qué se hace aquí

SPP son las siglas de System Parameter Permutation. SQX mueve **todos los parámetros a la vez**, al azar dentro de ±35 % de su valor (en pasos del 4 %), y corre hasta 15.000 combinaciones. Hay dos tareas: una sobre `build` (SPP IS) y otra sobre `oos1` (SPP OOS), con la aceptación apagada para que el perfil sea un mapa y no un filtro. El paso 16 lo lee y, además, deja escrito el diseño con el que el paso 16.5 fabrica las variantes.

### Qué calculamos y qué resultado sale

- **Los percentiles de la rejilla, `spp.panel1.<métrica>.p1 … p99`**, con `.median` y `.real` (el backtest original), para beneficio neto, PF, retorno/drawdown, drawdown máximo, Sharpe y Sortino. Dicen dónde cae la estrategia real dentro de su propia vecindad de parámetros. Si la real está muy por encima de la mediana, se eligió un pico.
- **`spp.panel2.*`** — lo mismo comparando IS con oos1, sólo en métricas que no crecen con la longitud de la ventana (PF, Sharpe, Sortino, R/edge).
- **`spp.verdict.score`** — cuánto supera el mejor punto de la rejilla a lo que daría el mejor de N tiradas de puro ruido (`σ × √(2 ln N)`). Por encima de 1, la rejilla contiene algo más que ruido. Supone N tiradas independientes cuando los vecinos están correlacionados, así que sobrestima: «score ≥ 1 y las diez pasan» no es una señal fiable.
- **`spp.verdict.area_de_meseta`** — qué parte de la rejilla queda cerca del mejor nivel. Cerca de 1 es una zona ancha y estable.
- **`spp.verdict.max_mediana_iqr`** — cuánto sobresale el mejor punto, en rangos intercuartílicos. Alto = pico aislado.
- **`spp.verdict.tuplas_distintas_n_eff`** — cuántas combinaciones realmente distintas hay (los parámetros inertes duplican puntos).

Ejemplo real, las 10 estrategias: PF real de mediana 1,48 contra 1,37 de la mediana de su rejilla; p5 del PF de la rejilla, 1,005 de mediana; área de meseta entre 0,23 y 1,00 (mediana 0,96); `score` entre 1,3 y 19,3; unas 11.500 combinaciones distintas de 15.000. El veredicto propio del estudio (`spp.verdict.pass`) da 1 a las diez.

### El criterio puesto y por qué

**Ninguna regla** (`rules: []`). El paso corta sobre «SPP OOS» pero, sin reglas, pasan todas.

El Council lo quiso como prueba de **sólo descarte**, con dos condiciones:

- una «solución pico»: el rendimiento cae en todas las direcciones al mover los parámetros (Kaufman);
- la media de la rejilla menos una desviación típica es negativa (Kaufman: se debe esperar la media de la rejilla, o la media menos una desviación, nunca la mejor celda).

**Ninguna de las dos está expuesta como hecho**, así que no se pudo escribir la regla. Los datos más cercanos que sí existen son los percentiles bajos del beneficio (`spp.panel1.net_profit.p5`, `.p10`) y `spp.verdict.max_mediana_iqr`, pero no son lo mismo y nadie los ha calibrado.

Por qué no hay PASA: el criterio de Kaufman (70 % o más de combinaciones rentables) lo contradice el contraejemplo de Katz —todos los juegos de parámetros rentables dentro de muestra y ninguno fuera— y la conclusión es que **una meseta no es robustez**. Además el «% de vecinos rentables» es bimodal, porque los vecinos están correlacionados, y aporta poca información. El Council se puso del lado de las mediciones contra el 70 % de Kaufman.

### Cómo sería el resultado ideal

La estrategia real cerca de la mediana de su rejilla (no en la cola alta); p5 y p10 del beneficio positivos; área de meseta cerca de 1 y un `max_mediana_iqr` bajo; y la misma imagen en IS y en oos1.

Techo honesto: dos corridas de SPP no se pueden emparejar punto a punto (medido: IS y OOS comparten 6 combinaciones de unas 11.600), así que aquí no se compara una ventana con otra. Para eso existen las variantes del paso 16.5.

---

## 8. Pasos 16.5 y 17 — Variantes y Walk Forward Correlation (WFC)

### Qué se hace aquí

- **16.5:** con el diseño que dejó el SPP se fabrica un lote de variantes de la madre (la misma estrategia con otros parámetros) y SQX las retestea en tres tareas: `build`, `oos1` y `oos2`. Ahora sí hay los mismos puntos medidos en las tres ventanas.
- **17:** el WFC pregunta: **¿lo que optimiza bien dentro de muestra predice lo que va bien fuera?** Un punto por variante: beneficio dentro contra beneficio fuera.

Desde el paso 16 en adelante, todas las supervivientes pasan por 16.5 a 19 sin filtrar.

### Qué calculamos y qué resultado sale

- **rho de Spearman** entre el orden de las variantes dentro de muestra y su orden fuera, **con su intervalo de confianza al 95 %**. Lo que importa es el intervalo, no el coeficiente: con pocas variantes distintas el error es enorme.
- **La llamada**, una de tres: `fiable` (el intervalo entero por encima de 0,30), `no_fiable` (entero por debajo) o `indeciso` (lo cruza; es el caso habitual, y significa «faltan puntos», no «baja el umbral»).
- **Persistencia de la cabeza:** de las variantes en el mejor 20 % del build, cuántas siguen en la mejor mitad fuera. Por azar sería la mitad; se publica el exceso. Calculado y mostrado, sin umbral.

Una nube que llena los cuatro cuadrantes dice que optimizar dentro no compra nada fuera; una nube sobre la diagonal dice que la superficie lleva información.

No hay hechos de este paso en las corridas consultadas.

### El criterio puesto y por qué

**Sólo anota.** No hay regla en `criteria.yaml` y, aunque se escribiera, el piloto automático no juzga los pasos 17 a 19: los ejecuta como tres lecturas «a ciegas» que alimentan el paso 20.

El corte que ya existía —el extremo bajo del intervalo por encima de 0,30 (`rho_floor: 0.30`)— **no lo tocó el Council**, pero lo calificó: es más estricto que cualquier cosa observada. La persistencia medida de la población entre `oos1` y `oos2` es **0,06** (intervalo de 0,035 a 0,084); 0,026 en H1 y 0,084 en M30; Katz da 0,15 entre el IS y el OOS de un mercado. Karpathy propuso bajar la línea a 0,15 y lo retiró en la ronda final: sin una población nula recorriendo la prueba, cualquier línea es una convención, y «un PASA por convención se cuenta como confirmación» (Kahneman).

### Cómo sería el resultado ideal

Un intervalo entero por encima de 0,30 (`fiable`) y el mismo signo en las dos composiciones (build contra oos1, y build + oos1 contra oos2).

Techo honesto: no se sabe con qué frecuencia saldrá `fiable`; la persistencia poblacional de 0,06 mide otra cosa (estrategias distintas, no variantes de una misma madre) y sólo sirve de referencia aproximada.

---

## 9. Paso 18 — CSCV y PBO

### Qué se hace aquí

El CSCV (de Bailey, Borwein, López de Prado y Zhu) no pregunta por esta historia en concreto, sino por **la manera de elegir parámetros**: ¿es propensa al sobreajuste? Lee el mismo lote de variantes del 16.5, con sus rendimientos diarios.

### Qué calculamos y qué resultado sale

- La historia se corta en **16 bloques** y se forman las 12.870 maneras de repartirlos en dos mitades. En cada reparto se elige la mejor variante de una mitad (por Sharpe) y se mira en qué puesto queda en la otra.
- **PBO** = la fracción de repartos en los que la elegida quedó **por debajo de la mediana** fuera. 0 % sería que elegir siempre acierta; 50 % es lo que da el azar.
- Se calcula **una vez por regla de elección**. La respuesta útil no es «esta estrategia decae» sino, por ejemplo, «elegir el centro de la meseta en vez del máximo baja el PBO del 30 al 4 %».
- La **pendiente agregada**: sobre todas las variantes, cuánto del orden dentro se traslada fuera.

Una trampa: el panel de «decaimiento» por punto elegido da pendiente negativa **por construcción** (las dos mitades son complementarias) y más negativa cuanto más real es la ventaja. Hay que leer la pendiente agregada, nunca ese signo.

### El criterio puesto y por qué

**Sólo anota.** Sin regla, y el piloto automático no lo juzga.

La razón es una medición: **el PBO de ruido puro tiene una desviación típica de 0,21**. Las particiones se solapan mucho y no son, ni de lejos, 12.870 observaciones independientes. Una rejilla con PBO 0,45 y otra con 0,55 no se distinguen.

Las líneas que se propusieron y no prosperaron: PASA con PBO ≤ 0,15 y NO PASA con ≥ 0,71 (Karpathy, retirado); «sólo informa por debajo de 0,08» (Kahneman, que es 0,5 menos dos desviaciones). Feynman: «no sé explicar qué certifica un PBO ≤ 0,15», y además está correlacionado con el paso 8.

### Cómo sería el resultado ideal

No hay un PBO ideal certificable: sólo por debajo de 0,08 (0,5 menos dos desviaciones del ruido) se separa del azar, y aun así es ausencia de señal de alarma, no prueba. Entre 0,08 y 0,92 no se distingue del azar. Importa la comparación entre reglas de elección, no el valor absoluto. Además, la pendiente agregada debe ser claramente positiva.

Techo honesto: el CSCV **rompe la cronología a propósito**. Juzga el procedimiento de selección, no dice si la estrategia funcionará hacia delante.

---

## 10. Paso 18.5 — Superficies por mercado

### Qué se hace aquí

Que una estrategia gane en otro mercado es evidencia débil: puede estar simplemente larga de un activo correlacionado. Que **la misma región de parámetros** sea la buena en dos mercados no lo es: la suerte de un backtest no produce eso. Este paso toma el lote de variantes, ya retesteado en los mercados de `_markets.yaml`, y compara las superficies. No lanza ningún backtest y lee `build` y `oos1`.

### Qué calculamos y qué resultado sale

Entre cada par de mercados:

- **rho** — Spearman entre el orden de las variantes en un mercado y en el otro: ¿se ordenan igual?
- **`rho_neutral`** — el mismo, quitando a cada mercado el efecto de la exposición. En largo, el beneficio es en parte «tiempo en mercado × deriva», y dos mercados que derivaron distinto ordenan las variantes sólo por cuánto tiempo están dentro. La llamada se hace sobre éste (tu decisión del 2026-09-29).
- **J (Jaccard del decil superior)** — de las mejores variantes de cada mercado (el 10 %), qué parte coincide.
- La **región**: la meseta detectada en el activo principal, llevada tal cual a cada mercado, con el rendimiento dentro contra fuera.

Sólo entre el 36 y el 45 % de las variantes de un lote dan un resultado distinto: las filas no son observaciones.

### El criterio puesto y por qué

**Sólo anota.** El Council no le dio banda; lo trató dentro del bloque 16-19.

Los umbrales del propio estudio son previos y el Council no los examinó: rho por encima de 0,30 (por debajo, dos órdenes comparten menos del 9 % de su varianza), el Jaccard por encima del percentil 97,5 de dos órdenes independientes, y que se cumpla en al menos **la mitad** de los mercados declarados. Este último figura como provisional hasta que tú lo fijes.

### Cómo sería el resultado ideal

`rho_neutral` por encima de 0,30 y Jaccard significativo en más de la mitad de los mercados, en los dos tramos, con la región del activo principal siendo buena también fuera de él.

Techo honesto: con seis parámetros vivos y unas 500 variantes, la meseta del activo principal suele reducirse a la propia estrategia original, y entonces la tabla de la región no dice nada.

---

## 11. Paso 19 — Walk Forward Matrix (WFM)

### Qué se hace aquí

SQX reoptimiza la estrategia sobre una ventana que se desliza y corre cada elección sobre el tramo siguiente, que no vio. Lo repite para 30 combinaciones de **cuántas pasadas** y **qué porcentaje de cada pasada va fuera de muestra**:

```
                 % de cada pasada fuera de muestra
 pasadas      20 %    25 %    30 %    35 %    40 %
    6          ·       ·       ·       ·       ·
    8          ·       ·       ·       ·       ·
   10          ·       ·       ·       ·       ·
   12          ·       ·       ·       ·       ·
   14          ·       ·       ·       ·       ·
   16          ·       ·       ·       ·       ·
```

La ventana es `build..oos2` entera (en XAUUSD, 18,7 años), cobrada al coste de `oos1`. Es el último paso que mira datos.

### Qué calculamos y qué resultado sale

**Dentro de SQX**, en cada casilla se evalúan diez condiciones de cuatro familias:

- **`oos`** — el resultado de juntar todas las pasadas fuera de muestra. Es el dinero de verdad.
- **`stability`** — la métrica fuera dividida por la misma dentro, en %. 100 = fuera rinde igual que dentro.
- **`score`** — la WFM entera contra el backtest original: ¿reoptimizar mejora o estropea?
- **`special`** — cómo se reparte el resultado entre pasadas.

Una casilla aprueba si cumple el 80 % de las condiciones. Luego se busca un rectángulo de 4×4 casillas con al menos 12 aprobadas.

**En Python** (`studies/optimisation/wfm/`):

- **rho por casilla** entre lo bien que optimizó cada pasada y lo bien que fue después, con su intervalo sobre las casillas.
- **La llamada**: `predicts` (el intervalo entero por encima de cero), `blind` (cruza el cero: el orden dentro de muestra no dice nada) o `perverse` (entero por debajo: lo que optimiza mejor va peor después).
- La **deriva de parámetros**: cuánto cambia el optimizador de una pasada a la siguiente. En la primera lectura, rehacía entre el 70 y el 78 % de los parámetros en cada pasada.

### El criterio puesto y por qué

**En `criteria.yaml`: sólo anota**, sin regla, y el piloto automático no lo juzga.

**Pero la WFM es hoy un corte activo dentro de SQX**, y conviene tenerlo presente porque es la excepción a «el veredicto se toma en Python». La tarea lleva las diez condiciones encendidas, con `threshold_pct: 80`, `grid_passing_size: 4` y `min_squares: 12`: la estrategia que no encuentra el rectángulo **no se escribe en el databank de salida**. Las condiciones son previas al Council (calibradas el 2026-09-24 sobre las 150 casillas de 5 estrategias del maestro; con ellas, 2 de 5 encontraban el área) y el Council no las examinó. Para volver al modo mapa basta `min_squares: 0`.

Por qué el Council la dejó en anotar:

- **Las 30 casillas no son 30 pruebas.** Todas reparten la misma historia; valen por entre **1,6 y 3 curvas independientes**. Un «12 de 16» suena a mucho y es muy poco.
- **Una estrategia que SQX había dado por buena tenía un rho IS→OOS de −0,49**: lo que optimizaba mejor iba peor después.
- Ningún libro del dossier da un umbral de eficiencia walk-forward ni de número de pasadas. Kaufman sólo avisa de que un óptimo que salta de ventana en ventana es la señal de alarma, y de que repetir el walk-forward gasta el fuera de muestra.

Lo único que el Council aceptó como señal de descarte (Karpathy, Munger, Feynman) es el rho negativo, la lectura `perverse`. No está en ninguna regla.

### Cómo sería el resultado ideal

Lectura `predicts` en Python; un área 4×4 con 12 o más casillas aprobadas; beneficio fuera de muestra positivo en la mayoría de las casillas; y poca deriva de parámetros entre pasadas.

Techo honesto: con 1,6-3 curvas independientes, incluso el resultado ideal es una evidencia pequeña. Y la tarea termina en `oos2`: lo que se lea aquí ya ha mirado el último tramo.

---

## 12. Lo que falta por medir antes de fijar nada

La primera línea del bloque de pasos en `criteria.yaml` lo dice: provisional, **no congelar antes de que una población nula haya corrido la cadena**. Tres mediciones pendientes, todas pedidas por el Council:

1. **Una población nula por los pasos 14 a 19.** Unos 1.100 «monos seleccionados»: sistemas de entrada al azar, elegidos con la misma métrica que las estrategias de verdad y pasados por la cadena. Un mono sin seleccionar sólo da una cota inferior de los falsos positivos. Con 1.100 entrando en un paso se mide una tasa del 1 % con ±0,3 % de error típico (≈ ±0,6 % al 95 %). Si más del 90 % de los nulos pasa una prueba, esa prueba es vacía (Feynman). Hoy **no hay ninguna tasa de falsos positivos medida** para los pasos 14 a 19.
2. **Una ventaja plantada de 0,04.** Todas las cifras de potencia suponen un Sharpe por operación de 0,15, que es 7,5 veces la dispersión medida de la ventaja real (0,02). Hay que plantar una ventaja de 0,04 en estrategias sintéticas y ver cuántas pasa cada línea, antes de congelar ninguna banda (Kahneman).
3. **Un bootstrap del lift de H1 y de M30**, con sus intervalos. Si el intervalo de H1 incluye el cero, la regla de H1 queda zanjada; si no, hay que quitar la línea inalcanzable (Karpathy).

Tampoco está medido: H4 (sin recalibrar), los builds largos, y la corrección del sesgo por lado del término de deriva (medida, quita cerca del 60 % del sesgo, **no aplicada**: desplaza la t sin ventaja entre ±0,02 y ±0,27; en EURUSD H1 a 1,65 deja pasar un 2,6 % de largos contra un 5,8 % de cortos).

### Decisiones que puedes tomar ya, con su coste al lado

| decisión | lo que se gana | lo que cuesta |
|---|---|---|
| **Apagar el modo de desarrollo** (`dev: on: false`) | el paso 8 deja pasar a todas las que superan las reglas, no a 3 sorteadas | más CPU en los pasos 9 a 19 |
| **Línea de PASA del paso 8: 2,33 o 1,65** | a 2,33: falsos positivos 0,6 % y lift +103 (apoyado en sólo 18 celdas, IC +31 a +175); a 1,65: 3,9 % y +52 (más sólido, IC +24 a +83) | en NIKKEI225 M30, 44 estrategias llegan a 2,33 y 325 a 1,65, de 10.000: no se distinguen del azar (esperables 15-60 y unas 390 por azar) |
| **El suelo de 35 operaciones/año: PASA o descarte** | como descarte no se gana nada medible (17,1 contra 16,8 por cada 1.000 en oos2) | como descarte, el 81 % de las robustas; como línea de PASA (lo de hoy), ninguna: van a LIMBO. El descarte cargado hoy está en 20/año: pierde el 51 % de las robustas (63 % con 25, 74 % con 30) sin mejorar la calidad por operación; bajar el suelo duro es una decisión tan válida como subirlo a 35 |
| **Dejar pasar de 20 a 35/año si t ≥ 2,33** (Munger) | recupera estrategias de 20 a 35/año con t alta, si además se baja el suelo | la misma t vale menos con pocas operaciones (Kahneman) |
| **H1 como mucho LIMBO** | no se da por buena una clase cuyo lift es +19 ≈ 0 | ninguna H1 puede PASAR en el paso 8; depende del bootstrap pendiente |
| **Mantener el paso 10 como corte** | falsos positivos del 0,4-6 % y del orden del 0,7 % | en la muestra sorteada de NIKKEI225, las 10 de 10 caen; en índices hay menos de 2 mercados efectivos |
| **Mantener el paso 14 como corte** | quita lo que pierde en el 5 % peor de los mundos perturbados | 6 de 10 en la muestra; falsos positivos no medidos |
| **Edge por coste ≥ 2 en el paso 8** | lift +34; margen ante un error de costes | en NIKKEI225 M30 no cambia el total: las 653 que mata ya estaban fuera |
| **La WFM: corte en SQX o mapa** (`min_squares: 0`) | en mapa, Python ve también las que fallan | el corte de hoy no tiene tasa de falsos positivos medida y las 30 casillas son 1,6-3 curvas |
| **R9 (peor día y peor MAE por debajo de −5R): cortar o anotar** | cortar protege del límite diario del 5 % de una cuenta de fondeo | en NIKKEI225 M30 descartan 841 y 1.712; 175 operaciones no pueden acotar la peor pérdida (Taleb) |

«Esto apenas ayuda» también es una decisión válida, y aquí aplica a tres cosas: el mono como filtro (lift +5), el suelo de 35 como descarte, y cualquier PASA en los pasos 14 a 19.

---

## 13. Resumen en una tabla

| paso | prueba | estadístico que manda | criterio en disco | estado del cableado |
|---|---|---|---|---|
| 6 | build en SQX | operaciones/año, PF y neto in-sample | 10-75 operaciones/año (índices desde 13-16; H4 hasta 100), PF ≥ 1,0, neto > 0 | cargado en `assets/_study.yaml`; el piloto no lo juzga; sin PASA |
| 7 | retest oos1 | — | ninguno | es una ejecución |
| 8 | puerta OOS | `gate.scorecard.drift_excess_t` | PASA ≥ 2,33 en M30 (H4 2,5; H1 nunca), LIMBO ≥ 1,65; más 17 reglas | cargado; modo de desarrollo encendido (3 sorteadas) |
| 8 | frecuencia | `gate.scorecard.is_trades_per_year` | PASA 35-75, LIMBO 20-35, fuera lo demás | cargado |
| 8 | edge por coste | `edgeCost.verdict_csv.edge_mean` | PASA ≥ 2, LIMBO ≥ 1,25 | cargado |
| 8 | mono, FDR, snooping, forma, entrada, feed | p del mono y otros | ninguno | sólo anota |
| 10 | otros mercados | `crossmarket.verdict_csv.excess_t_pooled` y `excess_t_vs_main_half` | PASA ≥ 2,33 y ≥ 0,5; fuera < 1,0 o ≤ 0 | cargado |
| 12 | otros timeframes | `crossTF.combined.z_new` | PASA ≥ 2,33; lo demás LIMBO | cargado; nunca descarta |
| 14 | MC Retest | `mcRetest.stress.la_cola.profit_factor_p5.valor` | fuera si < 1,0 | cargado, sólo mata; retención bajo peor ejecución sin exponer |
| 16 | SPP | media de la rejilla − 1 desviación; solución pico | ninguno | sin métrica expuesta |
| 17 | WFC | rho y su intervalo | ninguno (el corte previo de 0,30 no se aplica) | sólo anota; el piloto no lo juzga |
| 18 | CSCV | PBO | ninguno | sólo anota; el piloto no lo juzga |
| 18.5 | superficies | `rho_neutral`, Jaccard | ninguno | sólo anota |
| 19 | WFM | rho por casilla; área 4×4 | ninguno en `criteria.yaml` | sólo anota en Python; **corte activo dentro de SQX** |

**Fuentes:** `pipeline/autopilot/criteria.yaml`, `assets/_study.yaml`, `assets/_build.yaml`, `assets/_markets.yaml`, los README de cada estudio en `studies/`, los hechos de `AlgoData/autopilot/Trade_NIKKEI225_M30_volatilidadL/` (corridas `20261004-154759` y `20261004-163510`) y la deliberación del Council del 2026-10-04 con su paquete de evidencia.
