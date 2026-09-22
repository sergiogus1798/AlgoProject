# Contexto para el agente que va a diseñar el ecosistema de skills de SQX

No es un encargo: es el estado del terreno. El dueño te dirá él mismo qué skills quiere. Esto es lo
que necesitas saber antes de que te lo diga, para no proponer algo que ya existe ni repetir errores
que ya costaron horas de máquina.

**Lee también** `CLAUDE.md` (las nueve reglas duras) y `sqx/CLAUDE.md` (los carriles). Este
documento no los sustituye.

---

## 1 · Qué es esto

StrategyQuant X genera y testea estrategias para MT5; Python hace las matemáticas encima. El
objetivo actual es un **protocolo de robustez**: coger una estrategia madre, ver de qué parámetros
depende, fabricar miles de variantes suyas, retestearlas todas y decidir si su ventaja es real o es
ruido con buena pinta.

Tres árboles, y la frontera entre ellos es regla dura:

| dónde | qué | peso |
|---|---|---|
| `~/Desktop/SQX*` | los tres installs de SQX | 94 + 4,4 + 4,3 GB |
| `~/Desktop/AlgoData` | **todo dato que el proyecto produce** | 7,3 GB |
| `~/Desktop/AlgoProject` | **solo código y texto.** Nunca datos | 30 MB |

`docs/manual/20-donde-esta-todo.md` es el mapa completo. Hay 24 páginas de manual; cada comando
tiene la suya y `tools/checks.py` falla si falta.

## 2 · La topología: tres installs con papeles distintos

| | install | puerto | papel |
|---|---|---|---|
| **M** | `~/Desktop/SQX` | 5050 | el maestro del dueño. **Solo lectura** |
| **W1** | `~/Desktop/SQX_w1` | 5060 | **conductor**: trabajos cortos, siempre despierto |
| **W2** | `~/Desktop/SQX_w2` | 5070 | **custodio**: un trabajo largo cada vez |

Se pilotan con `bin/sqx-worker.sh [--role conductor|custodian] start|stop|check` y desde Python con
`core.worker.call(cmd, role=...)`. `core/paths.py` es el único módulo autorizado a saber dónde vive
nada; `checks.py` revienta si aparece una ruta absoluta en cualquier otro sitio, incluidos los `.sh`.

**El maestro no se toca.** Leer sus ficheros está bien; `sqcli` contra él, no. Y nunca
`pkill -f StrategyQuantX`: ese patrón casa con tu propio shell. Matar por PID.

## 3 · Las trampas de SQX. Todas medidas, todas silenciosas

Esto es lo caro de este proyecto y lo que más valor tiene meter en skills. **Ninguna de estas
escribe un error en ningún log.** Están todas en `knowhow/03-driving-sqx.md` con su medición.

| lo que pasa | la realidad |
|---|---|
| `-project action=startOnlyTask` | **no hace nada.** Dice que arranca y testea 0, para siempre. Hay que usar `action=start` |
| Un segundo `action=start` | **no hace nada** si no va precedido de `action=stop` |
| Tarea Retest sin `<Databanks retestSelected="false">` | retestea "la selección", que está vacía, y reporta 0 |
| Un `<Chart>` con un símbolo que no existe | mata la tarea sin hacerla fallar — **aunque su cross-check esté apagado** |
| `-databank action=count` | hace sync-from-files y **destruye** lo que `action=load` acaba de cargar. Verificar con `action=export` |
| `action=clear` | vacía memoria; al arrancar SQX recarga del disco |
| Editar un `project.cfx` con el install vivo | SQX lo reescribe al salir y tu cambio se pierde |
| ...y al revés | la reescritura al salir es **cómo un `loadconfig` se vuelve permanente** |
| `SequentialOptimization` | **NO es el SPP.** Ver §4 |
| Nombres de proyecto con espacios | la API HTTP parte su comando por espacios. Solo guiones bajos |

Y una que no es de SQX sino de método: **una estrategia sacada de `raw/.../strategies/` ya trae un
`optimizationProfile.bin` del maestro dentro.** Leerlo de vuelta tras una corrida parece éxito y no
lo es. Probar sobre una variante fabricada, que no tiene ese miembro.

## 4 · El SPP, que es donde más se ha sangrado

`OptProfileSysParamPermutation` es el SPP. `SequentialOptimization` está al lado en el mismo
`<CrossChecks>`, suena igual, y **no escribe perfil**. Encender el equivocado costó **47 núcleos
durante 91 minutos** para nada — y todos los síntomas encajaban con «el SPP no persiste headless»,
que es como quedó anotado en falso.

Los valores por defecto del dueño, salvo que él diga otros:

| ajuste | valor | por qué |
|---|---|---|
| `MaxTests` | **15.000** (10.000 vale) | ⚠️ una tarea donante trae `1000000001`, el centinela de **exhaustivo**. Fijarlo, nunca heredarlo |
| `DistributionUp/Down` | **35 o 40** | ±30 se queda corto |
| `Steps` | `round(2 × spread / 4)` → 18 con ±35 | ~4 % por paso |
| `WhatToParametrize` | `type="0"`, solo `Recommended` | elegir familias a mano permuta lo que la estrategia no usa |

**Todo lo demás de la tarea** — ventana IS/OOS, cierre de viernes, money management, salidas,
spread — tiene que **coincidir con lo que la estrategia traiga**. Por eso una tarea se construye
**copiando una que el dueño ya usa** y sustituyendo solo el bloque de cross-checks y los databanks.
Nunca a mano: una tarea hecha a mano se deja elementos y falla en silencio.

Ya existe la skill `sqx-spp` con todo esto. `sqx/variants/harness.py` lo implementa.

## 5 · Qué hay construido ya

**Skills** (`tools/sqx-lab/plugins/sqx-lab/skills/`): `sqx-custom-block`, `sqx-random-group`,
`sqx-strategy-template`, `sqx-strategy-project`, `sqx-spp`. Las cuatro primeras son de autoría
(bloques → grupos → plantillas → proyectos de build) y vienen de fuera; `sqx-spp` la escribimos aquí.

**Módulos del repo que ya conducen SQX:**

| | qué hace |
|---|---|
| `sqx/variants/harness.py` | reconstruye el arnés de una tarea copiando la del donante congelado |
| `sqx/variants/spp.py` | corre un SPP en el custodio y deja el perfil donde el exportador lo lee |
| `sqx/variants/make.py` | diseño → 5.000 `.sqx` + manifiesto (contrato C2) |
| `sqx/variants/execute.py` | carga el lote, lo retestea, exporta el panel |
| `sqx/variants/collect.py` | une panel y manifiesto (C3) y **aborta si los controles no se movieron** |
| `sqx/export/export_spp.py` | exporta perfiles SPP; `--role` para leer de un worker |
| `sqx/inspect/` | lectura pura: `dump_project.py`, `project_health.py` |
| `strategies/walkForwardCorrelation/` | el estudio y su gráfico |
| `pipeline/` | encadena las diez etapas con libro mayor reanudable |

**El pipeline entero es un comando** y mide cada etapa sola (`pipeline/ledger/cost.py` muestrea los
dos árboles de procesos, incluido el JVM que `getrusage` no ve):

```bash
python3 -m pipeline.run --project XAUUSD --databank SPP_IS --strategy "Strategy 17.9.39"
```

`spp_is → spp_oos → spp_export → sppultra → design → build → ran → collected → wfc → verdict`

## 6 · Lo que cuesta, medido

`docs/AgentPDFs/coste-pipeline-2026-09-22.md` tiene el detalle. Lo que decide un diseño:

- **Fabricar es gratis**: 2,6 ms y 14 KB por variante. 5.000 son 13 s y 70 MB.
- **Retestear**: 47 ms por variante con un mercado, 90 ms con dos. Un mercado adicional cuesta
  **otro backtest entero**, +90 % de tiempo y +76 % de memoria.
- ⚠️ **Y el export del databank no devuelve ni una columna del mercado adicional.** Hoy se paga el
  doble por resultados que no se pueden leer. Está sin resolver.
- **El JVM es toda la memoria**: 21 GB con dos mercados y 2.000 variantes. Python nunca pasa de 300 MB.
- **La memoria, no el tiempo, es el límite de un SPP.** El perfil pesa ~20 MB en disco y decenas de
  gigas mientras se construye. **Nunca dos SPP en el mismo install.**

## 7 · Cómo se sabe que algo funcionó

Tres costumbres que valen más que cualquier test:

1. **Preguntarle a SQX qué cargó**, no fiarse del fichero escrito: `-project action=saveconfig` y
   leer el `.cfx` que devuelve.
2. **Controles positivos.** `collect.py` cuenta cuántos resultados distintos devolvieron los
   controles y aborta si todos coinciden — que es exactamente cómo se ve un lote que nunca corrió.
3. **La memoria del JVM como señal de vida.** Un SPP no reporta progreso: escribe sus líneas de log
   en los primeros segundos y calla media hora. Subiendo = trabajando. Plana = colgado.

## 8 · Dónde queda cada cosa

| | |
|---|---|
| hechos sobre SQX | `knowhow/` — `INDEX.md` primero. `01-file-formats.md` y `03-driving-sqx.md` son los gordos |
| cómo se ejecuta algo | `docs/manual/` — `00-empezar.md`, luego la página del módulo |
| qué está roto o pendiente | `OPEN.md` |
| qué cuesta cada cosa | `docs/AgentPDFs/coste-pipeline-2026-09-22.md` |
| el protocolo de robustez | `docs/AgentPDFs/protocolo-robustez-2026-09-21.md` |

**Regla permanente del proyecto:** un hallazgo no obvio se escribe en el `knowhow/` que toque **en
la misma tarea**, etiquetado 🔬 probado · 📓 de logs · 🤔 inferido. Un hallazgo que solo vive en un
transcript muere con la sesión — y este proyecto ya ha pagado esa factura varias veces.

Si encuentras una conclusión anterior que resultó falsa, **márcala como superada, no la borres**.
Hay dos así en `03-driving-sqx.md`: las mediciones eran correctas y enseñan cómo se construye una
conclusión equivocada con confianza cuando corres todos los controles menos el que importaba.

## 9 · Lo que sigue abierto

- **Las columnas del cross-check de mercado no se exportan.** Es la optimización más rentable que
  hay sobre la mesa: resolverla o apagar el cross-check.
- **Los costes de XAUUSD son PROVISIONALES** (defaults de SQX, no cifras de Infinox). El
  `state.json` lo marca con `costs_provisional: true`. No cambiarlos sin el dueño.
- **El pre-registro del holdout está sin firmar** (`docs/preregistro/`). Es una puerta de un solo
  sentido: hasta que esté firmado, ningún módulo lee 2022–2026.
- **La corrida de las 3 madres está preparada y sin lanzar.** Las madres están congeladas en
  `AlgoData/donors/madres-2026-09-22/` con 6, 8 y 11 parámetros a propósito, y su md5 en
  `MADRES.json`. `Test_XAUUSD` en W2 es el proyecto de prueba con el SPP bien configurado.
