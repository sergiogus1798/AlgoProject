# ENCARGO 1 — Instalaciones de StrategyQuant X

**Tu oficio:** sistema. Bash, ficheros de configuración, `sqcli`. **No escribes código Python del
proyecto**; como mucho ejecutas herramientas que ya existen.

**Tu encargo son tres tareas** — la cuarta fue **anulada por el dueño el 2026-09-21** y sigue abajo
solo para que no la vuelva a recoger nadie. Las tres se pueden hacer hoy. No necesitas leer el plan
grande.

---

## 0 · Antes de tocar nada

**Lee, en este orden:** `CLAUDE.md` entero · `knowhow/02-databanks.md` · `knowhow/03-driving-sqx.md`.

Las cuatro reglas que muerden en este encargo. Cada una ha destruido trabajo ya:

1. **Cada sync de SQX borra del disco los `.sqx` que no tiene en memoria.** No es al apagar: hay
   auto-sync horario. Por eso la tarea 1 es un snapshot y va primero.
2. **Nunca `sqcli` contra el maestro mientras su GUI está levantada** — responde `Error: CLI not
   ready.`. Usa el worker en **5060**. Y **nunca `pkill -f StrategyQuantX`**: ese patrón casa con tu
   propio shell. Matar por PID.
3. **No arranques builds, y no cambies qué construye un proyecto.** La configuración del maestro es
   del dueño. Generación genérica o por plantilla, una tarea inactiva, lo que una tarea limpia: son
   decisiones suyas, **no son bugs y no son hallazgos que reportar**.
4. **Nunca edites un `project.cfx` que una instancia viva tiene abierto.** SQX reescribe el fichero
   al guardar y al salir, y tu cambio se pierde en silencio.

**Estado de la máquina que te vas a encontrar:** maestro en `~/Desktop/SQX` con la GUI levantada y
generando; worker en `~/Desktop/SQX_w1`, apagado, API en 5060. Un tercer install (`SQX_w2`) está
planificado pero **no existe todavía y no es tuyo en este encargo**.

---

## Tarea 1 · Snapshot de seguridad  ✅ hoy

Antes de que nada reinicie SQX ni escriba en un databank.

Copia `user/projects` de **los dos** installs a `AlgoData/snapshots/<AAAA-MM-DD>/`, separando
maestro y worker.

Escribe dentro un `MANIFIESTO.txt` con **el recuento de `.sqx` por proyecto y por databank**, en el
origen y en la copia. Sin ese recuento el snapshot no sirve: no podrías demostrar que está completo.

**Verificación:** los dos recuentos coinciden, proyecto a proyecto y databank a databank. Si alguno
no coincide, para y dilo — significa que algo estaba escribiendo mientras copiabas.

⚠️ Ojo con el espacio: el maestro ocupa 98 GB, pero **84 de ellos son `user/data/History`**, que no
entra aquí. `user/projects` son ~4,2 GB.

---

## Tarea 2 · La sonda de tres ficheros  ✅ hoy — *es lo que otro agente está esperando*

**Dos preguntas abiertas que deciden si las 5.000 variantes futuras ocupan 57 MB o 500 MB.** Se
matan con tres ficheros y unos segundos.

1. **¿Carga SQX un `.sqx` de 5 miembros?** Es decir, conservando solo `META-INF`, `settings.xml`,
   `strategy_Portfolio.xml`, `lastSettings.xml` y `version.txt`. Pesos medidos: **11,3 KB** así,
   **100 KB** sin `optimizationProfile.bin`, **5.215 KB** íntegro.
2. **¿El databank deduplica por el `<Fingerprint>` heredado** del original? Si deduplica, tres
   variantes del mismo padre se convierten en una y el estudio entero es imposible tal y como está
   diseñado.

**Método.** Toma `Strategy 17.9.39` y fabrica tres variantes a mano:

- Los valores de parámetro viven en **un solo sitio**: `strategy_Portfolio.xml`, en
  `<variable><id>NOMBRE</id>…<value>N</value></variable>`. Las reglas referencian la variable por
  nombre, así que reescribir `<value>` reescribe la regla. 🔬 `settings.xml` **no** lleva los nombres
  de parámetro — comprobado, cero coincidencias.
- **Renombra las dos cosas** o las tres caen bajo el mismo nombre: `<ResultsGroup ResultName="…">`
  y `<StrategyName type="String">`, ambas en `settings.xml`.

Cárgalas en un databank del **conductor (5060)** y cuenta.

> **Corrección al plan:** el plan ponía esta tarea «tras clonar W2». Es innecesario — son tres
> ficheros, y W1 ya existe. Hazlo en W1 hoy.

**Entregable, y es lo importante:** la respuesta 🔬 a las dos preguntas, escrita en
`knowhow/01-file-formats.md` con su fecha. Un agente que trabaja en `sqx/variants/` la está
esperando para elegir forma de fichero.

⚠️ Arranca el worker con `bin/sqx-worker.sh start`, haz el trabajo, y **`bin/sqx-worker.sh stop`
cuando termines**. Un trabajo, y se para. El puerto abre y responde `Error: CLI not ready.` durante
unos 20 s antes de aceptar comandos: eso es normal, se sondea, no se concluye que está roto.

---

## Tarea 3 · Higiene de logs  ✅ hoy

`user/log/StrategyQuant/` crece sin techo y rápido. Tamaños reales:

```
log_2026_09_18.log     1,1 MB
log_2026_09_19.log     1,2 MB
log_2026_09_20.log    55,5 MB      ← 46 veces más
```

Deja una poda por antigüedad. **No toques el log del día en curso**, que está abierto.

Anota la política que hayas puesto (cuántos días se guardan, qué se borra) en
`knowhow/07-practices.md`.

⚠️ Ese log **nunca se lee entero: se tailea.** Si necesitas mirarlo, `tail` y `grep`.

---

## Tarea 4 · ~~Reparar el proyecto roto~~  ⚪ **ANULADA POR EL DUEÑO, 2026-09-21**

**No se hace.** El dueño la retiró: «olvídate de ese proyecto del SP500 · quita de la ejecución del
plan ese punto». `Infinox_SP500ft_H4_HighPrecision` no se repara.

El diagnóstico queda registrado en `OPEN.md` issue 3 (⚪) y en `knowhow/03-driving-sqx.md`. Lo que
hay que arrastrar a cualquier trabajo futuro son las dos consecuencias, que ahora son permanentes:

- **La lista viva de proyectos siempre dará 14 contra 15 directorios.** Sigue diffeando la lista
  contra el directorio — pero ese hueco concreto es este, no un fallo nuevo.
- **El error horario `Project ... does not exist.` se sigue escribiendo.** La tarea 3 acota el disco,
  no apaga la causa: quien lea el log del maestro tiene que filtrar `ProgressEngine` en origen.

## Lo que NO es tuyo en este encargo

Dilo si te lo encuentras, pero no lo hagas:

- **Redimensionar heaps, capar núcleos, clonar el tercer install (`SQX_w2`).** Necesitan la GUI
  cerrada y son un encargo aparte que el dueño lanzará cuando pueda parar el maestro.
- **Cualquier cosa en `core/`, `sqx/` o `pipeline/`.** Hay tres agentes Python trabajando ahí a la
  vez que tú.
- **La configuración de los proyectos del dueño.** Regla 3.

---

## Cómo cierras

Devuelve:

1. **Qué hiciste**, tarea a tarea.
2. **Qué verificaste**, con la salida de los comandos pegada — no «funcionó».
3. **Qué dejó sin hacer y por qué** (la tarea 4 si el dueño no cerró la GUI).
4. **Los dos hechos nuevos de la tarea 2**, ya escritos en `knowhow/01-file-formats.md`, y la
   política de logs en `knowhow/07-practices.md`. Etiqueta la procedencia: 🔬 probado · 📓 de logs ·
   🤔 inferido.

Un hallazgo que solo vive en un transcript muere con la sesión. Por eso el punto 4 es parte del
trabajo, no un extra.
