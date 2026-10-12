# 65 · Implementar el consenso de las cuatro opiniones sobre los criterios del workflow

**Qué es.** Plan **vivo**: los diez cambios de la lista «lo que cambia mañana» de
`docs/AgentPDFs/criterios-cuarta-opinion-2026-10-12.md:315` (consenso de los encargos 63 y 64, la
tercera y la cuarta opinión, §9 del dossier), convertidos en filas ejecutables. Donde este encargo y
los frentes de 63 o 64 tocan lo mismo (repreciador, `dev.on`, StepM en el 8), **manda este**.

**Para la sesión que lo retome.** Lee `CLAUDE.md`, la tabla de estado y **sólo la sección de la
primera fila que no esté ✅**. No replanifiques ni reabras lo decidido. Cada fila la ejecuta un
subagente (modelo en la tabla) con el brief «ejecuta la sección N de este encargo; lee
`CODESTYLE.md` y el `README.md` de la carpeta; no toques nada fuera de los ficheros que nombra; si
algo admite dos lecturas, para y dilo»; la sesión (Opus) verifica la entrega y **actualiza la fila
y la bitácora antes de lanzar la siguiente**. Regla 12: un solo árbol, `master`, sin commits por tu
cuenta. Regla 3: `.claude/skills/sqx-wait/preflight.sh` antes de tocar un worker.

## Estado (2026-10-12)

Estados: ⬜ sin empezar · 🟡 en curso · ✅ hecho (fecha y cifra de la verificación) · 🔴 espera al dueño o a otra fila.
Modelo: **S** = Sonnet · **H** = Haiku (regla 17). Opus sólo diseña y verifica.

| # | punto | bloque | modelo | depende de | estado |
|---|---|---|---|---|---|
| 1 | `dev` fuera; una medoide por grupo, ≤ 4 por lote | A | S | — | ✅ 2026-10-12: 180 tests de autopiloto, puerta y criterios en verde; el número vive sólo en `criteria.yaml`. Falta `/ui-shot` de Criterios (cierre A) |
| 2 | Top-up diario del mapa y botón «Proponer investigación» fuera | A | S | — | 🟡 2026-10-12: hecho salvo borrar `ui/daemon/research/direct.py` (huérfano; al subagente se le denegó el borrado: lo autoriza el dueño). `grep -c marketProfile` del script = 0 |
| 3 | `peor` del 20 fuera · 18.5 apagado · 18 y 14 a columnas | A | S | 1 (comparten `criteria.yaml`) | ✅ 2026-10-12: tests de cola, paso 14, vecinas y blindJoint en verde. Queda suelto: el StepM del 20 usa una semilla fija, no una por madre (va al cierre B, con la tabla de 5.4) |
| 4 | Paso 10: P3 sobre V0 + V2, signo por familia, controles negativos | A | S | 3 | ✅ 2026-10-12: tests de familia, signos, viaje, builder y ayuda en verde; tabla de 7 familias escrita por `core.assetwrite`; `workflow.sh simple` exige la familia |
| A✓ | Cierre de bloque: deriva documental, manual, dependencias | A | H | 1-4 | ✅ 2026-10-12: commit 899a5ac, en GitHub. `direct.py` borrado con el sí del dueño |
| 5.0 | Mono con las horas de la estrategia | B | S | — | ✅ 2026-10-12 — 82 tests; 65 → 98 sobre z ≥ 1,65 porque la sd de los monos baja a 0,91 (su media no se mueve) |
| 5.1 | Ledger: arreglo de `accumulated`, contador por celda, `seal` en el 8 | B | S | — | ✅ 2026-10-12 — 73 tests; el sello real (`python3 -m ledger.cells --seal`) se corre en B✓ |
| 5.2 | Paso 8: una z sobre el mono con horas, R3 por celda, reglas inertes a columnas | B | S | 5.0, 5.1 | ✅ 2026-10-12 — tests del 8, del autopiloto y de Criterios en verde; la regla por celda pasa por el diálogo sin tocarse |
| 5.3 | Paso 8: p por estrategia (fdr local) y corte p ≥ 0,15 | B | S | 5.2 | ✅ 2026-10-12 — `p_fdr` columna (4 tests); en el lote de USATEC p = 0 para todas: ninguna se separa de la nube |
| 5.4 | Tabla «R3 · StepM 5 · StepM 10 · BH 10», una vez, y corrida nula | B | S | 5.3 | 🟡 tabla ✅ 2026-10-12 (R3 173 · StepM 5 % 0 · StepM 10 % 0 · BH 10 % 0, de 7.822); corrida nula **parada por orden del dueño** a las 21:30 UTC del 12-10 (PID 319701, a 3 h 19 min, en «cadena, ventaja nula»): sin cifra; hay que relanzarla entera (~10 h, `TMPDIR` en AlgoData) cuando él lo diga |
| 6 | Lectura única de oos2 (17 + 19) | B | S | 5.0, 5.1; decisión D2 | ✅ 2026-10-12 — paso 19.5 cableado (38 tests); falta su fila en `WORKFLOW.md` (B✓) |
| 7 | Ficha de NIKKEI225 a 747 y lotes a 304 en suspenso | B | S | — | ✅ 2026-10-12 — sin cambio: el dueño deja `spread_is` en 304,11 (D9) |
| 8 | Repreciador < 1 % frente a SQX | B | S | — | ✅ 2026-10-12 con límites — EndTest arreglado, 18.5 de vuelta por madre (29 tests); XAUUSD/USA500 oos1 no cuadran (fill partido) y stop corto, objetivo y comisión en % siguen sin verificar → incidencia en `OPEN.md` (B✓) |
| B✓ | Cierre de bloque | B | H | 5-8 | 🟡 2026-10-12 — hecho salvo la corrida nula de 5.4 (en marcha): 100 tests, `checks.py` 0 problemas, sello puesto, #120 abierta, recorrido de la ventana 17 zonas y 0 excepciones; sin crítica de capturas |
| 9 | Build sintético de USATEC H1 ruptura, K = 5 | C | S | bloque B; custodio libre | ⬜ |
| 10 | Protocolo en vivo: Etapa A y SPRT de la fondeada | C | S | — | ✅ 2026-10-12 con un límite — `portfolio/funded/live/` (9 tests, `checks.py` 0 problemas); fronteras derivadas +14,4 / −11,2 R; operaciones del historial de la flota unidas por magic (`mt5/reconcile/register.csv`), R = P&L / pérdida media de SQX, fallos a `live_failures` de la ficha con `--anotar`. Sin probar contra una cuenta viva (`--firm`): sólo el CSV. `tests/test_mt5verify.py` sale con 6 fallos de Setup y filas ajenos a esta fila, sin mirar |
| C✓ | Cierre de bloque | C | H | 9-10 | ⬜ |

**Ritmo (dueño, 2026-10-12): por bloques.** Con A en ✅ ya se puede volver a correr el workflow; B y
C siguen después. Cada bloque acaba con su lista de ficheros y «¿Quieres hacer el commit?».

### Bitácora

- 2026-10-12 — encargo escrito desde el plan aprobado; filas 1 y 2 lanzadas en paralelo (no comparten fichero).
- 2026-10-12 — fila 2 entregada. Pendiente: borrar `ui/daemon/research/direct.py` (sin él `checks.py` da «no manual chapter»). `tests/test_ui_research.py` falla en `test_routes_read_the_real_profile` y `test_views_offscreen` por `/api/research/cell` sin `measures` (XAUUSD H4, datos reales del perfil): el diff de la fila no toca esa ruta; sin comprobar en árbol limpio.
- 2026-10-12 — D1 resuelta (tabla de 6 arquetipos) y D1b sin objeto: los `structural` ya estaban curados.
- 2026-10-12 — fila 1 cerrada. La medoide se elige sobre las barras de entrada de oos1; la puerta marca la de cada grupo y el juez (`judge.largest`) se queda con los N mayores de `criteria.yaml`. Fila 3 lanzada.
- 2026-10-12 — fila 3: 18.5 fuera de `tail.py` y de `PIECES`, 18 y 14 con `rules: []`, T2 y T3 borrados. Paró en (a) porque `drop` del 20 salía de `peor`, y en T1 por medida y tramo sin definir: resueltas como D4 y D5, relanzada.
- 2026-10-12 — fila 3 cerrada. Los dos hechos del 14 salen en la pestaña «Fragilidad» (`t1.oos1.percentil_madre`, `t1.ambas.dd_r_p99`); no hay ruta del 14 al 16.5 y no se inventó. Fila 4 lanzada.
- 2026-10-12 — fila 4: la z nueva (`z_conj_v0v2`) sólo agrupa los mercados `family` cuando la familia se conoce; las columnas antiguas no cambian. Restaurada la ayuda de dos campos de `marketSurfaces` en `ui/text/columnhelp_criteria.py` (faltaba desde 909d812). Cierre A adelantado; se repite tras D6-D7.
- 2026-10-12 — fila 4 cerrada con D6-D7. `workflow.sh simple <P> <SYMBOL> <TF> <side> <FAMILY> …`; el registro gana la columna `family` en la próxima escritura; un simple antiguo sin familia se recrea sin ella (`registry.check_family`).
- 2026-10-12 — `tests/test_ui_research.py` falla por datos, no por el encargo: `AlgoData/research/profiles/measures.csv` (reescrito hoy 07:07) trae 12 medidas que no están en `studies/research/marketProfile/config.yaml` y `familias.describe` (`familias.py:24`) lanza `StopIteration` desde `ui/daemon/research/views.py:66`. Decisión del dueño: darles entrada en el config o que `describe` tolere desconocidas.
- 2026-10-12 — bloque A comiteado (899a5ac) y subido. Dueño: las 12 medidas nuevas del perfil ganan entrada en `studies/research/marketProfile/config.yaml` (en curso). Bloque B arrancado: 5.0, 5.1 y 8 en paralelo (no comparten fichero); 7 espera a 5.1 (ledger).
- 2026-10-12 — ojo para la fila 9: otra sesión ya tiene `docs/encargos/58-mcpt-fabrica.md` y `assets/symbols/XAUUSD_SYN01.yaml` sin comitear. Antes de escribir `mcpt_fabrica`, leer el 58 y `ListAgents`: puede estar ya en marcha.
- 2026-10-12 — fila 5.0 entregada (`engines/nulls/windowed.py`, `gate/level3c.py`). Sobre el export de USATEC (169 vivas, 5.000 sorteos): `z_mono ≥ 1,65` pasa de 65 a 98 (63 en común, 2 fuera, 35 nuevas). Error de Monte Carlo de z con 5.000 sorteos ≈ 0,022; coste lineal, 169 estrategias × 1 M de sorteos ≈ 17 min → en 5.2 `monkey.draws` sube a 100.000 (error ≈ 0,005). Siguen con el mono uniforme: `falsePositives/model.py:62`, `blindJoint/benchmark.py:44`, `readings/monkey/one.py:42`, `crossTF/cells.py:82` — los dos primeros entran en 5.2/5.3; los otros dos, decisión pendiente.
- 2026-10-12 — diagnóstico de 5.0 (169 vivas, 5.000 sorteos, misma semilla): la media de los monos casi no cambia (Δ = −0,034 sd) y su sd baja a 0,91 de la uniforme; la z mediana va de 1,575 a 1,694. No hay patrón por hora en la nula (P/L medio por hora ruidoso y sin signo) y el coste no depende de la hora salvo el swap. Tres de las cinco que más ganan entran a las 2 h (18,7 % de las entradas del lote). 5.0 cerrada.
- 2026-10-12 — fila 5.1: `ledger/trials.py` (`extra or 0`) y `ledger/cells.py` (contador por celda, relleno hacia atrás de 171 proyectos; 44 juzgados). `generated` sale de las filas del paso 6 del ledger (`steprows.log_build`, «Strategies generated»): 135 proyectos antiguos no la tienen y no suman. El builder no se tocó (`sqx` sólo importa `core`): el contador se deriva del registro. 152 proyectos caen en familia `unknown` y 130 en dirección `unknown`. El sello del 8 paró: `ledger.gate.seal` sólo guarda tramos reservados y no hay hash sellado por celda → D8.
- 2026-10-12 — medidas del perfil: las 12 del scout y sus 16 textos de condición quedan en `config.yaml` y `familias_texto.yaml`; hacían falta los textos (9 de 12 fallaban sin ellos), no bastaba con llamar a `literature.extend()` en `views.py`. `extend()` salta los nombres que ya existen: 111 medidas, sin duplicados.
- 2026-10-12 — fila 7: `spread_is` de NIKKEI225 304,11 → 747 por `core.assetwrite.set_cost`. Sin tocar y a decidir (D9): `slippage_is` 106,44 (35 % de 304; sería 261,45), `spread_oos` 474,91 y `spread_oos2` 796,12 (0,0174 % del precio, de la familia del 304), el rango MC (la ficha lo da en múltiplos 0,5x-2x → 373,5-1.494; 607-747 sería 0,81x-1,0x) y los lotes: no existe marca «veredicto en suspenso» y no se inventó. Lotes con veredicto a 304: `Test_NIKKEI225_M30_simpleL_{ref,val,auto,live,fin}`, `Test_NIKKEI225_H1_aroonL_{cal6,mc1,mc1b,mc2,mc5}`, `Test_NIKKEI225_M30_volatilidad_wf3`, y `Trade_NIKKEI225_M30_volatilidadL` (de otra sesión). 5.2 lanzada.
- 2026-10-12 — decisiones D2, D8 y D9. Fila 7: `spread_is` devuelto a 304,11 con su `why` original por `core.assetwrite.set_cost` (la ficha queda igual que en HEAD). Fila 6 desbloqueada; sale cuando 5.2 suelte `criteria.yaml`.
- 2026-10-12 — fila 5.1 cerrada: `cells.seal()` y `cells.edits(celda)`; el sello vive en `AlgoData/ledger/cells/seal.json` y cada juicio del 8 deja su hash en `judgements.csv` (las filas del paso 8 del ledger no llevan nombre de proyecto). Sólo cuenta, no rechaza: una corrida con hash distinto del sellado se juzga igual y suma 1. **En B✓, tras 5.3: `python3 -m ledger.cells --seal`.**
- 2026-10-12 — fila 5.2: regla única `z del mono con horas, por celda` (`alpha: 0.05, per: cell, missing: fail`); el umbral lo pone `judge.per_cell` con `ledger.cells.batches_for`. El build de USATEC no lee oos1 (2012-01-19 a 2019-12-31; oos1 2020-2023). Siguen juzgando R1a, R1b, R2, la parte de ventaja sobre coste de R5c, R5d, calidad de datos, retraso, R6 y R7. `monkey.draws` 100.000 (error de z ≈ 0,005): 149 s para 169 estrategias; como R3 ya no corta en el nivel 1a (7.649 de 10.000 caían ahí), un lote de 10.000 puede costar ~2,4 h en el nivel 3c. Sobre las 169 del export: pasan 100 con B = 1, 22 con B = 2, 2 con B = 4. `falsePositives` y el benchmark de `blindJoint` ya usan el mono con horas.
- 2026-10-12 — fila 8: bug real, EndTest se repreciaba a la apertura de barra (USA500: 240 USD por variante → 0,27); pasa a `AT_PRICE`. Verificados contra SQX: cortos (47.610 ops USDJPY, 99,994 % a 0,02 USD), swap en puntos con noche triple, comisión SizeBased al centavo. Descuadre tras el arreglo: USDJPY 0,0 (filtrando `Symbol==feed`; el `variant_trades.parquet` del 10k es anterior a c443f1d y mezcla 16 símbolos bajo `Main`), DAX40 0,009, USATEC 0, NIKKEI oos2 0,001; **siguen fuera** XAUUSD oos1 0,28-0,59 y USA500 oos1 0,14-0,15 (SQX parte el fill entre los dos ticks que rodean el coste declarado: 0,2286 → 0,23 el 87 % y 0,22 el 13 %) y NIKKEI build 1,0 (la tarea corrió con ~5,2 puntos de coste ida y vuelta y la ficha dice 9,60: configuración, no repreciador). Sin verificar desde disco: salidas por objetivo, stop en cortos, comisión PercentageBased — haría falta un `Test_` USDJPY M30 de cortos. 18.5 no vuelve.
- 2026-10-12 — D10 (dueño): el descuadre se mide con tolerancia relativa — una variante cuadra si difiere de SQX menos que max(1 USD, 1 % de su neto) — y se lanza el `Test_` de cortos en el conductor para objetivo, stop en cortos y comisión en porcentaje.
- 2026-10-12 — fila 6: `python3 -m studies.optimisation.oos2Reading.report --project <P>`; 100.000 volteos, error de Monte Carlo publicado (`p_error_mc`); operaciones de oos2 de la madre desde su lote de variantes (las que ya lee el 20), sin tarea nueva de SQX; firma en `ledger.gate.seal` como paso 19 (la política sólo reserva oos2 a WFC/CSCV/WFM/BlindJoint/ATRStop); miradas en `extras.json` vía `cells.look_oos2` (una por proyecto; la 4.ª de una celda se niega, salida 3). Decisión mía: no se abre un paso 19.5 — el estudio corre dentro del 19 y su regla (`oos2Reading.z > 0`) es una más del 19; el benchmark compartido con el 20 pasa a `engines/nulls/` (una copia).
- 2026-10-12 — fila 5.3 parada (regla 11). El encargo 64 §4 describe otro modelo (posterior de μ por operación) y no fija estimadores. En el export de USATEC las z de las 10.000 reales tienen media 0,48 y sd 0,52 frente a sd 0,99 de los monos nulos: con la nula de los monos la p sale negativa o no monótona (0, 31-35 o 67 supervivientes según el estimador de π₀). Lectura mía: es un lote de estrategias correladas (un factor común con ρ ≈ 0,73 da justo esa nube), el caso de la nula empírica de Efron; se mide antes de preguntar.
- 2026-10-12 — 5.3 medida con la nula empírica sobre las 10.000 z: δ₀ ≈ 0,55, σ₀ ≈ 0,55, π₀ ≈ 1; sobre 1,645 hay 78 y la nube predice 196-266; p = 0 en toda la cola. Mezcla plantada (1.000 a +3σ₀): recupera 840 y deja pasar ~230 de 9.000 nulas. Decisiones D11-D13 anotadas. Fila 8: la tolerancia max(1 USD, 1 %) deja NIKKEI build en 0 (antes 1,0) y no mueve XAUUSD ni USA500. Pendiente de B✓: `docs/AgentPDFs/WORKFLOW.md` gana el 19.5 (tiene cambios de otra sesión; no se tocó).
- 2026-10-12 — fila 6 cerrada: `tail.py` añade `add("19.5", "oos2read")` y `judge("19.5")` tras el 19; salida 3 («solo vivo») y dato ausente = limbo, la cola sigue. El comando es por proyecto, así que no tiene botón en el runner por madre de la ventana.
- 2026-10-12 — fila 8 cerrada con límites. El `Test_USDJPY_M30_cortosReprice_leaseWeb` se creó y se retiró sin arrancar SQX: el simple corto no activa `StopLoss` ni `ProfitTarget` en el Build, no habría dado los casos. 18.5 vuelve por madre y en ejecución (`blind.skipped`: máximo de `descuadre_sqx` de c1..c3 en `wfc.json` < `wfc.sqx_gap_relative`; si no, o sin fichero, se salta con su frase y la madre queda en limbo). No vuelve a `blindJoint/pieces.py` (el 20 marca incompleta a la madre con una pieza ausente) ni se restaura la pasada previa de build+oos1 (corría antes de existir `wfc.json`): el 18.5 se juzga una vez, sobre build+oos1+oos2.
- 2026-10-12 — fila 5.3 cerrada: `engines/inference/localfdr.py` (nula empírica por MLE truncada en el 50 % central; fdr no creciente por máximo acumulado desde la derecha, para que una cola más ligera que la nube dé p = 0; < 500 z → p vacía). La puerta la ajusta sobre las z de todas las que llegan al nivel 3c y ordena por ella. Con las reglas nuevas llegan 6.754 de 10.000 de USATEC (antes 169), 127 con z ≥ 1,645; δ₀ = 0,623, σ₀ = 0,779, π₀ = 1; p = 0 en todas. Mezcla plantada: ≥ 800 de 1.000 con p ≥ 0,15 (otra semilla dio 797). Coste: la puerta entera a 5.000 monos, 1.000 s; a 100.000 son horas por lote de 10.000 — pendiente de que el dueño diga si quiere monos adaptativos (5.000 para todas, 100.000 cerca del umbral).
- 2026-10-12 — fila 5.4: tabla hecha sobre 7.822 estrategias con operaciones (209 semanas de exceso neto de oos1, 10.000 réplicas): SPA p = 0,74, t máxima 2,54; StepM y BH no dejan a ninguna. Dossier `docs/AgentPDFs/criterios-paso-08-corrida-nula-2026-10-12.md`. La corrida nula falló una vez por disco lleno en `/tmp` (el estudio guarda borradores allí: hay que lanzarla con `TMPDIR` en AlgoData) y se paró a las 4 h; relanzada entera y desatendida a 100.000 sorteos (~10 h, 2 h por población × 5; `falsePositives` no reanuda). Resultado: `tail -n 40 ~/Desktop/AlgoData/tmp_fp/null_run_2026-10-12.log` (embudo y Pass por regla de la nula y de las plantas 0,05/0,10/0,15; el intervalo binomial hay que calcularlo). Objetivo: ≤ 1,2 % de monos nulos supervivientes. **Quien retome: leer ese log, completar el dossier y cerrar la fila.**
- 2026-10-12 — sello del paso 8 puesto (`python3 -m ledger.cells --seal`): sha256 bc1e1b31…, 18:11 UTC. Ojo: si el dueño pide monos adaptativos o la fila 9 mueve el corte de `p_fdr`, `criteria.yaml` cambiará y las celdas sumarán una edición.
- 2026-10-12 — cierre de B. StepM del 20: no se cambia la semilla — es un remuestreo conjunto que comparte los días entre madres (`blindJoint/measure.py:43,96`, `bootstrap.seed`); los traders al azar ya llevan semilla por madre (`engines/nulls/simulate.py`). El recorrido de la ventana sólo mueve controles genéricos: el diálogo de la regla por celda, el 19.5 del raíl y la columna `p_fdr` no se han visto con `/ui-shot`. Pendiente del dueño: monos adaptativos sí/no. Siguiente: leer la corrida nula, cerrar 5.4, y bloque C (9: leer antes el encargo 58 y `ListAgents`; 10).

## Tu oficio

Eres quien lleva los criterios del workflow del papel al código. La sesión que orquesta es **Opus**
(decide, redacta briefs, verifica); cada fila la ejecuta un subagente **Sonnet**; los cierres de
bloque, **Haiku**.

## Tu encargo

Dejar el autopiloto juzgando como dice el consenso: lo que no discrimina deja de cortar, el paso 8
emite una probabilidad por estrategia con la multiplicidad contada por celda, oos2 se mira una vez,
y lo que se repreciaba sin cuadrar con SQX deja de contar hasta que cuadre. Lo que devuelve al
dueño: tras el bloque B, **la tasa de monos nulos que sobreviven al 8 (≤ 1,2 %) junto a la tasa de
paso de las plantas de 0,05 / 0,10 / 0,15 R** — el coste en estrategias al lado de la ganancia.

## §0 De dónde sale

- Dueño, 2026-10-12: «planee la implementación de todo lo que se ha decidido colectivamente para
  mejorar, y elimine todo lo que se vea como perjudicial»; «que escriba el plan como encargo con
  tabla de estado, porque son diez bloques y más de una sesión».
- El dossier: `docs/AgentPDFs/criterios-cuarta-opinion-2026-10-12.md` §9 (líneas 291-317), §10
  (319-342), §4.2 (fila 10), §8.4 (línea 284, el contador). Las cifras se usan sin recalcular.
- **Decidido por el dueño el 2026-10-12 (no se reabre):** el corte p ≥ 0,15 **se añade** a R3 ·
  paso 1 = top-up del mapa **y** botón «Proponer investigación» · primer build sintético en
  **USATEC H1 ruptura**, con permiso para importar las series en el master o donde haga falta · P3
  del 10 pasa ≥ 1,65, limbo entre 0 y 1,65, falla < 0 · R3 se queda en 1,65 corregido por celda ·
  **sin límites por capacidad de cómputo**: el número de monos, volteos y remuestreos lo fija la
  precisión; los 5.000 del consenso son suelo, y cada cifra lleva su error de Monte Carlo — «si has
  de poner algún mono con 1 millón de runs, lo pones». Ningún Builder ni nula se recorta para que
  quepa. (No deroga la regla 19: nada pesado **al lado** de un workflow.)

**Lo que la exploración corrigió del prompt de partida** (para que nadie lo busque dos veces):
el autopiloto no tiene paso 1 (`pipeline/autopilot/plan.py:90-92`); OPEN #26 está cerrado y es otro
asunto — el repreciador sin verificar está en `engines/market/reprice.py:85,181`; el `TypeError`
de `ledger/trials.py` sólo salta con `extra=None` (`:46,58`); el paso 20 está en
`criteria.yaml:305-314`; no existe ninguna medoide ni ningún «mono con horas» en el código; no
existe `mcpt_fabrica`.

## Bloque A — borrados y apagados

### 1 · `dev` fuera y medoides

- **Qué.** Se borra el bloque `dev` (`pipeline/autopilot/criteria.yaml:52-56`), el sorteo
  (`pipeline/autopilot/judge.py:174,197-203`) y el apaño del `on` en `settings()` (`judge.py:34-39`).
  En su lugar el paso 8 declara `medoids: 4`: de las vivas, agrupadas por `structure` (lo que ya
  hace `redundancia`, `studies/screening/gate/redundancy.py:37`), se toman los **4 grupos mayores**
  y de cada uno la **medoide por huella de operaciones**: la estrategia con mayor Jaccard medio de
  sus barras de entrada con el resto del grupo (empate: orden de nombre; grupo de una: ella). El
  resto se corta con la razón «no es la medoide de su grupo».
- **Ficheros.** `redundancy.py` (función `medoides`), `studies/screening/gate/many.py:33-36`
  (persistir `redundancia_grupo` y `medoide` en el scorecard), `judge.py`, `criteria.yaml`,
  `ui/daemon/criteria/read.py:177,215`, `ui/desktop/criteria/zone.py:99-116` (fuera el aviso de
  modo desarrollo).
- **Tests.** Adaptar `tests/test_autopilot_smoke.py:19`, `test_autopilot_zero.py:31,54`,
  `test_ui_criteria.py:105-106`; nuevo `tests/test_gate_medoid.py` de respuesta conocida (grupo de
  3 con huellas escritas a mano, más un empate).
- **Manual.** `80-autopiloto`, `29-puerta`, `95-app-criterios` en `AlgoData/manual-fuentes/`.
  Ventana tocada → `/ui-shot` de Criterios.

### 2 · Paso 1 apagado

- **Qué.** Fuera `python3 -m studies.research.marketProfile.report --top-up` de
  `bin/daily-literature-scout.sh:98` (el scout sigue buscando y extrayendo papers; las entradas
  esperan en cola sin medir, y el informe lo dice). Fuera el botón «Proponer investigación» y su
  endpoint (`ui/daemon/research/api.py:14`, `DIRECTOR`, y su vista en `ui/desktop/`). El mapa se
  regenera a mano al abrir una celda. La skill `/research-direct` y los agentes `researchDirector`,
  `ideaExpert`, `ideaReviewer` **no se borran**: quedan sin lanzador en la ventana.
- **Verificación.** El dry-run del script no nombra `marketProfile`; `/ui-shot` de Investigar sin
  excepciones; `tests/test_ui_*` de la zona en verde.
- **Manual.** `83-tablero-de-investigacion`, `84-app-investigar`, y el capítulo del scout.

### 3 · Cola: 14, 18, 18.5, 20

- **(a) `peor` del 20.** Fuera de `studies/closing/blindJoint/` (`config.yaml:40`,
  `readings.py:23,35,91`, `one.py:88`, `report.py:80`). StepM queda como diagnóstico con semilla
  por madre; la etiqueta REVISAR se queda. La regla del 20 (`criteria.yaml:313-314`,
  `blindJoint.verdict_csv.drop`) se conserva **sólo si no depende de `peor`**: compruébalo, y si
  depende, para y pregunta. Tests `test_blindjoint.py:173-195`, `test_autopilot_step20.py`. Manual
  `56-paso-20`.
- **(b) 18.5 apagado.** Fuera de `pipeline/autopilot/tail.py:8-9` (`BLOCK`, `SPLIT`) y de
  `blindJoint/pieces.py:12`, con un comentario que apunta a la fila 8 de este encargo (vuelve
  cuando `descuadre < wfc.sqx_gap_relative`, `ledger/thresholds.yaml:1291`). Sin interruptor nuevo.
  Tests `test_autopilot_tail.py:26-27,121-131`, `test_autopilot_blind_criteria.py`. Manual
  `52-superficies-mercado`.
- **(c) 18 a columna.** `rules: []` en `criteria.yaml:251-267` (mismo patrón que 11.5, 16 y 16.5:
  `judge.py:175-176`). Manual `25-cscv`.
- **(d) 14 a columna.** `rules: []` en `criteria.yaml:209-224`. T2
  (`mcRetest/measure/excess.py:58-77`) y T3 (`contract/retention.py:11-16`) se borran. T1
  (`neighbours/t1.py:36-60`) pasa a entregar dos hechos: el **percentil de la madre entre sus 500
  vecinas en oos1** y el **p99 del drawdown** (la dispersión que fija k), que el 16.5 enseña.
  Tests `test_autopilot_step14_rules.py`. Manual `32-mcretest`, `11-retest-mc`.

### 4 · Paso 10

- **Qué.** P3 (`criteria.yaml:150`) lee una z conjunta nueva sobre **V0 + V2**
  (`travel/rules.py:92-95,176-177`; hoy mezcla todo el tramo; las ventanas en `cells.py:12-48`):
  pasa ≥ 1,65, limbo ≥ 0. P4 (`z_conj_v2`, contenida ya en P3) pasa a columna. Los mercados de
  control negativo (D1) pasan con z ≤ 0, y P8 (`criteria.yaml:165-168`, `worse()`) cuenta para
  ellos los que salen ≥ +1,65 en vez de ≤ −1,65.
- **Signo esperado.** La tabla de D1, en `assets/_markets.yaml`, escrita por
  `core/assetwrite/markets.py` y leída por `core/assetdata.py:225` — nunca a mano.
- **Tests.** `test_crossmarket_step10_rules.py:36`, `test_crossmarket_travel*.py`,
  `test_crossmarket_contract.py`. Manual `05-retest-mercados`, `30-crossmarket`,
  `39-crossmarket-lote`.

### A✓ · Cierre (Haiku)

Deriva documental que la exploración encontró y que se corrige aquí: `pipeline/autopilot/README.md:11`
(«keep 5»), `.claude/skills/workflow-simple/steps.md:35,44`, el comentario de `judge.py:141-142`,
`criteria.yaml:255-256`, `pipeline/autopilot/survivors.py:14` (`"21"` sin entrada en el YAML: se
anota, no se decide). Luego `python3 tools/depmap.py && python3 tools/checks.py`,
`python3 tools/manual.py`, `graphify update .`.

## Bloque B — la estadística

### 5.0 · Mono con horas

Los monos sortean la entrada sólo en las horas en que entra la estrategia (su histograma de hora de
entrada), sobre la máscara de sesión que ya existe (`engines/market/feed/session.py`). Va en
`engines/nulls/` (la decisión está escrita en `engines/nulls/README.md:117`);
`studies/screening/gate/level3c.py:47-49` lo usa. **Sustituye** al uniforme. Test de respuesta
conocida: una estrategia que sólo entra a las 15 h produce monos que sólo entran a las 15 h.

### 5.1 · Ledger

- `ledger/trials.py:46,58`: `extra = extra or 0`.
- **Contador por celda** (activo × TF × dirección × familia; `ledger/study.py:21` no lleva
  dirección: se añade). Seis enteros: plantillas probadas, lotes construidos, generadas
  acumuladas, cribadas en oos1, ediciones de `criteria.yaml` desde el último sello, miradas a oos2.
  Lo escriben `sqx/projects/builder.py` al crear y `judge.py` al juzgar; un `Test_` cuenta igual
  que un `Trade_`. Se rellena hacia atrás desde `AlgoData/projects/registry.csv`.
- `ledger/gate.py:30,86-123`: `seal` cubre el 8 con el hash de `criteria.yaml` por corrida; una
  corrida cuyo hash difiere del sellado no cuenta para la celda.

### 5.2 · Paso 8, una z

Una sola regla juzga: la z de la estrategia sobre su mono con horas ≥ **Φ⁻¹(1 − 0,05/B)**, B =
lotes cribados en oos1 en la celda (1,65 con B = 1; 1,96 con 2; 2,24 con 4). Sustituye como jueces
a R3, R5c-t y z_mono. R4a, R5, R5b, R8 y R9b dejan de juzgar y quedan como columnas
(`criteria.yaml:79-126`). El orden por t dentro de oos1 no se usa en ningún sitio. El número de
monos se sube hasta que el error de Monte Carlo en la cola Φ⁻¹(1 − 0,05/B) no mueva el veredicto, y
se declara. **Antes de tocar:** `sqx/inspect/dump_project.py` sobre el proyecto de USATEC para
confirmar que el paso 6 no lee oos1 (si lo lee, para y pregunta: el 8 iría a oos2).

### 5.3 · Paso 8, p por estrategia

Módulo `engines/inference/localfdr.py` junto a `fdr.py`: mezcla de dos grupos con F₀ = las z de los
monos nulos de `studies/screening/falsePositives` (`hechos_monos.parquet`; 5.000 como suelo);
p = 1 − π₀·f₀(z)/f(z). El 8 la emite, **corta en p ≥ 0,15 además de 5.2** y ordena por p. El método
fino lo fija `docs/encargos/64-…md` §4: léelo y, si no lo determina, para y pregunta (regla 11).
Test de respuesta conocida con una mezcla sintética de proporción conocida.

### 5.4 · Tabla y corrida nula

- La tabla «R3 solo · StepM 5 % · StepM 10 % · BH 10 %» (encargo 64 §3) con
  `engines/inference/snooping/superior.py` y `engines/inference/fdr.py`, **una vez**, sobre el
  export de USATEC; a `docs/AgentPDFs/` con `/dossier-pdf`. Documenta, no elige corte.
- **Corrida nula:** `python3 -m studies.screening.falsePositives.report` sobre
  `AlgoData/reports/Test_USATEC_H1_ruptura_leaseWeb/Results/2026-10-11/gate/` — **≤ 1,2 % de monos
  nulos supervivientes**, con la tasa de paso de las plantas al lado. Sin nada pesado en paralelo.
- Manual: `29-puerta`, el capítulo de `falsePositives`, `80-autopiloto`.

### 6 · Lectura única de oos2 — 🔴 espera a D2

Estudio nuevo con `/new-study`: suma semanal del exceso neto de la madre contra su mono con horas;
nula de volteos centrados (`engines/weekly/flip.py`; 5.000 como suelo), una cola, α 0,05. Corta
**sólo por signo** (z ≤ 0); el nivel ordena las medoides. Una mirada por celda, sellada con
`ledger.gate.seal` y sumada al contador de 5.1; celda con > 3 miradas → etiqueta «solo vivo» y no
se lee. Las reglas actuales de 17 y 19 (`criteria.yaml:234-250,287-305`) pasan a `rules: []`.

### 7 · NIKKEI225

`python3 -m core.assets NIKKEI225` (regla 5), luego
`core.assetwrite.set_cost("NIKKEI225", "spread_is", 747.0, "<por qué>")`
(`core/assetwrite/__init__.py:74`) y el rango de MC Retest a 607-747; informa de los demás tramos
sin tocarlos. Los lotes construidos a 304 quedan marcados «veredicto en suspenso» en el ledger
hasta repreciarlos con el repreciador verificado (fila 8). `Trade_NIKKEI225_M30_volatilidadL` es de
otra sesión: el proyecto no se toca.

### 8 · Repreciador

`engines/market/reprice.py`: cerrar los «UNVERIFIED» (cortos y salidas por objetivo, comisión ≠ 0,
swap en puntos; `:85,181`, `knowhow/research/monkey-reprice-audit.md`) contra operaciones
exportadas por SQX, hasta `descuadre_sqx < 0,01` (`studies/optimisation/wfc/one.py:144-148`; hoy
0,59-0,87). Si no hay export con cortos + comisión + swap, un `Test_` pequeño en el conductor que
lo dé, retirado al acabar (reglas 6 y 10). `tests/test_reprice.py` gana los casos dorados. Al
cerrar: 18.5 vuelve a `tail.py`, y 14, 16.5 y 18 vuelven a contar. Incidencia nueva en `OPEN.md`
(la cita a #26 del dossier es vieja); carta en `knowhow/research/`.

## Bloque C — fábrica y vivo

### 9 · Build sintético, USATEC H1 ruptura, K = 5

Módulo `mcpt_fabrica` según `docs/AgentPDFs/criterios-mcpt-fabrica-propuesta-2026-10-12.md` (§2.2
generador por volteo de signo sobre la deriva anual; §4; sus fases F0-F4): cinco series
`USATEC_SYN01..05`, mismas sesiones, huso y costes; semillas `SeedSequence(root).spawn(5)`; fichas
copiadas por `core.assetwrite`; un proyecto `Test_USATEC_H1_ruptura_SYNkk_leaseWeb` por serie con
`sqx/projects/builder.py`, **misma configuración y mismo criterio de parada que el real** (no se
recorta; lo que tarde se mide y va a `perf/`). Custodio, un job cada vez, `/sqx-wait`, sin workflow
al lado. Importación de datos (permiso del dueño, 2026-10-12): `preflight.sh` antes, snapshot de
`user/projects` (regla 1), y en el master **sólo con su GUI cerrado** (regla 2) — si está abierto,
se avisa y se espera. Sale: FDR por etapa con su IC y veredicto PASA (FDR ≤ 0,2 e IC90 ≤ 0,5) /
NO PASA (≥ 0,5) / LIMBO (K → 10). Los `Test_` se retiran al acabar. Capítulo nuevo del manual.

### 10 · Protocolo en vivo

En `portfolio/funded/`, junto a `decide/` y `sim/`:

- **Etapa A.** Lee las filas 1, 2, 3a y 5 del paso 26 (`mt5/verify/judge.py:97-115`; umbrales en
  `ledger/thresholds.yaml:1041-1097`) sobre 30 operaciones reales: emparejadas ≥ 0,95 (sólo
  aviso), diferencia media ≤ 0,05 R, correlación diaria ≥ 0,95, drawdown relativo ≤ 0,10. Una fila
  que falla saca a la estrategia y anota la causa en la ficha del activo.
- **SPRT de la fondeada.** Sigue mientras −11,2 R < S_n − 0,05·n < +14,4 R (μ₁ 0,10, σ 0,706,
  ln A 2,89, ln B −2,25); frontera alta → k a 1,5 %; frontera baja → retirar y sustituir por otra
  medoide de la celda. Umbrales al final de su sección en `ledger/thresholds.yaml`. Test de
  respuesta conocida: secuencias escritas a mano que cruzan cada frontera.
- Un comando con su capítulo del manual. **Las cuentas las abre el dueño.**

## Decisiones del dueño — pregúntalas (regla 11)

- **D1 (bloquea la fila 4) — la tabla de signo esperado.** El consenso dice «7 filas, por familia»;
  la biblioteca tiene **6 arquetipos** (`AlgoData/templates/registry.csv`: trendFollowing 16,
  volatility 16, meanReversion 12, momentum 10, session 5, pattern 2). Dos cosas a decidir:
  (a) ¿la séptima fila es `breakout` separada de `volatility`, o son 6? (b) el signo de cada fila.
  **Resuelta (dueño, 2026-10-12): son 6 filas, una por arquetipo, con esta tabla:**

  | familia de la idea | mercados `family` | mercados `structural` |
  |---|---|---|
  | volatility / ruptura | + | control negativo (pasa con z ≤ 0) |
  | meanReversion | + | control negativo |
  | session | + | control negativo |
  | trendFollowing | + | sin signo (no juzga: la tendencia viaja entre clases) |
  | momentum | + | sin signo |
  | pattern | + | sin signo |

  **D1b — sin objeto (comprobado el 2026-10-12).** Los 29 activos de `assets/_markets.yaml` ya
  tienen `structural` curado por el dueño el 2026-10-02 (reglas en `:49-62`); el comentario de
  `:40-47` que habla de 16 vacíos está viejo. No hay nada que curar: la fila 4 usa las listas
  que hay. Escritor, si hiciera falta: `core.assetwrite.set_market` (`core/assetwrite/markets.py:36`).
- **D2 (bloquea la fila 6) — a medio resolver.** A «¿qué pasa con las tareas de SQX del 17 y del 19?»
  el dueño contestó el 2026-10-12: **«Siguen corriendo y se siguen usando para el veredicto»**. Las
  tareas de SQX, pues, no se apagan. Queda una lectura doble que se le pregunta **antes de lanzar la
  fila 6**: (a) sus datos alimentan la lectura única y es esa lectura la que juzga (lo que dice el
  consenso), o (b) las reglas actuales de 17 y 19 (`criteria.yaml:234-250,287-305`) siguen juzgando
  además de la lectura única — lo que reabre la fila «cola 17-20» de §9. Hasta su respuesta, la
  sección 6 **no** pone esas reglas a `rules: []`.
- **D4 — resuelta (dueño, 2026-10-12).** Sin `peor`, en el paso 20 **no descarta nadie**: `pieces: null`, todo MANTENER; StepM de diagnóstico y etiqueta REVISAR. En la cola sólo corta la lectura única de oos2 (fila 6).
- **D5 — resuelta (dueño, 2026-10-12).** Las dos cifras del 14: percentil de la madre entre sus vecinas en oos1 **del exceso neto de deriva**; p99 del **drawdown máximo de cada vecina sobre build + oos1, en R**.
- **D6 — resuelta (dueño, 2026-10-12).** Las «7 familias» del consenso son las de `studies/research/memory/config.yaml`; la tabla gana la séptima fila `breakout` (ruptura), con `structural` como controles negativos.
- **D7 — resuelta (dueño, 2026-10-12).** Un proyecto sin plantilla lleva su familia como **argumento obligatorio** de `bin/workflow.sh simple`, guardada en `AlgoData/projects/registry.csv`; si falta, se pregunta. Los ya creados sin ella se juzgan en el 10 como antes.
- **D3 (al llegar a 7).** Si existe export de `Trade_NIKKEI225_M30_volatilidadL` construido a 304,
  ¿se reprecia en Python cuando la fila 8 cierre, o se reconstruye a 747?
- **D2 — resuelta (dueño, 2026-10-12).** Las reglas actuales del 17 y del 19 **siguen juzgando** y la lectura
  única de oos2 corta además: pasa quien supera las tres. No pasan a `rules: []`.
- **D8 — resuelta (dueño, 2026-10-12).** El primer sello del paso 8 se pone **al cerrar el bloque B**: el hash de
  `criteria.yaml` que quede tras 5.3 sella todas las celdas de golpe; desde ahí cada hash distinto con que se
  juzgue una celda suma 1 a sus ediciones.
- **D9 — resuelta (dueño, 2026-10-12).** NIKKEI225 **se queda en 304,11**: «devuelve el spread a los 304 que había».
  El 747 del consenso no se aplica, ni el rango MC 607-747; ningún lote queda en suspenso (la lista de los
  construidos a 304 está en la bitácora, por si se reabre). D3 queda sin objeto.
- **D10 — resuelta (dueño, 2026-10-12), y corregida.** La tolerancia relativa ya existía (`wfc.sqx_gap_relative`, 1 USD + 1 % del
  neto); pasa a max(1 USD, 1 %). No cierra la brecha: ver D13. El `Test_` de cortos sale con familia momentum, stop y
  objetivo los del builder y sin tarea de comisión en porcentaje.
- **D11 — resuelta (dueño, 2026-10-12).** La p del paso 8 se calcula con la **nula empírica del lote** (Efron), se enseña y
  ordena, y **no corta** hasta que la fila 9 diga cuánto del desplazamiento común del lote es ventaja real. Sustituye
  a «el corte p ≥ 0,15 se añade a R3». En el lote de USATEC ese corte dejaba 0 supervivientes.
- **D12 — resuelta (dueño, 2026-10-12).** La lectura única de oos2 **corta** con clave propia `19.5` (z ≤ 0 fuera); es el
  único corte de la cola. El 17 y el 19 siguen juzgando y anotando sin borrar.
- **D13 — resuelta (dueño, 2026-10-12).** El 18.5 vuelve **por activo**: corre sólo donde el descuadre medido es < 0,01 (hoy
  USDJPY, USATEC, NIKKEI) y se salta diciéndolo en el resto (XAUUSD oos1 0,28-0,46, USA500 oos1 0,15, DAX40 0,011).

## Lo que no tocas

- El master `SQX` (5050) y sus proyectos, salvo la importación de datos de la fila 9.
- `Trade_NIKKEI225_M30_volatilidadL` y los `Test_XAUUSD_*` / `Test_USDJPY_*` del custodio: son de
  otras sesiones; se miran con `ls -lt`, no se retiran.
- `assets/*.yaml` a mano: sólo `core.assetwrite` y la ventana.
- `docs/manual/` sólo PDFs; `docs/AgentPDFs/criterios-*` se enlazan, no se reescriben.
- `MonteCarloManipulation`, en ninguna tarea. `criteria.yaml` no se edita para saltarse un fallo
  de una corrida (regla 19): aquí se edita porque es el encargo.
- oos2: sólo la lectura única de la fila 6, una vez por celda, anotada.

## Objetivo — un comando

```
python3 tools/depmap.py && python3 tools/checks.py && python3 -m pytest tests -q -x \
  && ! grep -qE '^\| [0-9A-C.✓]+ \|.*(⬜|🟡|🔴)' docs/encargos/65-consenso-cuatro-opiniones.md
```

Sale 0 sólo con las comprobaciones en verde y ninguna fila abierta. La corrida nula (5.4) y el
build sintético (9) no caben en un comando: su cifra va en la fila al cerrarla.

## Cómo cierras

- **Cada sesión**, acabe donde acabe: tabla y bitácora al día; `python3 tools/depmap.py && python3
  tools/checks.py` en verde sobre lo tocado; las cartas `knowhow/` de lo no obvio; qué hizo · qué
  verificó, con la salida pegada · qué dejó sin hacer y por qué; lista de ficheros cambiados y,
  como última línea, «¿Quieres hacer el commit?» (por pathspec, y push en el mismo paso, sólo tras
  su sí). Si quedan filas abiertas, `/handoff` apuntando a este encargo y a la primera fila ⬜.
- **El encargo entero:** el Objetivo sale 0, la corrida nula ≤ 1,2 % y el veredicto del build
  sintético están escritos en sus filas; entonces este fichero se borra como cualquier encargo
  cumplido.

No se despacha con `/loop`: cada fila la lanza y la verifica la sesión que orquesta.
