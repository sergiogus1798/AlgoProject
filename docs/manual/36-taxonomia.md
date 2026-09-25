# 36. Taxonomía y paletas de bloques — qué bloque pega con qué tipo de estrategia

### Qué pregunta responde

SQX conoce 1.020 bloques. Con tantos, el builder puede combinar un filtro de reversión a la media
con un disparador de ruptura y sacar algo que parece rentable y no significa nada. Este módulo
prepara el fichero donde se decide, bloque a bloque, **con qué familia de estrategia pega cada uno**.

No etiqueta nada: monta la tabla vacía, con todo lo que se puede saber leyendo la instalación, para
que la etiqueta la ponga alguien que sepa —tú o un agente— y no se pierda en un chat.

### Cuándo lo usas, y cuándo no

Se corre **cuando cambia el vocabulario de la instalación**: después de autorar bloques propios con
`/strategy-template`, después de importar un paquete de bloques, o cuando llega una instalación
nueva. Fuera de eso no hay motivo: el fichero ya está y las etiquetas no las pone este comando.

No sirve para saber si un bloque es bueno, ni si funciona en tu mercado. Solo dice qué bloques
existen, qué papel puede jugar cada uno y qué grupos aleatorios lo agrupan.

⚠️ **Y no vale para estrechar un hueco atado a un grupo.** Las etiquetas alimentan una paleta, y una
paleta solo alcanza los huecos **libres** de una plantilla. Un `RandomCondition` atado a un grupo
sortea ese grupo y se salta los interruptores — medido el 2026-09-24, `knowhow/authoring/builder-block-switches.md`.
Para esos, la palanca es el grupo.

### Antes de empezar

Nada. Lee tres ficheros XML de la instalación y una tarea Build del donante congelado. **No arranca
SQX, no escribe en ninguna instalación y se puede correr con la GUI del maestro abierta.**

Lo único que tiene que existir es el donante, que ya está:
`~/Desktop/AlgoData/projectsBackup/XAUUSD_base_2026-09-21/project.cfx`.

### Cómo se ejecuta

```bash
python3 -m sqx.blocks.taxonomy                       # refresca desde el maestro
python3 -m sqx.blocks.taxonomy --role custodian      # leer otra instalación
```

| flag | obligatorio | qué hace |
|---|---|---|
| `--role` | no | `master`, `conductor` o `custodian`. Por defecto **el maestro**, que es el que lleva el vocabulario de referencia |
| `--donor` | no | el `project.cfx` cuya tarea Build lista los papeles. Por defecto el donante congelado de XAUUSD. **Solo lectura** |
| `--out` | no | dónde escribir. Por defecto `sqx/blocks/taxonomy.yaml` |

Tarda menos de dos segundos.

### Qué produce

Un único fichero, **en el repositorio** porque es configuración a mano y tiene que estar versionada:

```
sqx/blocks/taxonomy.yaml        (~148 KB, 767 bloques en 83 categorías)
```

**Lo sobrescribe entero en cada corrida**, pero conservando lo único que no es derivado: los
`archetypes` que ya tuvieran valor. Todo lo demás —los papeles, los grupos, la forma escrita— se
vuelve a leer de la instalación y se pisa.

### Cómo se lee el resultado

La salida real de hoy:

```
/home/sergioguslw/Desktop/AlgoProject/sqx/blocks/taxonomy.yaml: 767 bloques en 83 categorías, leídos de SQX
  papeles   señal 588 · indicador 171 · nivel 85
  etiquetas 0 puestas, 767 por poner
  nuevos (767): ADX, ADXChangesDown, ADXChangesUp, ADXCrossDown, ADXCrossUp, ADXFalling, ADXHigher, ADXLower …
```

Tres cosas que leer ahí:

- **767 de 1.020.** Los otros 253 existen y el builder no los ve: las acciones, las funciones
  matemáticas, los 158 `talib_*`. Etiquetarlos sería etiquetar algo que ninguna paleta puede tocar.
- **Los tres papeles.** Un mismo bloque puede jugar dos: el `ATR` es indicador (un valor que
  comparar) y nivel (el precio de una orden stop). Son dos interruptores distintos sobre él.
- **`etiquetas 0 puestas, 767 por poner`.** Ese es el trabajo que falta. Mientras esté en 0, ninguna
  paleta se puede construir.

Una fila del fichero:

```yaml
BookTriggers_user:
  CBlock_BBBreakoutUp:
    roles: [signal]
    origin: own
    form: BBBreakoutUp
    groups: [BookTriggers]
    archetypes: {}
```

`archetypes` es lo que hay que rellenar: **un peso por familia**, `breakout`, `mean_reversion` y
`trend`. `0` excluye el bloque de esa familia, `1` es neutro, `2` y `3` lo prefieren. Vacío = sin
etiquetar, y un bloque sin etiquetar no entra en ninguna paleta.

`groups` es el aviso: ese bloque está en `BookTriggers`, así que una plantilla que ate un hueco a
`BookTriggers` lo puede sacar **aunque la paleta lo apague**.

### Un ejemplo completo

Etiquetar los bloques de ruptura propios y comprobar que sobreviven a un refresco.

```bash
$ python3 -m sqx.blocks.taxonomy
sqx/blocks/taxonomy.yaml: 767 bloques en 83 categorías, leídos de SQX
  papeles   señal 588 · indicador 171 · nivel 85
  etiquetas 0 puestas, 767 por poner
```

Se edita el fichero a mano y se pone una etiqueta:

```yaml
  CBlock_BBBreakoutUp:
    roles: [signal]
    origin: own
    form: BBBreakoutUp
    groups: [BookTriggers]
    archetypes: {breakout: 3, mean_reversion: 0, trend: 1}
```

Se vuelve a correr, por ejemplo después de autorar un bloque nuevo:

```bash
$ python3 -m sqx.blocks.taxonomy
sqx/blocks/taxonomy.yaml: 768 bloques en 83 categorías, leídos de SQX
  papeles   señal 589 · indicador 171 · nivel 85
  etiquetas 1 puestas, 767 por poner
  nuevos (1): CBlock_DonchianBreakUp
```

La etiqueta sigue ahí y el bloque nuevo aparece vacío, esperando la suya.

### Qué NO te dice

- **No dice si la etiqueta es correcta.** Es una opinión escrita en un fichero. La evidencia de que
  un bloque pega con una familia sale de las corridas (`runs.csv`), no de aquí.
- **No construye ninguna paleta ni toca ningún proyecto.** Escribe un YAML y nada más.
- **No alcanza los huecos atados a un grupo.** Repetido porque es el error que va a costar caro: una
  paleta perfecta no cambia nada en una plantilla cuyos huecos apuntan a grupos.
- **No es el catálogo completo del vocabulario.** Para eso, `sqx/inspect/vocabulary.py` y la página
  `21-vocabulario.md`.

---

## La librería de paletas

La taxonomía dice **qué es** cada bloque. Una **paleta** dice **qué entra en una construcción
concreta**, y de esas hay muchas: tres por defecto que vienen con el repositorio, una por familia,
y todas las que clones o crees encima.

```
sqx/blocks/palettes/ruptura_base.yaml        ★ por defecto, familia Ruptura
sqx/blocks/palettes/reversion_base.yaml      ★ por defecto, familia Reversión a la media
sqx/blocks/palettes/tendencia_base.yaml      ★ por defecto, familia Tendencia
sqx/blocks/palettes/<lo_que_tú_guardes>.yaml
```

Una paleta son cuatro decisiones y nada más:

| campo | qué decide |
|---|---|
| `family` | de qué columna de la taxonomía hereda los pesos: `breakout`, `mean_reversion` o `trend` |
| `unlabelled` | qué pasa con un bloque sin etiquetar — `neutral` entra a peso 1, `off` lo deja fuera |
| `overrides` | los pesos puestos a mano, que ganan sobre la taxonomía. `0` apaga el bloque |
| `label` · `note` · `origin` · `based_on` | cómo se llama, para qué es, y de dónde salió |

**`unlabelled: off` más una lista de `overrides` hace que la paleta SEA esa lista**: no entra nada
más. Es la forma de tener una paleta curada —«para ruptura yo usaría estos treinta bloques»— **sin
esperar a que la taxonomía esté etiquetada**. Con `neutral` la paleta hereda lo que diga la
taxonomía y solo corrige lo que tú le digas.

### El comando

```bash
python3 -m sqx.blocks.palette                    # la librería entera
python3 -m sqx.blocks.palette ruptura_base       # una paleta: qué deja pasar
python3 -m sqx.blocks.palette ruptura_base --json  # lo mismo, para un agente
```

| flag | obligatorio | qué hace |
|---|---|---|
| `NAME` | no | el slug de una paleta. Sin él, lista la librería |
| `--json` | no | emite la paleta y su resolución bloque a bloque, para que un agente la consuma |

Salida real de hoy, con las tres por defecto y ninguna curada todavía:

```
ruptura_base      Ruptura                default  condiciones   64  ⚠️ FUERA DE 90-170  Ruptura — base
reversion_base    Reversión a la media   default  condiciones   83  ⚠️ FUERA DE 90-170  Reversión a la media — base
tendencia_base    Tendencia              default  condiciones   98  ok                  Tendencia — base
```

El número que importa es **condiciones**, y tiene banda: el dueño pide **entre 90 y 170 por build**
(2026-09-24). Por debajo el builder no tiene de dónde combinar; por encima vuelve el sobreajuste que
esto viene a evitar. El comando marca `⚠️ FUERA DE 90-170` cuando una paleta se sale, y la ventana
pinta el recuento en rojo. No es una orientación: es el criterio de aceptación.

### Clonar, editar, guardar

Se hace en la ventana (`docs/manual/35-app-plantillas.md`, zona **Paletas**): abres una, pulsas
**Clonar**, le das nombre, y la copia es tuya para editar. Las tres por defecto **no se pueden
borrar** desde la ventana — son de las que parte todo lo demás.

### Si algo falla

- **`KeyError: 'custodian'`** — esa instalación no está en `config/machine.yaml`. Es válido tener
  solo maestro y conductor.
- **`FileNotFoundError` del donante** — falta
  `AlgoData/projectsBackup/XAUUSD_base_2026-09-21/project.cfx`. Es el donante congelado del que
  clona todo; si no está, hay que recuperarlo antes de seguir.
- **`StopIteration` en `builder_roles`** — el `.cfx` que le has pasado con `--donor` no tiene tarea
  Build, y los papeles solo viven ahí.
- **`'<slug>' already exists`** al clonar — ya hay una paleta con ese nombre de fichero. Dale otro
  nombre; no se sobrescribe una paleta por accidente.
- **`FileNotFoundError` de un `.yaml` de paleta** — le has pedido una paleta que no está en la
  librería. `python3 -m sqx.blocks.palette` sin argumentos dice cuáles hay.
