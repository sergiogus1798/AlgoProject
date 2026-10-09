# 48 · Pasos 16.5 (fábrica de variantes y nube) y 17 (WFC): «¿elegir por el pasado sirve fuera?» — encargo autocontenido

> **Plan vivo.** El dueño entregó las dos propuestas el 2026-10-07 y cerró cuatro decisiones (§0).
> El Council (Feynman, Sócrates, Ada; 2026-10-07) revisó el criterio del 17: «construir como está
> escrito, calibrar antes de oos2». Cada agente actualiza su fila de la tabla al terminar.

| parte | qué | modelo | ficheros que posee | oleada | estado |
|---|---|---|---|---|---|
| E | el exceso compartido: por operación, por variante y ventana, y la serie diaria | Opus (estadística) | `engines/variants/excess.py` (nuevo), `engines/variants/README.md` (su fila), `tests/test_variant_excess.py` | 1 | **hecho 2026-10-07.** `per_trade(trades, bars, costs, span, drift, feed=None, drift_span=None)`, `per_year(excess, window)`, `daily(...)` con los mismos argumentos; el invariante Σ días = Σ operaciones es exacto con las cuatro derivas (la `d` incluida): la deriva de cada operación se reparte a partes iguales entre sus barras. **Pendiente de otros:** `mcRetest/neighbours/excess.py` no se tocó (su sesión cambia la llamada); `checks.py` falla en capas por `engines → studies` (`drift_term` vive en `studies/`): o se mueve a `engines/` o entra en `ALLOW`. Con `drift_span` que deja fuera el año de una operación, las derivas `b` y `d` no existen y `per_trade` se niega: W usa ahí `a` o `c`. |
| F | la fábrica: hipercubo latino, clases de parámetro, tamaño del lote, controles, operaciones de todas las variantes | Sonnet | `sqx/variants/**` salvo `neighbours.py`, `neighbourbatch.py` y la sección `neighbours:` de `config.yaml`; `studies/breakage/spp/run.py` (sólo claves añadidas al brief); `pipeline/autopilot/variants.py`; `tests/test_variants*.py`, `tests/test_autopilot_variants_order.py` | 1 | **hecho 2026-10-07** (sin SQX): brief con `class`/`plateau`, hipercubo `design/lhs.py`, `size` por ledger, estratos `lhs`/`origin`/`canary`/`inert`, cosecha sin suelo, `varianttrades.py` → `variant_trades.parquet` (autopiloto exporta y reúne antes del `clear`). A U: la sección `size` (era `minimum`); a D: capítulo de `varianttrades` |
| P | fontanería: extractor de hechos, sellado de oos2, composiciones y filtros del panel, claves de `criteria.yaml`, filas del ledger | Sonnet | `pipeline/autopilot/{facts.py,tail.py,criteria.yaml}` (sólo claves `"16.5"` y `"17"`), `engines/variants/{panel.py,look.py,config.yaml}`, `ledger/thresholds.yaml` (filas nuevas al final), `ledger/gate.py` (sólo una entrada nueva), `tests/test_autopilot_facts_batch.py`, `tests/test_variants_panel.py` | 1 | **hecha 2026-10-07**. Filtros en `engines/variants/filters.py` nuevo (panel.py ya rozaba las 250 líneas). Sello `gate.seal` (registro `AlgoData/ledger/wfc_calibration.json`: `criteria_sha256`, `abre`, `fecha`, `tasas`). `cut` del 17 decidido (dueño, 2026-10-07): `cut: null`, el 17 sólo anota; `judge.judge` evalúa y escribe veredicto y fila del ledger sin borrar en SQX (el databank que mira es el de `survivors.bank`). `gate.criteria_hash(step)` sella sólo la entrada `"17"` (json canónico `sort_keys`), no el fichero entero |
| W | el WFC nuevo: medida, nulo, estado, tres composiciones; traducción para el paso 20 | Opus (estadística) | `studies/optimisation/wfc/**`, `studies/closing/blindJoint/{pieces.py,readings.py}` (sólo la traducción), `tests/test_wfc*.py` | 2 | **hecho 2026-10-07; nivel con nulo propio añadido el mismo día** (decisión del dueño: `measure` publica `p_nivel`, `verdict/state.py` pide `p_nivel ≤ wfc.level_alpha` = 0,05 para PASA; top que gana sin superar el nulo = LIMBO) (sin SQX, sin oos2; la lectura real de `variant_trades.parquet` en `inputs/batch.py` no se ha ejecutado contra un lote: la valida V). Para C: todo el cálculo es puro sobre arrays — `measure.reading.measure(e_is, e_oos, days, years, cfg)` y `verdict.state.judge(measured, cfg)`; con un lote, `inputs.batch.read(work, symbol, timeframe, legs=("build", "oos1"))` y `one.composition((("build",), ("oos1",)), …)` no tocan oos2. Tasas en 300 familias sintéticas (`python3 tests/test_wfc_families.py`): sin ventaja, perverso 0,043 y positivo 0,050 (α 0,05) y **PASA 0,047** (era 0,47 antes del nulo del nivel). Preguntas abiertas al dueño: qué recuento de operaciones controla la ρ parcial (`order.partial` existe, sin publicar), y el número del «denominador casi nulo» de R_sel (provisional `level.r_sel_min_gap: 0.05`). Para U y P: ya no existen `estudios/wfc_<comp>.*`, `collected.json` ni los hechos `exceso_persistencia_*` / `mediana_ratio_Sharpe` (los nombran `pipeline/autopilot/offered.yaml`, `ui/text/columnhelp_criteria.py`, `ledger/blind.py:61-67`, `pipeline/recipe.yaml`). |
| N | la nube como mapa: Sobol sobre los vivos, R² ajustado y su referencia barajada; el autopiloto la lanza | Opus (estadística) | `studies/optimisation/cloud/**`, `pipeline/autopilot/variants.py` (sólo la llamada a la nube, tras F), `tests/test_cloud*.py` | 2 | **hecho 2026-10-07** (sin SQX, sin oos2). La nube lee `variant_trades.parquet` (sólo patas build y oos1, mercado `Main`), mide el exceso por año con `engines.variants.excess` y escribe `estudios/cloud.json` con `facts`: `vivos`, `coeficientes`, `variantes.{build,oos1}`, y por pata `r2_ajustado`, `r2_barajado`, `legible`, `sobol_primer.<p>`, `sobol_total.<p>`. Fuera A1, A3, B2, C1, `verdict/` y las filas `parameterCloud.{rank_high,plateau_low,rho_low}` y `variants.design`. El autopiloto la lanza al final del 16.5, por madre. **A U:** el estudio ya no tiene `run.symbol` (el activo y el timeframe salen del lote, `look.market`): quitar `--set run.symbol` de `ui/daemon/runner/optimisation.py:13` y `"cloud"` de `forproject.SET` (hoy `tests/test_ui_workflow.py::test_project_knobs` falla por eso), pedir `variant_trades.parquet` en `where.batch`, y añadir `cloud` a los estudios del paso 16.5 en `ui/daemon/workflow/steps.py` para que `facts.gather` recoja sus hechos; pestañas nuevas `build`, `oos1`, `variantes`; el resumen es `variants`, `live`, `r2_adj`, `r2_ref`, `legible`. **A D:** tarjeta de knowhow — una superficie ajustada a ruido puro reparte igualmente un ranking de Sobol (Σ primer orden ≈ 0,8, Σ total ≈ 1,2 en la prueba), y la referencia barajada del R² **ajustado** ronda 0,06 con 458 variantes y 105 coeficientes (el 0,23 de la propuesta es el R² sin ajustar); `marketSurfaces/measure/region.py:6-7` y dos tarjetas (`plateau-radius-degenerates-at-six-params`, `cloud-ranking-stability`) nombran módulos retirados en su texto; capítulo 39 del manual. Sin objetivo en `perf/`: no hay lote real con `variant_trades.parquet` hasta V. **Pregunta abierta (regla 11):** la lectura de oos1 usa la misma nube (sólo el suelo de dentro, 0 para quien no opera allí); ¿o debe llevar además el suelo de fuera de 10/año? |
| C | la calibración: familia sin ventaja y con ventaja plantada, ensayo en build → oos1, registro que abre el bloque ciego | Opus (estadística) | `studies/optimisation/wfc/calibrate/` (nuevo), `tests/test_wfc_calibrate.py`, su capítulo del manual | 3 | **hecho 2026-10-07; recalibrada con el nulo del nivel: `abre: true`** (falso PASA sin ventaja 0,02 ≤ 0,40; falso NO PASA con Sharpe 0,5 a 2,75 años 0,22 ≤ 0,25; el criterio anterior daba 0,49 y 0,22; tope renombrado `max_false_fail`; `oos2` sigue sin leerse; la columna «sin nulo» queda en el informe como comparación). Lo que sigue es el primer escrito, **superado**: `python3 -m studies.optimisation.wfc.calibrate` escribió `AlgoData/ledger/wfc_calibration.json` con **`abre: false`**: a 2,75 años el criterio escrito da falso PASA sin ventaja 0,49 (tope 0,40; es 0,5 × 0,95 por construcción, no baja con más familias) y PASA perdido con Sharpe 0,5 de 0,25 (tope 0,25). La alternativa con nulo en el nivel (p ≤ α, mismos sorteos) baja el falso PASA a 0,02 y sube el perdido a 0,80: **decide el dueño** (subir el tope, adoptar (b) o un α intermedio) y se recalibra; oos2 sigue sellado. Ensayo build → oos1: 0 lotes con `variant_trades.parquet` (rama probada con un lote sintético; lee `metrics.parquet` sin columnas de oos2 y no apunta miradas en el ledger: un lote no guarda su familia). **A V:** relanzar el comando cuando exista un lote. **A D:** capítulo 107 hecho; sin objetivo en `perf/` (20 min con 4 procesos junto a SQX); tarjetas de knowhow propuestas en el informe de cierre; el generador de familias vive ahora en `calibrate/families.py` y `tests/test_wfc_families.py` lo importa. **Preguntas al dueño:** las casillas de referencia de `abre` (2,75 años, Sharpe 0,5, la peor de con/sin orden) las fijé yo en `calibrate/config.yaml#reference`; y a dónde van en (b) las que dejan de pasar (LIMBO o NO PASA). |
| U | la ventana: vistas del WFC y de la nube, ayudas de columna, parámetros editables | Sonnet | `ui/**` (lo que nombre el WFC o la nube), `ui/daemon/sqxconfig/studies.py` | 3 | **hecho 2026-10-07** (sin SQX, sin oos2). Ventana: `sqxconfig/studies.py` (partes `size`, mapa `cloudcfg`, `calibcfg` si existe; toda clave del §2 editable salvo `variants.design`, que ya no es una opción: siempre hipercubo), `forproject`/`runner/optimisation` sin `run.symbol`, `where.batch` pide `variant_trades.parquet`, paso 16.5 con `cloud`, ayudas de columna nuevas, `LIMBO` en ámbar, recta de Spearman con ρ. **Abierto:** `n_target`/`strata` del SPP siguen visibles (el lote ya no los lee: ¿quitarlos?); `calibrate/tooltips.py` no existe, la ventana lleva frases de reserva. Tests ajenos que fallan: `test_ui_batch` (sin lote real), `test_ui_criteria`/`test_ui_shell` (`criteria-history.jsonl` con `dev.on`). |
| D | documentación y cierre: README, skill `variants`, WORKFLOW, manual, knowhow, `depmap` y `checks` | Sonnet | `studies/optimisation/{wfc,cloud}/README.md`, `sqx/variants/README.md`, `.claude/skills/variants/SKILL.md`, `.claude/skills/workflow-simple/steps.md`, `docs/AgentPDFs/WORKFLOW.md`, `AlgoData/manual-fuentes/`, `knowhow/`, `docs/DEPENDENCIES.md` | 4 | **hecho 2026-10-07** (sin SQX, sin oos2). READMEs de wfc, nube, `sqx/variants` y `design`; `POSSIBLE_IMPROVEMENTS.md` del WFC reescrito y el viejo (todo del CSCV) movido a `cscv/`; skill `variants` y `steps.md`; filas 16.5 y 17 de `WORKFLOW.md`; capítulos 18, 19 y 39 del manual (el 18 nombra `varianttrades`); siete tarjetas de knowhow; nota en OPEN.md #50 (parte V). `checks.py` 0 problemas. `tests/test_ui_results.py` falla por `studies/research/*` ausente del catálogo (anterior a hoy, no de este encargo) |
| V | **validación con datos reales**: un lote nuevo en SQX y el ensayo de C sobre él | — | — | — | espera al «adelante» del dueño: quema CPU en el custodio |

## Tu oficio

Eres el agente de **una** parte de la tabla (te la dice quien te despacha). Trabajas en
`~/Desktop/AlgoProject`, rama `master`, sin worktree ni commit (regla 12). Tocas sólo los ficheros de
tu fila. El modelo es el de tu fila (regla 17).

## Tu encargo

Dejar los pasos 16.5 y 17 como los describen las dos propuestas del dueño, con **todos sus números
como parámetros configurables** (§2) y con oos2 sellado hasta que el criterio esté escrito y calibrado.
Lo que el dueño recibe: por madre, un estado **PASA / LIMBO / NO PASA** del paso 17 que el piloto
juzga solo, y del 16.5 un lote y un mapa que no cortan nada.

## §0 De dónde sale

- Las propuestas, que **mandan** sobre este encargo donde difieran:
  `docs/AgentPDFs/criterios-paso-16.5-nube-propuesta.md` y
  `docs/AgentPDFs/criterios-paso-17-wfc-propuesta.md` (dueño, 2026-10-07). Léelas enteras antes de
  empezar: son cortas.
- Decisiones del dueño, 2026-10-07:
  1. Los cambios sin commit de `sqx/variants/` son base buena: se edita encima.
  2. La calibración (§10.2 de la propuesta del 17) **entra y bloquea**: el bloque ciego no lee oos2
     sin criterios escritos en `criteria.yaml` **y** una calibración registrada.
  3. El paso 20 **traduce** el estado: PASA = sin fallo, NO PASA = fallo, LIMBO = indeciso. El PASA
     es un veto levantado, no un voto a favor. No se rediseña el 20.
  4. La ventana se adapta en este mismo trabajo.
  5. **El nivel lleva su nulo de volteo (p ≤ 0,05) para PASA** (2026-10-07, tras la calibración: el
     criterio escrito daba PASA al 49 % de las familias sin ventaja). Misma `wfc.level_alpha` = 0,05
     en el ledger; los mismos sorteos que el orden.
  6. **Top que gana sin superar el nulo → LIMBO**, en cualquier orden; el top que no gana sigue
     siendo NO PASA. Los topes de la calibración pasan a ser falso PASA sin ventaja ≤ 0,40 y
     **falso NO PASA** con ventaja plantada ≤ 0,25 (`max_false_pass`, `max_false_fail`).
- Acordado con la sesión que programa los pasos 14 y 16 (`algoproject-ff`):
  - no se cambian las firmas de `engines/market/reprice.real`, de
    `studies/screening/analysis/tradelevel.drift_term`, de `pipeline/autopilot/closing.export` ni de
    `sqx.variants.execute` (parámetros opcionales nuevos sí);
  - `criteria.yaml`: sólo las claves `"16.5"` y `"17"`; las `"14"` y `"16"` son suyas;
  - el brief del SPP sólo **gana** claves.

## §1 Lo que ya se sabe del código (no lo vuelvas a buscar)

- El lote vive en `AlgoData/strategyPermutations/<proyecto>/<estrategia>/` (`core/datapaths.py:87`):
  `metrics.parquet`, `segments.parquet`, `equity.parquet`, `equity_markets.parquet`, y `trades.parquet`
  sólo de la madre (`sqx/variants/mothertrades.py:41-70`). **No hay operaciones por variante.**
- Leen el lote y no deben romperse: `studies/optimisation/cscv/report.py:113-121` (`param_*`),
  `studies/optimisation/marketSurfaces/inputs/surfaces.py:25-139` (`variant_id`, `param_*`,
  `result_key`, `trades`, `value`, `usable`), `studies/closing/blindJoint/inputs.py:93-102`. La
  columna `stratum` la leen `wfc/contract/wfc.py:144` y `sqx/variants/collect.py:135`: **se conserva**.
- El diseño de hoy: estratos en `sqx/variants/design/{strata,plan}.py`; el reparto y `n_target: 500`
  vienen del brief (`studies/breakage/spp/config.yaml:17-22`, `spp/run.py:128`).
- El brief (`spp/run.py:104-136`) lleva por parámetro `levels`, `center`, `plateau_width`,
  `is_shift`; **no** lleva el tramo de la meseta, aunque `spp/model/profile.py:57` lo calcula
  (`from`, `to`). Los patrones de desplazamiento están en `spp/config.yaml:39` (`grid.fixed`) y los
  aplica `spp/model/mapa.py:19` (`is_fixed`): es la única fuente, no se escribe otra.
- La exportación de operaciones de un lote ya existe: `pipeline/autopilot/closing.py:61`
  (`export(project, role, tag, banks)`), como la usa `pipeline/autopilot/neighbours.py:69`. Escribe
  en `AlgoData/raw/<P>/<databank>/<día>/<tag>/trades.parquet`.
- El exceso del paso 14: `studies/breakage/mcRetest/neighbours/excess.py:11`
  (`totals(trades, bars, costs, span, drift, feed=None)`), que compone `reprice.real` y `drift_term`
  con la ventana y la variante de `studies/screening/gate/config.yaml:57-64`.
- `pipeline/autopilot/facts.py:220-225` descarta lo que no es carpeta; el WFC escribe
  `<lote>/estudios/wfc*.json`. `ui/daemon/workflow/sources.py:60` es quien encuentra los resultados.
- El sellado: `engines/variants/look.py:32` → `ledger/gate.py:40,61`, que no hace nada sin
  `ALGO_AUTONOMOUS=1` (`core/assetdata.py:18-27`). `gate.allow` tiene otros nueve llamantes: no se
  cambia su comportamiento para ellos.
- El paso 20: `studies/closing/blindJoint/pieces.py:12,46` y `readings.py:15-19`.

## §2 Parámetros configurables

Cada número es una fila de `ledger/thresholds.yaml` (la escribe P, con `source`, `set_by: owner`,
`set_on: 2026-10-07`, `why`), leída en el `config.yaml` de su estudio como `ledger:<clave>`
(patrón de `parameterCloud.*`, `thresholds.yaml:47-63`), con su ayuda en `tooltips.py` y editable
desde la ventana (`ui/daemon/sqxconfig/studies.py:27-30`). Ningún número de la lista en el código.

| clave | valor | qué es |
|---|---|---|
| `variants.n_min` · `n_max` · `per_coefficient` | 1000 · 5000 · 8 | tamaño del lote: `min(n_max, max(n_min, per_coefficient × p))` |
| `variants.design` | `lhs` | hipercubo latino (la secuencia de Sobol queda como decisión abierta) |
| `wfc.floor_is_per_param` | 15 | operaciones dentro por parámetro vivo |
| `wfc.floor_oos_per_year` | 10 | operaciones fuera por año de la ventana |
| `wfc.min_variants` | 30 | por debajo, «sin dato» |
| `wfc.null_draws` | 2000 | sorteos del nulo de volteo |
| `wfc.null_block_days` | 1 | días por bloque del volteo (se anota además con 5) |
| `wfc.alpha` | 0,05 | corte de `p+` y `p-` |
| `wfc.rho_strong` | 0,30 | etiqueta «fuerte» |
| `wfc.top_share` | 0,20 | el top por exceso de dentro |
| `wfc.deciding` | `build+oos1__oos2` | la composición que decide |
| `wfc.seed` | 0 | semilla del nulo |
| `parameterCloud.shuffles` · `shuffle_percentile` | 200 · 95 | referencia barajada del R² ajustado |
| `parameterCloud.heatmap_pairs` | 4 | cuántos parámetros entran en los mapas de calor |
| `wfc.calibration.families` · `max_false_pass` · `max_false_fail` | 300 · 0,40 · 0,25 | calibración (los dos topes son del Council, provisionales: «Decisiones del dueño») |

## Parte E — el exceso compartido

Una sola función para los pasos 14, 16.5 y 17, en `engines/variants/excess.py`:

1. `per_trade(trades, bars, costs, span, drift, feed=None)`: lo que hoy hace
   `mcRetest/neighbours/excess.py`, movido aquí como envoltura de `reprice.real` + `drift_term`
   (sin tocar sus firmas). Deja `mcRetest/neighbours/excess.py` importándolo, sin cambiar su `totals`.
2. `per_year(excess, window)`: suma por variante y ventana, dividida por los años de la ventana.
3. `daily(trades, bars, ...)`: la serie `d[i, t]` de la propuesta del 17 §3 — ganancia del día menos
   deriva cobrada ese día por la posición abierta — como matriz variantes × días.
4. **Invariante probado:** para toda variante, `Σ_t d[i,t] == Σ_j exceso_j` en la ventana (tolerancia
   de céntimo). Si la variante de `drift_term` en uso no permite repartir por día de forma exacta,
   para y pregunta (regla 11); no aproximes en silencio.
5. Parámetro opcional `drift_span`: de qué barras sale la deriva. Por defecto las de la propia
   ventana (lo que dice la propuesta); W lo usa además con «sólo barras anteriores a oos2» para una
   anotación (fallo 4 del Council).

Contrato de entrada que comparte con F: `variant_trades.parquet` en la carpeta del lote, esquema de
operaciones `T` de `mothertrades.py` más `variant_id`, `leg` (`build`, `oos1`, `oos2`) y `market`.

## Parte F — la fábrica

1. **Brief:** añade al brief, por parámetro, `plateau: {from, to}` (ya calculado en
   `profile.py:57`) y `class`: `live`, `frozen` o `shift` (con `mapa.is_fixed`). Comprueba que el
   perfil sale **sólo del SPP IS** (build); si lee el OOS, para y dilo.
2. **Diseño:** un hipercubo latino (`scipy.stats.qmc.LatinHypercube`, con semilla) sobre los vivos,
   dentro de `[from, to]`; los enteros, al entero más cercano. Congelados y desplazamientos, fijos
   en el valor de la madre en **todas** las variantes. Sustituye a los estratos; `stratum` pasa a
   valer `lhs`, `origin` (la madre, `P00000`), `canary` o `inert`.
3. **Tamaño:** la fórmula de §2 con `k` = vivos. Deja de leer `n_target` y `strata` del brief (no
   los borres de `spp/config.yaml`: son de la otra sesión). Si se llega al tope, aviso en el
   manifiesto.
4. **Controles:** canarios y pares inertes se mantienen y siguen comprobándose en `collect.py`.
5. **Cosecha:** no descarta variantes por operaciones (fuera `wfc.min_trades_total` de
   `collect.py:100-102`; `usable` se sigue escribiendo, todo `True` salvo sin datos, para no romper
   `marketSurfaces`).
6. **Operaciones de todas las variantes:** tras el retest, `closing.export` con tag `variants` sobre
   las tres patas y los mercados, y un paso que las reúne en `variant_trades.parquet` (contrato de
   E). En `pipeline/autopilot/variants.py`, antes del `clear`.
7. No lances SQX: código y tests. Rule 5 no aplica (no se autora ningún proyecto).

## Parte P — fontanería

1. `facts.gather` lee también el resultado que es **fichero** (`estudios/<clave>.json`) y aplana sus
   hechos numéricos y de texto (17, 18 y 18.5). Los hechos del 17 se llaman `wfc.c1.*`, `wfc.c2.*`,
   `wfc.c3.*` (c1 = build+oos1 → oos2; c2 = build → oos1+oos2; c3 = build → oos2); el que juzga es
   `wfc.c1.estado` ∈ `pasa`, `limbo`, `no_pasa`. ρ, p y percentiles, **números**.
2. `tail.py:107-110`: al cerrar el bloque ciego, el 17 se **juzga** con su regla.
3. `criteria.yaml`: las claves `"16.5"` (`cut: null`, `rules: []`) y `"17"` (propuesta del 17 §6).
4. **Sellado dentro del estudio:** una entrada nueva (p. ej. `gate.seal(step, segment)`) que
   `look.admit` llama **siempre**, sin mirar `ALGO_AUTONOMOUS`: niega oos2 si el paso no está en
   `reserved_for`, si `criteria.yaml` no tiene regla para el paso, o si no hay calibración registrada
   (el registro lo define C: un fichero en `core.paths` del ledger con fecha y hash de
   `criteria.yaml`; tú lees su existencia y que el hash coincide). `gate.allow` no cambia.
5. `panel.py`: las tres composiciones con claves distintas (`c1`, `c2`, `c3`; fuera `build__oos1`
   sola); filtros de la propuesta del 17 §2 — fuera controles y duplicados exactos, suelos
   `15 × k` y `10/año`, y si la madre no cumple el suelo se avisa y no se aplica; devuelve además el
   recuento de variantes por filtro. Las tres composiciones se apuntan en el ledger como miradas.
   Los duplicados y el suelo de fuera leen oos2: van **después** del sello.
6. El nombre: `Strategy_10.11.484` (carpeta) frente a `Strategy 10.11.484` (databank) — una sola
   función de ida y vuelta, la de `blindJoint/pieces.py:24-28`, usada por `facts`.
7. Las filas de §2 en `ledger/thresholds.yaml`.

## Parte W — el WFC

Sobre E y P. Propuesta del 17, §3 a §8, tal cual:

1. `measure/`: ρ de Spearman de `e_IS` contra `e_OOS`; nulo de volteo por día con el mismo signo
   para todas las variantes y el lado de dentro fijo (vectorizado: una matriz de signos por la de
   `d`); `p+`, `p-`, p5 y p95; orden positivo / neutro / perverso; etiqueta «fuerte».
2. Nivel: mediana del exceso de fuera del top (≥ percentil 80 de dentro; se anota cuántas son).
3. `state(orden, nivel, n)`: **función pura** con la tabla de §6. Sólo la composición `c1`.
4. Anotado sin decidir (§7 de la propuesta) y, por el Council: `p` con bloques de 5 días, ρ parcial
   controlando el número de operaciones, nivel con la deriva de barras anteriores a oos2, y
   `R_sel` con guarda cuando el denominador es casi nulo (se escribe «sin dato», no un cociente
   enorme).
5. Se quita todo lo de §8 de la propuesta: Fisher y su veredicto, persistencia y
   `exceso_persistencia_*`, ratio de Sharpe, Pearson y pendiente, la composición `build → oos1`.
6. Contrato (`core/study`): pestaña con la tabla de las tres composiciones, la nube con sus
   cuadrantes y la recta de **Spearman**, recuento por filtro. Un coeficiente no se pinta como
   porcentaje.
7. Paso 20: `blindJoint/pieces.py` traduce `pasa` → sin fallo, `no_pasa` → fallo, `limbo` → indeciso.
8. Tests con familias sintéticas (sin SQX ni datos reales): sin ventaja → «perverso» ≤ α dentro del
   error de simulación; ventaja plantada con orden → positivo; todas ganan sin orden → neutro + PASA.

## Parte N — la nube

Propuesta del 16.5, §1, §3 y §4:

1. Fuera A1, A3, B2 y C1 (`model/neighbourhood.py`, lo local de `surrogate`, `measure/stability.py`,
   `measure/ensemble.py`, `verdict/call.py`) y sus pestañas.
2. Métrica: exceso por año en build (de E); en oos1 como lectura secundaria. **Nunca oos2**: la
   nube no pide esa pata (y `inputs/cloud.py:65-84` deja de depender de `ALGO_AUTONOMOUS`).
3. Superficie cuadrática sobre los vivos, Sobol de primer orden y total, mapas de calor de la
   mediana por celda para los pares de mayor índice total.
4. R² ajustado global y su referencia barajada; «legible» sólo si supera su percentil. Aviso si hay
   menos de `per_coefficient` variantes por coeficiente.
5. Hechos del informe (§4 de la propuesta). Sin regla.
6. `pipeline/autopilot/variants.py`: lanza la nube tras recoger el lote.

## Parte C — la calibración

1. `python3 -m studies.optimisation.wfc.calibrate`: (a) familias sintéticas sin ventaja y con
   ventaja plantada, con la dependencia entre variantes de un lote real; (b) el mismo criterio
   ensayado en `build → oos1` (tramos ya gastados) sobre los lotes que tengan
   `variant_trades.parquet`. Devuelve la tasa de cada casilla de la tabla de §6.
2. Escribe el **registro** que abre el bloque ciego (lo lee `gate.seal` de P): fecha, hash de
   `criteria.yaml`, tasas. Nunca lee oos2.
3. Si el falso PASA sin ventaja o el PASA perdido con ventaja plantada pasan de sus topes (§2), el
   registro se escribe con `abre: false` y el informe lo dice arriba. No cambies el criterio para
   que pase: es decisión del dueño.
4. Comando nuevo → capítulo del manual en la misma parte (`/manual-chapter`, regla 8).

## Parte U — la ventana

`ui/desktop/studypage/{wfclote.py,page.py}`, `ui/text/columnhelp_{criteria,verdicts,fields}.py`,
`ui/desktop/{detail.py,theme.py}`: quita lo que nombre las claves retiradas y pinta el estado nuevo,
la tabla de las tres composiciones y la nube con cuadrantes; la nube de parámetros sin las pestañas
quitadas y con el aviso «sin estructura distinguible del ruido». Los parámetros de §2, editables
(`ui/daemon/sqxconfig/studies.py`). Cierra con `/ui-shot` de las dos zonas.

## Parte D — documentación

README de los dos estudios y de la fábrica, la skill `variants`, `workflow-simple/steps.md`, las
filas 16.5 y 17 de `WORKFLOW.md`, los capítulos del manual que nombren lo retirado, y una tarjeta de
`knowhow/` por hecho no obvio que las otras partes dejaron anotado en su fila.

## Decisiones del dueño — pregúntalas (regla 11)

1. Los topes de la calibración (falso PASA ≤ 0,40; falso NO PASA ≤ 0,25) son del Council, no suyos.
2. Las madres de la corrida de referencia, cuya nube ya leyó oos2 sin anotarlo: ¿se rejuzgan con el
   criterio nuevo o se dan por quemadas?
3. Hipercubo latino o secuencia de Sobol; top del 20 % o del 10 %; métrica del mapa (exceso por año
   o Sharpe del exceso): las propuestas las dejan abiertas; aquí van como parámetro con el valor
   propuesto.
4. Cuántas variantes por mercado aleatorio (se decide en el 18.5).

## Lo que no tocas

El master. **oos2**: ningún agente de este encargo lo lee, ni para probar. SQX: nadie arranca un
worker (la parte V espera al dueño). Los ficheros de otra fila. Las claves `"14"` y `"16"` de
`criteria.yaml`, `plan.py`, `run.py`, `sqx/projects/**`, `assets/_build.yaml`, y
`sqx/variants/neighbours*.py`: son de la sesión de los pasos 14 y 16.

## Verificación

`python3 -m pytest tests/ -q -k "<lo de tu parte>"` con la salida pegada, y al final de cada parte
`python3 tools/depmap.py && python3 tools/checks.py`. W y C pegan además la tabla de tasas.

## Cómo cierras

Actualiza tu fila de la tabla (estado, fecha, lo que el siguiente necesita saber en dos líneas) y
devuelve: qué hiciste · qué verificaste, con la salida pegada · qué dejaste sin hacer y por qué ·
qué descubriste que merezca ir a `knowhow/` · la lista de ficheros cambiados. No hagas commit.
