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
| A | inventario de lo implementado | **hecho** (2026-10-06; lo que cambia el encargo, en P.1) |
| — | plan de ejecución (al final de este fichero) | **aprobado** (2026-10-06); oleada 0 en marcha |
| B | identidades build → retest (R1a) | reproducido (2026-10-06); el arreglo espera a que no haya workflow |
| C | auditoría del repreciado del mono y repreciado común | **hecho** (2026-10-06; forex pendiente del dueño) |
| D | R3: deriva por ventana, error estándar con sesgo y curtosis, sin excepciones | programado (2026-10-06); falta medir (D-m) y la parada 1 |
| E | R5, R5b, R5c, R5d, R8, R9b, calidad de datos | programado (2026-10-06), sin conmutar |
| F | retraso de una barra | programado (2026-10-06), sin conmutar |
| G | R7, R6, mono | R7 y R6 programados (2026-10-06); el mono (G2) espera |
| H | lo que se borra | pendiente |
| I | la cascada y el juez | pendiente |
| J | parámetros en la ventana | pendiente |
| K | poblaciones de prueba, líneas, `dev.on` | pendiente |
| L | datos para el módulo de fondeo | pendiente |
| M | documentación | pendiente |

**Bitácora** (una línea por sesión: fecha, qué partes, qué quedó a medias):

- 2026-10-06 · redactado tras la revisión del dueño; nada ejecutado salvo R2b y R4b.
- 2026-10-06 · parte A y «Plan de ejecución» (P.1-P.7), pasado por el Council y por un ataque
  sin contexto; cuatro decisiones del dueño (P.2). Ni una línea de código. A medias: las
  preguntas de P.7 y el sí del dueño para lanzar la oleada 0.
- 2026-10-06 · plan aprobado, P.7 respondida. Oleada 0: **0** hecho (esqueleto, claves, 16
  reglas en fixture; `monkey.draws` sigue en 2.000 hasta I), **E0-m** hecho (feedQuality murió
  por falta de inventario; hoy no falta ninguno), **C1-m** hecho (el mono no cobra spread ni
  slippage: tarjeta «monkey-reprice-audit»; convención y tolerancia para C2 en ella), **B1**
  reproducido (1.557 de 10.000 caen por presencia; 29 revivirían) — su arreglo es sólo
  `judge.py:117` y espera, con **B2**, a que no haya workflow corriendo. A medias: cinco
  lecturas de reglas pedidas al dueño por el paquete 0; C2 lanzado.
- 2026-10-06 · **C2** hecho (`engines/market/reprice.py`, firma congelada en P.3; rechaza forex:
  swap en puntos, pendiente del dueño). **D** hecho (`drift_term` a-d, `t_skew_kurt`,
  `level1a.py`; nada de hoy cambia). Esperan a que no haya workflow: arreglo de B1, B2, D-m y
  G2. Oleada 3 lanzada sin G2. Preguntas abiertas al dueño: 5 del paquete 0, 5 de C2, 3 de D.
- 2026-10-06 · oleada 3 hecha salvo G2: **E1**, **E2**, **E3**, **F**, **G1** (los cinco niveles
  rellenos, sus tests en verde; nada de producción los llama). Parado aquí: lo que queda (arreglo
  de B1, B2, D-m, G2 y la conmutación I) toca ficheros vivos o carga la máquina y espera a que
  no haya workflow de otra sesión; y 25 lecturas con dos caminos esperan al dueño (la lista, en
  la respuesta de la sesión: reglas sin dato y bordes, coste de R5c, forex, cortos, anomalías
  que cuentan, `e_fin`, operación más corta que el retraso, P/L del build en R6…).

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

---

# Plan de ejecución (2026-10-06) — aprobado por el dueño el 2026-10-06

Quien ejecuta es **una sesión orquestadora** (Opus) que lanza un subagente por paquete —el 0
incluido—, en la misma carpeta y rama (regla 12), y no programa ella. Cada paquete está escrito para un subagente
que no sabe nada más: se le pasa su bloque, las secciones «Contratos» y «Reglas de todos los
paquetes», y la parte del encargo que cita.

## P.1 · Lo que el inventario encontró y cambia el encargo

| tema | decía el encargo | es |
|---|---|---|
| operaciones de la población | `spread/trades.parquet` es el único sitio | la cosecha (`AlgoData/harvest/<P>/<D>/<día>/trades.parquet`) las guarda todas, **pero una re-cosecha el mismo día la pisa**: de las 10.000 de `Trade_NIKKEI225_M30_volatilidadL` sólo quedan en `reports/…/2026-10-04/spread/trades.parquet` (167 MB, sin MAE ni curva). Paquete B2 |
| R1a, las 29 de 169 | la identidad cambia | el scorecard se indexa por la identidad del **build** (`gate/harvest.py:89-96`) y el juez busca por la del **retest** (`pipeline/autopilot/judge.py:112-117`); `presencia_passed` lleva `missing: fail`. Inferido del código, sin reproducir: lo reproduce B1 |
| el repreciado común | «busca lo que ya exista en `engines/`» | no existe. `engines/market/calibrate.py` + `engines/nulls/kernel.py` precian con el coste **residual** de cada operación (no el declarado), sin lado explícito, sin swap por noche; `engines/market/replay/` está documentado y sin construir. C2 es código nuevo |
| la operación ciega (D.2 c) | por hacer | existe en `studies/transfer/crossmarket/simulate/excess.py` (`blind`, ~`:40`), fuera de la puerta; su `t` duplica la de `tradelevel` y un test las ata (`tests/test_crossmarket_excess.py:53`) |
| `entryQuality` sin datos | por averiguar | corre **después** del corte (`pipeline/autopilot/run.py:97`, `AFTER_CUT`), por estrategia y con export propio: el juez nunca ve sus hechos. `feedQuality`: causa sin establecer (paquete E0) |
| `edgeCost` | `edge_mean` sobre oos1 | hoy mezcla build y oos1, y su denominador es el spread **de hoy** de la ficha + comisión, sin slippage ni swap (`studies/readings/edgeCost/one.py:48`, `costs.py:93`). Es también la lectura del paso 25 |
| `falsePositives/chain.py:14` lee el spread | sí | no: sólo reutiliza el nombre `spread.verdict_csv.operaciones_oos`, relleno desde `sanidad_value` |
| parámetros en la ventana (J) | «el mecanismo ya existe» | a medias. Las **líneas** se editan y se guardan (`ui/daemon/criteria/write.py:93`), pero el diálogo pierde `missing:` al editar (`ui/desktop/criteria/dialog.py:209-234`). Los **parámetros de estudio no se guardan**: el cajón sólo cambia la siguiente ejecución (`ui/desktop/studypage/drawer.py:88`); el único escritor persistente es `ui/daemon/sqxconfig/studywrite.py`, sólo para WFC y CSCV. Ninguna vista lee el motivo por regla del juez |
| poblaciones para K | cuatro, del 4 al 6 de octubre | con ≥ 30 estrategias sólo **una**: `Test_USA500_H1_indicesIBS` 2026-10-05 (3.000, H1 largo; ya tiene 150.000 monos en `falsePositives/`). NIKKEI225 M30 largo: las 10.000 del ejemplo (sólo operaciones). El resto, 3 a 10 estrategias |
| `snoopingScreen` | borrar | su clave `snoopingScreen.stepm.fwer` la lee `studies/closing/blindJoint/config.yaml:18` (paso 20) y `tests/test_close_curve.py:15` y `perf/inputs/workloads.py:20` importan su `inputs` |

## P.2 · Decisiones del dueño al planificar (2026-10-06) — no se reabren

1. **Todo en la puerta.** Los hechos de todas las reglas del paso 8, incluidos el retraso y la
   calidad de datos, los calcula la puerta en un solo proceso, nivel a nivel, como
   `gate.scorecard.*`. `entryQuality` (e-ratio) sigue anotando tras el corte; `feedQuality` da el
   inventario de anomalías. Los parámetros de «su estudio» de la tabla J viven en el
   `config.yaml` de la puerta.
2. **Las cribas viejas se borran:** `degradacion`, `forma`, el `mono` de p y `familia`. Queda una
   cascada, la de niveles, con las líneas de `criteria.yaml`. `presencia`, `sanidad` y
   `estaticas` dan los hechos del nivel 0; `redundancia` sigue anotando. Sus filas del ledger
   salen (P.7-5). El MANTENER / DESCARTAR de la ficha pasa a ser el veredicto del juez.
3. **`edgeCost` cambia entero ahora:** sólo oos1, denominador = el coste realmente pagado (C2),
   sin `edge_median`, `n` ni `spread_share.py`. El paso 25 lee la definición nueva.
4. **Con la mitad del spread se van** el paso 25.5, el encargo 36 (y `OPEN.md` #76) y, en la
   ventana, la curva y el «Net Profit con spread y slippage reales» con su botón «calcular».

## P.3 · Contratos — los fija la oleada 0; ningún paquete los cambia

**Arquitectura.** `studies/screening/gate/levels.py` lleva el registro ordenado de niveles; cada
nivel es una función `(data, alive, cfg) -> DataFrame` indexado por identidad, en un fichero
propio, y declara los hechos que produce. Tras cada nivel la puerta evalúa, con
`pipeline.autopilot.criteria` (las mismas funciones que el juez), las reglas del paso "8" cuyo
hecho produce ese nivel; quien da Falla sale de `alive` y queda anotado en `cayo_nivel` y
`cayo_regla`. El nivel de una regla se deduce de su hecho: `criteria.yaml` no gana ninguna clave.
Con `cascade.on: false` no sale nadie. Las matemáticas van a `studies/screening/analysis/` (un
fichero por paquete); la puerta no importa ningún estudio — el inventario de anomalías se lee
como dato (`AlgoData/feedQuality/<feed>/events.parquet`).

- **La tabla por operación.** El nivel 1a escribe `operaciones.parquet` en la carpeta del
  informe de la puerta: una fila por operación de oos1 de toda la población pareada, con
  identidad, horas, lado, lotes, `pnl` y `cost` (los de C2), `drift`, `excess` y `window`. Los
  niveles 1b, 2 y 3 la reciben en `data["oos"]` y no recalculan el exceso; `--from-level` la
  relee. Es también donde la puerta **guarda las operaciones de la población** (§H).
- **Las mismas reglas que el juez.** La puerta resuelve las reglas con `criteria.resolved` y las
  etiquetas de `judge.tags`, filtra como `judge.settings()` (bajo `ALGO_SMOKE` sólo las
  `READABLE`) e indexa por la identidad que deja B1. Si no, cascada y juez pueden discrepar.
- **Los cocientes sólo existen con exceso medio positivo.** `ret_datos` y `retraso_ret_min`
  dividen por el exceso medio: con media ≤ 0 el hecho queda vacío (no «pasa» por ser un
  negativo entre un negativo). Con la cascada encendida no ocurre —llegan las que pasan R3—;
  con ella apagada, K-m mide esas reglas sólo sobre las de media positiva y lo dice.
- **Lo que recibe un nivel en `data`** (fijado por D, 2026-10-06): `trades`, `bars`, `market`
  (con `windows["OOS"]`), `costs` = `reprice.costs(feed, "oos1")`, `out` = la carpeta del informe
  de la puerta (`Path`), y desde el nivel 1a `oos`, la tabla por operación (de **todas** las
  pareadas, no sólo las vivas). Con `data` vacío un nivel devuelve sus hechos vacíos: lo usa
  `tests/test_gate_rules.py`. Las claves `costs` y `out` las pone el paquete I.
- **Lo que la oleada 3 pide al paquete I** (2026-10-06): `data["quality"]` =
  `core.paths.feed_quality_dir(feed)` (se omite si el feed no tiene inventario); `data["build"]`,
  la tabla por operación del build (`identity`, `pnl`, en orden de cierre) para R6;
  `data["costs_build"]` sólo con `delay.on_build`; `market["windows"]["IS"]` tiene que ser la
  ventana que el build recorrió de verdad (si es más ancha, R5 inventa años a cero); una corrida
  = un activo y un timeframe; los niveles dejan `retraso.parquet` en `out`; `monkey.draws` sube a
  5.000 al conmutar. Petición a `tradelevel.drift_term`: aceptar las etiquetas de ventana de la
  operación original (pregunta abierta del retraso).
- **`cayo_regla` es texto** y `facts.number()` descarta el texto (`pipeline/autopilot/facts.py:34-47`):
  el juez lo lee del scorecard; lo resuelve el paquete I, que posee `facts.py`.

| nivel | fichero de la puerta | maths | hechos `gate.scorecard.*` |
|---|---|---|---|
| 0 | `level0.py` | (las cribas `presencia`, `sanidad`, `estaticas`) | `presencia_passed`, `sanidad_passed`, `sanidad_value` (para **todas** las pareadas), `estaticas_value`, `is_trades_per_year` |
| 1a | `level1a.py` | `analysis/tradelevel.py` | `drift_excess_t` (mismo nombre, dato nuevo) |
| 1b | `level1b_centred.py` | `analysis/centred.py` | `z_frec`, `t_b`, `e_fin` |
| 1b | `level1b_onepass.py` | `analysis/onepass.py` | `edge_mean_oos`, `t_exceso_k`, `t_sin_mejor_trimestre`, `t_sin_3_mejores`, `mae_p95_r` (positivo) |
| 1b | `level1b_data.py` | `analysis/dataquality.py` | `ret_datos`, `t_a`, `n_afectadas` |
| 2 | `level2.py` | `analysis/delay.py` | `retraso_ret_min`, `retraso_t_delta` |
| 3a, 3b | `level3ab.py` | `analysis/resample.py` | `q_p`, `dd_p`, `dd_esperado_p95_r` |
| 3c | `level3c.py` | `engines/nulls/` | `z_mono`, `mono_p`, `z_mono_<peldaño>` (anotan), `mono_seed` |
| — | `levels.py` | — | `cayo_nivel`, `cayo_regla`; siguen sin regla `oos_worst_day_r`, `oos_dd_over_net_year`, `oos_net_per_year_r` (parte L) |

**El repreciado común** — `engines/market/reprice.py`; la firma definitiva la cierra C2 tras la
auditoría y queda congelada al cerrar la oleada 1, antes de que D la use:

- `costs(feed, segment) -> Costs` — de la ficha del activo: valor del punto, spread, slippage,
  comisión, swap largo y corto, noche del triple swap, hora de rollover. Un solo camino.
- `pnl(open_px, close_px, open_time, close_time, side, size, costs) -> (pnl, cost)` — arrays de
  cualquier forma igual; devuelve el P/L en dinero y **el coste cobrado** a cada operación.
- `fills(bars, positions) -> px` — el precio de ejecución de una operación movida o sorteada.

**Congelada el 2026-10-06 (C2 hecho; manda sobre las tres líneas de arriba):** `open_px` y
`close_px` son aperturas de barra **en crudo**, nunca precios de SQX (se cobraría dos veces);
`fills` devuelve la apertura en crudo de la fila `positions`; `side` es +1 / −1; hay una cuarta
función, `nights(open_time, close_time, costs)`; `Costs` es un dict con `point_value`,
`tick_size`, `spread`, `slippage` (en precio), `commission_method`, `commission`, `swap_long`,
`swap_short`, `triple`, `rollover`. Cortos y comisión ≠ 0, sin verificar. `costs()` **rechaza
las fichas de forex** (swap en puntos): pendiente del dueño.

**Claves nuevas del `config.yaml` de la puerta** (valor de partida):
`cascade.on: true` · `drift.window: year` (`year` | `semester` | `quarter`; nada menor) ·
`drift.variant: b` (`a`-`d`, provisional hasta D-m) · `drift.se_skew_kurt: true` ·
`frequency.phi_min: 1.5`, `phi_max: 3.5` · `centring.min_strategies: 30`,
`centring.cap_log_rate: 0.35`, `centring.cap_slope` (sin valor: lo propone K-m) ·
`cost_stress.k: 1.25` · `concentration.drop_trades: 3`, `drop_period: quarter` ·
`mae.percentile: 95` · `delay.variants: [E+1, S+1, ES+1]` (admite `E-1`), `delay.on_build: false`
· `homogeneity.permutations: 5000`, `period: quarter`, `seed` · `drawdown.block: 8`,
`sequences: 5000`, `seed` · `monkey.draws: 5000`, `monkey.seed`. Las semillas viven en el
`config.yaml` de la puerta, nunca en `engines/nulls/config.yaml`; nueva en cada corrida y anotada
en el scorecard (P.7-3). En `falsePositives/config.yaml` (las escribe el paquete 0): `population.per_level: 5000`,
`population.edges: [0.05, 0.10, 0.15]`, `population.seed`.

**Las reglas.** El bloque del paso "8" con las 16 reglas de §1.2 se escribe en la oleada 0 en
`tests/fixtures/criteria_paso8.yaml` — no en el `criteria.yaml` vivo — con una tabla de verdad
por regla en `tests/test_gate_rules.py`. Las de dos hechos (R5c, R5d, R8, calidad de datos,
retraso) van con `all` / `any` **anidados** (comprobado: caben; R5, sin valor absoluto, son dos
reglas de un lado); ningún valor inventado para «ninguna afectada» (`n_afectadas`).
Si una regla no cabe en el formato, es pregunta al dueño, no una clave nueva.

**Un hecho mal nombrado no falla: se lee como Limbo** (`pipeline/autopilot/criteria.py:92-96`),
que es un veredicto legal. Por eso el contrato se comprueba dos veces, sin pieza nueva:
`tests/test_gate_rules.py` afirma que la unión de los hechos que declaran los niveles contiene
todos los que nombran las reglas del fixture (los niveles vacíos ya los declaran: pasa desde la
oleada 0, y lo rompe en su oleada quien renombre una columna); e I afirma, con la cascada
apagada sobre las 3.000 de USA500, que ningún hecho de las reglas falta entero y lista, por
hecho, cuántas estrategias lo tienen vacío.

**Producción nunca lee de `tests/fixtures/`.** Hasta el paquete I el registro de niveles no lo
llama nadie más que los tests; I pasa las reglas del fixture a `criteria.yaml` y borra el
fixture en el mismo paquete.

## P.4 · Reglas de todos los paquetes

- Lee `CLAUDE.md`, `CODESTYLE.md`, `studies/CLAUDE.md` y el `README.md` de cada carpeta que toques.
- Tocas **sólo** los ficheros que posees. Lo que necesites de otro —una clave, una firma— lo
  devuelves como petición; no lo editas.
- **Primero se añade, se conmuta una vez, se borra al final.** Hasta el paquete I la puerta
  viva y `criteria.yaml` no cambian de comportamiento: otras sesiones corren workflows desde
  este mismo árbol. Al acabar tu paquete, los tests que ya pasaban siguen pasando.
- Ninguna cifra en el código: claves de P.3. Un caso de respuesta conocida por hecho nuevo.
- No haces commit, no lanzas SQX, no tocas el maestro, `oos2`, `portfolio/funded/`, los criterios
  de otros pasos ni el paso 4 de `studies/data/spread/`. `ledger/thresholds.yaml` sólo gana filas.
- No regeneras documentos (`tools/depmap.py`, `tools/manual.py`, `tools/skillmap.py`) ni editas
  `README.md` compartidos (`pipeline/autopilot/README.md` entre ellos) ni los `INDEX.md` de `knowhow/`: lo hace la orquestadora al cerrar la
  oleada, con lo que devuelvas.
- **Medir** (paquetes `-m`) sólo con la máquina sin workflows: `.claude/skills/sqx-wait/preflight.sh`
  antes; si hay uno en marcha, se espera (regla 19).
- Una duda con dos lecturas se devuelve como pregunta (regla 11); no se elige.
- **Devuelves:** ficheros cambiados · la salida pegada de tu orden de prueba · desviaciones y
  peticiones · hechos para `knowhow/` (tarjeta y texto) · líneas para el README de la carpeta.
- **Corres sólo tus tests** (`python3 -m pytest -q tests/<tus ficheros>`). `tools/checks.py` y
  los tests de otros no: en una oleada en paralelo leen ficheros a medio escribir de otro
  paquete y fallan por lo que no es tuyo. Los corre la orquestadora al cerrar la oleada.
- **Un fichero cambia de dueño sólo entre oleadas**, y lo dice la columna «posee»: los
  `gate/level*.py` vacíos del paquete 0 pasan en la oleada 3 a quien los rellena;
  `gate/config.yaml` y `tooltips.py` son del 0, luego de I, de Z0 y de Z1; `criteria.yaml` es de
  I y luego de Z1; `gate/harvest.py`, de B1 y luego de B2.
- **Excepción a «nada vivo cambia hasta I»:** B1 y B2 corrigen dos errores de la puerta de hoy
  (identidades, cosecha pisada) en ficheros vivos. Se lanzan con los workers parados y su prueba
  incluye que una corrida ya juzgada dé el mismo veredicto salvo en las estrategias que arreglan.

## P.5 · Oleadas

Dentro de una oleada los paquetes van en paralelo salvo que diga «en serie». ⏸ = parada del dueño.

### Oleada 0 — contratos, identidades y lo que hay que saber antes

| paquete | objetivo | posee | sólo lee | contrato y casos | prueba | modelo |
|---|---|---|---|---|---|---|
| **0** | El esqueleto de P.3: registro de niveles con funciones vacías, claves de configuración, frases de ayuda, y las 16 reglas en un fixture con su tabla de verdad | `gate/levels.py`, `gate/level*.py` (vacíos), `gate/config.yaml`, `gate/tooltips.py`, `falsePositives/config.yaml` y su `tooltips.py` (sólo las claves `population.*`), `tests/fixtures/criteria_paso8.yaml`, `tests/test_gate_rules.py` | `pipeline/autopilot/criteria.py`, especificación §0.3 y §4-8 | P.3 entero. Nada llama aún a `levels.py`. Cada regla: Pasa, Limbo y Falla con valores a mano, y «hecho que falta» | `pytest tests/test_gate_rules.py tests/test_gate_measures.py tests/test_ui_gate.py`; `grep -rn "gate.levels\|gate import levels" --include=*.py` sólo en el test | opus |
| **B1** | Que el juez encuentre los hechos de una estrategia cuya identidad cambió en el retest, en el único punto por el que pasan todos | `pipeline/autopilot/facts.py`, `pipeline/autopilot/judge.py` (sólo la resolución de identidad), `gate/harvest.py`, `gate/pairing.py`, `tests/test_autopilot_facts.py` | `knowhow/sqx-format/identity-differs-across-databanks.md`, `ui/daemon/advance/preflight.py:110` | **Reproduce antes** en una población cosechada donde caigan por presencia: si no se reproduce, ⏸ con lo hallado, sin tocar nada. El juez también juzga los pasos 10 a 16: el arreglo no cambia el veredicto de ninguna estrategia cuya identidad no cambió. Caso: par con identidad cambiada → sus hechos se encuentran | el recuento antes y después, pegado; `pytest tests/test_autopilot_facts.py tests/test_autopilot_criteria.py tests/test_autopilot_zero.py` | opus |
| **B2** (tras B1) | Que una cosecha no pise a otra de un conjunto distinto el mismo día, y rescatar las 10.000 de NIKKEI | `gate/harvest.py`, `tests/test_gate_harvest.py` | `gate/inputs.py`, `core/paths.py:146` (el que resuelve la carpeta, con 17 lectores: **no se toca**), quién re-cosecha tras el corte (`pipeline/autopilot/`) | Lo que resuelve `core/paths.py` no cambia; la cosecha que iba a pisarse se aparta donde ese resolvedor no la vea, y K la lee por ruta explícita. Casos: dos cosechas el mismo día de conjuntos distintos → quedan las dos; el resolvedor devuelve la misma carpeta que antes | su test | sonnet |
| **C1-m** | La auditoría de §C.1: A, B y C operación a operación contra SQX, hasta que cuadre o la diferencia tenga nombre y tamaño; y qué convención de precio y qué tolerancia hereda C2 | la tarjeta nueva «monkey-reprice-audit» en `knowhow/research/`, `scratch/` | `engines/market/calibrate.py`, `engines/nulls/`, `gate/monkey.py`, las fichas `assets/symbols/`, propuesta del mono `:8-28` | Entrega: tabla por componente (precio, lotes, valor del punto, spread, slippage, comisión, swap) con la diferencia en USD de cada una | la tabla; suma de componentes = 6.999 USD ± lo no explicado | opus |
| **E0-m** | Por qué `feedQuality` no dejó datos en la corrida de ejemplo; qué inventarios de anomalías existen por feed y si su eje de minutos sirve para marcar operaciones de cualquier timeframe; y lanza el `scan` del paso 4 para los feeds de las poblaciones de K que no lo tengan (sin inventario la regla sería Limbo para todas) | `AlgoData/feedQuality/<feed>/` de los feeds que falten | `studies/data/feedQuality/`, `AlgoData/feedQuality/`, `ui/daemon/runner/screening.py` | Entrega: causa con `fichero:línea`, y la lista feed → `events.parquet` (fecha, K, sesión) | el informe | sonnet |

### Oleada 1 — el repreciado común

| paquete | objetivo | posee | sólo lee | contrato y casos | prueba | modelo |
|---|---|---|---|---|---|---|
| **C2** | La función de P.3, con lado, costes declarados y swap por noche | `engines/market/reprice.py`, `tests/test_reprice.py`, `engines/market/README.md` | la tarjeta de C1-m, `core/trades.py:28`, `sqx/inspect/strategymeta/settings.py:89`, `knowhow/costs/per-task-costs.md` | Casos: A, B y C sin mover reproducen SQX dentro de la tolerancia de C1-m, escrita en el test; una operación de precio plano pierde exactamente su coste; larga y corta simétricas; una noche de triple swap | `pytest tests/test_reprice.py` | opus |

Si C1-m no cuadra ni nombra la diferencia: ⏸ — nada del mono entra en la puerta (§3.3 de la
especificación) y el plan sigue sin G2 hasta que el dueño decida.

### Oleada 2 — R3

| paquete | objetivo | posee | sólo lee | contrato y casos | prueba | modelo |
|---|---|---|---|---|---|---|
| **D** | El exceso con deriva por ventana, las cuatro variantes del término y el error estándar con sesgo y curtosis | `analysis/tradelevel.py`, `gate/level1a.py`, `tests/test_gate_r3.py` | `engines/market/reprice.py`, `crossmarket/simulate/excess.py` (`blind`: se copia, no se importa), especificación §5 | `mean_move`, `drift` y `t` conservan firma y columnas (`n`, `iid`, `ar1`): `tests/test_crossmarket_excess.py:53` ata a ellas la t del paso 10. Lo nuevo se añade. El P/L es el de C2. Casos: siempre larga y siempre dentro → exceso total 0 con cualquier ventana; ventana < trimestre → rechaza; con γ3 = 0 y γ4 = 3 dados a mano la fórmula da s·√(n−1) / √(1 + s²/2) | `pytest tests/test_gate_r3.py tests/test_gate_measures.py tests/test_crossmarket_excess.py` | opus |
| **D-m** (tras D) | La medida de D.2 y D.3 | `knowhow/research/drift-term-biased-by-side.md`, `gate-t-scales.md`, `trade-t-vs-frequency-and-skew.md` (editar) | las cosechas, las barras | Entrega, año y semestre lado a lado, para (a)-(d): sesgo por lado y activo de una estrategia sin ventaja, falsos positivos a 1,65, cuántas cambian de veredicto y hacia dónde; y la t con sesgo-curtosis **junto** al n efectivo AR(1): falsos positivos de las cuatro combinaciones | las tablas | opus |

⏸ **Parada 1 — la ventana de la deriva** (año o semestre), con las tablas de D-m. La variante se
carga sola. No bloquea la oleada 3, que programa con `year` provisional; sí bloquea K-m.

### Oleada 3 — las reglas, en paralelo (arranca al acabar D)

| paquete | objetivo | posee | sólo lee | contrato y casos | prueba | modelo |
|---|---|---|---|---|---|---|
| **E1** | R5 y R5d con su centrado | `analysis/centred.py`, `gate/level1b_centred.py`, `tests/test_gate_centred.py` | `tradelevel.py`, propuesta R5 `:19-130`, `:208-262`, especificación §6.1, §6.3 | Se calcula para **toda** la población retesteada. Población del centro: mismo activo, timeframe y lado; < 30 → no centra; centro recortado. Casos: misma tasa en build y oos1 → `z_frec` ≈ 0; 29 estrategias → sin centrar; población que cae un 60 % → el centro se queda en −0,35; exceso constante → `t_b` ≈ 0 | `pytest tests/test_gate_centred.py` | opus |
| **E2** | R5c, R8 y R9b | `analysis/onepass.py`, `gate/level1b_onepass.py`, `tests/test_gate_onepass.py` | `tradelevel.py`, `reprice.py`, `analysis/floating.py`, especificación §6.2, §6.4, §6.5 | `edge_mean_oos` = bruto medio / coste medio cobrado, sólo oos1; `t_exceso_k` = la t de R3 restando (k − 1) × coste. Casos: k = 1 → `t_exceso_k` = `drift_excess_t`; quitar 3 de una serie constante no cambia la media; MAE todas iguales → p95 = ese valor | `pytest tests/test_gate_onepass.py` | sonnet |
| **E3** | Calidad de datos | `analysis/dataquality.py`, `gate/level1b_data.py`, `tests/test_gate_dataquality.py` | informe de E0-m, `feedQuality/touch.py` (referencia, no se importa), especificación §6.6 | Marca las operaciones de oos1 con una anomalía entre su barra de entrada y la de salida. Sin inventario del feed → hecho ausente (Limbo), nunca excepción muda. Casos: ninguna afectada → `n_afectadas` = 0; todas las ganancias en las afectadas → `ret_datos` ≈ 0 y `t_a` alto | `pytest tests/test_gate_dataquality.py` | sonnet |
| **F** | El retraso de una barra | `analysis/delay.py`, `gate/level2.py`, `tests/test_gate_delay.py` | `reprice.py`, propuesta 4.2-4.4 `:38-132`, especificación §7 | E+1, S+1, ES+1 repreciadas con C2; se juzga la peor; `t_Δ` pareada de la misma variante que da el `ret` mínimo (P.7-4). `E-1` y el build, programados y apagados. Casos: precio plano → `ret` = 1; ventaja que vive sólo en la primera barra → `ret` ≈ 0 | `pytest tests/test_gate_delay.py` | opus |
| **G1** | R7 y R6 | `analysis/resample.py`, `gate/level3ab.py`, `tests/test_gate_resample.py` | `tradelevel.py`, propuesta R6-R7-R8 `:20-160`, especificación §8.1, §8.2 | Semilla fija → mismo resultado byte a byte. Casos: operaciones idénticas en todos los trimestres → `q_p` alto; todo el beneficio en un trimestre → `q_p` bajo; oos1 = build remuestreado → `dd_p` centrado | `pytest tests/test_gate_resample.py` | opus |
| **G2** | El mono: sorteo dentro de la ventana de R3, tamaño por la doctrina en su momento, repreciado con C2, 5.000 sorteos, z | `engines/nulls/` (entero), `gate/level3c.py`, `tests/test_gate_mono.py`, `tests/test_nulls_seed.py`, `engines/nulls/README.md` | `reprice.py`, `falsePositives/model.py:29,67` (`atr_sized`: se sube al motor copiándolo), `knowhow/research/monkey-size-carries-donor-volatility.md`, especificación §8.3 | Lo que hoy usa `engines/nulls` (`readings/monkey`, `falsePositives`, `crossmarket`) da los mismos números que antes: lo nuevo es opción. Sólo oos1. Casos: estrategia que **es** un sorteo → z ≈ 0 en media; entrada con previsión perfecta → z alta; misma semilla → mismo z | `pytest tests/test_gate_mono.py tests/test_nulls_seed.py tests/test_calc_engines.py tests/test_false_positives.py tests/test_sweep.py tests/test_crosstf_facts.py tests/test_conditionalmap.py tests/test_models.py` y los `tests/test_oracle_*.py` (uno a uno): `engines/nulls` tiene unos 35 importadores | opus |
| **G2-m** (tras G2) | Lo que cuesta el mono a 5.000 sorteos contra 2.000 de hoy, por estrategia y para 300, 3.000 y 20.000 | nada (informe) | — | Entrega: segundos y GB. Si 20.000 estrategias no caben en una noche, lo dice con la cifra | la tabla | sonnet |

### Oleada 4 — la conmutación (un solo paquete, con los workers parados)

Era I1 + I2: el ataque mostró que partirla deja el árbol roto entre los dos (al borrar las
cribas dejan de importarse `falsePositives/chain.py:9`, `tests/test_autopilot_facts.py:15`,
`perf/inputs/workloads.py:19`, `ui/daemon/gateview.py:41` y `gate/inputs.py:30`). Va entera.

| paquete | objetivo | posee | sólo lee | contrato y casos | prueba | modelo |
|---|---|---|---|---|---|---|
| **I** | La puerta corre por niveles, sin cribas viejas, y el juez y el piloto leen las reglas nuevas | `gate/{levels,cascade,screens,monkey,measures,report,many,one,inputs}.py`, `gate/config.yaml`, `gate/tooltips.py`; `pipeline/autopilot/criteria.yaml` (paso "8" y cabecera), `judge.py`, `facts.py`, `run.py` (`AFTER_CUT`); `ui/daemon/workflow/steps.py` (lista del paso 8), `ui/daemon/gateview.py`, `databank/funnel.py`, `results/forproject.py`; `falsePositives/chain.py` (sólo el import y la llamada a la puerta), `perf/inputs/workloads.py` (sólo la línea del import); `tests/test_gate_{measures,cascade,rules}.py`, `test_ui_gate.py`, `test_autopilot_{criteria,facts,smoke,policy}.py`, `test_false_positives.py`, `tests/fixtures/criteria_paso8.yaml` (se borra); `ledger/thresholds.yaml` y `tests/test_thresholds.py` (las filas de las cribas borradas salen, P.7-5) | los `level*.py`, `pipeline/autopilot/criteria.py` | **En este orden, y si (a) falla no se pasa a (b):** (a) el camino por niveles, sin tocar el de hoy: sobre las 3.000 de USA500, con las reglas del fixture y `criteria.outcomes` sobre los hechos recogidos —**nunca `judge.judge()`**, que corta el databank y firma el ledger (`judge.py:126-129`)—, cascada encendida y apagada dan **el mismo veredicto**, y sale la tabla de hechos vacíos; (b) la conmutación: las 16 reglas a `criteria.yaml`, fuera `degradacion`, `forma`, `mono` de p y `familia`, fuera las reglas R5 vieja (`oos_trades_per_year`), R6, R7, R8 viejas, R9a, R9c, `spread.*` y `edgeCost.*`; `READABLE` (`judge.py:27`) pasa a los hechos del nivel 0; los importadores de arriba, arreglados. R3: `pass ">= 1.65"`, sin `limbo` ni `by`. El scorecard se escribe tras cada nivel; `--from-level N` reanuda. `funnel.csv`: por nivel y regla, entran y caen. El motivo de una caída nombra su primera regla y no lista «sin dato» de las no calculadas. `dev.on` **no se toca**. Paso 8: `gate` solo (`feedQuality` sale, P.7-2); tras el corte, `entryQuality` y `monkey`. Caso: una que cae en el nivel 0 no tiene hechos del 1a | `preflight.sh` antes (regla 19: nada pesado junto a un workflow); `pytest` de todos sus tests; el embudo de USA500 y la tabla de hechos vacíos, pegados; `python3 -c "import studies.screening.falsePositives.chain, perf.inputs.workloads, ui.daemon.gateview"` | opus |

### Oleada 5 — borrados, ventana, poblaciones y fondeo

H va **en serie** (H1 → H2 → H3: comparten `catalogue.py`, `knobs.py`, `tools/manual.py`,
`candidates.py`, `steps.py`, `ui/text/columnhelp*.py`, `tests/test_columnhelp.py`,
`tests/test_thresholds.py`); J1, J2, K, L van en paralelo con H y entre sí.

| paquete | objetivo | posee | sólo lee | contrato y casos | prueba | modelo |
|---|---|---|---|---|---|---|
| **H1** | Borrar la mitad del paso 8 del spread y lo que arrastra (P.2-4) | `studies/data/spread/{reprice,one,many,report}.py`, su `inputs.py` (sólo lo que usaba `report`), `config.yaml` (bloque `reprice`), `README.md`; `ui/daemon/runner/screening.py`, `results/catalogue.py`, `results/knobs.py`, `databank/equity.py`, `strategy/{costcurve,api,stats}.py`, `tearsheet/{api,sheet,pnl}.py`, `ui/desktop/workspace/{fichacurves,fichajobs}.py`; `tests/test_spread.py`; `manual-fuentes/59-spread-real.md`, `68-app-estrategia.md`; `docs/AgentPDFs/WORKFLOW.md` (fila 25.5), `docs/encargos/36-…md` y su `README.md`, `OPEN.md` #76 (`/open-close`), `knowhow/costs/darwinex-real-spread.md`; `tools/manual.py` (la lista de capítulos), `portfolio/common/construct/candidates.py` (`:19`), `ui/daemon/workflow/steps.py` (fila 25.5), `ui/text/columnhelp_verdicts.py`, `tests/test_columnhelp.py` | `graphify affected` de cada fichero | El paso 4 intacto: `scan`, `onboard`, `bands`, `fundedswap` y sus tests. Los **datos** de `AlgoData/reports/*/spread/` no se borran | `pytest tests/test_spread.py tests/test_columnhelp.py tests/test_ui_*.py`; `grep -rnE "data\.spread\.(reprice|report|one|many)|data\.spread import (reprice|report|one|many)" --include=*.py .` vacío (`engines/market/reprice.py` es otro y se queda) | sonnet |
| **H2** | Borrar `snoopingScreen` y `profitShape` | las dos carpetas, sus filas en `catalogue.py`, `knobs.py`, `runner/{screening,readings}.py`, `ui/daemon/runs.py`, `runner/table.py`, `ui/daemon/workflow/tests.py`, `steps.py` (`EXTRA`), `pipeline/autopilot/run.py` (`AFTER_CUT`), `facts.py:208`, `portfolio/common/construct/candidates.py`, `studies/research/memory/config.yaml:141`, `perf/inputs/{targets,workloads}.py`, `tests/test_snooping.py`, `test_tradeshape.py`, `test_close_curve.py`, `test_thresholds.py`, `test_columnhelp.py`, `test_rail_run.py`, `test_ui_{runner,loader,ops}.py`, `test_autopilot_facts.py:144-154`, `ui/text/columnhelp*.py`, `manual-fuentes/49-snooping.md`, `40-forma-del-beneficio.md`, `tools/manual.py`, `studies/CLAUDE.md` | `blindJoint/` (no se toca) | La clave `snoopingScreen.stepm.fwer` del ledger **se queda**: la lee el paso 20. Lo que `test_close_curve.py` y `perf` importaban de `snoopingScreen.inputs` se copia a quien lo usa | los tests citados; `grep -rnE "^\s*(from|import) .*(snoopingScreen|profitShape)" --include=*.py .` vacío (un comentario no cuenta; la clave del ledger es texto en un YAML) | sonnet |
| **H3** | `edgeCost` a la definición nueva (P.2-3) | `studies/readings/edgeCost/` (entero; fuera `spread_share.py`), `ui/text/columnhelp*.py`, `ui/daemon/databank/layout.py`, `tests/test_edgecost*.py`, `test_columnhelp.py`, `manual-fuentes/50-edge-por-coste.md` | `reprice.py`, `analysis/onepass.py`, `pipeline/autopilot/{tail,traded}.py` | Caso: sobre las mismas operaciones, `edge_mean` de `edgeCost` = `edge_mean_oos` de la puerta | sus tests, `tests/test_autopilot_closing.py`, `test_chain.py` | sonnet |
| **J1** | Los parámetros de la puerta y de `falsePositives` se guardan desde la ventana, con comentarios | `ui/daemon/sqxconfig/{studies,studywrite,sections}.py`, `tests/test_ui_sqxconfig_studies.py` | `gate/config.yaml`, `gate/tooltips.py`, `falsePositives/config.yaml`, `ui/daemon/sqxconfig/api.py:34-44`, `ui/README.md` | Una entrada por clave de P.3, con rango (`drift.window` nunca bajo trimestre; repeticiones ≥ 5.000 de partida). Sin editor nuevo: es la vista de configuración que hoy guarda WFC y CSCV. Si esa vista no pinta sola las secciones nuevas, devuelve el fichero de `ui/desktop/` que hay que tocar como petición; J3 lo prueba con captura | su test: escribir cada clave y releerla con sus comentarios | sonnet |
| **J2** | El diálogo de reglas conserva `missing:` y enseña la frase de la regla | `ui/desktop/criteria/{dialog,overrides,zone}.py`, `ui/daemon/criteria/{read,write,api}.py`, `tests/test_ui_criteria.py` | `criteria.yaml` | Caso: editar una regla con `missing: fail` y una compuesta **anidada** (`all` dentro de `any`, como R5d), guardar, y el YAML sólo cambia en lo editado | su test | sonnet |
| **K** | `falsePositives` por la cadena nueva, cascada apagada, con ventaja plantada | `studies/screening/falsePositives/` (entero), `tests/test_false_positives.py`, `manual-fuentes/99-monos-por-la-cadena.md` | `gate/levels.py`, `engines/nulls/`, `studies/research/profilePower/` (patrón) | Niveles 0 (nula), 0,05, 0,10, 0,15: a cada operación de oos1 del mono se le suma Sharpe × desviación de su exceso. Sale `reglas.csv`: regla × nivel × Pasa/Limbo/Falla, y el embudo. Tamaño `atr`. Lee la cosecha por ruta explícita. No cambia los nombres que importa `perf/inputs/workloads.py:19,245-249` (ese fichero es de H2 en esta oleada). Casos: nivel 0 → R3 pasa ≈ 5 %; Sharpe 0,15 con 196 operaciones → R3 pasa ≈ 67 % | su test | opus |
| **L** | Guardar para fondeo al pasar el WFM | `pipeline/autopilot/kept.py` (nuevo), `tail.py`, `core/paths.py` (una constante), `tests/test_autopilot_kept.py` | `blind.py:57-79`, `wfm/verdict/call.py`, `gate/inputs.py`, encargo 45 | Por estrategia: curva diaria de flotante de oos1, `oos_worst_day_r`, `dd_esperado_p95_r`, neto anual en R, en la raíz de datos. **Antes de programar:** cómo se llega de la que pasa el WFM (madre o variante) a su fila del paso 8; si no es única, pregunta | su test, `tests/test_autopilot_tail.py` | sonnet |

### Oleada 6 — medir (en serie: Z0 → P → J3 → K-m)

En serie porque P cronometra y no puede tener a K-m cargando la máquina, y porque la prueba de
J3 cambia `gate/config.yaml` mientras K-m lo lee.

| paquete | objetivo | posee | sólo lee | contrato y casos | prueba | modelo |
|---|---|---|---|---|---|---|
| **Z0** (tras la parada 1) | Cargar la ventana de la deriva y la variante del término | `gate/config.yaml` (`drift.window`, `drift.variant`), `knowhow/research/drift-term-biased-by-side.md` | la respuesta del dueño, las tablas de D-m | — | `pytest tests/test_gate_r3.py tests/test_gate_rules.py` | sonnet |
| **P** | El coste de cada nivel en `perf/`, y el de guardar para fondeo (L) | `perf/inputs/{targets,workloads}.py`, `perf/config.yaml`, `manual-fuentes/12-rendimiento.md` | informe de G2-m | Un objetivo por nivel, el del mono a 5.000 y el de `kept` | `preflight.sh`; `python3 -m perf …` del catálogo | sonnet |
| **J3** | El embudo por nivel y regla en la ventana, y la prueba de la tabla J | `ui/desktop/workspace/funnel.py`, `ui/daemon/databank/api.py`, `ui/text/glossary.py`, y lo que J1 devolvió como petición | lo de J1, J2, I | `/ui-shot` de Criterios, de la configuración de la puerta y del embudo; cada fila de la tabla J cambiada desde la ventana cambia el resultado. **Deja `gate/config.yaml`, `falsePositives/config.yaml` y `criteria.yaml` byte a byte como los encontró** (`git hash-object` antes y después) | las capturas, la tabla parámetro → hecho que cambió, y los hashes | sonnet |
| **K-m** | El embudo de las dos poblaciones | `AlgoData/reports/…/falsePositives/`, la tarjeta nueva «gate-chain-false-positives» en `knowhow/research/` | — | Entrega de §K: por regla y nivel, Pasa / Limbo / Falla; el embudo; por línea, «a X pierde el A % de las de 0,10 y deja pasar el B % de las nulas»; el tope de R5d; R7 con las dos ventanas; cuánto efecto común le queda a R5d; H1 frente a M30; si R1b pide suelo. Dice qué reglas **heredan** su resultado del donante (frecuencia) y no se miden, y cuáles midió sólo sobre las de exceso medio positivo | `preflight.sh`; las tablas | opus |

⏸ **Parada 2 — las líneas**, con el embudo de K-m: las líneas de cada regla, el tope de R5d y
el ±0,35 de R5, H1 y H4, el suelo de R1b. Y los argumentos de la corrida V (activo, timeframe,
plantilla o simple, cuántas): son del dueño.

### Oleada 7 — cierre

| paquete | objetivo | posee | sólo lee | contrato y casos | prueba | modelo |
|---|---|---|---|---|---|---|
| **Z1** | Cargar las líneas congeladas | `criteria.yaml` (paso "8"), `ledger/thresholds.yaml` (filas nuevas), `gate/config.yaml` | la respuesta del dueño | — | `pytest tests/test_gate_rules.py tests/test_thresholds.py` | sonnet |
| **M** | La documentación de §M | la especificación y su PDF (`/dossier-pdf`), `criterios-pasos-6-a-19-explicados…md`, `manual-fuentes/29-puerta.md` (`/manual-chapter`), `gate/README.md`, `.claude/skills/workflow-simple/steps.md`, `.claude/skills/oos-gate/SKILL.md`, `WORKFLOW.md` (fila 8), los `INDEX.md` de `knowhow/` | lo devuelto por todos los paquetes | — | `python3 tools/manual.py && python3 tools/depmap.py && python3 tools/checks.py` | sonnet |
| **V** (tras Z1) | La corrida de verificación | un proyecto `Test_` | — | `bin/workflow.sh` entero, **nunca `--smoke`** (bajo `ALGO_SMOKE` el juez sólo lee las reglas del nivel 0), con los argumentos que dio el dueño en la parada 2 y el custodian libre (`preflight.sh`); el embudo pegado; el proyecto retirado (regla 6) | el embudo y el `retire` | sonnet |

⏸ **Parada 3 — apagar `dev.on`**: sólo cuando el dueño lo diga, con V a la vista.

**La orquestadora** (Council, 2026-10-06):

- **Antes de la oleada 0, el árbol limpio en lo que el plan posee.** Hoy tienen cambios sin
  commit de otras sesiones `engines/nulls/*`, `gate/{cascade.py,config.yaml,README.md}`,
  `pipeline/autopilot/{facts,run,plan}.py`, `tests/test_autopilot_facts.py`, `tools/manual.py`,
  `ledger/thresholds.yaml` y `perf/config.yaml`. Mientras sigan así un paquete no distingue su
  diff del ajeno: pregunta 0 de P.7.

- **Antes de cada oleada** guarda en `scratch/` la línea base: `git status --porcelain` y el
  `git hash-object` de cada fichero modificado o sin seguimiento. El árbol ya está sucio con
  cambios de otras sesiones: sin línea base, comparar con `git status` no dice nada.
- **Al volver cada paquete** compara con la línea base. Una ruta cambiada que no está en su
  «posee» ni en el de otro paquete en marcha es **parada**: nombra el paquete y el fichero.
  Puede ser de otra sesión; lo decide ella mirando el diff, no lo ignora.
- **Regla de parada, única:** test rojo, desviación del contrato o petición sobre un fichero
  ajeno → la oleada no se cierra. Un reintento del paquete con el fallo pegado; si sigue,
  informe al dueño. Nunca se salta a la oleada siguiente.
- **Al cerrar cada oleada:** `python3 tools/depmap.py && python3 tools/checks.py`, los tests de
  la oleada juntos y `tests/test_gate_rules.py` (que desde la oleada 0 afirma que los hechos
  declarados por los niveles cubren todos los que leen las reglas), las tarjetas e índices de
  `knowhow/`, la tabla de estado y la bitácora.
- En cada parada del dueño entrega la lista de ficheros y **¿Quieres hacer el commit?**; entre
  paradas no hay commit.

## P.6 · Riesgos, y cómo se detecta cada uno

| riesgo | cómo se detecta | qué se hace |
|---|---|---|
| El mono a 5.000 sorteos no cabe: K-m son 20.000 estrategias × 5.000 | G2-m, antes de I, da segundos por estrategia | si K-m pasa de una noche, se le lleva al dueño la cifra: menos estrategias por nivel o el mono sólo sobre las que pasan R3 |
| La auditoría del repreciado no cuadra | C1-m: queda diferencia sin nombre | ⏸; el plan sigue sin G2 |
| Cascada encendida ≠ apagada | el paso (a) de I sobre las 3.000 de USA500 | no se pasa a (b) hasta que sea idéntico |
| El centrado sobre clones: en K los monos de un donante comparten frecuencia, y una plantilla es una sola idea | K-m compara el centro de R5 y R5d entre reales y monos, y lista las reglas heredadas | esas reglas se entregan como «no medidas» y no se les propone línea |
| Una sola población grande (H1 largo) | K-m lo dice por regla | nada sobre H4 ni cortos se propone; es pregunta al dueño (abajo) |
| Un workflow de otra sesión corre la puerta a medio cambiar | la regla «añadir, conmutar, borrar»; el scorecard de hoy idéntico tras la oleada 0 | I se lanza con los workers parados (`preflight.sh`) |
| Dos paquetes tocan el mismo fichero, o un paquete toca lo que no posee | la línea base de la orquestadora antes de cada oleada y su comparación al volver cada paquete | parada con paquete y fichero |
| Un nivel emite un hecho mal nombrado o vacío en datos reales y el juez lo lee como Limbo | `tests/test_gate_rules.py` en cada cierre; la tabla de hechos vacíos de I (a) | no se pasa a (b) con un hecho entero ausente |
| Una regla de dos hechos no cabe en `all` / `any` | la tabla de verdad del paquete 0 | pregunta al dueño antes de la oleada 1 |
| `edgeCost` nuevo mueve la lectura del paso 25 | H3: su test contra la puerta; `tests/test_autopilot_closing.py` | decidido (P.2-3); se anota en el capítulo 50 |
| La que pasa el WFM no es la fila del paso 8 (variantes de 16.5) | L, antes de programar | pregunta |
| B1 cambia cómo el juez busca a una estrategia, y el juez juzga también los pasos 10 a 16 | su prueba: ningún veredicto cambia donde la identidad no cambió; si el diagnóstico no se reproduce, ⏸ | no se toca `judge.py` sin reproducirlo |
| El árbol ya está sucio en ficheros del plan | la línea base de la orquestadora | pregunta 0: commit antes de la oleada 0 |
| El plantado es un exceso constante: no depende de la entrada | — (por construcción) | K-m lo escribe: en el retraso y la calidad de datos mide rechazos por ruido, no potencia |

## P.7 · Preguntas al dueño — respondidas el 2026-10-06

**Respuestas, que mandan sobre el texto de las preguntas de abajo y no se reabren:**

0. Commit previo: **sí**, hecho antes de la oleada 0.
1. Poblaciones de K: **habrá más**. K-m corre sobre todas las cosechas completas (≥ 30
   estrategias, con MAE y curva) que existan al llegar a la oleada 6, además de USA500 H1 y de
   las 10.000 de NIKKEI225 M30; las lista antes de medir.
2. `feedQuality` **sale del paso 8**: el paquete I deja el paso con `gate` solo (tras el corte,
   `entryQuality` y `monkey`). El inventario de anomalías sigue saliendo del `scan` del paso 4.
3. Semillas: **nuevas en cada corrida**. Las claves `seed` de la puerta valen `null`; cada
   remuestreo (R7, R6, mono) anota la que usó en el scorecard (`q_seed`, `dd_seed`,
   `mono_seed`), y dada una semilla el resultado es el mismo.
4. `retraso_t_delta` es la t pareada de **la misma variante que da el `ret` mínimo**.
5. Las filas del ledger de las cribas borradas **salen**: el paquete I las quita de
   `ledger/thresholds.yaml` junto con las cribas (única excepción a «el ledger sólo gana filas»).


Las 0, 3, 4 y 5 hacen falta antes de la oleada 0 (fijan contratos); la 1 antes de K; la 2 antes
de I.

0. **El commit previo.** El árbol tiene cambios sin commit de otras sesiones en ficheros que
   este plan posee (lista en «La orquestadora»). ¿Los dejas en un commit antes de lanzar la
   oleada 0?
1. **Las poblaciones de K.** Con ≥ 30 estrategias hay una: USA500 H1 largo (3.000). Las 10.000
   de NIKKEI225 M30 sólo tienen operaciones (sin MAE ni curva: R9b y el flotante no se miden).
   ¿Basta con esas dos, o K espera a que haya más cosechas completas?
2. **`feedQuality` en el paso 8.** La regla de calidad de datos la calcula la puerta; el informe
   de `feedQuality` del paso 8 (su alarma y su `verdict.csv`) queda sin regla. El plan lo deja
   corriendo. ¿Se queda o sale del paso?
3. **Las semillas.** El encargo pide remuestreos reproducibles; tu decisión anterior para el mono
   es semilla nueva en cada corrida (`knowhow/eng/nulls-seed-fresh-per-run.md`, #45), guardada
   en el resultado. Dos lecturas: (a) nueva en cada corrida y anotada en el scorecard
   (`mono_seed`, y lo mismo R6 y R7) — reproducible releyéndola; (b) fija en `config.yaml`. El
   plan está escrito para (a) con la semilla anotada; con (b) cambia una línea del contrato.
4. **`t_Δ` del retraso.** «Se juzga la peor» de E+1, S+1 y ES+1: ¿`retraso_t_delta` es la t de
   **la misma** variante que da el `ret` mínimo (una variante decide las dos cifras), o la
   mayor t de las tres aunque sea de otra variante (más duro)?
5. **Las filas del ledger de las cribas que se borran** (`gate.degradacion.*`, `gate.forma.*`,
   `gate.mono.max_p`, `gate.familia.alpha`). Su `source` apunta a `gate/config.yaml#screens[…]`
   y `tests/test_thresholds.py:48` lo recorre: al borrar las cribas, o las filas salen del
   ledger, o se quedan marcadas como retiradas y el test deja de recorrerlas. ¿Cuál?
