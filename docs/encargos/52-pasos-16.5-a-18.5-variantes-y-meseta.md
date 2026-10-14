# 52 · Pasos 16.5 a 18.5: variantes, nube, WFC, superficies por mercado y meseta en el tiempo — plan que cruza sesiones

> **Plan vivo.** Consolida lo que quedaba por hacer de los encargos 48, 29 y 31 (2026-10-09). Cada
> sesión actualiza su fila al terminar y añade una línea a la Bitácora.

| frente | qué | modelo | depende de | estado |
|---|---|---|---|---|
| V | validar con un lote real: el ensayo `build → oos1` de la calibración del WFC y la lectura de los hechos reales | Sonnet (lanzar y leer) + Opus (leer las tasas) | el «adelante» del dueño si hay que fabricar un lote nuevo (quema CPU en el custodio) | **abierto.** Ya hay un lote real de tres madres (§V.0); falta el ensayo |
| Q | las preguntas abiertas del 16.5 y el 17 (ρ parcial, suelo de oos1, casillas de referencia, `n_target`/`strata`, madres quemadas) | Opus (decisión) | el dueño | **abierto**, sólo preguntas (sección «Decisiones del dueño») |
| M | meseta en el tiempo: ¿la región buena de parámetros es la misma en build, oos1 y oos2? (ex 29) | Opus (diseño y estadística) | Q-8 (oos2), V | **sin empezar** (primer paso: reescribir contra el código actual) |
| R | mapa mercado × parámetro de la ventaja sobre el mono (ex 31) | Opus (diseño y estadística) | M no; sí la medición del export (§R.1) | **sin empezar** (primer paso: reescribir contra el código actual) |

## Bitácora

- 2026-10-09 · Consolidado de los encargos 48 (el plan vivo de 16.5 y 17), 29 (meseta en el tiempo) y
  31 (mapa de ventaja sobre el mono). Del 48 sólo queda V y las preguntas; el 29 y el 31 no se habían
  empezado y están escritos contra el `marketSurfaces` anterior al 2026-10-07.

## Tu oficio

Eres el agente de **un** frente de la tabla (te lo dice quien te despacha). Trabajas en
`~/Desktop/AlgoProject`, rama `master`, sin worktree ni commit (regla 12). Modelo: el de tu fila
(regla 17). Python y estadística; SQX sólo en V, y sólo por la ruta de las reglas 3, 10, 18 y 19.

## Tu encargo

Cerrar la cadena de los pasos 16.5-18.5 con **datos reales** y decidir si sus dos ampliaciones
pendientes (la meseta entre tramos y el mapa contra el mono) merecen construirse. Lo que recibe el
dueño: (V) las tasas de falso PASA y falso NO PASA del criterio del 17 medidas en `build → oos1` sobre
lotes reales, junto a las de las familias sintéticas; (M, R) o bien una medida con su coste en
estrategias y su decisión, o bien «esto no ayuda» dicho sin rodeos.

## §0 De dónde sale

- **El 16.5 y el 17 (ex 48).** Las dos propuestas del dueño, 2026-10-07:
  `docs/AgentPDFs/criterios-implementados-2026-10-12.md` y
  `docs/AgentPDFs/criterios-implementados-2026-10-12.md`, y sus PDF de criterios
  `criterios-implementados-2026-10-12.pdf`, `criterios-implementados-2026-10-12.pdf`. El
  Council (Feynman, Sócrates, Ada; 2026-10-07): «construir como está escrito, calibrar antes de oos2».
- **Decisiones del dueño ya tomadas (2026-10-07), no se vuelven a preguntar:**
  1. Los cambios de `sqx/variants/` son base buena.
  2. La calibración **entra y bloquea**: el bloque ciego no lee oos2 sin criterios escritos en
     `criteria.yaml` **y** una calibración registrada.
  3. El paso 20 **traduce** el estado: PASA = sin fallo, NO PASA = fallo, LIMBO = indeciso; el PASA es
     un veto levantado, no un voto a favor. No se rediseña el 20.
  4. La ventana se adapta en el mismo trabajo.
  5. **El nivel lleva su nulo de volteo** (p ≤ `wfc.level_alpha` = 0,05) para PASA, tras ver que el
     criterio escrito daba PASA al 49 % de las familias sin ventaja.
  6. **Un top que gana sin superar el nulo → LIMBO**, en cualquier orden; el top que no gana sigue
     siendo NO PASA. Topes de la calibración: falso PASA sin ventaja ≤ 0,40 y falso NO PASA con ventaja
     plantada ≤ 0,25 (`max_false_pass`, `max_false_fail`; los números son del Council, ver Q-1).
  7. `cut: null` en el 17: sólo anota; `judge.judge` evalúa y escribe veredicto y fila del ledger sin
     borrar en SQX.
- **La meseta en el tiempo (ex 29).** Katz (p. 45): «la tolerancia de los parámetros no sirve para
  medir la robustez»; su contraejemplo (pp. 100-103) es una ruptura de volatilidad con los cien juegos
  de parámetros rentables dentro de muestra y ninguno fuera
  (`docs/AgentPDFs/ideas-de-internet-y-libros-2026-09-27.md` §1.3). El dueño, 2026-09-28:
  > *«Sería buena idea mirar las mesetas en periodos diferentes. Es decir, mirar si la posición y
  > forma de la meseta coinciden en el IS separado, en el oos1 separado y en el oos2 por separado.
  > Eso es un poco también aplicarlo a diferentes mercados y ver las mesetas allí.»*
- **El mapa contra el mono (ex 31).** Plugin WinRateEdge de StrategyQuant, guía *Parameter Sweeps and
  Multiple Testing* §6 (copia en
  `~/Downloads/codebase-strategy-vs-random-edge-testing-winrateedge-results-panel/`); su figura 3 es
  una rejilla de mercados por periodos de Donchian con la z de la entrada contra entradas al azar. El
  dueño, 2026-09-28: «apúntalo como encargo».

## Lo hecho (no se repite; dónde vive)

| bloque | dónde | cierre |
|---|---|---|
| E, exceso compartido (por operación, por variante y ventana, serie diaria; Σ días = Σ operaciones exacto) | `engines/variants/excess.py`, `tests/test_variant_excess.py` | 2026-10-07, commit `ca7dd56` |
| F, la fábrica: hipercubo latino, clases de parámetro `live/frozen/shift`, tamaño por ledger, estratos `lhs/origin/canary/inert`, cosecha sin suelo, operaciones de todas las variantes | `sqx/variants/design/lhs.py`, `sqx/variants/varianttrades.py` (→ `variant_trades.parquet`), `pipeline/autopilot/variants.py`, `tests/test_variants*.py`; manual 18 | 2026-10-07 |
| P, fontanería: hechos del 17 (`wfc.c1/c2/c3.*`), sello de oos2 (`gate.seal`), filtros, claves `"16.5"` y `"17"` de `criteria.yaml`, filas del ledger | `pipeline/autopilot/{facts,tail,criteria.yaml}`, `engines/variants/{panel,filters,look}.py`, `ledger/gate.py:86` (`seal`) y `:81` (`criteria_hash`), `ledger/thresholds.yaml` (`wfc.*`) | 2026-10-07 |
| W, el WFC nuevo: ρ de Spearman, nulo de volteo, nivel con nulo propio, tres composiciones, `state` pura, traducción para el paso 20 | `studies/optimisation/wfc/**` (`measure/`, `verdict/state.py`, `inputs/batch.py`), `studies/closing/blindJoint/{pieces,readings}.py`, `tests/test_wfc*.py`; manual 19 | 2026-10-07; tasas en 300 familias sintéticas: sin ventaja perverso 0,043 y positivo 0,050, PASA 0,047 (`python3 tests/test_wfc_families.py`) |
| N, la nube como mapa: superficie cuadrática sobre los vivos, Sobol, R² ajustado y su referencia barajada; el autopiloto la lanza | `studies/optimisation/cloud/**`, `tests/test_cloud_map.py`; manual 39 (`39-nube-de-parametros`) | 2026-10-07; nunca lee oos2 |
| C, la calibración: familias sin ventaja / con ventaja plantada y registro que abre el bloque ciego | `studies/optimisation/wfc/calibrate/`, `tests/test_wfc_calibrate.py`; manual 107; registro `AlgoData/ledger/wfc_calibration.{json,md}` | 2026-10-07: **`abre: true`** (falso PASA 0,02 ≤ 0,40; falso NO PASA 0,22 ≤ 0,25; sin el nulo del nivel daba 0,49 y 0,22). La tabla completa está en el `.md` del registro |
| U, la ventana: vistas del WFC y la nube, ayudas de columna, parámetros editables, `LIMBO` en ámbar | `ui/**`, `ui/daemon/sqxconfig/studies.py` | 2026-10-07 |
| D, documentación: READMEs, skill `variants`, `steps.md`, `WORKFLOW.md`, siete tarjetas de knowhow | `studies/optimisation/{wfc,cloud}/README.md`, `sqx/variants/README.md`, `.claude/skills/variants/SKILL.md` | 2026-10-07; `tools/checks.py` en verde |
| 18.5, superficies por mercado (reescrito el 2026-10-07): ρ de Spearman del orden entre mercados, nulo de volteo semanal, prima, potencia | `studies/optimisation/marketSurfaces/` (README al día), `tests/test_marketsurfaces.py`; manual `52-superficies-mercado` | 2026-10-07; ejecutado sobre los tres lotes de §V.0 el 2026-10-08 |

El sello es coherente a 2026-10-09: `ledger.gate.criteria_hash` de la entrada `"17"` de hoy coincide
con el `criteria_sha256` del registro (815e4960…). **No hace falta recalibrar** mientras no se toque
esa entrada de `criteria.yaml`; si se toca, hay que volver a correr `calibrate`.

## Parte V — validar con datos reales

### V.0 Estado del disco (comprobado 2026-10-09)

`~/Desktop/AlgoData/strategyPermutations/Test_USDJPY_M30_doubleROCLong_10k/` guarda **tres madres**
con `variant_trades.parquet` real (210-360 MB cada una, 2026-10-08): `Strategy_12.15.405`,
`Strategy_12.21.437`, `Strategy_3.25.298`. Las tres tienen `estudios/cloud.json`,
`marketSurfaces.json` y `verdict.csv`. `wfc.json` existe en las dos primeras (`call` = `limbo` con
ρ = 0,080 y `no_pasa` con ρ = −0,219, composición `c1`, fuera = oos2); la tercera no lo tiene.
El registro `wfc_calibration.json` dice `ensayo_build_oos1: {"lotes": [], "tasas": null}` (se escribió
el 2026-10-07, antes de que existieran los lotes): **el ensayo en tramos ya gastados está sin hacer**.
El README de `marketSurfaces` aún dice «no se ha ejecutado sobre un lote real»: ya se ejecutó; V corrige
esa línea.

### V.1 Qué hacer

1. **Antes de nada**: `python3 -m core.assets USDJPY` (regla 5, sólo informa) y comprobar con
   `ls -lt ~/Desktop/AlgoData/strategyPermutations/` que la carpeta es la del §V.0.
2. **El ensayo `build → oos1`** no necesita SQX: `python3 -m studies.optimisation.wfc.calibrate`
   (lee los lotes con `variant_trades.parquet`, usa `metrics.parquet` sin columnas de oos2 y no apunta
   miradas en el ledger; ruta: `studies/optimisation/wfc/calibrate/rehearsal.py:37` `one_batch`, `:71`
   `run`). Si `lotes` sigue vacío, la causa está en `rehearsal.py:21` `batches(root)`: arréglala en el
   código, no a mano. Tres madres dan tres puntos, no una tasa: el informe debe decir cuántas son y
   que con tres no se concluye.
3. **Cuánto cuesta leer un lote real**: tiempo y memoria de `studies.optimisation.cloud` y del WFC
   sobre `Strategy_3.25.298` (360 MB, el mayor), con `perf/` (`/perf`, `perf/README.md`). El `README` de `marketSurfaces` anota 18 s para 500
   variantes × 11 mercados × 620 semanas sintéticas, sin la lectura.
4. **Un lote nuevo con SQX** sólo si el dueño lo pide (su «adelante»): `/variants`, proyecto propio
   `Test_`/`Trade_`/`Research_` (reglas 6 y 10), por `bin/workflow.sh` (regla 19), custodio una tarea a
   la vez, espera con `/sqx-wait` (regla 18). La skill y `sqx/variants/README.md` mandan en el cómo.
5. Si el ensayo muestra tasas distintas de las sintéticas (falso PASA o falso NO PASA fuera de sus
   topes), **no cambies el criterio**: escribe la tasa y pregúntalo al dueño (Q-1). El registro
   ya dice `abre: true`; no lo reescribas a mano.

### V.2 Verificación

```
python3 -m pytest tests/test_wfc_calibrate.py tests/test_wfc_batch.py tests/test_cloud_map.py -q
python3 -m studies.optimisation.wfc.calibrate      # escribe AlgoData/ledger/wfc_calibration.{json,md}
```
Y el campo `ensayo_build_oos1.lotes` del registro con tres entradas. Nunca se lee oos2 en este frente.

## Parte M — la meseta en el tiempo (ex 29, sin empezar)

### M.0 Primer paso, obligatorio: reescribir contra el código actual

El encargo 29 se escribió el 2026-09-28 contra el `marketSurfaces` anterior. Desde el commit `ca7dd56`
(2026-10-07) **ya no vale**:

- No hay `measure/region.py` ni mapas de calor del beneficio neto. Las rejillas son el **rango
  percentil** (0 peor, 100 mejor) de la mediana de las variantes de cada celda
  (`marketSurfaces/contract/grids.py:19` `grid`, niveles `LEVELS = [20, 40, 60, 80]`), de **exceso
  bruto** por mercado, no beneficio neto ni deciles.
- «Los pares dejan de ser mercado contra mercado» ya no encaja: el estudio hoy mide
  ρ_m = Spearman(exceso bruto del principal, exceso bruto en m) y ρ̄ ponderada
  (`marketSurfaces/measure/order.py`), con nulo de volteo semanal (`engines.weekly.flip`), no con
  deciles ni `J` de solape.
- «Mismo `top_share`» sigue existiendo pero ahora es `marketSurfaces.top_share` del ledger y se aplica
  al **neto** del principal para la prima (README «What is measured»).
- «Ampliación del 52 del manual»: el capítulo es `52-superficies-mercado`.
- El cálculo de «la regla de meseta o borde» de `cloud` ya no existe tal cual: la nube es una
  superficie cuadrática + Sobol (`studies/optimisation/cloud/README.md`), no una regla de meseta.
- Las pestañas retiradas de la nube (A1, A3, B2, C1) y `inputs/cloud.py:65-84` ya no están.
  La parte B del 29 («tabla que acumula meseta o pico») pedía la lectura «meseta o pico» de `cloud.json`:
  **ese campo ya no existe**. Los hechos de la nube son `r2_ajustado`, `r2_barajado`, `legible`,
  `sobol_primer.*`, `sobol_total.*`. Hay que decidir qué hace de «meseta» hoy (Q-6).

### M.1 Qué mide la idea (para rescribirla)

Por cada par de tramos (`build`,`oos1`), (`build`,`oos2`), (`oos1`,`oos2`) en el mercado de la madre:
`rho` de Spearman del orden de las variantes; solape de las mejores (`J`) con su nulo por permutación;
**desplazamiento del centro** de la región buena en unidades de cada parámetro normalizado; **forma**
(área y si es una sola mancha); si **la madre cae dentro** de la región buena de cada tramo. Lo que ve
el dueño: las rejillas por par de parámetros, una por tramo, lado a lado y con la misma escala, y un
mapa de consenso de 0 a 3 tramos. **No elige parámetros**: el PDF del dueño prohíbe sustituir la madre
por el mejor clon.

Hueco que cubre: el WFC compara el orden de todas las variantes dentro contra fuera, la nube mira la
forma dentro de build y oos1, el 18.5 compara mercados. Nadie compara **tramos entre sí en el mismo
mercado**. Con el WFC `build+oos1 → oos2` del 17 ya decidiendo, hay que argumentar qué añade esto antes
de construirlo (Q-8 y la pregunta final de M.4).

### M.2 Parte B del 29: ¿predice la meseta?

Tabla que crece con cada madre que llega al paso 20 (lectura de meseta, consenso entre tramos, si
sobrevive al paso 20 y su resultado en oos2), una tabla de contingencia y la p exacta de Fisher.
Mientras haya pocas madres el informe dice cuántas hay y que todavía no se puede concluir, **sin
inventar un veredicto**. Si con suficientes madres la meseta no predice nada, la lectura de meseta es
decorativa, y eso también es un resultado. Hoy hay tres madres con lote (§V.0): sin material.

### M.3 La puerta de oos2

`assets/_policy.yaml` reserva oos2 para `WFC, CSCV, MarketSurfaces, WFM, ATRStop`, y el estudio
vive dentro de MarketSurfaces, así que la política lo permite. Pero el estudio hoy **no lee el oos2 del
mercado principal** nunca (README: «The main market's oos2 is never read by either reading»; `--oos2`
significa «el oos2 de los otros mercados», `report.py:77`). Leer oos2 del principal sería un cambio de
doctrina del estudio: **decisión explícita del dueño** (Q-8), no un detalle de la implementación.
Sin esa autorización, M sólo puede comparar (`build`, `oos1`). Si la hay: la mirada pasa por
`ledger.gate.seal` / `allow`, deja una fila por tramo leído, y el resultado **se retiene** hasta que
17, 18, 18.5 y 19 estén hechos (lectura conjunta y ciega del paso 20, `ledger.gate.allow_read`; la
ventana tampoco lo pinta antes).

### M.4 Verificación al construirla (si el dueño la aprueba)

1. Lote sintético con región que se desplaza una cantidad conocida entre tramos: el desplazamiento
   medido coincide; otro sin desplazamiento: `J` alto, desplazamiento ≈ 0.
2. Tramos barajados entre variantes: `J` cae al valor de azar.
3. Un test en el que la puerta niega oos2 y el módulo se para antes de abrir un fichero (como el del
   18.5 en `tests/test_marketsurfaces.py`).
4. Un lote real de §V.0, con su tiempo y su memoria.
5. Cierre: ampliar el capítulo `52-superficies-mercado` (con capturas reales, regla 8), la fila del
   18.5 en `docs/AgentPDFs/WORKFLOW.md`, tarjeta en `knowhow/research/`, `tools/depmap.py` y
   `tools/checks.py`. Y la pregunta que decide si se construye: **cada umbral con lo que gana y lo que
   cuesta en estrategias al lado**; «esto apenas ayuda» es una respuesta válida.

## Parte R — el mapa de ventaja sobre el mono (ex 31, sin empezar)

### R.0 Primer paso, obligatorio: reescribir contra el código actual

El 31 parte de «la mediana del beneficio neto de las variantes de cada celda» y de «un mapa de consenso»
(figura 3 del plugin). El 18.5 de hoy pinta **rangos percentiles del exceso bruto**
(`contract/grids.py`), el consenso entre mercados ya no es «cuántos mercados baten a su mono» sino la
ρ̄ del orden, y **nada de `marketSurfaces` importa `engines.nulls`** (se comprobó 2026-10-09; sólo
`engines.weekly`). El mono del 31 sería una dependencia nueva. Reescribe el encargo con eso delante;
la «z de la entrada contra entradas al azar» debe decidirse contra los peldaños de
`engines/nulls/README.md` y `studies/readings/monkey/README.md` (Q-7).

### R.1 Medir el coste ANTES de proponer nada

El mono necesita **las operaciones** de cada variante en cada mercado, con hora de entrada, salida y
tamaño. El lote guarda `equity_markets.parquet` (P&L diario) y, desde el 16.5 nuevo,
`variant_trades.parquet` (columnas `variant_id`, `leg`, `market`; esquema de
`sqx/variants/mothertrades.py`). **Compruebas si ese parquet ya trae los mercados adicionales**
(`market != "Main"`), porque en tal caso no hay que exportar nada. Si no los trae, `sqx.export`
exporta operaciones de un retest multimercado con la columna `Symbol` (`knowhow/export/`); el volumen
(≈ 5.000 variantes × 10 mercados) se mide con `perf/` sobre una muestra: tiempo y disco. Cualquier
export corre en un worker con la ruta de las reglas 1-3 y 10 (`/export`, `/sqx-wait`); ni lo lances sin
el «adelante».

### R.2 Qué se mide en cada celda (idea del 31, a reencajar)

La unidad es la variante en un mercado: p empírica y z del mono sobre sus operaciones; la celda resume
la mediana de z y la fracción con p bajo el umbral. **Por qué no la z del plugin**: compara tasas de
acierto con error binomial que trata cada operación como independiente; las operaciones se solapan y esa
z sobrestima la confianza. **Por qué no multiplicar p entre mercados**: 5 % × 5 % = 0,25 % sólo vale con
mercados independientes (US100/US500, USDJPY y cruces del yen no lo son): el informe cuenta cuántos
grupos independientes hay con la correlación de sus rendimientos. **Corrección por pruebas múltiples**:
Benjamini-Hochberg con `engines/inference/fdr.py` sobre todas las celdas (10 mercados × 30 celdas =
300 pruebas); una celda verde aislada entre grises es sospechosa aunque su p sea pequeña.

### R.3 Dónde va y cómo se verifica

Capa nueva de `studies/optimisation/marketSurfaces/` (una pestaña más con los ejes «Eje X»/«Eje Y»),
`marketSurfaces` importa el motor, nunca otro estudio; en paralelo con `fork` si es largo
(patrón de `crossmarket.report`, avance por orden de terminación, `OPEN.md` §47). Verificación:
(1) lote sintético con ventaja plantada en celdas y mercados conocidos: el mapa enciende esas y no las
otras; (2) lote sin ventaja (entrada aleatoria): la fracción de celdas verdes queda en la tasa de
descubrimientos falsos elegida; (3) en la celda de la madre y su mercado la p coincide con la de la
puerta si usan el mismo peldaño y estadística; (4) un lote real, con su tiempo y su memoria.
Cierre: capítulo `52-superficies-mercado`, fila del 18.5 en `WORKFLOW.md`, tarjeta de knowhow con el
coste del export, `tools/depmap.py` y `tools/checks.py`. Hereda la regla de oos2 del 18.5: pide la
puerta antes de abrir nada. Relacionado con el frente de monos y nulos (`53-monos-y-nulos.md`): no
dupliques allí lo que se haga aquí.

## Decisiones del dueño — pregúntalas (regla 11)

**Contestadas por el dueño (2026-10-14)** — lo que sigue manda sobre la lista de abajo:
- **52-0 → las partes M y R se borran.** Caen con ellas Q-6, Q-6b, Q-6c, Q-7a-e y Q-8 (oos2 sigue sellado).
- Q-1 → **los topes del WFC los fija el dueño**, con la cifra delante. Q-2 → **0,05 confirmado**. Q-3 → **suelo de dentro + suelo de fuera de 10/año**.
- Q-4 → **confirmadas** las referencias de `abre`. Q-5a → **quitar** `n_target` y `strata`. Q-5b → **dar por quemadas** las madres que ya leyeron oos2.
- Q-5c → **LHS y 20 %**, como hoy. Q-5d → **se decide en el 18.5**.


Cada una lleva su origen. Ninguna lleva valor por defecto.

**Del 16.5 y el 17 (ex 48):**

- **Q-1 (ex 48, §«Decisiones del dueño» 1).** Los topes de la calibración (falso PASA ≤ 0,40, falso NO
  PASA ≤ 0,25) son **del Council**, no suyos; `wfc.calibration.*` está como provisional. ¿Los fija él?
- **Q-2 (ex 48, fila W).** `wfc.r_sel_min_gap` = 0,05 (el denominador casi nulo de R_sel, se escribe «sin
  dato») es provisional en el ledger (`ledger/thresholds.yaml:1361`), no lo fijó el dueño. Y: ¿qué recuento
  de operaciones controla la ρ parcial (`order.partial` existe, sin publicar)?
- **Q-3 (ex 48, fila N).** La lectura de oos1 de la nube usa la misma nube (sólo el suelo de dentro, 0
  para quien no opera allí): ¿o debe llevar además el suelo de fuera de 10/año?
- **Q-4 (ex 48, fila C).** Las casillas de referencia de `abre` (2,75 años, Sharpe 0,5, la peor de
  con/sin orden; `studies/optimisation/wfc/calibrate/config.yaml#reference`) las puso el agente, no el
  dueño. ¿Las confirma? *(Ya decidido por el dueño, no se pregunta de nuevo: el LIMBO para un top que
  gana sin superar el nulo, 2026-10-07, ver §0.)*
- **Q-5a.** ¿Se **quitan** `n_target` y `strata` del SPP, que la
  ventana aún muestra y el lote ya no lee? (ex 48, fila U; `studies/breakage/spp/config.yaml:18-19` y
  `studies/breakage/spp/run.py:138`). Son de la otra sesión del 14 y el 16: coordinar antes de borrar.
- **Q-5b (ex 48, §«Decisiones» 2).** Las madres de la corrida de referencia cuya nube **ya leyó oos2**
  sin anotarlo: ¿se rejuzgan con el criterio nuevo o se dan por quemadas?
- **Q-5c (ex 48, §«Decisiones» 3).** Hipercubo latino o secuencia de Sobol; top del 20 % o del 10 %;
  métrica del mapa de la nube (exceso por año o Sharpe del exceso). Las propuestas las dejaron abiertas;
  hoy corren con el valor propuesto como parámetro (`wfc.top_share` = 0,20, `variants.design` = `lhs`).
- **Q-5d (ex 48, §«Decisiones» 4).** Cuántas variantes por mercado aleatorio: se decide en el 18.5.

**De la meseta en el tiempo (ex 29):**

- **Q-6 (ex 29, §6.2-6.3).** La métrica: el 29 proponía el beneficio neto por tramo (la misma del WFC y
  del 18.5) y preguntaba si añadir el factor de beneficio como segunda lectura. Hoy el 17 y el 18.5
  miden exceso (no beneficio neto): ¿qué métrica lee la meseta? Y el tamaño de la región buena:
  propuesta del decil superior (`top_share`); ¿otro?
- **Q-6b (ex 29, §6.4).** Tramos de distinta longitud (oos2 más corto que build): propuesta de comparar el
  orden, no el nivel, y que el informe diga la longitud de cada tramo. ¿De acuerdo?
- **Q-6c (ex 29, §4).** Sin la lectura «meseta o pico» de `cloud.json` (retirada): ¿qué la sustituye en
  la tabla de contingencia?
- **Q-8 (ex 29, §5/§6.1).** **¿Se autoriza leer oos2 del mercado principal en la comparación entre
  tramos?** Propuesta del 29: sí, porque es el tramo que más dice y la política lo reserva para este
  paso. Hoy el estudio no lo hace nunca. Sin una respuesta explícita, oos2 sigue sellado.

**Del mapa contra el mono (ex 31):**

- **Q-7a (ex 31, §4.1).** ¿Todo el lote o variantes representativas (p. ej. la mediana de cada celda) si
  exportar es caro? Depende de lo que mida R.1.
- **Q-7b (ex 31, §4.2).** El peldaño del mono. Propuesta: el que fija la huella de trading, frecuencia,
  duración y dirección, y sortea la entrada (aísla la entrada, que es lo que mide el plugin).
- **Q-7c (ex 31, §4.3).** La estadística: propuesta, la misma de la puerta, para que celda y estrategia se
  lean con el mismo número.
- **Q-7d (ex 31, §4.4).** El umbral de la celda verde y la tasa de descubrimientos falsos (van a
  `ledger/thresholds.yaml`).
- **Q-7e (ex 31, §4.5).** ¿Rejilla de un parámetro o de pares? Propuesta: pares, para que las dos capas se
  superpongan.

## Lo que sólo vivía en los encargos de origen

- **Dossier de la nube y del WFC**, por si hay que releer el porqué de un número: los PDF
  `criterios-implementados-2026-10-12`, `criterios-implementados-2026-10-12` y
  `criterios-implementados-2026-10-12` en `docs/AgentPDFs/`.
- **Acuerdos con la sesión de los pasos 14 y 16 (`algoproject-ff`), siguen valiendo:** no se cambian las
  firmas de `engines/market/reprice.real`, `studies/screening/analysis/tradelevel.drift_term`,
  `pipeline/autopilot/closing.export` ni `sqx.variants.execute` (parámetros opcionales nuevos, sí);
  `criteria.yaml`: sólo las claves `"16.5"` y `"17"`; el brief del SPP sólo **gana** claves.
- **Notas de integración de partes ya hechas que otros frentes necesitan:**
  `mcRetest/neighbours/excess.py` no se tocó (su sesión cambia la llamada); con un `drift_span` que deja
  fuera el año de una operación, las derivas `b` y `d` no existen y `per_trade` se niega (W usa `a` o `c`).
  Ya no existen `estudios/wfc_<comp>.*`, `collected.json` ni los hechos `exceso_persistencia_*` /
  `mediana_ratio_Sharpe`, aunque los nombran todavía `pipeline/autopilot/offered.yaml`,
  `ui/text/columnhelp_criteria.py`, `ledger/blind.py:61-67` y `pipeline/recipe.yaml`: son referencias
  muertas por limpiar (compruébalo con `grep -n` antes de borrar).
- **Dato medido** (card pendiente de confirmar en `knowhow/research/`): una superficie ajustada a
  ruido puro reparte igualmente un ranking de Sobol (Σ primer orden ≈ 0,8, Σ total ≈ 1,2); la referencia
  barajada del R² **ajustado** ronda 0,06 con 458 variantes y 105 coeficientes (el 0,23 de la propuesta
  era el R² sin ajustar). El hallazgo de la caja de meseta está en
  `knowhow/research/plateau-radius-degenerates-at-six-params.md`; el encargo 38 que la rehacía se
  descartó sin heredero y **no se resucita**.
- **Ventana de 3 lotes de USDJPY M30 `doubleROCLong`** (§V.0): es el único material real; las
  superficies por mercado del 2026-10-08 se midieron sobre él.

## Lo que no tocas

El master. **oos2**: ningún frente lo lee sin la autorización expresa del dueño para esa tarea (V no lo
necesita; M la necesita y se pide en Q-8). SQX: nadie arranca un worker sin el «adelante» (V.1.4); los
tres workers siguen las reglas 1-3. Las claves `"14"` y `"16"` de `criteria.yaml`, `sqx/projects/**`,
`assets/_build.yaml`, `sqx/variants/neighbours*.py` y el resto de la carpeta de los pasos 14 y 16.
**Antes de editar `sqx/variants/` o `pipeline/autopilot/`, `git status`**: otras sesiones tienen
cambios sin commit allí (hoy `sqx/variants/{make,scale,varianttrades}.py` y
`pipeline/autopilot/{closing,judge,plan,run,traded}.py`). No toques `criteria.yaml` entrada `"17"`
sin recalibrar (rompería el sello).

## Objetivo — un comando

V es el único frente con un criterio ejecutable; M y R están a la espera de las preguntas del dueño y
de la reescritura. Mientras no se respondan Q-6 a Q-8:

```
python3 -m pytest tests/test_wfc_calibrate.py tests/test_wfc_batch.py tests/test_cloud_map.py tests/test_marketsurfaces.py -q \
  && python3 -m studies.optimisation.wfc.calibrate \
  && python3 - <<'E'
import json,os
d=json.load(open(os.path.expanduser('~/Desktop/AlgoData/ledger/wfc_calibration.json')))
assert d['abre'] and d['tasas']['ensayo_build_oos1']['lotes'], 'ensayo build->oos1 sin lotes'
E
python3 tools/depmap.py && python3 tools/checks.py
```

Sólo cubre V. **Verificación (no se puede resumir en un comando)** para M y R: las respuestas del
dueño a Q-6/Q-7/Q-8 por escrito en esta Bitácora; el encargo reescrito contra el código actual
(M.0, R.0) con la lista de lo caducado; el coste medido del export (R.1); y, si se construyen,
las verificaciones de M.4 y R.3.

## Cómo cierras

Actualiza tu fila de la tabla (estado, fecha, lo que el siguiente necesita saber en dos líneas) y
añade una línea a la Bitácora. Devuelve: qué hiciste · qué verificaste, con la salida pegada · qué
dejaste sin hacer y por qué · qué descubriste que merezca ir a `knowhow/` · la lista de ficheros
cambiados y, como última línea, **¿Quieres hacer el commit?** (regla 12; stagea sólo los ficheros de
tu tarea, nunca `git add -A`).

/loop Lee docs/encargos/52-pasos-16.5-a-18.5-variantes-y-meseta.md y ejecútalo entero. Tras cada iteración corre el Objetivo; si sale 0, para el bucle; si no, arregla lo que falló y vuelve a correrlo.
