# Paso 8 — Índice de decisiones y sugerencias de implementación

**Fecha:** 2026-10-06 · **Alcance:** todas las reglas y estudios del paso 8 (puerta IS/OOS) revisados en la sesión del 2026-10-06.
**Referencia:** `criterios-paso-08-puerta-oos-2026-10-06`.

Este documento junta en un solo sitio lo decidido regla por regla, dónde está el detalle, y cómo llevarlo al código.

---

## 1. Ficheros de la propuesta

| fichero | contenido |
|---|---|
| `criterios-paso-08-R5-R5b-R5c-propuesta.md` | R5 (estabilidad de la frecuencia), R5b, R5c (ventaja frente al coste), R5d (degradación) |
| `criterios-paso-08-R6-R7-R8-propuesta.md` | R6 (drawdown por bootstrap), R7 (homogeneidad), R8 (t sin lo mejor) |
| `criterios-paso-08-R9-propuesta.md` | R9a y R9c → módulo de fondeo; R9b (MAE p95) |
| `criterios-paso-08-mono-propuesta.md` | test del mono; ⚠️ revisión del repreciado; mercados adicionales |
| `criterios-paso-08-estudios-4.2-4.3-4.4-propuesta.md` | 4.2 y 4.3 eliminados; 4.4 retraso de una barra |
| `criterios-paso-08-estudios-4.5-4.6-4.7-propuesta.md` | 4.5 calidad de datos; 4.6, R2b y 4.7 eliminados |

---

## 2. Tabla de decisiones, regla por regla

| regla / estudio | decisión | resumen | coste |
|---|---|---|---|
| **R1a** presencia | se mantiene | **arreglar el fallo de identidades** (el juez no encuentra los hechos cuando la identidad cambia entre build y retest) | 0 |
| **R1b** sanidad | se mantiene | sobre todo anti-clones; el 20 es redundante (R5 ya impone más). Opcional: suelo absoluto de 60–80 operaciones en oos1 | 0 |
| **R2** neto > 0 | sin cambios | red por si se afloja la t | 0 |
| **R2b** neto al spread real | **se elimina** | dependía del spread de Darwinex | — |
| **R3** t descontada la deriva | se mantiene | regla central. Anotar como hecho la versión con deriva por ventanas anuales para explorar | 1 |
| **R4a** suelo de frecuencia en IS | sin cambios por ahora | 35 / 20. Pendiente fijarlo con $s_{\min}$ económico y potencia; suelo dependiente de los años de oos1 | 0 |
| **R4b** techo de frecuencia | sin cambios | ≤ 75 | 0 |
| **R5** frecuencia en oos1 | **rediseñada** | test de estabilidad IS → OOS: Poisson con sobredispersión $\varphi \in [1{,}5;\,3{,}5]$, centrado por población, bilateral. PASA $\lvert z\rvert \le 1{,}5$, LIMBO hasta 3,5, NO PASA > 3,5 | 1 |
| **R5b** ≥ 100 operaciones | red sin descarte | la cubren R4a + R5 nueva; lee `sanidad_value` | 0 |
| **R5c** ventaja frente al coste | **rediseñada** | IS y OOS separados; denominador con el coste realmente pagado; t de R3 con el coste × 1,5 | 1 |
| **R5d** degradación | **nueva** | pendiente del exceso dentro de oos1, centrada por población. LIMBO si $t_b < -1{,}65$; NO PASA si además el exceso proyectado al final ≤ 0 | 1 |
| **R6** drawdown | **rediseñada** | percentil del DD de oos1 en un bootstrap por bloques del build con la media desplazada a la de oos1. PASA > 0,10, NO PASA ≤ 0,01 | 3 |
| **R7** años positivos | **rediseñada** | homogeneidad del exceso por trimestres (Q con nula por permutación). Sólo LIMBO | 3 |
| **R8** concentración | **rediseñada** | $t_{-Q^*}$ (sin el mejor trimestre) y $t_{-3}$ (sin las 3 mejores operaciones). PASA ≥ 1,65; NO PASA ≤ 0 | 1 |
| **R9a** peor día | **→ módulo de fondeo** | el paso 8 sólo guarda la curva diaria de flotante y el peor día | 0 |
| **R9b** MAE | **rediseñada** | $\text{MAE}_{95}$: PASA ≤ 1,5R, LIMBO hasta 2,5R, NO PASA > 2,5R | 1 |
| **R9c** DD / neto anual | **→ módulo de fondeo** | el paso 8 sólo guarda el DD$_{95}$ simulado de R6 | 0 |
| **Mono** | **rediseñado** | ⚠️ revisar antes el repreciado (+18 % frente a SQX). Tamaño por la doctrina, sorteo estratificado por año, $z$ continuo. Control de R3: PASA exige $z_{\text{mono}} \ge 1{,}65$; si discrepan, LIMBO. Sólo OOS | 3 (el más caro) |
| **4.2** espionaje / criba familia | **se elimina** | | — |
| **4.3** forma del beneficio | **se elimina** | sus medidas pasan a R3, R5d y R8 | — |
| **4.4** calidad de la entrada | **se mantiene** | retraso de una barra (E+1, S+1, ES+1): NO PASA si retiene < 25 % de la ventaja y la caída es significativa. e-ratio anota | 2 |
| **4.5** calidad de datos | **se mantiene** | retención de la ventaja sin las operaciones que tocan anomalías; mismo criterio que el retraso | 1 |
| **4.6** spread | **se elimina** | el coste lo fija el estudio de emparejamiento MT5–SQX | — |
| **4.7** `edge_median` y `n` | **se eliminan** | | — |

*Coste computacional por estrategia:* 0 = metadatos o recuentos; 1 = una pasada sobre las operaciones; 2 = repreciado sobre barras; 3 = remuestreo (miles de repeticiones).

**Repreciado común** para R3, el mono, el retraso y la calidad de datos: costes de SQX calibrados con el estudio de emparejamiento MT5–SQX. Un único P/L para todos.

---

## 3. Estado del punto 5.3 del documento de referencia

| decisión abierta del documento | estado |
|---|---|
| 1. el juez no encuentra los hechos cuando cambia la identidad | **abierta: prioridad máxima** (sugerencia 1) |
| 2. apagar `dev.on` | **abierta**: después de las poblaciones de prueba (sugerencia 2) |
| 3. línea de descarte de la t (1,65) | se deja igual |
| 4. corrección del término de deriva | resuelta mejor con el mono con tamaño por la doctrina |
| 5. suelo duro de 20 al año | se deja igual por ahora (ver R4a) |
| 6. variante de Munger | no tratada |
| 7. peor día y peor MAE (Taleb) | resuelta: R9a al módulo de fondeo, R9b con p95 |
| 8. qué significa `edge_mean` | resuelta con R5c |
| 9. spread de la tarea de NIKKEI225 | decae: se elimina el estudio del spread |
| 10. H1 y H4 | **abierta**: las reglas nuevas también necesitan calibración por timeframe |
| 11. reglas que nunca deciden | resuelta: rediseñadas o eliminadas |

---

## 4. Sugerencias de implementación

### Sugerencia 1 — Arreglar el fallo de identidades lo primero

No depende de ningún criterio, y hoy descarta 29 de las 169 vivas (el 17 %) por un error de contabilidad. Cualquier recuento para calibrar las reglas nuevas estará contaminado mientras siga ahí.

### Sugerencia 2 — Pasar dos poblaciones de prueba por toda la cadena antes de apagar `dev.on`

Ninguna línea se congela hasta medir qué hacen todas las reglas juntas. Con las pruebas nuevas, esto es todavía más necesario.

**a) Población nula** (estrategias sin ventaja): cuántas pasan la cadena entera por suerte. Es la tasa real de falsos positivos.

**b) Población con ventaja plantada:** estrategias sintéticas con un Sharpe por operación conocido (0,05, 0,10, 0,15), construidas sobre operaciones nulas con un exceso añadido. Mide cuántas buenas se pierden por el camino: la potencia real.

La b) es la que falta. Cada regla añadida es otra oportunidad de descartar una buena por mala suerte. Si cada una perdiera un 5 % de las buenas y fueran independientes:

$$1 - 0{,}95^{8} \approx 34\,\%$$

Un tercio de las buenas fuera sólo por acumular filtros. La población plantada dice si eso pasa y qué regla es la culpable. Con las dos poblaciones se fijan todas las líneas a la vez, con datos.

**Importante:** para estas dos poblaciones la cascada de la sugerencia 3 se **desactiva** y se calculan todas las reglas para todas las estrategias. Si no, no se puede medir el efecto de cada regla por separado.

### Sugerencia 3 — Cascada de la más barata a la más cara, eliminando las NO PASA por el camino

Las reglas se evalúan **en orden de coste computacional creciente**. En cuanto una estrategia da **NO PASA** en una regla, sale y no se le calcula nada más. Las que dan **LIMBO** siguen adelante.

**Por qué no cambia el resultado.** El resultado de una estrategia es el de su peor regla: basta un NO PASA para que sea NO PASA. Así que descartarla en cuanto aparece el primer NO PASA da **exactamente el mismo veredicto** que calcularlo todo, y ahorra casi todo el tiempo de máquina. Sólo cambia que a las descartadas les faltarán hechos de las reglas posteriores, que no importa para seleccionar (sí para calibrar: ver sugerencia 2).

**Orden propuesto:**

| nivel | coste | reglas | notas |
|---|---|---|---|
| **0** | metadatos y recuentos | R1a presencia · R1b sanidad y clones · R4a suelo IS · R4b techo IS · R2 neto > 0 | instantáneo; aquí cae buena parte de la población |
| **1a** | una pasada sobre las operaciones | **R3** (t descontada la deriva) | la deriva $\mu$ se calcula una vez por activo y timeframe. Es la que más descarta: va primero dentro del nivel 1 |
| **1b** | una pasada | R5 (frecuencia) · R5c (coste estresado) · R5d (degradación) · R8 ($t_{-Q^*}$, $t_{-3}$) · R9b ($\text{MAE}_{95}$) · 4.5 (calidad de datos) | R5 y R5d necesitan la mediana poblacional: se calcula con las que han llegado a este nivel. 4.5 usa el inventario de anomalías por activo, calculado una vez |
| **2** | repreciado sobre barras | 4.4 retraso de una barra (3 variantes) | |
| **3a** | remuestreo ligero | R7 (Q, ≈ 2.000 permutaciones) | sólo baraja etiquetas de trimestre |
| **3b** | remuestreo medio | R6 (bootstrap por bloques, ≈ 5.000 secuencias) | guarda también el DD$_{95}$ para el módulo de fondeo |
| **3c** | remuestreo caro | Mono (≈ 2.000 sorteos con repreciado y tamaño por la doctrina) | el más caro: va el último |

**Por qué este orden ahorra tanto.** Tras el nivel 0 y R3 sólo queda alrededor del 3 % de la población (en la corrida de ejemplo, 326 de 10.000 con t ≥ 1,65). Las pruebas de nivel 3, que son el grueso del coste, se ejecutan sobre unas 300 estrategias en lugar de 10.000: el coste total queda por debajo del del mono actual sobre toda la población.

**Detalles de implementación:**

- **Dentro de un mismo nivel**, poner primero la regla que más descarta (hoy R3 en el nivel 1). A igual coste, la que más elimina ahorra más a las siguientes.
- **Registrar en qué regla cayó cada estrategia** (el nivel y la regla del primer NO PASA). Es el embudo, y dice qué reglas trabajan.
- **Los hechos que guarda el paso 8 para el módulo de fondeo** (curva diaria de flotante, peor día, DD$_{95}$) sólo se guardan para las que llegan al final sin NO PASA.
- **El fallo de identidades** (sugerencia 1) tiene que estar arreglado antes de montar la cascada: hoy hace caer estrategias en el nivel 0 por error.

### Sugerencia 4 — El límite de fondo no cambia

Con las reglas nuevas sigue siendo cierto: pasar el paso 8 hace a una estrategia **candidata**, no válida. Con 3–5 años de oos1, la t tiene poca potencia y ninguna regla lo arregla. Lo que de verdad mueve la aguja es **más muestra fuera**: oos2 y, sobre todo, los mercados adicionales combinados con Stouffer (ver la propuesta del mono, sección 5). Si hay que elegir dónde poner tiempo de máquina, mejor ahí que en refinar más filtros de oos1.

---

## 5. Orden de trabajo sugerido

1. Arreglar el fallo de identidades (R1a).
2. ⚠️ Revisar a fondo el repreciado del mono y unificar el repreciado común (costes de SQX calibrados con MT5–SQX).
3. Comprobar por qué `entryQuality` y `feedQuality` no dejaron datos en la corrida de ejemplo.
4. Implementar las reglas nuevas y rediseñadas, y la cascada por niveles.
5. Construir y pasar las poblaciones nula y con ventaja plantada (con la cascada desactivada).
6. Fijar todas las líneas con esos resultados.
7. Apagar `dev.on`.
8. Diseñar el módulo de fondeo (R9a, R9c, nivel de cartera, feed de la fondeadora).
