# Plan de ejecución — AlgoProject + SQX

**Qué es este documento.** El plan de trabajo completo, escrito para ser **repartido entre varios
agentes que trabajan en paralelo**. Cubre todo menos la interfaz de escritorio, que queda fuera de
alcance por decisión del dueño.

**Para quién.** Para el dueño, que reparte, y para cada agente que recoge una tarea. Cada tarea de
las §4 y §5 es un encargo autocontenido: dice qué leer, qué hacer, cómo verificarlo y qué entregar.
**Un agente no necesita leer las tareas de los demás**, solo los contratos de la §6.

**Relación con los documentos anteriores.** Continúa y actualiza
`protocolo-robustez-2026-09-21.md`: su §9 («Bloqueos») y su tabla «Estado a 2026-09-21» quedan
**sustituidas por la §7 de aquí**. El destino sigue siendo `plataforma-unificada-2026-09-20.md`,
cuya carcasa de escritorio **no se construye todavía**.

**Regla que hereda de esta carpeta.** El dossier guarda la narrativa y el plan; `knowhow/` guarda
los hechos. **Donde los dos discrepen, manda `knowhow/`.**

Generado el 2026-09-21.

---

## 1 · Los dos carriles

El trabajo se parte en dos oficios que **no se pisan** porque tocan cosas distintas:

| carril | quién | toca | nunca toca |
|---|---|---|---|
| **S — Instalaciones** | un agente de sistema. Bash, ficheros de configuración, `sqcli` | los tres installs de SQX, sus heaps, sus puertos, sus vistas, sus proyectos | código Python del repo |
| **P — Python** | varios agentes de programación, en carpetas disjuntas | `core/`, `sqx/`, `strategies/`, `pipeline/`, `docs/manual/` | los installs de SQX en marcha |
| **O — Dueño** | solo él | cerrar la GUI, aprobar, decidir umbrales, `sudo` | — |

**El punto de contacto es uno solo:** el carril S deja los installs en un estado que la §6 describe,
y el carril P programa contra esa descripción. Ninguno espera al otro para empezar.

### Qué puede empezar HOY, sin que nadie haga nada antes

```
CARRIL O   O1 pre-registro del holdout        ← MUY IMPORTANTE, irreversible
CARRIL S   S6 RETIRADA (proyecto SP500) · S7 higiene de logs · S10 sonda de 3 ficheros
CARRIL P   P0 monitor de vida · P1 portabilidad · P2 pipeline · P3 variantes (diseño)
```

Cinco agentes en paralelo desde el minuto uno. Lo único verdaderamente secuencial es
**S1→S5** (la topología), que necesita que el dueño cierre su GUI.

---

## 2 · Decisiones ya tomadas — no se vuelven a discutir

Cerradas el 2026-09-21 con medición. Un agente que las cuestione está perdiendo el tiempo del dueño.

| tema | decisión | evidencia |
|---|---|---|
| **Instalaciones por PC** | **tres**: maestro + conductor + custodio | §3 |
| **Heap del maestro** | `-Xmx24g` (era `108g`) | 🔬 `jstat -gc` sobre el maestro vivo: conjunto **vivo 15,9 GB**, comprometido 57,4 GB, RSS 67,5 GB. El exceso era basura sin presión de GC |
| **Reserva Python** | **24 GB** | pico medido hoy 2,5 GB (`montecarlo.analyse_long`). Una reserva no se asigna: solo es RAM que no se promete a ninguna JVM |
| **Núcleos** | maestro **elástico** (`-1`), workers capados | reparto fijo costaría la mitad de la generación con la máquina vacía |
| **Licencia** | dos licencias, dos PCs. Cerrado | decisión del dueño |
| **Barra de progreso SQX** | **degradada a monitor de vida** (P0). Sin WebSocket, sin activar nada | decisión del dueño |
| **Umbrales del veredicto** | **no bloquean nada**: los decide el usuario y son cambiables | decisión del dueño |
| **Multi-máquina** | PCs **independientes**, misma receta replicada. Sin clúster, sin demonio remoto | decisión del dueño |
| **Interfaz de escritorio** | **fuera de alcance** de este plan | decisión del dueño |

---

## 3 · La topología objetivo

Lo que el carril S tiene que dejar montado. **Por PC**, no por red.

| | install | GUI | `-Xms` | `-Xmx` | `coreUsage` | puertos | papel |
|---|---|---|---|---|---|---|---|
| **M** | `~/Desktop/SQX` | sí, del dueño | `2g` | **`24g`** | **sin tocar** (`-1`) | 5050 / 5051 / 8080 | sus proyectos, su generación. Agentes: **solo lectura** |
| **W1** | `~/Desktop/SQX_w1` | nunca | `1g` | **`16g`** | **8** | 5060 / 5061 / 8081 | **conductor**: exports, `-databank`, autoría, config de proyectos. Siempre vivo |
| **W2** | `~/Desktop/SQX_w2` | nunca | `1g` | **`80g`** (era 48g) | **-1** = todos (era 48) | **5070 / 5071 / 8082** | **custodio**: un trabajo largo cada vez. Sostiene el databank de 5.000 variantes |

Presupuesto sobre 125 GB, **revisado por el dueño el 2026-09-23**: el maestro casi nunca se abre, así
que el custodio se lleva la RAM: `10-12 SO + 20 Python + 80×1,08 W2 ≈ 118`, y W1 (16g de techo,
~2 GB ocioso) cabe mientras no sostenga nada grande a la vez. **Si el maestro se abre como visor**
(`-Xmx12g`, 2 núcleos) sigue cabiendo justo; **abrirlo para generar con 24g mientras W2 está lleno
no cabe** — swap de 4 GB, así que el que sobre muere por OOM. Núcleos: medido 2026-09-23, de 48 a 95
hilos un retest gana ≤ 10 % (los 47 extra son SMT), así que W2 con todos los núcleos no compite con
nadie mientras el maestro esté cerrado, y si se abre a generar los dos van a la mitad.

(Presupuesto anterior, 2026-09-21: `5 SO + 24 Python + (24+16+48) techos + ~8 % overhead ≈ 124`.)

**Las tres reglas de oro de esta topología:**

1. **Al custodio no se le habla mientras trabaja.** Entre «arranca» y «recoge» no recibe ni un
   comando. Es lo que convierte la regla dura 1 (cada sync borra los `.sqx` que no tiene en memoria)
   de riesgo permanente en imposible.
2. **El conductor nunca sostiene nada grande.** Si un trabajo va a tardar más de un minuto o a
   cargar más de mil estrategias, es del custodio.
3. **`-Xms` bajo en los workers.** Un worker ocioso no debe reservar su heap. Es lo que hace que
   quepan tres.

### Los dos PCs

La fórmula, y las dos instalaciones concretas:

```
Σ(-Xmx)  ≈  (RAM_total − 5_SO − reserva_Python) / 1,08
M = 24   ·   W1 = 16   ·   W2 = el resto
```

| | **PC-A** — 96 núcleos / 125 GB | **PC-B** — 16 núcleos / 128 GB |
|---|---|---|
| Presupuesto de heap | Σ ≈ 88 de 88 disponibles | Σ ≈ 88 de **91** disponibles |
| **M** maestro | `-Xms2g -Xmx24g` · `coreUsage -1` | `-Xms2g -Xmx24g` · `coreUsage -1` |
| **W1** conductor | `-Xms1g -Xmx16g` · `coreUsage 8` | `-Xms1g -Xmx16g` · **`coreUsage 2`** |
| **W2** custodio | `-Xms2g -Xmx48g` · `coreUsage 48` | `-Xms2g -Xmx48g` · **`coreUsage 8`** |
| Restricción real | **RAM**, al límite | **CPU** — la RAM sobra |

**Los heaps son idénticos en los dos PCs.** Con 128 GB, PC-B tiene incluso 3 GB más de margen que
PC-A. **No subas los techos por tener RAM libre**: la lección del maestro es que un `-Xmx` generoso
no se traduce en rendimiento, se traduce en basura sin recoger (57 GB comprometidos para 15,9 GB
vivos).

**Lo que sí cambia en PC-B son los núcleos, y con ellos el reloj.** Escalando las medidas del log
del maestro (95 núcleos), y sabiendo que los backtests son CPU-bound:

| trabajo | PC-A (96 núcleos) | PC-B (16 núcleos) |
|---|---|---|
| Retest de 5.000 variantes | **3,5 min** | ~21 min (~42 con `coreUsage 8`) |
| SPP de 15k runs (~62.000 backtests) | **6 min** | ~36 min |

🔭 **Y eso hace que en PC-B el tercer install valga MÁS, no menos.** El argumento del custodio es que
nadie le habla mientras sostiene su databank; si el trabajo dura seis veces más, la ventana durante
la cual un comando despistado destruiría trabajo es seis veces más ancha. El conductor separado deja
de ser comodidad y pasa a ser la única forma de consultar algo sin tocar al custodio.

**Reparto recomendado de trabajo entre los dos PCs:**

| | se hace en |
|---|---|
| Fabricar y correr las **5.000 variantes con mercados adicionales**, los SPP de 15k runs, la generación 24/7 | **PC-A** |
| Análisis sobre datos ya exportados, desarrollo, segundo mercado, corridas largas desatendidas que no tienen prisa | **PC-B** |

Son PCs **independientes**: cada uno con su `config/machine.yaml`, su `AlgoData` y sus tres installs.
El repositorio viaja por git; los datos **nunca**.

---

## 4 · CARRIL S — las instalaciones de SQX

**Antes de tocar nada, el agente de este carril lee:** `CLAUDE.md` entero,
`knowhow/databanks/`, `knowhow/sqx-drive/three-install-topology.md`, `docs/SETUP-NEW-MACHINE.md`.

**Las cuatro reglas que más muerden aquí:**

- **Regla 1** — cada sync borra del disco los `.sqx` que no están en memoria. **Snapshot de
  `user/projects` antes de cualquier cosa que reinicie SQX.**
- **Regla 2** — nunca `sqcli` contra el maestro con su GUI levantada. Nunca `pkill -f
  StrategyQuantX`: el patrón casa con tu propio shell. **Matar por PID.**
- **Regla 3** — no arrancar builds, no cambiar qué construye un proyecto. La configuración del
  maestro es del dueño: **no es un bug y no es un hallazgo que reportar.**
- **Regla 4** — nunca editar un `project.cfx` que una instancia viva tiene abierto.

---

### S1 · Snapshot de seguridad
**Puede empezar:** ya · **Bloquea:** S2, S3, S4 · **Dura:** minutos

Antes de que nada reinicie SQX, copia `user/projects` de los installs existentes a
`AlgoData/snapshots/<fecha>/`. Es el seguro contra la regla 1 y contra un clonado mal hecho.

**Verificación:** el número de `.sqx` bajo el snapshot coincide con el del origen, por proyecto y
por databank. Escribe ese recuento en un `MANIFIESTO.txt` dentro del snapshot.

---

### S2 · Re-dimensionar el maestro
**Puede empezar:** con la GUI del maestro **cerrada** (lo hace el dueño) · **Dura:** minutos

En `~/Desktop/SQX/StrategyQuantX.config`: `-Xms2g`, `-Xmx24g`. **No toques `coreUsage`**, que se
queda en `-1`.

**Verificación:** arrancado de nuevo y generando una hora, `jstat -gc <PID>` (el binario está en
`~/Desktop/SQX/j64/bin/jstat`) da `OU + EU` por debajo de ~20 GB y `FGCT` no crece más de unos
segundos por hora. **Si hace full GC continuo, súbelo a 32g y baja W2 a 40g** — esa es la única
palanca y se decide con este número, no con opiniones.

---

### S3 · Re-dimensionar y capar el conductor
**Puede empezar:** tras S1, con el worker parado (`bin/sqx-worker.sh stop`) · **Dura:** minutos

En `~/Desktop/SQX_w1/sqcli.config`: `-Xms1g`, `-Xmx16g`. En
`~/Desktop/SQX_w1/user/settings/settings.xml` añade `<coreUsage>8</coreUsage>` — **hoy la clave no
existe en ese fichero**, así que el worker cree que los 96 núcleos son suyos.

**Verificación:** `bin/sqx-worker.sh start`, luego
`curl -sg "http://localhost:5060/call?cmd=-project%20action=list"` responde. El puerto abre y
contesta `Error: CLI not ready.` durante ~20 s antes de aceptar comandos: eso es normal, se sondea,
no se concluye que está roto.

---

### S4 · Clonar el custodio W2
**Puede empezar:** tras S1 y S3, con **todo SQX y sqcli cerrados** · **Dura:** 1 hora

H2 toma bloqueos exclusivos: clonar con algo en marcha produce una copia rota que **trunca la
ventana de backtest en silencio**.

1. Parametriza `bin/clone-sqx-worker.sh` (o pásale las rutas): `WORKER=~/Desktop/SQX_w2`,
   `CLI_PORT=5070`, `EDITOR_PORT=5071`, `WEB_PORT=8082`.
2. Ejecútalo. Hace seis cosas y **la cuarta es la peligrosa**: reescribe toda ruta absoluta de
   `settings.xml`. Sin ella el worker es un **alias silencioso del maestro** y escribe dentro de él.
3. Heap: `-Xms2g`, `-Xmx48g`. Núcleos: `<coreUsage>48</coreUsage>`.

**Verificación, y no se salta ninguna:**

```bash
grep -c "Desktop/SQX/" ~/Desktop/SQX_w2/user/settings/settings.xml     # tiene que dar 0
grep -E "Port" ~/Desktop/SQX_w2/internal/AppSettings.txt               # 5070 / 5071
ls -la ~/Desktop/SQX_w2/user/data/                                     # History es un symlink
```

⚠️ El script actual **refuse-a-terminar** si alguna ruta sigue apuntando al maestro. **No lo
anules.**

---

### S5 · Verificar los tres juntos bajo carga
**Puede empezar:** tras S2, S3, S4 · **Dura:** 1 hora de observación

Los tres vivos, el maestro generando, un trabajo cualquiera en W2.

**Criterio de éxito:** `available` de `free -g` **no baja de ~8 GB**, `load1` **no pasa de ~100**, y
el `FGCT` de los tres no se dispara. Deja la traza en `AlgoData/perf/` como fila fechada.

**Entregable:** una tabla con los tres PID, sus `OU+EU`, su `FGCT` y el `free -g` del final.

---

### S6 · ~~Reparar el proyecto roto~~ — **RETIRADA POR EL DUEÑO, 2026-09-21**

**No se hace. No la recojas.** Decisión del dueño: `Infinox_SP500ft_H4_HighPrecision` no le
interesa, así que la reparación sale del plan.

El diagnóstico sigue siendo cierto y queda en `OPEN.md` issue 3 como hecho registrado, no como
trabajo pendiente: el proyecto declara 8 tareas, trae 3 ficheros, la GUI lo omite **en silencio**, y
genera cada hora un `Project ... does not exist.` que es lo que llevó `log_2026_09_20.log` a
55,5 MB.

**Lo que hay que saber al leer el resto del plan:**

- **El log seguirá ensuciándose** mientras el maestro esté levantado. S7 se lleva los bytes, no la
  causa. Cualquier presupuesto de disco de este plan tiene que contar con ello.
- **P0 lee de ese canal.** El diluvio no lo rompe — el error es una línea repetida, no ruido en el
  vocabulario de `ProgressEngine` — pero un `tail` sobre ese fichero verá esa excepción a menudo y
  hay que esperarla, no tratarla como señal.
- **La lista viva de proyectos miente**, y va a seguir mintiendo: 14 entradas contra 15 directorios.
  Quien diffee la lista contra `user/projects/` verá esa discrepancia siempre; es esta, no una
  nueva.

Si algún día cambia de idea: `python3 -m sqx.repair.graft_tasks` sigue escrito y verificado en seco,
e injerta en vez de restaurar. **Nunca `project_backup.cfx`** — es de 2025-10-13 y reintroduce tres
regresiones ya arregladas.

---

### S7 · Higiene de logs
**Puede empezar:** ya · **Dura:** 30 min

El log del maestro se escribe rápido y crece sin techo. Deja una rotación o una poda por antigüedad
bajo `user/log/StrategyQuant/`, y anota la política en `knowhow/eng/log-retention.md`.

⚠️ **Nunca leas ese log entero: se tailea.** Todo lo que lo consuma (P0) filtra por
`ProgressEngine` **en origen**.

---

### S8 · La vista `WFC Variants.vw` en W2 — **antes** de cualquier retest de variantes
**Puede empezar:** tras S4 · **Bloquea:** P4 · **Dura:** 1 hora

La vista existente `Export Data View.vw` del maestro es **asimétrica**: 22 columnas IS
(`sampleType="10"`) y solo 13 OOS (`sampleType="20"`). Le faltan en OOS `NumberOfTrades`,
`Drawdown`, `Stability` y `RSquared`. **No se toca.**

Crea en **W2** una vista `WFC Variants.vw` **simétrica**: las mismas 41 columnas de la §4 del
protocolo en IS y en OOS.

⚠️ **Esto es irreversible por estrategia.** `knowhow/columns/custom-columns-stored.md`: el valor de una columna se
congela dentro del `.sqx` al calcular el resultado. Una columna añadida a la vista **después** sale
0 en toda estrategia anterior, sin aviso y sin celda vacía. **La vista tiene que estar cerrada antes
de lanzar el retest de las 5.000.**

**Verificación:** exporta 5 estrategias cualesquiera con ella y comprueba que las 41 salen con valor
en las dos muestras. Ojo con las dos columnas que llevan un **`?` literal** en el nombre
(`CalmarRatio?`, `AnnualPctReturnDDRatio?`): pedirlas sin el `?` da una columna entera de NaN sin
error.

---

### S9 · La sonda de tres ficheros — desbloquea el diseño de las variantes
**Puede empezar:** tras S4 · **Bloquea:** decisiones de P3 · **Dura:** 30 min

Dos incógnitas 🤔 que deciden si las 5.000 variantes ocupan **57 MB o 500 MB**, y que se matan con
tres ficheros:

1. **¿Carga SQX un `.sqx` de 5 miembros?** (solo `META-INF` + `settings.xml` +
   `strategy_Portfolio.xml` + `lastSettings.xml` + `version.txt` = **11,3 KB**, frente a 100 KB sin
   `optimizationProfile.bin` y 5.215 KB íntegro).
2. **¿El databank deduplica por el `<Fingerprint>` heredado** del original?

**Método:** fabrica tres variantes a mano de `Strategy 17.9.39` (los parámetros viven **solo** en
`strategy_Portfolio.xml`, en `<variable><id>NOMBRE</id>…<value>N</value></variable>`; renombra
además `ResultsGroup ResultName` y `StrategyName` de `settings.xml` o las tres caen bajo el mismo
nombre). Cárgalas en un databank de W2 y cuenta.

**Entregable:** respuesta 🔬 a las dos preguntas, escrita en `knowhow/sqx-format/five-member-sqx.md`. Es lo que
permite a P3 elegir forma de fichero con un dato en vez de con una apuesta.

---

### S10 · Barras y disciplina del tercer install
**Puede empezar:** tras S4 · **Dura:** 30 min

Los ficheros H2 no se pueden compartir (bloqueo exclusivo), así que **W2 necesita su propia copia**
de `data.db`, `data_futures.h2.db` y `data_stock.h2.db`; `History/` va por symlink al maestro. El
mecanismo ya existe y es correcto: **sincronizar al arrancar**, porque en ese instante el worker
está parado por definición.

Comprueba las **`.version`**, nunca los `.db`: H2 reescribe la cabecera cada vez que abre una base,
así que los bytes divergen en la primera ejecución aunque las barras sean idénticas.

**Entregable:** `bin/sqx-worker.sh` sabe arrancar y parar **cualquiera de los dos workers por rol**
(coordinado con P1, que es quien lo parametriza).

⚠️ **La GUI de W2 nunca se abre a la vez que su demonio de 5070, y abrirla dispara syncs.** Con un
databank de 5.000 variantes dentro, eso es el escenario del log de USDJPY. Inspeccionar **antes** de
fabricar o **después** de recoger; nunca en medio.

---

### S11 · Medir lo que decide el resto
**Puede empezar:** tras S5 y P3 · **Dura:** una tarde

Tres números que hoy no existen y que el plan necesita:

| medida | cómo | qué decide |
|---|---|---|
| **RSS real de W2** con 5.000 variantes | `jstat -gc <PID de W2>` durante la corrida | convierte los 48 GB de estimación en número |
| **Tiempo de export de trades de 100 variantes** | cronometrar, extrapolar ×50 | **el único cuello de botella real, hoy sin medir.** Dice si 100 madres son 3 días o 3 semanas |
| **Pico de disco del ciclo una-madre-cada-vez** | `du` antes/durante/después | confirma los 57–500 MB estimados |

**Un solo trabajo en el custodio, y después `stop`.**

---

## 5 · CARRIL P — Python

**Antes de escribir una línea, todo agente de este carril lee:** `CODESTYLE.md` y el `README.md` de
la carpeta que va a tocar.

**Las tres reglas que aplican a todos:**

- **Ninguna ruta absoluta fuera de `core/paths.py`.** `tools/checks.py` lo exige.
- **Comando nuevo = página de manual en español en la misma tarea.** Se copia
  `docs/manual/_PLANTILLA.md` a `docs/manual/NN-<nombre>.md`, con capturas de salida **real**.
  `checks.py` falla si un `__main__` no aparece en ninguna página, ni por ruta ni por su forma
  `python3 -m`. **`docs/manual/PENDIENTE.md` es backlog heredado: no se añade nada nuevo ahí.**
- **Al terminar:** `python3 tools/depmap.py && python3 tools/checks.py` → «0 problems».

---

### P0 · Monitor de vida
**Puede empezar:** ya · **Bloquea:** nada · **Dura:** 1–2 días · **Carpeta:** `core/`

El dueño no quiere una barra de progreso exacta. Quiere **no mirar una pantalla muerta preguntándose
si el programa se ha colgado.** Eso es diez veces más barato.

Salida objetivo, una línea que se reescribe:

```
XAUUSD · madre 7/100 · etapa: retest variantes · 14m 22s · cpu 94% · último evento hace 3s
    ProgressEngine: "WF: 6 runs : 20 % OOS WFO 4"
```

Tres fuentes, todas de coste cero y **ninguna necesita activar nada en SQX**:

| fuente | qué demuestra |
|---|---|
| `state.json` escrito **durante** cada etapa (contrato C5) | las etapas Python, con su avance real |
| `%CPU` del proceso + **mtime** del log | «está vivo», de la forma más tonta y más robusta |
| última línea `grep ProgressEngine` del log | qué está haciendo SQX ahora mismo |

⚠️ **Filtra `ProgressEngine` en origen.** Sin eso, el monitor lee 55 MB de *stack traces* ajenos.
Y esto ya **no** es temporal: S6 se retiró el 2026-09-21, así que la excepción horaria del proyecto
SP500 se queda. El filtro deja de ser una optimización y pasa a ser un requisito. El porcentaje fino, cuando lo hay, **no viaja en el mensaje sino en el nombre del hilo**:
`[Blocking computeThread common #45 - WF: 6 runs : 20 % OOS WFO 4]`.

**Explícitamente fuera de alcance:** el WebSocket `/websocket/updates` y activar el acceso remoto de
SQX. Si algún día hace falta, se añade como fuente extra sin cambiar la interfaz.

**Entregable:** `core/liveness.py` + `python3 -m core.liveness` + `docs/manual/16-monitor.md`.

---

### P1 · Portabilidad y roles de install
**Puede empezar:** ya · **Bloquea:** P4, S10 · **Dura:** 1–2 días · **Carpetas:** `core/`, `bin/`, `tools/`

Tres deudas que hoy impiden que exista un tercer install y que el proyecto corra en otro PC:

1. **`bin/sqx-worker.sh` y `bin/clone-sqx-worker.sh` llevan las rutas de esta máquina a fuego**
   (`/home/sergioguslw/Desktop/SQX`). Tienen que leer de `config/machine.yaml` como todo lo demás.
2. **`core/paths.py` expone un `WORKER` y un `WORKER_PORT` únicos.** Pasa a roles:
   `WORKERS = {"conductor": (ruta, 5060), "custodian": (ruta, 5070)}`, conservando `WORKER` como
   alias del conductor para no romper lo que ya existe.
3. **`tools/checks.py` solo inspecciona ficheros `.py`** (usa `depmap.py_files()`), por eso no vio
   nunca las rutas de los `.sh`. **Extiéndelo a `bin/*.sh`.**

**Entregable adicional:** `docs/SETUP-NEW-MACHINE.md` actualizado — su §2 dice hoy «dos es el mínimo
de trabajo», y la decisión es **tres con roles**; su §7 (Windows) se mantiene como está.

**Fuera de alcance por ahora:** portar `sqx-worker.sh` entero a Python. Los PCs son Linux; se hace
cuando haga falta Windows para algo más que análisis.

---

### P2 · `pipeline/` — el lote W6
**Puede empezar:** ya · **Bloquea:** nada · **Dura:** 1–2 semanas · **Carpeta:** `pipeline/` (nueva, en la raíz)

Encadena las etapas por estrategia madre, reanudable y auditable: entra una madre, sale un veredicto,
se borra lo innecesario, empieza la siguiente. Con ~100 madres son **días de máquina desatendida**,
así que la reanudabilidad y la higiene de disco son **requisitos, no detalles**.

Se construye **contra los contratos C1–C5 de la §6 y fixtures**. No necesita que exista ningún otro
módulo.

⚠️ **Esto es la cola de trabajos del futuro demonio, aunque hoy no lo parezca.** Si lo escribes como
«script que encadena etapas», se tira cuando llegue la plataforma. Escríbelo como **un modelo de
*job* con su *ledger***. Concretamente:

- `state.json` se escribe **durante** cada etapa, no al terminarla — `stages.<nombre>.progress`
  (0..100) más una línea de estado.
- **Un test que exija monotonía de ese `progress`**, para que deje de ser una buena intención.
- El ledger pesa kilobytes y **sobrevive al borrado**: es lo que hace el borrado auditable.

**Los umbrales del veredicto no bloquean esto**: son parámetros de configuración, el usuario decide,
y son cambiables. Que sean cambiables **sin reprocesar** es requisito de diseño.

**Entregable:** `pipeline/` + `docs/manual/17-pipeline.md`.

---

### P3 · `sqx/variants/` — diseño y fabricación (lote W2)
**Puede empezar:** ya, contra un `design_brief.json` de fixture · **Dura:** 1–2 semanas · **Carpeta:** `sqx/variants/`

Fabrica las 5.000 variantes `.sqx` a partir del contrato C1 y emite el manifiesto C2.

**Hechos que no hay que volver a medir** (🔬, ya en `knowhow/`):

- Los parámetros viven en **un solo sitio**: `strategy_Portfolio.xml`,
  `<variable><id>NOMBRE</id>…<value>N</value></variable>`. Las reglas referencian la variable por
  nombre, así que reescribir `<value>` reescribe la regla. **`settings.xml` no lleva los nombres de
  parámetro** — comprobado, 0 coincidencias.
- El nombre visible en el databank es `settings.xml`: `<ResultsGroup ResultName="…">` y
  `<StrategyName type="String">`. **Renombra los dos por variante** o todas caen bajo un nombre.
- **Una sola corrida de retest da las dos muestras** si el `Setup` abarca IS+OOS y el
  `<OutOfSample>` está puesto: sample 10 y sample 20 quedan en el mismo `.sqx`. **Un WFC necesita una
  corrida, no dos.**
- **`RExpectancy` lleva centinelas**: `99999.0` y `-1.0`, todas con ~1 operación. Son el 0,08 % y
  **ganan el argmax sobre 5.000 variantes**. Filtrar `|v| > 100` antes de cualquier ranking.

**Los tres modos de fallo que este módulo tiene que impedir**, porque son silenciosos: renombrado en
colisión, `<Fingerprint>` heredado, y tupla ≠ fichero. El manifiesto C2 lleva `tuple_hash`
justamente para detectar duplicados de fabricación.

**Depende de S9** para elegir forma de fichero (5 miembros / sin `optimizationProfile` / íntegro).
Mientras S9 no conteste, **programa las tres y decide al final**: es una constante, no una
arquitectura.

**Entregable:** `sqx/variants/` (diseño + fabricación) + `docs/manual/18-variantes.md`.

---

### P4 · `sqx/variants/` — ejecución y recogida (lote W3)
**Puede empezar:** tras P1, P3, S4 y S8 · **Dura:** 1 semana · **Carpeta:** `sqx/variants/`

Carga las variantes en **W2**, lanza el retest, recoge C3 (métricas) y C4 (trades), y borra.

**Reglas no negociables de este módulo:**

- **Guarda de recuento contra el sync.** Cuenta antes y después; si el databank encoge, para y
  grita. Es la regla dura 1 en forma de código.
- **`collect.py` se niega a borrar la estrategia madre** (`origin = true` en el manifiesto).
- **El orden de fila ES el `Ticket`** — verificado sobre 4.115 operaciones: ya vienen ordenadas, 0
  `Open time` duplicados, 0 solapes. **Nunca reordenar al escribir.** Comprueba por fichero
  (ordenado ∧ sin duplicados ∧ sin solapes) y, si falla, **conserva `Ticket`** en ese fichero y
  anótalo en el manifiesto.
- **El proyecto de variantes se crea en W1 y se ejecuta en W2**, nunca en el maestro. `loadconfig`
  **nunca sobrescribe**: en un nombre existente crea `MiProyecto(2)` y deja el original intacto —
  **lee la respuesta**, o verificarás el proyecto equivocado.
- **Nombres de proyecto: solo guiones bajos.** La API HTTP parte su comando por espacios.

**Formato de salida: Parquet zstd.** Medido: **6,9×** frente al CSV sin perder un dato; la poda de
columnas da 3,8× más y **es donde vive el arrepentimiento**. Trades particionados en bloques de 500
variantes.

**Entregable:** ejecución + recogida + la guarda + `docs/manual/18-variantes.md` extendida.

---

### P5 · `studies/optimisation/wfc/` (lote W5)
**Puede empezar:** ya contra fixtures de C3/C4; la corrida real tras P4 · **Dura:** 1 semana

¿Sobrevive la superficie fuera de muestra, y qué regla de selección de parámetros usar?

**El modo de fallo propio de este módulo es confundir *nivel* con *orden*, y fabricarse un n
efectivo falso.** La redundancia medida es **intra-ventana**: `NetProfit` ≡ `CAGR` ≡
`AnnualPctReturn` con ρ = 1,000 dentro de una ventana, pero **entre ventanas de distinta longitud
dejan de serlo** — que es exactamente el sesgo √T. Por eso se guardan las dos.

**Entregable:** módulo + `docs/manual/19-walkforwardcorrelation.md`.

---

### P6 · Multi-mercado (lote W8)
**Puede empezar:** tras P4 · **Dura:** 1 semana · **Carpeta:** `studies/transfer/crossmarket/`

**Extensión, no módulo nuevo:** `crossmarket/` ya construye nulos de ocupación igualada. `OPEN.md`
issue 22 deja cuatro hilos abiertos ahí; ciérralos en el mismo lote.

---

### P7 · Las skills y el orquestador
**Puede empezar:** cuando P2–P5 existan · **Dura:** 1 semana

Seis skills que envuelvan los módulos nuevos, al estilo de las que ya hay. **Las skills son, de
facto, la API de alto nivel del futuro demonio** — esa capa normalmente hay que inventarla; aquí ya
está escrita para los módulos viejos. Que los nuevos la tengan es lo que mantiene la puerta abierta.

---

## 6 · Los contratos — lo que permite trabajar en paralelo

**Congelados. Se construye contra ellos con fixtures, sin esperar al módulo anterior.** Definición
completa en `protocolo-robustez-2026-09-21.md` §2; aquí solo quién produce y quién consume.

| | fichero | lo produce | lo consume |
|---|---|---|---|
| **C1** | `design_brief.json` | `sppUltra` (ya hecho) | **P3** |
| **C2** | `manifest.parquet` — la clave de unión de todo el estudio | **P3** | P4, P5, P6 |
| **C3** | `metrics.parquet` — 41 métricas × {IS, OOS} | **P4** | P5, P6 |
| **C4** | `trades.parquet` — 12 columnas, bloques de 500 | **P4** | P5, P6 |
| **C5** | `state.json` — el ledger, **escrito durante, no al terminar** | **P2** | P0, y el futuro demonio |

**Contrato entre carriles (S → P):** el carril P programa contra la §3 de este documento — tres
installs, los roles, los puertos 5060 y 5070, y las tres reglas de oro. **No necesita saber nada
más de lo que hace el carril S.**

---

## 7 · Estado y orden — sustituye a la §9 y a «Estado a 2026-09-21» del protocolo

| lote | estado | ahora |
|---|---|---|
| **W0** `core/surface/` | ✅ hecho | — |
| **W1** `studies/breakage/spp/` | ✅ hecho | — |
| **W4** `studies/optimisation/wfm/` | ✅ hecho | — |
| **W7** presupuesto de disco + costes | ✅ hecho | `core.assets XAUUSD` ya sale 0 |
| **W2** variantes diseño+fabricación | ⬜ *«pausado por topología»* | 🟢 **P3, desbloqueado** |
| **W3** variantes ejecución+recogida | ⬜ *bloqueado ×3* | 🟡 **P4, solo espera P1+P3+S4+S8** |
| **W5** `walkForwardCorrelation` | ⬜ | 🟡 **P5, ya contra fixtures** |
| **W6** `pipeline/` | ⬜ | 🟢 **P2, desbloqueado** (los umbrales ya no bloquean) |
| **W8** multi-mercado | ⬜ | ⬜ P6, tras P4 |
| Skills + orquestador | ⬜ | ⬜ P7 |
| **Pre-registro del holdout** | ⬜ | 🔴 **O1 — MUY IMPORTANTE, ver §8** |
| **Topología de SQX** | ⬜ *«bloquea W2 y W3»* | 🟢 **decidida**, ejecuta el carril S |
| **Licencia SQX** | ⚠️ *«nadie ha leído el EULA»* | 🟢 **cerrado** — dos licencias, dos PCs |

### Grafo

```
O1 pre-registro ──── (no bloquea código, bloquea leer 2022-2026)

S1 ─┬─ S2 ──┐
    ├─ S3 ──┼─ S5 ─── S11 medidas
    └─ S4 ──┘   │
        ├─ S8 ──┼──────────────┐
        └─ S9 ──┘              │
                               ▼
P1 ─────────────────────────► P4 ──┬─► P5 ──┐
P3 ─────────────────────────►      └─► P6   ├─► P7
P2 ────────────────────────────────────────┘
P0 ─── (independiente)
S7 ─────── (independiente, hoy).  S6 retirada 2026-09-21
```

**Cinco agentes en paralelo hoy:** O1 (dueño) · S7+S9 (carril S; S6 retirada) · P0 · P1 · P2 · P3.

---

## 8 · 🔴 MUY IMPORTANTE — el pre-registro del holdout

**Es lo único de todo el plan que no se puede arreglar retroactivamente.**

Si cualquier análisis mira **2022–2026** antes de que este documento exista, el holdout queda
quemado para siempre y ningún resultado posterior sobre esa ventana es defendible. No cuesta nada.
No depende de ningún código. **Va primero.**

Fichero: **`docs/preregistro/holdout-XAUUSD-<fecha>.md`** — en el repositorio, **no** en
`AlgoData`: un pre-registro sin control de versiones no prueba nada, y la regla dura 7 habla de
*datos pesados*, no de un documento de gobierno de 150 líneas. Dice:

1. **Qué ventana es el holdout** y cuáles son IS y OOS de trabajo.
2. **Qué métrica decide y con qué umbral.** Se registra el número de hoy aunque sea provisional; si
   cambia, **se registra el cambio con su fecha**. Eso es lo que lo mantiene honesto mientras los
   criterios siguen evolucionando.
3. **Cuántas veces se puede leer** esa ventana, y quién autoriza cada lectura.
4. **Qué se hace si falla** — decidido **antes** de verlo.

Hasta que exista, **ningún módulo de este plan lee 2022–2026.** Los lotes se construyen y se
verifican contra la Fase 0 del SPP, que ya está en disco.

---

## 9 · Verificación global

Nada está terminado hasta que todo esto pasa:

```bash
python3 tools/depmap.py && python3 tools/checks.py     # 0 problems
python3 tests/test_surface.py                          # property test verde
python3 -m core.assets XAUUSD                          # preflight por activo
grep -c "Desktop/SQX" bin/*.sh                         # 0 — las rutas salen de machine.yaml
python3 -m sqx.inspect.project_health                  # ningún proyecto incompleto
```

Y tres que no son comandos:

- **Cada `__main__` nuevo tiene su página en `docs/manual/`**, en español, con capturas reales.
- **Cada hecho no obvio descubierto está en `knowhow/`**, con su etiqueta 🔬 / 📓 / 🤔, escrito en la
  misma tarea. *Un hallazgo que solo vive en un transcript muere con la sesión.*
- **Los tres installs pasan S5** con el maestro generando.

### Lo que va a `knowhow/` al terminar cada carril

| fichero | qué |
|---|---|
| `03-driving-sqx.md` | la topología de tres roles con heaps, `coreUsage` y puertos; el reparto elástico de núcleos; que SQX escucha en `0.0.0.0` **sin autenticación**; la guarda de recuento contra el sync |
| `07-practices.md` | el presupuesto de RAM y su fórmula por máquina; que `jstat -gc` separa heap comprometido de conjunto vivo y por qué el RSS de una JVM no mide nada; que `-Xms` bajo es lo que hace caber tres installs; la política de logs |
| `01-file-formats.md` | la respuesta de S9: si carga el `.sqx` de 5 miembros y si el databank deduplica por `<Fingerprint>` |
| `02-databanks.md` | que el rol de custodio elimina la clase de fallo de la regla 1, y bajo qué condición exacta |
| `04-export.md` | el throughput real del export masivo (S11), que es el único cuello de botella medido |

---

## Apéndice — lo que NO se ha verificado

Por honestidad, y porque un dossier que se lee como certero es peor que ninguno: se construye encima.

- **🤔 Que 24 GB le basten al maestro.** El conjunto vivo medido es 15,9 GB, pero es una lectura
  instantánea durante su bucle de generación. Un SPP de 15k runs lanzado desde su GUI es justo lo que
  puede empujarlo por encima. **Salida:** subirlo a 32g y bajar W2 a 40g. Se ve con `jstat` en S2.
- **🤔 Que 48 GB le basten a W2** para 5.000 variantes con mercados adicionales. Nadie lo ha corrido
  nunca. Es un techo razonado, no medido. Lo mide S11.
- **🤔 Cuánto tarda exportar los trades de 5.000 estrategias.** Sin medir, y es **el cuello de
  botella real** — no el cómputo, que son 3,5 min. Lo mide S11.
- **🤔 Si SQX carga un `.sqx` de 5 miembros** y si el databank deduplica por el `<Fingerprint>`
  heredado. Lo mata S9 con tres ficheros.
- **🤔 Si la GUI de W2 es usable y con qué precauciones.** Inferido del comportamiento del maestro,
  sin verificar.
- **🤔 La forma exacta de la respuesta de `-project action=status`** con una tarea en marcha.
- **⚠️ Las duraciones de las tareas de las §4 y §5** son juicio de ingeniería, no medición.
- **⚠️ `UlcerPerformanceIndex` no reconcilia**: forma confirmada (ρ +0,998 con
  `AnnualPctReturn/UlcerIndex`) pero la constante no converge y el residuo depende de
  `NumberOfTrades` y `DataLength`. Se usa el de SQX y se exporta.

---

*Generado el 2026-09-21. Sustituye la §9 y la tabla de estado de
`protocolo-robustez-2026-09-21.md`; lo demás de ese documento sigue vigente. La carcasa de
escritorio de `plataforma-unificada-2026-09-20.md` queda fuera de alcance por decisión del dueño.*
