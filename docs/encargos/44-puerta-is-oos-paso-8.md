# 44 · La puerta IS/OOS (paso 8): reglas, pruebas y cascada nuevas — encargo autocontenido

> **Listo para planificar y ejecutar.** El dueño revisó el paso 8 regla a regla el 2026-10-06 y
> cerró todas las decisiones de diseño. Las que quedan abiertas son de **calibración** y se le
> entregan con números (sección «Decisiones del dueño»).

**Tu oficio:** estadístico e ingeniero de la puerta IS/OOS. Diseño, estadística y medidas:
**Opus**. Lo mecánico — borrados, renombrados, regenerar documentos, comprobaciones —: **Sonnet**
(regla 17).

**Tu encargo:** dejar el paso 8 juzgando con las reglas de la sección 1.2, evaluadas en cascada de
la más barata a la más cara, con **todos sus parámetros editables desde la ventana**, y devolver
al dueño tres cosas:

1. **El inventario** (parte A): por cada regla, qué hay hoy implementado y qué falta.
2. **El embudo de dos poblaciones de prueba** (parte K): cuántas estrategias sin ventaja pasan la
   cadena entera y cuántas con ventaja conocida se pierden, **regla por regla**.
3. **Las líneas de Pasa / Limbo / Falla propuestas con esos números**, cada una con su coste en
   estrategias al lado, para que él las congele. Hasta entonces `dev.on` sigue encendido.

**Lee, en este orden:** `CLAUDE.md` · `CODESTYLE.md` ·
`docs/AgentPDFs/puerta-is-oos-paso-08-especificacion-2026-10-06.md` (la especificación entera,
con fórmulas y ejemplos: es tu referencia de diseño) · `pipeline/autopilot/criteria.yaml` paso
"8" · `studies/screening/gate/README.md` · `studies/CLAUDE.md` · `engines/README.md` ·
`ui/README.md` (cómo edita la ventana una regla y un parámetro). Las seis propuestas originales
del dueño (`docs/AgentPDFs/criterios-paso-08-*-propuesta-2026-10-06.md`) y su índice
(`…-indice-decisiones-2026-10-06.md`) se citan abajo por `fichero:línea`: ábrelas por el tramo,
no enteras (regla 16).

**Cuando una propuesta y este encargo no coincidan, manda este encargo.** Las propuestas son
anteriores a varias decisiones; las diferencias están en la sección 1.3.

## Estado — lo actualiza cada sesión

| parte | qué | estado |
|---|---|---|
| — | R2b retirada | **hecho** (commit `9a3b60d`) |
| — | R4b retirada (techo de 75 operaciones al año) | **hecho** (2026-10-06) |
| A | inventario de lo implementado | pendiente |
| B | identidades build → retest (R1a) | pendiente |
| C | auditoría del repreciado del mono y repreciado común | pendiente |
| D | R3: deriva por ventana, error estándar con sesgo y curtosis, sin excepciones | pendiente |
| E | R5, R5b, R5c, R5d, R8, R9b, calidad de datos | pendiente |
| F | retraso de una barra | pendiente |
| G | R7, R6, mono | pendiente |
| H | lo que se borra | pendiente |
| I | la cascada y el juez | pendiente |
| J | parámetros en la ventana | pendiente |
| K | poblaciones de prueba, líneas, `dev.on` | pendiente |
| L | datos para el módulo de fondeo | pendiente |
| M | documentación | pendiente |

**Bitácora** (una línea por sesión: fecha, qué partes, qué quedó a medias):

- 2026-10-06 · redactado tras la revisión del dueño; nada ejecutado salvo R2b y R4b.

---

## 0 · De dónde sale

- Dueño, 2026-10-06: revisión del dossier del paso 8 regla a regla, con seis propuestas suyas y
  un índice. Sus instrucciones: «deja la mayoría de cosas como parámetros configurables»; que
  los parámetros se editen **en la UI**; y que las pruebas que envuelven repeticiones lleven
  **por defecto al menos 5.000**.
- Las medidas que se hicieron ese día y sostienen varias decisiones:
  `knowhow/research/trade-t-vs-frequency-and-skew.md` (la frecuencia no compra t; la t normal
  deja pasar de más con sesgo negativo) y `knowhow/costs/funded-tick-spread-vs-price.md` (la
  recalibración de costes del 2026-10-04).
- El módulo de fondeo es otro encargo: `45-modulo-de-fondeo.md`. Aquí sólo se le deja el dato.

## 1 · Las reglas del juego

### 1.1 Principios — valen para todas las partes

1. **Estados:** Pasa, Limbo, Falla; manda la peor. Un hecho que **falta** es Limbo (dueño,
   2026-10-01). Un hecho **no calculado porque la estrategia ya había caído** en la cascada no
   es «falta»: el juez los distingue (parte I).
2. **Un solo repreciado, a los costes de SQX.** La estrategia, R3, el retraso de una barra, la
   calidad de datos y los monos usan el mismo P/L, con el spread, el slippage, la comisión y el
   swap que la tarea de SQX cobró — los de la ficha del activo recalibrada el 2026-10-04. Ningún
   criterio usa el spread de los ticks de Darwinex.
3. **Ninguna cifra en el código, y todas en la ventana** (parte J). Las líneas viven en
   `criteria.yaml`; los parámetros de cálculo, en el `config.yaml` de su estudio.
4. **Toda prueba con repeticiones lleva por defecto al menos 5.000** — permutaciones, secuencias
   de bootstrap, sorteos del mono, estrategias por nivel en las poblaciones de prueba —, con
   semilla fija y configurable. Donde una propuesta dice 2.000, son 5.000.
5. **El trader al azar, sólo en OOS** (dueño): ningún nulo de entrada aleatoria toca el build.
6. **Se mide antes de congelar.** Cambiar el dato de una regla invalida la tasa de falsos
   positivos con la que se fijó su línea. Las líneas de la sección 1.2 son las de partida; las
   definitivas salen de la parte K y las congela el dueño.
7. **Mecánico, robusto, sencillo:** la puerta se ejecuta sola dentro de `bin/workflow.sh` (regla
   19) y falla claro. Menos piezas antes que más opciones.

### 1.2 Lo que se decide en cada estrategia — la tabla final

`e` es el **exceso por operación** de R3: el P/L de la operación menos lo que habría ganado una
operación ciega del mismo lado, duración y tamaño. Todas las reglas que hablan de «exceso» o de
«la t» usan los de R3 (parte D), no otros.

| nivel | regla | hecho | Pasa | Limbo | Falla |
|---|---|---|---|---|---|
| 0 | **R1a** presencia | la estrategia del build aparece en el retest | sí | — | no |
| 0 | **R1b** sanidad y clones | como hoy | como hoy | como hoy | como hoy |
| 0 | **R2** neto de oos1 | como hoy | > 0 | — | ≤ 0 |
| 0 | **R4a** operaciones al año en el build, como está cargada | `is_trades_per_year` | ≥ 35 | 20 – 35 (H4: desde 15) | < 20 (H4: < 15) |
| 0 | **R5b** operaciones en oos1 | `gate.scorecard.sanidad_value` | ≥ 100 | < 100 | nunca |
| 1a | **R3** t del exceso | `gate.scorecard.drift_excess_t` | ≥ 1,65 | **no tiene** | < 1,65 |
| 1b | **R5** estabilidad de la frecuencia | `z_frec` | \|z\| ≤ 1,5 | hasta 3,5 | > 3,5 |
| 1b | **R5c** ventaja frente al coste | `edge_mean_oos`, `t_exceso_k` (k = 1,25) | t(k) ≥ 1,65 y edge ≥ 2 | t(k) < 1,65, o edge 1,25 – 2 | edge < 1,25 |
| 1b | **R5d** degradación dentro de oos1 | `t_b`, `e_fin` | t_b ≥ −1,65 | t_b < −1,65 | t_b < −1,65 y e_fin ≤ 0 |
| 1b | **R8** concentración | `t_sin_mejor_trimestre`, `t_sin_3_mejores` | las dos ≥ 1,65 | alguna entre 0 y 1,65 | alguna ≤ 0 |
| 1b | **R9b** MAE | `mae_p95_r` | ≤ 1,5R | hasta 2,5R | > 2,5R |
| 1b | **Calidad de datos** | `ret_datos`, `t_A` | ret ≥ 0,60, o ninguna afectada | 0,25 – 0,60, o < 0,25 con t_A ≤ 1,65 | < 0,25 y t_A > 1,65 |
| 2 | **Retraso de una barra** | `retraso_ret_min`, `retraso_t_delta` | ret ≥ 0,60 | 0,25 – 0,60, o < 0,25 con t_Δ ≤ 1,65 | < 0,25 y t_Δ > 1,65 |
| 3a | **R7** homogeneidad por trimestres | `q_p` | > 0,05 | ≤ 0,05 | nunca |
| 3b | **R6** drawdown | `dd_p` | > 0,10 | 0,01 – 0,10 | ≤ 0,01 |
| 3c | **Mono** | `z_mono` | ≥ 1,65 | < 1,65 | nunca |

Fuera del paso 8: **R2b** y **R4b** (ya retiradas), **R9a** y **R9c** (al módulo de fondeo), el
espionaje de datos y la criba `familia`, `profitShape`, el repreciado al spread de Darwinex,
`edge_median` y `n` de `edgeCost` (parte H).

### 1.3 Dónde este encargo corrige a las propuestas

| tema | dice la propuesta | manda |
|---|---|---|
| R4a | pendiente de un suelo económico; a media sesión, 100 operaciones en el build | 35 / 20 al año, sin tocar |
| R4b | sigue en ≤ 75 | retirada |
| R5, bandas | 2 / 3 en su §5.2 | 1,5 / 3,5 |
| R5 y R5d, centrado | la mediana de «las que han llegado a ese nivel» | la mediana de las que llegaron al retest, con mínimo de 30 y tope (parte E) |
| R5c, estrés de coste | k = 1,5 | k = 1,25 |
| R7 y mono, repeticiones | 2.000 | 5.000 |
| mono, ventana del sorteo | año o trimestre | la misma ventana que la deriva de R3 |
| mono y R3 | «si discrepan, Limbo» | sólo en un sentido: pasa R3 y pierde con el mono → Limbo. Por debajo de 1,65 es Falla y el mono no se calcula |
| costes del repreciado | «spread real de Darwinex + slippage» en algún tramo | los de la ficha, los que cobra SQX |
| corrección de la deriva | «resuelta mejor con el mono» (índice) | se corrige en R3 (parte D); el mono no la sustituye |
| datos para fondeo | para las que acaban el paso 8 sin Falla | cuando la estrategia pasa el WFM (parte L) |
| el mono en mercados adicionales, Stouffer, oos2 | propuesto | sólo comentario: fuera de este encargo |

---

## A · El inventario: qué hay implementado

Antes de escribir una línea. Por cada fila de la tabla 1.2 y cada cosa de la parte H, una fila
con: el hecho que existe hoy y dónde se calcula (`fichero:línea`), la regla cargada en
`criteria.yaml`, si la ventana lo enseña y lo edita, sus tests, y **la distancia a lo
especificado**. Se entrega al dueño como tabla en la respuesta, no como documento.

Puntos de partida, verificados el 2026-10-06 — compruébalos, no los des por buenos:

- El exceso y la t: `studies/screening/analysis/tradelevel.py` (`mean_move` `:7-19`, `drift`
  `:22-40`, `t` `:43-64`) y `studies/screening/gate/measures.py:25-36`.
- El mono de la puerta: `studies/screening/gate/monkey.py`; la criba `familia` en `monkey.py:85`
  y `screens.py:150`. Las lecturas: `studies/readings/monkey/`.
- El flotante: `studies/screening/analysis/floating.py`.
- Las reglas cargadas: R3 lleva hoy `pass ">= 2.33"`, `limbo ">= 1.65"` y excepciones `by` para
  H4 y H1; R5b lee `spread.verdict_csv.operaciones_oos`.
- Usa `graphify explain` y `graphify affected` antes de abrir ficheros.

## B · Identidades entre el build y el retest (R1a) — lo primero

El juez no encuentra los hechos de una estrategia cuando su identidad cambia entre el databank
del build y el del retest: en la corrida de ejemplo caen por eso 29 de las 169 vivas (17 %), un
error de contabilidad y no un veredicto. Lee la cabecera de
`knowhow/sqx-format/identity-differs-across-databanks.md` y el tramo del índice
`docs/AgentPDFs/criterios-paso-08-indice-decisiones-2026-10-06.md:78-80`.

Se arregla **en el punto por el que pasan todos los que leen** — la resolución de la identidad —,
no en cada regla. Prueba: una población ya cosechada en la que hoy fallen por presencia, antes y
después, con el recuento pegado. Ningún recuento de las partes siguientes vale hasta entonces.

## C · La auditoría del repreciado del mono, y el repreciado común

**C.1 · La auditoría.** El mono reprecia con su propio motor y da a la estrategia A un neto de
45.464 USD donde SQX da 38.465 (+18 %), sin explicación
(`docs/AgentPDFs/criterios-paso-08-mono-propuesta-2026-10-06.md:8-28`). Se revisa operación a
operación para A, B y C: precio de entrada y de salida, lotes y valor del punto, spread,
slippage, comisión y swap, contra las operaciones de SQX. Termina cuando cuadra o cuando la
diferencia tiene nombre y tamaño. El resultado va a una ficha de `knowhow/research/`.

**C.2 · Un solo repreciado.** Una función que, dadas las operaciones y las barras, devuelve el
P/L a los costes de la tarea de SQX, usada por R3, el retraso de una barra, la calidad de datos
y el mono. Busca primero lo que ya exista en `engines/` (regla del repo: se reutiliza, no se
reescribe). El coste por operación que esa función cobró es también el denominador de
`edge_mean_oos` y el coste de `t_exceso_k` (parte E).

**Verificación:** el P/L repreciado de A, B y C sin desplazar nada coincide con el de SQX dentro
de la tolerancia que la auditoría justifique, escrita en el test.

## D · R3 — la regla central

Especificación, sección de R3. Tres cambios:

**D.1 · La deriva por ventana.** Hoy `mean_move` da un movimiento medio por tramo y `drift` se
lo aplica a cada operación. Pasa a ser un movimiento medio **por ventana de calendario dentro de
oos1**, y cada operación lleva el de la ventana en la que se abrió. La t sigue siendo **una**,
sobre todas las operaciones de oos1 (una t por ventana no tiene potencia: descartado por el
dueño). La ventana es un parámetro; **nunca por debajo de un trimestre** — cuando se acerca a la
duración de una operación el exceso tiende a cero por construcción.

**D.2 · El sesgo por tamaño.** El término supone que cada barra fue una barra media, pero la
doctrina dimensiona en inverso a la volatilidad: desplaza la t de una estrategia sin ventaja
entre ±0,02 y ±0,27 según activo y lado (`knowhow/research/drift-term-biased-by-side.md`, que
describe la corrección de «la operación ciega de la misma duración»).

**Qué se mide, y qué se entrega al dueño:** con ventana de **un año natural** y de **seis
meses**, las cuatro variantes — (a) el término de hoy, (b) movimiento por ventana, (c) la
corrección de la operación ciega, (d) b y c juntas —, y para cada una: el sesgo por lado y
activo de una estrategia sin ventaja, la tasa de falsos positivos a 1,65, y cuántas estrategias
cambian de veredicto y en qué sentido. **Los dos resultados, año y semestre, lado a lado**: la
ventana la elige él. La variante se carga sola: la que menos sesgo deje; si empatan, la más simple.

**D.3 · El error estándar con sesgo y curtosis.** `t = s·√(n−1) / √(1 − γ3·s + (γ4−1)/4·s²)`,
con `s` la media entre la desviación del exceso, `γ3` su sesgo y `γ4` su curtosis (3 = normal).
Aprobado por el dueño. Medido sobre operaciones independientes baja los falsos positivos de
USA500 H1 indicesIBS de 6,9 % a 5,1 % a 1,65 sin mover las otras poblaciones
(`knowhow/research/trade-t-vs-frequency-and-skew.md`). **Falta medirla junto al n efectivo
AR(1)** que ya usa la puerta: hazlo antes de cargarla.

**D.4 · La línea.** `pass: ">= 1.65"` (p = 0,05, una cola) y nada más: **sin Limbo y sin
excepciones por timeframe** — fuera las `by` de H4 y de H1. Coste a decir al entregar: de 10.000
estrategias sin ventaja pasan por azar unas 390 con el dato de hoy (3,9 %); se vuelve a medir.

**Ficheros:** `studies/screening/analysis/tradelevel.py`, `studies/screening/gate/measures.py`,
el `config.yaml` de la puerta, sus tests, `criteria.yaml`,
`knowhow/research/drift-term-biased-by-side.md` y `gate-t-scales.md` (editar, no añadir).

## E · Las reglas de una pasada sobre las operaciones (nivel 1b)

Diseño: `docs/AgentPDFs/criterios-paso-08-R5-R5b-R5c-propuesta-2026-10-06.md` (R5 `:19-130`,
R5b `:132-152`, R5c `:154-206`, R5d `:208-262`), `…-R6-R7-R8-propuesta-…md:162-194` (R8),
`…-R9-propuesta-…md:35-63` (R9b), `…-estudios-4.5-4.6-4.7-propuesta-…md:19-63` (calidad de datos).

- **R5 · `z_frec`.** Logaritmo del cociente de tasas oos1 / build, con sobredispersión φ
  estimada en el build y acotada a [1,5; 3,5], menos el centro de la población. Bilateral.
- **El centrado (R5 y R5d).** La población son las estrategias de la corrida que llegaron al
  retest, del mismo activo, timeframe y lado. **Con menos de 30 no se centra.** El centro es su
  mediana **recortada** a ±0,35 en logaritmo (una frecuencia que baja un 30 % o sube un 42 %):
  lo que pase de ahí se queda en la z de cada estrategia. Motivo: en una población de plantilla
  todas son la misma idea y la mediana es la plantilla; sin tope, una plantilla que deja de
  operar en oos1 saldría con z ≈ 0. Para R5d el tope se define igual sobre la pendiente, en las
  unidades de `b_pop`: propón su valor con las poblaciones de la parte K.
- **R5b.** Sólo cambia de dónde lee: `gate.scorecard.sanidad_value`. Sigue sin descartar.
- **R5c.** `edge_mean_oos`: sólo oos1, con el denominador = el coste realmente pagado (parte
  C.2); y `t_exceso_k` = la t de R3 restando a cada operación (k − 1) × su coste, con k = 1,25.
  A saber al documentarlo: el coste que SQX ya cobra es el techo de lo medido en operaciones
  reales, así que 1,25 es margen, no una estimación.
- **R5d.** Pendiente del exceso contra el tiempo dentro de oos1, centrada por población: `t_b`
  y `e_fin` (el exceso proyectado al final de oos1). Es la única regla que hay que calcular
  para toda la población retesteada aunque la estrategia ya haya caído, por el centrado. La
  deriva por ventana de D.1 ya quita de cada periodo lo que hizo el mercado: mide cuánto queda
  del efecto común antes de restarlo otra vez.
- **R8.** La t de R3 sin el mejor trimestre y sin las tres mejores operaciones. **Sus líneas de
  1,65 no son p = 0,05:** quitar lo mejor baja la t de cualquiera y deja sesgo negativo, que
  D.3 corrige a su vez. El coste en estrategias buenas lo da la parte K.
- **R9b.** Percentil 95 de |MAE| / 1R sobre las operaciones de oos1, en lugar de la peor.
- **Calidad de datos.** Se marcan las operaciones de oos1 que tocan una anomalía del histórico
  entre su barra de entrada y la de salida; `ret_datos` = exceso medio sin ellas / exceso medio;
  `t_A` = diferencia de medias (Welch) entre afectadas y resto. Antes de activarla: qué cuenta
  hoy como anomalía en `studies/data/feedQuality`, **por qué no dejó datos en la corrida de
  ejemplo**, y el inventario de anomalías por activo, calculado una vez por activo y timeframe.

**Ficheros:** `studies/screening/gate/measures.py` y `studies/screening/analysis/`,
`studies/readings/edgeCost/`, `studies/data/feedQuality/`, `criteria.yaml`, tests.

## F · El retraso de una barra (nivel 2)

Diseño: `docs/AgentPDFs/criterios-paso-08-estudios-4.2-4.3-4.4-propuesta-2026-10-06.md:38-132`.
Sobre cada operación de oos1, tres variantes — E+1 (entrada en la apertura de la barra
siguiente), S+1 (salida), ES+1 (las dos) —, repreciadas con C.2. `ret` = exceso medio desplazado
/ original; `t_Δ` pareada; **se juzga la peor variante**. El e-ratio de
`studies/readings/entryQuality` se sigue calculando y sólo anota. E−1 y la versión sobre el
build quedan como opción apagada. Antes de activarla: por qué `entryQuality` no dejó datos en
la corrida de ejemplo (`:149`).

**Fuera de este encargo:** el retest exacto en SQX con la ejecución retrasada para las
finalistas (`:138`) y la prueba con el feed real de la firma (encargo 45).

## G · Las pruebas de remuestreo (nivel 3)

Diseño: `…-R6-R7-R8-propuesta-…md` (R6 `:20-120`, R7 `:122-160`) y `…-mono-propuesta-…md:53-129`.

- **R7 · `q_p`.** Q de homogeneidad del exceso por trimestre natural de oos1, con la nula
  barajando operaciones entre trimestres, **5.000 veces**. Nunca descarta. Mídela con las dos
  ventanas de D.1: parte de la diferencia entre trimestres ya está restada.
- **R6 · `dd_p`.** Se desplaza la media de las operaciones del build a la de oos1, se
  remuestrean por bloques (longitud 8, **5.000 secuencias** de tantas operaciones como oos1,
  sobre la curva de operaciones cerradas) y se mira en qué percentil cae el drawdown observado.
  Deja además `gate.scorecard.dd_esperado_p95_r` (parte L). No es un nulo de entrada al azar:
  remuestrea operaciones de la propia estrategia.
- **El mono · `z_mono`.** Entradas sorteadas **dentro de la misma ventana que la deriva de R3**
  (un solo parámetro para los dos), cada una dimensionada con la regla de la doctrina en *su*
  momento (`knowhow/research/monkey-size-carries-donor-volatility.md`), **5.000 sorteos**,
  repreciadas con C.2, sólo en oos1. `z_mono` = (media real − media de los monos) / desviación
  de esa media entre sorteos; el p empírico se guarda de dato secundario; los cuatro peldaños
  sólo anotan. **Sólo se calcula para las que pasan R3, y sólo puede bajarlas a Limbo.**
  Es la prueba más cara: mide su coste con 5.000 sorteos contra el de hoy y déjalo en `perf/`.

## H · Lo que se borra

«Se elimina» es borrar del todo (dueño): el código, su fila en la ventana, su paso en
`pipeline/autopilot/plan.py`, su objetivo de `perf/`, sus tests y su capítulo del manual
(`python3 tools/manual.py` después). Antes de cada borrado, `graphify affected`.

| qué | detalle |
|---|---|
| el espionaje de datos | `studies/screening/snoopingScreen` y la criba `familia` de la puerta. El comentario «SIN regla, a propósito: … snooping …» de `criteria.yaml` se reescribe |
| la forma del beneficio | `studies/readings/profitShape`. Lo que medía queda en R8, en el n efectivo de R3 y en R5d |
| el repreciado al spread de Darwinex | **sólo la mitad del paso 8** de `studies/data/spread/`: `reprice.py`, `one.py`, `many.py`, `report.py`. **Se queda entero el paso 4**: el escaneo, `/asset-onboard` (`onboard.py`), las bandas del MC Retest (`bands.py`), el swap de fondeo (`fundedswap.py`) |
| `edge_median` y `n` | de `studies/readings/edgeCost`; su medida de spread sobre ticks (`spread_share.py`) deja de ser el denominador |
| R9a y R9c como reglas | salen de `criteria.yaml`; sus hechos se siguen calculando (parte L). El dueño aceptó que, hasta que exista el módulo de fondeo, nada juzgue el peor día ni el drawdown sobre el neto |

**Cuidado con la mitad del spread:** la leen `ui/daemon/results/catalogue.py` y `knobs.py`,
`ui/daemon/runner/screening.py`, `ui/daemon/data/`, `ui/desktop/datazone/zone.py`,
`tests/test_spread.py` y `studies/screening/falsePositives/chain.py:14`. Y
`reports/<P>/Results/<día>/spread/trades.parquet` es hoy **el único sitio donde quedan las
operaciones de toda la población** después de la cosecha: R3 y todo lo que viene detrás las
necesitan, así que la puerta pasa a guardarlas ella antes de que ese fichero desaparezca.

## I · La cascada y el juez

Diseño: `docs/AgentPDFs/criterios-paso-08-indice-decisiones-2026-10-06.md:98-123`.

- Las reglas se evalúan por el nivel de la tabla 1.2. Una estrategia **sale en su primer
  Falla** y no se le calcula nada más; las de Limbo siguen. El veredicto es el mismo que
  calculándolo todo, porque manda la peor.
- Dentro de un nivel, primero la que más descarta (hoy R3).
- **Se registra en qué nivel y regla cayó cada una**: es el embudo, y la ventana lo enseña.
- **«No calculado» no es «falta»**: el juez no lee como Limbo lo que la cascada no calculó.
- **Un interruptor de configuración la apaga**: entonces se calcula todo para todas. Así corren
  las poblaciones de la parte K y cualquier estudio de calibración.
- Excepciones al orden: el centro de R5 (recuentos, gratis) y la pendiente de R5d se calculan
  sobre toda la población retesteada.
- Cada nivel tiene que poder ejecutarse sin rehacer los anteriores, y la puerta entera sigue
  corriendo sola dentro de `bin/workflow.sh`. Nada de esto se lanza a mano paso a paso (regla 19).

**Ficheros:** `pipeline/autopilot/` (el juez, `plan.py`, `criteria.yaml` y su cabecera, que aún
dice «Fallo = R1, R2, R2b o R9»), `studies/screening/gate/`, tests.

## J · Todos los parámetros, en la ventana

Cada fila de esta tabla se ve y se edita desde la ventana, con su frase de ayuda en español
(qué es y qué pasa si se sube o se baja), y se guarda en su YAML conservando los comentarios. El
mecanismo ya existe — la ventana edita las líneas de una regla y sus excepciones por timeframe,
y los parámetros de un estudio —: léelo en `ui/README.md` y úsalo; no se abre un editor nuevo.
Un parámetro que no esté en la ventana no está terminado. Se enseña con `/ui-shot`.

| parámetro | valor de partida | de quién |
|---|---|---|
| líneas de Pasa / Limbo / Falla de cada regla | las de la tabla 1.2 | `criteria.yaml` |
| ventana de la deriva de R3 y del sorteo del mono | la que elija el dueño (año o semestre); mínimo un trimestre | puerta |
| variante del término de deriva | la que salga de D.2 | puerta |
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

Un umbral que el dueño congele pasa a ser fila al final de su sección en
`ledger/thresholds.yaml`, leído como `ledger:<clave>`.

## K · Las dos poblaciones de prueba, las líneas y `dev.on`

Diseño: `docs/AgentPDFs/criterios-paso-08-indice-decisiones-2026-10-06.md:82-96`. Con la cascada
**apagada**, por la cadena entera:

- **La nula:** estrategias sin ventaja. Cuántas pasan todo por suerte: la tasa real de falsos
  positivos de la puerta, y la de cada regla.
- **La de ventaja plantada:** operaciones nulas con un exceso añadido de Sharpe por operación
  0,05, 0,10 y 0,15. Cuántas buenas se pierden y **en qué regla**: ocho reglas que pierdan cada
  una un 5 % de las buenas se llevan un tercio.

Al menos 5.000 estrategias por nivel, construidas sobre las operaciones de las poblaciones ya
cosechadas a los costes del 2026-10-04 (hay cuatro del 4 al 6 de octubre en
`AlgoData/reports/`; mira `AlgoData/INDEX.md`). `studies/screening/falsePositives/` es el sitio:
léelo antes, parte de esto puede existir.

**Lo que se entrega:** por regla y por nivel de ventaja, la proporción en Pasa, Limbo y Falla;
el embudo de la cadena; y, para cada línea, la propuesta con su coste — «a 1,65 pierde el X % de
las de 0,10 y deja pasar el Y % de las nulas». Incluye aquí lo que dejaron pendiente las partes
D (ventana, variante), E (el tope de R5d, las líneas de R8) y G. Con eso el dueño fija las
líneas; **después**, y sólo cuando él lo diga, se apaga `dev.on`.

## L · Lo que se deja para el módulo de fondeo

Cuando una estrategia **pasa el WFM** (dueño: «si llegan hasta el punto de guardarse (pasar
wfm), se guardan») se guardan, en la raíz de datos (regla 7) y con su fila en `perf/`: la curva
diaria de flotante de oos1, `oos_worst_day_r`, `gate.scorecard.dd_esperado_p95_r` y el neto
anual en R. El WFM es el paso 19 (`docs/AgentPDFs/WORKFLOW.md`; `studies/optimisation/wfm/`): el guardado se engancha ahí;
el formato lo lee el encargo 45, así que queda descrito en el `README.md` de la carpeta.

## M · Documentación — en la misma tarea

- La especificación (`docs/AgentPDFs/puerta-is-oos-paso-08-especificacion-2026-10-06.md` y su
  PDF, `/dossier-pdf`): se actualiza con lo que las medidas cambien y con las líneas congeladas.
- `docs/AgentPDFs/criterios-pasos-6-a-19-explicados-2026-10-06.md`: su parte del paso 8 describe
  las reglas viejas; se reescribe para que apunte a la especificación.
- El capítulo del manual de la puerta y de cada estudio tocado o borrado (regla 8, `/manual-chapter`).
- `studies/screening/gate/README.md`, la cabecera del paso 8 en `criteria.yaml`,
  `.claude/skills/workflow-simple/steps.md` (qué lee y qué llena el paso 8).
- Cada hecho no obvio, a su ficha de `knowhow/` (editar la que exista).

---

## Decisiones del dueño — pregúntalas (regla 11)

Ya decididas (no se reabren): todo lo de la sección 1.

Se le llevan **con números**, no antes:

- **La ventana de la deriva:** año o semestre (parte D).
- **Las líneas definitivas** de cada regla, con el embudo de la parte K.
- **El tope del centrado de R5d** y si el ±0,35 de R5 se mantiene.
- **H1 y H4:** R3 no lleva ninguna excepción por timeframe («por ahora») y las reglas nuevas
  nacen sin ellas; la única que queda es la de R4a en H4, que no se toca. Si las poblaciones de
  prueba enseñan que una regla se comporta distinto en un timeframe, se le propone; no se carga.
- **R1b:** el índice deja como opcional un suelo absoluto de 60-80 operaciones en oos1. No está
  decidido: pregúntalo si los números lo piden.

Y cualquier punto donde la especificación admita dos lecturas al implementarla: se pregunta, no
se elige la común.

## Lo que no tocas

El maestro. `oos2`, salvo las celdas que el dueño tenga autorizadas. Los criterios de los demás
pasos (10, 12, 14, 20…): otro día. El paso 4 de `studies/data/spread/`. `ledger/thresholds.yaml`
sólo gana filas. Nada de `portfolio/funded/` (es del encargo 45). No se lanza SQX fuera de
`bin/workflow.sh`, y nada pesado corre al lado de un workflow en marcha (regla 19): las medidas
de este encargo son Python sobre operaciones ya cosechadas.

## Verificación

- Casos de respuesta conocida, uno por hecho nuevo. Mínimos: una estrategia siempre larga y
  siempre dentro tiene exceso total 0 con cualquier ventana; una serie con la misma tasa en
  build y oos1 da `z_frec` ≈ 0; operaciones idénticas en todos los trimestres dan `q_p` alto;
  quitar tres operaciones de una serie constante no cambia la media; el repreciado sin
  desplazar reproduce SQX (parte C).
- La cascada encendida y apagada dan **el mismo veredicto** para toda una población real.
- La población nula da en R3 una tasa de falsos positivos compatible con el 5 %.
- Una corrida entera con `bin/workflow.sh` sobre un proyecto `Test_`, con el embudo pegado, y el
  proyecto retirado al acabar (regla 6).
- Cada parámetro de la tabla J, cambiado desde la ventana, cambia el resultado (`/ui-shot`).
- `python3 -m pytest -q tests/<fichero>` por fichero (el `-k` sobre `tests/` entero tropieza con
  `tests/test_oracle_draws.py`, que sale al importarse; es anterior a este encargo).
- `python3 tools/depmap.py && python3 tools/checks.py`

## Cómo cierras

Cada sesión: la tabla de estado y la bitácora de arriba actualizadas · qué hizo · qué verificó,
con la salida pegada · qué dejó sin hacer y por qué · qué descubrió para `knowhow/` — la lista
de ficheros cambiados y **¿Quieres hacer el commit?**
