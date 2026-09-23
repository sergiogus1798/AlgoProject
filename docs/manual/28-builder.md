# 28. Builder — de una plantilla a un proyecto que arranca, en un comando

### Qué pregunta responde

Tienes una plantilla en la librería y quieres que SQX genere estrategias con ella sobre un activo.
Esto monta el proyecto entero: clona el donante, se queda solo con la tarea de construcción, apunta
la plantilla, pone los topes, deja los databanks escribiendo a disco, fecha la ventana desde
`assets/` y lo instala. **Hasta el 2026-09-23 esos cinco pasos se editaban a mano en el XML de la
tarea**, que es lo que impedía meter la cadena dentro de una aplicación.

### Cuándo lo usas, y cuándo no

Cuando la plantilla ya existe y está registrada. No sirve para crear la plantilla —eso es
`/strategy-template`— ni para lanzar la construcción: esto deja el proyecto listo, y arrancarlo es
una decisión aparte porque cuesta CPU.

### Antes de empezar

1. **La instalación de destino tiene que estar parada.** Reescribe el `project.cfx` al salir y se
   comería el proyecto recién escrito (regla dura 4). El comando se niega si el puerto contesta.
2. **Regla dura 5**: el activo tiene que tener sus costes pactados. Si alguno sigue en `use: null`,
   el comando para y te dice cuál.
3. **El bloque de la plantilla tiene que estar en esa instalación**:
   `python3 -m sqx.inspect.vocabulary --diff custodian`.

### Cómo se ejecuta

```bash
python3 -m sqx.projects.builder chat_v2 \
    --template ~/Desktop/AlgoData/templates/library/keltnerUpperCrossUp/template.sqx \
    --symbol XAUUSD --role custodian --max-strategies 25 --minutes 8
```

| flag | obligatorio | qué hace |
|---|---|---|
| `name` | sí | nombre del proyecto, **solo guiones bajos** — la API parte por espacios |
| `--template` | sí | el `.sqx` de la librería |
| `--symbol` | sí | activo de `assets/`; de ahí salen la ventana y los costes |
| `--role` | no | instalación destino; `custodian` por defecto |
| `--max-strategies` | no | tope de estrategias, 30 por defecto |
| `--minutes` | no | tope de reloj, 10 por defecto |
| `--donor` | no | proyecto del que clona; el XAUUSD congelado por defecto |
| `--json` | no | emite el resultado como JSON y nada más — **esto es lo que consume un chat** |

Instantáneo: mueve ficheros y reescribe XML, no arranca SQX.

### Qué produce

```
<instalación>/user/projects/<nombre>/project.cfx           el proyecto
<instalación>/user/settings/StrategyTemplates/authored/    la plantilla, con su propio nombre
```

La plantilla se instala con el nombre de **su carpeta de librería**, no con el del fichero: todas
las carpetas guardan un `template.sqx`, así que instalarlas por el nombre del fichero haría que dos
plantillas distintas se pisaran en silencio.

### Cómo se lee el resultado

```
chat_v2 on SQX_w2
  template  .../StrategyTemplates/authored/keltnerUpperCrossUp.sqx
  tasks     Build   caps 25 strategies / 8 min
  segments  Build-Task3.xml=build
  to disk   Results, Last generation, Initial population, Strategies to improve
  costes    NO van en la tarea: una InstrumentInfo que no coincida con el registro
            de SQX deja el proyecto irresoluble. Aplícalos con el install vivo:
            -instrument action=edit instrument=XAUUSD_Infinox defaultspread=10.0 ...
  ⚠️ PROVISIONAL: spread_is, spread_oos, commission, slippage, swap_long, swap_short
```

Cuatro cosas que decide esa salida:

- **`to disk`** — los databanks que estaban en `Auto-sync never` y ahora escriben. Sin eso, tras
  generar el directorio queda vacío y `/curate` no tiene ficheros que mover.
- **`segments`** — de qué tramo sale la ventana de cada tarea. `build` es la única muestra que ve
  el generador.
- **`costes`** — no se escriben en la tarea, y el motivo está medido: ver `knowhow/03-driving-sqx.md`.
- **`PROVISIONAL`** — cifras de trabajo del dueño, no pactadas con el bróker. Marcan todo resultado.

Si la plantilla fuese a ignorarse —`type="simple"` con un `templateFile` puesto— **aborta** en vez
de construir. Esa comprobación es gratis: lee un atributo, mientras que demostrar lo mismo después
cuesta la construcción entera.

### Un ejemplo completo

```bash
python3 -m sqx.projects.builder chat_v2 --template .../keltnerUpperCrossUp/template.sqx \
    --symbol XAUUSD --role custodian --max-strategies 25 --minutes 8
bin/sqx-worker.sh --role custodian start
python3 -c "from core import worker; print(worker.call('-project action=start name=chat_v2','custodian'))"
```

Resultado real del 2026-09-23: el proyecto arranca, genera **25 estrategias**, quedan **25 en
disco**, y la puerta de la plantilla da **25/25 llevan el bloque fijo**
(`python3 -m sqx.inspect.template_check --role custodian chat_v2`).

### Qué NO te dice

- **No dice si la estrategia sirve.** Un proyecto que arranca y genera no es una estrategia buena.
- **No aplica los costes.** Los imprime como comando; aplicarlos en el registro de SQX es un paso
  aparte y **global a la instalación**.
- **No lanza la construcción.** A propósito: eso cuesta horas y es una decisión del dueño.

### Si algo falla

`Project has unresolved resources` al arrancar — la `InstrumentInfo` de alguna tarea no coincide con
el registro de SQX. No lo arregla este comando; ver `knowhow/03-driving-sqx.md`.

`the custodian is running and rewrites a project.cfx on exit` — párala primero.

`'<nombre>': project names are underscores only` — la API HTTP parte el comando por espacios.
