# 47. El proyecto del workflow — todas las pruebas de una estrategia en un solo custom project

## Qué pregunta responde

¿Dónde corre cada prueba de SQX de una población, del build a la Walk Forward Matrix? En **un único
custom project**, creado en el paso 5 con todas las tareas del workflow dentro. Cada paso enciende
sólo las suyas antes de lanzar, y SQX se salta las apagadas. Dos comandos: `builder --workflow` lo
crea y `stage` elige qué paso corre en el próximo `start`.

Decisión del dueño, 2026-09-25: "que se creen todas las tasks dentro del mismo custom project".

## Cuándo lo usas, y cuándo no

- **Sí:** siempre que una plantilla entra en el workflow. `/template-run` lo crea así, y el resto
  de skills (`/crossmarket`, `/crosstf`, `/mcretest`, `/spp`, `/variants`, `/wfm`) configuran y
  corren su tarea dentro de ese mismo proyecto.
- **No:** para una prueba suelta sobre un proyecto hecho sólo para ella (por ejemplo el antiguo
  `USDJPY_variantes`). Ahí se sigue usando `builder --tasks … --only …`. `stage` se niega sobre un
  proyecto que no lleva las tareas del workflow, y los configuradores lo avisan con un ⚠️.

## Antes de empezar

- `python3 -m core.assets <SIMBOLO>` con salida 0 (regla dura 5).
- **La instalación donde vive el proyecto, parada.** SQX reescribe el `.cfx` al salir y se perdería
  el cambio (regla dura 4). Los dos comandos se niegan si la instalación está arriba.
- Una plantilla ya en la librería (`~/Desktop/AlgoData/templates/library/<nombre>/template.sqx`).

## Cómo se ejecuta

Crear el proyecto (paso 5):

```bash
python3 -m sqx.projects.builder XAUUSD_keltner_H1 \
    --template ~/Desktop/AlgoData/templates/library/keltnerUpperCrossUp/template.sqx \
    --symbol XAUUSD --timeframe H1 --role custodian --workflow --max-strategies 2000 --minutes 90
```

Elegir qué corre en el próximo `start`, a mano:

```bash
python3 -m sqx.projects.stage --cfx ~/Desktop/SQX_w2/user/projects/XAUUSD_keltner_H1/project.cfx \
    --step spp
```

| flag | obligatorio | qué hace |
|---|---|---|
| `--workflow` (builder) | no | mete todas las tareas del workflow en el proyecto; sin él, el builder se queda con `--tasks`/`--only` como antes |
| `--cfx` (stage) | sí | el `project.cfx` del proyecto |
| `--step` (stage) | sí | uno o varios pasos separados por comas: `build`, `oos`, `crossmarket`, `crosstf`, `mcretest`, `spp`, `wfm`, `wfc` |

Normalmente no hace falta llamar a `stage`: **cada configurador lo hace solo para su paso** al
terminar (`sqx.projects.crossmarket`, `crosstf`, `mcretest`, `spp`, `wfc`, `wfm`). Tardan menos de
un segundo y no arrancan SQX.

## Qué produce

`<instalación>/user/projects/<nombre>/project.cfx` con 18 tareas:

| paso | tarea(s) | lee → escribe |
|---|---|---|
| build | `CONSTRUCCION` | — → `Results` |
| oos | `OOS` | `Results` → `OOS` |
| crossmarket | `Retest Markets - Family` | `OOS` → `Retest Markets - Family` |
| mcretest | `MCR 1 Bar` … `MCR 8 Stress` | lo que diga `--input` |
| spp | `SPP IS`, `SPP OOS` | lo que diga `--input` |
| wfm | `WFM` | lo que diga `--input` |
| crosstf | `CrossTF` (añadida) | `CrossTF_Input` → `CrossTF`, ventana `build..oos1` |
| wfc | `WFC 1 IS`, `WFC 2 OOS1`, `WFC 3 OOS2` (añadidas) | `WFC_Variants` → `WFC_Build`, `WFC_OOS1`, `WFC_OOS2` |

`MC Trades` y las tareas auxiliares del donante (`Clear databanks`, `Go To Task`) no entran: ningún
paso las corre, y un `Go To Task` activo hace que `action=start` no acabe nunca. **Sobrescribe** un
proyecto que ya tenga ese nombre en esa instalación.

## Cómo se lee el resultado

Salida real del builder, 2026-09-25 (la línea nueva es `workflow`):

```
test_workflow on SQX_w1
  template  ~/Desktop/SQX_w1/user/settings/StrategyTemplates/authored/keltnerUpperCrossUp.sqx
  workflow  + CrossTF, WFC 1 IS, WFC 2 OOS1, WFC 3 OOS2: todas las tareas del workflow, activas sólo CONSTRUCCION y OOS. CrossTF va a build..oos1; las WFC se precian con sqx.projects.wfc
  doctrina  H1 en todas las tareas, sesión XAUUSD_ftmo, salida por barras 2–24
  to disk   Results, Last generation, Initial population, Strategies to improve
  ⚠️ PROVISIONAL: spread_is, spread_oos, commission, slippage_is, slippage_oos, swap_long, swap_short
```

Salida real de `stage --step spp` sobre ese proyecto. `●` corre en el próximo `start`, `·` se
salta:

```
test_workflow: el proximo `action=start` corre spp
  · CONSTRUCCION
  · OOS
  · Retest Markets - Family
  · MCR 1 Bar
  ...
  · MCR 8 Stress
  ● SPP IS
  ● SPP OOS
  · WFM
  · CrossTF
  · WFC 1 IS
  · WFC 2 OOS1
  · WFC 3 OOS2
```

Lo que dice el log de SQX al lanzar el paso `wfc` (🔬 2026-09-25, conductor, 3 madres):

```
CONSTRUCCION : SKIPPED, inactive task
...
CrossTF : SKIPPED, inactive task
WFC 1 IS : Task finished in 16.52 s.
WFC 2 OOS1 : Task finished in 7.03 s.
WFC 3 OOS2 : Task finished in 5.60 s.
Project finished
```

**Lo que hay que mirar:** que las `●` sean justo las del paso que vas a correr. Si `CONSTRUCCION`
sale con `●` cuando no toca, el `start` vuelve a construir desde cero y pisa `Results`.

## Un ejemplo completo

Un paso cualquiera, el SPP, sobre el proyecto del workflow en el custodio:

```bash
python3 -m core.assets XAUUSD
python3 -m sqx.projects.spp XAUUSD --cfx ~/Desktop/SQX_w2/user/projects/XAUUSD_keltner_H1/project.cfx \
    --input OOS                          # el databank con los supervivientes que llegan aquí
# … imprime `el proximo `action=start` de XAUUSD_keltner_H1 corre solo `spp``
bin/sqx-worker.sh --role custodian start
python3 -c "from core import worker; worker.call('-project action=stop name=XAUUSD_keltner_H1','custodian')"
python3 -c "from core import worker; worker.call('-project action=start name=XAUUSD_keltner_H1','custodian')"
# mientras corre, sólo `-project action=status`; el final es `Project finished` en el log de SQX
bin/sqx-worker.sh --role custodian stop
```

El `stop` antes del `start` es obligatorio: en un proyecto que ya corrió, un segundo `start` sin él
no hace nada, y no avisa.

## Qué NO te dice

- Que la tarea esté bien configurada: eso lo dice cada configurador en su salida. `stage` sólo
  enciende y apaga.
- Qué databank lee cada paso de la mitad del embudo: las MCR, el SPP y la WFM leen lo que les pases
  con `--input`, y eso lo decides tú según lo que haya sobrevivido.
- Nada sobre el `oos2`: la WFM y el WFC lo gastan igual en un proyecto que en otro.

## Si algo falla

- `<proyecto> no lleva la(s) tarea(s) …` — no es un proyecto de workflow. Créalo con `--workflow` o
  usa el proyecto suelto sabiendo qué tareas tiene activas.
- `el custodian tiene este proyecto abierto…` — para la instalación con `bin/sqx-worker.sh --role
  custodian stop` antes de tocar el `.cfx`.
- `⚠️ <proyecto> no es un proyecto de workflow` (en un configurador) — ha escrito su tarea pero no
  ha tocado qué está activo. Míralo antes de lanzar.
