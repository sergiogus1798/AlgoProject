# 54 · Fondeo: la economía del banco y el riesgo máximo por cuenta — plan que cruza sesiones

> Consolidado el 2026-10-09 desde los encargos 33 (economía del fondeo) y 45 (módulo de fondeo). Los
> originales siguen legibles en git: `git show c923d10:docs/encargos/<fichero>`.

**Tu oficio:** Python y estadística de cuentas de fondeo, en `portfolio/funded/`, con vistas en `ui/`.
Diseño y estadística: **Opus**; lo mecánico (un editor de la ventana ya especificado, tests, el capítulo
del manual): **Sonnet** (regla 17).

**Tu encargo:** cerrar lo que queda para responder, con números y su incertidumbre, dos preguntas del
dueño sobre fondeo. (1) ¿Qué challenge compro, con qué add-ons, con qué cartera y a qué riesgo para que
el dinero que **entra** en su banco por cobros supere al que **sale** por compras (VE_banco)? Construido
en lo esencial; faltan el editor de sus entradas en la ventana, sus decisiones y la corrida sobre una
cartera real. (2) Para una cartera ya superviviente y una cuenta concreta, ¿cuál es **el riesgo máximo
por operación que cabe dentro del límite diario y del total**? Sin empezar. La salida de ambas es una
decisión (`CLAUDE.md`: un análisis termina en una decisión): «compra X de tamaño Y con los add-ons Z,
riesgo r₁ en challenge y r₂ en fondeada; VE +A $/mes si el edge en vivo es ≥ h % del OOS», o «ningún
plan es positivo» — y, del lado del riesgo, un veredicto viable / dudosa / inviable con el coste en
carteras junto a lo que se gana.

Lee `CLAUDE.md` · `CODESTYLE.md` · `portfolio/CLAUDE.md` (sección «Funded rules, written here first») ·
`portfolio/DECISIONS.md:10` («Settled by the owner — #6») y `:37` («Still open in #6») ·
`OPEN.md` #85 (`grep -n '^## 85' OPEN.md`) · `portfolio/funded/{sim,rules,decide,catalog}/README.md`.
Memoria del dueño que manda aquí: **fondeo va antes que Darwinex**; en fondeo manda el **flotante**
(MAE, MFE); los costes de trabajo de agentes se cuentan en **tokens**, no en dólares; probar no escribe
nunca la raíz real (`portfolio/testroot/README.md`).

## Estado — lo actualiza cada sesión

| frente | qué | modelo | depende de | estado |
|---|---|---|---|---|
| A | La ventana edita los huecos del catálogo, el precio pagado y las entradas `owner.*` (33 entregable 5) | Sonnet (mecánico) | nada | hecho 2026-10-14 salvo el precio pagado (el modelo no tiene esa entrada; usa lista) |
| B | Las entradas del dueño aún `null` y las preguntas abiertas de 33: listarlas y preguntarlas, nunca rellenarlas | Opus | A (para que él las escriba) | hecho 2026-10-14 y 2026-10-15; no queda nada abierto |
| C | «Hecho es» de 33: la tabla de §4 sobre una cartera REAL, contra el mono, con recortes y una frase de decisión | Opus | encargo 55 (pool validado), B | bloqueado |
| D | Módulo de riesgo máximo: inventario y las cinco decisiones (45 parte 1) | Opus | nada | inventario hecho 2026-10-14 (abajo); decisiones 1-7 ya contestadas; E desbloqueado |
| E | `q_día`, `DD_95`, `riesgo_max` y veredicto (45 partes 2-4) | Opus | D contestado | libre |
| F | La prueba del retraso con el feed de la firma (45 parte 5) | Opus | D; paso 26 (encargo 55) | bloqueado |
| G | Vista del módulo de riesgo máximo y su capítulo del manual (45 parte 6) | Sonnet tras el dibujo del dueño | E | bloqueado |

**Bitácora:**

- 2026-10-14 · A, B y D ejecutados (Sonnet). A: botón «Entradas del dueño» en Fondeo y Banco
  (`ui/daemon/portfolios/owner.py`, `ui/desktop/portfolios/ownerinputs.py`), escribe la capa local
  `config/owner.yaml` (decisión 14; fuera de git, así que gorilla no la ve). B: escritos en los
  `config.yaml` del repo (eurusd 1,12, colchón 0, comisión 0,02, cierre 0,05/año, los 4 huecos,
  `open_risk_cap` 0,5, `pass_percentile` 95 vía ledger `portfolio.funded.verdict_percentile`); FTMO 2-step
  `fee_refund` pasa a `true` (confirmado) en `rules/ftmo.yaml` y en `funding.sqlite`. Sin escribir:
  `tax_rate` (pendiente del dueño), `p_payout_denied` («5 % al año»: el modelo es por petición de cobro,
  ¿cuál?) y `t1_gap`. D: inventario en §4.
- 2026-10-15 · B cerrado (Sonnet): contestadas `tax_rate`, `p_payout_denied`, `t1_gap` y `seasonality.fdr_q`
  (bloque «Contestadas por el dueño (2026-10-15)», abajo). `tax_rate` sale del núcleo de la caja
  (`kernel`, `bank`, `plans`): todo se calcula sin impuestos y `measures.after_tax` pone el VE con ellos
  al lado en `funded.sim.report`, `funded.decide` y la ventana (Decisión y Tabla VE).
- 2026-10-09 · consolidado desde los encargos 33 y 45; nada ejecutado desde la consolidación. Verificado
  ese día: lo construido de 33 (§0), las rutas de A y que `kept/` solo tiene `Trade_NIKKEI225_M30_volatilidadL`.

---

## §0 De dónde sale

- Dueño, 2026-09-29: «Un error que cometía yo antes era ver las cuentas de fondeo de la misma forma que
  una cuenta real, fijándome únicamente en la performance interna de la cuenta, sin contar el coste de la
  fondeada. Quiero empezar a aplicar matemáticas seriamente». Una empresa vende challenges de 1, 2 y 3
  pasos y cuentas instantáneas, con add-ons que cambian reglas **y** precio: un problema de decisión con
  un precio en cada casilla.
- Dueño, 2026-10-06 (45): R9a (peor día) y R9c (drawdown sobre neto anual) del paso 8 «no dicen si hay
  ventaja, sino cuánto riesgo se le puede poner: es dimensionado, no validación». Desde que el encargo 50
  ejecute la nueva puerta y hasta que exista el frente E, **nada en la cadena juzga el peor día ni el
  drawdown**; el dueño aceptó el hueco. Propuesta con las fórmulas: `docs/AgentPDFs/criterios-implementados-2026-10-12.md`
  (el diseño está en `:65-142` del encargo de origen; si ese rango se movió, `grep -n 'R9' ` el fichero).
- Fondeo antes que la cuenta real en Darwinex; en fondeo manda el flotante (dueño, memoria).

## Ya construido — no se rehace (una línea por bloque)

- **Catálogo** (33 entregable 1): `portfolio/funded/catalog/` + `AlgoData/funding/funding.sqlite`, Hantec y
  FTMO, todas las combinaciones de add-ons (`combos`) y el compendio de reglas (`rules`); `fundingWatcher`
  lo refresca los domingos. Fórmula de precio: `knowhow/costs/prop-firm-catalogue-hantec.md`; test
  `tests/test_funded_price.py`. Manual: capítulo 73 (`fondeo-catalogo`).
- **Reglas** (entregable 2): `portfolio/funded/rules/` (funciones puras sobre el flotante del día del
  servidor), `tests/test_funded_rules.py`.
- **Simulación de caja** (3): `portfolio/funded/sim/` (compra → fases → fondeada → cobros, caminos por
  bloques, recorte `h`, mono), `tests/test_funded_sim.py`, `test_funded_bank.py`. Manual: 88 (`fondeo-caja`).
- **Decisión** (4): `portfolio/funded/decide/` (frase de decisión con coste junto a ganancia, o «ninguno»),
  `tests/test_funded_decide.py`. Manual: 102 (`fondeo-decision`).
- **Ofertas** (7): `portfolio/funded/deals/`, `deals.worth` enchufado al modelo. Manual: 74 (`fondeo-ofertas`).
- **Ventana, zona «Fondeo»** (parte del 5): `ui/desktop/portfolios/`, `ui/daemon/portfolios/funded.py`,
  `bank.py`. Manual: 79 (`cartera-fondeo`).
- **Reglas escritas primero** (8, cerrado 2026-10-09): `portfolio/CLAUDE.md` «Funded rules, written here
  first» y `portfolio/DECISIONS.md` «Settled by the owner — #6» — no se duplican aquí. Commits de 33:
  `7567635`, `2bd12d6`, `866bec4`, `ce61c0f`.
- **Lo ya fijado por el dueño** (todo en `portfolio/funded/sim/config.yaml` y `DECISIONS.md`): universo 10k USD
  como máximo; presupuesto de caja 1.000 EUR; precio de lista; recompra `same_plan` y `none` comparadas;
  recortes `h` 0/25/50/75/100 con el 50 % decidiendo; nivel del edge desde OOS y forma del camino desde el
  histórico largo; manda el Monte Carlo más pesimista (T1, T2, D).

---

## 1 · Frente A — la ventana edita las entradas del dueño (33 entregable 5)

**No cumplido.** El dueño edita la configuración desde la ventana, nunca abriendo un YAML (memoria). Hoy la
ventana solo *muestra* «Falta owner.<x>: decisión tuya»: `ui/daemon/portfolios/bank.py:15-18` y
`ui/daemon/portfolios/funded.py:10-14` (KNOBS) y `:25-28` (`missing`); `ui/daemon/portfolios/commands.py:58`
rechaza `--set` en la raíz real; los editores genéricos (`ui/daemon/sqxconfig/write.py:11`
`WRITABLE = ("build","classes","policy")`, `ui/daemon/results/knobs.py:36` mapa de configs) no alcanzan
`portfolio/funded/sim/config.yaml` ni `portfolio/common/construct/config.yaml`.

Construir, en la zona «Fondeo» (estilo terminal `theme.T`, regla de `ui/`), un editor que escriba:
1. los `gaps.*` (huecos del catálogo) y `owner.*` de `portfolio/funded/sim/config.yaml`;
2. el **precio pagado** (hoy es de lista por decisión del dueño; sigue siendo una entrada del modelo y el
   cambio EUR/USD, `owner.eurusd`, debe quedar escrito junto al resultado, nunca buscado en la red);
3. los `null` que bloquean la etapa A/B y el veredicto en `portfolio/common/construct/config.yaml`:
   `open_risk_cap` (`:44`), `t1_gap` (`:54`), `pass_percentile` (`:79`).

Reglas: conservar los comentarios del YAML (`ruamel.yaml`, como `core.assetwrite`); un único escritor
(modelo: «`core.assetwrite` es el único escritor» de los activos); cada campo con su frase de ayuda y lo
que bloquea; validar el tipo y el rango sin inventar defectos; **nunca escribir un valor que el dueño no
haya tecleado**. Tests: lectura→escritura conserva comentarios, un `null` sigue `null` si no se toca,
y la raíz de prueba no toca la real. Verifica con `/ui-shot`. Capítulo del manual 79 o 88 actualizado
(regla 8: el editor es un comando nuevo para el dueño).
*Decisión previa (regla 11):* ¿el editor escribe el YAML en el repo (el que se versiona) o una capa
local en `config/`? — pregunta abajo (ex 33, entregable 5).

## 2 · Frente B — lo que es del dueño (cerrado 2026-10-15; lo de abajo es el histórico)

Todo esto lo contesta el dueño; este plan lo **lista y lo pregunta** (frente A lo hace escribible), y
**nunca** rellena un valor. Mientras sean `null`, `decide` responde siempre «ninguno».

Entradas `null` en `portfolio/funded/sim/config.yaml` (`:24-40`):
`owner.eurusd`, `payout_cushion`, `tax_rate`, `payout_fee`, `p_payout_denied`, `p_firm_closes_year`;
`gaps.hantec_fee_refund`, `hantec_endurance_payout_days`, `hantec_express_floor_after_payout`,
`ftmo_1step_floor_after_payout`. Y en `portfolio/common/construct/config.yaml`: `verdict.pass_percentile`
(`:79`) y `funded.open_risk_cap` (`:44`). El detalle de los huecos del catálogo y por qué faltan:
`knowhow/costs/funded-stage-catalogue-gaps.md`.

Abiertas de 33 que ninguna ficha contesta: las listadas en «Decisiones del dueño» (más abajo).

## 3 · Frente C — «Hecho es» de 33: la tabla real

Definición de hecho de 33: **para la cartera que el dueño elija del archivo, la tabla de §4 sobre los
planes de 10k como máximo de Hantec y FTMO con los add-ons que tengan sentido, contra el mono, con
recortes, y una frase de decisión.** Solo corrida hasta hoy: el pool de prueba `Test_nikkei_ref` bajo la
raíz de prueba (RAÍZ DE PRUEBA, ninguna cifra es resultado). Falta un pool validado (encargo 55; hoy las
filas del pool son todas `fail`) y Monte Carlo pesado (regla 19/CPU: nada más corriendo al lado).

**La tabla de §4 — una por cartera, un plan por fila, ordenada por VE_banco con el recorte decisorio:**
precio pagado (lista, add-ons) y riesgo por fase · P(aprobar cada fase), P(llegar al primer cobro), nº
esperado de compras hasta el primer cobro · cobros esperados por cuenta fondeada y vida esperada (días,
ciclos de cobro) · VE_banco por compra, por dólar y por mes con intervalo al 90 % · **desembolso máximo
acumulado (mediana, p90, p99) antes del primer cobro — el drawdown de la caja se da en percentiles, no
en media** · recorte de equilibrio y ventaja sobre el mono · la regla que más suspende.
Comando y lectura: `python3 -m portfolio.funded.sim.run --help`, `python3 -m portfolio.funded.decide.run
--help`, capítulos 88 y 102. Tras la corrida real: ficha en `knowhow/` con lo no obvio y, si cambia lo que
los READMEs dicen («no real result yet», `portfolio/CLAUDE.md`), corrígelo.

---

## 4 · Frente D — módulo de riesgo máximo: inventario y las cinco decisiones (45 parte 1)

**No empezado**: solo hay su borrador (commit `6c90300`). Lo único construido para él es su *entrada*:
`pipeline/autopilot/kept.py:11` (`FACTS = ("oos_worst_day_r", "dd_esperado_r", "oos_net_per_year_r")`)
guarda esos tres hechos por estrategia que pasa el WFM; hoy solo
`AlgoData/kept/Trade_NIKKEI225_M30_volatilidadL`. Test: `tests/test_autopilot_kept.py`.

**Primera entrega = el inventario y las cinco preguntas, sin código** (45 §1). Una tabla: para cada pieza
de las partes E y F, qué existe ya (`fichero:línea`), qué responde hoy y la distancia a lo pedido. Mira
antes (`graphify explain "<ruta>::<símbolo>"`): `portfolio/funded/sim/` (`account.py`, `kernel.py`,
`bank.py`, `plans.py`, `haircut.py`, `monkey.py`, `frompool.py`), `portfolio/funded/rules/`
(`machine.py`, `floors.py`, `catalog.py`), `portfolio/funded/decide/`, y el Monte Carlo a nivel de
operación `portfolio/common/monteCarlo/` (`README.md`, `POSSIBLE_IMPROVEMENTS.md`). **Puede que parte de
E ya exista con otro nombre** — la etapa A/B de la cartera fondeada (`ui/daemon/portfolios/funded.py`,
P(pasar), `open_risk_cap`) ya dimensiona riesgo; el inventario dice cuánto se solapa. Cada decisión, con tu
recomendación y su coste. No se escribe código hasta que el dueño conteste.

### Inventario (hecho 2026-10-14; qué existe, qué responde hoy, distancia)

| pieza | qué existe | distancia |
|---|---|---|
| Entrada por estrategia | `pipeline/autopilot/kept.py:12` `FACTS`, `:15` `rows()` (curva oos1 en R, mínimo diario de SQX), `:68` `save()` | poca; la curva es el mínimo diario, cota conservadora al sumar |
| E2a curva diaria de cartera en R | `portfolio/common/construct/equity/blocks.py:82` `joint_day_low`; `construct/mc/blocklen.py:11` `daily_pnl` (en divisa, universo M1 reconstruido) | media: falta sumar las curvas de `kept` de los miembros elegidos a mano, solo oos1 |
| E2b POT / Pareto, `q_día` | nada (`scipy.stats.genpareto` está instalado) | total: ajuste, umbral, bootstrap ≥ 5.000 con extremo conservador, «sin dato» |
| E2c declustering | nada (`construct/mc/paths.py:45` `daily_blocks` es otra cosa) | total, pequeño |
| E3 `DD_95` de cartera | R6: `studies/screening/gate/level3ab.py:67-74` → `studies/screening/analysis/resample.py:151` (bloques de operaciones, por estrategia) | media-alta: hace falta bloques por fecha comunes sobre la curva de cartera; decidir si R6 se extrae a núcleo común |
| Monte Carlo `portfolio/common/monteCarlo/` | por estrategia (orden, omitidas, ejecución, régimen) | casi nada que reutilizar |
| E4a `L_d`, `L_tot` y semántica | `portfolio/funded/rules/catalog.py:158` `plan()`, `floors.py:6,27`, `machine.py:175` | baja; falta la hora de corte por plan (`construct/equity/days.py:76` calcula el día de servidor) |
| E4b `riesgo_max` y veredicto | nada (`construct/search/stagea.py:14` `open_cap` es otra cosa) | total, ~30 líneas + config |
| Cuentas que elige el dueño | `rules/catalog.py:50` `plans()`, `funded/sim/plans.py:287`, `decide/` | baja; un mando que pase `plan_key` |
| `funded/sim/` | `account.py`, `bank.py`, `haircut.py`, `monkey.py`, `frompool.py` | ninguno responde «cuánto riesgo cabe»; la comprobación va al lado (decisión 5) |

Solape: solo `open_risk_cap` (0,5; riesgo abierto simultáneo, no una cola estadística) y la P(pasar) de la
etapa A/B (probabilidad de aprobar con un riesgo dado); `riesgo_max` es lo inverso. Se muestran juntos, no
se fusionan. El «número por estrategia suelta» (decisión 3) con la curva diaria no cuadra con `dd_esperado_r`
de la puerta (remuestreo por operaciones): la prueba «cartera de una estrategia = `dd_esperado_r`» exige
reutilizar `resample.drawdowns` con operaciones.

## 5 · Frente E — `q_día`, `DD_95`, `riesgo_max` y veredicto (45 partes 2-4)

Bloqueado hasta que D esté contestado. Qué se construye (el diseño estadístico lo definió el dueño el
2026-10-06):

**Parte 2 — el peor día que llegará, no el que se vio (`q_día`).** Dato: la **curva diaria de flotante de
la cartera en oos1, en R**, suma día a día de las curvas de sus estrategias (el límite diario se juega con
varias abiertas; sumar los peores días por separado no vale). Método: *peaks over threshold* — pérdidas
diarias sobre un umbral alto, Pareto generalizada; `q_día` = la pérdida diaria con probabilidad
≈ 0,05 / 252. **Conservador por construcción:** con ~100 excedencias el ajuste es ruidoso, se usa el
**extremo conservador del intervalo de confianza**, no la central, con intervalo por bootstrap de **al
menos 5.000 repeticiones**. A mirar: cómo se elige el umbral (gráfico de vida media residual o percentil
fijo configurable) y que el resultado no baile con él; con menos excedencias de las que el ajuste aguanta
no hay `q_día` — el veredicto es «sin dato», nunca un número inventado; *declustering* de días malos
seguidos.

**Parte 3 — `DD_95` de la cartera.** La puerta deja por estrategia `gate.scorecard.dd_esperado_r` (percentil
`drawdown.percentile`, 95 de serie, del bootstrap por bloques de R6). **El de la cartera no es la suma:**
se recalcula sobre la curva de la cartera con el mismo método (bloques cortados por fecha, los mismos para
todas las estrategias, 5.000 secuencias). Reutiliza el bootstrap de R6 de `studies/screening/gate/` (encargo 50)
y el Monte Carlo de `portfolio/`; no se escribe un tercero.

**Parte 4 — riesgo máximo y veredicto.**

$$\text{riesgo}_{\max} = \min\!\left(\frac{L_d}{q_{\text{día}}},\ \frac{L_{\text{tot}}}{\text{DD}_{95}}\right)$$

`L_d` y `L_tot` **del catálogo** (`python3 -m portfolio.funded.catalog.show <firma o plan>`), nunca
escritos; respetando cómo mide cada firma su límite (balance o equity, estático o trailing, hora de corte)
con `portfolio/funded/rules/`. Veredicto de partida —orientativo, configurable y **pendiente de números
del dueño**—: viable con `riesgo_max` ≥ 0,75 %, dudosa entre 0,4 % y 0,75 %, inviable por debajo. Anotado,
nunca regla: rendimiento anual a ese riesgo (`riesgo_max` × neto anual en R), tiempo de recuperación
(`DD_95` / neto anual) y cuál de los dos límites manda. Orden de magnitud para comprobar (propuesta R9,
aproximaciones optimistas y por estrategia suelta): con 5 % diario y 10 % total, A ≈ 0,74 % y ≈ 7 % anual;
C ≈ 0,99 % y ≈ 1,2 % anual; en las dos manda el límite total.

**Todo es un parámetro y en la ventana** (con su frase de ayuda): probabilidad del día extremo
(0,05 / 252), umbral de la cola, nivel del intervalo, percentil del drawdown, longitud de bloque,
repeticiones (≥ 5.000), semilla y niveles del veredicto. Los límites, del catálogo.

**Verificación (45):**
- Pareto generalizada simulada con parámetros dados: `q_día` cae dentro de su intervalo en la proporción que dice el nivel.
- Cartera de una sola estrategia: mismo `DD_95` que `dd_esperado_r` de la puerta.
- Dos estrategias idénticas doblan `q_día` y `DD_95`; dos que nunca coinciden, no.
- Con los límites de un plan real del catálogo, `riesgo_max` coincide con el cálculo a mano.
- Un test nuevo por pieza (`tests/test_funded_riskmax*.py` o el nombre que elija la decisión 1 de D), `python3 -m pytest -q tests/<fichero>`.

## 6 · Frente F — la prueba del retraso con el feed de la firma (45 parte 5)

La puerta mide si la ventaja sobrevive a entrar una barra tarde sobre el histórico propio. La versión real
(`docs/AgentPDFs/criterios-implementados-2026-10-12.md:141`): con las barras de la
propia firma, ¿la estrategia se dispara en los mismos momentos? **Primero mira qué da ya el paso 26**
(`mt5/verify/README.md`: `run.py`, `judge.py`, `sidebyside.py` emparejan por hora de entrada las
operaciones de SQX y de MT5 en la cuenta de cada firma). Con eso decide —y pregunta al dueño— si es parte
de este módulo o una lectura más del paso 26 (encargo 55). No construyas nada antes de esa respuesta.

## 7 · Frente G — vista y manual del módulo de riesgo máximo (45 parte 6)

Lo que tiene interfaz es una vista dentro de `ui/` (estilo terminal `theme.T`, `QFrame` llamado `term`),
todos los parámetros editables y con su frase. **La zona de cartera sigue la estructura de Quant Analyzer
con los colores de la ventana, y la propuesta se enseña al dueño antes de construirla** (memoria
`ui-portfolio-estilo-quant-analyzer`). Capítulo del manual en la misma tarea (regla 8; `/manual-chapter`),
y `/ui-shot` antes de dar nada por hecho.

---

## Decisiones del dueño — pregúntalas (regla 11)

**Contestadas por el dueño (2026-10-15)** — cierran 11 (lo de B):
- `tax_rate` = 0,40 sobre beneficio neto. Todo cálculo, veredicto, umbral y orden se hace SIN impuestos;
  donde se enseñe dinero, la cifra sin impuestos y con ellos, una al lado de la otra; el impuesto nunca es
  entrada de una decisión. Texto neutro: «impuestos: 40 % sobre beneficio neto, sólo informativo».
  Vive en `portfolio/funded/sim/config.yaml` (`owner.tax_rate`).
- `p_payout_denied` = 0,05 POR COBRO, cada cobro por separado (como ya lo sortea `bank.hazards`).
  Mismo fichero.
- `t1_gap` = `close_to_open_blocks`, en `portfolio/common/construct/config.yaml` (`stageb.t1_gap`).
- `seasonality.fdr_q` = 0,05 confirmado: ya estaba en `ledger/thresholds.yaml`, ahora `set_by: dueño`.

**Contestadas por el dueño (2026-10-14)** — lo que sigue manda sobre la lista de abajo:
- 1 → **en `portfolio/funded/`**. 2 → **se marca y se queda**. 3 → **la cartera a mano + el número de cada estrategia suelta**. 4 → **las cuentas que elija el dueño en la ventana**.
- 5 → **comprobación al lado** de `funded/sim/`. 6 → **0,05/252 y 0,75 % / 0,4 %**, ratificado con los números delante. 7 → **en el paso 26**.
- 9 → **se descarta** (dropped, never trimmed). 10 → **sólo entre fase y fondeada**. 12 → **mercados adicionales o datos futuros**, nunca oos2 gastado.
- 13a → **504 días**. 13b → **sólo oos1**. 13c → **la tolerancia se fija viendo la tabla**. 13d → **el extremo bajo del intervalo**. 13e → **rejilla adaptativa**.
- 14 → **capa local en `config/`**.
- Siguen abiertas (datos del dueño): 8, 11, 15.
- 8 (en parte) → Hantec **no reembolsa** la cuota (confirmado: `AlgoData/funding/rules/hantec.yaml:169`, artículo de ayuda de Hantec). **FundedNext se admite sólo con cuentas de menos de 25k** (por encima no permite EAs) y **FundingPips se admite**: los dos entran por `/firm-onboard`. El resto del 8, buscado en las páginas de las firmas (2026-10-14; llevarlo a las fichas en el frente B, cada valor con su cita y su URL):
  - Endurance fondeada (`gaps.hantec_endurance_payout_days`): **14 días** hasta el primer cobro, 7 con el add-on semanal (help.htrader.hmarkets.com, artículo 158000445800). Que los siguientes también sean cada 14 días sólo lo dicen terceros: ambiguo.
  - Hantec Express (`gaps.hantec_express_floor_after_payout`): **`initial`**, confirmado: «your maximum total loss will lock in at your starting balance» (artículo 158000445797).
  - FTMO 1-step (`gaps.ftmo_1step_floor_after_payout`): **`stays`**, lectura natural de «Your Maximum Loss Limit does not reset» (ftmo.com/en/faq/how-do-i-withdraw-my-profits/); ambiguo.
  - FTMO 2-step: **la cuota SÍ se reembolsa con el primer cobro** («we will refund you the initial purchase fee once you request your first Reward withdrawal», ftmo.com/en/faq/are-the-fees-recurrent/). `AlgoData/funding/rules/ftmo.yaml` dice `fee_refund: false` (Consejo, 2026-10-04): **está mal y se corrige**; el dueño cobró un reembolso el 2026-09-29.
  - Hantec «Profit Target −2 %»: **no encontrado**; su artículo sólo dice «Reduces the required profit target». Sigue la lectura «sólo fase 1» hasta que Hantec conteste.
  - Estrategias prohibidas de Hantec: la ficha ya las tiene (`forbidden_practices`, `ea_policy`, confirmadas 2026-10-04), contrastadas con los 6 artículos de su carpeta de ayuda; nada nuevo.
- 11 (en parte) → **EUR/USD = 1,12**. Siguen abiertos: colchón de retiro, impuestos, comisión de cobro, probabilidades de cobro denegado y de cierre de firma.
- 11 (resto) → **colchón de retiro 0** (retirar todo), **comisión de cobro y divisa 2 %**, **5 % al año** de cobro denegado y **5 % al año** de cierre de firma. Sigue abierto: el tipo de impuestos.
- 11 (impuestos) → **impuestos: opción apagada, encargo 73** (`owner.tax_rate: null` = nada se calcula ni se muestra; con una fracción, informativo al lado del VE; sustituye el 0,40 del 2026-10-15).
- 15 → **`funded.open_risk_cap = 0,5`** (todos los stops a la vez gastan como mucho la mitad de la pérdida diaria máxima) y **`verdict.pass_percentile = 95`** (la cartera pasa mejor que el 95 % de las carteras al azar). Se escriben al ejecutar el frente B: el primero en `portfolio/common/construct/config.yaml`, el segundo como `ledger:portfolio.funded.verdict_percentile`.


**Ex 45 (antes de escribir código de D/E):**
1. **(ex 45, D1) Dónde vive y en qué paso se lee:** dentro de `portfolio/funded/` junto al simulador
   (recomendado mirar primero), o como estudio de `studies/`; y si es un paso numerado del WORKFLOW o una
   lectura de la zona de cartera.
2. **(ex 45, D2) Corta o anota:** ¿una cartera inviable sale, o solo queda marcada?
3. **(ex 45, D3) Qué cartera:** la que arme a mano, la que salga del buscador de carteras, o todas las
   combinaciones de las supervivientes; y si además se da el número por estrategia suelta.
4. **(ex 45, D4) Contra qué cuentas:** todos los planes del catálogo, solo los de las firmas activas, o los
   que él elija en la ventana.
5. **(ex 45, D5) Qué hace con el simulador existente** (`portfolio/funded/sim/`): ¿este número es una
   entrada suya, una comprobación al lado, o lo sustituye en parte? Depende del inventario.
6. **(ex 45)** Con números cuando existan: la probabilidad del día extremo (propuesta 0,05 / 252) y los
   niveles del veredicto 0,75 % / 0,4 %.
7. **(ex 45, parte 5)** La prueba del retraso con el feed: ¿parte de este módulo o lectura del paso 26?

**Ex 33 (huecos y entradas):**
8. **(ex 33, §2/§6.1)** Los huecos del catálogo que los Términos no resuelven sin interpretación y que
   `DECISIONS.md:39-48` deja abiertos: reembolso de cuota de Hantec (`gaps.hantec_fee_refund`), días entre
   cobros de la Endurance fondeada, qué hace un cobro al suelo trailing de la Express fondeada y del 1-step
   de FTMO (`stays` | `initial`), reembolso de la cuota del FTMO 2-step por cuenta (el Consejo lo modela sin
   reembolso, 2026-10-04, sin confirmar), si el «Profit Target −2 %» de Hantec baja todas las fases (Consejo:
   solo la 1), artículo de estrategias prohibidas de Hantec, y candidatas FundedNext / FundingPips (admisión).
9. **(ex 33, §6.2)** Cierre del viernes / sin noticias: ¿se descarta la estrategia o se modifica para cumplir?
   (`DECISIONS.md` fija «dropped, never trimmed» para lo que la firma prohíbe sin remedio; confirmar si
   cubre también estos dos casos.)
10. **(ex 33, §6.3)** ¿Se puede cambiar el riesgo entre fase y fondeada, y dentro de la fondeada tras un cobro?
    (El modelo ya admite un riesgo por fase; falta lo de «tras un cobro».)
11. **(ex 33, §3.5/§5)** Entradas `owner.*`: colchón de retiro (`payout_cushion`; 0 = retirar todo; la
    política de retiro es variable de decisión), impuestos (`tax_rate`), comisión de pago/divisa
    (`payout_fee`), probabilidad de cobro denegado y de cierre de la firma por año, cambio EUR/USD del día.
    Ninguna se inventa.
12. **(ex 33, §6.7 y DECISIONS #11)** Con qué datos no vistos se valida la combinación elegida — `oos2` ya
    está gastado cuando se llega aquí, pero la elección sigue siendo una búsqueda que cuenta en el ledger.
13. **(ex 33, primera corrida real, 2026-10-05; nada decidido)**
    a. **Horizonte de la simulación de caja:** a 504 días el trader sin edge pierde en todos los planes; a
    1.008 tres planes de suelo fijo le dan VE positivo (el mono `demean` no paga costes y un suelo fijo
    regala de media el margen de pérdida a quien no tiene edge). ¿504, 1.008 u otro?
    b. **Qué tramos fuera de muestra fijan el nivel del edge** (`--edge-from`, `portfolio/funded/sim/frompool.py:32`).
    c. **Cuánto puede moverse el puesto al cambiar `h`** antes de llamar frágil a la elección.
    d. **La barra:** ¿VE puntual o extremo bajo de su intervalo?
    e. **La rejilla de riesgo de la caja** (0,25 / 0,5 / 1 %) no contiene el riesgo del veredicto: ¿se
    amplía, se hace adaptativa o el veredicto se redondea a ella?
14. **(ex 33, entregable 5)** El editor de A: ¿escribe el YAML versionado del repo o una capa local?
15. **(ex 33, CLAUDE.md)** `verdict.pass_percentile` y `funded.open_risk_cap`: sin ellos `decide` siempre
    contesta «ninguno» y `oos2` no se abre (`DECISIONS.md:50`).

---

## Lo que no tocas

El maestro (`SQX`, 5050) y sus proyectos. `oos2` sin autorización del dueño para la tarea. **Ningún valor
`null` de `owner.*`/`gaps.*`/`verdict.*`/`funded.open_risk_cap` se rellena por tu cuenta.** El catálogo y
las ofertas (`portfolio/funded/catalog/`, `deals/`) solo se leen salvo el trabajo del `fundingWatcher`.
`pipeline/autopilot/criteria.yaml` del paso 8 y `studies/screening/gate/` son del encargo 50 (solo se
leen). Los ficheros de `mt5/` y del pool son del encargo 55. Ninguna orden a MT5: el terminal solo se
consulta. Ni SQX ni `bin/workflow.sh` desde aquí: este plan es Python sobre datos ya guardados. Probar
no escribe la raíz real (`ALGO_DATA_ROOT=<AlgoData>/portfolio/_test/root`; todo proceso imprime «RAÍZ DE
PRUEBA»). Nada se mezcla con el Monte Carlo pesado en la misma máquina mientras corre un workflow.

## Objetivo — un comando

No existe un comando único que valga para todo el plan: C y la mayor parte de B/D son **decisiones del
dueño** y una corrida real pesada. Hasta que existan los tests de E, la `Verificación` es:

1. Frente A: `python3 -m pytest -q tests/test_funded_*.py tests/test_ui_*.py` (con el test del editor
   nuevo) y una captura `/ui-shot` de la zona «Fondeo» con el editor.
2. Frente B: cada entrada de «Decisiones del dueño» contestada por él y escrita desde la ventana; nada
   `null` que no lo sea por su decisión explícita.
3. Frente C: `python3 -m portfolio.funded.decide.run` sobre una cartera real devuelve la frase de decisión
   (o «ninguno» con su causa), con la tabla de §4 en el capítulo 88/102.
4. Frentes D-G: la lista de verificación de §5 más el inventario y las respuestas D1-D5 anotadas en la
   Bitácora.

En cada sesión, al final: `python3 tools/depmap.py && python3 tools/checks.py && python3 -m pytest -q
tests/test_funded_price.py tests/test_funded_rules.py tests/test_funded_sim.py tests/test_funded_bank.py
tests/test_funded_decide.py tests/test_autopilot_kept.py` debe salir 0 (hoy es la línea base; los
frentes nuevos la amplían).

## Lo que sólo vivía en los encargos de origen

**Motivo del dueño:** véase §0 (2026-09-29). Cambio de unidad que el modelo respeta (ex 33 §1): VE_banco =
E[cobros] − E[precios pagados] (− comisiones, − impuestos), con las **recompras** tras cada suspenso en las
compras y el **reembolso de la cuota** en los cobros; la pérdida está acotada al precio y la ganancia es la
cola; el riesgo óptimo por operación es una U invertida y **distinto en cada fase**; todo se mide en % del
tamaño pero el **precio no es lineal** (Hantec Express: 2k = 39 $ = 19,5 $/k; 200k = 999 $ = 5,0 $/k; 10k
≈ 9,9 $/k); varias cuentas con la misma cartera suspenden juntas, no diversifican; la caja tiene su
propio drawdown (racha de suspensos antes del primer cobro).

**Hechos del catálogo que ningún otro fichero guarda (ex 33 §2) — verificar en los Términos antes de
simular, y que el dueño confirme:** el JSON da un solo objetivo por plan (faltan los de las fases 2 y 3); el
reparto base de los challenges (`profitSharePct` viene a 0; solo las instantáneas traen 80 %); la pérdida
diaria es, según el centro de ayuda de Hantec, un % del mayor entre balance y equity a las 00:00 del
servidor del día anterior (confirmar); la fórmula de la consistencia la página la muestra rota
(«(Best Day's Profit + Total Profit) × 100», probablemente mejor día ÷ total); cobro mínimo, límite de
riesgo abierto, apalancamiento y plan de escalado sin dato; `rewardFrequency` 0 y `timeLimit` 0 sin
significado confirmado (¿«sin cobro programado» / «sin límite»?). La web anuncia además un −50 % casi
permanente (DROP50, no para Instant24) que el catálogo no recoge: **el precio pagado es una entrada, no el
de lista** (hoy el dueño decidió lista). Hechos ya anotados: `knowhow/costs/funded-stage-catalogue-gaps.md`,
`prop-firm-catalogue-hantec.md`, `prop-firm-discounts.md`, `portfolio/PLAN.md` §14, `OPEN.md` #85.

**Geometría sin edge (ex 33 §3.5):** P(tocar +a antes que −b) = b/(a+b): Express +10/−6 ≤ 37,5 %;
+2 %/−2 % 50 %; dos pasos +10/−10 y +5/−10 → 33 %; Endurance (+6/−8)³ → 19 %. Precio por cuenta aprobada sin
edge = precio / esa P (orden de magnitud; el mono de `studies/readings/monkey/` da el suelo real). Referencia
de add-on: el 95 % en la Express de 25k (80 → 95 %, +59,70 $) compensa solo si el beneficio bruto esperado
en fondeada supera 59,70 / 0,15 ≈ 398 $. Add-ons se evalúan por **ΔVE − precio, también por parejas**.
Lote mínimo: en 10k un 0,5 % son 50 $; con 0,01 lotes y stop ancho el riesgo mínimo puede pasar del
objetivo — el riesgo es discreto y la estrategia cuyo lote mínimo lo excede queda fuera del plan.

**Intuición a confirmar o tumbar, no a asumir (ex 33 §3.5):** con edge modesto y fiable ganarán los planes
de DD estático, cuota reembolsable y sin consistencia (FTMO 2-step, Hantec Enhanced); con edge dudoso, los
que ya valen algo sin edge (reembolso, barreras simétricas, reparto alto). Sin límite de tiempo el riesgo del
challenge baja; riesgo por fase, bajo en challenge y más alto en fondeada, es la intuición a contrastar. En
fondeada manda una opción sobre el P&L (cobras parte de lo positivo, no pagas lo negativo): la volatilidad
vale hasta la barrera.

**Límites que el modelo declara (ex 33 §5):** riesgo de contraparte (cobro denegado, cierre de la firma, con
el VE enseñado también con ellos); ejecución en el servidor de la firma (spread/comisión distintos de
Darwinex; el puente MT5 y `assets/RULES.md`); impuestos y comisiones de pago como parámetros del dueño; el
techo de asignación por trader limita cuántas cuentas escalan.

**Criterio robusto de elección (ex 33 §3.5.6):** el mayor VE_banco con un recorte pesimista (`h` = 50 %,
ahora decidido), dentro del presupuesto de caja, y cuyo puesto no cambie mucho al mover `h`; nunca el
máximo con edge completo. Presupuesto de caja: 1.000 EUR en total (dueño, 2026-09-29: «pon 1000 euros en
total en la cuenta bancaria»), un plan cuyo p90 de desembolso antes del primer cobro lo supera no se elige.

**Fechas del dueño de las decisiones ya tomadas** (para no repreguntar): universo 10k USD y recompra
(2026-09-29 / 2026-10-05), recortes y `h` decisorio (2026-10-05), «de lista» (2026-09-29), cuentas solo en
USD (2026-09-29), Consejo por delegación (2026-10-04, `DECISIONS.md`).

## Cómo cierras

La tabla de estado y la bitácora actualizadas · qué hizo · qué verificó, con la salida pegada · qué dejó sin
hacer y por qué · qué descubrió para `knowhow/` (una ficha por hecho no obvio, en el dominio que toque) ·
la lista de ficheros cambiados y, como última línea, **¿Quieres hacer el commit?** (el dueño commitea;
nunca `git add -A`).

`/loop` no se despacha: el plan no tiene un `Objetivo` de un solo comando (decisiones del dueño y corrida real).
