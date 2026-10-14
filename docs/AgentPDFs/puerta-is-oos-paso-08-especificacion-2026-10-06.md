# Paso 8 — La puerta IS/OOS: especificación completa del rediseño

**Fecha:** 2026-10-06 · **Para:** el dueño · **Alcance:** sólo el paso 8 · **Sustituye a:** `criterios-implementados-2026-10-12`, que describía las 16 reglas anteriores.

**Qué es:** el documento de referencia de la puerta tal como quedó decidida en tu revisión del 2026-10-06. De cada regla dice qué pregunta contesta, cómo se calcula paso a paso, qué significa cada estadístico, un ejemplo, sus líneas de Pasa / Limbo / Falla, sus parámetros, lo que cuesta calcularla y lo que falta por medir antes de congelar su línea. Después explica el orden de cálculo (la cascada), las dos poblaciones de prueba, la tabla de parámetros, lo que se quita, lo que pasa al módulo de fondeo y lo que queda por decidir.

**De dónde salen los números.** Los ejemplos con las estrategias A, B y C son de la corrida `Trade_NIKKEI225_M30_volatilidadL` del 2026-10-04 (10.000 estrategias, NIKKEI225, M30, largas) y están calculados sobre sus operaciones con las reglas y los datos **de hoy**. Donde una regla nueva pide un número que todavía no se ha calculado, el ejemplo lo dice: «ilustrativo» quiere decir que la cuenta está hecha a mano con cifras conocidas o inventadas para enseñar a leerla, no que sea una medida. **Ninguna línea de este documento está congelada**: son las de partida (apartado 10).

**Quién manda si dos papeles no coinciden:** el encargo `docs/encargos/44-puerta-is-oos-paso-8.md`. Tus seis propuestas y tu índice son anteriores a varias decisiones; este documento ya las lleva aplicadas.

---

## 0. En una página

### 0.1 La pregunta que contesta la puerta

**¿Hay en esta estrategia una ventaja real y estable fuera de la muestra con la que se construyó?** Sólo eso. Cuánto riesgo se le puede poner dentro de una cuenta de fondeo es otra pregunta, y se va a otro módulo (apartado 13).

### 0.2 Qué cambia respecto a lo anterior

| regla | antes | ahora |
|---|---|---|
| R1a presencia | el juez perdía los hechos cuando la identidad cambiaba entre build y retest | igual, con ese fallo arreglado lo primero |
| R1b, R2 | — | sin cambios |
| R2b neto al spread de Darwinex | descartaba | **retirada** |
| R3 t del exceso | Pasa ≥ 2,33, Limbo ≥ 1,65, excepciones para H4 y H1; una sola deriva para todo oos1 | **Pasa ≥ 1,65, sin Limbo y sin excepciones**; deriva por ventana de calendario; error estándar con sesgo y curtosis; sesgo por tamaño corregido en la propia R3 |
| R4a suelo en el build | 35 / 20 al año | sin cambios |
| R4b techo de 75 al año | Pasa ≤ 75 | **retirada** |
| R5 frecuencia en oos1 | umbral absoluto: ≥ 15 / ≥ 10 al año | **prueba de estabilidad** build → oos1 (z con sobredispersión, centrada por población, a dos lados) |
| R5b 100 operaciones | leía del estudio del spread | igual, lee `gate.scorecard.sanidad_value`; sigue sin descartar |
| R5c ventaja frente al coste | `edge_mean` sobre build y oos1 juntos, denominador sin slippage | sólo oos1, sobre el coste pagado, más **la t de R3 con el coste × 1,25** |
| R5d degradación | no existía | **nueva**: pendiente del exceso dentro de oos1 |
| R6 drawdown | DD de oos1 / DD del build ≤ 1,25 | **percentil del DD de oos1** en un bootstrap por bloques del build |
| R7 años positivos | ≥ 3 años positivos | **homogeneidad del exceso por trimestres** (Q con nula por permutación) |
| R8 concentración | mejor trimestre ≤ 50 % del beneficio | **la t de R3 sin el mejor trimestre y sin las 3 mejores operaciones** |
| R9a peor día, R9c DD / neto anual | reglas del paso 8 | **fuera**: al módulo de fondeo |
| R9b MAE | la peor operación | **percentil 95** de la MAE |
| mono | criba laxa, p con suelo | **control de R3**: z continuo, tamaño por la doctrina, sorteo dentro de la ventana de la deriva |
| calidad de datos, retraso de una barra | anotaban | **reglas**, y pueden descartar |
| espionaje de datos y criba `familia`, `profitShape`, repreciado al spread de Darwinex, `edge_median` y `n` | anotaban | **borrados** |
| orden de cálculo | todo para todas | **cascada** de lo barato a lo caro, saliendo en el primer Falla |

### 0.3 La tabla final de reglas

`e` es el **exceso por operación** de R3: el P/L de la operación menos lo que habría ganado una operación ciega del mismo lado, duración y tamaño (apartado 5). Todas las reglas que hablan de «exceso» o de «la t» usan los de R3.

| nivel | regla | qué pregunta | hecho | Pasa | Limbo | Falla |
|---|---|---|---|---|---|---|
| 0 | **R1a** presencia | ¿sigue en el databank del retest? | `gate.scorecard.presencia_passed` | sí | — | no |
| 0 | **R1b** sanidad y clones | ¿hay algo que medir y no es copia de otra? | `gate.scorecard.sanidad_passed` | sí | — | no |
| 0 | **R2** neto de oos1 | ¿ganó dinero en oos1? | `gate.scorecard.estaticas_value` | > 0 | — | ≤ 0 |
| 0 | **R4a** operaciones al año en el build | ¿opera lo bastante? | `is_trades_per_year` | ≥ 35 | 20 – 35 | < 20 |
| 0 | **R5b** operaciones en oos1 | ¿se puede leer la t? | `gate.scorecard.sanidad_value` | ≥ 100 | < 100 | nunca |
| 1a | **R3** t del exceso | ¿la ventaja se distingue del azar, quitado el mercado? | `gate.scorecard.drift_excess_t` | ≥ 1,65 | **no tiene** | < 1,65 |
| 1b | **R5** estabilidad de la frecuencia | ¿opera al mismo ritmo que en el build? | `z_frec` | z en valor absoluto ≤ 1,5 | hasta 3,5 | > 3,5 |
| 1b | **R5c** ventaja frente al coste | ¿aguanta un coste peor? | `edge_mean_oos`, `t_exceso_k` (k = 1,25) | t(k) ≥ 1,65 y edge ≥ 2 | t(k) < 1,65, o edge 1,25 – 2 | edge < 1,25 |
| 1b | **R5d** degradación dentro de oos1 | ¿la ventaja se va apagando? | `t_b`, `e_fin` | t_b ≥ −1,65 | t_b < −1,65 | t_b < −1,65 y e_fin ≤ 0 |
| 1b | **R8** concentración | ¿depende de un trimestre o de tres operaciones? | `t_sin_mejor_trimestre`, `t_sin_3_mejores` | las dos ≥ 1,65 | alguna entre 0 y 1,65 | alguna ≤ 0 |
| 1b | **R9b** MAE | ¿el riesgo real es el nominal? | `mae_p95_r` | ≤ 1,5R | hasta 2,5R | > 2,5R |
| 1b | **Calidad de datos** | ¿la ventaja vive de datos defectuosos? | `ret_datos`, `t_A` | ret ≥ 0,60, o ninguna afectada | 0,25 – 0,60, o < 0,25 con t_A ≤ 1,65 | < 0,25 y t_A > 1,65 |
| 2 | **Retraso de una barra** | ¿sobrevive a mover la operación una barra? | `retraso_ret_min`, `retraso_t_delta` | ret ≥ 0,60 | 0,25 – 0,60, o < 0,25 con t_Δ ≤ 1,65 | < 0,25 y t_Δ > 1,65 |
| 3a | **R7** homogeneidad por trimestres | ¿el resultado depende de un régimen? | `q_p` | > 0,05 | ≤ 0,05 | nunca |
| 3b | **R6** drawdown | ¿el drawdown de oos1 es el esperable? | `dd_p` | > 0,10 | 0,01 – 0,10 | ≤ 0,01 |
| 3c | **Mono** | ¿gana a entrar al azar, sin suponer normalidad? | `z_mono` | ≥ 1,65 | < 1,65 | nunca |

Son dieciséis filas. Tres nunca descartan (R5b, R7 y el mono); las otras trece pueden. La que hace casi todo el trabajo sigue siendo R3.

---

## 1. Qué es el paso 8 y cómo decide

### 1.1 Qué hace y dónde está

El paso 6 construye estrategias en SQX mirando sólo el tramo `build`. El paso 7 las vuelve a probar en un tramo que el generador no vio, `oos1`. El **paso 8** es Python: lee los dos databanks (el del build y el del retest), calcula sus números por estrategia y aplica las reglas de `pipeline/autopilot/criteria.yaml`. Lo que falla se borra del databank `OOS`, que es el que lee la siguiente tarea de SQX (el paso 9). Corre solo, dentro de `bin/workflow.sh`: nunca se lanza a mano.

Los tramos, según `assets/symbols/`:

| activo | `build` | `oos1` (lo que juzga el paso 8) | `oos2` |
|---|---|---|---|
| XAUUSD y forex | 2008–2017 (10 años) | 2018–2022 (5 años) | 2023–sept. 2026 |
| NIKKEI225 | 19-09-2011–2019 (8,28 años) | 2020–2023 (4 años) | 2024–sept. 2026 |

El paso 8 **no toca `oos2`**.

### 1.2 Los tres estados

| estado | qué significa | qué hace el workflow |
|---|---|---|
| **Pasa** | cumple la línea exigente de todas las reglas | sigue al paso 9 |
| **Limbo** | ni prueba ni condena | sigue al paso 9, **marcada** |
| **Falla** | alguna regla la da por mala | se **borra** del databank `OOS` |

### 1.3 Manda la peor, y lo que no se calculó no es «falta»

Cada regla lee un dato de la estrategia (un «hecho») y da Pasa, Limbo o Falla. El resultado de la estrategia es el de **su peor regla**: basta una en Falla para sacarla; basta una en Limbo para que no pueda ser Pasa.

Dos casos que parecen iguales y no lo son:

- **Un hecho que falta** — el estudio corrió y no dejó el dato — es **Limbo** (tu decisión del 2026-10-01).
- **Un hecho no calculado porque la estrategia ya había caído** en un nivel anterior de la cascada no es «falta»: la estrategia es Falla por la regla que la tiró, y el juez no lee como Limbo lo que la cascada no llegó a calcular (apartado 9).

### 1.4 Dos avisos antes de leer números

1. **El modo de desarrollo sigue encendido** (`dev.on` en `criteria.yaml`). Mientras lo esté, el piloto automático no se queda con las que no fallan: sortea unas pocas y borra el resto, sin mirar el veredicto. Sirve para probar el workflow, no para seleccionar. Se apaga cuando tú lo digas, después de fijar las líneas con las dos poblaciones de prueba (apartado 10).
2. **Las líneas de este documento son puntos de partida.** Cambiar el dato de una regla invalida la tasa de falsos positivos con la que se fijó su línea, y aquí cambia el dato de casi todas. Se mide antes de congelar.

### 1.5 Las tres estrategias que nos acompañan

Las tres son de la misma corrida (NIKKEI225, M30, largas).

| | **A** | **B** | **C** |
|---|---|---|---|
| nombre | `Strategy 4.9.301` | `Strategy 16.11.437` | `Strategy 14.3.479` |
| operaciones en el build / al año | 329 / 39,71 | 307 / 37,06 | 189 / 22,81 |
| operaciones en oos1 / al año | 196 / 49,0 | 193 / 48,25 | 98 / 24,5 |
| neto en oos1 (USD) | 38.465 | 31.862 | 4.690 |
| t del exceso (R3, dato de hoy) | 2,540 | 2,154 | 0,702 |
| con las reglas anteriores | Pasa | Limbo (t entre 1,65 y 2,33) | Falla (t < 1,65) |
| con R3 nueva | pasa R3 | **pasa R3** (ya no hay Limbo) | Falla en R3 |

A y B llegan a todos los niveles; C sale en el nivel 1a y no se le calcula nada más. Una cuarta hace de invitada: **D**, `Strategy 8.4.275`, la de mejor t de la población (3,14), que opera 16,66 veces al año en el build y cae en el nivel 0 por R4a.

Las operaciones de las 10.000 estrategias están en disco. La curva diaria de flotante y la MAE de oos1, en cambio, sólo se conservan de las diez que salieron del sorteo de aquella corrida; C está entre ellas, A y B no. Por eso algunos ejemplos sólo pueden dar el valor guardado de A y B.

---

## 2. La estadística mínima

Lo que usan casi todas las reglas. Cada prueba más específica se explica en su apartado, la primera vez que aparece.

### 2.1 Media, desviación típica y R

```
media = (x1 + x2 + … + xn) / n
desv  = √( suma de (xi − media)² / (n − 1) )
resultado en R = resultado en dinero / 1R          1R = 1.000 USD (assets/_build.yaml)
```

La **media** dice cuánto gana una operación normal. La **desviación típica** dice cuánto se aparta de esa media una operación cualquiera. **R** es la unidad de riesgo: medir en R permite comparar activos y estrategias sin pensar en el tamaño de la cuenta. Aquí R es **nominal**: la doctrina no lleva stop fijo, así que una operación puede perder más de 1R, y eso es justo lo que mide R9b.

En A, sobre sus 196 operaciones de oos1: media 196,25 USD (0,196R), desviación 951,32 USD. La desviación es casi cinco veces la media: lo normal en trading.

### 2.2 Error estándar

```
error estándar = desv / √n
```

La media que has medido no es «la» media verdadera de la estrategia: es la de las operaciones que le tocaron. El error estándar dice cuánto bailaría esa media si la historia se repitiera. Baila menos cuantas más operaciones hay, pero **con la raíz**: para la mitad de baile hacen falta cuatro veces más operaciones. En A: 951,32 / √196 = 951,32 / 14 = 67,95 USD.

### 2.3 El Sharpe por operación y la t

```
s = media / desv                    (Sharpe por operación)
t = media / (desv / √n) = s × √n    (estadístico t)
```

La **t** dice **a cuántos errores estándar está la media de cero**. Si la estrategia no tuviera ventaja, su media verdadera sería cero y la medida bailaría alrededor de ahí: una t de 0,5 es un baile corriente; una de 3, uno muy raro. La forma `s × √n` separa las dos cosas que hacen grande una t: **calidad** por operación (`s`) y **cantidad** (`√n`).

En A: s = 196,25 / 951,32 = 0,2063; t = 0,2063 × 14 = 2,888.

### 2.4 n efectivo: cuando las operaciones no son independientes

```
ρ = suma de (xi − media) × (x(i−1) − media) / suma de (xi − media)²
n efectivo = n × (1 − ρ) / (1 + ρ)        (nunca más que n, nunca menos que 2)
t corregida = t × √(n efectivo / n)
```

`ρ` (ro) es la **autocorrelación de orden 1**: cuánto se parece cada operación a la anterior, entre −1 y +1. Si una buena tiende a ir seguida de otra buena (rachas), hay menos información que operaciones: el n efectivo baja y la t se encoge. Con ρ negativa el código deja n como está, para que la alternancia no fabrique observaciones. En A, ρ = −0,139: la t no cambia. En D, ρ = +0,032 sobre 96 operaciones: n efectivo 90,04 y la t baja de 3,24 a 3,14.

### 2.5 p-valor y línea a una cola

El **p-valor** de una t es la probabilidad de ver una t así de grande **o mayor** en una estrategia sin ninguna ventaja:

```
p = 1 − Φ(t)
```

`Φ` (fi mayúscula) da, para un número z, la probabilidad de que una variable normal estándar quede por debajo de z: Φ(0) = 0,5; Φ(1,65) = 0,95; Φ(2,33) = 0,99. **«A una cola»** quiere decir que sólo se mira un lado: interesa que gane, no que pierda mucho.

**Qué significa p = 0,05.** Que una de cada veinte estrategias **sin ventaja** llega a esa línea por pura suerte. No significa que la estrategia tenga un 95 % de probabilidad de ser buena: eso depende además de cuántas buenas había antes de mirar, que nadie sabe.

| línea de t | p nominal | se lee |
|---|---|---|
| 1,65 | 5 % | 1 de cada 20 sin ventaja llega aquí por suerte |
| 2,00 | 2,3 % | 1 de cada 44 |
| 2,33 | 1 % | 1 de cada 100 |

El 5 % es lo que dice la teoría. Lo **medido** con poblaciones de estrategias sin ventaja y el dato de hoy es un 3,9 % en la celda mediana y un 5,8 % en la peor: queda por debajo porque una estrategia sin ventaja paga costes y su media no es cero sino algo negativa.

### 2.6 Potencia: cuántas buenas se quedan fuera

```
potencia = Φ( s × √n − z )
```

La **potencia** es la probabilidad de que una estrategia **con** ventaja real `s` supere la línea `z`. Es el espejo de la tasa de falsos positivos: aquella mide la basura que entra; esta, lo bueno que se pierde. Una estrategia con ventaja verdadera `s` tiene una t que baila alrededor de `s × √n` con un baile de tamaño 1; si `s × √n` cae justo en la línea, la supera la mitad de las veces.

Con la línea en 1,65 (la fórmula; no es una medida):

| operaciones en oos1 | s = 0,05 | s = 0,10 | s = 0,15 |
|---|---|---|---|
| 100 | 12,5 % | 25,8 % | 44,0 % |
| 196 (las de A) | 17,1 % | 40,1 % | 67,4 % |
| 250 | 19,5 % | 47,3 % | 76,5 % |

Con una ventaja pequeña la prueba pierde a casi todas las buenas, con cualquier frecuencia. Es el límite de fondo del paso (apartado 15).

---

## 3. Un solo P/L para todo: el repreciado común y los costes

### 3.1 La regla

**La estrategia, R3, el retraso de una barra, la calidad de datos y los monos usan el mismo P/L**, calculado por una sola función: dadas las operaciones y las barras, devuelve el resultado a los costes que la tarea de SQX cobró — su spread, su slippage, su comisión y su swap. Si cada prueba repreciara por su cuenta, estarían contrastando hipótesis distintas y una discrepancia entre ellas no significaría nada.

### 3.2 Qué costes

Los de la ficha del activo, **recalibrada el 2026-10-04**: el porcentaje del precio de la firma más cara, aplicado al precio medio de cada tramo; slippage del 35 % de ese spread; y un rango de 0,5× a 2× para el MC Retest. Es un porcentaje a propósito: la historia paga la fricción de 2026 en proporción al precio.

**Ningún criterio del paso 8 usa el spread de los ticks de Darwinex.** En algunos activos no es realista (no se opera con tanto), y el hallazgo de que «el spread de SQX estaba en el percentil 10 del real» se midió contra él, así que decae con él.

En la corrida de ejemplo el coste que SQX cobró a cada operación de NIKKEI225 en oos1 fue de 8,07 puntos de precio: el spread declarado (4,7491) más dos veces el slippage (2 × 1,6622). Ese coste por operación, en dinero, es también **el denominador de `edge_mean_oos` y el coste de `t_exceso_k`** en R5c.

### 3.3 La auditoría pendiente del repreciado del mono

El mono reprecia hoy con su propio motor y le da a la estrategia A un neto de **45.464 USD** donde SQX da **38.465**: un **18 % más**, sin explicación. Es del orden de toda la deriva de A (4.689 USD, el 12 % de su neto): suficiente para cambiar conclusiones. Nada del mono entra en la puerta hasta que esté resuelto.

Se revisa operación a operación, para A, B y C, contra las operaciones de SQX:

1. precio de entrada y precio de salida;
2. lotes y valor del punto (NIKKEI225: 0,063137 USD por punto y lote);
3. spread, slippage, comisión y swap;
4. la suma: el P/L de cada operación cuadra con SQX, o la diferencia tiene nombre y tamaño.

Termina cuando cuadra o cuando la diferencia está explicada. El resultado se escribe en una ficha de `knowhow/research/`, y la tolerancia que la auditoría justifique queda escrita en el test: **el P/L repreciado de A, B y C sin desplazar nada reproduce el de SQX**.

---

## 4. Nivel 0 — metadatos y recuentos

Cinco reglas que no necesitan recorrer las operaciones. Son instantáneas y aquí cae buena parte de la población.

### 4.1 R1a — Sigue en el databank del retest

Hecho: `gate.scorecard.presencia_passed`

**La pregunta.** ¿La estrategia del build sigue existiendo en el retest? SQX tira una estrategia del retest cuando salta una de sus propias banderas rojas.

**Cómo se calcula.** Vale 1 si la identidad de la estrategia del build aparece entre las del retest, y 0 si no. La identidad es la huella (SHA-256) del XML interno de la estrategia, normalizado.

**El fallo que se arregla lo primero.** La puerta guarda sus hechos bajo la identidad que la estrategia tenía en el build; el juez los busca por la identidad del fichero del databank `OOS`; en una parte de las estrategias las dos no coinciden, el juez no encuentra el dato y la regla (`missing: fail`) las descarta. En la corrida de ejemplo:

```
ficheros en el databank OOS (los que se juzgan):                 10.000
  su identidad coincide con la que usó la puerta:                 8.443
  su identidad es otra (cambió entre el build y el retest):       1.548
  su identidad no aparece en ningún hecho:                            9
  sin el dato presencia_passed  →  Falla                          1.557
```

De esas 1.557, por sus propios números 1.528 habrían fallado igualmente y **29 habrían sido Limbo**: el 17 % de las 169 vivas se pierde por un error de contabilidad, no por un veredicto. Se arregla **en el punto por el que pasan todos los que leen** — la resolución de la identidad —, no regla a regla. **Ningún recuento de las reglas siguientes vale hasta entonces.**

**Las líneas.** Pasa si está; Falla si no. Sin Limbo. Si SQX la tiró, esa decisión ya está tomada.

**Parámetros.** Ninguno. **Coste:** nivel 0. **Por medir:** el recuento antes y después del arreglo sobre una población ya cosechada.

### 4.2 R1b — Hay algo que medir y no es un clon

Hecho: `gate.scorecard.sanidad_passed`

**La pregunta.** ¿Hay operaciones en oos1, y la lista de operaciones no es la misma que la de otra estrategia?

**Cómo se calcula.** Cuenta las operaciones de oos1 (ese recuento es `sanidad_value`). Vale 1 si hay **al menos 20** y la lista no es idéntica a la de otra estrategia; de un grupo de clones sobrevive la primera. El 20 está en `ledger/thresholds.yaml` (`gate.sanidad.min_trades`). Los clones se buscan en las operaciones mismas, no en el nombre.

**Ejemplo.** A tiene 196 operaciones en oos1, B 193 y C 98: las tres valen 1. En la población descarta 142: **129 clones** y 13 con menos de 20 operaciones.

**Las líneas.** Pasa si vale 1; Falla si no. Sirve sobre todo contra los clones: el 20 queda por debajo de lo que ya imponen R4a y R5.

**Parámetros.** El mínimo de operaciones (20, del ledger). **Coste:** nivel 0. **Por decidir:** un suelo absoluto de 60–80 operaciones en oos1, por la no normalidad de la media con pocas operaciones y distribuciones sesgadas. No está decidido; se te pregunta sólo si los números de las poblaciones de prueba lo piden.

### 4.3 R2 — Ganó dinero en oos1

Hecho: `gate.scorecard.estaticas_value`

**La pregunta.** ¿El neto de oos1, tal como lo da SQX con los costes de la tarea de retest, es positivo?

**Cómo se calcula.** Es la métrica `Net profit [OOS]` del fichero de la estrategia: la suma del resultado de sus operaciones de oos1.

```
A:  196 × 196,25 = 38.465 USD      B:  193 × 165,09 = 31.862 USD      C:  98 × 47,86 = 4.690 USD
```

**Las líneas.** Pasa si > 0; Falla si ≤ 0. Sin Limbo.

**Lo que vale.** Es un criterio débil: en la población de ejemplo el 59 % acaba oos1 en positivo, y son largas en un índice que subió de 23.470 a 33.290. No es la única que descarta a ninguna: toda estrategia con neto ≤ 0 tiene también una t por debajo de 1,65. Se queda de **red**, por si alguna vez se afloja la t, y porque en la cascada ahorra calcular R3 a 3.912 estrategias.

**Parámetros.** Ninguno. **Coste:** nivel 0.

### 4.4 R4a — Opera lo bastante en el build

Hecho: `is_trades_per_year`

**La pregunta.** ¿Cuántas operaciones al año hace la estrategia en el `build`? Es su frecuencia de diseño.

**Cómo se calcula.**

```
operaciones por año en el build = operaciones en el build / años del tramo build
```

Los años son los del tramo del activo en el calendario (días entre su principio y su final, entre 365,25), no el tiempo entre la primera y la última operación: 8,2847 en NIKKEI225, 10 en XAUUSD y forex.

**Ejemplo.**

```
A:  329 / 8,2847 = 39,71   → Pasa   (≥ 35)
B:  307 / 8,2847 = 37,06   → Pasa
C:  189 / 8,2847 = 22,81   → Limbo  (entre 20 y 35)
D:  138 / 8,2847 = 16,66   → Falla  (< 20)
```

**Las líneas.** Pasa ≥ 35 · Limbo de 20 a 35 · Falla < 20. Sin cambios: 35 es tu suelo de trabajo y 20 el suelo duro. En la población de ejemplo: 4.202 pasan, 3.557 quedan en Limbo y 2.241 fallan.

**Lo que se sabe del suelo.** Más operaciones al año **no compran t**: en las poblaciones medidas, la proporción de estrategias con `drift_excess_t ≥ 1,65` **baja** al subir la frecuencia, porque cada operación de más paga el spread. Un suelo de frecuencia no se puede justificar por la potencia de la prueba; se justifica porque con muy pocas operaciones no hay nada que leer.

**El techo desaparece.** R4b (como mucho 75 al año) está retirada.

**Parámetros.** Las dos líneas. **Coste:** nivel 0. **En H4** la regla conserva su excepción de hoy (Limbo desde 15 al año): «sin tocar» es dejarla como está cargada. La ausencia de excepciones por timeframe es de R3.

### 4.5 R5b — Al menos 100 operaciones en oos1

Hecho: `gate.scorecard.sanidad_value`

**La pregunta.** ¿Hay bastantes operaciones en oos1 para leer la t con confianza? Por debajo de 100 el resultado no es negativo: es ilegible.

**Cómo se calcula.** El recuento de operaciones de oos1. Antes lo leía del estudio del spread, que se borra; pasa a leer el mismo número de la puerta.

**Ejemplo.** A, 196: Pasa. B, 193: Pasa. C, 98: **Limbo** por dos operaciones.

**Las líneas.** Pasa ≥ 100 · Limbo < 100 · **nunca falla**.

**Por qué es sólo una red.** Su función la cubren R4a y la R5 nueva: con 35 operaciones al año en el build y una sobredispersión de 2, el borde inferior del Pasa de R5 queda en unas 27–28 al año, que son unas 80 operaciones en 3 años de oos1, 110 en 4 y 141 en 5 (cuenta hecha con las bandas de 1,5; apartado 6.1). No es una garantía exacta de 100, pero sí del orden correcto. R5b no cuesta nada y cubre los builds cortos y los casos de frontera.

**Parámetros.** La línea (100). **Coste:** nivel 0.

---

## 5. Nivel 1a — R3, la regla central

Hecho: `gate.scorecard.drift_excess_t`

### 5.1 La pregunta

**¿El beneficio medio por operación en oos1 se distingue del azar después de quitarle lo que el mercado habría pagado a cualquiera por estar dentro?**

### 5.2 Por qué se resta la deriva

Un largo en un índice que sube gana aunque la entrada no valga nada. Sin restar la deriva, la t premiaría a las estrategias por pasar mucho tiempo dentro de un mercado alcista. El **exceso** es lo que queda del resultado de una operación cuando se le quita lo que habría ganado una operación «ciega»: del mismo lado, la misma duración y el mismo tamaño, pero sin ninguna habilidad para elegir el momento.

### 5.3 Qué cambia y por qué

| | antes | ahora | motivo |
|---|---|---|---|
| deriva | un movimiento medio por barra para todo oos1 | uno **por ventana de calendario** | cuatro o cinco años no son un solo régimen: la estrategia no debe cobrar por haber estado más tiempo dentro en los años buenos |
| sesgo por tamaño | conocido y sin corregir | **corregido en la propia R3** | trata distinto a largos y cortos; no se delega en el mono |
| error estándar | el normal | **con sesgo y curtosis** | con sesgo negativo fuerte, la t normal deja pasar de más |
| líneas | Pasa ≥ 2,33, Limbo ≥ 1,65, excepciones H4 y H1 | **Pasa ≥ 1,65, sin Limbo, sin excepciones** | una sola línea con significado claro: p = 0,05 a una cola |

### 5.4 El método, paso a paso

**Paso 1 — La deriva del mercado por barra, en cada ventana.** Se parte oos1 en ventanas de calendario (años naturales o semestres). En cada ventana `w` se toman todas las barras del timeframe de la estrategia y se calcula el cambio medio de cierre a cierre:

```
μ(w) = media de (cierre de la barra − cierre de la barra anterior), sobre las barras de la ventana w
```

`μ` (mu) es la **deriva**: lo que el precio sube, de media, en una barra. Con una sola ventana para todo oos1 (el dato de hoy), en NIKKEI225 M30 de 2020 a 2023 el índice pasó de 23.470 a 33.290 (+9.819 puntos) en 45.979 barras: μ = 0,2136 puntos por barra.

**Paso 2 — Lo que la deriva le pagó a cada operación.** Cada operación lleva la deriva **de la ventana en la que se abrió**:

```
deriva de la operación = lado × μ(ventana de la apertura) × barras abierta × lotes × valor del punto
```

`lado` es +1 si es larga y −1 si es corta.

**Paso 3 — El exceso.**

```
e = P/L de la operación (repreciado común) − deriva de la operación
```

**Paso 4 — Una sola t, sobre todas las operaciones de oos1.** No una t por ventana: con 40 o 50 operaciones cada una no tendría potencia.

```
s = media de e / desv de e

                     s × √(n − 1)
t = ─────────────────────────────────────────────
     √( 1 − γ3 × s + (γ4 − 1) / 4 × s² )
```

- `γ3` (gamma tres) es el **sesgo** de `e`: 0 si la distribución es simétrica; negativo si tiene una cola de pérdidas grandes y raras (lo típico de una reversión a la media sin stop); positivo si la cola es de ganancias grandes (lo típico de seguir tendencias).
- `γ4` (gamma cuatro) es la **curtosis**: cuánto pesan las colas. Vale 3 en una distribución normal; más de 3, colas gordas.
- Con γ3 = 0 y γ4 = 3 el denominador es casi 1 y la fórmula devuelve la t de siempre. Con sesgo negativo el denominador crece y la t **baja**: la media de una distribución con cola de pérdidas es menos fiable de lo que su desviación dice, porque la pérdida grande que la corrige puede no haber salido todavía.

Es la forma del *Probabilistic Sharpe Ratio*: el mismo error estándar que usa esa medida, aplicado a la t.

### 5.5 El sesgo por tamaño, y cómo se corrige

El paso 2 supone que cada barra que la operación estuvo abierta fue una barra media. Pero la doctrina dimensiona las operaciones **en proporción inversa a la volatilidad**: más lotes cuando el mercado está tranquilo, menos cuando está agitado. En A se ve: 75,04 lotes en enero de 2020 y 21,50 en marzo de 2020. Si en un activo a las épocas tranquilas les siguen movimientos distintos de la media, una operación sin habilidad se queda con un resto positivo o negativo que el término no descuenta, y ese resto tiene **el signo contrario para largos y cortos**.

Medido: desplaza la t de una estrategia sin ventaja entre **±0,02 y ±0,27** según activo y lado (EURUSD largo −0,19; USDCAD largo +0,18, a 50 operaciones al año); el desplazamiento medio es de 0,12 en oos1. En EURUSD, a 1,65 pasan el 2,6 % de las largas sin ventaja y el 5,8 % de las cortas. Un largo y un corto, o dos activos, **no están en la misma escala de t**. Para NIKKEI225 largo el tamaño del sesgo no está medido.

La corrección conocida es «la operación ciega de la misma duración» como término de deriva (`knowhow/research/drift-term-biased-by-side.md`): medido, quita cerca del 60 % del sesgo y deja a un largo unos +0,05 de t (como mucho +0,32).

**Lo que se mide antes de elegir.** Cuatro variantes del término, cada una con ventana de **un año natural** y de **seis meses**:

| variante | término de deriva |
|---|---|
| (a) | el de hoy: una deriva para todo oos1 |
| (b) | deriva por ventana (pasos 1 y 2 de arriba) |
| (c) | la corrección de la operación ciega |
| (d) | (b) y (c) juntas |

Y de cada una: el sesgo por lado y activo de una estrategia sin ventaja, la tasa de falsos positivos a 1,65, y cuántas estrategias cambian de veredicto y en qué sentido. **La variante se carga sola:** la que menos sesgo deje; si empatan, la más simple. **La ventana la eliges tú**, con los dos resultados — año y semestre — lado a lado.

**Por qué la ventana nunca baja de un trimestre.** Cuando la ventana se acerca a la duración de una operación, la deriva de la ventana **es** el movimiento que la operación cogió, y el exceso tiende a cero por construcción: se estaría llamando «mercado» a la habilidad de elegir el momento.

### 5.6 Ejemplo

**Una operación.** La primera de A en oos1: larga, 9-01-2020 de 07:30 a 21:00 (27 barras), 75,04 lotes, resultado −41,70 USD. Con el dato de hoy (variante a):

```
deriva = 1 × 0,2136 × 27 × 75,04 × 0,063137 = 27,32 USD
e      = −41,70 − 27,32 = −69,02 USD
```

El mercado, sólo por subir, «le debía» 27 USD a esa operación; perdió 42, así que frente al mercado perdió 69. Con la deriva por ventana, el 0,2136 se sustituye por el μ de 2020 (o de su primer semestre): ese valor está por calcular.

**Las tres estrategias, con el dato de hoy.**

| | A | B | C |
|---|---|---|---|
| operaciones (n) | 196 | 193 | 98 |
| media del P/L (USD) | 196,25 | 165,09 | 47,86 |
| deriva media (USD) | 23,92 | 24,92 | 7,04 |
| media de e (USD) | 172,33 | 140,17 | 40,82 |
| desv de e (USD) | 949,76 | 903,96 | 575,90 |
| s = media / desv | 0,1814 | 0,1551 | 0,0709 |
| **`drift_excess_t`** | **2,540** | **2,154** | **0,702** |
| con la línea nueva | **Pasa** | **Pasa** | **Falla** |

La deriva explica 4.689 de los 38.465 USD de A: el 12 %. C apenas tiene deriva (7 USD) porque sus operaciones duran 6,9 barras de media; lo que la hunde es que 41 USD de media con 576 de desviación y 98 operaciones no se distinguen de cero.

**Lo que hace el error estándar nuevo (ilustrativo).** El sesgo y la curtosis de `e` en A no están calculados. Con su s = 0,1814 y n = 196, la fórmula daría:

| forma de las operaciones | γ3 | γ4 | denominador | t |
|---|---|---|---|---|
| normal | 0 | 3 | √(1 + 0,5 × 0,0329) = 1,008 | 2,533 / 1,008 = **2,51** |
| cola de pérdidas (reversión sin stop) | −1,5 | 8 | √(1 + 0,272 + 0,058) = 1,153 | 2,533 / 1,153 = **2,20** |
| cola de ganancias (tendencia) | +1,5 | 8 | √(1 − 0,272 + 0,058) = 0,886 | 2,533 / 0,886 = **2,86** |

(2,533 = 0,1814 × √195.) La misma media y la misma desviación valen 2,20 o 2,86 según de qué lado esté la cola.

### 5.7 Las líneas

| Pasa | Limbo | Falla |
|---|---|---|
| t ≥ 1,65 | **no tiene** | t < 1,65 |

Para cualquier timeframe: **fuera las excepciones de H4 y de H1**.

**Lo que cuesta la línea.** De 10.000 estrategias sin ventaja pasan por azar unas **390** con el dato de hoy (3,9 % en la celda mediana; 5,8 % en la peor). Esa cifra se vuelve a medir con el dato nuevo. En la población de ejemplo hay 325 estrategias con t ≥ 1,65 con el dato de hoy; con la línea anterior de Pasa (2,33) había 44.

**Lo medido del error estándar nuevo.** Un t normal sobre operaciones con sesgo de −1,5 rechaza a una estrategia sin ventaja el 6,9 % de las veces en la línea del 5 % y el 2,1 % en la del 1 %. Con el error estándar corregido, los falsos positivos de USA500 H1 `indicesIBS` bajan de **6,9 % a 5,1 %** a 1,65, sin mover las otras poblaciones. Con un sesgo dentro de ±0,8 la tasa apenas se mueve (de 5,8 % a 4,7 %): la corrección sólo trabaja donde hace falta.

### 5.8 Parámetros

| parámetro | valor de partida |
|---|---|
| línea de Pasa | 1,65 |
| ventana de la deriva (la misma que la del sorteo del mono) | año o semestre, la que elijas; mínimo un trimestre |
| variante del término de deriva | la que salga de la medida de 5.5 |
| error estándar con sesgo y curtosis | encendido |

### 5.9 Lo que cuesta calcularla

Nivel 1: una pasada sobre las operaciones. La deriva por ventana se calcula una vez por activo y timeframe. Es la regla que más descarta, así que va **la primera** de su nivel.

### 5.10 Lo que falta por medir

- Las cuatro variantes con las dos ventanas (5.5).
- El error estándar nuevo **junto al n efectivo** de 2.4, que la puerta ya usa: se han medido por separado, no juntos. Se mide antes de cargarlo.
- La tasa de falsos positivos a 1,65 con el dato definitivo: la población nula tiene que dar una tasa compatible con el 5 %.

---

## 6. Nivel 1b — reglas de una pasada sobre las operaciones

Seis reglas que comparten con R3 el exceso por operación. Se calculan en la propia puerta, junto a `drift_excess_t`.

### 6.1 R5 — La frecuencia no cambia entre el build y oos1

Hecho: `z_frec`

**La pregunta.** ¿La estrategia sigue disparando sus reglas en oos1 al mismo ritmo que en el build?

**Por qué cambia.** La regla anterior era un suelo absoluto (15 al año). No comparaba con nada: una estrategia que hacía 60 al año en el build y 16 en oos1 pasaba. Una **caída** fuerte dice que las reglas ya no se activan (estaban ajustadas a algo que dejó de pasar); una **subida** fuerte, que la estrategia se comporta distinto de como se construyó. Las dos son sospechosas, así que la prueba mira **los dos lados**.

**El modelo.** Las operaciones se tratan como un **proceso de Poisson**: sucesos que llegan al azar a un ritmo medio constante, como las llamadas a una centralita. Con `N1` operaciones en `T1` años de build y `N2` en `T2` años de oos1:

```
r1 = N1 / T1          r2 = N2 / T2          (operaciones por año)

log del cociente = ln(r2 / r1)

error estándar (Poisson) = √( 1/N1 + 1/N2 )
```

Se trabaja con el **logaritmo** del cociente porque así «la mitad» y «el doble» quedan a la misma distancia de cero (−0,69 y +0,69).

**Primera corrección: la sobredispersión.** Las operaciones no llegan como un Poisson puro: se agrupan por régimen de volatilidad. En un Poisson, la varianza de los recuentos anuales es igual a su media; cuando la varianza es mayor se habla de **sobredispersión**, y significa que los recuentos bailan más de un año a otro de lo que el modelo espera. Se estima en el build, con los recuentos por año natural `x1 … xk`:

```
φ estimada = varianza de los recuentos anuales / media de los recuentos anuales

φ = la estimada, acotada entre 1,5 y 3,5
```

`φ` (fi minúscula) vale 1 en un Poisson puro. El **suelo de 1,5** evita que una estrategia excepcionalmente regular en el build tenga una banda demasiado estrecha. El **techo de 3,5** evita que una muy irregular tenga una banda tan ancha que nunca falle. Con 8–10 años de build, φ se estima con sólo 8–10 puntos: es ruidosa, y el acotado la estabiliza.

Ejemplo (ilustrativo): recuentos anuales 30, 45, 38, 52, 35, 41, 33, 55 (suman 329).

```
media = 41,1        varianza = 562,8 / 7 = 80,4        φ = 80,4 / 41,1 = 1,96
```

**Segunda corrección: el efecto común de mercado.** Si todo el mercado cambió de régimen (la volatilidad de 2020), casi todas las estrategias operan más en oos1, y eso no dice nada de cada una. Se resta el **centro de la población**:

```
m_pop = mediana de ln(r2 / r1) entre las estrategias de la corrida que llegaron al retest,
        del mismo activo, timeframe y lado
```

con dos seguros:

- **Con menos de 30 estrategias no se centra** (m_pop = 0): una mediana de pocas no es una referencia.
- **El centro se recorta a ±0,35 en logaritmo** — una frecuencia que baja un 30 % o sube un 42 %. Lo que pase de ahí se queda en la z de cada estrategia. Motivo: en una población de plantilla todas son la misma idea y la mediana **es** la plantilla; sin tope, una plantilla entera que deja de operar en oos1 saldría con z ≈ 0.

**El estadístico.**

```
                ln(r2 / r1) − m_pop
z_frec = ─────────────────────────────────
           √( φ × ( 1/N1 + 1/N2 ) )
```

Es una z: a cuántos errores estándar está el cambio de frecuencia de la estrategia del de su población.

**Ejemplo.** Sin centrar (m_pop = 0; el centro de esta población está por calcular) y con φ = 2 de referencia (la φ de cada una también):

| | N1 | r1 | N2 | r2 | ln(r2/r1) | error Poisson | z con φ = 1 | z con φ = 2 | estado sin centrar |
|---|---|---|---|---|---|---|---|---|---|
| A | 329 | 39,7 | 196 | 49,0 | 0,21 | 0,090 | 2,33 | 1,65 | Limbo |
| B | 307 | 37,1 | 193 | 48,25 | 0,26 | 0,092 | 2,87 | 2,03 | Limbo |
| C | 189 | 22,8 | 98 | 24,5 | 0,07 | 0,124 | 0,57 | 0,41 | Pasa |

Las tres operan **más** en oos1 que en el build, lo que apunta a un efecto común. Si la mediana de la población hubiera operado un 15 % más (m_pop = 0,14, ilustrativo), la z de A bajaría a (0,21 − 0,14) / (0,090 × √2) ≈ 0,5: Pasa. Casi toda su subida sería del mercado.

**Las bandas en operaciones al año.** Estrategia de NIKKEI225 con **40 operaciones al año en el build** (8,28 años, N1 = 331), sin centrar. Entre paréntesis, el total de operaciones en oos1. Recalculadas para las bandas de 1,5 y 3,5.

*oos1 de 4 años (NIKKEI225)*

| φ | Falla | Limbo | **Pasa** | Limbo | Falla |
|---|---|---|---|---|---|
| 1,0 | < 27,2 (109) | 27,2–34,4 | **34,4–45,9** (137–184) | 45,9–54,3 | > 54,3 (217) |
| 1,5 | < 24,4 (98) | 24,4–33,1 | **33,1–47,3** (132–189) | 47,3–57,8 | > 57,8 (231) |
| 2,0 | < 22,1 (88) | 22,1–32,1 | **32,1–48,5** (128–194) | 48,5–60,8 | > 60,8 (243) |
| 2,5 | < 20,1 (80) | 20,1–31,2 | **31,2–49,5** (125–198) | 49,5–63,5 | > 63,5 (254) |
| 3,0 | < 18,3 (73) | 18,3–30,4 | **30,4–50,4** (121–202) | 50,4–66,0 | > 66,0 (264) |
| 3,5 | < 16,6 (66) | 16,6–29,6 | **29,6–51,3** (118–205) | 51,3–68,3 | > 68,3 (273) |

*oos1 de 3 años*

| φ | Falla | Limbo | **Pasa** | Limbo | Falla |
|---|---|---|---|---|---|
| 1,5 | < 22,6 (68) | 22,6–32,4 | **32,4–48,0** (97–144) | 48,0–59,6 | > 59,6 (179) |
| 2,0 | < 20,0 (60) | 20,0–31,2 | **31,2–49,3** (94–148) | 49,3–62,8 | > 62,8 (189) |
| 2,5 | < 17,6 (53) | 17,6–30,2 | **30,2–50,5** (91–151) | 50,5–65,8 | > 65,8 (197) |
| 3,0 | < 15,5 (46) | 15,5–29,3 | **29,3–51,5** (88–155) | 51,5–68,5 | > 68,5 (206) |
| 3,5 | < 13,4 (40) | 13,4–28,5 | **28,5–52,5** (85–157) | 52,5–71,1 | > 71,1 (213) |

*oos1 de 5 años (XAUUSD, forex; con el build de 8,28 años — con uno de 10 las bandas son algo más estrechas)*

| φ | Falla | Limbo | **Pasa** | Limbo | Falla |
|---|---|---|---|---|---|
| 1,5 | < 25,6 (128) | 25,6–33,6 | **33,6–46,8** (168–234) | 46,8–56,6 | > 56,6 (283) |
| 2,0 | < 23,5 (118) | 23,5–32,7 | **32,7–47,9** (163–239) | 47,9–59,4 | > 59,4 (297) |
| 2,5 | < 21,7 (108) | 21,7–31,8 | **31,8–48,9** (159–244) | 48,9–62,0 | > 62,0 (310) |
| 3,0 | < 20,0 (100) | 20,0–31,1 | **31,1–49,7** (155–249) | 49,7–64,3 | > 64,3 (322) |
| 3,5 | < 18,5 (93) | 18,5–30,4 | **30,4–50,6** (152–253) | 50,6–66,5 | > 66,5 (333) |

Cómo leerlas: las bandas son **asimétricas** en número de operaciones porque la prueba trabaja en logaritmo; con menos años de oos1 se ensanchan (con menos datos se exige menos precisión); y **el centrado lo desplaza todo** — si la mediana de la población operó un 15 % más en oos1, todas las bandas se multiplican por 1,15.

**Las líneas.**

| Pasa | Limbo | Falla |
|---|---|---|
| z en valor absoluto ≤ 1,5 | entre 1,5 y 3,5 | > 3,5 |

La franja de Pasa es estrecha y la de Limbo muy ancha a propósito: R5 **marca pronto** un cambio de frecuencia, pero sólo **descarta** cuando es muy grande (p a dos lados ≈ 0,0005 bajo el modelo).

**Parámetros.** Las dos líneas (1,5 y 3,5) · las cotas de φ (1,5 y 3,5) · el mínimo de estrategias para centrar (30) · el tope del centro (±0,35 en logaritmo).

**Lo que cuesta.** Recuentos: casi gratis. El centro se calcula sobre **toda** la población retesteada, no sólo sobre las que siguen vivas (es una de las dos excepciones de la cascada).

**Por medir.** La distribución real de φ en la población, para comprobar que el intervalo [1,5; 3,5] es razonable · el centro por activo, timeframe y lado · cuántas estrategias cambian de estado · si el ±0,35 se mantiene.

### 6.2 R5c — La ventaja frente al coste

Hechos: `edge_mean_oos`, `t_exceso_k`

**La pregunta.** Si el coste fuera peor de lo que SQX cobra, ¿la estrategia seguiría siendo distinguible del azar?

**Por qué cambia.** El `edge_mean` anterior tenía tres defectos: mezclaba el build (inflado por la selección de SQX) con oos1; devolvía arriba spread más slippage y dividía abajo sólo por el spread, de modo que en NIKKEI225 su punto de equilibrio era 1,70 y no 1; y, sobre todo, es **la media del P/L reescalada por el coste**, sin dividir por la desviación — contiene la misma información que la t, pero con más ruido. Para A (desviación ≈ 950 USD, coste ≈ 22 USD), su error estándar era de ≈ 3,1 con todo oos1 y de ≈ 6,2 con un año: por eso en la población no decidía nada.

**Cómo se calcula.** Dos números, los dos sólo sobre oos1.

```
bruto de la operación = P/L de la operación + coste que se le cobró (repreciado común)

edge_mean_oos = media del bruto / media del coste cobrado
```

Con el coste realmente pagado en el denominador, `edge_mean_oos = 1` es el punto de equilibrio y `2` significa de verdad «sobrevive a un coste doble».

```
                  media de e − (k − 1) × media del coste
t_exceso_k = ──────────────────────────────────────────────── × √(n efectivo)        k = 1,25
                              desv de e
```

Es **la t de R3 después de restarle a cada operación un 25 % más de coste** (con el mismo error estándar de 5.4). Dice si la estrategia sigue distinguiéndose del azar con costes peores, que es lo que importa; `edge_mean_oos` sólo dice si la media sigue siendo positiva.

**Por qué k = 1,25.** El coste que SQX ya cobra es el techo de lo medido en operaciones reales: 1,25 es **margen**, no una estimación de cuánto más caro va a ser.

**Ejemplo.** Con el exceso de hoy y el coste medio pagado de cada una (37,12, 37,50 y 36,71 USD; es la media de build y oos1 juntos, porque la de oos1 sola está por calcular: las cifras cambiarán ligeramente).

| | A | B | C |
|---|---|---|---|
| media de e (USD) | 172,33 | 140,17 | 40,82 |
| 25 % del coste (USD) | 9,28 | 9,38 | 9,18 |
| media de e con el coste × 1,25 | 163,05 | 130,80 | 31,64 |
| t(1) = R3 | 2,54 | 2,15 | 0,70 |
| **t(1,25)** | **2,40** | **2,01** | 0,54 |
| `edge_mean_oos` ≈ (media del P/L + coste) / coste | (196,25 + 37,12) / 37,12 = **6,3** | (165,09 + 37,50) / 37,50 = **5,4** | (47,86 + 36,71) / 36,71 = 2,3 |
| estado | Pasa | Pasa | (no llega: cayó en R3) |

Para comparar, la t de A con el coste × 1,5 sería 2,27 y con el coste doble, 1,99.

**Las líneas.**

| Pasa | Limbo | Falla |
|---|---|---|
| t(1,25) ≥ 1,65 **y** `edge_mean_oos` ≥ 2 | t(1,25) < 1,65, o `edge_mean_oos` entre 1,25 y 2 | `edge_mean_oos` < 1,25: no aguanta ni un 25 % más de coste |

No hay umbrales por año: con un error de ± 6 por año serían ruido. El análisis en el tiempo lo hace R5d.

**Parámetros.** k (1,25) y las líneas. **Coste:** nivel 1. **Por medir:** el coste pagado sólo en oos1; cuántas estrategias de las que pasan R3 bajan a Limbo por t(1,25).

### 6.3 R5d — La ventaja no se apaga dentro de oos1 (nueva)

Hechos: `t_b`, `e_fin`

**La pregunta.** ¿El exceso por operación va cayendo con el tiempo dentro de oos1?

**Cómo se calcula.** Una **regresión**: la recta que mejor se ajusta al exceso de cada operación contra su fecha de cierre `t_i`, en años.

```
e_i = a + b × (t_i − t medio) + error
```

- `a` es el exceso medio.
- `b` es la **pendiente**: cuánto cambia el exceso medio por año (USD por año). Negativa quiere decir que la ventaja se va apagando.
- `t_b = b / error estándar de b`: a cuántos errores estándar está la pendiente de cero, con la misma corrección de n efectivo que R3.
- `e_fin = a + b × T / 2`: el **exceso proyectado al final de oos1**, con `T` los años de oos1. Si es ≤ 0, al acabar el tramo ya no quedaba ventaja.

**Sólo dentro de oos1.** No se incluye el build: allí el exceso está inflado por la selección, y la caída del build a oos1 es esperable aunque la estrategia no se degrade. Mezclarlo fabricaría una pendiente negativa en casi todas.

**Centrado por población.** Si un año fue malo para todos los largos de un activo, la pendiente común no es degradación de una estrategia. A cada `b` se le resta la mediana `b_pop` de la población (las que llegaron al retest, mismo activo, timeframe y lado; mínimo 30 estrategias; con tope, cuyo valor está por proponer). Por eso la pendiente es **la única medida que hay que calcular para toda la población retesteada**, aunque la estrategia ya haya caído. Una cautela: la deriva por ventana de R3 ya quita de cada periodo lo que hizo el mercado, así que antes de restar otra vez se mide cuánto efecto común queda.

**Lo que esta prueba puede ver y lo que no.** Con operaciones repartidas uniformemente en `T` años:

```
error estándar de b = desv / ( √n × T / √12 )
```

Estrategia A (desv = 950, n = 196, T = 4):

```
error estándar de b = 950 / (14 × 1,155) = 58,8 USD por año
```

El intervalo al 95 % de `b` es ± 115 USD por año: ± 67 % de su exceso medio (172) **por año**. Una caída lineal de 344 a 0 USD en los cuatro años — la ventaja desaparece por completo — da b = −86 y t_b = −1,46: **no se detecta ni a 1,65**. Con oos1 y oos2 juntos (≈ 7 años, n ≈ 340) el error bajaría a 25,5 y la misma caída daría t_b ≈ −1,9.

Conclusión: en el paso 8 esta prueba **sólo detecta degradaciones catastróficas**. Las graduales quedan dentro del ruido con 3–4 años.

**Las líneas.**

| Pasa | Limbo | Falla |
|---|---|---|
| t_b ≥ −1,65 | t_b < −1,65 y e_fin > 0 | t_b < −1,65 **y** e_fin ≤ 0: se degrada, y al final de oos1 ya no queda ventaja |

**Parámetros.** Las líneas · el mínimo de estrategias para centrar (30) · el tope del centro (por proponer). **Coste:** nivel 1, para toda la población retesteada. **Por medir:** cuánto efecto común queda tras la deriva por ventana · el tope del centrado, en las unidades de `b_pop`, con las poblaciones de prueba · los valores de A y B.

### 6.4 R8 — La ventaja no depende de un trimestre ni de tres operaciones

Hechos: `t_sin_mejor_trimestre`, `t_sin_3_mejores`

**La pregunta.** Si quito lo mejor que le pasó, ¿sigue habiendo ventaja?

**Por qué cambia.** La regla anterior dividía el beneficio del mejor trimestre por el beneficio total. Cuando la t es pequeña ese total está cerca de cero y el cociente explota (hay un caso de 59.693 en la población): medía sobre todo lo pequeño que es el total, que ya mide R3.

**Cómo se calcula.** La t de R3, dos veces más:

```
t_sin_mejor_trimestre = t de R3 sobre oos1 quitando las operaciones del mejor trimestre natural
                        (el de mayor exceso total)

t_sin_3_mejores       = t de R3 sobre oos1 quitando las tres operaciones de mayor exceso
```

Misma escala que R3, sin unidades nuevas y sin dividir por totales pequeños. La segunda es la bandera roja de Chande (la mayor ganancia por encima del 40–50 % del beneficio) sin el problema del cociente.

**Ejemplo.** Con la regla anterior, el mejor trimestre de A era el 21 % de su beneficio, el de B el 22 % y el de C el 64 %. La t nueva de A y B está por calcular. De C, una cuenta aproximada: sin su mejor trimestre (3.021 USD de un total de 4.690) le quedan ≈ 1.670 USD en ≈ 90 operaciones; descontada la deriva, un exceso medio de ≈ 11 USD con desviación ≈ 576, y una t de ≈ 0,2. (C no llega a esta regla: cae antes en R3.)

**Las líneas.**

| Pasa | Limbo | Falla |
|---|---|---|
| las dos ≥ 1,65 | alguna entre 0 y 1,65 | alguna ≤ 0: todo el exceso venía de un trimestre o de tres operaciones |

**Aviso: aquí 1,65 no es p = 0,05.** Quitar lo mejor **baja la t de cualquiera**, también la de una estrategia buena, y deja la distribución con sesgo negativo, que el error estándar de R3 corrige a su vez hacia abajo. Las líneas son puntos de partida; lo que cuestan en estrategias buenas lo dicen las poblaciones de prueba.

**Parámetros.** Operaciones que se quitan (3) · periodo que se quita (trimestre) · las líneas. **Coste:** nivel 1. **Por medir:** el coste en buenas de cada línea; si conviene quitar un número proporcional (por ejemplo el 2 % de n) en lugar de 3.

### 6.5 R9b — La MAE típica mala

Hecho: `mae_p95_r`

**La pregunta.** ¿El riesgo que la estrategia toma es el que se cree tomar?

**Qué es la MAE.** La **máxima excursión adversa**: lo máximo que una operación llegó a ir perdiendo mientras estaba abierta, aunque después cerrara mejor. La doctrina no lleva stop fijo, así que 1R es nominal; la MAE mide cuánto se aparta el riesgo real del nominal.

**Por qué cambia.** La regla anterior miraba **la peor** operación. Ese mínimo se apoya en una sola operación, empeora sólo por tener más operaciones (más oportunidades de ver una mala), y su efecto sobre la cuenta ya lo recoge el peor día. Lo que interesa en la puerta es la parte **sistemática**: si la operación mala *típica* va mucho más allá de 1R.

**Cómo se calcula.**

```
mae_p95_r = percentil 95 de ( MAE de la operación en valor absoluto / 1R ), sobre las operaciones de oos1
```

El **percentil 95** es el valor que deja por debajo al 95 % de las operaciones: una de cada veinte fue peor. Con 196 operaciones se apoya en unas 10, frente a 1 del mínimo: es un número estable.

**Ejemplo.** La peor MAE guardada es −2,62R en A, −2,52R en B y −1,74R en C. El percentil 95 de las tres está por calcular; será menor que esas cifras.

**Las líneas.**

| Pasa | Limbo | Falla |
|---|---|---|
| ≤ 1,5R | entre 1,5R y 2,5R | > 2,5R: el riesgo real es sistemáticamente más del doble del nominal |

**Parámetros.** El percentil (95) y las líneas. **Coste:** nivel 1. **Por medir:** las líneas son orientativas: hay que ver dónde cae el p95 en la población. La única referencia es que la mediana de la **peor** MAE de la población es −3,72R.

### 6.6 Calidad de datos — La ventaja no vive de un defecto del histórico

Hechos: `ret_datos`, `t_A`

**La pregunta.** ¿Cuánta ventaja queda si quito las operaciones que tocan datos defectuosos?

**Por qué.** Una ventaja que sale de operaciones que tocan huecos, picos o velas imposibles no se va a repetir con el feed de la fondeadora. Antes sólo anotaba, con una prueba de permutación que no podía ver nada: si sólo 5 operaciones tocan una anomalía, la prueba nunca sale significativa **aunque esas 5 sean todo el beneficio**.

**Cómo se calcula.**

1. Se marcan las operaciones de oos1 que tocan una anomalía del histórico entre su barra de entrada y la de salida, las dos incluidas: el conjunto `A`, con `n_A` operaciones. El inventario de anomalías se calcula una vez por activo y timeframe.
2. Retención de la ventaja sin ellas:

```
ret_datos = media de e sin las operaciones afectadas / media de e con todas
```

1 = la ventaja no cambia; 0,5 = la mitad estaba en las afectadas; ≤ 0 = estaba toda.

3. ¿Las afectadas ganan más que el resto? Una **t de Welch**: la diferencia entre las medias de dos grupos, dividida por su error estándar, sin suponer que los dos grupos tienen la misma desviación ni el mismo tamaño (aquí uno tiene un puñado de operaciones y el otro casi todas):

```
              media de e en A − media de e en el resto
t_A = ───────────────────────────────────────────────────────
        √( desv_A² / n_A + desv_resto² / n_resto )
```

Se anotan además la t de R3 sin las afectadas y la fracción del exceso total que viene de `A`.

**Ejemplo (números inventados, para leer la regla).** Una estrategia con 196 operaciones y exceso medio 172 USD (33.712 en total), de las que 6 tocan una anomalía.

| | caso 1 | caso 2 |
|---|---|---|
| exceso medio de las 6 afectadas | 3.000 | 4.500 |
| exceso medio de las otras 190 | (33.712 − 18.000) / 190 = 82,7 | (33.712 − 27.000) / 190 = 35,3 |
| `ret_datos` | 82,7 / 172 = **0,48** | 35,3 / 172 = **0,21** |
| `t_A` (desv 1.500 en A, 900 en el resto) | 4,7 | 7,2 |
| estado | **Limbo** | **Falla** |

En el caso 2, seis operaciones de 196 llevan cuatro quintas partes de la ventaja, y la diferencia con el resto no es ruido.

**Las líneas.**

| Pasa | Limbo | Falla |
|---|---|---|
| ret ≥ 0,60, o ninguna operación afectada | ret entre 0,25 y 0,60, o ret < 0,25 con t_A ≤ 1,65 | ret < 0,25 **y** t_A > 1,65: la ventaja estaba en los datos malos |

**La solución de fondo** es otra: si un activo tiene muchas anomalías, se arregla **una vez en los datos**, antes de construir. Esta regla es la red para lo que se escape.

**Parámetros.** Las líneas (0,60 y 0,25, las mismas del retraso). **Coste:** nivel 1; el inventario de anomalías, una vez por activo y timeframe. **Por medir antes de activarla:** qué cuenta hoy como anomalía en `studies/data/feedQuality` · **por qué el estudio no dejó datos en la corrida de ejemplo** · el inventario por activo, que dice además dónde merece la pena limpiar el histórico.

---

## 7. Nivel 2 — El retraso de una barra

Hechos: `retraso_ret_min`, `retraso_t_delta`

**La pregunta.** ¿La ventaja sobrevive a mover la operación una barra?

**Por qué es regla.** Las cuentas de fondeo y los brókers tienen **feeds distintos**: barras con otro horario de cierre, otros huecos, otros máximos y mínimos, a veces desplazadas. La misma señal puede dispararse una barra antes o después. **Si la estrategia se rompe sólo por mover una barra, no es operable**: su ventaja depende de un detalle del histórico que en real no se va a reproducir. Por eso puede descartar, aunque una barra de M30 o H1 sea un desplazamiento grande.

**Las variantes.** Sobre cada operación de oos1, en el timeframe de la estrategia:

| variante | entrada | salida | qué simula |
|---|---|---|---|
| **E+1** | apertura de la barra siguiente a la original | la original | la señal de entrada llega una barra tarde |
| **S+1** | la original | apertura de la barra siguiente a la original | la señal de salida llega una barra tarde |
| **ES+1** | una barra tarde | una barra tarde | un feed con las barras corridas |

Cada variante se reprecia con el **repreciado común** (apartado 3): precio de apertura de la barra que toque y los costes de SQX. Los lotes son los de la operación original (una barra de diferencia en la volatilidad no cambia el tamaño de forma apreciable). La deriva se recalcula con la nueva duración, igual que en R3.

**Las medidas.** Con `e_i` el exceso original y `e_i(v)` el de la variante `v`:

```
ret(v) = media de e(v) / media de e                     (retención de la ventaja)

Δ_i = e_i − e_i(v)                                      (lo que pierde cada operación al desplazarla)

t_Δ(v) = media de Δ / ( desv de Δ / √n )                (t pareada)
```

La **t pareada** compara cada operación consigo misma desplazada, en lugar de comparar dos grupos de operaciones distintas. Como casi todo lo que hace bailar a una operación (el día, el régimen, su tamaño) es igual en las dos versiones, la diferencia `Δ` baila mucho menos que cada exceso por separado, y la prueba ve caídas que una comparación normal no vería. `t_Δ > 1,65` dice que la pérdida al desplazar es real y no ruido.

**Se juzga la peor variante**, la de menor retención: `retraso_ret_min` y su `retraso_t_delta`. Se guardan también qué variante fue y la t de R3 de cada variante.

**Por qué no se exige simplemente que la t desplazada siga en 1,65.** Con una t original de 2,33, retener el 60 % de la ventaja deja la desplazada en ≈ 1,4: exigir 1,65 obligaría a partir de 2,75, y el retraso estaría juzgando otra vez la ventaja, que ya juzga R3. La retención y la t pareada aíslan la pregunta: *¿cuánto de la ventaja depende de la barra exacta?*

**Ejemplo (números inventados, para leer la regla).** Estrategia con exceso medio 172 USD y n = 196:

| variante | media de e(v) | ret | t_Δ | lectura |
|---|---|---|---|---|
| E+1 | 140 | 0,81 | 1,2 | apenas cambia |
| S+1 | 155 | 0,90 | 0,7 | apenas cambia |
| ES+1 | 118 | 0,69 | 2,0 | pierde algo, de forma real, pero conserva dos tercios |
| **peor** | | **0,69** | | **Pasa** |

Si en E+1 el exceso cayera a 30 USD (ret = 0,17) con t_Δ = 3,5: **Falla**. Toda la ventaja estaba en entrar en esa barra exacta.

**Las líneas (sobre la peor variante).**

| Pasa | Limbo | Falla |
|---|---|---|
| ret ≥ 0,60 | ret entre 0,25 y 0,60, o ret < 0,25 con t_Δ ≤ 1,65 (caída grande pero no distinguible del ruido) | ret < 0,25 **y** t_Δ > 1,65: pierde más de tres cuartos de la ventaja al mover una barra, y la caída es real |

**La limitación.** En Python se desplazan las marcas de tiempo, pero no se vuelve a ejecutar la lógica de la estrategia: si la salida depende de reglas sobre el precio (un objetivo, un trailing), la salida desplazada es una aproximación. La versión exacta es un retest en SQX con la ejecución retrasada, para las finalistas; queda fuera de este trabajo, igual que la prueba con el feed real de la firma, que es del módulo de fondeo.

**Lo que sólo anota.** El e-ratio de `studies/readings/entryQuality` — si tras la entrada el precio se mueve más a favor que en contra, frente a entradas al azar a las mismas horas — se sigue calculando como diagnóstico: un e-ratio alto en las primeras barras con una retención baja en E+1 dice que la ventaja está concentrada en el primer movimiento tras la señal, la parte más frágil en real.

**Parámetros.** Variantes activas (E+1, S+1, ES+1) · las líneas (0,60 y 0,25). Apagadas, como opción: E−1 (entrada una barra antes) y la versión sobre el build.

**Lo que cuesta.** Nivel 2: repreciar tres veces sobre barras cada operación de oos1. Sólo llegan las que siguen sin Falla tras el nivel 1.

**Por medir antes de activarla.** **Por qué `entryQuality` no dejó datos en la corrida de ejemplo** · la distribución de `retraso_ret_min` entre las que pasan R3, para calibrar 0,60 y 0,25.

---

## 8. Nivel 3 — pruebas de remuestreo

Las tres repiten un cálculo miles de veces. **Toda prueba con repeticiones lleva por defecto al menos 5.000**, con semilla fija y configurable: con la misma semilla, el mismo resultado.

### 8.1 R7 — El resultado es homogéneo en el tiempo

Hecho: `q_p`

**La pregunta.** ¿El exceso es parecido de un trimestre a otro, o depende de un régimen concreto?

**Por qué cambia.** Contar años positivos no discrimina: con 4 años, una moneda al aire saca 3 o más positivos el 31 % de las veces; con 5 años, 3 o más el 50 %. No pesa el tamaño: en C, el 2021 «positivo» son 213 USD (0,2R) y cuenta igual que un año de +16R. Y el «3» significa cosas distintas con 4 y con 5 años de oos1. Es, en el fondo, la t de R3 con menos potencia.

**Cómo se calcula.** Se agrupa el exceso por operación por **trimestre natural** de oos1: `K = 16` trimestres en NIKKEI225, `K = 20` en XAUUSD y forex. Los trimestres con menos de 5 operaciones se juntan con el siguiente.

```
        suma, sobre los K trimestres, de   n_k × ( media de e en el trimestre k − media de e total )²
Q = ───────────────────────────────────────────────────────────────────────────────────────────────────
                              varianza de e dentro de los trimestres
```

`Q` suma, trimestre a trimestre, cuánto se aparta su media de la media total, pesado por sus operaciones y medido en unidades de ruido. Si el exceso es homogéneo, Q ronda `K − 1`; un Q mucho mayor dice que algunos trimestres son muy distintos de los demás.

**La nula por permutación.** Para saber si un Q es «grande» hace falta saber qué Q da el puro azar. La teoría dice que sigue una ji-cuadrado, pero con colas gordas esa curva da demasiados positivos. Así que la referencia se fabrica con los propios datos: **se barajan las operaciones entre trimestres** (cada trimestre conserva su número de operaciones) y se recalcula Q, **5.000 veces**. Barajar destruye cualquier relación entre una operación y su trimestre, que es exactamente lo que afirma «el exceso es homogéneo»: las 5.000 Q barajadas son lo que se vería si eso fuera cierto.

```
q_p = ( número de barajadas con Q ≥ Q observado + 1 ) / ( 5.000 + 1 )
```

`q_p` es un p-valor: la proporción de mundos «homogéneos» que dan una heterogeneidad igual o mayor que la vista.

**Ejemplo (de juguete).** Cuatro trimestres de 10 operaciones, en R, con desviación 1 dentro de cada uno y media total 0,2:

| medias de los cuatro trimestres | Q | lectura |
|---|---|---|
| +0,6 · +0,1 · +0,2 · −0,1 | 10 × (0,16 + 0,01 + 0 + 0,09) = 2,6 | ronda K − 1 = 3: homogéneo |
| +1,4 · −0,2 · −0,2 · −0,2 | 10 × (1,44 + 0,16 + 0,16 + 0,16) = 19,2 | muy por encima: todo está en un trimestre |

Las dos tienen la misma media total. A, B y C no tienen todavía su Q.

**Las líneas.**

| Pasa | Limbo | Falla |
|---|---|---|
| q_p > 0,05 | q_p ≤ 0,05 | **nunca** |

No descarta porque algo de heterogeneidad entre regímenes es normal en trading, y con 3–5 años la potencia es baja.

**Parámetros.** Permutaciones (5.000) · periodo (trimestre) · semilla · la línea (0,05). **Coste:** nivel 3a, el remuestreo más ligero: sólo baraja etiquetas de trimestre. **Por medir:** con las dos ventanas de R3, porque la deriva por ventana ya resta parte de la diferencia entre trimestres.

### 8.2 R6 — El drawdown de oos1 es el esperable

Hecho: `dd_p` (y `gate.scorecard.dd_esperado_p95_r`, que se guarda para el módulo de fondeo)

**La pregunta.** *Con la ventaja que de verdad tuvo en oos1, ¿es normal un drawdown como el de oos1 para la forma de riesgo que la estrategia enseñó en el build?*

**Por qué cambia.** El cociente anterior (drawdown de oos1 entre drawdown del build) comparaba tramos de distinta duración — 8,3 años contra 4 en NIKKEI225, y el drawdown esperado crece con el número de operaciones, así que un cociente menor que 1 salía casi siempre por construcción —; mezclaba la caída de la ventaja con el cambio de riesgo; y por la cascada anterior no tenía dato en el 60 % de la población.

**De qué depende un drawdown.** De tres cosas: la **media** por operación (más media, recuperación más rápida), la **dispersión** (más dispersión, caídas más hondas) y el **orden**: si las pérdidas se agrupan, el drawdown es mucho mayor con la misma media y la misma dispersión. Hay una fórmula de referencia para un paseo sin agrupamiento (Magdon-Ismail y otros, 2004), con media `μ`, desviación `σ` y `n` operaciones:

```
drawdown esperado ≈ (2σ² / μ) × ( ln(x) / 4 + 0,49 )        x = μ² × n / (2σ²)
```

A en oos1 (μ = 196 USD, σ = 951 USD, n = 196): x = 4,17 y un drawdown esperado de ≈ 7.800 USD = 7,8R; el observado en su curva diaria fue 6,8R. La fórmula orienta, pero no ve el tercer punto, el agrupamiento, que es justo lo que hace que un drawdown se dispare. Por eso se usa un bootstrap por bloques.

**El método.**

*Paso 1 — Desplazar la media del build a la de oos1.* Con `x_i` las operaciones del build, en R:

```
y_i = x_i − media del build + media de oos1
```

El desplazamiento cambia la media y deja intactos la dispersión, las colas y el orden. Ejemplo de juguete (build con media 100 USD, oos1 con media 20: se resta 80 a cada una):

| build original | +300 | −100 | +200 | −200 | +400 | −150 | +250 | −50 | +350 | 0 |
|---|---|---|---|---|---|---|---|---|---|---|
| desplazada (−80) | +220 | −180 | +120 | −280 | +320 | −230 | +170 | −130 | +270 | −80 |

La curva original va 300, 200, 400, 200, 600, 450, 700, 650, 1.000, 1.000: drawdown máximo 200. La desplazada va 220, 40, 160, −120, 200, −30, 140, 10, 280, 200: drawdown máximo 340. Con las mismas operaciones y menos ventaja, el drawdown es un 70 % mayor.

*Por qué se desplaza.* Un drawdown mayor en oos1 puede venir de **menos ventaja** o de **un riesgo distinto** (pérdidas más grandes o más agrupadas). Lo primero ya lo juzgan R3 y R5d; desplazar la media lo neutraliza para que R6 juzgue sólo lo segundo. Es comparar a igualdad de ventaja, como la distancia de frenado de dos coches se compara a igual velocidad. Además la media del build casi siempre baja en oos1 aunque la estrategia sea buena — SQX eligió las mejores entre decenas de miles, y esa media lleva dentro la suerte de haber sido elegida —: sin desplazar, R6 castigaría a casi todas por haber sido seleccionadas.

*Por qué no se simula con las operaciones de oos1.* Se compararía el drawdown de oos1 consigo mismo, y la prueba no podría detectar ningún cambio.

*Paso 2 — Bootstrap por bloques.* Un **bootstrap** fabrica historias alternativas sacando operaciones al azar de las que hubo. Aquí se construyen **5.000 secuencias**, cada una de tantas operaciones como tuvo oos1, encadenando **bloques de 8 operaciones consecutivas** de `y` con inicio al azar. **Por qué bloques:** sacar las operaciones de una en una rompería las rachas — las pérdidas quedarían repartidas al azar — y subestimaría el drawdown. Un bloque de 8 consecutivas conserva dentro el orden real, y con él el agrupamiento de pérdidas que la estrategia enseñó en el build.

*Paso 3 — El percentil del drawdown observado.*

```
dd_p = ( número de secuencias con drawdown máximo ≥ el de oos1 + 1 ) / ( 5.000 + 1 )
```

`dd_p` dice **qué proporción de las historias simuladas tuvo un drawdown igual o peor que el real**. 0,53 quiere decir que el de oos1 es de lo más corriente; 0,01, que sólo una de cada cien historias con el riesgo del build fue tan mala: el riesgo ha cambiado. Todo en R, sobre el P/L de operaciones cerradas.

**Ejemplo (datos sintéticos).** Build: 330 operaciones, media 0,30R, desviación 0,81R, colas gordas. oos1: 196 operaciones, media 0,19R, desviación 0,95R, t = 2,77, beneficio final +37R. **Las dos versiones de oos1 tienen exactamente las mismas operaciones; sólo cambia el orden.** Simulación: build desplazado a media 0,19R, 5.000 secuencias de 196 operaciones, bloques de 8.

| | ejemplo 1 — se mantiene | ejemplo 2 — falla |
|---|---|---|
| orden de las operaciones | normal | las 14 peores pérdidas dentro de una ventana de 28 operaciones |
| media / desviación / t | 0,19R / 0,95R / 2,77 | 0,19R / 0,95R / 2,77 |
| racha perdedora más larga | 5 | 7 |
| **drawdown observado** | **5,6R** | **20,0R** |
| simulado: mediana / p90 / p95 / p99 | 5,8 / 9,8 / 11,2 / 15,1 R | 5,8 / 9,8 / 11,3 / 15,2 R |
| `dd_p` | 0,53 | 0,0012 |
| **estado** | **Pasa** | **Falla** |

Lo que enseña:

- **R3 no distingue los dos casos**: media, desviación, t y beneficio final son idénticos. La t mira el conjunto de operaciones; el drawdown, su orden. R6 aporta algo que no mide ninguna otra regla.
- **La racha perdedora más larga apenas cambia** (5 frente a 7). Lo que dispara el drawdown es la *densidad* de pérdidas en una ventana, no una racha seguida.
- **Lo que pasaría sin desplazar la media.** Simulando con la media del build (0,30R), la mediana simulada del ejemplo 1 baja de 5,8R a 4,3R y el p99 de 15,1R a 11,9R: el 5,6R observado parecería un 30 % peor de lo esperado, y esa diferencia es entera por la caída de la ventaja, no por el riesgo.
- **Para fondeo:** el percentil 95 simulado del ejemplo 1 (11,2R) es el doble del drawdown observado (5,6R). Ese p95 es el drawdown que cabe esperar en el próximo tramo de igual duración, y es el que se guarda.

**Lo que no es.** No es un nulo de entrada al azar: remuestrea operaciones **de la propia estrategia**. Por eso puede usar el build sin romper la regla de «el trader al azar, sólo en OOS».

**Las líneas.**

| Pasa | Limbo | Falla |
|---|---|---|
| dd_p > 0,10 | entre 0,01 y 0,10 | ≤ 0,01 |

**Parámetros.** Longitud de bloque (8) · secuencias (5.000) · semilla · las líneas. **Coste:** nivel 3b: 5.000 secuencias por estrategia. **Por medir:** la sensibilidad de `dd_p` a la longitud de bloque · los valores de A, B y C (el drawdown de 6,8R de A es el de su curva diaria; el de operaciones cerradas está por calcular).

### 8.3 El mono — El control de R3

Hecho: `z_mono`

**La pregunta.** ¿La estrategia gana a entrar al azar, **sin suponer** que las operaciones tienen forma normal?

**Qué es.** Un «trader al azar» que hace el mismo número de operaciones, del mismo lado y con las mismas duraciones, pero **entrando en momentos sorteados**. Repetido miles de veces, da la distribución de lo que gana alguien sin habilidad en ese mercado y en esos años.

**Por qué no es una regla aparte.** El resultado esperado de una entrada al azar del mismo lado, duración y tamaño es:

```
P/L esperado de un mono = lado × μ × barras × lotes × valor del punto − costes
```

Es **la deriva de R3** menos los costes. El mono contrasta la misma hipótesis que R3 («la entrada no vale más que una al azar»), sacando la referencia del mercado real en lugar de una fórmula. Lo medido lo confirma: de las 325 estrategias con t ≥ 1,65, 318 ya ganaban al mono con p ≤ 0,05 (las otras 7 no tenían dato), y pedirlo como regla daba un lift de +5 por cada 1.000: nada. Su sitio es ser **la versión no paramétrica de R3**: si las dos discrepan, algo falla en los supuestos de R3 — las colas, el sesgo del tamaño o la deriva por régimen.

**Los tres cambios.**

1. **El tamaño sigue la regla de la doctrina, no se copia.** Antes cada entrada sorteada recibía los lotes de la operación real. Pero esos lotes se calcularon con la volatilidad del momento real; movidos a otra barra, el mono queda mal dimensionado y hereda el mismo sesgo que el término de deriva. Ahora el mono **dimensiona su entrada sorteada con la regla de la doctrina en *su* momento** (inverso de la volatilidad, mismo 1R): reproduce lo que ganaría una estrategia sin habilidad con tu forma de dimensionar.
2. **El sorteo va dentro de la ventana.** Cada entrada se sortea **dentro de la misma ventana de calendario que la operación real**, y esa ventana es **la misma que la de la deriva de R3**: un solo parámetro para los dos. Así el mono mide si la entrada es buena *dentro de su régimen*, no si la estrategia estuvo más tiempo dentro en los años buenos.
3. **Una z continua en lugar de un p.** Con 2.500 sorteos el p más pequeño posible era 1 / 2.501 = 0,0004: A estaba en ese suelo, y el mono no podía ordenar a las buenas.

```
              media por operación de la estrategia − media de esa media entre los monos
z_mono = ────────────────────────────────────────────────────────────────────────────────
                       desviación de esa media entre los monos
```

Con **5.000 sorteos** la media y la desviación de los monos están muy bien estimadas: la z no tiene suelo, y está en **la misma escala que la t de R3**, así que se comparan directamente. El p empírico se guarda de dato secundario, para ver si la cola de los monos se aparta de la normal.

Todo repreciado con el repreciado común, y **sólo sobre oos1**: en el build no significa nada, porque SQX eligió la estrategia precisamente por ganar ahí.

**Su papel en la puerta.**

- **Sólo se calcula para las que pasan R3.** Por debajo de t 1,65 la estrategia ya es Falla y el mono no se calcula.
- **Sólo puede bajarlas a Limbo.** Pasa R3 y pierde con el mono (z < 1,65) → Limbo. Nunca descarta por sí solo, y nunca rescata a una que R3 tiró.

**Las líneas.**

| Pasa | Limbo | Falla |
|---|---|---|
| z_mono ≥ 1,65 | z_mono < 1,65 | **nunca** |

**Los cuatro peldaños, sólo para anotar.** Según lo que se deja al azar: sólo el momento (*timing*), el momento y la duración, el momento y el tamaño, o todo (*free*). Una z parecida en *timing* y en *free* dice que la ventaja está en **cuándo entra**; una z alta sólo en *free*, que está en la duración o el tamaño, no en la entrada.

**Ejemplo.** Con el mono anterior, A tenía p = 0,0004 (ningún mono de 2.500 la igualó), B 0,0032 y C 0,097 (la iguala uno de cada diez). La z de las tres está por calcular, y antes hay que cerrar la auditoría del repreciado (apartado 3.3).

**Parámetros.** Sorteos (5.000) · la ventana (la de R3) · semilla · la línea (1,65).

**Lo que cuesta.** Nivel 3c: es **la prueba más cara** — 5.000 sorteos, cada uno repreciado sobre barras y redimensionado — y por eso va la última. Su coste con 5.000 sorteos contra el de hoy se mide y queda en `perf/`.

**Por medir.** La auditoría del repreciado · cuántas de las que pasan R3 discrepan con el mono · el coste.

**Lo que queda fuera.** El mono en mercados adicionales — donde todo el histórico es fuera de muestra —, la combinación de varios mercados con Stouffer y `oos2` son un comentario para más adelante, no parte de esta puerta (apartado 15).

---

## 9. El orden de cálculo: la cascada

### 9.1 La idea

Las reglas se evalúan **de la más barata a la más cara**. En cuanto una estrategia da **Falla** en una regla, sale y no se le calcula nada más. Las que dan **Limbo siguen adelante**.

### 9.2 Los niveles

| nivel | qué cuesta | reglas | notas |
|---|---|---|---|
| **0** | metadatos y recuentos | R1a · R1b · R2 · R4a · R5b | instantáneo; aquí cae buena parte de la población |
| **1a** | una pasada sobre las operaciones | **R3** | la que más descarta: va la primera de su nivel |
| **1b** | una pasada | R5 · R5c · R5d · R8 · R9b · calidad de datos | comparten el exceso de R3; el inventario de anomalías, una vez por activo y timeframe |
| **2** | repreciado sobre barras | retraso de una barra (3 variantes) | |
| **3a** | remuestreo ligero | R7 (5.000 permutaciones) | sólo baraja etiquetas de trimestre |
| **3b** | remuestreo medio | R6 (5.000 secuencias) | guarda también el drawdown esperado para fondeo |
| **3c** | remuestreo caro | mono (5.000 sorteos repreciados) | el más caro: el último |

Dentro de un mismo nivel va primero la regla que más descarta: a igual coste, la que más elimina ahorra más a las siguientes.

### 9.3 Por qué el veredicto es exactamente el mismo

El resultado de una estrategia es el de su peor regla, y **no hay nada peor que Falla**. Una estrategia con un Falla en el nivel 0 es Falla diga lo que diga el nivel 3: calcularlo no puede cambiar su veredicto. Lo único que cambia es que a las descartadas les faltan los hechos de las reglas posteriores, que no importa para seleccionar. Sí importa para **calibrar** — y por eso existe el interruptor de 9.6.

Se comprueba, no se supone: la cascada encendida y apagada tienen que dar **el mismo veredicto para toda una población real**.

### 9.4 Cuánto ahorra

Tras el nivel 0 y R3 queda alrededor del **3 % de la población**: en la corrida de ejemplo, **326 de 10.000** (325 con t ≥ 1,65 y una sin dato). Las pruebas del nivel 3, que son el grueso del coste, corren sobre unas 300 estrategias en lugar de 10.000. El coste total de la puerta queda por debajo del que tenía el mono anterior sobre toda la población. Los tiempos de cada nivel se miden al implementarlo y quedan en `perf/`.

Lo que cada regla del nivel 0 quita en esa corrida, con las reglas y los datos de hoy (una misma estrategia puede caer por varias): R1b, 142 · R2, 3.912 · R4a, 2.241. R3 da Falla a 9.674.

### 9.5 El embudo

De cada estrategia se registra **en qué nivel y en qué regla cayó** (su primer Falla). Sumado, es el embudo: cuántas entran en cada nivel, cuántas salen y por qué regla. Dice qué reglas trabajan y cuáles no deciden nada, y la ventana lo enseña.

### 9.6 El interruptor que la apaga

Un parámetro de configuración apaga la cascada: entonces **se calcula todo para todas**. Así corren las dos poblaciones de prueba del apartado 10 y cualquier estudio de calibración, porque sin eso no se puede medir el efecto de cada regla por separado.

### 9.7 Las dos excepciones al orden

Dos medidas se calculan sobre **toda la población retesteada**, aunque la estrategia ya haya caído, porque sirven para centrar a las demás:

- **El centro de R5** — la mediana del cambio de frecuencia. Son recuentos: gratis.
- **La pendiente de R5d** — para su mediana poblacional. Es una pasada sobre las operaciones.

### 9.8 «No calculado» no es «falta»

Un hecho que **falta** es Limbo. Un hecho **no calculado** porque la cascada ya había sacado a la estrategia no es ni Limbo ni nada: la estrategia es Falla por su regla. El juez distingue los dos casos; si no lo hiciera, convertiría en Limbo justo a las que acababa de descartar. Ejemplo: D cae en el nivel 0 por R4a; su t de 3,14 ya no se calcula, y eso no la devuelve al Limbo.

### 9.9 Lo que tiene que cumplir

Cada nivel se puede ejecutar sin rehacer los anteriores. La puerta entera sigue corriendo sola dentro de `bin/workflow.sh`. El fallo de identidades de R1a tiene que estar arreglado antes de montarla: hoy hace caer estrategias en el nivel 0 por error.

---

## 10. Las dos poblaciones de prueba

### 10.1 Por qué hacen falta

Ninguna línea se congela hasta medir qué hacen **todas las reglas juntas**. Cada regla añadida es otra oportunidad de descartar una estrategia buena por mala suerte. Si ocho reglas perdieran cada una un 5 % de las buenas y fueran independientes:

```
1 − 0,95⁸ ≈ 34 %
```

Un tercio de las buenas fuera sólo por acumular filtros. Una medida lo dice; un razonamiento, no.

### 10.2 Cuáles son

| población | qué es | qué mide |
|---|---|---|
| **nula** | estrategias sin ventaja | cuántas pasan la cadena entera por suerte: la tasa real de falsos positivos de la puerta, y la de cada regla |
| **de ventaja plantada** | operaciones nulas a las que se añade un exceso conocido, de Sharpe por operación **0,05, 0,10 y 0,15** | cuántas buenas se pierden y **en qué regla**: la potencia real |

Al menos **5.000 estrategias por nivel**, construidas sobre las operaciones de poblaciones ya cosechadas a los costes del 2026-10-04. Es Python sobre operaciones que ya existen: no se lanza SQX. El sitio es `studies/screening/falsePositives/`. Las dos corren con **la cascada apagada**.

Como referencia de lo que cabe esperar sólo de R3, la fórmula de 2.6 con 196 operaciones da una potencia del 17 % para 0,05, del 40 % para 0,10 y del 67 % para 0,15. Lo que las demás reglas quitan encima de eso es lo que no se sabe.

### 10.3 Lo que se te entrega

Por regla y por nivel de ventaja, la proporción en Pasa, Limbo y Falla; el embudo de la cadena; y, para cada línea, la propuesta con su coste al lado — «a 1,65 pierde el X % de las de 0,10 y deja pasar el Y % de las nulas». Ahí entra también lo que las reglas dejan pendiente: la ventana y la variante de R3, el tope del centrado de R5d, las líneas de R8.

### 10.4 El orden

Con esos números **fijas tú las líneas**. Un umbral que congeles pasa a ser una fila al final de su sección en `ledger/thresholds.yaml`. **Después**, y sólo cuando lo digas, se apaga `dev.on`. Hasta entonces la puerta calcula y anota, pero lo que sigue al paso 9 es un sorteo.

---

## 11. Todos los parámetros, con su valor de partida

**Ninguna cifra vive en el código, y todas se editan desde la ventana**, cada una con su frase de ayuda (qué es y qué pasa si se sube o se baja). Las líneas se guardan en `criteria.yaml`; los parámetros de cálculo, en el `config.yaml` de su estudio, conservando los comentarios. Se usa el mecanismo que la ventana ya tiene para editar las líneas de una regla y los parámetros de un estudio; no se abre un editor nuevo. Un parámetro que no esté en la ventana no está terminado.

| parámetro | valor de partida | de quién |
|---|---|---|
| líneas de Pasa / Limbo / Falla de cada regla | las de la tabla 0.3 | `criteria.yaml` |
| ventana de la deriva de R3 y del sorteo del mono | la que elijas (año o semestre); mínimo un trimestre | puerta |
| variante del término de deriva | la que salga de la medida de 5.5 | puerta |
| error estándar con sesgo y curtosis | encendido | puerta |
| R5: cotas de φ | 1,5 y 3,5 | puerta |
| centrado: mínimo de estrategias | 30 | puerta |
| centrado: tope del centro | ±0,35 en logaritmo (R5); el de R5d, por proponer | puerta |
| R5c: k del coste estresado | 1,25 | puerta |
| R8: operaciones que se quitan · periodo que se quita | 3 · trimestre | puerta |
| R9b: percentil de la MAE | 95 | puerta |
| calidad de datos y retraso: variantes activas | E+1, S+1, ES+1 | su estudio |
| R7: permutaciones · periodo | 5.000 · trimestre | puerta |
| R6: longitud de bloque · secuencias | 8 · 5.000 | puerta |
| mono: sorteos | 5.000 | puerta |
| semilla de cada remuestreo | fija | su estudio |
| cascada | encendida | puerta |
| poblaciones de prueba: estrategias por nivel · niveles de ventaja | 5.000 · 0,05, 0,10, 0,15 | `falsePositives` |

---

## 12. Lo que se quita, y adónde va lo que medía

«Se elimina» es borrar del todo: el código, su fila en la ventana, su paso en el piloto automático, su objetivo de rendimiento, sus tests y su capítulo del manual.

| qué se quita | por qué | dónde queda lo que medía |
|---|---|---|
| **R2b**, el neto al spread de Darwinex | dependía de un spread que no es realista en algunos activos. No era la única regla que descartara a ninguna estrategia | los costes de SQX recalibrados; el margen, en R5c |
| **R4b**, el techo de 75 operaciones al año | no descartaba a ninguna | — |
| **R9a** y **R9c** como reglas | son dimensionado, no validación | módulo de fondeo (apartado 13); sus hechos se siguen calculando |
| **el espionaje de datos** (`snoopingScreen`) y la criba `familia` | como regla por estrategia no puede decir nada en esta cadena: la mejor t de la población (3,14) está por debajo del máximo que da el ruido con 10.000 estrategias (≈ 3,7), así que ninguna prueba de comparaciones múltiples va a nombrar a nadie | — |
| **la forma del beneficio** (`profitShape`) | todo lo que medía está en otra regla | la concentración en las mayores ganadoras → `t_sin_3_mejores` (R8) · la autocorrelación → el n efectivo de R3 · la rotura de la curva → la pendiente de R5d |
| **el repreciado al spread de Darwinex** | sólo la mitad del paso 8 del estudio del spread | el repreciado común (apartado 3). **Se queda entero lo del paso 4**: el escaneo de spreads, el alta de activos, las bandas del MC Retest y el swap de fondeo |
| **`edge_median`** y **`n`** de `edgeCost` | la mediana castiga a los sistemas de tendencia sin medir la ventaja; `n` era el total de build más oos1 | la dependencia de pocas operaciones grandes → `t_sin_3_mejores` (R8) |

Un cuidado al borrar la mitad del spread: el fichero de operaciones que ese estudio deja es hoy **el único sitio donde quedan las operaciones de toda la población** después de la cosecha. R3 y todo lo que viene detrás las necesitan, así que la puerta pasa a guardarlas ella antes de que ese fichero desaparezca.

---

## 13. Lo que se deja al módulo de fondeo

R9a (el peor día) y R9c (el drawdown frente al neto anual) no dicen si la estrategia tiene ventaja, sino **cuánto riesgo se le puede poner** dentro de los límites de una cuenta. Además usaban el extremo observado, que empeora sólo por tener más días y **no acota el futuro**: con unos 1.000 días de oos1, el peor día visto es más o menos el de uno entre mil; el que rompe una cuenta puede ser el de uno entre cinco mil, todavía no visto. Y el límite diario real se juega **por cartera**, con varias estrategias abiertas a la vez, no estrategia a estrategia.

El paso 8 **calcula y no juzga**. Cuando una estrategia **pasa el WFM** se guardan, en la raíz de datos:

| dato | de dónde sale |
|---|---|
| la curva diaria de flotante de oos1 | hoy sólo se conserva de las del sorteo |
| `oos_worst_day_r`, el peor día en R | como hoy |
| `gate.scorecard.dd_esperado_p95_r`, el percentil 95 del drawdown simulado | el bootstrap de R6 |
| el neto anual en R | oos1 |

El módulo es otro encargo, `docs/encargos/45-modulo-de-fondeo.md`, todavía en redacción. **Desde que estas reglas salgan y hasta que ese módulo exista, nada en la cadena juzga el peor día ni el drawdown sobre el neto.** Ese hueco está aceptado. El caso grave — pérdidas sistemáticamente mucho mayores de 1R — lo sigue cortando R9b en la puerta.

---

## 14. Lo que queda por decidir y el orden de trabajo

### 14.1 Decisiones tuyas, que se te llevan con números

Las de diseño están cerradas. Quedan las de **calibración**:

| decisión | con qué números llega | de qué parte sale |
|---|---|---|
| **la ventana de la deriva**: año o semestre | sesgo, falsos positivos a 1,65 y cambios de veredicto de las cuatro variantes, año y semestre lado a lado | la medida de R3 |
| **las líneas definitivas** de cada regla | el embudo de las dos poblaciones, cada línea con su coste en estrategias | poblaciones de prueba |
| **el tope del centrado de R5d**, y si el ±0,35 de R5 se mantiene | la distribución del centro en las poblaciones | poblaciones de prueba |
| **H1 y H4** | R3 no lleva ninguna excepción por timeframe y las reglas nuevas nacen sin ellas (la única que queda es la de R4a en H4). Si las poblaciones enseñan que una regla se comporta distinto en un timeframe, se te propone; no se carga | poblaciones de prueba |
| **R1b**: un suelo absoluto de 60–80 operaciones en oos1 | sólo si los números lo piden | poblaciones de prueba |
| **apagar `dev.on`** | cuando las líneas estén fijadas | — |

Y cualquier punto donde esta especificación admita dos lecturas al implementarla: se pregunta, no se elige la común.

### 14.2 El orden de trabajo

1. **El inventario**: por cada regla, qué hay hoy implementado y a qué distancia está de lo especificado.
2. **Las identidades entre el build y el retest** (R1a). Ningún recuento vale antes.
3. **La auditoría del repreciado del mono** y el repreciado común.
4. **R3**: la deriva por ventana, la medida de las cuatro variantes, el error estándar nuevo junto al n efectivo, la línea única.
5. **Las reglas del nivel 1b**, antes averiguando por qué `feedQuality` no dejó datos.
6. **El retraso de una barra**, antes averiguando por qué `entryQuality` no dejó datos.
7. **Las pruebas de remuestreo**: R7, R6 y el mono.
8. **Los borrados** del apartado 12.
9. **La cascada y el juez**.
10. **Todos los parámetros en la ventana**.
11. **Las dos poblaciones de prueba**, las líneas propuestas con su coste, y — cuando lo digas — `dev.on`.
12. **El guardado para el módulo de fondeo**.
13. **La documentación**: este documento se actualiza con lo que las medidas cambien y con las líneas congeladas.

---

## 15. El límite que no cambia

Con las reglas nuevas sigue siendo cierto: **pasar el paso 8 hace a una estrategia candidata, no válida.**

- **La potencia es baja y ninguna regla lo arregla.** Con 3–5 años de oos1, una ventaja real de 0,10 por operación supera la línea de R3 cuatro veces de cada diez con las operaciones de A (apartado 2.6); una de 0,05, menos de dos de cada diez.
- **La búsqueda sigue ahí.** En la población de ejemplo, la mejor t (3,14) queda por debajo del máximo que da el puro ruido entre 10.000 estrategias (≈ 3,7). Ninguna estrategia se sostiene sola después de haber buscado entre tantas: la puerta **enriquece** la lista, no certifica a nadie.
- **Una de cada veinte sin ventaja pasa R3 por construcción**, y la población que entra es grande.

Lo que de verdad mueve la aguja es **más muestra fuera**: `oos2` y, sobre todo, los mercados adicionales — donde todo el histórico es fuera de muestra — combinados en una sola prueba. Eso es un comentario de cierre, no parte de esta puerta: si hay que elegir dónde poner tiempo de máquina, rinde más ahí que en afinar otro filtro sobre oos1.
