# 74 — Listo el domingo: la cadena entera, de la idea a la cartera, en las dos máquinas

## Estado (cada sesión actualiza su fila)

| # | frente | sesión | recurso | estado | espera |
|---|---|---|---|---|---|
| 1 | V del 50: corrida entera con el paso 8 vigente | 18 | custodio leaseWeb | ✅ jue 21:30: paso 8 verificado en `Test_USATEC_H1_breakoutL_v8b_leaseWeb` (B=2, línea 2,576, 10.000 → 4 medoides); la cadena llegó al 18 y paró en el 18.5 por fichas sin `price_rounding` (medidas y arregladas esta noche); 4 + 2 supervivientes en el almacén | — |
| 2 | Z1 del 50 y resto del 49 (ledger, autopilot, umbrales al ledger, higiene de `criteria.yaml`) | 18 | Python | ✅ Z1/M del 50 (5c8055d), 49: `--calib` fuera, umbrales al ledger, `ledger/blind` arreglado (aaa03d6); la parte de `criteria.yaml` (paso 16 + higiene) va en el commit de la #93 de 07; mcRetest P14-7 → pregunta S3 | 1 |
| 3 | #93: C2-C11 del 72 en `criteria.yaml` y `assets/_study.yaml` | 07 | Python | pendiente | 2 commiteado, y el dueño confirma a 07 |
| 4 | Resto del F3 del 56 (`entryQuality` lee el replay tier 2 con stop) | 07 | Python | **hecho** (ya estaba: bitácora del 56, 2026-10-14; `tests/test_replay.py` + `test_entry_delay_replay.py` 10/10, 2026-10-15) | — |
| 5 | 66 frentes 1, 2, 4, 5, 9, 10 (sin SQX; sin medir mientras corra SQX) | 95 | Python | hecho jue noche: casi todo ya estaba construido; quedan las mediciones con la máquina libre (bitácora del 66) | P10, D27 |
| 6 | #96 (L4): silueta en el CSCV · #104 (F8a/b) | 95 | Python | hecho jue noche: #96 cerrada (fila en la lectura del CSCV), #104 F8a/b (F8c tras la corrida limpia), #119 cerrada | — |
| 7 | 66 frentes 6-7 (SQX vivo) · #112 (núcleos) · mediciones aplazadas del 66 | 95 | conductor y custodio | pendiente | 1 terminado |
| 8 | Corrida real en gorilla (celda del dueño) → `bin/remote.sh gorilla collect` → paso 26 en leaseWeb (#123, 72 D) | 95 | gorilla, luego MT5 | build 10.000 hecho; **paso 8 falló: EURUSD sin `price_rounding`** (sólo 6 activos medidos). Medida `engines.market.rounding` en curso → ficha → `run` | medida |
| 9 | Si V falla: arreglo con su test y V otra vez desde cero (regla de la corrida limpia) | 18 | custodio | ✅ 1.ª V cayó en el 8 (`List index overflow`, d52908d) → 2.ª desde cero; su parada en el 18.5 → `rollout_hour` sin comillas en 4 fichas (1fcb33b) y `price_rounding` de DJ30/UK100/HK50/AUS200/UKOIL/USOIL (dc6eede, 4fe279b). No hay 3.ª V: la próxima corrida entera (GBPJPY u otra) hace de prueba limpia | 1 |
| 10 | Paso 26 con una superviviente real (55 C) → su fila en el pool | 95 | conductor, MT5 | pendiente | supervivientes de 1 u 8 |
| 11 | Motor de carteras con un pool real (#87; M0 ya filtra por costes actuales) | 07 | Python | pendiente | 10 |
| 12 | Ensayo general: dos celdas a la vez (leaseWeb y gorilla), del director a la cartera, sin manos | 95 + 18 | todo | sábado | 2, 3, 10 |
| 13 | Campaña desatendida toda la noche del sábado en las dos máquinas | 95 | todo | sábado noche | 12 |
| 14 | Hoja final para el dueño: qué está listo, qué no, cómo lanza un agente | 95 | — | domingo 8:00 | 13 |

## Bitácora

- 2026-10-15 (jueves noche) — escrito por algoproject-95 a petición del dueño: «el domingo por la
  mañana quiero el proyecto terminado para empezar a usar agentes para lanzar workflows,
  desarrollar estrategias y testearlas». Dueño: D1 = la cadena entera probada una vez en las dos
  máquinas, más la campaña corriendo sola; D2 = lo aparcado sigue aparcado (53, 57, 58, 60, 67,
  56 F2/F4/F5, 69); D4 = «lo que sea, pero termina a tiempo»; D5 = sin Council. Reparto acordado
  con 18 y 07 por mensajes. N3: commit y push por frente con pathspec y `checks.py` verde. N4: una
  ambigüedad para ese frente; la pregunta va a «Preguntas para la mañana» y se sigue con otro.
- 2026-10-15 20:40 — dueño: «cuanto más rápido mejor», «elige, pero dale». Reparto: 18 = V, criteria.yaml y 49, ensayo en leaseWeb; 95 = gorilla, D27, 66 frentes 6-7, collect, paso 26, celdas del viernes, campaña; 07 = ya sin esperar: F3 del 56, prueba en seco de la campaña, preparar #87 con un pool archivado; luego #93 y #87 real. Celdas del viernes (elegidas por 95): leaseWeb `Trade_GBPJPY_H1_momentumL_leaseWeb` (simple, largo, `momentum_base_v3`), gorilla `Trade_AUDUSD_H1_reversionL_gorilla` (simple, largo, `reversion_base_v3`), 10.000 estrategias y 30 min cada una. Hecho esta noche: #96, #104, #119, P10, D27 fase 1, dos fallos de gorilla (`remote.sh`, `live._log`).
- 2026-10-15 21:05 — gorilla `Trade_EURUSD_M30_reversionL_gorilla`: build 0 → 10.000 en 35 min; paso 8 falla: la ficha de EURUSD no tiene `price_rounding` (#120: 22 fichas sin medir). Bloquea también GBPJPY y AUDUSD (celdas del viernes) y la campaña fuera de XAUUSD, USA500, DAX40, NIKKEI225, USATEC y USDJPY. 95: medida reutilizable sobre las operaciones del propio build, y EURUSD medido con el build de gorilla. Pregunta R1 abajo.
- 2026-10-15 21:45 — 95: la celda de gorilla del viernes pasa de AUDUSD H1 a **`Trade_XAUUSD_M15_momentumL_gorilla`** (simple, largo, `momentum_base_v3`): `core.assets AUDUSD` avisa de que su feed sólo es estable desde 2025 (construcción 2008 = calidad B), y XAUUSD ya tiene `price_rounding`. Gorilla no tiene el proyecto de herramientas ni el snippet `AlgoBank` compilado (`sqx.snippets.install --check`): cada volcado cae a la ruta lenta; se instala al acabar EURUSD, antes de la celda siguiente.
- 2026-10-15 22:00 — el dueño encarga a 07 dos celdas de campaña en el custodio de leaseWeb (6-7 h): 95 le cede el custodio y GBPJPY H1 se aparta (después, o a gorilla tras XAUUSD M15). El 18.5 se niega con cualquier mercado de familia o estructural sin `price_rounding`: 18 mide índices y energías (DJ30, UK100, HK50, AUS200, oils) y 95 forex y metales, desde el lote del 18.5 del EURUSD de gorilla.
- 2026-10-15 23:10 — gorilla EURUSD M30, tras medir los forex (12 fichas + GBPJPY), arreglar el medio tick del repreciador (#124) e instalar los snippets: pasa 18.5 (1 madre leída) y 19 (WFM, 874 s) y se para en el **19.5**: `PermissionError: el paso 19.5 no puede mirar oos2 de EURUSD: reservado para WFC, CSCV, MarketSurfaces, WFM, BlindJoint, ATRStop` (`assets/_policy.yaml`, del dueño). Toda corrida del autopiloto se parará ahí. Pregunta R2.
- 2026-10-15 23:20 — 95: el 19.5 NO es la política: `oos2Reading` se presenta al ledger como paso 19 (`inputs.py:16`, a propósito), pero el juez firma su fila como 19.5 (`judge.ledger_row` → `gate.allow` sin el 19.5 en `STEPS`). Fallo de código de 18 (autopilot/ledger), pasado con el arreglo propuesto; R2 retirada.
- 2026-10-16 00:40 — gorilla con el arreglo del 19.5 de 18 (ca27380): `Trade_EURUSD_M30_reversionL_gorilla` FIN, sin superviviente (la lectura de oos2 del 19.5 la cortó: resultado). `Trade_XAUUSD_M15_momentumL_gorilla`: 10.000 → 2 (paso 8) → 1 (10, 12) → 19.5 pasa (1 → 1, guardada para fondeo en `kept/`), y **falla en el paso 20**: BlindJoint «la curva reconstruida de las madres no reproduce la de SQX (83 % de los días, hace falta 99 %)»; el 18.5 ya había saltado esa madre por descuadre 0,60 (oro, #120/#121). Diagnóstico en curso (Sonnet). Gorilla sigue con `Trade_GBPJPY_H1_momentumL_gorilla`.

- 2026-10-16 02:30 — gorilla `Trade_GBPJPY_H1_momentumL_gorilla`: **FIN sin fallos, del build al 20** (10.000 → 4 en el paso 8 → 4 en el 19 → **1 tras el 19.5 y el 20**); collect hecho (`store/GBPJPY_H1_simple_long_gorilla`, ledger `_gorilla`), lista para el paso 26. XAUUSD M15: arreglado `closecurve.measured` (c85645c); el 20 sigue a 98,7 % en oos1 por la precisión del export → pregunta R4. Gorilla sigue con `Trade_USDJPY_H1_momentumL_gorilla` (simple, largo, `momentum_base_v3`, 10.000 / 30 min).
- 2026-10-16 04:18 — gorilla `Trade_USDJPY_H1_momentumL_gorilla`: **FIN sin fallos, del build al 20**, 10.000 → 4 en el paso 8 → **4 tras el 19.5 y el 20**; collect hecho. Gorilla sigue con `Trade_EURUSD_H1_momentumL_gorilla` (simple, largo, `momentum_base_v3`).

## Reglas de la noche

- Nada pesado de CPU junto a una corrida de SQX (regla 19). El custodio tiene un solo dueño a la vez.
- Cada sesión orquesta y reparte cada frente a un subagente Sonnet. Commit sólo de sus ficheros
  (`git commit -- <ficheros>`; con un fichero compartido, índice temporal).
- Ficheros de 18 esta noche: `ledger/`, `pipeline/autopilot/` (con `criteria.yaml`),
  `verdict/gates.py`, `ledger/thresholds.yaml`, encargos 49/50/53. Nadie más los toca.
- `criteria.yaml` no se edita mientras una corrida lo lee.

## Preguntas para la mañana

| código | frente | qué se decide | lecturas | recomendación |
|---|---|---|---|---|
| G1 | 8 | celda de la corrida de gorilla | **contestada: B** (EURUSD M30 largos reversión, `Trade_EURUSD_M30_reversionL_gorilla`) | — |
| P10 ✅ B | 5 | dos objetivos de `perf/inputs/construct.py` apuntan a datos borrados | A primer miembro + cosecha USDJPY (no existe) · B cosecha XAUUSD `Test_XAUUSD_H1_ruptura_wtc3` · C retirarlos | B |
| D27 ✅ A | 5 | ledger único del 66 | el diseño A/B/C está escrito en el 66, sección «D27 · Diseño…» | sin recomendación aquí; fuera de la ruta crítica |
| K1 ✅ A | 11 | cómo se dimensiona en cartera una estrategia sin stop (OPEN #113 (1); el M3 para con «sin stop del paso 24») | A pérdida diaria flotante de la firma + tope de exposición conjunta · B stop ATR sintético sólo para el tamaño · C 1 lote fijo (rompe límites en 50-77 % de cuentas) | A |
| K2 ✅ A | 11 | `oos2` se gasta una vez por pool: ¿quién lo lee? | A sólo la cartera de fondeo · B dos pools · C la real primero | A |
| K3 | 11 | de qué proyecto salen las supervivientes del pool del viernes | nombre del proyecto, o «las de la corrida V del 50» | — |
| K1a | 11 | forma del lote (hecho A en `4f8241a`) | A la gestión ATR de SQX escalada por una constante: el lote varía con el ATR · B lote fijo por miembro = cuota del límite diario / peor pérdida por lote (reconstruye curvas por lote, EA con `FixedSize`) | A, salvo que el EA de MT5 no pueda llevar `ATRRiskBasedSizingFixedRisk` |
| K1b | 11 | qué es el «peor día» (hecho A) | A suma del MAE de las operaciones que cierran ese día, reloj del feed (barato, aproximado) · B mínimo intradía exacto del flotante en barras M5, reloj de cada firma (dimensiona por firma) | A; B si las quiebras simuladas no cuadran |
| K1c | 11 | unidad de la rejilla de riesgo (hecho A) | A fracción del saldo inicial (0,001-0,01, la de hoy) · B cuota del límite diario de cada plan | A |
| W1 ✅ fuera | 7 | la celda interrumpida `squeezeBBLong XAUUSD H1` es un test de 15 min y `following()` la corre la primera | A dejar que termine · B marcarla hecha/fallida en el ledger | B |
| W2 ✅ B (`c5ca165`) | 7 | `claude -p` con límite de uso: el bucle ahora para (`7f6a293`) | A parar · B dormir 30 min y reintentar, con tope | B si va desatendido |
| W3 ✅ B | 7 | la campaña no retira sus `Trade_` (1,1 GB el de NIKKEI) y SQX los carga al arrancar | A dejarlos · B retirarlos tras `keep` | A un fin de semana, B si dura semanas |
| W4 ✅ fuera (`dropped_templates`) | 7 | `squeezeBBLong` falla en 16.5 (`not variables of this strategy: ['SqueezeBB']`, la causa sigue) | A dejarla en la cola · B al final | B |
| W5 ✅ No | 7 | antes de lanzar: existe `AlgoData/campaign/STOP` (desde 07-10), la cola está vacía y nada relanza el bucle si muere | `run --go` quita el STOP; `plan --queue N` encola; ¿supervisor (cron) sí/no? | encolar y lanzar a mano; supervisor no hasta ver una noche limpia |
| W6 ✅ A, N = 2 | 7 | lanzar la campaña esta noche | lanzada 22:05: `Trade_EURUSD_M30_cciPercLong`, `Trade_USDJPY_H1_cciPercLong_withExit` | — |
| W7 ✅ B | 7 | 21 activos sin `price_rounding` fuera de la campaña (`ad41f58`) | se miden la semana que viene; si R1 = A el filtro se borra | — |
| R4 | 20 (oro) | arreglado `closecurve.measured` (c85645c: build 90→99,7 %, oos1 78→98,7 % de días a 1 USD). Los 16 días de 1232 que aún fallan en oos1 son la precisión del export: el oro va con `price_rounding: none`, SQX ejecuta a medio céntimo y el `Open price` exportado lleva 2 decimales → ±0,5 USD/lote, que con 2–4 lotes supera `TOLERANCE = 1.0` (`blindJoint/inputs.py:26`). Hacen falta ≤ 12 fallos | A tolerancia por día = max(1 USD, medio decimal del export × valor de punto × lotes abiertos): sólo absorbe lo que el export no puede decir (oos1 → 99,9 %) · B subir el 1,0 a 2,0 fijo · C dejarlo: el oro no pasa del 20 | A |
| R3 | 8 (oro) | el 18.5 saltó la madre de XAUUSD M15 por descuadre 0,60, y build y oos1 reprecian a 0 %: el descuadre está casi seguro en **oos2** (`wfc/one.py:236-244` toma el máximo por tramo, oos2 incluido), donde nadie ha medido `price_rounding` (la ficha tiene un solo valor, medido en build/oos1). Un agente no puede mirar oos2 | A el dueño mide a mano `rounding.measure('XAUUSD', <operaciones oos2 de la madre>, 'oos2', timeframe='M15')` y, si gana otro modo, `price_rounding` pasa a ser por tramo · B el descuadre del 18.5 sólo cuenta build y oos1 · C dejarlo: el oro salta el 18.5 | A |
| R1 | 8, 12, 13 | un activo sin `price_rounding` en su primera corrida | A el paso 8 lo mide solo sobre las operaciones del build y escribe la ficha (con `why`), y sigue · B se para, se mide a mano y `run` · C la campaña sólo elige activos ya medidos | A: sin ella la campaña del sábado se para en cada activo nuevo |
| S1 | 2 | ¿segundo sello de `criteria.yaml`? El sello es del 12-10; el α 0,01 del 15-10 y el commit de la #93 + 49 cuentan como ediciones en cada celda juzgada después (`edits_since_seal`) | A sellar de nuevo tras la #93 (el contador vuelve a 0 desde ahí) · B dejar el sello del 12-10 y que cuenten | A: las dos ediciones son del dueño y ya están medidas |
| S2 | 9 | `price_rounding` indistinguible (tick y none ≈ 0 %): DJ30, UK100, HK50 (18) y EURAUD, EURGBP, XAGUSD, XCUUSD (95) escritos `tick` por el precedente de USATEC/NIKKEI225 | A vale · B dejarlos sin ficha hasta un lote que distinga | A: con 0 % por los dos lados el reprecio da lo mismo |
| S3 | 2 | 49 P14-7: borrar los cortes viejos de mcRetest (`verdict/gates.py`) deja sin veredicto a `scoring.py` (STRONG…FAIL), los vetos del informe y las columnas de la ventana | A el paso 14 se queda sólo con columnas: se borra el veredicto entero · B se conserva el veredicto como columna informativa | B: es lo que el 65 hizo con el 14 (columnas) sin perder la lectura |
| S4 | 2 | los pasos sin regla (11.5, 16, 16.5) no dejan fila en el ledger (`judge.py:242` sale antes) | A que dejen fila (con 0 cortes) · B así está bien | A: el registro completo era el punto 1.3 del 49 |

## Informe de las 5:40 (viernes 2026-10-16, hora del servidor, UTC)

Orden del dueño (jue 21:30): toda la noche buscando soluciones, testeando, arreglando y commiteando,
las tres instancias; a las 5:40 cada una dice qué ha hecho y sus siguientes pasos del día. Cada
sesión rellena sólo su sección antes de las 5:35; 95 las junta para el dueño.

### Informe de las 5:40 — algoproject-95

| qué | estado | commit |
|---|---|---|
| gorilla, 4 celdas | EURUSD M30 reversión: FIN sin superviviente · XAUUSD M15 momentum: llega al 20 y falla (R4) · **GBPJPY H1 momentum: FIN, 1 superviviente** · **USDJPY H1 momentum: FIN, 4 supervivientes** · EURUSD H1 momentum en el 16.5 | `e8b5065`, `d2acffd`, `9d2d7ef` |
| collect | 5 supervivientes reales de gorilla en el almacén de leaseWeb (`_gorilla`), listas para el 26 | — |
| `price_rounding` | medida reutilizable `engines.market.rounding.measure` (segmento obligatorio); 23 fichas medidas (EURUSD, 8 forex, AUDNZD, GBPJPY, AUDUSD, EURAUD, EURGBP, XAGUSD, XCUUSD…) | `592926c`, `503ccdd`, `eb74726`, `abcdfba` |
| repreciador | medio tick hacia arriba como SQX (np.round iba al par): media población descuadrada en GBPJPY/AUDUSD → 100 % a 0,01 USD; #124 cerrada | `3341069`, `4fd652d` |
| paso 20 | `closecurve.measured` descarta las operaciones del día con swap (comisión del oro 6,1/8,2 → 5,0): build 90 → 99,7 %, oos1 78 → 98,7 % | `c85645c` |
| tests y limpieza | `test_real_run` con cierres reales; `stop_percentile` fuera; skill workflow con `core.assetmarkets` | `fcc1056`, `56cf3d0`, `b22805e` |

**Siguientes pasos del día (viernes):**
1. R4 → si A, tolerancia por precisión del export en `blindJoint/inputs.py` con test y `run` de XAUUSD M15 desde el 20.
2. Paso 26 de las 5 supervivientes de gorilla en el conductor de leaseWeb, con tus cuatro parámetros y el conductor libre.
3. D27 fase 2 (ledger por servidor, `ALGO_SERVER`) en cuanto acabe la campaña de 07.
4. Gorilla: leer EURUSD H1 y seguir con celdas de fichas medidas (o la propuesta del director, si la vetas).
5. Con el custodio libre: mediciones del 66 (frentes 6-7) y #112.

### Informe de las 5:40 — algoproject-18

| qué | estado | commit |
|---|---|---|
| V del 50 (paso 8 vigente) | ✅ verificada en `Test_USATEC_H1_breakoutL_v8b_leaseWeb`: B=2, línea 2,576, z_mono máx. 2,84, 10.000 → 7.356 → 6 → 4 medoides; la cadena llegó al 18; 4 + 2 supervivientes en el almacén; proyectos retirados, custodio cedido a 07 | `5c8055d` |
| 1.ª V cayó en el 8: `List index overflow` | `distribuciones.parquet` en grupos de 1.000 filas; `facts` lee primero `strategy`; ficha de knowhow y fila en `/workflow` | `d52908d`, `cad155e` |
| 2.ª V paró en el 18.5 (fichas sin `price_rounding`) | causa de fondo: `rollout_hour: 23:00` sin comillas = entero 1380 en UK100/HK50/AUS200/XCUUSD → entrecomillado y `core.assetdata.load` se niega a uno sin comillas (test); medidos UKOIL, USOIL, DJ30, UK100, HK50 tick y AUS200 none | `1fcb33b`, `dc6eede`, `4fe279b` |
| 49 | `--calib` y `calib_rows` fuera; umbrales de crossmarket/crossTF/spp a `ledger/thresholds.yaml`; `ledger/blind` lee el CSCV; T-2 `ALGO_OOS2_PIN`; SPP media/sd/media−sd en `verdict.csv`; tramos gastados en `campaign plan`. Parche de `criteria.yaml` (paso 16 + higiene) entregado a 07 para su commit de la #93 | `aaa03d6`, `a4c2f71`, `9fe9bf3` |
| 50 Z1 y frente 4 M | la documentación de la puerta (WORKFLOW, especificación, README, skill, glosario, manual 03-05) describe el paso 8 vigente | `5c8055d` |
| OPEN #118 (a) | el builder se niega si la ventana de una tarea se sale de su tramo (`refuse_off_segment`); probado sin conexión con builds `--workflow` de USATEC H1, GBPJPY H1, EURUSD M30 y XAUUSD H1 | `94be9dd` |
| paso 19.5 bajo `ALGO_AUTONOMOUS` | toda corrida moría en el 19.5 (`PermissionError`, gorilla EURUSD): la fila del corte firmaba 19.5 y la reserva de oos2 sólo conoce el 19 con que firma su estudio → `ledger.gate.READS_AS = {19.5: 19}`, test | `ca27380` |
| `test_false_positives` | suelo de potencia del R3 a 10 de 40 con α 0,01 | `e97c475` |
| encargos | 52 y 62 borrados (hechos); 49, 50 y 53 reescritos con las respuestas; #91 cerrada | — |

**Siguientes pasos del día (viernes):**
1. Cuando aterrice el commit de la #93 de 07: marcar hecha la fila 1.6 del 49 y, si S1 = A, sellar de nuevo `criteria.yaml`.
2. Respuestas S1-S4 → aplicarlas (S3 y S4 son código en `verdict/gates.py` y `ledger/judge.py`, ficheros míos).
3. Fila 12 del 74 (ensayo del sábado en leaseWeb): en cuanto el custodio quede libre de la campaña de 07, una celda del director a la cartera sin manos.
4. Paso 20 (gorilla XAUUSD M15): la guarda de la curva (83 % < 99 %) falla antes de gastar la mirada de oos2; se relanza con `run` desde el 20 cuando 95 arregle el descuadre M15 (#120/#121). Saltar la madre en el 20 como en el 18.5 sería un filtro nuevo: pregunta del dueño, recomiendo fallar.
5. Pendiente con la máquina libre: frente 5 del 50 (receta IS, Opus), calibraciones 12 y 16 del 49 (esperan al 53, aparcado).

### Informe de las 5:40 — algoproject-07

| qué | estado | commit |
|---|---|---|
| Motor de carteras de punta a punta sobre `Test_nikkei_ref` (M0-F5, < 90 s por paso) | hecho; secuencia «Con supervivientes reales» en el README | `2d6f031` |
| Prueba en seco de la campaña: una celda real ya no hereda el modo test; `claude -p` fallido no aparta la celda | hecho, tests verdes | `7f6a293` |
| W3 B (retirar el `Trade_` terminado) · squeezeBB fuera (`dropped_templates`) | hecho | `f5636b0` |
| La campaña sólo ofrece activos con `price_rounding` (filtro; se borra si R1 = A) | hecho | `ad41f58` |
| W2 B: `claude -p` caído espera 30 min y reintenta (6 veces) | hecho, test | `c5ca165` |
| K1 A: la cartera dimensiona sin stop (factor = 1 / peor día de MAE en build; tope `open_risk_cap`) | hecho; sin correr el motor entero sobre supervivientes reales | `4f8241a` |
| Campaña lanzada 22:05: `Trade_EURUSD_M30_cciPercLong`, luego `Trade_USDJPY_H1_cciPercLong_withExit` | **EURUSD falló dos veces en el 6+7** («el disco se paró 120 s sin igualar la memoria», 00:54 y 04:04); va por su 3.er intento (`--restart`, build desde 04:04) | — |
| #93 (C2-C11) + parche del 49 de 18 en `criteria.yaml` | pendiente: un solo commit cuando acabe la campaña | — |

**Custodio de leaseWeb: NO está libre.** El bucle (PID 2310663) sigue con el 3.er intento de EURUSD; el build acaba hacia las 07:05 y después vienen los pasos 8-21; luego la celda USDJPY (~6-7 h).

**Siguientes pasos del día**
1. Diagnosticar el fallo del 6+7 (guardado del databank tras un build de 10.000) antes de que el 3.er intento caiga igual; si es de código, arreglarlo y relanzar la celda con `run`.
2. Al acabar el bucle: la #93 + el parche del 49 en un único commit; quitar `stop_x` de `pipeline/campaign/shelf.py`.
3. Dueño: **K3** (de qué proyecto sale el pool de la cartera), **K1a-c** (ya en A), **R1** (si A, se borra el filtro de `price_rounding`), **R2**.
