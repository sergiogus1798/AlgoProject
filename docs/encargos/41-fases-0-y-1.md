# 41 · Fases 0 y 1: proteger lo hecho y que la fábrica decida — plan vivo

**Qué es.** El plan de trabajo de las dos primeras fases del dossier
`docs/AgentPDFs/estado-y-direccion-2026-10-02.pdf` (§8), que el dueño aprobó el 2026-10-02. Es un
plan **vivo**: cada sesión que avance un punto actualiza la tabla de estado de abajo y la nota del
punto, y no reescribe el resto. Cuando las dos fases estén cerradas, este fichero se borra como
cualquier encargo cumplido.

**Para la sesión que lo retome.** Lee `CLAUDE.md`, la tabla de estado, y solo el punto que te toque.
Los puntos marcados **DUEÑO** no se hacen por él: se le prepara lo necesario y se le pregunta.
Regla 12: nada de commits por tu cuenta. Regla 3: mira `ListAgents` y los candados antes de tocar
un worker.

**Unidad de coste:** S = una sesión corta · M = una o dos sesiones largas · L = de tres a cinco.

---

## Estado

Estados: ⬜ sin empezar · 🟡 en curso · ✅ hecho · 🔴 espera al dueño.

| # | punto | quién | coste | depende de | estado |
|---|---|---|---|---|---|
| 0.1 | Cerrar la API de SQX al exterior | DUEÑO (root) | S | — | ✅ |
| 0.2 | Commit y push de lo pendiente | sesión + sí del dueño | S | — | ✅ |
| 0.3 | Propuesta diaria de commit | sesión | S | 0.2 | ⬜ |
| 0.4 | Copia nocturna fuera del disco | sesión; destino del DUEÑO | S-M | D6 | ✅ a mano, por el dueño |
| 0.5 | `/tmp` al 92 % | sesión | S | — | 🟡 |
| 0.6 | Higiene de cron y de `settings.json` | sesión | S | — | 🟡 |
| 0.7 | Documentación al día | sesión | S | 0.2 | ⬜ |
| 1.1 | Hoja de decisiones D1-D5 en PDF | sesión | S | — | ⬜ |
| 1.2 | Firma provisional de los pasos 6 y 8 | DUEÑO | S | 1.1 | 🔴 |
| 1.3 | Registro completo | sesión | M | — | ⬜ |
| 1.4 | Autopilot: lo mínimo para una población nula | sesión | S-M | — | ⬜ |
| 1.5 | Nulos en la escala nueva de la t y curva de mínimos | sesión | M | — | ⬜ |
| 1.6 | Reglas de 10, 12, 14, 16 y paso 20 | sesión + DUEÑO | M | 1.2, 1.5 | ⬜ |
| 1.7 | Monos por la cadena en Python (encargo 9) | sesión | L | 1.3, 1.6 | ⬜ |
| 1.8 | Monos seleccionados en SQX (encargo 30) | sesión | L | 1.4, 1.7 | ⬜ |
| 1.9 | Congelación final de umbrales | DUEÑO | S | 1.7, 1.8 | ⬜ |

**Orden recomendado.** Fase 0 entera primero, 0.1 y 0.2 el mismo día. En la fase 1, los puntos
1.3, 1.4 y 1.5 no dependen del dueño y pueden avanzar mientras él decide 1.2.

**Criterio de salida de la fase 0:** nada del proyecto existe solo en este disco, y nadie de fuera
puede mandar una orden a SQX.
**Criterio de salida de la fase 1:** un proyecto nuevo corre del paso 6 al 16 cortando por reglas
firmadas, deja una fila en el registro por paso, y se sabe cuántos monos de N llegan al final.

---

## Fase 0 — Proteger lo que hay

### 0.1 · Cerrar la API de SQX al exterior — DUEÑO

- **Porqué.** Visto el 2026-10-02: los puertos 5050 y 5070 escuchan en `0.0.0.0` sin
  autenticación (`knowhow/sqx-drive/api-no-auth.md`) y la máquina tiene IP pública. El cortafuegos
  no se pudo leer sin root.
- **Primero, comprobar.** Desde otra máquina: `nc -zv <IP-del-servidor> 5050`. Si conecta, está
  expuesto. Mira también si el proveedor tiene un cortafuegos delante.
- **Después, cerrar.** Con el cortafuegos del proveedor o con `ufw`. **Antes de activarlo, permite
  el puerto por el que entras tú** (SSH u otro), o te quedas fuera. Puertos a cerrar a todo el que
  no sea la propia máquina: 5050, 5051, 5060, 5061, 5070, 5071, 8080, 8081, 8082, y el del demonio
  de la ventana.
- **Hecho:** el `nc` desde fuera falla en todos, y la ventana y los workers siguen funcionando en
  local. Actualizar la tarjeta `api-no-auth.md` con la fecha y cómo quedó.

### 0.2 · Commit y push de lo pendiente

- **Porqué.** 384 rutas sin commit (302 modificadas, 76 nuevas, 6 borradas) y 11 commits sin subir
  el 2026-10-02. Además bloquea al `fixer` nocturno, que no toca ficheros «de otra sesión».
- **Cómo.** El skill `/sync`: corre `tools/checks.py`, rechaza datos y `machine.yaml`, y agrupa por
  tema. La sesión presenta los grupos; el dueño dice sí; se hace commit grupo a grupo y push.
- **Cuidado.** Puede haber otra sesión trabajando: no meter en un commit ficheros a medio escribir.
  Mirar `ListAgents` y las fechas de modificación de la última hora.
- **Hecho:** `git status` limpio salvo lo que esté en curso, y `origin/master` igual a `master`.

### 0.3 · Propuesta diaria de commit

- **Porqué.** El commit sigue siendo del dueño (regla 12), pero tiene que costarle un sí.
- **Cómo.** `bin/nightly-sync.sh` existe y no está en el cron porque haría commits solo. Darle un
  modo que **solo proponga**: escribe `AlgoData/audit/<fecha>-commit.md` con los grupos y el
  mensaje de cada uno, y no ejecuta `git commit`. Va en el cron detrás del `fixer`.
- **Hecho:** cada mañana hay una propuesta, y aplicarla es un comando o una frase en el chat.
  Capítulo de manual en la misma tarea (regla 8).

### 0.4 · Copia nocturna fuera del disco

- **Porqué.** Repo, `AlgoData` y los tres SQX están en un único disco físico.
- **Decisión del dueño (D6):** el destino. Opciones: el segundo servidor por SSH si ya existe, o un
  almacenamiento de objetos barato. Es gasto, así que es suyo.
- **Qué se copia.** `AlgoData` sin `raw/`, `scratch/` ni `snapshots/` (hoy 40,6 GB en total);
  `user/projects` y los bloques y plantillas propios de las tres instalaciones;
  `config/machine.yaml`, que no está en git; y `~/.claude/projects/.../memory/`.
- **Con qué.** `restic` instalado en `~/.local/bin` (aquí `sudo` pide contraseña), cifrado, con
  retención de 7 diarias y 4 semanales. Cron a las 05:30, después de los agentes.
- **Hecho:** una restauración de prueba en una carpeta aparte recupera un proyecto de SQX y un
  estudio, y el log de la copia entra en la auditoría mecánica. Capítulo de manual.

### 0.5 · `/tmp` al 92 %

- **Porqué.** Es una partición propia de 3,9 GB y ya se llenó el 2026-09-26.
- **Cómo.** Ver qué la ocupa; lo que sea del proyecto (exports temporales, Chrome del manual,
  `loadFilesToDatabank`) pasa a una carpeta temporal dentro de `AlgoData`, resuelta en
  `core/paths.py`. Añadir `/tmp` al informe de disco nocturno.
- **Hecho:** por debajo del 50 % tras una corrida completa, y el informe avisa si pasa del 80 %.

### 0.6 · Higiene de cron y de `settings.json`

- Escalonar lo que choca: sábado 03:00 (auditoría y actualización de datos) y lunes 03:00
  (auditoría y conserje).
- Corregir el comentario del crontab del `fixer` (habla de rama y worktree) y el del conserje.
- La regla `Write(**/project.cfx)` de `.claude/settings.json` no casa con nada: arreglarla.
- La auditoría mecánica corre solo dos pruebas (`tools/daily_audit.py`): que corra todas, y
  arreglar o apartar con motivo las que fallen.
- **Hecho:** ninguna tarea arranca a la misma hora que otra; la auditoría mecánica sale con 0
  cuando no hay nada nuevo.

### 0.7 · Documentación al día

- Las contradicciones del dossier §4.4: número de pasos (20, 25, 26), pasos 9 y 22 y los building
  blocks en `WORKFLOW.md`, el título de OPEN #87, el director de investigación en
  `docs/AgentPDFs/README.md`, y `docs/SKILLS.md` sin `autopilot`, `workflow-start` ni
  `research-direct`. `WORKFLOW.md` cita `criterios-pasos-6-y-8-2026-10-02.md`, que no está.
- **Cómo.** El agente `documenter`, con esta lista.
- **Hecho:** `WORKFLOW.md`, `OPEN.md` y `CLAUDE.md` dicen el mismo número de pasos y el mismo estado.

---

## Fase 1 — Que la fábrica decida

### 1.1 · Hoja de decisiones en PDF

El dueño solo lee PDFs. Una hoja de dos o tres páginas en `docs/AgentPDFs/` con las cinco
decisiones, cada una con sus opciones, lo que cuesta cada opción en estrategias y la recomendación.
El material ya existe en `AlgoData/scratch/calib_final/` (`ab_build.md`, `final_step8.yaml`,
`criterios.html`) y en `scratch/calib_redteam/review.md`.

| | decisión | recomendación de la sesión |
|---|---|---|
| D1 | Suelo de operaciones/año del build: `_study.yaml` propone 30 (H1, M30) y 20 (H4); la regla del dueño es 40-50. Subir de 20 a 50 baja el rendimiento de 31,7 a 8,6 por mil | Que la hoja enseñe los dos lados; no hay recomendación sin su criterio |
| D2 | Regla del paso 8 y sobre qué t juzga | `drift_excess_t`, limbo ≥ 1,65 y pasa ≥ 2,33, como propone el equipo rojo |
| D3 | Qué es «pasar» el paso 20 (`joint.pieces`, `joint.population`) | Se decide en 1.6, con los nulos recalculados delante |
| D4 | ¿La reserva de `oos2` ata al autopilot (`ALGO_AUTONOMOUS=1`)? | Sí |
| D5 | ¿Monos antes de mirar supervivientes reales? | Sí: primero el 9, luego el 30 |

**Aviso con fecha:** `bin/monthly-oos2-roll.sh` corre por primera vez el sábado 2026-10-03 a las
03:05 y alarga `oos2` hasta fin de septiembre. Fue decisión del dueño el 2026-09-30 y no se toca;
pero D4 debe decir si un estudio ya empezado sigue con el `oos2` que tenía al empezar.

### 1.2 · Firma provisional de los pasos 6 y 8 — DUEÑO

- Con D1 y D2 contestadas: las cifras de `assets/_study.yaml` dejan de ser «propuesta de agente»,
  y `pipeline/autopilot/criteria.yaml` recibe las reglas del paso 8 y `dev.on: false`.
- Es **provisional**: se firma la versión 1 para dejar de sortear. La definitiva es el punto 1.9.
- Antes de cambiar nada: `python3 -m core.assets <SYMBOL>` (regla 5).
- **Hecho:** una corrida del autopilot corta en el paso 8 por regla y no por sorteo, y las cifras
  llevan `set_by` y `set_on` en `ledger/thresholds.yaml`.

### 1.3 · Registro completo

- **Porqué.** 22 ficheros y 595 filas, ninguna del paso 6. La búsqueda genética no cuenta en N y
  el Sharpe desinflado sale optimista.
- **Qué.**
  1. `sqx/projects/builder.py` o el autopilot apuntan la fila del build: cuántas generó SQX y
     cuántas aceptó (sale del log de SQX).
  2. `pipeline/autopilot/judge.py` apunta una fila por corte, con el hash de `criteria.yaml`.
  3. La WFM apunta la suya sin `ledger.backfill --blind`.
  4. Un N global entre estudios en `ledger/trials.py`, además del N por estudio.
  5. Rellenar hacia atrás las 23 poblaciones `Test_Calib_*` (87.357 estrategias), que sí se
     miraron.
- **Hecho:** una corrida nueva deja una fila por paso, incluido el 6, sin intervención;
  `ledger.report` enseña el N del estudio y el global. Prueba en `tests/`, tarjeta en `knowhow/`.

### 1.4 · Autopilot: lo mínimo para una población nula

Adelantado de la fase 2, porque sin esto los monos no pueden correr por la cadena real: casi todas
sus corridas acaban en cero supervivientes.

- «Cero supervivientes en el paso N» es un final limpio, no un `FALLO`.
- Un hecho que falta deja de ser limbo que pasa: destino explícito por regla.
- `sqx/projects/live.py` `wait()`: límite de tiempo, comprobar que el proceso vive, detectar la
  línea de error.
- Si D4 es sí: el autopilot pone `ALGO_AUTONOMOUS=1`.
- **Hecho:** tres corridas seguidas que acaban en cero supervivientes terminan en `FIN`, y matar la
  JVM a mitad de una corrida acaba en un fallo con mensaje, no en una espera infinita.

### 1.5 · Nulos en la escala nueva de la t, y la curva de mínimos

- **OPEN #91.** El nulo de `AlgoData/scratch/null-fpr-2026-10-01` usó la fórmula con el fallo y
  operaciones cerradas. Recalcularlo sobre `trade_t` y `drift_excess_t`, con costes que casen con
  una población de generación aleatoria. Volver a correr los informes anteriores al 2026-10-02 que
  se sigan usando.
- **OPEN #88.** La curva diaria de SQX es el mínimo del día. Decidir por estudio (WFC, CSCV,
  snoopingScreen, blindJoint, exposure) si se reconstruye la curva a cierre desde operaciones y M1
  (`portfolio/common/construct/equity/` ya lo hace) o se documenta el sesgo.
- **Hecho:** #91 y #88 cerrados o reducidos a una decisión del dueño con cifras.

### 1.6 · Reglas de los pasos 10, 12, 14 y 16, y el paso 20

- Una regla por paso sobre hechos que ya están en `hechos.parquet`. Propuesta de la sesión con su
  coste en estrategias sobre las poblaciones de calibración; firma del dueño.
- Mover los umbrales de crossmarket, crossTF, mcRetest y WFC desde el `config.yaml` de cada estudio
  a `ledger/thresholds.yaml`, con `set_by` y `set_on`. Los tres del Monte Carlo son provisionales
  desde OPEN #19.
- El paso 16 (SPP) hoy es «un mapa, no un filtro»: decidir si corta o no. Si no corta, que
  `criteria.yaml` lo diga en vez de dejar `rules: []`.
- D3: qué es pasar el paso 20.
- **Hecho:** ningún paso que juzga tiene `rules: []` sin una razón escrita al lado.

### 1.7 · Monos por la cadena, en Python — encargo 9

- Ya está escrito: `docs/encargos/9-monos-de-punta-a-punta.md`. Va en
  `studies/screening/falsePositives/`, con las series de `engines/nulls/`. No toca SQX; unos 35
  minutos por 10.000 monos.
- Estaba aparcado («no se implementa por ahora», 2026-09-26). D5 lo reabre: actualizar esa línea
  en `docs/encargos/README.md`.
- Dos activos: USDJPY y XAUUSD, que es donde hay poblaciones reales con las que emparejar la huella.
- **Hecho:** una tabla «de N monos, K llegan al paso 8, al 10, …, al 20», con las mismas reglas de
  `criteria.yaml`, y su fila en el registro.

### 1.8 · Monos seleccionados en SQX — encargo 30

- `docs/encargos/30-monos-seleccionados-en-sqx.md`: monos construidos y elegidos por el Builder
  con el bloque aleatorio, pasados por la cadena real con el autopilot. Mide la tasa de falsos
  positivos **con la selección del build incluida**, que es lo que el 9 no ve.
- Cuesta tiempo de custodio: una corrida de autopilot por población. Proyectos `Test_`, retirados
  al acabar (regla 6).
- **Hecho:** la misma tabla que el 1.7, y al lado la de las poblaciones reales.

### 1.9 · Congelación final de umbrales — DUEÑO

- Con las tablas del 1.7 y el 1.8 delante, el dueño fija la versión 2 de los criterios. La pregunta
  ya no es «qué umbral parece razonable» sino «cuántos monos dejo pasar».
- **Hecho:** `criteria.yaml` y `ledger/thresholds.yaml` con fecha de congelación; a partir de ahí,
  un cambio de umbral es una fila en el registro. Los primeros proyectos `Trade_` solo después.

---

## Decisiones del dueño que este plan necesita

| | qué | para qué punto |
|---|---|---|
| D1-D5 | las de la tabla del 1.1 | 1.2, 1.4, 1.6, 1.7 |
| D6 | destino de la copia, y si el segundo servidor ya existe | 0.4 |
| D7 | cómo se cierra el cortafuegos: el del proveedor o `ufw` | 0.1 |

## Bitácora

Una línea por sesión que avance algo: fecha, punto, qué quedó.

- 2026-10-02 — plan escrito y aprobado el orden por el dueño. Nada empezado.
- 2026-10-02 — fase 0 arrancada: 0.2 (propuesta de commits, a la espera del sí), 0.5 y 0.6 en curso, en paralelo. 0.3 y 0.7 esperan al commit del 0.2. Visto para el 0.1: hoy solo el 5050 escucha en `0.0.0.0` (master abierto); 5060/5070 abajo; también 22 y 3389 (escritorio remoto) abiertos a todo.
- 2026-10-02 — **0.2**: propuesta de 24 commits (372 rutas) lista, 111 rutas de otra sesión fuera; espera el sí del dueño. **0.5**: `/tmp` del 93 % al 54 %; temporales del proyecto en `AlgoData/tmp` (`core.datapaths.tmp_dir`), limpieza diaria, `/tmp` en el informe de disco con tope 80 %. Falta comprobar el «< 50 % tras una corrida completa». **0.6**: cron sin dos tareas en el mismo minuto (sábado: datos 02:00 y `oos2` 02:05), reglas muertas de `project.cfx` quitadas de `settings.json` (manda `guard.py`), la auditoría mecánica corre las 105 pruebas (92 pasan, 13 apartadas con motivo en `tools/audit_tests.py`). Sigue saliendo con 1 por tres causas ajenas: `checks.py` rojo por la sesión de Investigar, el proyecto `Infinox_SP500ft_H4_HighPrecision` que no se pinta y un export sin manifiesto (`Test_USDJPY_donchianUpperCrossUp_M30/SPP_IS/2026-09-27`). Pendiente de apuntar en OPEN: `ledger/thresholds.py` rompe con el feed `UKOIL.cash_M1`.
- 2026-10-02 — **D7 (0.1):** el dueño no toca el cortafuegos salvo necesidad extrema: ya se quedó fuera del servidor una vez y hubo que reinstalarlo. El 0.1 queda aparcado; el 5050 sigue escuchando en `0.0.0.0` cuando el master está abierto. Sin decidir: una vía que no pase por el cortafuegos (que SQX escuche solo en local). **D6 (0.4):** no hay copia nocturna automática; lo importante está en GitHub y el resto lo copia el dueño a mano a su SSD privado (la primera, esta noche). **0.2:** sí del dueño; commits aplicados grupo a grupo y push. Lo de la sesión de Investigar (111 rutas) queda sin commit hasta que cierre.
- 2026-10-02 — **0.1 cerrado.** El dueño instaló Tailscale (servidor `100.113.159.40`) y encendió `ufw` con tres reglas: entrada por `tailscale0`, 22/tcp y 3389/tcp; lo demás, denegado por defecto. Comprobado desde fuera (portchecker.io): antes el 5050 respondía; ahora 5050, 5051, 5060, 5070 y 8080 no responden, el 3389 sí, y SQX sigue respondiendo en local. `ufw` queda activo en el arranque. Queda a decisión del dueño cerrar el 22 público (se ven intentos de conexión de fuera) y dejar el SSH solo por Tailscale.
