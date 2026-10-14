# Qué mirar en los runs hasta el paso 12

Lista de trabajo para el agente que hará los runs (tú). Cada run termina en el paso 12 inclusive (6, 7, 8, 9, 10, 10.5, 11, 11.5, 11.7, 12). Aquí está QUÉ mirar y anotar, no cómo operar SQX ni el plan de runs.

Origen: `docs/AgentPDFs/pendientes-y-decisiones-2026-10-08.md` (el «catálogo»), recortado a los pasos 6-12 más lo transversal que los condiciona. Los pasos 7 y 9 no tienen ítems propios en el catálogo (el 9 no hace nada: ver P10-8a).

Etiquetas de cada ítem: código del catálogo (`P8-3`, `T-1`, `X-2`), fuente (`file:línea`, `OPEN #N`, `enc. N` = encargo N, `K` = tarjeta de `knowhow/`, y las siglas del catálogo `ESP`, `EXP`, `C04`, `IND`, `MONO`, `DP`, `P10`, `P12`, `R5`, `TB`, `AS`) y, cuando aplica, «Hoy: …» = lo que hace el código ahora. Las decisiones de dueño NO las resuelves tú: se anotan los datos que ayuden a decidir y se sigue con el valor de hoy. «Pasa/Limbo/Falla» son los tres estados de una regla.

## Antes del primer run

### Estado que cambia lo que mide cada run

- **`dev.on` está encendido**: `dev: {on: true, sample: 3, at: ["8"], seed: null}` (`pipeline/autopilot/criteria.yaml:3-8,52-56`). Tras aplicar las reglas del paso 8 se conservan solo 3 estrategias al azar y se borra el resto sin mirar el veredicto. Mientras esté on, lo que llega al 10 NO es el recuento de la puerta. OPEN #93 línea 704 dice 5: desfasado. Se apaga solo cuando el dueño lo diga (P8-8); no lo toques tú. Anota siempre el estado de `dev.on` junto a cada recuento. La auditoría del 10-05 avisa de que el paso 8 del `WORKFLOW_TIMING_BASELINE` usó `--smoke` (1.000 → 10 «por sorteo") y no es un cribado. Fuente: P8-8, `ledger/criteria-history.jsonl`, audit 2026-10-05:16.
- **R3 vive en 1,65 sin Limbo** en el código (`criteria.yaml:85`: `drift_excess_t ≥ 1,65` pasa; sin dato falla). El 2,33 con Limbo desde 1,65 es la propuesta escrita (OPEN #91:548-552, EXP, C04) y está desfasado. Verdad hoy = 1,65. Fuente: P8-1; sección «Documentos que se contradicen» del catálogo.
- **Suelo de operaciones/año: tres cifras vivas**: Build 10-75 (H4 10-100; índices y crudos 13-16; `assets/_study.yaml:30-42`), puerta R4a Pasa ≥ 35 / Limbo ≥ 20 (H4 ≥ 15) / Falla por debajo (`criteria.yaml:79-81`), memoria 35 desde 2026-10-02 y OPEN #93 «40-50». El Build deja entrar estrategias de 10-20/año que el paso 8 descarta por construcción (CPU gastada). Fuente: P6-1.
- **Las cifras del paso 6 salen de una calibración borrada** (203 poblaciones, 990.820 estrategias, spread equivocado, borradas 2026-10-04) y el constructor las sigue escribiendo en cada proyecto nuevo: techo 75, suelo 10, PF 1,0, beneficio > 0 (`assets/_study.yaml:3-6,40-46`). Tampoco vale lo que salió de `Test_Calib` para los pasos 6 y 8. Fuente: P6-2.
- **Ninguna línea de los pasos 8-19 está congelada** (`criteria.yaml:59`: PROVISIONAL, Council 2026-10-04; el archivo no tiene `frozen`). Toda línea es «convención»; no hay tasa de falsos positivos ni potencia medidas. Las reglas de los pasos 10, 12 y 14 las puso un Council sin datos (punto de partida razonado). Fuente: T-1, T-9, enc. 43:27-29.
- **Costes provisionales**: XAUUSD `costs_provisional` (OPEN #26); XAGUSD, UKOIL, USOIL `provisional_costs` arrastran avisos en todo estudio y todo número en R de esos activos. Los 17 activos nuevos exigen comprobar coste/spread por tramo (`core.assets`). Reajuste al spread Darwinex (OPEN #76) sin contrastar con retest DATATICK; spread real modelado desde Dukascopy antes de oct 2017 sin verificar; XAUUSD pasa de 9 a 63 puntos (2017-2026) frente a 5/10 declarados. Fuente: WORKFLOW.md:33-34; `studies/research/board/config.yaml:45`; `marketSurfaces/inputs/markets.py:33-36`; K `costs/darwinex-real-spread.md:6-12`, `costs/funded-tick-spread-vs-price.md:6-14`.
- **Referencias a datos borrados**: `calib_final/ab_build.md` y `scratch/calib*` (borrados 2026-10-04), tablas `null-fpr-2026-10-04` y `null2` (borradas 2026-10-06), `scratch/calib_step10/`, `scratch/calib_step12`. Cualquier cifra del catálogo que cite esas tablas (0,6 % FPR a 2,33; 0,4-6 %, 5-24 %) no se puede reproducir; no la uses como verificada. Fuente: P8-1, P10 (límites), P12.
- **`oos1` ya se leyó dos veces para elegir umbrales** (USDJPY y XAUUSD): todo umbral futuro elegido sobre ellos hereda esa mirada. **`oos2` es el bloque ciego: no lo leas nunca** en estos runs. Fuente: P8-9, T-1, T-2.
- **Árbol de trabajo con 601 rutas sin commitear**, incluidos ficheros de criterios vivos (grupos 8 y 11-15): el código que corre es el del árbol, no el de ningún commit. Fuente: X-3.

### Lo que recomendó el Council (2026-10-08) y toca 6-12 — recomendación a la espera del dueño, no orden

- Sellar `oos2` y apagar `dev.on` al calibrar (encendido solo para probar código, nunca a mano); no congelar números; lo no medido cuenta LIMBO, nunca PASA; prueba de viabilidad primero (construir un mono para pasos 10-19 y pasar plantadas por 10-20, horas, sin tocar `oos2`).
- Paso 8: tasa objetivo máxima del 1 % de monos pasan con costes; R3 en 2,33 provisional igual en código y documento (hoy el código está en 1,65: aceptarlo es un CAMBIO de código); suelo 35; no mirar más `oos1`.
- Paso 10: anotación, no puerta; quitar P7.
- Lo que invalidaría su veredicto y te afecta: un cambio de criterios de pasos 6-20 durante la corrida o antes del 2026-10-15; calibración del paso 8 que deje pasar más del 1 % de monos con costes antes del 2026-10-15; ninguna plantada que pase el paso 8 con 2,33 y 35 antes del 2026-10-15.
- Lo que el Council no sabe: si existe un mono que recorra 10-19 (hoy solo llega al 8); si 2,33 y 35 son buenos números (sus tablas se borraron); cuántas candidatas quedan con ambos (puede que ninguna). Aurelio avisa: con cadena corta la validación descansa en el paso 8 sobre un `oos1` mirado dos veces. Panel de una misma familia de modelo: trata 2,33 como apuesta.

### Decisiones del dueño aún sin responder en 6-12 — no las resuelvas; aplica el valor de hoy y anota datos

Paso 6
- **P6-1** Suelo de operaciones/año: ¿10, 35 o 40-50, y dónde (Build o puerta 8)? (a)(b)(c índices×reversión)(d Munger: 20-35 si t ≥ 2,33).
- **P6-2** ¿Firmas las cifras actuales del paso 6 o pides calibración nueva (spreads recalibrados, commit 3b71384, o sus números)?
- **P6-3** ¿Filtro de calidad IS dentro del Build o aplicado después?
- **P6-4** ¿Paleta para la calibración: originales, `_v2` o `_v3`?
- **P6-5** ¿Cuentan como «leer el reloj» (regla 15) `SessionHigh/Low/Open/Close`, `HighD/LowD/OpenD`, VWAP anclado, `HighestInRange`, `CBlock_TimeBreakout*`? (hoy solo se rechaza «Bar And Time»; la familia «sesión» no se corre hasta respuesta).
- **P6-6** ¿Se gastan builds en las 7 celdas «medido en contra» de `FAMILIAS.md»? (hoy no).
- **P6-7** ¿Salida obligatoria siempre, también con plantilla, o aleatoria al 50 %?
- **P6-8** ¿Confirmas 40 h de builds como presupuesto de calibración?
- **P6-9** ¿Cómo se construye la población sin seleccionar (regla 19; `bin/workflow.sh` no pasa `--acceptance calibration` ni `--random`)?
- **P6-10** ¿Riesgo por operación de las cuentas de fondeo?
- **P6-11** ¿Qué objetivo optimiza la búsqueda genética (ruido entre ejecuciones ~16 pp > efecto de cualquier objetivo)?

Paso 8
- **P8-1** Línea de R3: ¿1,65 sin Limbo (hoy), Pasa 2,33 con Limbo desde 1,65, u otra?
- **P8-2** Ventana de la deriva de R3 y del mono: ¿año (hoy) o semestre? (variante `d` elegida; Z0 pendiente).
- **P8-3** ¿AR(1) y corrección de sesgo/curtosis en la t de R3? (hoy fuera / no cargada).
- **P8-4** ¿Congelas las líneas Pasa/Limbo/Falla de cada regla («parada 2»)?
- **P8-5** ¿Tope del centrado de R5d (`cap_slope`) y mantener ±0,35 de R5?
- **P8-6** ¿Suelo duro de 60-80 operaciones en `oos1` (R1b/R5b) o red actual (Limbo < 100)?
- **P8-7** ¿Factor k del coste estresado en R5c: 1,25 (cargado) o 1,5?
- **P8-8** ¿Cuándo se apaga `dev.on` (parada 3)?
- **P8-9** ¿Se vuelve a leer `oos1` para elegir umbrales?
- **P8-10** ¿R3 sin excepciones por timeframe «por ahora»?
- **P8-11** ¿Umbral de `maeDepth`: `mark` o `drop`; uno o dos k?
- **P8-12** ¿Qué hacer con operaciones de `oos1` abiertas y cerradas en la misma barra (stop/target)?
- **P8-13** ¿Tamaño y papel del mono (donante vs ATR; informar ambos; Stouffer vs t conjunta semanal)?
- **P8-14** Estrategias archivadas antes de 2026-10-01 con reloj distinto: ¿congelar al archivar o re-cosechar?
- **P8-15** ¿Valor de «dato ausente» (`missing`) por regla: Pasa, Limbo o Falla? ¿Un «Project stopped» manual es fallo o parada?

Paso 10
- **P10-1** ¿Puerta o anotación (aceptar especialistas de su mercado)?
- **P10-2** ¿Confirmas las líneas P1-P9 o esperas a calibrarlas?
- **P10-3** ¿Línea de Falla de z_conj < 1,0 y se mide sobre el neto?
- **P10-4** ¿Cómo se lee el cociente cuando el original es negativo o ≈ 0?
- **P10-5** Cobre XCUUSD M30: ¿ficha de costes errónea y lista de mercados?
- **P10-6** ¿Línea distinta por clase de activo (mercados efectivos, Stouffer)?
- **P10-7** ¿t sin corregir o «ciega» (estropeada en UK100 y DAX40)?
- **P10-8** ¿Mantienes las decisiones que tomó el agente en el encargo 46 (a-f)?
- **P10-9** ¿Qué hacer con la media de z_conj de las diez de referencia (+1,45 frente a ±0,63 pedido)?

Pasos 10.5-12
- **P12-1** ¿Das el «corta» a T0-T4 y qué lee el 12 (`z_new`, máximo, `n_survives`)?
- **P12-2** K-1: ¿la R de `ret` es la de cada timeframe o la de la madre?
- **P12-3** K-2: ¿una sola vecina que falla T2a/T2b es Limbo o No Pasa?
- **P12-4** K-3: ¿qué ventana usa T4 (vela de la madre o la más lenta)?
- **P12-5** `CBlock_CandleBreakoutLong*.Double2`: ¿`bar` u `other`?
- **P12-6** ¿Debe el paso 12 descartar alguna vez?
- **P12-7** D1 para madres H1: ¿dentro o fuera de las hermanas?
- **P12-8** ¿Mínimo de madres para T1 (`tf.frequency.min_population`, hoy 5)?

Transversales que condicionan 6-12
- **T-1** ¿Cuándo y cómo se corre la calibración con población nula y plantada y quién autoriza gastar `oos2` en ella?
- **T-2** D4: ¿la reserva de `oos2` ata al autopilot (`ALGO_AUTONOMOUS=1`) y un estudio conserva su `oos2` de partida?
- **T-6** Registro del ledger: ¿qué se rellena hacia atrás y qué cuenta como N de pruebas?
- **T-7** ¿Claves de criterios por familia (`by:`)?
- **T-8** ¿Cómo se firma un criterio como «tuyo» (`set_by`/`set_on`; umbrales de crossmarket/crossTF a `ledger/thresholds.yaml`)?
- **T-9** ¿El archivo de criterios sigue sin sellar (`frozen`)?

## Paso 6 — Build

### Qué calibrar

| regla | valor de hoy | qué medir en los runs para fijarla | fuente |
|---|---|---|---|
| Operaciones/año del Build (H1, M30) | 10-75 (índices y crudos suelo 13-16) | población nueva por familia; qué parte de lo construido entre 10 y 35/año muere en el 8 por R4a | `_study.yaml:30-42`; P6-1, P6-2 |
| Operaciones/año del Build (H4) | 10-100; «H4 no se ha recalibrado» | recalibrar H4 | P6-2 |
| PF mínimo IS / beneficio neto mínimo | 1,0 / 0 | calibración nueva | `_study.yaml:44-45` |
| Aceptación mínima del Build | `NumberOfTrades` ≥ 100, `NetProfit` > 0 | cuánto IS-filtrado dentro vs después (P6-3) | P6-3 |
| Hecho «PF IS» | no existe como hecho | exponerlo para poder escribir una regla `PF ≥ 1,10` en el paso 8 | P6-2 |
| Salida con plantilla | `exits.condition_required` solo en Simple Strategy (aleatoria 50 % + 1-2 condiciones) | cuántas estrategias salen sin regla de salida | P6-7 |

### Fallos y cosas rotas que un run puede destapar

- Un hueco libre puede resolverse en un `AND` anidado de dos condiciones (39 % en Donchian + libre tiene 3), contra la regla 14; un hueco ligado a grupo se desvió de su bloque en 180 de 5.026. Cuenta condiciones por estrategia construida. K `sqx-drive/unselected-build-population.md:6-13`.
- Los interruptores de `BuildingBlocks` solo gobiernan huecos libres y la generación genérica; SQX ignora los pesos de la paleta en comparadores y valores genéricos. Comprueba que lo construido respeta la paleta. K `authoring/builder-block-switches.md:6-13`.
- Una plantilla con bloque en el gráfico 1 aborta la build y el constructor no la rechaza antes de lanzar (fallan `filterMALong`, `filterMAShort`, sus `_withExit` y `spRSI2`; las otras 56 usan solo el gráfico 0). Aborto de build = síntoma. K `authoring/template-second-chart-aborts-build.md:6-12`.
- El lado de plantilla con idea fija se escribe `1..1` (idea + una aleatoria), no `0..1`: «la idea sola» no se construye desde plantilla hasta que un build corto pruebe si un hueco ligado con mínimo 0 conserva su bloque. OPEN #93 (733-736).
- Un build `Trade_` llena el databank en minutos y luego reemplaza por Ret/DD IS el resto de sus 180 min: selección no medida. OPEN #93 (714-717).
- Bloques de reloj: hoy solo se rechaza «Bar And Time»; vigila que ningún bloque de P6-5 se cuele en una paleta que lo vete. WORKFLOW.md:248.
- Palettes: los originales (148-180 bloques) llevan bloques de reloj y de stop/limit (regla 15); los `_v2` (6-13) y `_v3` (99-127, `pullback_base_v3` la termina otra sesión) sin aprobar. Anota cuál usó cada run. enc. 42:158-160.
- Databank llena en memoria y vacía en disco exporta 0 estrategias en silencio (el exporter lee disco; regla 1). K `databanks/memory-vs-disk-exporter.md:6-14`.
- Perfil de mercado a medias: top-up parado el 2026-10-02, solo DAX40 y DJ30 tienen las seis medidas de TR-65; `measures.csv` y `assets/FAMILIAS.md` con filas viejas. OPEN #100 (819-825).
- Ninguna Simple Strategy se ha arrancado nunca en SQX (solo ficheros); tampoco los 17 activos nuevos (DAX40 y USOIL solo en un install temporal; DAX40 no está en ningún proyecto). Un fallo de primera vez es plausible. OPEN #93 (713, 730-732), OPEN #28; enc. 42:44-52.

### Lo que solo SQX puede verificar

- Si un hueco ligado con mínimo 0 conserva su bloque (build corto; P6 arriba).
- Spread por tramo de cada activo nuevo con `core.assets` y una población de prueba de cinco minutos por activo (enc. 42:44-52).
- Selección dentro del databank lleno: 180 min contra 6 min (OPEN #93 714-717); ningún filtro IS se probó con databank lleno (P6-3).
- La isla es la unidad de azar: φ ≈ 38× la varianza binomial (19 de 56 supervivientes del 8 venían de una isla de 20); compara builds por islas completas. K `research/genetic-build-islands-are-the-sampling-unit.md:6-12`.
- Caja de tiempo (250 × 20 islas = 5.000 individuos por generación) sin medir; duración por población (P6-8).

### Qué anotar de cada run

- Paleta usada, familia, lado, timeframe, activo, spread por tramo aplicado.
- Estrategias aceptadas (Accepted de SQX) y generadas; distribución de operaciones/año (cuántas < 20, 20-35, ≥ 35) y de condiciones por estrategia (¿alguna con 3?).
- Duración del build y estado de llenado del databank; isla de origen si se ve.
- Estrategias con PF IS < 1,10 (para el hecho «PF IS»).

### No tocar / no decidir

P6-1 a P6-11 (arriba); no cambiar `assets/_study.yaml` ni la paleta de ninguna familia; no correr la familia «sesión» (P6-5) ni las 7 celdas «medido en contra» (P6-6). Los dossiers `criterios-implementados-2026-10-12.md` y `criterios-implementados-2026-10-12.md` no valen como fuente de cifras.

## Paso 8 — Puerta IS/OOS

### Qué calibrar

| regla | valor de hoy | qué medir en los runs para fijarla | fuente |
|---|---|---|---|
| R1a presencia / R1b sanidad | `presencia_passed ≥ 1`, `sanidad_passed ≥ 1`; sin dato falla | nada (decisión del dueño); orden de trabajo sugerido: arreglar R1a primero | IND:78-80 |
| R2 neto `oos1` | `estaticas_value > 0` | nada | |
| R3 `drift_excess_t` | Pasa ≥ 1,65; sin dato falla; sin Limbo | tasa de monos que pasan (objetivo Council ≤ 1 % con costes) y de plantadas (0,05/0,10/0,15, EXP añade 0,04); ≥ 5.000 por nivel con la cascada apagada; cuántas pasan a 1,65 y a 2,33 | `criteria.yaml:85`; P8-1, P8-2 |
| R4a operaciones/año build | Pasa ≥ 35, Limbo ≥ 20 (H4 ≥ 15) | banda con s_min económico y potencia (depende de los años de `oos1`) | `criteria.yaml:79-81` |
| R5b operaciones `oos1` | Pasa ≥ 100, si no Limbo; nunca Falla | cuántas caen < 100 y < 60-80 (P8-6) | `criteria.yaml:83` |
| R5 `z_frec` | Pasa en [−1,5; 1,5], Limbo en [−3,5; 3,5]; solo diagnóstico; φ acotado [1,5; 3,5] | φ̂ real, mediana poblacional por activo/timeframe/lado (mín. 30), cuántas de las 169 vivas cambian de estado | P8-5 |
| R5c `edge_mean_oos`, `t_exceso_k` | Pasa edge ≥ 2 y t ≥ 1,65; Limbo edge ≥ 1,25; k = 1,25 | coste pagado solo en `oos1`; denominador de costes calibrados MT5-SQX; bootstrap H1 y M30 | `criteria.yaml:92-94`; P8-7 |
| R5d `t_b`/`e_fin` | Limbo si `t_b` < −1,65; Falla si además `e_fin` ≤ 0; `cap_slope` null; solo diagnóstico | tope de centrado (mín. 30 estrategias para centrar) | P8-5 |
| R8 `t_sin_mejor_trimestre`, `t_sin_3_mejores` | Pasa ≥ 1,65, Limbo > 0 | coste en buenas (3 operaciones fijas o ≈ 2 % de n) | |
| R9b `mae_p95_r` | Pasa ≤ 1,5, Limbo ≤ 2,5 («orientativos») | mediana de la peor MAE de la población = −3,72 R | |
| Calidad de datos / retraso una barra | `n_afectadas == 0` o `ret_datos ≥ 0,6` (Limbo ≥ 0,25); `retraso_ret_min ≥ 0,6` (Limbo ≥ 0,25) | distribución de `retraso_ret_min`; `feedQuality` sin datos | |
| R7 `q_p` / R6 `dd_p` / mono `z_mono` | R7 Pasa > 0,05; R6 Pasa > 0,10, Limbo > 0,01; mono ≥ 1,65; R7 y mono nunca fallan | sensibilidad de R6 a L (hoy L = 8, 5.000 secuencias; probar 5-10 o √n_IS); R7 con meses; las dos ventanas de R3 | |
| `maeDepth` | solo mide (k 3 y 4 ATR; `min_cuota_rec: null`; no marca a nadie) | deep trades (≥ 3 ATR: 26 % de las operaciones y 33 % del neto en build; 24 % y 8 % en `oos1`) | P8-11 |
| R9a / R9c | salieron de la puerta (encargo 45) | nada aquí | |
| Tasa de falsos positivos del paso 8 | convención | población nula + plantada con la cascada apagada | T-1 |

Cifras de referencia ya medidas (para comparar, no para fijar): R3 en NIKKEI225 M30 pasan 44 a 2,33 y 325 a 1,65 de 10.000 (nulo esperado 15-60 y ≈ 390); R3 a 1,65 dejaría pasar ≈ 405 de 240.000 sin ventaja en bruto (87 netas de costes); caso sintético de 196 operaciones deja pasar 0,9 / 13 / 34 / 62 % de nulos según nivel; 8 reglas que pierden 5 % de las buenas cada una = ≈ 34 % perdido. Fuente: P8-1, P8-4.

### Fallos y cosas rotas que un run puede destapar

- **Mismo tramo, misma barra**: `level1a.py:38` (assert) y `edgeCost/costs.py:48` se rompen con operaciones de `oos1` abiertas y cerradas en la misma barra (0,04-0,14 % en donchian, emaCloseCross, timeRangeBreakout; todas las versiones con stop del paso 25). Síntoma: assert. enc. 44:110-117,125-139; P8-12.
- **Cambio de identidad build → retest**: B1 arregló el síntoma (`judge.resolve`: 1.557 fallos de presencia → 0), pero el 7-11 % cambia de identidad (huella coincide 99,7-100 % en 3 poblaciones); el fallo de identidades descartaba 29 de las 169 vivas (17 %). Compara conteos de presencia build↔retest; causa sin nombre. enc. 44:41; IND:62-63,131-139; OPEN #93 (745); K `sqx-format/identity-differs-across-databanks.md:6-13`.
- **`entryQuality` y `feedQuality` sin datos**: `feedQuality` murió por falta de inventario (hoy no falta); `entryQuality` corre después del corte y el juez no ve sus hechos; con los K de hoy casi toda estrategia sale «insuficiente» (< 10 marcadas). Comprueba si los hechos llegan al juez. enc. 44:352-353,365-366,571,744; IND:47-48; ESP:827,890,1249-1250.
- **Estrategias archivadas con reloj distinto**: antes del 2026-10-01 las operaciones están en Asia/Jerusalem y las barras en EETUS (1 h en semanas de desfase DST); el universo rechaza el miembro (licencia < 99 %). Síntoma: licencia MAE/MFE 0,73-0,97 < 0,99. K `export/archived-trades-vs-reclocked-bars.md:6-13`; P8-14.
- **Repreciado de stops** inflaba +290 a +370 USD por operación parada (30-37 % de las operaciones de toda población con stop) hasta 2026-10-07; las poblaciones guardadas no llevan `Close type`. Desconfía de cualquier pase de poblaciones con stop previo a esa fecha; sin medir: cortos, PT, stops con stamps M1. enc. 44:118-127; K `export/off-grid-stamps-and-stop-exits.md:6-12`.
- **Repreciado forex**: cortos, comisión ≠ 0 y swap en puntos sin verificar contra SQX (`tick_step = tick_size/10` supuesto); el signo del swap corto se mira en MT5. La z es robusta, la `e` en R no. enc. 44:658-668,858-862; `crossmarket/travel/README.md:104-114`.
- **`dailyEquity.bin` es el mínimo del día** (exacto en 3.983 días pero los lectores dan Sharpe/correlaciones/`worst_day_r` «low to low»). Sigue pendiente `search/stageb_data.py:62` (llama a `minute_path` sin comisión), reconstruir cachés de universo anteriores al 10-04, rama PercentageBased y objetivo de perf para `closecurve`. OPEN #88 (526-536); T-5.
- **Cuatro modos de cálculo**: `calibrate.charged()` solo mete swap y comisión (nunca spread ni slippage) y los modelos que sortean la duración conservan el swap viejo; cerrado solo para la puerta (`engines/nulls/windowed.py`); escalera y ~35 importadores no cobran nada. `engines/nulls/README.md:127-128`.
- **Persistencia `oos1` → `oos2`**: ρ ≈ 0,059; ~65 % de los que pasan aún pierden en `oos2`; pasar el 8 hace candidata, no válida (informativo; no leas `oos2`). K `research/oos1-oos2-persistence.md:6-13`.
- **Sin diagnosticar en el ledger**: el ledger decide por parámetros con semilla nueva en cada corrida (anotada en el scorecard; reproducible releyéndola). enc. 44:897-912.
- **Estrategias sin MAE/curva o < 30**: el centrado exige ≥ 30 estrategias; con menos no se centra. P8-5.
- **Reloj de feeds**: las cosechas del 27 al 29-09 de USDJPY no reconcilian por el cambio de reloj; USDJPY espera cosecha nueva. enc. 44 / `falsePositives/README.md:86-95`.
- **Reglas «heredadas del donante» sin medir** (R5/R5d, presencia, clones, R4a, R5b): el plantado es un exceso constante, así que retraso y calidad de datos miden rechazos por ruido, no potencia. enc. 44:885,895; `falsePositives/README.md:77-84`.
- **`falsePositives` aplica 14 de 16 reglas** (faltan las dos que piden escaneo de ticks); los pasos 10, 12 y 14 no tienen mono y dejan pasar a todos: «los monos vivos son un techo, no una medición». enc. 41:211-220.
- **Mono**: tamaño por ATR de la barra anterior; con tamaño de donante el MAE flotante queda fuera de sizing y `oos_worst_trade_mae_r`/`oos_worst_day_r` infraestiman el falso positivo; en USA500 H1 lotes reales promedian 19,4 y los de sorteo ATR 31,1; en la prueba pequeña de `Test_XAUUSD_donchianUpperCrossUp2_H1` cruzan el 8 entre 14 y 36 de 3.000 según dimensionado; `z_mono` correlaciona 0,971-0,992 con `drift_excess_t` (un activo/timeframe). K `research/monkey-reprice-audit.md:7-13`, `monkey-size-carries-donor-volatility.md:6-14`, `gate-monkey-z-tracks-drift-t.md:6-7`; P8-13.
- **Variantes de R3**: el sesgo medio absoluto es a 0,09, b 0,12-0,15 (máx 0,33), c 0,016, d 0,017 («usa d, o c, nunca b»); no consta cuál variante está cargada (una lectura dice que el criterio usa la a). Comprueba cuál usa realmente la corrida. EURUSD H1 a 1,65: 2,6 % largos vs 5,8 % cortos. P8-2; K `research/drift-term-biased-by-side.md:6-13`.
- **Escala de la t de R3 corregida el 2026-10-02** (viejo 1,3 → 1,42; 1,65 → 1,92; 2,0 → 2,55): no mezcles cifras anteriores. K `research/gate-t-scales.md:6-13`.
- **Nulos con fórmula con fallo**: los nulos de OPEN #91 se calcularon con operaciones cerradas; hay que recalcularlos sobre `trade_t` y `drift_excess_t`. enc. 41:188-197; OPEN #91.
- **Seis puntos abiertos de OPEN #93 en el paso 8**: corrección de deriva no aplicada en `crossmarket/simulate/excess.py`; `wfc.py` da a los mercados extra las fechas del principal; crossmarket y crossTF cablean su ventana y leen `oos2` de exports crudos; el fin de `oos2` de `_policy.yaml` (2026-09-30) está pasado el último bar de XAUUSD, XAGUSD y HK50 (una tarea OOS2 no arranca); 31 celdas base H1 sin `oos2` (`oos2_job.sh` sin correr). OPEN #93 (745).
- **Crítico independiente** no revisó el contraste de los cinco tests juntos, el enriquecimiento frente a la nula por franja de frecuencia ni las 47 celdas enriquecidas; `oos1` y `oos2` gastados para esas estrategias; solo 52-58 % son estructuras distintas. C04:262-318.

### Lo que solo SQX puede verificar

- Que `Project finished` coincide con todo en disco: aparece antes de que todo esté escrito; un worker matado durante el sync pierde la databank del retest y puede dejar un `.sqx` roto. K `perf/autopilot-dead-time.md:6-13`.
- Retest exacto en SQX con ejecución retrasada (para `entryQuality`): pasa al encargo 45, fuera de estos runs. enc. 44:368-369.
- Spread-en-% arrastrado a un segmento antiguo infraestima 2-4× (elasticidad −0,64 en NIKKEI225, aplicado 2026-10-04). K `costs/funded-tick-spread-vs-price.md:6-14`.
- Huella del `optimizationProfile.bin` con otra causa abierta 🤔. K `sqx-format/optimization-profile-byte-order.md:6-12`.

### Qué anotar de cada run

- Embudo por regla: entran/salen en cada R (R1a, R1b, R2, R3, R4a, R5, R5b, R5c, R5d, R6, R7, R8, R9b, calidad de datos, retraso, mono), con Pasa/Limbo/Falla de cada una y solapes; cuántos de los que pasan R3 caen por R4a.
- Total Pasa / Limbo / Falla del paso 8 ANTES del sorteo `dev.on`, y cuántas quedan tras él.
- Hechos que salen vacíos («sin dato») por regla; identidad: cuántas estrategias de build no aparecen en el retest.
- Cuántos pasan R3 a 1,65 y a 2,33 (para comparar, sin cambiar la línea); tasa si la población es nula y si es plantada.
- Tiempo del paso, φ̂ de R5 por activo/timeframe/lado; MAE profundo (≥ 3 ATR) share.
- Para K-m: embudo por regla y nivel de las dos poblaciones de prueba (USA500 H1 largo y las 10.000 de NIKKEI225 M30), H1 frente a M30, si R1b pide suelo.

### No tocar / no decidir

P8-1 a P8-15; no tocar `criteria.yaml` ni `ledger/thresholds.yaml`; no apagar ni encender `dev.on`; no cambiar la ventana ni la variante de R3 (Z0 espera la respuesta del dueño); Z1 (cargar líneas congeladas) y V (corrida de verificación) pendientes de P8-2/P8-4. R9a/R9c son del encargo 45. Parte M (documentación del 8) está pendiente: README de la puerta, `pipeline/autopilot/README.md`, skills `oos-gate` y `workflow-simple`, capítulo 29 del manual, glosario, fila 8 de `WORKFLOW.md`.

## Paso 10 — Otros mercados

### Qué calibrar

| regla | valor de hoy | qué medir en los runs para fijarla | fuente |
|---|---|---|---|
| P1 `fixed_distance`; control 7.1 `invalid_fraction` | `fixed_distance ≤ 0`; `invalid_fraction ≤ 0,25` (Limbo si no) | población nula y plantada por el 10 | `criteria.yaml:127-184` |
| P2 `freq_off`, `freq_off_fraction` | Pasa 0 (Limbo ≤ 2); fracción ≤ 0,25 | idem | |
| P3 `z_conj` | Pasa ≥ 2,33; Limbo ≥ 0 | FPR de las dos reglas juntas y potencia con ventaja plantada | |
| P4 `z_conj_v2` | Pasa ≥ 0; Limbo > −1,65 | idem | |
| P5 `z_minus_market` / P6 `p_breadth` | ≥ 1,65 (Limbo si no) / ≤ 0,10 (Limbo si no) | idem | |
| P7 `tau_half` | Pasa ≥ 0,5; Limbo > 0; sin dato = Limbo (hoy siempre) | idem; falta productor de `e_principal` en el 8 | |
| P8 `worse`, `worse_fraction` | Pasa ≤ 1; Limbo ≤ 2; fracción ≤ 0,25 (0 / 1-2 / ≥ 3 mercados) | idem | |
| P9 `z_beta`, `e_end` | Pasa z > −1,65 o (z > −2,33 y e > 0); Falla z ≤ −2,33 y e ≤ 0 | idem | |
| Juzgar en bruto (`travel.judge_on: gross`) | bruto (dueño: «Sí, tu recomendación») | caveat residual: con ATR alto la población neta +0,98 baja a +0,30 bruto, +0,08 sin huecos | |
| `max_displaced_share` / `max_fill_error` | 0,20 / 0,25 ATR | agente / diagnóstico viejo | P10-8f |
| Falla de z_conj | < 1,0 (pierde 38 % de ventajas modestas con transferencia completa, 62 % con media; sin tasa medida) | tasa medida | P10-3 |

### Fallos y cosas rotas que un run puede destapar

- **P7 / `e_principal`**: queda sin dato → Limbo siempre hasta que el mono del 8 lo entregue; hasta entonces NINGUNA estrategia puede dar PASA en el 10 (aceptado por el dueño). Las diez de referencia: 0 Pasa, 5 Limbo, 5 Falla. El encargo 44 entregó `level3c.py` pero no consta el enlace. Mira si el hecho sale vacío en cada run. enc. 46:17,40-41,97; OPEN #22; `travel/README.md:148-149`; `travel/run.py:132-133`; `steps.md:16`; WORKFLOW.md:35.
- **Original negativo o ≈ 0**: con original negativo el hecho sale vacío (Limbo; 7 de 10 guardadas tienen t mediana del original negativa); con original ≈ 0 el cociente estalla (−10,39 con 0,163; t = 0,05 y 0,03 da 0,6 y Pasa). P10-4.
- **Cobre XCUUSD M30**: coste recuperado 192 USD/op frente a ~340 típico, `fill_mismatch`, PF mediano 0,53; mete 0,6-2,2 de t en contra; posible error de ficha. Hoy solo cae el cobre con `max_fill_error` 0,58. P10-5.
- **Peso 1/ATR roto con barras casi planas** (24-12-2013 a feb 2014: 234 barras UK100, 362 DAX40): el 0,1 % de barras se lleva el 44 % del peso en UK100; `excess_blind_t` UK100 −5,24 frente a −3,72. `simulate/excess.py:212` recomienda `excess_blind_t_*` pero `criteria.yaml` lee `excess_t_pooled`. P10-7.
- **Huecos de feed 2011-2015** en HK50, UK100, AUS200, USA500 y USATEC (76-180 días; el arreglo es `max_displaced_share` 0,20 y exclusión por celda; un agujero sintético limpio no reprodujo el +0,44 original: causa no del todo explicada). K `research/index-feed-holes-and-the-shift-null.md:6-12`.
- **Nulo conjunto por año**: un año no es un número entero de semanas; no validar NaN sobre z_conj. K `research/joint-null-year-shift.md:6-13`.
- **Dos familias de PF** (`pf`/`pf_sqx`) discrepan de lado (DAX40: 1,17 frente a 0,94). P10:1035-1046.
- **Sesgo residual**: z_conj media de las diez de referencia +1,45 (propuesta pedía ±0,63); cinco de las diez dan z_conj ≥ 2,33 aunque fallaban el 8. Compara la media de z_conj de cada población nula. P10-9.
- **Diez t conjuntas negativas por costes** (cobro medio 69 USD/op; resultado −41). P10-3.
- **`markets_effective`** usa correlaciones al cuadrado y un solo mercado con pocas operaciones lo deja vacío. K `research/crossmarket-effective-markets.md:6-13`.
- **Estudio emite `verdict.csv`** aunque README y `config.yaml` dicen que no emite veredicto; los veredictos guardados con el estudio antiguo hay que rehacerlos (`shift_step: day` ahora cuenta días hábiles: resultados de crossmarket previos caducados). WORKFLOW.md:35; P10-1; P10-8c.
- **Paso 9**: no hay gancho de P1; la estrategia se retestea y el estudio la marca Limbo si `fixed_distance` > 0 (28 de 6.000). `DeadZonePip` del WAE y `#StopLossInPips#` no cuentan como distancia fija en P1 (350 de 6.000; con la otra opción quedarían «no evaluables»). P10-8a,b.
- **Cinco lecturas del núcleo** del encargo 46: lotes sin redondear ni topar (`Decimals: 2`, `MaxLots: 500` no se aplican); operaciones cerradas tras el fin de `oos1` fuera; a las desplazadas no se les reaplica cierre de viernes ni «plano para entrar»; entrada en barra defectuosa pasa a la siguiente válida; `shift_step: day` cuenta días hábiles. P10-8c.
- **Umbrales de crossmarket** en `config.yaml › travel:` y `criteria.yaml`, no en `ledger/thresholds.yaml`. P10-8d, T-8.
- **Sección 8.1 de la propuesta** sin implementar salvo P9 (prior de plantilla, factores, régimen, vecindad). P10-8e.
- **Sin medir**: FPR de las dos reglas juntas, potencia con ventaja plantada, una corrida sobre estrategias que pasen el 8, sesgo por lado para NIKKEI225 largo, efecto de que los primeros 4 años lleven solo 3 mercados, unidades de las reglas internas. Las cifras 0,4-6 %, 5-24 % venían de `scratch/calib_step10/` (ya no existe; solo se reprodujo 1,77 y la aritmética del 0,7 %). P10:1048-1050,1056-1068,1142-1143.
- **Pestaña Cross Market** sin capturar nunca con el estudio nuevo; lista de adaptación de la ventana sin tocar (sub-pestaña `oos` `ficha.py:18,168-178`; `judge_on`/`shift_unit`/`shift_step` como texto libre `knobs.py:56`; `catalogue.py:64-65` clasifica crossmarket como «gate» aunque nunca descarta; `many.population` sin lectura por regla; 19 carpetas `AlgoData/reports/*/*/*/crossmarket` con esquema viejo marcadas caducadas). enc. 46:332-413,460-467.
- **Stouffer** «prohibido como criterio» (deja pasar 5-24 % sin edge) frente a t conjunta semanal (sd 0,83-0,95); agrupar mercados del mismo lado multiplica el sesgo de lado (FPR 9-13 % en cortos de índices). EXP:329; P10:1052-1054,1068.
- **Repricer** auditado solo para largos, comisión cero y swap en %; la `e` en R en forex no es fiable (afecta P7, P9). `travel/README.md:104-114`; enc. 46:130-132.
- **Mercados: listas** de 2-5 tests independientes (forex 4,1-4,7; índices 1,6-1,9; metales/crudos 3,0-3,6). P10-6.

### Lo que solo SQX puede verificar

- Que los mercados adicionales del retest corren con sus ventanas y costes declarados (`assets/_markets.yaml`); el hallazgo de los huecos de índices depende de los feeds reales.
- Una corrida del 10 sobre estrategias que pasen el 8 (hoy no existe). P10:1048-1050.
- Tiempo del estudio (21 s por corrida el reejecutado de crossmarket antiguo). enc. 46.

### Qué anotar de cada run

- Pasa / Limbo / Falla del paso 10 y por qué regla (P1-P9), con los motivos «why»; cuántas dan Limbo por P7 sin dato.
- z_conj de cada estrategia y media de la población (nula: ¿≈ 0 o +1,45?); `main_excess_t` de las originales negativas.
- Mercados efectivos por clase de activo; qué mercados entran, cuáles quedan excluidos (`max_displaced_share`, huecos); `fill_mismatch`.
- Si cobre/UK100/DAX40 vuelven a salir con los mismos problemas; tiempo del paso.
- Cuántas fallan solo por especialista de su mercado (útil para P10-1).

### No tocar / no decidir

P10-1 a P10-9; no mover umbrales ni mover los de crossmarket a `ledger/thresholds.yaml`; no decidir si el 10 es puerta o anotación; las reglas del 10 las puso un Council sin datos y el 46 las sustituyó.

## Pasos 10.5 a 12 — Otras temporalidades

### Qué calibrar

| regla | valor de hoy | qué medir en los runs para fijarla | fuente |
|---|---|---|---|
| 11.5 corte | `rules: []` (no corta a nadie; todas las madres corren la fase 2) | corrida real con tareas de fase 2 y «corta» del dueño | `criteria.yaml:185-200`; P12-1 |
| 12 `crossTF.combined.z_new` | Pasa ≥ 2,33; si no Limbo; nunca Falla | solo hay medida a 1,65 (3,6-5,7 % FPR, madres H1 y gemelas a coste cero; sin M30); `scratch/calib_step12` ya no existe; a 2,33 se espera ≈ 1 % sin medir; combinada/máximo/`n_survives` dan 0 Pasa a 2,33 y 1/2/2 a 1,65 | P12-1, P12-6 |
| Cifras T0-T4 | `rounding_shift` 0,25; `min_trades` 30; φ en [1,5; 3,5]; `ret` 0,5; `z_Δ` 1,65; pico aislado 0,25; T2b 1,65 / 0; 5.000 corridas | datos reales de una corrida de fase 2; T0-T4 se emite en paralelo a `z_new` | enc. 47 |
| `tf.frequency.min_population` | 5 (por debajo: sin dato → Limbo) | corrida real | P12-8 |
| T3 etc. de umbrales de `ret` | 0,5 / 0,25 | con K-1 (R propia de cada TF) | P12-2 |

### Fallos y cosas rotas que un run puede destapar

- **Tareas de fase 2 inexistentes** en proyectos creados antes del encargo 47: quien las busca recibe lista vacía, 11.7 se salta y el 12 juzga con «sin dato». Síntoma: 11.7 saltado. enc. 47:157-158,177-178.
- **Identidad de la hermana**: el store guarda el fichero de la madre y los parámetros de cada hermana, nunca el `.sqx` de la hermana (existe la skill de reconstrucción). Relevante si hay que recuperar una.
- **`scale.fabricate(..., symbol)`** saca el activo de la primera madre si no se pasa (`crosstfload.py:107` puede pasarlo). `tf/inputs.build_banks` lee `build_databanks` de `blocks.json` y los exports `CrossTF_<TF>_build` los hace `afterrun`; solo probado en código y tests. enc. 47:9-12.
- **Hermanas M15**: periodos duplicados; coeficientes `k/c` (NIKKEI225 desde M30: M15 0,704; H1 1,419; H4 2,833); `k/c` puede pasar de `maxValue` (PMax 10,99 → 15,6 en M15); los parámetros `unverified` marcan la hermana para T0; la tabla de distancias fijas no cubre WAE `DeadZonePip`, `#StopLossInPips#` ni `SLPT.ValueFromFormula`; `CBlock_CandleBreakoutLong*.Double2` está `unverified` en `sqx/variants/ranges.yaml`. K `sqx-drive/crosstf-scaling-coefficients.md:6-12`, `sqx-format/fixed-distance-keys.md:6-12`; P12-5.
- **D1 para madres H1**: toda hermana D1 de una Simple Strategy H1 queda «clamped»; tarea propia con motor MetaTrader 4. `crossTF/README.md:93-96`; P12-7.
- **`ret` depende de la escala**: una hermana que gana lo mismo en precio por operación que su madre M30 lee `ret` ≈ 0,7 en H1 y ≈ 1,4 en M15 (medido 0,57 y 1,70). P12-2.
- **T2a/T2b con una sola vecina** (K-2) y T4 con ventana de la madre (K-3; en `Trade_NIKKEI225_M30_volatilidadL` la H1 más parecida da 0,44). P12-3, P12-4.
- **La combinada premia tener menos prueba** (`3.11.426`, una hermana, 1,72, por delante de P, dos hermanas, 1,30); el signo «heredada o falla» se lee sobre un Sharpe revalorado sin 807 puntos por operación de coste. P12:889-893,959.
- **`z_new`**: falla el doble con ρ > 0,9 (10 % de FP en 39 casos; el código corta en 0,95, afecta a 1 de 16); ρ sale de 48 meses (error ≈ 0,15); una hermana recortada entra igual (23 % H1→H4, 53 % M30→H4); el stop no se escala (≈ 1,4× más ancho en H1, ≈ 2,8× en H4); la z depende de la semilla (2 % con 2.500 monos); comentarios y README desfasados (5 % vs 2,7-6,3 %); la combinada tipo Stouffer supone hermanas independientes y no lo son. P12:897-917,961-965; EXP:373.
- **Mínimos de operaciones**: 121 operaciones (Feynman) dejarían solo 5 de 16 hermanas «legibles»; exigir `n_tested` = 2 a 1,65 quita el único Pasa (`3.11.426`). P12-6.
- **Hechos «comparado con el original»** del 12: bloquea que la celda baseline tuvo 0 operaciones en las 30 madres. OPEN #90 (684-695).
- **Repetición de 11.5**: puede leer un export obsoleto; `apply_verdict` sobre `CrossTF_Input` en 11.5. enc. 47 (V).
- **Parte B** (borrado de lo viejo: `z_new`, Stouffer, `corr_vs_baseline`, seis lecturas, filas `unscaled`/`control`, re-apuntar `many.py`/`report.py`) sin hacer, tras V; Parte D (documentación: README del estudio, skill `crosstf`, `steps.md`, WORKFLOW, CLAUDE.md, manual y knowhow) pendiente. enc. 47:13,15,181-187,260-277.
- **`test_ui_criteria::test_state_write_stamp_freeze`** falla por el paso 11.5 nuevo. enc. 46:415-449.

### Lo que solo SQX puede verificar

(Parte V del encargo 47, nunca corrida en vivo.)
- Una corrida real con las tareas de fase 2 (11.7).
- Que M15 sea aceptado por los indicadores (periodos duplicados).
- Que `k/c` no pase de `maxValue` (PMax 10,99 → 15,6 en M15).
- Que `z_Δ` y `z_build` salgan centradas en 0 con madres sin ventaja.
- El coste en tiempo de la fase 2.
- Si las tareas de fase 2 escriben `CrossTF_<TF>_build` y si una tarea relanzada sobrescribe o añade.
- `apply_verdict` sobre `CrossTF_Input` en 11.5; que una repetición de 11.5 pueda leer un export obsoleto.
- El lote de vecinas por la fábrica de variantes y el configurador sobre un proyecto sin las tareas (no probados en vivo; WORKFLOW.md:42).
- En 10.5 no hay stop; clasificación por vela/ventana; M15 dobla periodos (a confirmar).
- Fuente: enc. 47:14,58-60,223-226; OPEN #108.

### Qué anotar de cada run

- Por madre: hermanas fabricadas por timeframe, `unverified`/`clamped` y por qué; tareas de fase 2 presentes/ausentes.
- T0-T4 (por regla: valor, estado, `why`, `t2a_lone_fail`/`t2b_lone_fail`) y `z_new` combinada lado a lado; `ret` por timeframe; n de hermanas legibles; `n_tested`.
- Z de población nula centradas en 0 o no (`z_Δ`, `z_build`); tiempo de la fase 2; si 11.5 cortó a alguna (hoy `rules: []`).
- Cuántas madres pasan al 13 y cuántas Pasa/Limbo del 12 (nunca Falla hoy).

### No tocar / no decidir

P12-1 a P12-8; no dar «corta» ni sustituir `z_new` por T0-T4; no tocar `ranges.yaml` (`unverified`) ni quitar D1 por tu cuenta (`crosstfload --targets M30 H4` es opción del dueño); no ejecutar la Parte B.

## Transversal a los pasos 6-12

### Poblaciones nula y plantada hasta el 12

- Hoy el mono solo llega al paso 8; los pasos 10, 12 y 14 no tienen mono y dejan pasar a todos (el catálogo: «los monos vivos son un techo, no una medición»). El Council no sabe si existe un mono para 10-19. T-1; enc. 41:211-220; `falsePositives/README.md:86-95`.
- Calibración propuesta: ≥ 5.000 por nivel (nula y Sharpe por operación 0,05 / 0,10 / 0,15; EXP añade 0,04) con la cascada apagada, en `studies/screening/falsePositives/`. Falta: mono del paso 10, corrida a 10.000 con `--ledger` (es del dueño, README encargos:44), monos seleccionados en SQX (encargo 30; cuesta una corrida de autopilot de custodio por población). T-1; enc. 41:37-38,211-229.
- Las diez madres `Trade_NIKKEI225_M30_volatilidadL` (largas, M30) no sirven para calibrar: fallan hoy el 8 y el 10 y su `oos2` ya se leyó (en 18.5); no hay medición para H4, builds largos ni réplicas. T-1.
- Solo hay tres poblaciones de prueba y una grande (USA500 H1 largo): nada sobre H4 ni cortos se podrá proponer (P8-10). El plantado es un exceso constante.
- Los pasos 10, 12, 14, 16 y 20 no tienen comparación con la gemela aleatoria, ni medida de cuánta evidencia nueva añade cada paso, ni equipo rojo, ni embudo del 8 al 20 por población; falta dar al riesgo flotante un lugar en 10-20. enc. 43:43-87.
- Ningún paso que juzga debe tener `rules: []` sin razón escrita (1.6): hoy lo tiene 11.5. enc. 41:36,199-209.
- Autopilot para población nula: el código está (`ALGO_AUTONOMOUS=1`, cero supervivientes como final limpio) pero no consta probado el criterio de tres corridas seguidas a cero supervivientes que acaban en `FIN`, ni matar la JVM a media corrida y obtener un fallo con mensaje. enc. 41:34,175-186,258.
- Al registrar: el ledger no tiene filas de `Test_Calib` (el dueño las borró contra el consejo del Council) y N de pruebas está sin decidir (T-6): un Sharpe desinflado sale optimista sin ese registro.

### Costes y feed

- Mantén el spread/comisión/swap del `core.assets` por activo y tramo; los costes provisionales de XAUUSD, XAGUSD, UKOIL, USOIL marcan todo número en R. Consulta la sección «Antes del primer run».
- Feed quality: Brent (109 huecos propios al año) y plata (33) pasan del listón de 30; el dueño debe declarar la sesión del Brent; K y sesiones de NIKKEI225 (20), DAX40 (20), DJ30 (20), USA500 (25) las dejó el agente. WORKFLOW.md:29,249,251; `thresholds.yaml` `feedQuality.K.*`; `studies/data/feedQuality/POSSIBLE_IMPROVEMENTS.md`.
- `ledger/thresholds.py` rompe con el feed `UKOIL.cash_M1` (OPEN #94). enc. 41:254.
- Equity de USDJPY: 0 de 3.732 reconstrucciones cuadran dentro de 1 $ (USA500: 97 %); el hueco coincide con la comisión de 5 $ por lote con posición abierta (`portfolio/common/construct/equity/paths.py`). DP:18; COU:104-107,197-201.
- Costes cambiados a mitad de un run (9-30): las patas del WFC con spread antiguo de USDJPY (0,65, ahora 0,49/0,59/1,16 por tramo): comprueba que los costes del proyecto son los actuales antes de cada run. OPEN #89 (578-598).
- `test_commission_segments`: el donante dice SizeBased 5.0 y las fichas PercentageBased 0.005 (apartado). X-7.

### Tests rojos o apartados que tocan código de 6-12

- Auditoría del 10-08: 265 tests, 249 ok, 9 fallan, 7 apartados. `test_sqx_live` (`KeyError: 'strategies'` en `sqx/projects/live.py:235`) y `test_variants` sin diagnosticar; `test_worker_lifecycle` puede ser bug real de `bin/sqx-worker.sh stop` desde otro cwd (la línea 386 ya hace `cd "$ROOT"`). OPEN #107; `OPEN.md:861-873`.
- `test_ui_criteria` y `test_ui_shell` fallan por `criteria-history.jsonl` con `dev.on`; `test_ui_criteria::test_state_write_stamp_freeze` por 11.5; `test_ui_gate::test_window_client_sends_token` (404 en vez de 403); `test_ui_workflow::test_project_knobs` por `run.symbol`. enc. 46:415-449; enc. 48:13-16.
- `tests/test_oracle_draws.py:228` hace `sys.exit` a nivel de módulo y rompe `pytest tests/`. `checks.py` falla en capas por `engines → studies` (`drift_term`) y por estado rojo de otra sesión. enc. 48:15.
- Referencias muertas a `Test_Calib` y `scratch/calib*`: `perf/inputs/construct.py:21` (`CLOSE_HARVEST`), `tests/test_progress_genetic.py:16`, `tests/test_portfolio_golden_current.py:18,33`, `ledger/backfill.py:121`, `ledger/README.md:20`, `tests/README.md:266`, `studies/transfer/crossTF/README.md:82`.
- Fixtures borrados el 10-06 (`test_ui_batch`, `test_autopilot_closing`, `test_mt5_start_check`, `test_portfolio_universe`): decisión X-1 del dueño. `test_portfolio_build` no concilia por reloj de feed (X-2): mismo problema de licencia MAE/MFE 0,73-0,97 < 0,99 que afecta a P8-14.
- El árbol de trabajo sin commitear impide al fixer arreglar los tests (X-3).

### Documentos que contradicen el código en 6-12 (verdad hoy entre paréntesis)

- R3: OPEN #91:548-552, EXP y C04 dicen Limbo ≥ 1,65 / Pasa ≥ 2,33, «H1 nunca pasa», «17 reglas», «R4b techo 75» (verdad: `criteria.yaml:85` 1,65 sin Limbo; 16 reglas, R4b retirada; el correcto es ESP + encargo 44).
- `dev` sample: OPEN #93:704 dice 5 (verdad: `sample: 3`, `at: ["8"]`).
- Suelo de operaciones: 10 (Build) / 35-20 (puerta) / memoria 35 / OPEN #93 «40-50».
- Fila 6 de `WORKFLOW.md:245`: «PF ≥ 1,20» y cita `calib_final/ab_build.md` borrado (verdad: `_study.yaml:44-45` PF 1,0).
- Fila 8 de `WORKFLOW.md`: «umbrales laxos» (verdad: 16 reglas del encargo 44, P.5 bis; el dossier 10-04 no las recoge).
- Dossieres de criterios 6-8 (`criterios-implementados-2026-10-12.md`, `criterios-implementados-2026-10-12.md`) sin aviso de que sus cifras no valen (enc. 42:139-142); el del 10-04 tiene secciones «PENDIENTE» (decisión 6 pasos 10 y 12, §7, §8, §9, §12).
- Estudios del paso 10: README y `config.yaml` de `crossmarket` dicen que no emite veredicto (verdad: emite `verdict.csv`); el README lista un `POSSIBLE_IMPROVEMENTS.md` borrado.
- README de `falsePositives`: dice que de los pasos 17-20 «no rule exists» (falso) y que los pasos 10, 12 y 14 «no se aplican» al mono (cierto: no hay modelo).
- Estado de la recomendación D2 del encargo 41 (Limbo ≥ 1,65, Pasa ≥ 2,33): superada por el encargo 44 (R3 ≥ 1,65 sin Limbo).
- `WORKFLOW.md:35` (paso 10) y `steps.md:16` sobre P7/`e_principal`.

### Cadena SQX y operativa que afecta a la medición

- `Project finished` aparece antes de que todo esté en disco; cada acción de SQX gasta ~27 s en arrancar y 90-230 s en exportar; workflow medido 230 → 159 min, ≈ 140 estimado tras dos arreglos «aplicado, sin medir junto». K `perf/autopilot-dead-time.md:6-13`; AS:7,174-189; TB:57-59,79.
- Si algún run rinde tiempos, registra cuál es el paso 8 (con `--smoke` no es un cribado).
- `cpu_s` del catálogo de `perf/` cuenta ahora el árbol de procesos: las filas ya medidas se corrigen al volver a medir. enc. 44:142-146.
- Los hechos «dato ausente» (`missing`) hoy dan Limbo salvo declaración de otra cosa; solo el paso 8 declara segmento (`oos1`); los pasos 10-16 no. P8-15; DP:213-236.

## Lista corta: lo primero que miraría

1. **`dev.on` encendido con `sample: 3`**: el recuento que llega al 10 no es el de la puerta; anota su estado siempre (P8-8, `criteria.yaml:3-8,52-56`).
2. **R3 en 1,65 sin Limbo en el código frente a 2,33 en la propuesta/Council**: no mezcles cifras; anota ambos (P8-1, `criteria.yaml:85`).
3. **Ninguna línea de 8-19 está congelada y no hay FPR ni potencia medidas** (T-1, `criteria.yaml:59`): cada recuento es provisional.
4. **El hecho `e_principal` de P7 sale vacío**: ninguna estrategia puede dar PASA en el 10 (enc. 46:17,40-41; OPEN #22).
5. **Cambio de identidad build → retest** (7-11 %): compara presencia build↔retest (enc. 44:41; IND:62-63,131-139).
6. **Hechos de `entryQuality`/`feedQuality` que no llegan al juez** (enc. 44:352-353; IND:47-48).
7. **Fase 2 de 11.7 nunca corrida en vivo y proyectos antiguos sin esas tareas → el 12 juzga «sin dato»** (enc. 47:157-158; Parte V).
8. **Cifras del paso 6 de una calibración borrada y suelo de operaciones con tres valores vivos** (P6-1, P6-2).
9. **Assert por operación abierta y cerrada en la misma barra** (`level1a.py:38`, `edgeCost/costs.py:48`; P8-12).
10. **Costes provisionales (XAUUSD, XAGUSD, UKOIL, USOIL) y spread de los 17 activos nuevos sin verificar por tramo** (WORKFLOW.md:33-34; OPEN #26; OPEN #93 713,730-732).
