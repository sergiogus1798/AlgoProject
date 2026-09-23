# 22. Plantillas — de una idea a una plantilla que construye

### Qué pregunta responde

Tienes una idea de entrada —"que el cierre cruce por encima de la banda superior de Keltner"— y
quieres una plantilla de AlgoWizard que la construya. Estas tres herramientas hacen el camino
entero sin abrir la GUI: autoran el bloque que falte, lo meten en la instalación, montan la
plantilla y anotan lo que se ha probado y dónde.

### Cuándo lo usas, y cuándo no

Cuando la lógica esté decidida: qué condición exactamente, en qué dirección, qué se fija y qué se
deja aleatorio. Eso lo decide el brief, y el brief lo aprueba el dueño.

No sirve para decidir si la idea es buena, ni sustituye a una construcción real: lo que produce es
una plantilla que SQX acepta. Si la estrategia gana dinero es otra pregunta y otras herramientas.

### Antes de empezar

1. **La instalación de destino tiene que estar parada.** `customBlocks.xml` es el almacén de
   verdad, y una GUI abierta lo reescribe al salir: tu escritura se pierde en silencio.
   `sqx/blocks/install.py` se niega a escribir si el puerto de esa instalación contesta.
2. **Regla dura 5**: `python3 -m core.assets <SÍMBOLO>` antes de tocar cualquier plantilla o tarea.
   Si sale distinto de cero, se para y se pregunta.
3. **El bloque tiene que estar en las dos instalaciones** si autoras en el conductor y construyes
   en el custodio. `python3 -m sqx.inspect.vocabulary --diff custodian` te lo dice en un segundo.

### Cómo se ejecuta

```bash
# 1. meter los bloques autorados en una instalación parada
python3 -m sqx.blocks.install ~/Desktop/AlgoData/templates/library/<nombre>/deps/blocks.xml --role conductor
python3 -m sqx.blocks.install ~/Desktop/AlgoData/templates/library/<nombre>/deps/blocks.xml --role custodian

# 2. montar la plantilla fijando un bloque en el esqueleto
python3 -m sqx.templates.build <nombre> <deps/blocks.xml> <CBlock_clave> <salida.sqx> [--shape market_long] [--install custodian]

# 3. anotar lo que existe y lo que se ha probado
python3 -m sqx.templates.registry --set name=<nombre> --set archetype=breakout ...
python3 -m sqx.templates.registry --run --set template=<nombre> --set symbol=XAUUSD --set timeframe=H1 ...
```

| flag | obligatorio | qué hace |
|---|---|---|
| `install.py --role` | no | `conductor` (por defecto) o `custodian`. El maestro está prohibido |
| `build.py --shape` | no | esqueleto a transplantar; por defecto `market_long` |
| `build.py --install ROLE` | no | además copia el `.sqx` a `StrategyTemplates/` de esa instalación |
| `build.py --set` | no | subcarpeta usada al instalar; por defecto `authored` |
| `registry.py --run` | no | escribe en `runs.csv` en vez de en `registry.csv` |
| `registry.py --set COL=VALOR` | sí | un valor por columna, repetido tantas veces como columnas |

Los tres son instantáneos. Ninguno arranca SQX; `install.py` exige que esté parado.

### Qué produce

```
<instalación>/user/settings/customBlocks.xml           modificado, con copia fechada al lado
<instalación>/user/settings/StrategyTemplates/<set>/   la plantilla, si usas --install
AlgoData/templates/library/<nombre>/template.sqx       la plantilla
AlgoData/templates/registry.csv                        una fila por plantilla
AlgoData/templates/runs.csv                            una fila por plantilla × símbolo × timeframe
```

`install.py` **reemplaza** un bloque cuya clave ya exista en vez de añadirlo dos veces: SQX lee la
primera coincidencia y un duplicado no se ve hasta que una construcción usa el equivocado. Antes de
escribir deja una copia fechada en `customBlocks-backups/`, igual que hace la GUI.

### Cómo se lee el resultado

```
$ python3 -m sqx.blocks.install .../deps/blocks.xml --role conductor
SQX_w1: added ['CBlock_CloseCrossesAboveKCUpper', 'CBlock_CloseCrossesBelowKCLower'], replaced []
  store now holds 173 blocks; previous copy kept at .../customBlocks-backups/1790090019825.xml

$ python3 -m sqx.inspect.vocabulary --diff custodian
SQX_w2 lacks, against SQX_w1:
  custom blocks (2): CBlock_CloseCrossesAboveKCUpper, CBlock_CloseCrossesBelowKCLower
```

Esa segunda salida es la que hay que mirar siempre: el bloque estaba en el conductor y **no** en el
custodio, que es donde se construye. Una plantilla que referencia un bloque ausente no da error —
se queda coja y desaparece del builder.

```
$ python3 -m sqx.templates.build keltnerUpperCrossUp deps/blocks.xml CBlock_CloseCrossesAboveKCUpper template.sqx
.../template.sqx  (5267 bytes, shape market_long, fixed CBlock_CloseCrossesAboveKCUpper)
```

`build.py` aborta si el bloque no aterriza en la señal, si queda más de un hueco aleatorio, o si el
XML resultante no parsea. Los tres fallaron durante el desarrollo, así que los tres se comprueban.

### Configurar el proyecto desde `assets/`

Un proyecto se clona de un donante, y **el donante lleva los ajustes vivos del maestro**, que no son
la política declarada. En XAUUSD el donante cobra `SizeBased 8` donde `assets/` dice
`PercentageBased 0.00174`, y cero slippage donde `assets/` dice cinco puntos. Si nadie lo pisa, la
construcción corre a un coste que no ha elegido nadie, y no salta ningún error.

```bash
python3 -m sqx.projects.configure <ruta/project.cfx> XAUUSD
```

Sin `--segment`, **cada tarea toma el suyo de su tipo**: `Build` → `build`, todo lo demás → `oos1`,
según `assets/_policy.yaml`. Eso es lo que hace útil declarar `spread_is` y `spread_oos` por
separado; forzar un solo tramo en toda la cadena valora los retests con el spread de construcción.

```
cfgtest.cfx  XAUUSD
  build: spread 10.0, slippage 5, PercentageBased 0.00174, swap percent -7/-7,
         ventana 1199145600000 a 1514764800000
    1 tarea(s): Build-Task3.xml
  oos1:  spread 10.0, slippage 5, PercentageBased 0.00174, swap percent -7/-7,
         ventana 1514764800000 a 1672531200000
    14 tarea(s): Retest-Task1.xml, ... Retest-Task14.xml
  ⚠️ PROVISIONAL: spread_is, spread_oos, commission, slippage, swap_long, swap_short
  ⚠️ rangos MC Retest sin decidir: spread, slippage
```

Se niega ante tres cosas: `oos2` (reservado al WFC y la WFM — mirarlo lo gasta), un coste con
`use: null`, y un `.cfx` que tenga abierto una instalación viva, porque lo reescribe al salir.

### Un ejemplo completo

La cadena entera del `keltnerUpperCrossUp`, tal como se corrió el 2026-09-22:

```bash
python3 -m core.assets XAUUSD                                    # regla dura 5 → exit 0
python3 -m sqx.blocks.install .../deps/blocks.xml --role conductor
python3 -m sqx.blocks.install .../deps/blocks.xml --role custodian
python3 -m sqx.templates.build keltnerUpperCrossUp .../deps/blocks.xml \
        CBlock_CloseCrossesAboveKCUpper .../template.sqx
# proyecto de una sola tarea sobre el donante, con la plantilla apuntada
bin/sqx-worker.sh --role custodian start
python3 -c "from core import worker; worker.call('-project action=start name=smoke_keltnerUpperCrossUp','custodian')"
```

Resultado, leído del `-project action=status`:

```
Strategies generated                         13639
Rejected                                   99.48 %
Running time so far                          29 s.
In databank                                     30
```

Y la comprobación que decide si la plantilla sirve de algo — que las estrategias construidas lleven
**de verdad** el bloque fijo:

```
estrategias: 30   llevan el bloque fijo: 30
companeros que eligio el builder: CSSAMarketRegimeAboveLevel ×15, VWAP ×5,
                                  BollingerBands ×5, IsFalling ×4, HighD ×3, UlcerIndex ×2, ...
```

30 de 30 con el Keltner fijo, cada una con un compañero aleatorio distinto. Eso es exactamente lo
que se pidió: una condición fija y una libre.

### Qué NO te dice

- **No dice si la estrategia es rentable.** Una construcción de humo prueba la cadena, no la idea.
  30 estrategias con tope de 30 no son una muestra de nada.
- **No prueba que el bloque calcule lo que su nombre dice.** Que SQX lo acepte y construya con él no
  significa que el cruce esté bien definido. Eso solo lo dice leer sus trades.
- **No valida los costes.** El spread, la comisión y el point value de XAUUSD son a día de hoy los
  defaults de SQX, provisionales, no cifras acordadas con el bróker.
- **`registry.csv` no se lee solo.** Anota lo que le digas; si no anotas una corrida, la respuesta a
  "¿ya lo probé?" será que no.

### Si algo falla

`SQX_w1 is running on port 5060` — la instalación está levantada y reescribiría tu cambio al salir.
Párala: `bin/sqx-worker.sh --role conductor stop`.

`CBlock_X did not land in the signal` — la clave no está en el XML de bloques que le pasaste, o el
esqueleto no tiene dos huecos aleatorios.

**La construcción termina y el databank está vacío en disco.** No es un fallo: el databank está en
`Auto-sync never` y SQX guarda en memoria. Se arregla parando la instalación, poniendo ese databank
en `Auto-sync every 1 hour` dentro del `project.cfx` —nunca con una instancia abierta, regla dura
4— y reconstruyendo. Está contado en `knowhow/03-driving-sqx.md`.

**El proyecto arranca y no testea nada.** Estás usando `startOnlyTask`, que informa de éxito y no
hace nada. Usa `action=start`, y un `action=stop` antes de cada segundo arranque.
