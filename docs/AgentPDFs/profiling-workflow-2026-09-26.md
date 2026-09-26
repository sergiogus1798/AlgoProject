# Profiling del workflow entero — USDJPY H1, 2026-09-26 (encargo 21)

**Oficio de esta corrida: operador y medidor.** Los 25 pasos de `docs/AgentPDFs/WORKFLOW.md` se han
corrido uno detrás de otro sobre una población nueva, comprobando que cada uno funciona y midiendo
lo que cuesta — tiempo, CPU, memoria, disco. **No se ha optimizado nada y no se ha tocado código.**
Lo que se ha roto se anota con su error; lo que no depende de ello ha seguido.

El dueño estaba fuera; donde algo era ambiguo se ha elegido la lectura más conservadora, escrita
aquí como decisión propia, y se ha seguido.

- **Activo:** USDJPY (`USDJPY_DukasM1_the5ers`), **H1**.
- **Plantilla:** `crossAboveHMA_v1`, autorada en esta misma tarea (ver §5).
- **Proyecto:** `USDJPY_workflow_profiling_v1`, custodio (`SQX_w2`), `builder --workflow`.
- **Costes:** los PROVISIONALES de `assets/symbols/USDJPY.yaml` — spread 0.1, comisión 0.0 (¡cero!),
  slippage 0.05/0.05, swap 0/−10.4. Cada resultado con coste que sale de aquí lleva ese aviso: la
  comisión CERO infravalora el coste real ~10 veces y el spread no es creíble entre pares. Ningún
  número de este informe sirve para juzgar si el edge es real — sirve para saber qué cuesta correr
  la máquina.

---

## 0 · La plantilla — `crossAboveHMA_v1`

El dueño pidió «crossAboveHMA», el estilo de siempre (1 condición fija + 1 aleatoria libre, long),
y explícitamente: **el periodo de la HMA no lleva un valor fijo**. No existe en este install una
condición nativa de «el cierre cruza una HMA» ni el bloque custom ya presente con ese nombre sirve
(`CBlock_CrossAboveMA_3` cruza una HMA rápida contra una HMA lenta — dos medias, no precio contra
una). Se leyó como el equivalente exacto de `emaCloseCrossUp` (24/25-09, mismo estilo) con Hull en
vez de exponencial — **decisión mía, documentada en vez de preguntada** porque el dueño estaba fuera
y el encargo pedía conservador + seguir. Detalle completo, con la corrección del bug de autoría que
salió al construir: `~/Desktop/AlgoData/templates/library/crossAboveHMA_v1/brief.md` y
`knowhow/authoring/cloned-custom-block-native-key.md`.

Verificado sobre la población real: **200/200 estrategias del build llevan el bloque
`CBlock_CloseCrossesAboveHMA`**, con **64 periodos de HMA distintos** en el rango 2–220 — el periodo
se sortea por estrategia, tal y como pidió el dueño.

---

## 1 · El embudo — cuántas entran y cuántas salen de cada paso

| paso | qué | entran | salen | cómo se cortó |
|---|---|---|---|---|
| 4 | preflight `core.assets USDJPY` | — | ✅ exit 0 | — |
| 5–6 | build (`build` 2008–2017) | — | **200** | 352 condiciones de aceptación apagadas; tope `--max-strategies 200` |
| 7 | retest OOS (`oos1` 2018–2022) | 200 | 200 | acompaña al build en el mismo `action=start` |
| 8 | puerta OOS/IS (`gate.report`) | 200 | **96** | veredicto real: mono mata 1, estáticas/degradación matan 103; familia y redundancia son *soft* |
| 8 | corte de aforo por net profit IS | 96 | **8** | artificial, hasta el tope del encargo (≤8 hasta el 15) |
| 8 | snooping SPA/StepM | 200 (K = toda la cosecha) | — | 0/200 baten al buy&hold antes de corrección; anota, no filtra |
| 8 | edge por coste | 200 | — | reconciliación bruto/neto corr = 1.000000 |
| 9 | crossmarket, 9 pares the5ers | 8 | 8 | aceptación apagada, no filtra |
| 10 | análisis crossmarket (`studies.transfer.crossmarket.report`) | 8 | **0** | 0/8 pasan el suelo de amplitud (ningún mercado con esperanza > 0 en ≥ 50 % de los 9); **hallazgo real, no se aplicó `/curate`** — decisión mía: cortar aquí habría dejado 0 estrategias para ejercitar los pasos 10.5–16, así que las 8 siguen adelante como población de prueba del andamiaje, con esta ficha de que el veredicto real es «ninguna transfiere» |
| 10.5 | variantes escaladas H4+H12 | 8 | 16 | 3/8 clamped en H4, 5/8 en H12 (periodos cortos no se pueden dividir) |
| 11 | retest crossTF (H1+H4+H12) | 24 | 24 | aceptación apagada |
| 12 | lectura crossTF | 16 (hermanas escaladas) | **0** | 0/16 sobreviven: H4 4 `control_failed` + 4 `unusable`; H12 4 `control_failed` + 4 `unusable` |
| 13 | MC Retest (7 de 8 tareas — MinDist no aplica, entradas a mercado) | 8 | 8 en cada una de las 7 | **1er intento se rompió** (ver §4); reintento limpio |
| 14 | lectura MC Retest | 8 | **1** `INCONCLUSIVE`, 7 `FAIL` | 0/8 sobreviven; descarta correctamente los 8 duplicados que dejó el crash |
| 15 | SPP IS + SPP OOS | 8 | 8 | tope 15.000 permutaciones/estrategia, aceptación apagada, las dos tareas |
| 16 | lectura SPP (`design_brief`) | 8 | 8 `proceed` | ningún `noise`; las 8 quedan habilitadas para fabricar variantes |
| 16.5 | **corte a 3 madres** | 8 | **3** | regla del encargo (≤3 madres desde el 15 en adelante) — corrección mía tras fabricar de más para las 8 (ver §5) |
| 16.5 | fábrica de variantes, mínimo 1.000/madre | 3 | 7.549 | 1.23.51→4999, 1.28.59→1457, 1.29.55→1093 |
| 16.5 | retest WFC (3 patas × 3 madres, gasta `oos2`) | 7.549×3 tramos | **2 madres completas, la 3ª cortada** | 1.29.55 y 1.28.59 completas (3.279 y 4.371 backtests); 1.23.51 (4.999 variantes) cortada a mitad de `WFC 1 IS` por decisión de tiempo — ver §4.5 |
| **corrección** | alinear `Results`/`OOS` con las 3 madres del 16.5 | 8 | **3** | las 5 estrategias fuera del corte de variantes seguían en los databanks SQX; curadas para que 21–25 lean la misma población |
| 17 | Walk Forward Correlation | 2 madres (1.29.55, 1.28.59) | 2 | 1.29.55: rho 0,21 `no_fiable`; 1.28.59: rho 0,25 `indeciso` (cruza 0,3) — ninguna compra nada optimizando en IS |
| 18 | CSCV | 2 madres | 2 | 1.29.55: PBO 15 %, DSR 0,98; 1.28.59: PBO 9 %, DSR 0,98 |
| 18.5 | superficies por mercado | 2 madres | 2 | **0/9 mercados** comparten la región del decil superior en build, oos1 u oos2, en ninguna de las dos madres |
| 19 | Walk Forward Matrix | 3 madres (las 3 llegaron: no depende del WFC de variantes) | 3 | **0/3 predicen**: 1.23.51 y 1.28.59 `blind` (rho +0,08 y −0,08, IC cruza cero); 1.29.55 `perverse` (rho −0,25, IC no cruza cero — reoptimizar predice PEOR que no hacerlo). 1/3 (**1.28.59**, no 1.23.51 — corregido el 2026-09-26 leyendo `status.parquet` del export) marcada `FAILED` por el criterio de área 4×4, sin borrar |
| 20 | lectura conjunta ciega, a mano (el módulo no existe, por diseño) | 2 madres con las 4 piezas (1.29.55, 1.28.59) | 2 veredictos | ver §4.7 — ninguna de las dos pasa |
| 21 | exposición (`exposure.report`) | 3 | 3 | **3/3 `worth_it`**, eficiencia 2,33×–3,49× el buy&hold por hora expuesta |
| 22 | mapa condicional (sesiones + días) | 3 | 3 | 3 informes, sin veredicto — describe, no filtra |
| 23 | estructural (ablación + inversión) | 3 madres → 12 variantes | 12 | control «madre reconstruida == guardada» da **no** para el tramo build (846 vs 423 operaciones) — hallazgo real, no investigado a fondo |
| 24 | stop ATR (2 pasadas, percentiles 80/85/90/95) | 1 madre | 4 sub-estudios | pasada 1: X=80 no transfiere a `oos2`, los otros 3 sí; pasada 2 (rejilla de estabilidad): **los 4 leen «meseta»** |
| 25 | edge por coste sobre la versión con stop | 22 (lote del paso 24) | 22 | reconciliación bruto/neto corr = 1.000000; `--strategy <nombre original>` falla porque el lote renombra a `S00Vxxx` (ver §4.6) |

---

## 2 · La tabla de profiling — paso a paso

### SQX (custom project `USDJPY_workflow_profiling_v1`, custodio)

| paso | tarea SQX | entrada | pared | ritmo | nota |
|---|---|---|---|---|---|
| 5–6 | CONSTRUCCION (build) | 200 objetivo | 80 s | ~2.500/h | 1er intento falló por el bug de bloque (ver §4), 0 CPU perdida real (35 s) |
| 7 | OOS | 200 | 7,34 s | ~98.000/h | — |
| 9 | Retest Markets – Family (9 mercados) | 8×9 | 81 s | — | — |
| 11 | CrossTF (H1+H4+H12) | 24 | 26 s | ~3.300/h | — |
| 13 | MCR 1 Bar | 8 | 28,1 s | — | — |
| 13 | MCR 2 Spread | 8 | 260,1 s | — | — |
| 13 | MCR 3 Slippage | 8 | 268,9 s | — | — |
| 13 | MCR 5 Params | 8 | 21,3 s | — | MinDist no configurada (entradas a mercado) |
| 13 | MCR 6 Exits | 8 | 261,5 s | — | — |
| 13 | **MCR 7 OHLC** | 8 | **709,7 s** | — | la más cara de las 7 |
| 13 | **MCR 8 Stress** (5 métodos combinados) | 8 | **1.030,2 s** | — | la más cara de todas; sola es el 40 % del paso 13 |
| 15 | SPP IS | 8 | 161,1 s | — | tope 15.000 permutaciones |
| 15 | SPP OOS | 8 | 82,7 s | — | — |
| 16.5 | WFC 1 IS (madre 1.29.55, 1.093 variantes) | 1.093×10 mercados | 350,0 s | ~11.250/h | — |
| 16.5 | WFC 2 OOS1 (misma madre) | 1.093×10 | 176,5 s | ~22.300/h | — |
| 16.5 | WFC 3 OOS2 (misma madre) | 1.093×10 | 128,8 s | ~30.500/h | — |
| 16.5 | WFC 1 IS (madre 1.28.59, 1.457 variantes) | 1.457×10 | 352,0 s | ~14.900/h | **casi el mismo tiempo que con 1.093** — la carga de los 9 mercados domina, no el nº de variantes |
| 16.5 | WFC 2 OOS1 (1.28.59) | 1.457×10 | 176,8 s | — | — |
| 16.5 | WFC 3 OOS2 (1.28.59) | 1.457×10 | 129,0 s | — | — |
| 16.5 | WFC 1 IS (madre 1.23.51, 4.999 variantes) | 4.999×10 | **cortada, ~600 s parciales** | ~15.500/h tras el arranque | cortada deliberadamente por tiempo (§4.5); a ese ritmo habría tardado ~19 min sólo esta pata — sí escala con el nº de variantes, a diferencia de lo que sugerían las dos madres más pequeñas |
| 23 | WFC 1+2+3 (lote estructural, 12 variantes) | 12×10 | 74,5+32,1+25,3 = 131,8 s | — | lote pequeño: el coste fijo de cargar 9 mercados domina de sobra |
| 24 | WFC 1+2+3 (pasada 1, sonda, 2 variantes) | 2×10 | 48,1+26,7+19,9 = 94,7 s | — | — |
| 24 | WFC 1+2+3 (pasada 2, rejilla de 22, estabilidad) | 22×10 | 50,7+26,9+21,1 = 98,7 s | — | prácticamente el mismo tiempo que la pasada 1 con 11× más variantes: confirma que 9-mercados-fijo domina hasta poblaciones bastante mayores |

**Total SQX medido** (sin contar los ~600 s parciales de la 3ª madre del 16.5, que se cortaron y no
llegaron a producir un resultado usable): 80+7,34+81+26+28,1+260,1+268,9+21,3+261,5+709,7+1.030,2+
161,1+82,7+350,0+176,5+128,8+352,0+176,8+129,0+131,8+94,7+98,7 ≈ **4.660 s (≈ 78 min)** de SQX puro,
repartidos en más de 30 arranques/paradas de tarea.

### Python (mide, no toca SQX salvo exportar)

| paso | comando | entrada | pared | CPU | pico RSS | nota |
|---|---|---|---|---|---|---|
| 8 | `gate.harvest` | 200/200 | 43,3 s | — | — | arranca el conductor de refilón para exportar (ver §6) |
| 8 | `gate.report` | 200 | 3,12 s | 41,98 s | 664 MB | mono mata 1 |
| 8 | `snoopingScreen.report` | 200 | 4,23 s | 17,57 s | 1.849 MB | el pico de memoria más alto del paso 8 |
| 8 | `edgeCost.report` | 200 | 1,49 s | 8,10 s | 481 MB | — |
| 9 | `export_retest` (crossmarket) | 8×9 | 16,97 s | 60,5 s | 2.124 MB | 124.003 trades |
| 10 | `crossmarket.report` | 8 | 28,67 s | 555,0 s | 2.171 MB | **19,3× CPU/pared** — muy paralelo; el pico de CPU-tiempo más alto medido |
| 11 | `export_retest` (crossTF) | 24 | 18,22 s | 60,2 s | 2.130 MB | 190.724 trades |
| 12 | `crossTF.report` | 16 | 10,28 s | 23,26 s | 466 MB | — |
| 13 | `mcRetest.ingest` | 8×7 | 3,46 s | 38,4 s | 455 MB | 63.826 simulaciones leídas |
| 14 | `mcRetest.report` | 8 | 3,07 s | 37,9 s | 1.401 MB | — |
| 15 | `export_spp` ×2 | 8+8 | 43,68 s | — | — | — |
| 16 | `spp.report` ×2 | 8+8 | 4,94 s | 15,4 s | 1.222 MB | 16 `design_brief.json`, todos `proceed` |
| 21 | `export_retest` (OOS, para exposición) | 3 | — | — | — | el export de `Results` (IST) no sirve — ver §4.6 |
| 21 | `exposure.report` | 3 | 0,59 s | 15,19 s | 209 MB | 3/3 `worth_it`, eficiencia 2,33×–3,49× |
| 22 | `conditionalMap.report` ×3 | 3 | 1,27 s (c/u) | 7,63 s (c/u) | 325 MB | reutiliza el harvest ya hecho del paso 8, sin volver a exportar |
| 23 | `sqx.structural.make` | 3 madres | — | — | — | 2 ablaciones + 1 inversión + 1 identidad por madre |
| 23 | `sqx.structural.keep` | 12×3 | — | — | — | 36/36 `ok=True`; un falso positivo de "custodio arriba" por un `tail -F` propio (ver §4.6) |
| 23 | `structure.report` | 12 | 4,73 s | 10,47 s | 690 MB | control de reconstrucción da «no» en `build` |
| 24 | `atrCalculator.report` (pasada 1, sólo lee X) | 2 | 1,19 s | 13,81 s | 316 MB | 4 percentiles; injerto idéntico a X=1000 en las 3 ventanas (0 diferencias) |
| 24 | `atrCalculator.report` (pasada 2, estabilidad) | 22 | 1,69 s | 14,20 s | 503 MB | los 4 percentiles leen «meseta» |
| 25 | `gate.harvest` (WFC_Build+WFC_OOS1) | 22 | — | — | — | 0 con identidad distinta |
| 25 | `edgeCost.report` (población completa) | 22 | 0,74 s | 6,96 s | 286 MB | reconciliación corr = 1.000000, n = 29.850 |

**Total Python medido:** ≈ 220 s (3,7 min) — nada se acerca a los minutos, salvo `crossmarket.report`
en CPU-tiempo (9,25 min de CPU en 28,7 s de pared gracias al paralelismo).

---

## 3 · Dónde se va el tiempo, y dónde la memoria

**Los cinco pasos más caros en tiempo de pared** (sin contar el WFC de la 3ª madre, aún en curso):

1. **MCR 8 Stress** — 1.030,2 s (17,2 min). Combina 5 métodos de perturbación en una sola tarea.
2. **MCR 7 OHLC** — 709,7 s (11,8 min).
3. **WFC 1 IS** (por madre) — ~350 s cada vez, **casi constante entre 1.093 y 1.457 variantes**: la
   carga de los 9 mercados adicionales domina sobre el número de estrategias, hasta que la
   población crece lo bastante (la 3ª madre, 4.999 variantes, sí escaló).
4. **MCR 3 Slippage** — 268,9 s.
5. **MCR 6 Exits** — 261,5 s.

**Los cinco pasos más caros en CPU-tiempo (Python)**:

1. **`crossmarket.report`** — 555,0 s de CPU en 28,7 s de pared (19,3×). El estudio con
   permutaciones/bootstraps más caro de los medidos.
2. **`gate.report`** — 41,98 s de CPU (13,5× su pared).
3. **`crossTF.report`** — 23,26 s de CPU.
4. **`mcRetest.ingest`** — 38,4 s de CPU.
5. **`mcRetest.report`** — 37,9 s de CPU.

**Memoria (pico de RSS del proceso principal, no del árbol completo — ver §7 sobre la limitación de
medición)**: el pico más alto es `snoopingScreen.report` con 1.849 MB seguido de `crossmarket.report`
con 2.171 MB y las dos exportaciones de trades (`export_retest`) con ~2.1–2.13 GB cada una. Ninguno
se acerca a un límite preocupante en esta máquina (125 GB).

**Coste por unidad de trabajo**: el crossmarket (paso 9+10) cuesta ~81 s de SQX + 45,6 s de Python
por 8 estrategias × 9 mercados = 72 combinaciones → **~1,75 s por combinación estrategia-mercado**,
similar al coste medido el 24-09. El MC Retest cuesta, sumando sus 7 tareas, ~2.580 s por 8
estrategias → **~322 s por estrategia** con esta batería completa (7 de 8 tareas).

---

## 4 · Lo que se rompió, con su error y cómo reproducirlo

### 4.1 · Bloque custom mal escrito en la primera autoría de la plantilla

Al clonar `emaCloseCrossUp` para crear `crossAboveHMA_v1` con un `sed 's/EMA/HMA/g'`, el reemplazo
ciego rompió la referencia interna al indicador nativo: `key="EMA"` (que SÍ es la clave real de la
EMA) se convirtió en `key="HMA"`, pero la clave real de Hull Moving Average en este install es
`HullMovingAverage`, no `HMA`. El build generó miles de candidatos por segundo y ninguno entró en
el databank: `ERROR BacktestEvaluator ... Cannot find block 'HMA'`, en bucle, silencioso (no
incrementa `Failed`). **Arreglado** editando `deps/blocks.xml` (`key="HullMovingAverage"`,
`mI="HullMovingAverage"`) y reinstalando. Ficha: `knowhow/authoring/cloned-custom-block-native-key.md`.

### 4.2 · MC Retest: NullPointerException transitorio del motor de SQX

Primer `action=start` del paso 13: `MCR 1 Bar` terminó bien (27,96 s) y justo después el proyecto
entero se colgó con `java.lang.NullPointerException` dentro de `fastutil` (colecciones internas de
SQX, nada de esta configuración). `action=status` quedó devolviendo el mismo texto congelado
indefinidamente — sólo `ps` (tiempo de CPU parado) reveló que estaba realmente muerto, no lento. Un
reintento (`stop`+`start`) corrió limpio de principio a fin. Dejó 8 ficheros duplicados `(1)` en el
databank `MCR 1 Bar` que la lectura excluyó correctamente. Ficha:
`knowhow/sqx-drive/mcr-nullpointer-fastutil-transient.md`.

### 4.3 · `sqx.variants.execute` se queda colgado si el custodio ya estaba arrancado

El comando sólo para el worker al terminar **si fue él quien lo arrancó**. Siguiendo el patrón
habitual (arrancar el custodio a mano antes de lanzar), su exportación final se queda esperando
indefinidamente porque los databanks `WFC_OOS1`/`WFC_OOS2` sólo se sincronizan a disco al **parar**
el worker — y nadie lo para. `-project action=status` decía `Project finished` hacía 13 minutos
mientras el proceso Python seguía vivo al 0,9 % de CPU. Solución: pararlo a mano en cuanto aparece
`Project finished` en el log. Ficha: `knowhow/sqx-drive/variants-execute-needs-worker-it-started.md`.

### 4.4 · Corrección propia: fabriqué variantes para 8 madres en vez de 3

El encargo fija el tope de madres en 3 desde el paso 15 en adelante (yo llevaba 8 desde el corte de
aforo del paso 8, válido hasta el 15). Fabriqué el lote completo para las 8 (29.011 variantes) antes
de darme cuenta. Corregido borrando 5 carpetas (~340 MB) y quedándome con las 3 de mayor net profit
IS. Ninguna corrida de SQX se lanzó de más — el coste fue sólo de fabricación (Python, sin SQX) y de
disco temporal. Los databanks `Results`/`OOS` del proyecto SQX seguían con las 8 (no se habían
recortado, sólo el lote de variantes lo estaba); se curaron aparte a las mismas 3 antes de correr los
pasos 21–25, para que toda la cadena posterior al 16.5 lea la misma población.

### 4.5 · Decisión de tiempo: corté el WFC de la 3ª madre a mitad de camino

Con 2 madres ya medidas de punta a punta (1.093 y 1.457 variantes, ~11 min cada una las tres patas
juntas), la 3ª madre tenía 4.999 variantes. Los primeros minutos de su `WFC 1 IS` mostraron un ritmo
que sí escala con el número de variantes (a diferencia de las dos primeras, donde el coste fijo de
cargar los 9 mercados dominaba) — extrapolado, esa sola pata iba a tardar ~19 minutos, y las tres
juntas más de 30. **Decisión mía**: parar ahí (`action=stop` + parar el custodio) y usar el tiempo
restante para cubrir los pasos 21 a 25, que no dependen de que las 3 madres tengan su WFC completo y
cubren terreno nuevo del `WORKFLOW.md` que de otro modo se habría quedado sin tocar. No quedó ningún
resultado de WFC utilizable para esa madre — ni completo ni parcial-legible.

### 4.6 · Tres roces más, cada uno con arreglo de un minuto

- **`exposure.report` exige un export con `Sample type == OOS1`**: apuntarlo al databank `Results`
  (build/IS) da una tabla vacía y un `KeyError` de columnas que no dice «exportaste el databank
  equivocado». Hay que exportar `OOS`, no `Results`. Ficha:
  `knowhow/export/exposure-and-edgecost-input-contracts.md`.
- **`edgeCost.report --strategy "<nombre original>"` falla sobre un lote de `stopgrid`/`variants`**:
  esos lotes renombran cada fichero a su propio esquema (`S00V000`, ...), así que el nombre de la
  madre ya no existe en el export. Se corrigió omitiendo `--strategy` (procesa toda la población).
  Misma ficha que el punto anterior.
- **`sqx.structural.keep` rehusó con «custodio sigue arriba»** con un PID que `ps` identificó como un
  `tail`, no `sqcli` — era el propio `tail -F` de un Monitor de esta sesión, vigilando el log de SQX
  desde antes, que sin querer mantenía abierto un descriptor que el chequeo `worker.holding()`
  interpreta como instalación viva. Se resolvió parando ese Monitor. Ficha:
  `knowhow/sqx-drive/monitor-tail-trips-worker-holding-check.md`.

### 4.7 · Continuación tras el informe — el dueño preguntó por qué el ledger «saltaba» el WFM

El dueño leyó el primer informe y preguntó por qué el ledger parecía decir que todo estaba hecho
menos el WFM. **No era así**: el ledger real (`ledger/*.jsonl` y `python3 -m ledger.report`) no
tenía ninguna entrada para 17, 18 ni 19 — los tres seguían en cero. Lo que probablemente se leyó fue
`WORKFLOW.md`, que marca ✅ si el **módulo existe y funciona**, no si esta corrida lo usó (queda
dicho para que no se repita la confusión).

El dueño pidió arreglarlo y seguir corriendo lo que hiciera falta. Al intentarlo aparecieron dos
problemas reales, uno detrás de otro:

1. **Los datos de las 2 madres con el WFC completo ya no existían.** `sqx.variants.equity` lee los
   `.sqx` en vivo de `databanks/WFC_Build/OOS1/OOS2`, no un export — y los pasos 23 y 24, corridos
   después reutilizando el mismo proyecto, habían vaciado y vuelto a llenar esos mismos tres
   databanks con sus propios lotes. Hubo que **rehacer el WFC de las 2 madres** en el custodio
   (641 s y 657 s, una segunda lectura de `oos2` por madre — asumida, ya autorizada). Ficha:
   `knowhow/sqx-drive/wfc-databank-overwritten-by-next-batch.md`.
2. **Con los datos correctos, `sqx.variants.equity` seguía rehusando**: 8 de 30 bloques
   (segmento×mercado) donde el 100 % de las variantes tenían la curva desalineada de su `NetProfit`
   guardado — el propio código asumía que eso sólo podía ser una lectura equivocada. Diagnosticado a
   fondo: el hueco (447-840 USD) coincidía con el `AvgWin` del propio fichero (640-720 USD) — una
   posición abierta en la última barra, compartida por casi toda la población porque 1.093-1.457
   variantes de UNA madre comparten la misma condición fija y el mismo mercado, y sólo difieren en
   periodos. **Autorizado por el dueño, se corrigió el código** (`sqx/variants/equity.py`): el gate
   fatal ahora exige que el hueco supere 3 veces la mayor operación de ese resultado antes de
   llamarlo lectura equivocada. Verificado: exit 0 y 0 bloques implausibles en las 2 madres tras el
   parche. **Fusionado en `master` el 2026-09-26** (venía de la rama
   `fix/wfc-equity-open-position-boundary`, ya borrada).

Con eso resuelto, se completaron de verdad los pasos que faltaban:

- **17 (WFC)** sobre las 2 madres: `studies.optimisation.wfc.report` — 1.29.55 rho 0,21 `no_fiable`;
  1.28.59 rho 0,25 `indeciso` (el intervalo cruza 0,3, hacen falta más puntos para decidir).
- **18 (CSCV)**: 1.29.55 PBO 15 % con DSR 0,98; 1.28.59 PBO 9 % con DSR 0,98 — probabilidad de
  sobreajuste de backtest moderada-baja en las dos, ninguna alarmante pero ninguna despreciable.
- **18.5 (superficies por mercado)**: 0 de 9 mercados comparten la región del decil superior con el
  mercado principal, en ningún tramo, en ninguna madre — la región buena en USDJPY no es la región
  buena en ningún otro par de la familia.
- **19 (WFM)**, corrida sobre las 3 madres (no depende del WFC de variantes, así que la 3ª —cortada
  en el paso 16.5— sí pudo correr aquí): **0 de 3 predicen**. Dos `blind` (el intervalo de confianza
  de rho cruza cero: reoptimizar en el walk-forward no distingue de azar) y una **`perverse`**
  (1.29.55, rho −0,25 con el intervalo entero negativo: reoptimizar predice **peor** que no
  reoptimizar). 1 de 3 (**1.28.59**; aquí ponía 1.23.51, corregido el 2026-09-26 con `status.parquet`) quedó además marcada `FAILED` por el criterio de área 4×4 de SQX,
  sin borrarse (`DeleteFailedStrategies=false`, como manda la doctrina).
- **20 (lectura conjunta ciega)**, a mano, sobre las 2 madres con las cuatro piezas —
  `studies/closing/blindJoint/` no existe, por diseño, así que esto no es código, es la lectura:

  | madre | 17 (WFC) | 18 (CSCV) | 18.5 (superficies) | 19 (WFM) | veredicto |
  |---|---|---|---|---|---|
  | Strategy 1.29.55 | rho 0,21, `no_fiable` | PBO 15 %, DSR 0,98 | 0/9 | `perverse` (rho −0,25) | **No.** El WFM en `perverse` ya basta para descartar: la única prueba que mide si la búsqueda encontró algo estable dice que reoptimizar activamente perjudica. El WFC y las superficies sólo confirman que no hay nada que perder. |
  | Strategy 1.28.59 | rho 0,25, `indeciso` | PBO 9 %, DSR 0,98 | 0/9 | `blind` (rho −0,08) | **No, pero por una razón más floja.** Nada aquí es catastrófico — el WFC está indeciso, no en contra, y el WFM es ciego, no perverso — pero **nada apoya que haya una región de parámetros estable** tampoco: cuatro pruebas independientes, cuatro «no hay señal». Con el paso 21 ya a favor (`worth_it`, §2), esta sería la candidata a seguir mirando si hubiera que elegir una, pero no hay base para llamarla superviviente. |

  ✅ **Rehecho con el módulo el 2026-09-26** (`studies/closing/blindJoint/`, cap. 56-paso-20): mismo
  veredicto, las dos NO PASAN bajo cualquier lectura que use las piezas (las superficies fallan en las
  dos). Dos matices que la lectura a mano no vio: el `FAILED` de SQX es de 1.28.59, lo que debilita
  que fuera «la candidata a seguir mirando», y las dos madres llevan los mismos cinco parámetros y
  el 98,8 % de sus días de `oos2` con el mismo P&L: son una estrategia, no dos.

  **Lo que yo haría, si tuviera que decidir**: ninguna de las dos estrategias pasa. Coherente con
  crossmarket (0/8), crossTF (0/16) y MC Retest (0/8) más arriba en el embudo — la plantilla
  `crossAboveHMA_v1` no muestra edge transferible en ninguna prueba de robustez independiente que se
  ha corrido en esta población, y el paso 20 es la quinta confirmación, no la primera sospecha.

---

## 5 · Decisiones tomadas por no poder preguntar

1. **Lectura de «crossAboveHMA»**: precio cruzando una sola HMA (calco de `emaCloseCrossUp`), no el
   bloque custom ya existente que cruza una HMA rápida contra una lenta. Documentado en el brief de
   la plantilla.
2. **Periodo de la HMA no fijo**: se generó vía el mecanismo de grupo de un solo ítem
   (`generate="random"` sobre el parámetro, no sobre el bloque), igual que ya hace
   `sqx.templates.build` para cualquier plantilla — no es una lectura nueva, es el comportamiento ya
   establecido en el proyecto (`knowhow/authoring/fixed-native-block-params.md`).
3. **No se aplicó `/curate` tras el crossmarket (paso 10)** aunque el veredicto real fue 0/8: cortar
   ahí habría dejado cero estrategias para ejercitar los pasos 10.5 al 16, que es el objetivo de esta
   corrida (medir el andamiaje, no juzgar la estrategia). Las 8 originales del paso 8 siguieron
   adelante, con el hallazgo real anotado en el embudo.
4. **Corte por net profit (IS), no por net profit OOS**, en el corte de aforo del paso 8: el export
   de métricas de un solo databank no trae la columna OOS emparejada (viene vacía a 0.0 para todas);
   usar IS es consistente con el criterio del 24-09.
5. **Máximo 3 madres desde el paso 16.5**, corrigiendo mi propio error de fabricar para 8 (§4.4).
6. **No se leyeron 17/18/18.5/19 ni el 20**: el encargo exige leerlos juntos y sólo dio tiempo a
   fabricar el insumo del 17 (WFC) sobre 2 de 3 madres, la 3ª cortada por tiempo (§4.5). No se ha
   mirado ningún resultado de WFC todavía, así que la puerta ciega del paso 20 sigue intacta.
7. **Priorizar amplitud sobre profundidad en el 16.5**: en vez de esperar a que la 3ª madre terminara
   su WFC (habría consumido el resto del tiempo disponible), corté ahí y usé el tiempo en los pasos
   21–25, que no se habían tocado. Decisión de gestión del tiempo, no de la maquinaria.
8. **Step 23 (estructural) y 24 (ATR) corridos sobre una sola madre de las tres** donde el manual lo
   permite (24 es explícitamente «una estrategia, no una población») y sobre las 3 en el 23 —
   suficiente para ejercitar el mecanismo sin gastar el tiempo restante en repetirlo por madre.
9. **Paso 25 corrido sin `--strategy`**, sobre toda la población del lote de ATR, en vez de elegir a
   mano qué percentil/X es «la versión que se operaría» — esa elección es del dueño, no mía.

## 6 · Otros hallazgos, sin categoría propia

- `gate.harvest` (paso 8) arranca el **conductor** de refilón para una consulta corta, aunque toda
  la corrida vive en el custodio — coherente con «conductor para autoría, queries y exports; short
  jobs», pero vale la pena saber que un paso "sólo custodio" puede tocar brevemente el otro worker.
- `sqx.curate.apply_verdict` sobre `OOS` con un `verdict.csv` calculado sobre `Results` puede
  **rehusar aplicar nada** si alguna de las estrategias tiene una identidad IS/OOS distinta (3 de 200
  en esta corrida) — hay que recalcular el `identity` contra el databank de destino.
  `knowhow/databanks/curate-verdict-identity-per-databank.md`.
- El WFC gasta `oos2` **por madre × por pata**, no una vez por proyecto: cada `sqx.variants.execute`
  sobre una madre nueva vuelve a correr `WFC 3 OOS2`. Con 3 madres, `oos2` se ha mirado hasta 4 veces
  en esta sola corrida (2 completas del 16.5, más la del paso 24 sobre otra madre) — coherente con la
  doctrina (una mirada por variante fabricada, no por proyecto), pero el volumen de "miradas" a
  `oos2` que registra el ledger crece con el número de madres y de pasos que lo piden.
- **El coste fijo de un WFC (9 mercados) domina hasta lotes bastante grandes**: 12 variantes tardan
  132 s, 22 tardan 99 s (¡menos!) y 1.093–1.457 tardan ~656 s cada una — la varianza no es monótona
  con el tamaño del lote a estas escalas, así que "más variantes por corrida" probablemente sale más
  barato por variante hasta un punto que esta corrida no llegó a localizar con precisión.
- **El paso 23 (estructural) trae su propio control de sanidad y lo falló**: «la madre reconstruida
  reproduce un resultado guardado» dio `no` (846 operaciones reconstruidas contra 423 guardadas en
  el `.sqx` original, tramo `build`). El propio estudio lo marca y no bloquea nada — es una lectura,
  no un filtro — pero es una discrepancia real que alguien con más tiempo debería mirar antes de
  fiarse de las ablaciones del paso 23 sobre esta plantilla.
- **El paso 24 dio una lectura limpia**: el stop en X·ATR(20) para los 4 percentiles por defecto
  (80/85/90/95) es estable («meseta») en la ventana IS, y 3 de los 4 transfieren a `oos2` (el
  percentil 80 no). Con las salvedades de costes provisionales y de una sola estrategia de prueba,
  es la única lectura de calidad completa que deja esta corrida — el resto son 0/8, 0/16, 0/8 fail o
  "no leído todavía".

---

## 7 · «Por dónde empezar» — para el agente que optimice después

**No se ha optimizado nada en esta corrida — esto es la lista de dónde mirar primero, con el
comando exacto y sobre qué datos, en orden de impacto esperado.**

1. **MCR 7 OHLC + MCR 8 Stress son el 67 % del tiempo de SQX del paso 13** (1.740 de 2.580 s). Antes
   de tocar nada, perfilar qué hace cada uno con `--hotspots` no aplica aquí (es SQX, no Python) —
   pero si se decide reducir el catálogo de perturbaciones para una corrida de humo, éstas son las
   dos a bajar de `simulations` primero (`assets/_build.yaml`, bloque `mc_retest:`), midiendo con
   `python3 -m perf.catalogue --only mc_retest` si algún día ese target se registra ahí.
2. **`crossmarket.report` es el estudio de Python más caro por CPU-tiempo (555 s en 28,7 s de
   pared)**: `python3 -m perf.catalogue --hotspots crossmarket` (si se registra como target) o un
   `cProfile` directo sobre `studies/transfer/crossmarket/report.py --project
   USDJPY_workflow_profiling_v1 --databank "Retest Markets - Family" --asset USDJPY` — con los datos
   ya exportados en `~/Desktop/AlgoData/raw/USDJPY_workflow_profiling_v1/Retest_Markets_-_Family/2026-09-26/`,
   no hace falta volver a tocar SQX para repetir la medida.
3. **El WFC (paso 16.5/17) es el hueco de datos más grande que deja esta corrida**: con 2 de 3 madres
   medidas, la pata `WFC 1 IS` cuesta ~350 s **con independencia del número de variantes** hasta que
   la población crece lo bastante (la madre de 4.999 sí empezó a escalar) — merece la pena separar,
   con un profiler, cuánto de esos 350 s es cargar los 9 mercados adicionales (fijo) y cuánto es
   backtestear cada variante (variable), porque si el fijo domina, fabricar variantes en lotes más
   grandes por corrida sale más barato por variante.
4. **`sqx.variants.execute` necesita gestionar su propio arranque/parada del worker** (§4.3): antes
   de cualquier otra cosa, decidir con el dueño si se cambia el patrón operativo (nunca arrancar el
   custodio a mano antes de `execute`) o se arregla el propio comando para detectar `Project
   finished` y parar el worker aunque no lo arrancara él — esto no es una optimización de rendimiento
   pero cuesta minutos reales cada vez que alguien lo repite sin saberlo.
5. **La memoria nunca se ha acercado a un límite** en esta corrida (pico más alto 2,17 GB, máquina de
   125 GB) — no hay nada urgente que optimizar en RAM con esta población. Si se corre con una
   población de miles de madres (en vez de 3), revisar `snoopingScreen.report` y `export_retest`
   primero: son los dos picos más altos y ambos escalan con el número de trades exportados.
6. **17, 18, 18.5, 19 y 20 ya están medidos** (§4.7) — lo único que falta del WFC es la 3ª madre
   (1.23.51, cortada en el 16.5). Antes de rehacerla, **decidir con el dueño**: el ledger ya ha
   registrado `oos2` varias veces para las otras dos madres (WFC completo + su rehecho tras el
   borrado accidental, más el paso 24 sobre una tercera), así que una mirada más gasta otra vez una
   ventana que la doctrina trata como de un solo uso por variante.
6b. **`sqx.variants.equity` necesita gestionarse con cuidado si el proyecto se reutiliza para otra
   cosa** (§4.7, `knowhow/sqx-drive/wfc-databank-overwritten-by-next-batch.md`): corre `equity` +
   `collect` inmediatamente después de cada `execute`, antes de tocar los mismos databanks con
   structural, ATR o cualquier otro lote — si no, los `.sqx` de ese lote desaparecen sin aviso.
7. **El control de reconstrucción fallido del paso 23 (§6) merece una mirada antes de fiarse de sus
   ablaciones**: comparar a mano, sobre la misma madre, qué exporta `sqx.export.export_retest` de su
   `.sqx` original contra lo que reconstruye `sqx.structural.make` — 846 contra 423 operaciones es
   una diferencia de casi el doble, no un redondeo.
8. **El paso 25 necesita que alguien elija la X operativa** antes de que su lectura signifique algo:
   esta corrida la corrió sobre el lote entero (22 variantes) porque elegir una es decisión del
   dueño, no del andamiaje — pero el número final que se reporte debe ser sobre esa única variante,
   no sobre las 22.

---

## 8 · Dónde está todo

- **Datos crudos:** `~/Desktop/AlgoData/profiling/workflow-2026-09-26/` — `steps.csv` (una fila por
  paso), `run.log` (pulsos), `mem-samples/` (intentos de muestreo del árbol completo — ver
  limitación abajo).
- **Este informe:** `docs/AgentPDFs/profiling-workflow-2026-09-26.md`, fusionado en `master`
  el 2026-09-26.
- **Fichas nuevas en `knowhow/`:**
  `authoring/cloned-custom-block-native-key.md`,
  `sqx-drive/mcr-nullpointer-fastutil-transient.md`,
  `sqx-drive/variants-execute-needs-worker-it-started.md`,
  `sqx-drive/monitor-tail-trips-worker-holding-check.md`,
  `sqx-drive/wfc-databank-overwritten-by-next-batch.md`,
  `databanks/curate-verdict-identity-per-databank.md`,
  `export/exposure-and-edgecost-input-contracts.md`.
- **Plantilla nueva:** `~/Desktop/AlgoData/templates/library/crossAboveHMA_v1/`.
- **Arreglo de código:** `sqx/variants/equity.py`, fusionado en `master` el 2026-09-26.

### Resumen de hasta dónde llegó la cadena

**Los 25 pasos se han tocado todos.** El primer informe cerraba en el 16.5 (más 21-25 adelantados);
tras la pregunta del dueño sobre el ledger, esta continuación completó 17, 18, 18.5, 19 y 20 sobre
las 2-3 madres que lo permitían, arreglando por el camino un bug real en `sqx/variants/equity.py`
(§4.7). De los pasos que dieron un veredicto real (no un corte artificial de aforo):
**0/8 crossmarket, 0/16 crossTF, 0/8 MC Retest, 3/3 exposición, 0/3 WFM predicen, 0/2 pasan la
lectura conjunta del paso 20, 4/4 percentiles ATR estables** — la plantilla `crossAboveHMA_v1` no
muestra edge transferible en ninguna prueba de robustez independiente corrida en esta población.
Coherente de punta a punta: cinco pruebas distintas, cinco «no hay señal».

### Limitación de medición, dicha sin adornos

El script ad hoc que se preparó para muestrear el RSS de todo el árbol de procesos (el criterio de
`perf/`, no `ru_maxrss` del padre) dio números absurdos la primera vez que se probó (cientos de GB)
al toparse con el JVM del worker recién arrancado, y no se depuró más por tiempo — los números de
memoria de este informe son el **pico del proceso principal de Python** (`/usr/bin/time -v`), no del
árbol completo. Para el JVM de SQX no se ha muestreado memoria en absoluto: sólo tiempo de pared por
tarea, leído del propio log de SQX. Quien optimice memoria de verdad necesita arreglar o sustituir
ese muestreo antes de fiarse de un pico.
