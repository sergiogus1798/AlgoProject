# 49 · Plan vivo de las fases 0 y 1, y criterios de los pasos 10 a 20

**Qué es.** Sustituye a `41-fases-0-y-1.md` (plan vivo; su tabla de estado, con la misma
numeración 0.1-1.9) y a `43-criterios-pasos-10-a-20.md` (que era el punto 1.6). Los dos se
borran al consolidar; siguen legibles con `git show c923d10:docs/encargos/41-fases-0-y-1.md` y
`...43-criterios-pasos-10-a-20.md`. **Quien retome las fases 0 y 1 empieza aquí**: la memoria del
dueño apunta a «leer la tabla de estado antes de continuar» y esa tabla es la de abajo.
Es un plan **vivo**: cada sesión que avance un punto actualiza su fila y una línea de la
Bitácora, y no reescribe el resto. Cuando las dos fases estén cerradas, este fichero se borra
como cualquier encargo cumplido.

**Para la sesión que lo retome.** Lee `CLAUDE.md`, la tabla de estado y solo el punto que te
toque. Los puntos **DUEÑO** no se hacen por él: se le prepara lo necesario y se le pregunta.
Regla 12: nada de commits por tu cuenta. Regla 3: `ListAgents` y los candados
(`.claude/skills/sqx-wait/preflight.sh`) antes de tocar un worker.

## Estado (verificado el 2026-10-09)

Estados: ⬜ sin empezar · 🟡 en curso · ✅ hecho · 🔴 espera al dueño.
Modelo: **S** = Sonnet, mecánico · **O** = Opus, diseño o estadística (regla 17).

| # | punto | modelo | depende de | estado |
|---|---|---|---|---|
| 0.1 | Cerrar la API de SQX al exterior | — (dueño) | — | ✅ ufw + Tailscale, 2026-10-02 |
| 0.2 | Commit y push de lo pendiente | — | — | ✅ |
| 0.3 | Propuesta diaria de commit | — | 0.2 | ✅ |
| 0.4 | Copia fuera del disco | — | D6 | ✅ a mano, por el dueño |
| 0.5 | `/tmp` por debajo del 50 % tras una corrida | S | — | 🟡 hoy 67 % (93 → 54 % el 2026-10-02) |
| 0.6 | Auditoría mecánica a 0 | S | OPEN #95 | 🟡 |
| 0.7 | Documentación al día | — | 0.2 | ✅ |
| 1.1 | Hoja de decisiones en PDF | — | — | ✅ |
| 1.2 | Firma provisional de los pasos 6 y 8 | — (dueño) | 1.1 | 🔴 `dev: on: true` sigue; OPEN #93 abierto |
| 1.3 | Registro completo | S | — | 🟡 |
| 1.4 | Autopilot: lo mínimo para una población nula | S | — | 🟡 código hecho, falta la prueba en SQX |
| 1.5 | Nulos en la escala nueva de la t y curva de mínimos | O | — | ⬜ → ahora encargo **50** (ex 42 §3) |
| 1.6 | Reglas de los pasos 10, 12, 14, 16 y 20 | O + dueño | 1.2, 1.5 | ⬜ → **§3 de este fichero** (ex 43) |
| 1.7 | Monos por la cadena en Python | O | 1.3, 1.6 | 🟡 → encargo **53** (ex 9) |
| 1.8 | Monos seleccionados en SQX | O | 1.4, 1.7 | ⬜ → encargo **53** (ex 30) |
| 1.9 | Congelación final de umbrales | — (dueño) | 1.7, 1.8 | ⬜ |

**Orden.** 1.3, 1.4 y 1.5 no dependen del dueño y avanzan mientras él decide 1.2.
**Salida de la fase 0:** nada del proyecto existe solo en este disco y nadie de fuera puede
mandar una orden a SQX. **Salida de la fase 1:** un proyecto nuevo corre del paso 6 al 16
cortando por reglas firmadas, deja una fila en el registro por paso, y se sabe cuántos monos de
N llegan al final.

## Bitácora

Una línea por sesión que avance algo: fecha, punto, qué quedó.

- 2026-10-09 — consolidado a partir de los encargos 41 y 43. Se conserva de la bitácora de 41 lo
  que sigue vigente: 0.1 cerrado (2026-10-02, el dueño instaló Tailscale, servidor
  `100.113.159.40`, y `ufw` con entrada solo por `tailscale0`, 22/tcp y 3389/tcp; 5050, 5051, 5060,
  5070 y 8080 ya no responden desde fuera; queda a su decisión cerrar el 22 público); 0.3 hecho
  (`bin/nightly-commit-proposal.sh`, cron 05:45, se aplica con `python3 -m tools.commit_apply`; el
  push real con el aplicador no está probado); 0.5 y 0.6 dejaron el trabajo grande hecho el
  2026-10-02 (ver §1); 1.1 hecho; 1.7 construido el 2026-10-04 (ver el encargo 53).

---

## Tu oficio

Jefe de la fábrica de criterios: Sonnet para lo mecánico (fase 0, registro, autopilot, exponer
hechos, mover umbrales), **Opus** para lo que es estadística o diseño (calibración, equipo rojo,
síntesis para el dueño). Tu entrega es una decisión con su coste al lado, no una descripción
(CLAUDE.md, «An analysis ends in a decision»).

## Tu encargo

Dejar la fase 0 cerrada y la fase 1 lista para la firma del dueño: que **cada paso que juzga tras
el 8 tenga una regla medida en `pipeline/autopilot/criteria.yaml`, o una razón escrita de por qué
no corta**, con lo que gana y lo que cuesta en estrategias al lado; que cada paso del build al 16
deje su fila en el registro; y que el autopilot acabe limpio con cero supervivientes. Lo que firma
el dueño (1.2, 1.9 y cada criterio) se le prepara y se para.

## §0 De dónde sale

- Plan aprobado por el dueño el 2026-10-02: dossier `docs/AgentPDFs/estado-y-direccion-2026-10-02.pdf`
  §8. Unidad histórica de coste: S = una sesión corta, M = una o dos largas, L = de tres a cinco.
- Criterios de 43: «**Pasa** = probado con los datos que hay · **Limbo** = no se pudo probar
  todavía, sigue marcado · **Falla** = casi seguro azar, o un riesgo que una cuenta de fondeo no
  aguanta. **Un hecho que falta es Limbo** (dueño, 2026-10-01): no lo cambies; lo que deba fallar
  lleva su regla explícita.» El dueño quiere criterios que descansen en estadística y que acepten
  que el mundo es imperfecto: donde los datos no fijan una cifra, se dice y se toma la prudente.
- «**Todas las supervivientes del 16 en adelante pasan por 16.5-19 sin filtrar**» (dueño; memoria
  `workflow-todas-las-supervivientes-por-los-4`).
- El dueño dijo (2026-10-07) que **fijará él los criterios** del paso 16; los umbrales de 10, 14
  y WFC son «provisionales, sin calibrar» por escrito en `criteria.yaml`.
- El catálogo de las 105 decisiones abiertas por paso, con sus códigos (`P16-1`, `T-1`…), está en
  `docs/AgentPDFs/pendientes-y-decisiones-2026-10-08.md`: **ese es el sitio donde el dueño
  contesta**; este fichero solo dice cuáles de ellas bloquean qué punto.

## §1 Fase 0 — lo que queda

0.1, 0.2, 0.3, 0.4 y 0.7 están hechos (ufw/Tailscale; propuestas de commit en
`AlgoData/audit/<fecha>-commit.md`; copia manual del dueño a su SSD; `WORKFLOW.md`, `CLAUDE.md`,
`docs/SKILLS.md` al día con 26 pasos). Quedan dos:

**0.5 · `/tmp` por debajo del 50 %** (S). El 2026-10-02 pasó del 93 % al 54 %: los temporales del
proyecto van a `AlgoData/tmp` (`core.datapaths.tmp_dir`, limpieza diaria) y `/tmp` entra en el
informe de disco con tope 80 %. Hoy está al 67 % (`df -h /tmp`: partición propia de 3,9 GB).
- Qué hacer: tras la próxima corrida completa del workflow mira `df -h /tmp` y `du -sh /tmp/* |
  sort -h | tail`; lo que sea del proyecto (exports temporales, Chrome del manual,
  `loadFilesToDatabank`) se desvía a `tmp_dir`. **Hecho:** < 50 % tras una corrida completa y el
  informe nocturno avisa por encima del 80 %.

**0.6 · Auditoría mecánica a 0** (S). Hecho el 2026-10-02: cron sin dos tareas en el mismo minuto,
reglas muertas de `project.cfx` fuera de `settings.json` (manda `guard.py`), `tools/daily_audit.py`
corre las 105 pruebas (92 pasan, 13 apartadas con motivo en `tools/audit_tests.py`). Quedaba que
salga con 0 cuando no hay nada nuevo; tres causas ajenas lo impedían (`checks.py` rojo por otra
sesión, un proyecto que no se pinta, un export sin manifiesto).
- Qué hacer: `python3 tools/daily_audit.py`, repasar lo que siga rojo contra **OPEN #95** (doce
  pruebas apartadas, cada una con su motivo; `grep -n '^## 95' OPEN.md`) y OPEN #94 (`ledger/thresholds.py`
  rompe con el feed `UKOIL.cash_M1`; verifica si sigue). **Hecho:** sale con 0 sin novedades.

## §2 Fase 1 — registro, autopilot y firmas

**1.2 · Firma provisional de los pasos 6 y 8 — DUEÑO.** Con sus decisiones contestadas, las
cifras de `assets/_study.yaml` dejan de ser «propuesta de agente», `criteria.yaml` recibe las
reglas del paso 8 y `dev.on: false`. Es **provisional** (versión 1, para dejar de sortear): la
definitiva es 1.9. Estado: la puerta por niveles del paso 8 ya está en `criteria.yaml:69` (16
reglas, encargo 44, hoy en el encargo 50) pero `dev: on: true, sample: 3, at: ["8"]` sigue
(`criteria.yaml:52`) y OPEN #93 está abierto. Antes de cambiar nada por activo:
`python3 -m core.assets <SYMBOL>` (regla 5). **Hecho:** una corrida del autopilot corta en el 8
por regla y no por sorteo, y las cifras llevan `set_by` y `set_on` en `ledger/thresholds.yaml`.
Qué se le lleva: P8-* y T-2 del catálogo de decisiones (ver «Decisiones»).

**1.3 · Registro completo** (S). Por qué: la búsqueda genética no cuenta en N y el Sharpe
desinflado sale optimista. Hecho: el build, el WFM y las poblaciones de calibración ya dejan fila
(`ledger/steprows.py`: `log_build`, `log_wfm`, `calib_rows`); cada corte del autopilot escribe la
suya con el sha256 de `criteria.yaml` (`pipeline/autopilot/judge.py`); `ledger/report.py` imprime
la N global; prueba en `tests/test_ledger_steprows.py`. Queda:
1. **Repasar que no quede un paso sin fila**: recorre los pasos del 6 al 20 de
   `pipeline/autopilot/criteria.yaml` y comprueba en una corrida (o en el código de `judge.py` y
   `steprows.py`) que cada uno llama a `ledger.record`. Un paso sin fila es una línea de test nueva
   en `tests/test_ledger_steprows.py`.
2. **El relleno hacia atrás de las 23 poblaciones `Test_Calib_*` (87.357 estrategias) está
   desfasado**: el dueño borró esa calibración entera el 2026-10-04 por spread mal (memoria
   `oos2-autorizado-para-calibrar-criterios`), y también borró sus filas del ledger contra el
   consejo del Council. `ledger.backfill --calib` y `steprows.calib_rows` siguen en el código.
   **No lo ejecutes**: es una pregunta (ver «Decisiones», T-6), no una tarea.
- **Hecho:** una corrida nueva deja una fila por paso, incluido el 6, sin intervención;
  `python3 -m ledger.report` enseña el N del estudio y el global; tarjeta en `knowhow/`.

**1.4 · Autopilot: lo mínimo para una población nula** (S). Sin esto los monos no corren por la
cadena real, porque casi todas sus corridas acaban en cero supervivientes. Hecho en código:
«cero supervivientes» es un final limpio (`pipeline/autopilot/judge.py:184`, `tests/test_autopilot_zero.py`);
un hecho que falta tiene destino explícito por regla (`missing:`); `sqx/projects/live.py:116`
`wait()` falla con límite de tiempo, puerto caído o línea de aborto; el autopilot pone
`ALGO_AUTONOMOUS=1` (rastro en `core/assetdata.py`, `ledger/gate.py`). **Queda la prueba que
cierra el punto, y necesita SQX**: tres corridas seguidas que acaban en cero supervivientes
terminan en `FIN`, y matar la JVM a media corrida acaba en un fallo con mensaje, no en una espera
infinita. Se hace con `bin/workflow.sh` sobre un proyecto `Test_` (regla 19), esperando con
`/sqx-wait` (regla 18), el worker parado al acabar, y `python3 -m sqx.projects.retire <P> --role
<role> --yes` (regla 6). Mata la JVM **por PID**, nunca `pkill -f`. Se ordena con el encargo 53
porque comparte la misma población nula; si el dueño prefiere no gastar custodio antes, queda 🟡.

**1.9 · Congelación final de umbrales — DUEÑO.** Con las tablas de monos (encargo 53) delante,
fija la versión 2 de los criterios; la pregunta deja de ser «qué umbral parece razonable» y pasa
a «cuántos monos dejo pasar». **Hecho:** `criteria.yaml` (`frozen: {on, by, sha}` que escribe la
ventana con «Congelar») y `ledger/thresholds.yaml` con fecha de congelación; desde ahí, cambiar un
umbral es una fila en el registro. Los primeros proyectos `Trade_`, solo después.

## §3 Punto 1.6 — criterios de los pasos 10 a 20 (ex 43)

**Lo que ya existe y no se rehace** (se ve en `pipeline/autopilot/criteria.yaml`):
- Paso 10: reglas P1-P9, provisionales y sin calibrar (`criteria.yaml:127`, ex 46 → encargo 51;
  dossier `criterios-paso-10-otros-mercados-2026-10-06.md`).
- Paso 11.5/12: la criba T0-T4 existe en el estudio (ex 47 → encargo 51), pero `"11.5"` tiene
  `rules: []` a la espera del «corta» del dueño (`criteria.yaml:185-194`) y `"12"` sigue con la
  única regla del Council `crossTF.combined.z_new >= 2.33` (`:195`).
- Paso 14: T1, T2 y T3 sobre el exceso (`criteria.yaml:201`), provisionales (dueño, 2026-10-07).
- Paso 17: umbrales de WFC ya en el ledger (ex 48 → encargo 52). Pasos 17-19 con reglas propias
  (`criteria.yaml:234-296`).
- Dossier por paso: `docs/AgentPDFs/criterios-paso-{10,12,14,16,20}-*.md` (cada uno cierra con
  «las decisiones que te quedan», con coste en estrategias).

**Lo que queda, y es exclusivo de este punto:**

1. **Exponer los hechos del paso 16** (S). `"16"` sigue con `rules: []` y comentario del Council
   (`criteria.yaml:225-229`): «Falla solo si la solución es un pico aislado o si media de la rejilla
   − 1 σ < 0». Falta exponerlos como columnas numéricas: media, desviación y media−desv del
   beneficio (ya vienen en el export de SQX), rango del real, distancia del real en IQR (ya en
   `verdict.csv`), percentiles de `oos1`, y los 37 `spp.verdict_csv.*` que no estaban en el
   `hechos.parquet` del 2026-10-04 (114 contra 151 claves). Archivos: `pipeline/autopilot/facts.py`,
   `studies/breakage/spp/` (`verdict/`, `one.py`, `README.md`). Comprobar con
   `python3 -m pipeline.autopilot.facts --project <P> --step 16`. El dossier del paso 16 (§6.3,
   decisión 5) lo cuenta como trabajo de código, coste en estrategias 0. **Reescribir contra el
   código actual:** el `segment: oos1` de `criteria.yaml:227` engaña (todos los hechos son del
   build): documéntalo o corrígelo según P16-2.
2. **Paso 20 sin entrada en `criteria.yaml`** (no hay `"20"`): definir qué es «pasar» es la decisión
   P20-1 del dueño. Hasta entonces, anotar en el YAML la razón de que no corte.
3. **Mover los umbrales de crossmarket, crossTF, mcRetest y SPP a `ledger/thresholds.yaml`**
   (S; verificado 2026-10-09: ningún `config.yaml` de los cuatro lleva `ledger:` y el ledger no
   tiene claves `crossmarket.*`, `crossTF.*`, `mcRetest.*` ni `spp.*`; WFC ya está, 19 filas
   `wfc.*`). Filas al final de su sección con `set_by`, `set_on`, `why` y `source`; el
   `config.yaml` pasa a `ledger:<clave>` (mecanismo en la cabecera de `ledger/thresholds.yaml`);
   comprobar con `python3 -m ledger.report --check-thresholds` y `tests/test_thresholds.py`. Los tres del
   Monte Carlo son provisionales desde OPEN #19. Ficheros: `studies/transfer/crossmarket/config.yaml`,
   `studies/transfer/crossTF/config.yaml`, `studies/breakage/mcRetest/config.yaml`,
   `studies/breakage/spp/config.yaml`. Ojo: el `crossmarket/config.yaml` tiene una parte de
   «cómo se mide» (`travel.draws`, `validity`, `degradation`…) que no son umbrales de juicio:
   decide por clave cuál va al ledger y deja la regla en `criteria.yaml`.
4. **Calibrar con poblaciones nula y plantada** (O). **Bloqueado por el encargo 50** (poblaciones sin
   seleccionar, gemelas aleatorias, nulos, criterios de 6-8) y por el carril de SQX que el dueño
   elija para los pasos 9, 11, 13 y 15 (también por un solo comando, regla 19). Método, por paso y
   en este orden:
   1. *Qué calcula el paso de verdad* (un agente por paso, solo lectura, informe a disco):
      fórmulas de la tarea de SQX y del estudio de Python, nulos y cada clave de hecho. Verifícalas
      contra el código: la estadística central del paso 8 tenía un error de unidades que nadie
      había visto.
   2. *Primero los hechos* (`python3 -m pipeline.autopilot.facts --project <P> --step <N>`).
   3. *Entrada del paso:* lo que el anterior deja pasar con sus criterios **más una muestra sin
      seleccionar** de lo que falló; largo y corto, genética y aleatoria, M30 y H1.
   4. *Un nulo sobre la misma estadística* que calcula el paso (misma contabilidad, mismo ajuste de
      deriva, mismo N efectivo): un paso que «pasa» donde el anterior no encontró enriquecimiento
      está leyendo suerte.
   5. *Cada regla candidata* con qué deja, qué parte de lo bueno pierde, elevación, intervalo
      agrupado por estructura, tasa de falsos positivos en los nulos y **efecto en solitario**
      (fuera las que nunca disparan solas, salvo redes de seguridad baratas). «Buena» se define con
      datos que la regla no lee; tasas, no recuentos.
   6. *Cuánta evidencia nueva añade el paso* (ninguna estrategia es significativa por sí sola tras
      la búsqueda; un paso que vuelve a leer `oos1` añade poco: dilo con su número y di qué pasos
      son el mismo eje).
   7. *El riesgo flotante* donde el paso lo ve (peor día, peor MAE, drawdown sobre neto anual, en
      R): las cuentas de fondeo se juzgan por el flotante.
   8. *Equipo rojo* con contexto limpio (CONFIRMADO / FALSO / EXAGERADO / SIN APOYO por afirmación)
      y validación por el camino real (`facts.per_strategy` → `criteria.resolved` →
      `criteria.outcomes`): el embudo del 8 al 20, por población y agrupado.
   9. *Lo que se midió a posteriori se prueba dentro de SQX* con un A/B (misma caja, un brazo por
      ajuste): un filtro dentro de una tarea cambia lo que la tarea produce.
   Trampas ya pagadas: como mucho 8-12 procesos de Python y 25 GB libres (64 lecturas por
   estrategia en paralelo mataron la sesión y el custodio); nunca `pkill -f`; el mono con `--seed`
   o su p no se repite; ficheros grandes a `AlgoData`, no a `/tmp`; un umbral elegido tras leer un
   segmento lo gasta: di qué segmento usó cada paso y congela las cifras antes del siguiente
   build. `oos2` **no se lee** sin autorización del dueño para esta tarea (su autorización de
   2026-10-02 murió con la calibración borrada).
5. **Entrega:** las reglas de 10, 12, 14 y 16 en `criteria.yaml` como **propuesta de un agente**
   hasta la firma (las del Council se confirman, corrigen o quitan, cada una con su dato); un
   dossier en castellano en `docs/AgentPDFs/` con su PDF (`/dossier-pdf`): una tabla por paso
   (regla · gana · cuesta · falsos positivos · segmento que gastó) y el embudo entero; fichas de
   `knowhow/` por cada hecho no obvio; capítulo del manual de lo que cambie (regla 8).
   **Hecho:** ningún paso que juzga tiene `rules: []` sin una razón escrita al lado
   (`grep -n 'rules: \[\]' pipeline/autopilot/criteria.yaml`).

## Decisiones del dueño — pregúntalas (regla 11)

Cada una lleva su código del catálogo `pendientes-y-decisiones-2026-10-08.md` (el número de
línea de cada una es el de ese fichero) y las lecturas ya escritas allí y en el dossier del paso.

- **(ex 43, D1) El paso 16 (SPP)** → `P16-1` (línea 573). Hoy «un mapa, no un filtro». Lecturas:
  (a) `criteria.yaml` dice por escrito que no corta (coste 0, ganancia 0); (b) descarte con un hecho
  existente `spp.panel1.net_profit.p10 >= 0` (3 de 10: F, `16.5.352`, `19.2.363`), con `else:
  limbo` si solo marca; (c) `area_de_meseta >= 0.7` (2 de 10); (d) `net_profit.p5 >= 0` (4 de 10).
  Sin tasa de falsos positivos conocida hasta correr una población sin ventaja por 15-16 (26 min
  por 10). Dependen: `P16-2` (build u `oos1`) y `P16-3` (`spp.verdict.pass`, `area_de_meseta`, marca
  de pico).
- **(ex 43, D2; ex 41, D3) Qué es pasar el paso 20** → `P20-1` (línea 872): decisiones 1-7 del
  dossier `criterios-paso-20-analisis-conjunto-2026-10-08.md` §6 (aplicar DESCARTAR; qué es
  REVISAR —hoy «se queda»—; «peor» provisional; SPA/StepM; estandarización del SPA). El Council del
  2026-10-08 propuso mantener «peor» y elegir al final; solo Aurelio pide revisión predeclarada a
  `sin_fallo`. También `P20-2` (¿un agente autónomo lee `oos2` para BlindJoint?).
- **(ex 43, D3) El paso 14, ¿solo mata?** → `P14-8` (línea 538): el Council lo dejó así
  («sobrevivir no es evidencia»); ¿lo mantiene si los datos dicen que además discrimina? Cuelgan
  `P14-2`, `P14-3` y `P14-7` (cortes del veredicto antiguo de `gates.py`).
- **(ex 43, D4) El paso 12 nunca falla** (debajo de la línea es Limbo) → `P12-6` (línea 467) y
  `P12-1` (¿das el «corta» a T0-T4?). Ver encargo 51.
- **(ex 43, D5; ex 41, 1.2/1.9) Adoptar cada criterio y apagar `dev.on`** → `T-8` y `T-9` (líneas
  945, 952): cómo se firma un criterio como «tuyo» y si el archivo se sella (`frozen`). Tráele
  la decisión con su coste y para.
- **(ex 41, D1-D5 de la hoja 1.1, todavía vivas)** — hoja en `decisiones-pendientes-2026-10-04.md`:
  - *D1 suelo de operaciones/año del build*: `_study.yaml` proponía 30 (H1, M30) y 20 (H4); la regla
    del dueño es 40-50; subir de 20 a 50 baja el rendimiento de 31,7 a 8,6 por mil. (Hoy rige 35/año
    en M15, M30 y H1 y 20 en H4, dueño 2026-10-09, memoria `minimo-operaciones-por-ano`: confirma
    con el encargo 50 si esto cierra la D1.)
  - *D2 regla del paso 8 y sobre qué t*: recomendación del equipo rojo `drift_excess_t`, limbo
    ≥ 1,65 y pasa ≥ 2,33 (el Council 2026-10-08 sugiere R3 en 2,33 provisional; el código tenía 1,65).
  - *D4 ¿la reserva de `oos2` ata al autopilot (`ALGO_AUTONOMOUS=1`)?* → `T-2` (línea 918);
    recomendación: sí. Debe decir además si un estudio ya empezado conserva el `oos2` con el que
    empezó (`bin/monthly-oos2-roll.sh` lo alarga cada mes (sábados, 02:05); decisión del dueño del 2026-09-30, no
    se toca).
  - *D5 ¿monos antes de mirar supervivientes reales?* Recomendación: sí, primero el 9, luego el 30
    (encargo 53). Hoy el catálogo lo lleva como `T-1` (quién autoriza el gasto de `oos2` en la
    calibración nula y plantada).
- **(ex 41, 1.3) Relleno hacia atrás de `Test_Calib_*`** → `T-6` (línea 937): la calibración se
  borró el 2026-10-04. Lecturas: (a) no se rellena nada (el objetivo ya no existe); (b) se
  rellenan solo las poblaciones que sobrevivan en disco; (c) otra. Y qué cuenta como N: ¿estrategias
  generadas (millones) o aceptadas (4.600 o 4.238)? Cambiarlo altera todos los ajustes por pruebas
  múltiples.
- **(ex 41, 0.1) Cerrar el 22 público** y dejar el SSH solo por Tailscale: abierto, del dueño. (D7:
  no toca el cortafuegos salvo necesidad extrema; se quedó fuera una vez y hubo que reinstalar.)
- **(ex 41, 0.4, D6) Copia nocturna automática:** hoy no hay; lo importante está en GitHub y el
  dueño copia el resto a mano a su SSD. Si quiere automatizarla: destino (segundo servidor por SSH
  o almacenamiento de objetos) es gasto, suyo. Plan que quedó escrito: `restic` en `~/.local/bin`
  (aquí `sudo` pide contraseña), cifrado, 7 diarias y 4 semanales, cron 05:30; se copiaría
  `AlgoData` sin `raw/`, `scratch/` ni `snapshots/` (~40,6 GB), `user/projects` y bloques y
  plantillas propios de las tres instalaciones, `config/machine.yaml` y la carpeta de memoria de
  `~/.claude/projects/`; «Hecho» = restauración de prueba de un proyecto de SQX y un estudio.
- **(ex 41, 1.7) Cómo dimensionar el mono** (cruzan el paso 8 entre 14 y 36 de 3.000 según el
  dimensionado): decisión del dueño, en el encargo 53.

## Lo que no tocas

- El master. **`oos2`**, reservado: no se lee sin autorización del dueño para esta tarea.
- Los criterios de los pasos 6 y 8: son del encargo 50. Si un hallazgo los contradice, se anota.
- La campaña (`pipeline/campaign/`): la lleva otra sesión. El riesgo por operación y las sesiones.
- Los ficheros de los encargos 50-56 (cada uno el suyo). `docs/DEPENDENCIES.md` se regenera, no
  se mezcla; `ledger/thresholds.yaml` gana filas al final de su sección.
- Nada de SQX fuera de `bin/workflow.sh` ni sin `/sqx-wait`; ningún proyecto fuera de
  `Test_`/`Trade_`/`Research_`; un `Test_` se retira al acabar.

## Objetivo — un comando

El punto de cierre de este plan es la firma del dueño (1.2, 1.9) y dos corridas en SQX (1.4 y la
calibración del §3.4): **no se puede reducir a un comando**, por lo que este encargo se ejecuta a
mano, sin bucle. Verificación:

1. `python3 tools/depmap.py && python3 tools/checks.py && python3 -m pytest tests/test_ledger_steprows.py tests/test_autopilot_zero.py tests/test_thresholds.py -q`
2. `python3 -m ledger.report --check-thresholds`: cada fila de crossmarket, crossTF, mcRetest y
   SPP dice «se lee del ledger» (§3.3).
3. `grep -n 'rules: \[\]' pipeline/autopilot/criteria.yaml`: cada resultado lleva su razón al lado.
4. `python3 -m pipeline.autopilot.facts --project <P> --step 16`: todos los hechos de las reglas
   del 16 existen (§3.1).
5. `python3 tools/daily_audit.py` sale con 0 (0.6) y `df -h /tmp` < 50 % tras una corrida (0.5).
6. 1.4: las tres corridas a cero supervivientes y la JVM matada, con la salida pegada.
7. El embudo por el camino real y el informe del equipo rojo, pegados (§3.4).

## Cómo cierras

Qué hiciste · qué verificaste, con la salida pegada · qué dejaste sin hacer y por qué · qué
descubriste para `knowhow/` · la tabla de estado y la Bitácora al día · los ficheros cambiados y,
como última línea, **¿Quieres hacer el commit?**

---

## Lo que sólo vivía en los encargos de origen

- **Fase 0, detalle de 0.1 (cerrado):** puertos que se cerraron a todo el que no fuera la propia
  máquina: 5050, 5051, 5060, 5061, 5070, 5071, 8080, 8081, 8082 y el del demonio de la ventana;
  la tarjeta `knowhow/sqx-drive/api-no-auth.md` es donde queda el estado. Antes de activar un
  cortafuegos se permite el puerto por el que entra uno (SSH u otro).
- **Fase 0, 0.6:** crontab sin dos tareas en el mismo minuto (sábado: datos 02:00 y `oos2` 02:05);
  quedaba por corregir el comentario del crontab del `fixer` (habla de rama y worktree) y el del
  conserje. Compruébalo antes de darlo por hecho.
- **0.2/0.3:** la propuesta de 24 commits (372 rutas) y la de 7 grupos se aplicaron; el
  `nightly-commit-proposal` sustituyó (2026-10-03) al script antiguo que corría `/sync` solo.
- **1.5 (se mueve al encargo 50):** OPEN #91 (los nulos de `AlgoData/scratch/null-fpr-2026-10-01`
  usaron la fórmula con el fallo y operaciones cerradas; recalcular sobre `trade_t` y
  `drift_excess_t`) y OPEN #88 (la curva diaria de SQX es el mínimo del día; decidir por estudio
  WFC, CSCV, snoopingScreen, blindJoint, exposure si se reconstruye con
  `portfolio/common/construct/equity/`). El catálogo lo lleva como `T-5`.
- **1.7 (se mueve al encargo 53):** estado a 2026-10-04: `studies/screening/falsePositives/`
  construido (`python3 -m studies.screening.falsePositives.report`); aplicado el paso 8 (14 de 16
  reglas; faltan las dos que piden el escaneo de ticks); los pasos 10, 12 y 14 no tienen mono y
  dejan pasar a todos; prueba pequeña sobre `Test_XAUUSD_donchianUpperCrossUp2_H1` (300 donantes
  × 10); las cosechas de USDJPY del 27 al 29-09 no reconcilian (anteriores al cambio de reloj de
  los feeds), USDJPY espera una cosecha nueva. Falta: el mono del paso 10, la corrida a 10.000
  con `--ledger` y la tasa por umbral. Dos activos: USDJPY y XAUUSD. El encargo 9 estaba
  «aparcado» desde 2026-09-26; D5 lo reabrió.
- **1.8 (encargo 53):** una corrida de autopilot por población, proyectos `Test_`, retirados al
  acabar. Mide los falsos positivos **con la selección del build incluida**, lo que el 9 no ve.
- **Aviso de calendario:** `bin/monthly-oos2-roll.sh` corre los sábados a las 02:05 (cron) y
  alarga `oos2` hasta fin del mes anterior (decisión del dueño, 2026-09-30).
- **Veredicto del Council, 2026-10-08, sobre las seis decisiones raíz** (en el catálogo, líneas
  19-95): sellar `oos2` hoy y apagar el sorteo; no congelar números, lo no medido cuenta Limbo;
  prueba de viabilidad primero (¿existe un mono del 10 al 19? ¿separan 16.5-19 plantadas de monos?)
  con **cadena entera** si sí y **cadena corta** (se congelan 6-14, 16.5-20 como anotación, solo se
  calibra el 8) si no. Invalidaciones con fecha 2026-10-15. Condiciones, no decisiones tomadas:
  el dueño las puede aceptar o no.
- **Trampa de coste:** cada pulso de espera en la conversación relee todo el contexto: una sola
  espera en segundo plano (regla 18).
