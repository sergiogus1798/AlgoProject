# 57 · Gorilla en la ventana — primero mirar, luego lanzar

**Tu oficio:** Fase 1 (mecánica): daemon en leaseWeb que lee `/proc` de gorilla por SSH; Fase 2 (diseño): selector de servidor en los tres lanzadores. Sonnet para Fase 1 una vez diseñada; Opus para Fase 2.

**Tu encargo:** la ventana ve a gorilla (Ryzen 7950X, conductor_gorilla 5060, custodio_gorilla 5070). Dos fases sin solaparse: primero mirar, luego lanzar.

Lee `CLAUDE.md` (reglas 3, 8, 12) · `ui/README.md` · `ui/daemon/ops/pulse.py` (qué lee hoy leaseWeb) · `config/machine.yaml` · `core/paths.py`.

## Estado del plan

| # | fase | qué | modelo | bloqueado por | estado |
|---|---|---|---|---|---|
| 1 | SOLO MIRAR | bloque «custodio_gorilla» en «En marcha»; misma forma que leaseWeb: backtests, JVM, CPU, RAM libre, proyecto en marcha | Sonnet (mecánica) | nada | pendiente |
| 2 | MIRAR Y LANZAR | selector de servidor en los tres lanzadores; colector de supervivientes y ledger | Opus (diseño) | **respuestas del dueño (§2.1-2.3)** | pendiente, bloqueado |

### Bitácora

- 2026-10-10 — Encargo nuevo, propuesto por el dueño.

---

## Fase 1 · SOLO MIRAR (pequeño, primero)

**Objetivo:** en el panel «En marcha» de la ventana, un segundo bloque «custodio_gorilla» igual al de leaseWeb. Backtests finalizados de un total, memoria JVM contra su techo, CPU, RAM libre, proyecto en marcha y su paso; más los procesos Python del workflow.

**Cómo:** `pulse.py` de leaseWeb lee archivos y `/proc`. Gorilla tiene el mismo código. El demonio en leaseWeb llama a gorilla por SSH (un comando que devuelve JSON), lo pinta. Refresco cada pocos segundos, con timeout; si gorilla no contesta, el bloque dice «sin conexión», sin bloquear la ventana.

**Qué revisar antes de prometer:**
- Cómo lista hoy la ventana procesos Python en leaseWeb (en `pulse.py`).
- Si lo mismo se puede leer en gorilla por SSH.

**Normas:**
- Estilo terminal de la ventana (`theme.T`, frame `term`).
- Leer `ui/README.md` antes de cualquier cambio.
- La llamada a SSH sólo lee. Nunca `count`, `load` ni `export` en custodio (regla 3).
- Capítulo del manual actualizado (regla 8).
- Después, `/ui-shot` con la ventana corriendo en gorilla.

**Terminado cuando:** con un workflow en marcha en gorilla, la ventana de leaseWeb muestra su progreso sin escribir nada; gorilla apagada, la ventana abre igual y dice «sin conexión».

---

## Fase 2 · MIRAR Y LANZAR (después, más grande; espera decisiones del dueño)

**Objetivo:** los tres botones («Lanzar en SQX», «Continuar workflow», cola de investigación) eligen servidor: leaseWeb o gorilla.

**Piezas:**
- `bin/remote.sh` — tres verbos: push (git pull en gorilla + envía la plantilla y paleta), run (lanza `bin/workflow.sh`, detached), collect (trae supervivientes y la carpeta `AlgoData/autopilot/<P>/<run>/`).
- Fusión de lo que gorilla escribe (ledger, `projects/registry.csv`, tienda de estrategias, `templates/runs.csv`) sin perder ni duplicar.
- Selector en los tres lanzadores.
- Negarse a lanzar mientras corre `bin/mirror-data.sh` y al revés.

**Preguntas abiertas para el dueño (regla 11):**
- ¿Cuál lanzador primero?
- ¿Collect automático al fin o botón?
- ¿El conteo de trials del ledger se comparte entre servidores desde el lanzamiento o sólo en collect?
- ¿Qué pasa a un run en gorilla si leaseWeb se apaga?

**Deuda antes de confiar:** equivalence test — mismas estrategias fijas en ambos servidores, listas de operaciones idénticas.

**Terminado cuando:** un workflow desde la ventana en gorilla acaba con sus estrategias en la tienda de leaseWeb y sus trials en el ledger de leaseWeb, sin comandos.

---

## Sugerencias

- Fase 1: Sonnet, mecánica pura una vez diseñada.
- Fase 2: Opus para las decisiones de diseño con el dueño.

## Respuestas del dueño (2026-10-14)

**Contestadas por el dueño (2026-10-14)** — lo que sigue manda sobre la lista de abajo:
- 57-1 → **«Lanzar en SQX» primero**. 57-2 → **botón** para traer supervivientes. 57-3 → **ledger único** (66 D27).
- 57-4 → **la corrida sigue en gorilla** y se recoge al volver. Lo hallado en gorilla se verifica (paso 26) en el MT5 de leaseWeb.
- **Encargo PARADO por el dueño (2026-10-14)**, las dos fases: no se conecta ni se pone a correr gorilla desde la ventana hasta que él lo diga.

- **Hallazgo del encargo 71 (2026-10-14):** el «collect» de la fase 2 es lo único que falta para que una superviviente de gorilla llegue al MT5 Bridge de leaseWeb (paso 26); hoy no existe ningún camino de vuelta. Detalle en `OPEN.md` #123.
