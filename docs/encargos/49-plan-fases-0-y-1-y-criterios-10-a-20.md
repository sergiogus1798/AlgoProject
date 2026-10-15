# 49 · Plan vivo de las fases 0 y 1, y criterios de los pasos 10 a 20

**Qué es.** El plan que ordena a los demás encargos de las fases 0 y 1 (numeración 0.1-1.9, la
del antiguo 41) y el punto 1.6: que cada paso que juzga tras el 8 tenga una regla o una razón
escrita. **Quien retome las fases 0 y 1 empieza aquí**: la memoria del dueño apunta a «leer la
tabla de estado antes de continuar» y esa tabla es la de abajo. Es un plan **vivo**: cada sesión
que avance un punto actualiza su fila y una línea de la Bitácora, y no reescribe el resto. Cuando
las dos fases estén cerradas, este fichero se borra como cualquier encargo cumplido.

**Reescrito el 2026-10-15 contra el encargo 65** (`65-consenso-cuatro-opiniones.md`), que ya
resolvió el paso 8 (una z sobre el mono con las horas de la estrategia, α 0,01 por estrategia,
commit 9aef247), quitó `dev`, y dejó cerrados los pasos 10, 14, 18, 18.5 y 20. Lo que aquí queda
es lo que el 65 no tocó.

**Para la sesión que lo retome.** Lee `CLAUDE.md`, la tabla de estado y solo el punto que te
toque. Los puntos **DUEÑO** no se hacen por él: se le prepara lo necesario y se le pregunta.
Regla 12: nada de commits por tu cuenta. Regla 3: `ListAgents` y los candados
(`.claude/skills/sqx-wait/preflight.sh`) antes de tocar un worker.

## Estado (verificado el 2026-10-15)

Estados: ⬜ sin empezar · 🟡 en curso · ✅ hecho · 🔴 espera al dueño.
Modelo: **S** = Sonnet, mecánico · **O** = Opus, diseño o estadística (regla 17).

| # | punto | modelo | depende de | estado |
|---|---|---|---|---|
| 0.1 | Cerrar la API de SQX al exterior | — (dueño) | — | ✅ ufw + Tailscale, 2026-10-02 |
| 0.2 | Commit y push de lo pendiente | — | — | ✅ |
| 0.3 | Propuesta diaria de commit | — | 0.2 | ✅ |
| 0.4 | Copia fuera del disco: nocturna, `restic` a gorilla | S | — | ⏸ aparcada por el dueño (2026-10-15, «no te preocupes»); hoy sólo la copia a mano. No se ejecuta hasta que él lo retome |
| 0.5 | `/tmp` por debajo del 50 % tras una corrida | S | — | 🟡 hoy 42 % (1,6 G de 3,9 G; mayores: `claude-1000` 388 M, un `tmp*` 273 M, `pytest-of` 94 M) sin corrida; falta leerlo tras una completa |
| 0.6 | Auditoría mecánica a 0 | S | OPEN #95 | 🟡 |
| 0.7 | Documentación al día | — | 0.2 | ✅ |
| 0.8 | Cerrar el 22 público (SSH sólo por Tailscale) | — (dueño) | — | 🔴 dueño 2026-10-14: «cerrarlo, tras probar Tailscale desde fuera»; `ufw` pide `sudo` |
| 1.1 | Hoja de decisiones en PDF | — | — | ✅ |
| 1.2 | Firma provisional de los pasos 6 y 8 | — (dueño) | 1.1 | 🟡 paso 8 y `dev` hechos por el 65; paso 6 y lo pendiente de OPEN #93 → encargo **50** |
| 1.3 | Registro completo | S | — | 🟡 borrado el relleno de `Test_Calib_*` (2026-10-15); el repaso por paso dice que 11.5, 16 y 16.5 (`rules: []`) no dejan fila: `judge.judge` sale antes de `ledger_row`; ¿deben dejarla? |
| 1.4 | Autopilot: lo mínimo para una población nula | S | — | 🟡 código hecho, falta la prueba en SQX |
| 1.5 | Nulos y curva de mínimos | O | — | → encargo **50** (OPEN #88, #91) |
| 1.6 | Regla o razón escrita en 10, 12, 14, 16 y 20 | O + S | — | 🟡 10, 14, 18, 18.5 y 20 ✅ por el 65; quedan **12 y 16** y la higiene del YAML (§3); umbrales de crossmarket, crossTF y spp ya en el ledger (2026-10-15); los cortes viejos de mcRetest (P14-7) siguen: `gates.py` alimenta `scoring`, `report` y las columnas de la ventana |
| 1.7 | Monos por la cadena en Python | O | 1.3 | 🟡 → encargo **53** |
| 1.8 | Monos seleccionados en SQX | O | 1.4, 1.7 | ⬜ → encargo **53** |
| 1.9 | Congelación final de umbrales | — (dueño) | 1.6, 1.7, 1.8 | ⬜ |

**Orden.** 0.4, 0.5, 0.6, 1.3 y §3.1-§3.3 no dependen de nadie y avanzan ya. §3.4 espera a la
población nula del encargo 53. **Salida de la fase 0:** nada del proyecto existe solo en este
disco y nadie de fuera puede mandar una orden a SQX ni entrar por SSH. **Salida de la fase 1:** un
proyecto nuevo corre del paso 6 al 20 cortando por reglas firmadas, deja una fila en el registro
por paso, y se sabe cuántos monos de N llegan al final.

## Bitácora

Una línea por sesión que avance algo: fecha, punto, qué quedó.

- 2026-10-15 · 1.3: borrados `backfill --calib` y `steprows.calib_rows`. 1.6: `crossmarket.worse_z`, `crossTF.alpha` y `spp.margin` pasan a `ledger/thresholds.yaml` (mismo valor). `ledger/blind.py::from_batch` leía el `cscv.json` plano que ya nadie escribe: ahora lee `estudios/cscv.json` (`tests/test_ledger_blind_cscv.py`).
- 2026-10-15 · Q-1 → A (la regla «oos2 sólo en el 19.5» vale para los agentes de Claude; ya cumplida). Q-2 sin objeto: el dueño aparcó 0.4 (restic), «no te preocupes».

- 2026-10-09 — consolidado a partir de los encargos 41 y 43 (`git show c923d10:docs/encargos/41-fases-0-y-1.md`).
  0.1 cerrado (Tailscale, `ufw` con entrada solo por `tailscale0`, 22/tcp y 3389/tcp; 5050-5071,
  8080-8082 cerrados desde fuera); 0.3 hecho (`bin/nightly-commit-proposal.sh`, cron 05:45,
  `python3 -m tools.commit_apply`; el push con el aplicador no está probado); 1.1 hecho.
- 2026-10-14 — el dueño contestó P16-1/2/3, P14-7, P20-2, P12-1/6, T-1, T-2, T-8, puerto 22 y D6.
- 2026-10-15: reescrito contra el 65 (fila 5 del orden). Fuera: el `dev` y la regla del paso 8 de
  1.2 (los hizo el 65), las reglas de 10, 14, 18, 18.5 y 20 de §3 (las fijó el 65), §3.2 «el 20 sin
  entrada» (ya tiene `blindJoint.verdict_csv.drop`, que con D4 no descarta a nadie), la calibración
  de 8, 10 y 14 en §3.4, las decisiones sin objeto (P20-1, P14-2/3/8, T-6, T-9, D2 «sobre qué t»)
  y el veredicto del Council del 2026-10-08 (sustituido por el consenso del 65). 0.4 y 0.8 pasan
  de decisión a tarea.

---

## Tu oficio

Jefe de la fábrica de criterios: Sonnet para lo mecánico (fase 0, registro, autopilot, exponer
hechos, mover umbrales, borrar), **Opus** para lo que es estadística o diseño (calibración de 12 y
16, equipo rojo, síntesis para el dueño). Tu entrega es una decisión con su coste al lado, no una
descripción (CLAUDE.md, «An analysis ends in a decision»).

## Tu encargo

Dejar la fase 0 cerrada y la fase 1 lista para la firma del dueño: que **cada paso que juzga tras
el 8 tenga una regla medida en `pipeline/autopilot/criteria.yaml`, o una razón escrita al lado de
por qué no corta**, con lo que gana y lo que cuesta en estrategias; que cada paso del build al 20
deje su fila en el registro; y que el autopilot acabe limpio con cero supervivientes. Lo que firma
el dueño (0.8, 1.9 y cada criterio) se le prepara y se para.

## §0 De dónde sale

- Plan aprobado por el dueño el 2026-10-02: dossier `docs/AgentPDFs/estado-y-direccion-2026-10-02.pdf` §8.
- «**Pasa** = probado con los datos que hay · **Limbo** = no se pudo probar todavía, sigue
  marcado · **Falla** = casi seguro azar, o un riesgo que una cuenta de fondeo no aguanta. **Un
  hecho que falta es Limbo** (dueño, 2026-10-01).» Donde los datos no fijan una cifra, se dice y
  se toma la prudente.
- «**Todas las supervivientes del 16 en adelante pasan por 16.5-19 sin filtrar**» (memoria
  `workflow-todas-las-supervivientes-por-los-4`).
- Encargo 65 (consenso de las cuatro opiniones): cola de 17 a 20 = sólo corta el **19.5** (lectura
  única de `oos2`) y el 20 cuando su estudio dice DESCARTAR; 14 y 18 son columnas; 18.5 vuelve
  **por activo** (sólo donde el descuadre con SQX es < 0,01; D13; OPEN #121).
- Catálogo de decisiones con sus códigos: `docs/AgentPDFs/pendientes-y-decisiones-2026-10-08.md`.

## §1 Fase 0 — lo que queda

**0.4 · Copia nocturna con `restic` a gorilla** (S). **APARCADA (dueño, 2026-10-15): no la ejecutes.** Decidido por el dueño (2026-10-14). `restic`
en `~/.local/bin` (aquí `sudo` pide contraseña), cifrado, 7 diarias y 4 semanales, cron 05:30
(comprueba que el minuto está libre: `crontab -l`). Se copia `AlgoData` sin `raw/`, `scratch/` ni
`snapshots/` (~40,6 GB), `user/projects` y los bloques y plantillas propios de las tres
instalaciones, `config/machine.yaml` y la carpeta de memoria de `~/.claude/projects/`. Destino:
el repositorio `~/backups/restic_leaseWeb` en gorilla por SFTP (`ssh sqx2`; la copia es almacenamiento, no código que
corra allí, así que no pasa por `bin/remote.sh`). Script en `bin/` con su candado y su capítulo del
manual (regla 8; `/cron-agent` tiene la forma). **Hecho:** dos noches seguidas en el registro del
cron y una restauración de prueba de un proyecto de SQX y un estudio a una carpeta de scratch.

**0.5 · `/tmp` por debajo del 50 %** (S). Los temporales del proyecto van a `AlgoData/tmp`
(`core.datapaths.tmp_dir`, limpieza diaria) y `/tmp` entra en el informe de disco con tope 80 %.
Hoy 42 % (`df -h /tmp`, partición de 3,9 GB), pero sin una corrida detrás. Tras la próxima corrida
completa del workflow mira `df -h /tmp` y `du -sh /tmp/* | sort -h | tail`; lo que sea del
proyecto se desvía a `tmp_dir`. **Hecho:** < 50 % tras una corrida completa.

**0.6 · Auditoría mecánica a 0** (S). `python3 tools/daily_audit.py`; lo que siga rojo, contra
**OPEN #95** (`grep -n '^## 95' OPEN.md`). **Hecho:** sale con 0 sin novedades.

**0.8 · Cerrar el 22 público — DUEÑO.** Decidido (2026-10-14): cerrarlo tras probar Tailscale
desde fuera. `ufw` pide `sudo` y el dueño no quiere que se toque el cortafuegos sin él (se quedó
fuera una vez y hubo que reinstalar). Se le prepara: la orden exacta (`sudo ufw delete allow
22/tcp`, dejando `tailscale0`), cómo probar antes un `ssh` por la IP de Tailscale
(`100.113.159.40`) desde otra red, y la vuelta atrás desde la consola del proveedor. La tarjeta
`knowhow/sqx-drive/api-no-auth.md` recoge el estado al cerrarlo.

## §2 Fase 1 — registro, autopilot y firmas

**1.2 · Firma provisional de los pasos 6 y 8.** Lo del 8 está hecho por el 65 (filas 1, 5.2-5.4:
`dev` fuera, regla única «z del mono con horas» con α 0,01, sello del 8 con `ledger.cells
--seal`). Lo que queda es del paso 6 y de OPEN #93 («owner answers of 2026-10-15 to apply»), y lo
lleva el **encargo 50**. Aquí sólo se marca ✅ cuando el 50 cierre #93.

**1.3 · Registro completo** (S). El build, el WFM y cada corte del autopilot ya dejan fila
(`ledger/steprows.py`, `pipeline/autopilot/judge.py`, con el sha256 de `criteria.yaml`); el
contador por celda es del 65 (fila 5.1, `ledger/cells.py`). Queda:
1. **Repasar que no quede un paso sin fila**: cada clave de `steps:` de `criteria.yaml` (8 a 20,
   19.5 incluido) llama a `ledger.record`. Un paso sin fila es una línea nueva en
   `tests/test_ledger_steprows.py`.
2. **Borrar el relleno hacia atrás de `Test_Calib_*`** (regla 21): T-6 quedó sin objeto (la
   calibración se borró el 2026-10-04), así que `--calib` de `ledger/backfill.py` y
   `steprows.calib_rows` no tienen a quién servir. Antes, `grep -rn 'calib_rows\|--calib'` en todo
   el repo; si sólo los llaman ellos mismos y sus tests, se borran con sus citas (README, manual,
   knowhow). `ledger/cells.py:backfill` es otra cosa y se queda.
- **Hecho:** una corrida nueva deja una fila por paso sin intervención; `python3 -m ledger.report`
  enseña el N del estudio y el global.

**1.4 · Autopilot: lo mínimo para una población nula** (S). Hecho en código: cero supervivientes
es un final limpio (`tests/test_autopilot_zero.py`), un hecho que falta tiene destino por regla
(`missing:`), `sqx/projects/live.py` `wait()` falla con límite de tiempo, puerto caído o aborto.
**Queda la prueba en SQX**: tres corridas seguidas a cero supervivientes terminan en `FIN`, y
matar la JVM **por PID** a media corrida acaba en un fallo con mensaje. Con `/workflow` sobre un
`Test_` (regla 19), `/sqx-wait` (regla 18), worker parado y `python3 -m sqx.projects.retire <P>
--role <role> --yes` al acabar. Se ordena con el encargo 53 (misma población nula); el 53 está
**parado por el dueño** (2026-10-14), así que esto queda 🟡 hasta que lo reabra.

**1.9 · Congelación final de umbrales — DUEÑO.** Con las tablas de monos del 53 delante, fija la
versión 2. Firma **en la ventana, criterio a criterio** (T-8): comprueba que la zona «Criterios»
lo permite antes de llevárselo; si no, es una petición para `ui/`, no algo que se haga aquí.
**Hecho:** `frozen: {on, by, sha}` en `criteria.yaml` y fecha en `ledger/thresholds.yaml`.

## §3 Punto 1.6 — lo que queda de los pasos 10 a 20

**Cerrado por el 65 (no se rehace):** 10 (P3 sobre V0+V2 con signo por familia, controles
negativos; fila 4), 14 (columna; fila 3d), 18 (columna; fila 3c), 18.5 (por activo; filas 3b y 8,
D13), 19.5 (corta por signo; fila 6), 20 (sin `peor`, no descarta a nadie; fila 3a, D4). 11.5 y
16.5 ya llevan su razón escrita en el YAML. 12 queda como lo contestó el dueño: `z_new ≥ 2,33` y
debajo Limbo, nunca Falla (P12-1, P12-6), con T0-T4 al lado como hechos `crossTF.tf.*`.

1. **Paso 16 según P16-1/2/3** (S). En `criteria.yaml` `"16"`:
   - Sustituir el comentario del Council («neither is exposed as a fact yet») por la razón del
     dueño: **no corta hasta medir sus falsos positivos** (P16-1, 2026-10-14). `rules: []` se queda.
   - `segment: oos1` → **`build`** (P16-2): todos sus hechos son del build.
   - P16-3, suelo de 30 operaciones: comprobar que `studies/breakage/spp/config.yaml`
     `grid.min_trades: 30` es ese suelo; si lo es, citarlo en el comentario, sin regla nueva.
   - Exponer como columnas los hechos que necesitarán las candidatas de §3.4: media, desviación y
     media − desv de la rejilla, `net_profit.p5`/`p10`, `area_de_meseta`, marca de pico, distancia
     del real en IQR. Listar con `python3 -m pipeline.autopilot.facts --project <P> --step 16` y
     añadir en `studies/breakage/spp/verdict/` los que falten (`facts.py` los recoge del
     `verdict.csv`).
2. **Higiene del YAML** (S, regla 21). Quitar de la cabecera de `criteria.yaml` el párrafo de
   `dev` (la clave ya no existe); el `"11.5"` cita `docs/encargos/47-…`, que ya no existe: apunta al
   51. No toques el bloque `"8"` (es del 50).
   Y comprobar T-2 en el código: `ALGO_AUTONOMOUS=1` cierra `oos2` al autopilot (`ledger/gate.py`)
   y un estudio empezado conserva la ventana de `oos2` con la que empezó aunque
   `bin/monthly-oos2-roll.sh` la alargue; si no la guarda, se añade y se prueba.
3. **Umbrales al ledger** (S). Verificado el 2026-10-15: `ledger/thresholds.yaml` no tiene ninguna
   clave `crossmarket.*`, `crossTF.*`, `mcRetest.*` ni `spp.*`, y ningún `config.yaml` de los cuatro
   lleva `ledger:`.
   - **mcRetest:** P14-7 → **borrar** los cortes viejos (`studies/breakage/mcRetest/verdict/gates.py`
     y su bloque `gates:` del `config.yaml`, con `tooltips.py`, README y tests), no moverlos. Grep
     de llamadores antes. Si con eso OPEN #19 («three Monte Carlo thresholds are placeholders») se
     queda sin objeto, ciérrala con `/open-close`.
   - **crossmarket, crossTF, spp:** sólo los umbrales **de juicio** (p. ej. `travel.worse_z`,
     `verdict.alpha`, `verdict.margin`) pasan al ledger con `set_by`, `set_on`, `why` y `source`,
     y el `config.yaml` a `ledger:<clave>`; lo que es «cómo se mide» (`draws`, `seed`,
     `min_trades`…) se queda. Comprobar con `python3 -m ledger.report --check-thresholds` y
     `tests/test_thresholds.py`.
4. **Calibrar 12 y 16 con la población nula y la plantada** (O). **Espera al encargo 53** (parado
   por el dueño): sin su población nula no hay tasa de falsos positivos. En `oos1` y con otra
   población (T-1); **`oos2` no se lee**. Por paso:
   - *12:* ¿T0-T4 separa plantadas de monos mejor que `z_new ≥ 2,33`? Si sí, se le lleva al dueño
     el «corta» de T0-T4 en el 11.5 (P12-1) con su coste en estrategias.
   - *16:* tasa de falsos positivos de las tres lecturas del dossier del paso 16 —
     `spp.panel1.net_profit.p10 ≥ 0` (3 de 10), `area_de_meseta ≥ 0,7` (2 de 10),
     `net_profit.p5 ≥ 0` (4 de 10) — y efecto en solitario de cada una.
   Método: verificar contra el código qué calcula el paso; un nulo sobre la misma estadística;
   cada regla con qué deja, qué pierde de lo bueno, falsos positivos y efecto en solitario («buena»
   se define con datos que la regla no lee); equipo rojo con contexto limpio; validación por el
   camino real (`facts.per_strategy` → `criteria.resolved` → `criteria.outcomes`). Trampas: como
   mucho 8-12 procesos de Python y 25 GB libres; nunca `pkill -f`; el mono con `--seed`; ficheros
   grandes a `AlgoData`; di qué segmento gastó cada umbral.
5. **Entrega.** Las reglas propuestas de 12 y 16 en `criteria.yaml` como **propuesta de un
   agente** hasta la firma; un dossier en castellano en `docs/AgentPDFs/` con su PDF
   (`/dossier-pdf`): una tabla por paso (regla · gana · cuesta · falsos positivos · segmento que
   gastó); fichas de `knowhow/`; capítulo del manual de lo que cambie (regla 8).
   **Hecho:** `grep -n 'rules: \[\]' pipeline/autopilot/criteria.yaml` — cada resultado lleva su
   razón al lado, y la del 16 es la del dueño.

## Decisiones del dueño — pregúntalas (regla 11)

**Contestadas (2026-10-14 y 2026-10-15)** — mandan sobre cualquier otra lectura:
- P16-1 → no corta hasta medir falsos positivos. P16-2 → build. P16-3 → suelo de 30 operaciones.
- P14-7 → borrar los cortes viejos de `gates.py`. P12-1 → sigue `z_new ≥ 2,33`, T0-T4 al lado.
  P12-6 → el 12 no descarta.
- T-8 → firma en la ventana, criterio a criterio. T-1 → calibrar en `oos1` y con otra población;
  `oos2` reservado. T-2 → sí ata al autopilot; ventana anclada por estudio.
- Puerto 22 → cerrarlo tras probar Tailscale. D6 → copia nocturna `restic` a gorilla.
- P8-Z/L/E → del 65 (α 0,01; limbo sigue; `edge_mean_oos` no se endurece).
- Sin objeto por el 65: P20-1, P14-2/3/8, T-6, T-9, D2 «sobre qué t».

**Contestadas el 2026-10-15 («todas las recomendaciones»):**
- Q-1 → A: «oos2 sólo en el 19.5» obliga a los agentes de Claude (ideaExpert, researchDirector…), no al autopilot; ya se cumple, nada que hacer. Los pasos 17-20 siguen leyendo `oos2` dentro del bloque ciego (D2 del 65).
- Q-2 → sin objeto: el dueño aparcó la copia `restic` (0.4), «no te preocupes». No hay repositorio que crear en gorilla.

- Nada de SQX fuera de `/workflow` ni sin `/sqx-wait`; ningún proyecto fuera de
  `Test_`/`Trade_`/`Research_`; un `Test_` se retira al acabar. Nada en gorilla fuera de
  `bin/remote.sh`, salvo el destino de la copia de 0.4.

## Objetivo — un comando

El cierre depende de la firma del dueño (0.8, 1.9) y de dos corridas en SQX (1.4 y la población
del 53 para §3.4): **no se reduce a un comando**. Verificación:

1. `python3 tools/depmap.py && python3 tools/checks.py && python3 -m pytest tests/test_ledger_steprows.py tests/test_autopilot_zero.py tests/test_thresholds.py -q`
2. `python3 -m ledger.report --check-thresholds`: cada fila de crossmarket, crossTF y SPP dice «se
   lee del ledger»; `grep -rn 'gates' studies/breakage/mcRetest/` sin cortes viejos (§3.3).
3. `grep -n 'rules: \[\]' pipeline/autopilot/criteria.yaml`: cada resultado lleva su razón al lado.
4. `python3 -m pipeline.autopilot.facts --project <P> --step 16`: existen los hechos de §3.1.
5. `python3 tools/daily_audit.py` sale con 0 (0.6); `df -h /tmp` < 50 % tras una corrida (0.5);
   (0.4 aparcada: sin `restic snapshots` hasta que el dueño la retome).
6. 1.4: las tres corridas a cero supervivientes y la JVM matada, con la salida pegada.
7. §3.4: el embudo por el camino real y el informe del equipo rojo, pegados.
8. Si se movieron o borraron módulos: `graphify update . && python3 tools/projectmap.py` (regla 22).

## Cómo cierras

Qué hiciste · qué verificaste, con la salida pegada · qué dejaste sin hacer y por qué · qué
descubriste para `knowhow/` · la tabla de estado y la Bitácora al día · los ficheros cambiados y,
como última línea, **¿Quieres hacer el commit?**
