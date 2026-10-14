# 51 · Pasos 10 a 12: «¿la lógica viaja?» y «¿pico aislado en su TF?» — lo que falta — plan vivo

> **Plan vivo, consolidado el 2026-10-09** de los encargos 46 (paso 10, otros mercados) y 47 (pasos
> 10.5-12, otras temporalidades), ya borrados. Lo construido está en el código y se cita en una
> línea; aquí sólo queda lo pendiente. Cada sesión actualiza la tabla y la bitácora y no reescribe el resto.

| frente | qué | modelo | depende de | estado |
|---|---|---|---|---|
| 1 | calibrar P1-P9 del paso 10 (poblaciones nula y con ventaja plantada) y cerrar OPEN.md #22 | Opus (estadística) | el sí del dueño (D-1) | pendiente |
| 2 | la pestaña Cross Market de la ventana: lista de 12 puntos abiertos, captura y manual | Sonnet | `/ui-shot` con proyecto elegido (parte 3.A) | pendiente |
| 3 | limpieza de lo huérfano: `engines/nulls/placement/`, informes y capturas viejos de crossmarket | Sonnet | D-4, D-5 | pendiente |
| 4 | parte V del paso 12: primera corrida real en SQX (tareas de fase 2, M15, `k/c`, `z_Δ` centrada, coste) | Sonnet (la corrida) · Opus (leerla) | `bin/workflow.sh`, custodian libre | pendiente |
| 5 | el corte del paso 12: pegar el paquete en `criteria.yaml` | Sonnet | frente 4 y el «corta» del dueño | pendiente |
| 6 | parte B del paso 12: borrar la lectura vieja `z_new` | Sonnet | frente 5 | pendiente |

## Bitácora

- 2026-10-09 · Consolidado desde los encargos 46 y 47. Hecho y verificado ese día contra el árbol: ver §0.

**Tu oficio:** ingeniero de los estudios `studies/transfer/crossmarket` (paso 10) y
`studies/transfer/crossTF` (pasos 10.5-12). La calibración y la lectura de la corrida real son
estadística (**Opus**); la ventana, los borrados y los textos son mecánicos (**Sonnet**, regla 17).

**Tu encargo:** que los pasos 10 y 12 dejen de ser «provisionales y sin calibrar». Devuelves al dueño
(a) la calibración de las líneas de P1-P9, cada umbral con lo que gana y lo que cuesta en estrategias
al lado; (b) el resultado de la primera corrida real del paso 12 y el paquete del corte listo para
aplicar; (c) la pestaña Cross Market vista y documentada. Una línea que «apenas ayuda» se dice.

**Lee, en este orden:** `CLAUDE.md` · `CODESTYLE.md` · `studies/CLAUDE.md` ·
`studies/transfer/crossmarket/README.md` y `travel/README.md` · `studies/transfer/crossTF/README.md`
y `tf/README.md` · las especificaciones **solo por secciones**: paso 10,
`docs/AgentPDFs/criterios-implementados-2026-10-12.md` (la copia de `~/Desktop/` fue a la
papelera); paso 12, `/home/sergioguslw/Downloads/criterios-implementados-2026-10-12.md`
(copia en `docs/AgentPDFs/criterios-implementados-2026-10-12.md`). Cuando una
especificación y este encargo no coincidan, manda este encargo.

## §0 De dónde sale

Dueño, 2026-10-06/07, al entregar las dos propuestas: «Analiza lo que ya hay implementado y
modifícalo/cámbialo o borra si ya no es necesario […] o implementa lo nuevo […] con input parameters
configurables», y «Aquí tienes el set de pruebas, así como los criterios que quiero que
implementes/modifiques en lo que ya haya en el módulo de crossTF». El Council (Torvalds, Musashi,
Feynman) revisó los dos planes: núcleo como funciones puras con batería sintética de respuesta
conocida, lo que cambia qué datos se generan antes de gastar CPU, el corte y el borrado al final.

**Ya hecho — no se rehace** (verificado 2026-10-09):

| bloque | dónde vive |
|---|---|
| paso 10, núcleo (corridas al azar conjuntas, tamaño por doctrina, P/L en R, tensor), P2-P9, controles 7.1, ejecutor, juicio sobre el bruto | `studies/transfer/crossmarket/travel/{cells,sizing,shift,tensor,stat,validity,frequency,units,rules,records,run}.py`, tests `tests/test_crossmarket_travel{,_rules,_gross}.py` (commits `48a2f38`, `0997c83`) |
| P1, detector de distancias fijas | `sqx/inspect/strategymeta/fixed_distance.py`, `tests/test_strategymeta_fixed_distance.py`, tarjeta `knowhow/sqx-format/fixed-distance-keys.md` |
| el corte del paso 10 (diez reglas en `criteria.yaml`) y el borrado de `simulate/` y `verdict/` | `pipeline/autopilot/criteria.yaml:127` (paso `"10"`); el módulo pasó de 6.836 a 1.765 líneas |
| diagnóstico de la media +1,72 de las diez y sus arreglos (huecos de feeds por (mercado, celda), juicio sobre el bruto) | `travel/tensor.py` (`displaced_share`, `exclude`), `travel.judge_on: gross` en `config.yaml` |
| `e_principal` (denominador de P7) | **ya no espera al paso 8**: lo calcula crossmarket (`travel/run.py:88` `_e_principal`, 2026-10-09). Tarjeta `knowhow/pipeline/step10-p1-p7-never-have-data.md` |
| pasos 10.5-12, núcleo T0-T4 | `studies/transfer/crossTF/tf/{inputs,null,rules,run,table}.py`, tests `tests/test_crosstf_tf_{null,rules}.py` |
| fabricación escalada: `ranges.yaml`, cociente `c`, M15 | `sqx/variants/{ranges.yaml,ranges.py}`, `tests/test_scale_ranges.py`, tarjeta `knowhow/sqx-drive/crosstf-scaling-coefficients.md` |
| tareas de fase 2, pilotos 11.5 y 11.7, hechos `crossTF.tf.*`, filas de la ventana | `tests/test_crosstf_phase2.py`, `pipeline/autopilot/tffacts.py`, `tests/test_autopilot_crosstf_cascade.py`, `ui/daemon/workflow/steps.py` (commit `7224b58`) |
| ventana, paso 10: `CHOICES` de `knobs.py`, un «?» por hoja de `travel`, `only_options` con el principal y etiqueta `alias`, ejemplos de `table.py` | `ui/daemon/results/knobs.py`, `studies/transfer/crossmarket/tooltips.py`, `ui/daemon/runner/transfer.py` (2026-10-09) |

**Decisiones del dueño ya tomadas que acotan este frente:**

- Paso 10 (2026-10-07, «lo dejo a tu criterio»): el criterio nuevo sustituye al vivo; **P1 se marca y no
  saca nada del retest** (no hay gancho en el paso 9: 28 de 6.000 estrategias); `DeadZonePip` del WAE y
  `#StopLossInPips#` **no** cuentan en P1; `0,25 ATR` de `max_fill_error` se queda; se juzga sobre el
  **bruto en R** (decisión 10 = a). Los umbrales viven en `config.yaml › travel:` (lo que define el
  cálculo) y en `criteria.yaml` (lo que corta), ambos editables desde la ventana.
- Paso 10, 2026-10-09: la comprobación de la media de las diez dentro de ±0,63 es **humo**, no puerta;
  la puerta es la batería sintética (ya verde: 11/11).
- Paso 12 (2026-10-07): cascada en dos fases (11.5 criba en oos1, 11.7 SQX en el build, 12 veredicto);
  numeración `11 / 11.5 / 11.7 / 12`; **al lado y corta él**: lo nuevo emite hechos y la regla viva sigue
  siendo `crossTF.combined.z_new` hasta el «corta»; M15 activado para madres M30; población de T1 y del
  percentil = las madres comparables de la misma corrida y par de TF (mínimo `tf.frequency.min_population`,
  5; por debajo, LIMBO); se escalan con `c` los coeficientes `bar` y el stop/objetivo por ATR.
- **D1 está fuera del crossTF** (dueño, 2026-10-09): ninguna hermana ni tarea D1, sin motor MT4.
  El texto de 47 sobre «D1 sólo anota» y «lo de H1 → D1» está caducado: no lo implementes; el
  `assets/_build.yaml:165` ya lo dice.

## 1 · Calibrar P1-P9 (Opus; frente 1)

**Estado.** Las líneas del paso `"10"` de `pipeline/autopilot/criteria.yaml:127-183` son las de la
propuesta y llevan el aviso «PROVISIONAL y SIN CALIBRAR». `dev.on` sigue encendido. Nadie ha pasado por
el paso 10 una población sin ventaja ni una con ventaja plantada. Con los arreglos del 2026-10-09
(P1 lee los databanks de los workers; `e_principal` propio) casi nadie pasa P7 todavía
(`knowhow/pipeline/step10-p1-p7-never-have-data.md`).

**Qué haces** (el dueño debe decir sí antes: D-1; regla 19, la población se construye por
`bin/workflow.sh`, nunca paso a paso; regla 10, proyecto propio; regla 5, `python3 -m core.assets <SYMBOL>`):

1. Una población **sin ventaja** (entradas al azar sobre barras reales de los once mercados; ya existe el
   molde en `AlgoData/scratch/paso10_travel/2026-10-07-huecos/` y `…-bruto/`) y una con **ventaja
   plantada** (en el principal, y en todos los mercados) pasadas por `travel.run`
   (`studies/transfer/crossmarket/travel/run.py`).
2. Para cada línea de P1-P9 (§1 del contrato de abajo): tasa de falsos positivos sobre la nula y tasa de
   detección sobre la plantada, **con el coste en estrategias al lado**. Una línea que no separa se dice.
3. Reescribir contra el código actual: las líneas de `criteria.yaml` que cambien, con su comentario;
   quitar el aviso PROVISIONAL sólo de las calibradas.
4. Cerrar `OPEN.md` #22 con `/open-close` (`grep -n '^## 22' OPEN.md`).

**Contrato de columnas** (la única copia de la tabla del encargo viejo; las columnas están en
`travel/run.py` y en `criteria.yaml`): 7.1 `markets`, `markets_valid`, `invalid_fraction` (≤ 0,25 o Limbo) ·
P1 `fixed_distance` (0 pasa) · P2 `freq_off`, `freq_off_fraction` (0 pasa · 1-2 Limbo · ≥3 o >0,25 Falla) ·
P3 `z_conj`, `p_conj` (≥2,33 · ≥0 · <0) · P4 `z_conj_v2` (≥0 · >−1,65 · ≤−1,65) · P5 `z_minus_market`
(≥1,65) · P6 `p_breadth` (≤0,10) · P7 `tau_half`, `e_principal` (≥0,5 · >0 · ≤0) · P8 `worse`,
`worse_fraction` (≤1 · 2 · ≥3 o >0,25) · P9 `z_beta`, `e_end` · anota `net_t_pooled`, `trades`. Sin
dato = celda vacía, nunca 0. `config.yaml › travel:` lleva `draws 5000`, `seed 20261007`, `shift_unit
year`, `shift_step week`, `min_trades_market 30`, `worse_z −1,65`, `frequency {z 3,5, phi_min 1,5,
phi_max 3,5}`, `validity {point_value_margin 0,02, flat_atr_fraction 0,02, max_fill_error 0,25,
max_displaced_share 0,20}`, `degradation {min_trades_year 30, min_years 4}`.

**Pregunta que la calibración debe responder con números:** las diez de referencia dieron media de
`z_conj` **+1,45 sobre el bruto** (tras quitar los sesgos del aparato, que sumaban +0,3 a +0,45): el resto
vive en los años del build, estrategias ajustadas a su época; una población de ATR alto queda en **+0,30**
sobre el bruto (V0 −0,56 · V1 +0,45 · V2 +0,14), un resto que no es coste y no se ha explicado (D-2).

**Puerta:** `python3 -m pytest tests/test_crossmarket_travel*.py tests/test_strategymeta_fixed_distance.py
tests/test_autopilot_facts.py -q` verde, y un informe con la tabla línea × (falsos positivos,
detección, coste en estrategias), en `AlgoData/scratch/paso10_calibracion/` (regla 7).

## 2 · Parte V del paso 12: la primera corrida real (frente 4)

Es lo único que SQX puede verificar y que nada más cierra (`OPEN.md` #108,
`grep -n '^## 108' OPEN.md`). Se corre **sobre un proyecto propio** por `bin/workflow.sh run` o
`template` (regla 19), con la espera de `/sqx-wait` (regla 18: un comando en segundo plano, un aviso),
nada pesado al lado, `oos2` sin leer. Antes: `.claude/skills/sqx-wait/preflight.sh`. El corte exige:

1. Las tareas de fase 2 corren y escriben `CrossTF_<TF>_build`; si una tarea relanzada **sobrescribe o
   añade** a su databank; un 11.5 repetido no lee un export viejo de `CrossTF_<TF>_build`.
2. Los periodos doblados en M15 (madres M30) los aceptan todos los indicadores.
3. `k / c` con `c < 1` puede pasar del `maxValue` de un bloque (PMax 10,99 → 15,6 en M15): ¿lo acepta SQX?
4. `apply_verdict` sobre `CrossTF_Input` en 11.5: sale la madre con sus hermanas y se quedan las demás.
5. El coste en tiempo de la fase 2 (propuesta §8.5; 160 min es el tope actual del workflow entero).
6. `z_Δ` y `z_build` **centradas en 0 con madres reales sin ventaja** (propuesta §8.7). Ojo: las `z_build`
   de las corridas anteriores a 2026-10-09 están mal (cada databank de fase 2 se agrupaba bajo el nombre de
   una hermana: `knowhow/pipeline/step12-zbuild-not-centred-and-d1-sister-empty.md`); `z_delta`, `ret`,
   `t2a` y `z_new` no se tocaron. Mide con el arreglo ya puesto.

Devuelves el informe con esas seis respuestas y los números de `z_Δ` / `z_build` por TF de hermana.

## 3 · La pestaña Cross Market de la ventana (Sonnet; frente 2)

La pestaña **no se ha mirado ni capturado nunca** con el estudio nuevo; lo de abajo viene de leer
código. Las rutas se verificaron el 2026-10-09; los números de línea de 46 estaban datados el
2026-10-07, **comprueba cada `file:line` con `grep -n` antes de editar**. Estructura actual: tres pestañas
`resumen`, `mercados`, `anos` en `studies/transfer/crossmarket/contract/tabs.py`; el estudio no decide
(`verdict = "info"`), el juez es `criteria.yaml` paso `"10"`.

**A · Poder fotografiarla.** `/ui-shot` no abre una estrategia con proyecto elegido
(`QT_QPA_PLATFORM=offscreen bin/algoui --port 8757 --shot $S --zone Databanks`). Primero una opción en
`--shot` o abrir la estrategia por código; después la captura, y el PNG al agente `uiCritic`. Para
pintar el payload completo hace falta correr `python3 -m studies.transfer.crossmarket.report --project P
--databank D --asset A --day AAAA-MM-DD [--strategy S] --set travel.draws=500` sobre un export real (sin
SQX): una carpeta que guarda sólo `travel.run` no sirve.

**B · Puntos abiertos** (numeración del inventario de 46; los 2, 3, 4 y 13 ya están hechos):

| nº | qué | dónde |
|---|---|---|
| 1 | sub-pestaña muerta «Entrada aleatoria · OOS principal»: la pestaña `oos` ya no se emite. **D-3** | `ui/desktop/studypage/ficha.py:18` (`SUBS`), `_random_oos` en ~144; `ui/desktop/studypage/compare.py:25-40`; textos de `ui/desktop/studypage/README.md:32,41` y `ui/desktop/workspace/ficha.py:100` |
| 5 | pestaña `mercados`: la barra «z de cada mercado» omite z vacías; los motivos no válidos salen crudos (`fill_mismatch 0.581 ATR`); «Válido» y «Motivo no válido» sin «?»; la tabla no colorea los mercados con `z <= worse_z` (sólo la barra) | `studies/transfer/crossmarket/contract/tabs.py` (la función de la pestaña `mercados`) |
| 6 | rol del estudio: sigue `"crossmarket": "gate"` con el comentario «DESCARTAR under the breadth floor», y el estudio nunca descarta (`many.py` `WORD = "info"`). Decidir si «gate» sigue siendo el rol (afecta a `/curate` y a la agrupación) y corregir el comentario. **D-6** | `ui/daemon/results/catalogue.py:65` |
| 7 | resumen de población: barra «z conjunta por estrategia» con el nombre crudo y 25 columnas sin ordenar por prueba; no enseña qué regla P1-P9 deja en Limbo | `studies/transfer/crossmarket/many.py` (`population`), reglas en `criteria.yaml:127-183` |
| 8 | ventanas V0/V1/V2: sólo tres filas de «Resumen» y la ayuda de `z_conj_v*`; ninguna vista lado a lado ni los años de cada una (salen de los tramos `build` y `oos1` del principal, `core.assetdata`) | `ui/text/columnhelp_fields.py` (grep `z_conj_v`) |
| 9 | «?» de las columnas de `markets.parquet` (`z, p, e, trades, z_freq, valid, invalid_reason`) y de `strategy`. **Intentado y dejado**: la clave `("crossmarket","trades")` ya existe para la columna de `verdict.csv` con otro texto; `z`/`p`/`e` serían ambiguas porque la clave es `(estudio, campo)`; la pestaña «Mercados» usa cabeceras ya traducidas. Necesita la captura para decidir | `ui/text/columnhelp_fields.py`, `ui/text/glossary_crossmarket.py` |
| 10 | ocultar columnas: `HIDDEN_FIELDS` sólo oculta `note`; con 25 columnas decidir cuáles (p. ej. `breadth_count`, `e_end_ratio`, `beta`, `markets`) quedan fuera y cuáles son la vista mínima; el orden de `layout.py` es el de `verdict.csv`, no el de P1 a P9. **D-7** | `ui/daemon/databank/table.py:21` (`HIDDEN_FIELDS`), `ui/daemon/databank/layout.py` |
| 11 | 19 carpetas `AlgoData/reports/*/*/*/crossmarket` con el esquema viejo, marcadas caducadas por `ui/daemon/results/stale.py`: dejarlas, ocultarlas o reejecutarlas (21 s por corrida de diez, sin SQX). **D-5** | `AlgoData/reports/` |
| 12 | seis `crossmarket-*.png` viejos (`barrido-bloques`, `barrido-curva`, `barrido-distribuciones`, `barrido-resumen`, `nulo-conjunto`, `salidas`) que ningún `.md` cita; el aviso «Captura pendiente» de `30-crossmarket.md:50` (el `39-crossmarket-lote.md` ya no lo lleva) | `AlgoData/manual-fuentes/assets/`, `AlgoData/manual-fuentes/30-crossmarket.md` |

Tras la captura: sustituir el aviso en el capítulo 30 (`/manual-chapter`, regla 8), borrar los seis PNG
viejos si el dueño lo confirma (D-5), `python3 tools/manual.py`, `python3 tools/depmap.py && python3
tools/checks.py`.

**C · Tests de la ventana**, por separado y con nadie más editando `ui/`:
`python3 -m pytest tests/test_ui_runner.py tests/test_ui_screen.py tests/test_ui_studypage.py
tests/test_ui_results.py -q`. Los fallos de `test_ui_*` anotados en 46 (14 fallos, 8 errores el
2026-10-07: `test_state_write_stamp_freeze`, `test_ui_batch`, `test_ui_research`, `test_ui_gate`, las
fixtures `http`/`app` de `test_ui_tearmarket`/`test_ui_tearsheet`) eran de otras sesiones; **reevalúalos
antes de tocarlos**, pueden haber cambiado.

## 4 · El corte del paso 12 (Sonnet; frente 5, tras la parte V y el «corta»)

Condiciones: la parte V del §2 entregada y el dueño dice «corta» (D-8). Aplica este paquete **tal cual**
en `pipeline/autopilot/criteria.yaml`. Hoy el paso `"11.5"` (`:185`) tiene `rules: []` con
`cut: CrossTF_Input`, `siblings: follow`; el `"12"` (`:195`) tiene la regla `z_new` en `:199-200`.
La codificación de estados es `pass = 1, limbo = 0, fail = −1` (`pipeline/autopilot/tffacts.py`;
`criteria.py` sólo compara números); un estado vacío no es hecho, y un hecho ausente es limbo.

```yaml
# 1 · Paso 11.5 — sustituir `rules: []` (sale la madre que caiga y SUS hermanas; sólo corta el NO PASA)
    rules:
      # Fase 1 (T0, T2a, T3 con lo que hay en oos1): pico aislado en oos1 corta; lo demás sigue
      - {name: "Fase 1 · pico aislado en oos1", fact: crossTF.tf.phase1, pass: ">= 0", else: fail}

# 2 · Paso 12 — sustituir la regla `z_new` (criteria.yaml:199-200, comentario incluido)
    rules:
      # Pasos 10.5-12 (encargo 47, §6): PASA / LIMBO / NO PASA por madre con T0-T4. El 12 sigue
      # tirando las hermanas (sin `siblings:`); sólo la madre pasa a CrossTF_Mothers.
      - {name: "T0-T4 · ¿pico aislado en su TF?", fact: crossTF.tf.state, pass: ">= 1",
         limbo: ">= 0", else: fail}
```

(El comentario `criteria.yaml:185-190` sobre «sin regla que corte» debe actualizarse; la referencia a
«Paquete del corte» de 47 se sustituye por este §4.) Con el corte, `missing:` queda por omisión (limbo):
una madre sin ficheros nuevos o sin dato del build pasa a limbo.

**Antes del corte, preguntar** (regla 11) las tres lecturas K-1, K-2, K-3 de «Decisiones del dueño»: la
regla pegada arriba depende de ellas. Y revisar con el dueño la tabla `bar`/`unverified` de
`sqx/variants/ranges.yaml` (D-9).

## 5 · Parte B del paso 12: borrar la lectura vieja (Sonnet; frente 6, tras el corte)

Mapa de borrado de 47, **datado 2026-10-07; releer los números de línea antes de tocar nada**. Posiciones
re-comprobadas el 2026-10-09 donde se indica; el resto, a buscar por nombre.

| qué | dónde |
|---|---|
| `z_new` como criterio | `pipeline/autopilot/criteria.yaml:199-200` (lo sustituye el §4) |
| `z_new`, `combined_z_new`, `combined_z_new_max`, `combined_n_tested` (Stouffer y máximo) | `studies/transfer/crossTF/cells.py`, función `beyond` (:162) y su llamada |
| `corr_vs_baseline` (ρ como entrada) | `cells.py` (`MOST_ALIKE` :24, `correlations` :216), `many.py` (`correlation_grid` :101) |
| las seis lecturas (`survives`, `inherited`, …) y `usable` | `studies/transfer/crossTF/verdict.py` (`MEANS` :10, `usable` :20, `read` :38, `counts` :100), `many.py` (`MEANS_ES` :17 y su uso), `config.yaml › usable:/verdict:`, `tooltips.py` |
| filas `unscaled` y `control` | `inputs.py` (~:133-145), `verdict.py:83` (`unscaled`), `cells.py:197` (`matrix`, si sólo las lee) |
| `…_vs_original`, `p_net`, `p_pf`, `p_dd`, `p_retdd` (`seen_all`, `p_all`) | `cells.py:32` (`numbers`) y su consumo en `pipeline/autopilot/facts.py` |
| hechos viejos `crossTF.cells.*`, `crossTF.combined.*`, `crossTF.reading.*` | `pipeline/autopilot/facts.py` (`MEANS` :10-, `TARGET` :19, `crosstf_rows` :143: queda sólo `tffacts.rows(folder)`), comentario de `criteria.yaml` (~:13) |
| P/L revalorado sin spread ni slippage; sorteo uniforme operación a operación | `cells.py` (`numbers`), sustituido por `tf/null.py` y el repreciado común |
| columnas y palabras de la ventana de lo viejo | `ui/text/columnhelp_fields.py`, `ui/text/columnhelp.py`, `ui/text/columnhelp_verdicts.py`, `ui/daemon/results/store.py` (`survives`, `inherited`, `fails`) |
| sus pruebas | `tests/test_crosstf_facts.py`, `tests/test_crosstf_report.py` y lo de `tests/test_crosstf_mother.py` que lea lo viejo |

**Se mantiene:** la fabricación con su manifiesto y una tarea por temporalidad (D1 fuera). Antes de
borrar: re-apuntar `many.py` / `report.py` para que la ventana lea sólo `tf_*`, y quitar el prefijo `tf_*`
de las columnas (`ui/daemon/results/tfrows.py`) si el dueño lo prefiere (D-10). Puerta: `grep -rn` de
cada nombre viejo vacío en `ui/ pipeline/ studies/ tests/`, y `python3 tools/depmap.py && python3
tools/checks.py`.

## 6 · Limpieza (Sonnet; frente 3)

- `engines/nulls/placement/*`: candidato a otra pasada tras el borrado del paso 10. **No borres** sin un
  `grep -rn` de cada símbolo en `studies/ pipeline/ tests/ ui/` y el sí del dueño (D-4); `crossTF/tf/null.py`
  y `travel/shift.py` usan `engines/nulls/placement/trade_models.py` (`block_shift`, `semester_shift`).
- Diagnósticos y copias en `AlgoData/scratch/paso10_travel/` (incluida `borrado-2026-10-07/`, la
  copia sin commit de lo borrado): conservar hasta cerrar el frente 1; después, el dueño decide.

## Decisiones del dueño — pregúntalas (regla 11)

Cada una con su origen. No pongas un valor por defecto.

- **D-1 (ex 46, dec. 5) · ¿Calibrar P1-P9 ahora?** Las líneas son las de la propuesta, sin calibrar; falta
  pasar la población nula y la de ventaja plantada. Necesita el sí del dueño antes de gastar CPU.
- **D-2 (ex 46, parte D2/G) · El resto de +0,30 en la población de ATR alto sobre el bruto.** Lecturas:
  (a) aceptarlo como tolerancia de la nula y calibrar las líneas con él; (b) buscarle causa antes de
  calibrar. No es coste. Las diez de referencia salen en +1,45.
- **D-3 (ex 46, ventana 1) · La sub-pestaña «Entrada aleatoria · OOS principal».** Lecturas: (a) quitarla;
  (b) alimentarla del mono del paso 8 (`studies/screening/gate/level3c.py`, encargo 50).
- **D-4 (ex 46, decisión 4) · Sección 8 de la propuesta del paso 10** (prior de la plantilla, factores,
  régimen, vecindad…): sólo P9 se implementó; la **8.1** es la de prioridad 1 y da la población nula para
  calibrar. Lecturas: (a) encargo aparte; (b) construirla dentro del frente 1. Y el borrado de
  `engines/nulls/placement/`.
- **D-5 (ex 46, ventana 11 y 12) · Informes y capturas viejos de crossmarket.** Las 19 carpetas de
  `reports/*/*/*/crossmarket`: dejarlas marcadas caducadas, ocultarlas o reejecutarlas. Los seis PNG
  viejos: borrarlos tras la captura nueva.
- **D-6 (ex 46, ventana 6) · ¿Sigue siendo «gate» el rol de crossmarket en el catálogo?**
- **D-7 (ex 46, ventana 10) · Qué columnas del `verdict.csv` van en la vista mínima** y en qué orden
  (el de P1 a P9 o el actual).
- **D-8 (ex 47, parte V) · El «corta»** del paso 12, con el paquete del §4.
- **D-9 (ex 47, parte F) · `CBlock_CandleBreakoutLong*.Double2`** («cuerpo de una vela > Mult × ATR»):
  `bar` (Mult multiplica una medida por vela) u `other` (ambos lados son por vela, luego es un cociente).
  Hoy `unverified` en `sqx/variants/ranges.yaml` (grep `Double2: unverified`, líneas ~55 y ~57). Y la
  revisión del dueño de la tabla `bar` / `unverified` entera (también `Double3` de la entropía y
  `Period5` del MACD, `unverified` con su motivo).
- **D-10 (ex 47, parte B) · ¿Se quita el prefijo `tf_*` de las columnas de la ventana** (`ui/daemon/results/tfrows.py`)?
- **K-1 (ex 47) · La R de `ret`.** Los lotes siguen la doctrina sobre las velas de cada hermana, así que
  1 R son 4 ATR de *su* TF. Una hermana que gana lo mismo en precio por operación que su madre M30 lee
  `ret` ≈ 0,7 en H1 y ≈ 1,4 en M15 (batería sintética: 0,57 y 1,70). Las z no dependen de la escala;
  `ret` y sus umbrales 0,5 / 0,25 sí. Lecturas: (a) R propia de cada TF (§2.3 de la propuesta; **lo implementado**);
  (b) llevar `e` de la hermana a la R de la madre (× `c`) antes de dividir.
- **K-2 (ex 47) · Una sola vecina medida, y falla T2a o T2b.** §6 dice «decide ella, pero el máximo es
  LIMBO»; §5 define el pico aislado con las dos. Lecturas: (a) su NO PASA es el de la madre; (b) sin la
  otra no hay pico: LIMBO. **Implementado:** LIMBO con `t2a_lone_fail` / `t2b_lone_fail` en `why`
  (`tf/rules.py:108,125`). T1 sí falla con una sola (§5 dice «alguna»).
- **K-3 (ex 47) · La ventana de T4.** §5: «a menos de una vela (de la madre)»; §0.1 cita el 86 % «a
  menos de una hora» para una madre M30, que es la vela de la hermana. **Implementado** lo de §5 (sólo
  anota): en `Trade_NIKKEI225_M30_volatilidadL` la H1 más parecida da 0,44. Lecturas: (a) vela de la
  madre; (b) la más lenta de las dos.

Si al ejecutar aparece otra lectura doble, para y pregunta.

## Lo que no tocas

El master. `oos2` (no se lee sin autorización expresa del dueño para esta tarea). Ningún SQX a mano:
las corridas de los frentes 1 y 4 van sólo por `bin/workflow.sh` (reglas 3, 18, 19), en proyecto
propio `Test_`/`Trade_`/`Research_`, y los `Test_` se retiran al acabar. **Otras sesiones tienen
cambios sin commit en `studies/transfer/crossTF/inputs.py`, `sqx/variants/` y `sqx/projects/`
(mercados de varias temporalidades en las madres, `OPEN.md` #110): corre `git status` antes de editar
cualquiera de esos ficheros y no mezcles su trabajo con el tuyo.** `studies/screening/gate/level3c.py`
y la puerta del paso 8 (encargo 50); la fábrica de variantes (encargo 52); `ledger/thresholds.yaml`.
Ninguna rama, worktree ni commit propio (regla 12).

## Lo que sólo vivía en los encargos de origen

Medidas y hechos que no están en ningún otro sitio del repositorio:

- **Batería sintética del paso 10 (2026-10-06):** 11 mercados, ~300 estrategias de entrada al azar: media
  de `z_conj` −0,02, desviación 1,08, rechazo del 7 % al 5 % nominal y del 1 % al 1 %.
- **Diagnóstico del +1,72 (2026-10-07):** dos sesgos del aparato (huecos de feeds de índices en V1:
  +0,35 de z en entradas uniformes; coste en R con ATR alto: +0,12 en las diez), juntos +0,3 a +0,45.
  Huecos: HK50 157, 76 y 180 días; UK100 118 y 90; AUS200 111 y 92; USA500 y USATEC 89, en 2011-2015.
  Con `max_displaced_share 0,20` caen ~10 pares (todos de V1) y la población uniforme queda en +0,06 ± 0,07.
  Por ventana antes del arreglo: V0 +0,14 · V1 +1,63 · V2 +0,75; cinco de las diez daban `z_conj` ≥ 2,33
  aunque fallaban el paso 8; P2 marcaba 5 mercados a la Strategy 19.2.363, el ejemplo de §2.4.
  Salidas en `AlgoData/scratch/paso10_travel/{diagnostico-2026-10-07,2026-10-07-huecos,2026-10-07-bruto,2026-10-07-corte,2026-10-07-tras-borrado}/`.
- **Lecturas del núcleo que el dueño aceptó (dec. 7):** los lotes de la doctrina van **sin redondear ni
  topar** (`Decimals: 2`, `MaxLots: 500` no se aplican), en la real y en las al azar; las operaciones
  cerradas **después** del fin de oos1 del principal quedan fuera de V0+V1+V2; a las desplazadas no se les
  reaplica el cierre del viernes ni «plano para entrar» (conservan su duración en barras); una entrada
  sobre barra defectuosa pasa a la siguiente barra válida; con `shift_step: day` se cuentan días hábiles.
  Añadir `travel:` al `config.yaml` cambió su huella: los resultados antiguos de crossmarket se leen
  caducados.
- **Lo no verificado del repreciado** (docstring de `engines/market/reprice.py`): cortos, comisión no
  nula, swap de forex en puntos. Anotado, no arreglado.
- **Resultados del paso 10 en las diez de referencia** tras el corte (2026-10-07): 0 Pasa, 5 Limbo, 5
  Falla; el módulo `crossmarket` quedó en 1.765 líneas y `verdict.csv` idéntico antes y después del borrado.
  `DeadZonePip` lo llevan 350 de 6.000 estrategias reales (P1 no lo cuenta).
- **Paso 12, batería sin ventaja (300 madres, 300 corridas):** media de z entre −0,09 y +0,02 (error
  0,055), desviación 0,93-1,04, rechazo al 5 % entre 3,0 % y 5,7 %. La clave del YAML es `tf.runs` (`null:`
  es None en YAML). `c` de NIKKEI225: M30→M15 0,704 · →H1 1,419 · →H4 2,833. `scale.fabricate(..., symbol)`
  saca el activo de la primera madre si no se le da (`sqx/projects/crosstfload.py` puede pasarlo); un `bar`
  dividido por `c` < 1 puede pasar de `maxValue` (PMax 10,99 → 15,6).
- **Costura de la fase 2:** `tf/inputs.build_banks` lee `build_databanks` de `blocks.json`; los exports de
  los databanks `CrossTF_<TF>_build` los hace `afterrun` solo. Vecinas y lejana en `config.yaml › tf`
  (`neighbours: {M30: [M15, H1], H1: [M30, H4]}`, `far: {M30: H4}`); T0: `rounding_shift 0,25`,
  `min_trades 30`; T1: φ en [1,5; 3,5]; T2a 0,5 · 1,65 y pico aislado 0,25; T2b 1,65 / 0.

## Verificación

El encargo no tiene un único comando que lo cierre: el frente 1 y los puntos 5-12 de la ventana dependen
de la decisión del dueño, y los frentes 4-6 de una corrida real en SQX. La lista es:

1. `python3 -m pytest tests/test_crossmarket_travel*.py tests/test_strategymeta_fixed_distance.py
   tests/test_crosstf_*.py tests/test_scale_*.py tests/test_autopilot*.py -q` verde.
2. `python3 tools/depmap.py && python3 tools/checks.py` sin problemas.
3. Informe de calibración (frente 1) entregado con la tabla línea × falsos positivos × detección × coste.
4. Informe de la parte V (frente 4) con las seis respuestas del §2 y `OPEN.md` #108 actualizado.
5. Captura de la pestaña Cross Market vista por `uiCritic`, el aviso «Captura pendiente» fuera del
   capítulo 30 y `python3 tools/manual.py` rehecho.
6. Tras el corte y el borrado: `grep -rn` vacío de los nombres viejos (`z_new`, `combined_z_new`,
   `corr_vs_baseline`, `MEANS_ES`) en `ui/ pipeline/ studies/ tests/`; `OPEN.md` #22 y #108 cerrados con `/open-close`.

## Cómo cierras

Qué hiciste · qué verificaste, con la salida pegada · qué dejaste sin hacer y por qué · qué descubriste
para `knowhow/` (tarjetas nuevas o editadas, nunca añadidas al final) · actualiza la tabla de estado y la
bitácora · la lista de ficheros cambiados y, como última línea, **¿Quieres hacer el commit?**
