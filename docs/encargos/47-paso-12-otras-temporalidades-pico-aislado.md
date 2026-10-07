# 47 · Pasos 10.5, 11 y 12 (otras temporalidades): «¿pico aislado en su TF?» — T0-T4 — encargo autocontenido

> **Plan vivo.** El dueño entregó la propuesta el 2026-10-07 y cerró siete decisiones (§0). El
> Council (Torvalds, Musashi, Feynman; 2026-10-07) revisó el plan de implementación. Cada sesión
> actualiza la tabla de estado.

| parte | qué | modelo | ficheros que posee | estado |
|---|---|---|---|---|
| K | núcleo estadístico: `e`, corridas al azar conjuntas por año, T0-T4, veredicto por madre | Opus | `studies/transfer/crossTF/tf/` (nuevo), `studies/transfer/crossTF/config.yaml` (sección `tf:`), `tooltips.py`, `tests/test_crosstf_tf_*.py` | **hecho 2026-10-07** — `tf/{null,rules,table,inputs,run}.py`, llamado desde `report.py` tras lo viejo; 15 tests; batería sin ventaja (300 madres, 300 corridas): media de z entre −0,09 y +0,02 (error 0,055), desviación 0,93-1,04, rechazo al 5 % entre 3,0 % y 5,7 %; `checks.py` 0 problemas. La clave es `tf.runs` (`null:` es None en YAML). Costura de la fase 2: `tf/inputs.build_banks` lee `build_databanks` de `blocks.json`. Tres lecturas abiertas → «Decisiones del dueño» |
| F | fabricación: `ranges.yaml`, cociente de ATR `c`, coeficientes escalados, M15 | Opus | `sqx/variants/{scale.py,ranges.yaml,ranges.py,config.yaml}`, `assets/_build.yaml` (sólo `crosstf:`), `tests/test_scale_ranges.py` | **hecho 2026-10-07** (sin commit). `c` NIKKEI225 M30→M15 0,704 · →H1 1,419 · →H4 2,833. Para S: `scale.fabricate(..., symbol)` saca el activo de la primera madre si no se le da; `crosstfload.py:107` puede pasarlo. Para V: un `bar` dividido por `c` < 1 puede pasar del `maxValue` del bloque (PMax 10,99 → 15,6 en M15). Pregunta abierta al dueño: `CBlock_CandleBreakoutLong*.Double2` (¿`bar` u `other`?), hoy `unverified` |
| S | tareas SQX de la fase 2 (build) y la de M15 | Sonnet | `sqx/projects/{workflow.py,crosstfsolo.py,crosstfload.py,crosstf.py,summary.py}`, `tests/test_crosstf_phase2.py` | hecho 2026-10-07 (código y tests; sin SQX) |
| P | piloto: pasos 11.5 y 11.7, hechos nuevos, ventana | Sonnet | `pipeline/autopilot/{plan.py,facts.py,tffacts.py,judge.py,criteria.yaml,run.py}`, `ui/daemon/launch/{chainplan,steps,preflight}.py`, `ui/daemon/workflow/{steps,derive}.py`, `ui/daemon/results/{store,tfrows}.py`, `ui/text/columnhelp{,_tf}.py`, `tests/test_autopilot_crosstf_cascade.py` | **hecho 2026-10-07** (código y tests; sin SQX): 11 → 11.5 (juzga, sin regla; corta `CrossTF_Input` con `siblings: follow`) → 11.7 (se salta con una línea sin tareas de fase 2) → 12 (`z_new`). Hechos `crossTF.tf.*` con pass=1, limbo=0, fail=−1. Los exports de los databanks `CrossTF_<TF>_build` los hace `afterrun` solo; `tf/inputs.build_banks` los deduce de `blocks.json` + `CROSSTF_BUILD`. Paquete del corte escrito abajo. Filas nuevas en la tabla de WORKFLOW.md (sólo la fila; el resto es de D) |
| D | documentación: README del estudio, skill, WORKFLOW, manual, knowhow, checks | Sonnet | `studies/transfer/crossTF/README.md`, `.claude/skills/crosstf/SKILL.md`, `.claude/skills/workflow-simple/steps.md`, `docs/AgentPDFs/WORKFLOW.md`, `CLAUDE.md` (la fila de los 26 pasos), `AlgoData/manual-fuentes/`, `knowhow/`, `docs/DEPENDENCIES.md` | tras P |
| V | **validación con datos reales** y **el corte** (`criteria.yaml` deja `z_new`) | — | — | espera a la primera corrida real (tareas de fase 2, M15 aceptado por los indicadores, `k/c` sobre `maxValue`, `z_Δ` centrada) y al «corta» del dueño; OPEN.md #108 |
| B | borrado de lo viejo (§7 de la propuesta) | Sonnet | — | espera a V (el «corta» del dueño y la validación); luego el paquete de borrado de abajo |

**Tu oficio:** ingeniero del estudio `studies/transfer/crossTF`. K y F son estadística y
clasificación (Opus); el resto es llevar a código lo ya decidido (Sonnet, regla 17).

**Tu encargo:** que el paso 12 pueda juzgar a cada madre con T0-T4 de la propuesta — PASA, LIMBO
o NO PASA cuando la ventaja tiene un pico aislado en su TF — con cada número en un solo sitio
editable, **al lado** de lo que hoy juzga (`z_new`), y devolver al dueño el paquete del corte
listo para aplicar tras la primera corrida real.

**Lee, en este orden:** `CLAUDE.md` · `CODESTYLE.md` · `studies/CLAUDE.md` ·
`/home/sergioguslw/Downloads/criterios-paso-12-otras-temporalidades-propuesta.md` (**la
especificación**; por secciones) · `studies/transfer/crossTF/README.md` ·
`docs/encargos/46-paso-10-otros-mercados-la-logica-viaja.md` (sólo su tabla de estado: el paso 10
nuevo es el molde) · el `README.md` de la carpeta que toques. **Cuando la propuesta y este
encargo no coincidan, manda este encargo.**

## §0 De dónde sale

Dueño, 2026-10-07: «Aquí tienes el set de pruebas, así como los criterios que quiero que
implementes/modifiques en lo que ya haya en el módulo de crossTF». Sus respuestas de ese día:

1. **Sección 4.** En el paso 10.5 las estrategias no llevan stop ni objetivo
   (`assets/_build.yaml:51-52`; el stop se injerta en el paso 24). Se crea `ranges.yaml`, se
   escalan con `c` los coeficientes de **bloques de condición** que multiplican una medida por
   vela, **y también** el stop/objetivo basado en ATR cuando una estrategia lo lleve.
2. **Cascada en dos fases** (§6.1), dentro del piloto.
3. **Numeración:** `11` SQX en oos1 · `11.5` criba de fase 1 (Python) · `11.7` SQX en el build,
   sólo las que siguen · `12` veredicto final (sigue significando lo mismo para lo de después).
4. **Al lado, y corta él.** Lo nuevo emite sus hechos; la regla viva sigue siendo
   `crossTF.combined.z_new` hasta que una corrida real lo valide y el dueño diga «corta».
5. **M15 activado** para madres M30. SQX construye M15 de M1
   (`knowhow/sqx-drive/custom-timeframe-h12.md`).
6. **Población de T1 y del percentil del build:** las madres comparables de esa misma corrida y
   par de TF; con menos del mínimo (`tf.frequency.min_population`, 5 de partida) → sin dato →
   LIMBO, percentil vacío.
7. **D1** (madres H1) sigue aparte, tarea propia con motor MT4: sólo fase 1, sólo se anota.

**Lo que el Council fijó** (consenso 2,625 / 3,5): núcleo como funciones puras en ficheros nuevos
probadas con respuestas conocidas sin SQX; todo lo que cambia qué son las hermanas (parte F) y
qué datos se generan (parte S) va **antes** de la primera corrida — CPU gastada con hermanas mal
fabricadas no se recupera; el corte espera a que existan datos del build; el borrado, aparte.

**Consecuencia de «al lado» mientras no haya corte:** el paso 11.5 no corta a nadie (su regla
nueva no está viva), así que **todas** las madres corren la fase 2 — justo lo que la validación
necesita. Tras el corte, 11.5 corta el pico aislado en oos1.

## K · Núcleo estadístico (Opus)

Carpeta nueva `studies/transfer/crossTF/tf/`, sin tocar `cells.py`, `verdict.py`, `many.py`.
Reutiliza, **importando sin editar** (el paso 10 nuevo está a medio cortar, encargo 46):

| pieza | dónde |
|---|---|
| desplazamiento por año natural, el mismo para todos | `studies/transfer/crossmarket/travel/shift.py` (`shift_unit: year`), `engines/nulls/placement/trade_models.py:15,61` |
| lotes por la doctrina y P/L en R | `studies/transfer/crossmarket/travel/sizing.py`, `engines/nulls/windowed.py:24,121` |
| repreciado común con costes | `engines/market/reprice.py:24,69,111` |
| sobredispersión φ | `studies/screening/analysis/centred.py:21` |
| barras de cualquier TF | `core/barstore.py` |

Si una pieza de `travel/` no admite «temporalidades de un mismo mercado» en vez de «mercados»,
envuélvela en `tf/`; no la edites ni la copies entera.

Construye, cada cosa una función pura sobre tablas de operaciones:

1. **`e`** (§2): `(T_real − media T_azar) / n`, en R, por celda (estrategia, TF, ventana).
2. **Corridas al azar** (§2.3): un desplazamiento por año natural y corrida, **el mismo para la
   madre y todas sus hermanas**, sin cruzar de ventana (2011 parte en el inicio del build de la
   ficha), lotes recalculados, `tf.null.draws` (5.000) y `tf.null.seed` fijados en `config.yaml`
   y anotados en la salida.
3. **T0** (§5): `unverified`, `clamped`, `rounding_shift > tf.comparable.rounding_shift` (0,25),
   menos de `tf.comparable.min_trades` (30) en la ventana → no comparable, con su motivo.
4. **T1** (§5, build + oos1 juntos): `z_frec` con φ acotada en `[1,5; 3,5]` y `m_pop` de la
   corrida (§0.6). 1,5 / 3,5.
5. **T2a** (oos1): `ret`, `Δ`, `z_Δ` con la nula conjunta; 0,5 · 1,65; pico aislado con 0,25.
6. **T2b** (build): `z_build`; 1,65 / 0; pico aislado = las dos vecinas ≤ 0.
7. **T3**: la lejana comparable en NO PASA (T2a) baja un PASA a LIMBO. **T4** y la retención en
   el build (percentil en la corrida): sólo anotan.
8. **Veredicto por madre** (§6) y **veredicto de fase 1** (sólo T0, T2a, T3, con lo que haya en
   oos1): la tabla de §6 entera, incluidas «una sola vecina comparable → máximo LIMBO» y
   «ninguna → LIMBO».
9. Vecinas y lejana por TF de la madre en `config.yaml` (`tf.neighbours`, `tf.far`):
   M30 → M15, H1 · lejana H4; H1 → M30, H4 · sin lejana; D1 sólo anota T2a.
10. **Entrada y salida.** Lee las operaciones como hoy (`inputs.py`: un export por databank de
    TF) más las del build: las hermanas, de los databanks de la fase 2 (parte S fija sus
    nombres en `sqx/projects/workflow.py`; acuérdalo leyendo ese fichero, no lo edites); la
    madre, de donde **ya existan** (`sqx/variants/mothertrades.py`, el export del build) — no se
    vuelve a correr en SQX. Sin datos del build, T1 y T2b son «sin dato» y la salida lo dice.
    Escribe en la carpeta de la corrida, junto a lo viejo: `tf_siblings.parquet` (una fila por
    madre × TF: T0 y su motivo, `z_frec`, `e`, `ret`, `z_delta`, `z_build`, coincidencia por
    ventana, `ret_build` y su percentil, estado por test) y `tf_mothers.csv` (una fila por
    madre: estado de T1, T2a, T2b, T3, `phase1`, `state`, semilla, corridas). Estados como
    `pass | limbo | fail`, el vocabulario de `pipeline/autopilot/criteria.py:9`.
    `many.run` y `report.py` llaman a lo nuevo **después** de lo viejo; si lo nuevo lanza, lo
    viejo ya está escrito y el error sale con su nombre (no se traga).
11. **Forex o ficha sin coste:** como el paso 10 (`travel/run.py:50`): fila con motivo, estado
    «sin dato», nunca un 0.

**Tests de respuesta conocida** (`tests/test_crosstf_tf_*.py`, sintéticos, sin SQX ni AlgoData):
hermana idéntica a su madre → `z_Δ = 0`, `ret = 1`, coincidencia 1; población de madres sin
ventaja (entradas al azar sobre un paseo con deriva) → `z_Δ` y `z_build` con media dentro de
±2 errores estándar de 0 y rechazo al 5 % cerca del nominal (**si no, para y dilo: la nula está
mal**); ventaja plantada en la madre y no en las hermanas → pico aislado → `fail`; plantada en
todas → `pass`; cada fila de las tablas de §5 y §6; mismo `seed` → mismos números.

## F · Fabricación (Opus: clasificar medidas es criterio, no mecánica)

1. `sqx/variants/ranges.yaml` (molde: `lengths.yaml`, `lengths.py`): por custom block y
   parámetro no-longitud, `bar` (multiplica una medida por vela: ATR, rango de vela) ·
   `window` (medida sobre N velas: desviación de Bollinger, máximo − mínimo) · `other`
   (umbral sin unidades de precio: percentil, nivel de un oscilador, ratio) · `unverified`.
   Clasifica **leyendo la fórmula de cada bloque**, no por el nombre; ante la duda,
   `unverified`. Los incorporados: el coeficiente de `ATRBasedValue` de stop y objetivo es
   `bar` (`sqx/variants/build/stoploss.py`, `knowhow/sqx-format/grafting-a-stop-loss.md`,
   `fixed-distance-keys.md`); su periodo de ATR literal se escala como una longitud.
2. **`c`** (§4.2): mediana del ATR en el TF de la hermana (periodo ya escalado) / mediana del
   ATR en el TF de la madre, sobre build + oos1 del activo, con `core/barstore.py`. Función
   pura sobre dos tablas de barras + envoltorio que las carga. `k_hermana = k_madre / c`.
3. `scale.sibling` escala esos coeficientes; el manifiesto gana `n_coef_scaled` y el `c` usado;
   un coeficiente sobre una medida sin clasificar marca `unverified` (ya la lee T0). Corrige el
   comentario de `sqx/variants/config.yaml:144-151` y la regla del 2026-09-23 (§4.4).
4. `assets/_build.yaml` `crosstf.timeframes`: `M30: [M15, H1, H4]`. Nada más de ese fichero
   (otra sesión lo tiene modificado: edita sólo esa línea). Antes: `python3 -m core.assets
   NIKKEI225` (regla 5) y di qué imprime.
5. Tests (`tests/test_scale_ranges.py`): serie sintética con la volatilidad por vela escalada
   por `k` → `c = k` (±1 %); M30 → M15 dobla periodos, `rounding_shift = 0`, nada recortado;
   un coeficiente `bar` se divide por `c`, uno `window` y uno `other` no se mueven; uno sin
   clasificar → `unverified`; `ranges.yaml` cubre todo custom block de `lengths.yaml`.
   `tests/test_scale_lengths.py` sigue verde.

Entrega al dueño la tabla de lo clasificado como `bar` y lo dejado en `unverified`, con el motivo
de cada uno: la revisa él.

## S · Tareas SQX (Sonnet) — sin arrancar SQX

1. Tarea `CrossTF M15` → `CrossTF_M15` sale sola de la doctrina; compruébalo en
   `sqx/projects/crosstfsolo.py:19` con un test.
2. **Fase 2:** por cada TF de hermana que juzga o frena (no D1), una tarea gemela sobre la
   ventana `build`, que lee de `CrossTF_Input` y escribe en un databank propio (nombres en un
   solo sitio, `sqx/projects/workflow.py`, junto a `CROSSTF`). `builder --workflow` las crea
   en el paso 5 como las demás (regla 10); el paso 11 enciende sólo las de oos1 y el 11.7 sólo
   las del build (`sqx.projects.stage`).
3. Un proyecto creado antes de este encargo no las tiene: quien las busque recibe una lista
   vacía, no una excepción.
4. Corrige el texto viejo `build..oos1` (`workflow.py` docstring, `summary.py:24`).
5. Tests sobre el XML generado, como `tests/test_crosstf_separate.py`.

## P · Piloto y ventana (Sonnet)

1. `pipeline/autopilot/plan.py`, `ui/daemon/launch/chainplan.py`: `11` (sqx) → `11.5`
   (python, juzga) → `11.7` (sqx, build) → `12` (python, juzga). Entre 11 y 12 **las hermanas
   no se borran** de `CrossTF_Input` (hoy `judge.py:158,168` las tira al juzgar): en 11.5 sólo
   salen las madres que fallen **y sus hermanas**; en 12, como hoy. Proyecto sin tareas de fase 2
   → 11.7 se salta con una línea que lo dice y 12 juzga con «sin dato».
2. `facts.py`: hechos nuevos **junto a** los viejos, de `tf_mothers.csv` y
   `tf_siblings.parquet`: `crossTF.tf.state`, `crossTF.tf.phase1`, `crossTF.tf.{t1,t2a,t2b,t3}`
   y `crossTF.tf.<TF>.<columna>`. Falta el fichero → no hay hechos (sin dato), no excepción.
3. `criteria.yaml`: el paso 12 conserva su regla `z_new`. El paso 11.5 existe sin regla que
   corte. **No** escribas la regla nueva en el YAML: va, lista para pegar, en «Paquete del
   corte» al final de este encargo.
4. Ventana: filas 11.5 y 11.7 en `ui/daemon/workflow/steps.py`; las columnas nuevas en
   `ui/daemon/results/` y su ayuda en `ui/text/columnhelp*.py`, junto a las viejas. Luego
   `/ui-shot` de la zona.
5. Test: el plan de un proyecto con y sin tareas de fase 2; `crosstf_rows` con y sin ficheros
   nuevos; el vocabulario de estados.

## D · Documentación (Sonnet)

README del estudio (la lectura nueva, al lado de la vieja, marcada «sin cortar»), la skill
`crosstf`, `steps.md`, `docs/AgentPDFs/WORKFLOW.md` y la fila de `CLAUDE.md` (pasos 11.5 y
11.7), el capítulo del manual si hay comando nuevo (regla 8, `/manual-chapter`), y tarjetas de
`knowhow/` para lo no obvio (que en 10.5 no hay stop; la clasificación por vela / por ventana;
que M15 dobla periodos sin recorte). `python3 tools/depmap.py && python3 tools/checks.py`.

## Decisiones del dueño — pregúntalas (regla 11)

Cerradas las siete de §0. Si al ejecutar aparece otra lectura doble, **para y pregunta**; las que
sólo el ejecutor puede enmarcar van aquí con sus lecturas:

- **K-1 · La R de `ret`.** Los lotes siguen la doctrina sobre las velas de cada hermana, así que
  1 R son 4 ATR de *su* TF. Una hermana que gana lo mismo en precio por operación que su madre M30
  lee `ret` ≈ 0,7 en H1 y ≈ 1,4 en M15 (medido en la batería sintética: 0,57 y 1,70). Las z no
  dependen de la escala; `ret` y sus umbrales 0,5 / 0,25 sí. Lecturas: (a) R propia de cada TF,
  como dice §2.3 — lo implementado; (b) llevar `e` de la hermana a la R de la madre (× `c` de la
  parte F) antes de dividir.
- **K-2 · Una sola vecina medida, y falla T2a o T2b.** §6: «decide ella, pero el máximo es
  LIMBO»; §5 define el pico aislado con las dos. Lecturas: (a) su NO PASA es el de la madre;
  (b) sin la otra no hay pico: LIMBO. Implementado: LIMBO, con `t2a_lone_fail` / `t2b_lone_fail`
  en `why`, hasta que el dueño diga. (T1 sí falla con una sola: §5 dice «alguna».)
- **K-3 · La ventana de T4.** §5: «a menos de una vela (de la madre)»; §0.1 cita el 86 % «a
  menos de una hora» para una madre M30, que es la vela de la hermana. Implementado lo de §5
  (sólo anota): en `Trade_NIKKEI225_M30_volatilidadL` la H1 más parecida da 0,44. Lecturas: (a)
  vela de la madre; (b) la más lenta de las dos.

## Lo que no tocas

El master. SQX en ninguna instalación: nada de este encargo arranca, consulta ni configura un
proyecto vivo (reglas 3, 18, 19). `oos2`. `studies/transfer/crossmarket/` y `engines/` (se
importan). `cells.py`, `verdict.py` y la regla `z_new` (hasta el corte). `ledger/thresholds.yaml`.
Ficheros de otra parte de la tabla. Ni rama, ni worktree, ni commit (regla 12).

## Verificación

```
python3 -m pytest tests/test_crosstf_*.py tests/test_scale_*.py tests/test_variants.py tests/test_autopilot*.py -q
python3 tools/depmap.py && python3 tools/checks.py
```

Lo que **no** se puede verificar sin SQX y espera a la parte V: que las tareas de fase 2 corren
y escriben en su databank; que ningún indicador rechaza un periodo doblado en M15; el coste en
tiempo de la fase 2 (decisión abierta 8.5 de la propuesta); `z_Δ` centrada en 0 con madres
reales sin ventaja (8.7).

## Paquete del corte (parte V; lo aplica quien reciba el «corta» del dueño)

**Codificación de los estados** (parte P, `pipeline/autopilot/tffacts.py`): `criteria.py` compara
números (`pass: ">= 1"`), nunca texto, así que cada estado entra como número: **pass = 1, limbo = 0,
fail = −1**; un estado que el estudio no pudo decir (celda vacía) no es hecho, y un hecho que falta
es limbo (`missing:` por omisión). Hechos: `crossTF.tf.{state,phase1,t1,t2a,t2b,t3}` por madre y
`crossTF.tf.<TF>.<columna>` por madre y timeframe de hermana (`t0`, `t1`, `t2a`, `t2b`, `z_frec`,
`z_delta`, `z_build`, `ret`, `ret_build`, `ret_build_pct`, `clamped`…).

**1 · Paso 11.5** — en `pipeline/autopilot/criteria.yaml`, sustituir `rules: []` de `"11.5"`
(conserva `cut: CrossTF_Input` y `siblings: follow`: sale la madre que caiga y SUS hermanas; las
hermanas de las que siguen se quedan para el 11.7). Sólo corta el NO PASA; limbo sigue:

```yaml
    rules:
      # Fase 1 (T0, T2a, T3 con lo que hay en oos1): pico aislado en oos1 corta; lo demás sigue
      - {name: "Fase 1 · pico aislado en oos1", fact: crossTF.tf.phase1, pass: ">= 0", else: fail}
```

**2 · Paso 12** — sustituir la regla `z_new` (`criteria.yaml:199-200`, comentario incluido) por:

```yaml
    rules:
      # Pasos 10.5-12 (encargo 47, §6): PASA / LIMBO / NO PASA por madre con T0-T4. El 12 sigue
      # tirando las hermanas (sin `siblings:`); sólo la madre pasa a CrossTF_Mothers.
      - {name: "T0-T4 · ¿pico aislado en su TF?", fact: crossTF.tf.state, pass: ">= 1",
         limbo: ">= 0", else: fail}
```

`missing:` queda por omisión (limbo): una madre sin ficheros nuevos o sin dato del build no cae,
pasa a limbo, como pide §6 («ninguna vecina comparable → LIMBO»).

**Lo que borra la parte B** (§7 de la propuesta; líneas al 2026-10-07, antes de tocar nada):

| qué | dónde |
|---|---|
| `z_new` como criterio | `pipeline/autopilot/criteria.yaml:199-200` (las dos reglas de arriba lo sustituyen) |
| `z_new`, `combined_z_new`, `combined_z_new_max`, `combined_n_tested` (Stouffer y máximo) | `studies/transfer/crossTF/cells.py:148-181` (`beyond`), su llamada en `cells.py:144` |
| `corr_vs_baseline` (ρ como entrada de fórmula) | `cells.py:135,142-144`, `cells.py:202-` (`correlations`), `many.py:101` (`correlation_grid`), `cells.py:23` (`MOST_ALIKE`) |
| las seis lecturas (`survives`, `inherited`, …) y `usable` | `studies/transfer/crossTF/verdict.py:10-17` (`MEANS`), `verdict.py:20-81` (`usable`, `read`), `verdict.py:100-` (`counts`), `many.py:17` (`MEANS_ES`), `many.py:143,175-178,214`; `config.yaml:20-41` (`usable:`, `verdict:`); `tooltips.py:16` |
| filas `unscaled` y `control` | `inputs.py:133` (`unscaled`), `inputs.py:142` (`control`), `verdict.py:83-` (`unscaled`), `cells.py:183-` (`matrix` si sólo las lee) |
| `…_vs_original`, `p_net`, `p_pf`, `p_dd`, `p_retdd` (`seen_all`, `p_all`) | `cells.py:39-77` (`numbers`) y su consumo en `pipeline/autopilot/facts.py:182-203` |
| los hechos viejos `crossTF.cells.*`, `crossTF.combined.*`, `crossTF.reading.*` | `pipeline/autopilot/facts.py:13` (`MEANS`), `:17-18` (`TARGET`), `:161-206` (`crosstf_rows`: queda sólo `tffacts.rows(folder)`), comentario `criteria.yaml:13` |
| P/L revalorado sin spread ni slippage; sorteo uniforme operación a operación | `studies/transfer/crossTF/cells.py:31-77` (`numbers`), sustituidos por `tf/null.py` y el repreciado común |
| columnas y palabras de la ventana de lo viejo | `ui/text/columnhelp_fields.py:88-100`, `ui/text/columnhelp.py:40-42`, `ui/text/columnhelp_verdicts.py:22`, `ui/daemon/results/store.py:22` (`survives`, `inherited`, `fails`) |
| sus pruebas | `tests/test_crosstf_facts.py`, `tests/test_crosstf_report.py` y lo de `tests/test_crosstf_mother.py` que lea lo viejo |

**Se mantiene** (§7): la fabricación con su manifiesto, una tarea por temporalidad, D1 aparte.
Antes de borrar: re-apuntar `many.py` / `report.py` a que la ventana lea sólo `tf_*`, y quitar las
columnas `tf_*` del prefijo (`ui/daemon/results/tfrows.py`) si el dueño prefiere los nombres sin él.

## Cómo cierras

Qué hizo · qué verificó, con la salida pegada · qué dejó sin hacer y por qué · qué descubrió
para `knowhow/` · actualiza tu fila de la tabla de estado · la lista de ficheros cambiados y
**¿Quieres hacer el commit?**
