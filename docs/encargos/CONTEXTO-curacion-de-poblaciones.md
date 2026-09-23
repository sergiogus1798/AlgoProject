# Contexto: cómo la aplicación mueve, filtra y borra estrategias en SQX

No es un encargo: es el estado del terreno para quien diseñe las skills que van del prompt del dueño
a las estrategias generadas y filtradas. Revisión del 2026-09-23. **Lee también** `CLAUDE.md` (las
nueve reglas duras), `knowhow/02-databanks.md` y `.claude/skills/curate/SKILL.md`.

## 1 · El objetivo del dueño, en sus términos

Una aplicación con UI de quant que engloba SQX y Python, con un chat con Claude. El dueño escribe
«quiero testear una idea: el close cruza hacia arriba la banda superior de Keltner y entra long…» y
a partir de ahí, sin tocar nada más:

1. se crean los custom blocks que falten y con ellos la template;
2. se crea un workflow que intercala tareas de SQX (generar, retestear, MC, WFM…) con tests en
   Python;
3. desde la UI se manejan **los filtros de SQX y los de Python** con la misma facilidad;
4. **lo crítico:** si SQX genera 10k y el corte de Python lo pasan 2k, las 8k salen de SQX
   automáticamente, **sin quedarse en la RAM del install**, y las 2k quedan listas como entrada de
   la siguiente tarea de SQX;
5. el dueño quiere controlar las estrategias desde su UI de forma tan sencilla como desde la de SQX;
6. todo secuencial. Tareas en paralelo es futuro, no ahora.

## 2 · Lo que ya existe y hay que reutilizar, no reinventar

| pieza | qué resuelve | dónde |
|---|---|---|
| contrato `verdict.csv` (`strategy`, `verdict`=`DESCARTAR`) | cómo Python le dice a SQX qué sobra | `.claude/skills/curate/SKILL.md` |
| `sqx/curate/apply_verdict.py` | aplica el veredicto moviendo ficheros con el install parado, snapshot fuera del install, recuento de vuelta | `sqx/curate/` |
| `pipeline/` (recipe + ledger + cleanup) | la cola de trabajos del futuro daemon; etapas como datos, progreso `PROGRESS n status` en stdout | `pipeline/README.md` |
| tres installs: maestro M (intocable), conductor W1/5060, custodio W2/5070 | dónde se autora, dónde se construye | `knowhow/03-driving-sqx.md` |
| cadena bloque → grupo → template → proyecto probada headless | el punto 1 del objetivo ya funciona sin GUI | `OPEN.md` issue 25 |
| `sqx/inspect/index_sqx.py` | indexar 17k `.sqx` en 1,5 s: la base de una tabla de estrategias propia | `knowhow/01-file-formats.md` |

## 3 · El mecanismo de curación: una sola ruta funciona

**SQX trata la memoria como verdad y cada sync borra del disco lo que no está en memoria.** Medido
el 2026-09-23 sobre el custodio con un databank de 30 estrategias:

- `-databank action=delete|save|load strategies=…` **no llega**: el servidor HTTP parte el comando
  por espacios y todo nombre de estrategia lleva uno (`Strategy 11.3.25`). `%20`, `+`, `%2520` y
  comillas fallan igual, y el verbo responde `Reports removed.` sin mover el recuento.
- Un `sqcli` de un solo disparo no carga los registros: `action=save` escribió 0 de 30 respondiendo
  `Reports saved.`
- ⚠️ `action=move` con selector que no llega **mueve el databank entero**, sin error.
- **Lo que funciona:** parar el install, mover los `.sqx` fuera del directorio del databank,
  arrancar. SQX resincroniza *desde* ficheros y el directorio curado se convierte en memoria.
  Verificado 30 → 28 → 27 → 24 en cuatro rondas.

Consecuencia de diseño: el paso «Python decide → SQX obedece» es un ciclo **parar → snapshot →
mover ficheros → arrancar → recontar**, y el recuento que SQX devuelve tras arrancar es la única
verificación válida. `apply_verdict.py` ya hace exactamente eso.

## 4 · Lo que hoy falla o falta para el objetivo del dueño

1. **RAM y disco de las rechazadas.** Resuelto el 2026-09-23 por decisión del dueño: las
   rechazadas **se borran** tras anotar qué había (nombre, identidad, tamaño) y sus métricas, en
   `AlgoData/reports/<proyecto>/<databank>/<fecha>/curate/`. Ni carpeta de rechazadas ni databank
   `Rejected`: un `.sqx` pesa ~5 MB y SQX carga todos los databanks de un proyecto al arrancar. Lo
   que queda de la población completa son sus métricas; los trades de una rechazada se pierden.
2. **Identidad.** El contrato va por nombre externo. El nombre no es identidad: SQX renombra en
   colisión, y `copy`/`load` acumulan ficheros byte-idénticos con el mismo nombre sin ninguna
   comprobación. La identidad fiable es **SHA-256 del `strategy_Portfolio.xml` interno** (nunca del
   `.sqx`, que lleva timestamps). El `verdict.csv` debe llevar las dos columnas y el mover debe
   comprobar el hash del fichero que mueve.
3. **La idea del prompt puede no llegar a las estrategias.** `OPEN.md` issue 9: 0 de 642 estrategias
   generadas llevan el bloque fijo de su template. La skill `template-run` ya comprueba que las
   estrategias carguen el bloque; en el workflow de la aplicación esa comprobación es una **puerta
   obligatoria** justo después de la generación, no un paso opcional.
4. **Los filtros de SQX son XML de tarea.** Condiciones de aceptación (`use="true|false"` en 30
   condiciones), `DeleteFailedStrategies`, `<Databanks retestSelected="false">`, símbolo del
   `<Chart>`. Se cambian **copiando una tarea que ya corrió** y cargándola con
   `-project action=loadconfig` en el worker, con `action=remove` antes porque `loadconfig` nunca
   sobreescribe. Trampas medidas y silenciosas: `startOnlyTask` no hace nada; un segundo `start`
   necesita `stop`; un símbolo inexistente en un `<Chart>` mata la tarea aunque su cross-check esté
   apagado. `knowhow/03-driving-sqx.md` §trampas.
5. **Un databank de build está en `Auto-sync never` en el donante XAUUSD**: tras generar, su
   directorio está vacío y nada externo lo lee. Hay que dejarlo en `Auto-sync every 1 hour` o
   forzar `-databank action=synctofiles` antes de parar. Sin eso Python filtra sobre cero ficheros.
6. **Progreso en vivo.** El websocket de la GUI (`/websocket/updates`) responde
   `Remote access disabled`; hay que activarlo en ajustes de SQX. Mientras, el progreso se saca del
   log `ProgressEngine` y del nombre del hilo (`… 20 % OOS WFO 4`), a cola, nunca leyendo el log
   entero (55 MB/día).
7. **Seguridad.** La API de comandos escucha en `0.0.0.0` sin credenciales. La aplicación debe hablar
   solo con `127.0.0.1` y el cortafuegos cerrar 5050–5071 y 8080–8082.

## 5 · Dónde está el coste, para que la aplicación sea rápida

| paso | coste medido |
|---|---|
| mover 8k ficheros con el install parado | segundos |
| parar y arrancar un install | minutos, más la carga del databank |
| sync de un databank grande | 826 s para 1.2k estrategias (WFM) |
| trades de N estrategias vía `orderstocsv` | uno por estrategia: lo dominante a 10k |

Reglas que salen de ahí:

- **Filtrar en dos etapas en Python.** Primero con `-databank action=export file=…csv view=…`
  (135 métricas por estrategia, sin tocar ficheros, install vivo). Solo a las supervivientes se les
  piden trades. Cada test caro corre sobre 2k, no sobre 10k.
- **Agrupar los tests de Python entre dos tareas de SQX** para pagar un solo parar/arrancar.
- **Databanks pequeños.** Promover supervivientes y sacar rechazadas del install evita el sync de
  826 s y la RAM que preocupa al dueño. Tope de estrategias del builder como primer freno.
- **Serialidad estricta por install.** Mientras el custodio corre una tarea, ningún comando. El
  ledger del pipeline ya es secuencial; no hay que diseñar concurrencia ahora.

## 6 · Controlar las estrategias desde la UI propia

Lo que la GUI de SQX ofrece por estrategia y su equivalente sin GUI:

| en la GUI de SQX | sin GUI | estado |
|---|---|---|
| tabla de métricas de un databank | `-databank action=export file=csv view=` (install vivo) | 🔬 funciona |
| ver la lógica de una estrategia | leer `strategy_Portfolio.xml` del `.sqx`, XML plano | 🔬 funciona; `strategies/` ya lo traduce |
| trades y curva de equity | `-tools action=orderstocsv` por estrategia | 🔬 funciona, caro en masa |
| seleccionar y borrar / mover a otro databank | mover ficheros con el install parado | 🔬 la única ruta |
| copiar un databank entero a otro proyecto | `-databank action=copy\|move` sin selector | 🔬 funciona; duplica sin comprobar |
| crear databank | `-databank action=create` o `mkdir` + arranque | 🔬 funciona |
| retestear la selección | proyecto de una tarea Retest, `action=stop` + `action=start` | 🔬 funciona; `startOnlyTask` no |

Es decir: la tabla de la aplicación se alimenta del CSV de exportación más el índice de `.sqx`, y
cada acción de «borrar/mover» de la UI se traduce en un ciclo de curación. No en llamadas por
estrategia al CLI, que no existen.

## 7 · Medidas pendientes antes de dar esto por cerrado

- Si al arrancar SQX carga **todos** los databanks del proyecto o solo los que toca una tarea. Si
  carga solo los que toca, un databank `Rejected` dentro del proyecto no cuesta RAM y el punto 4.1
  se relaja. Se ve en el log: `Databank '<P>/<B>' loaded - N strategies`.
- Coste real de parar y arrancar el custodio con 10k estrategias en el databank de entrada.
- Si `Auto-sync every 1 hour` en el databank de build escribe a disco al terminar la tarea o solo
  al tick horario. Determina si hace falta `synctofiles` antes de parar.

---

## 8 · Correcciones y medidas del 2026-09-23 (tarde)

Tres cosas de arriba cambian. Se marcan, no se borran.

### 8.1 · El punto 4.3 está bien de conclusión y mal de motivo

«0 de 642 llevan el bloque fijo» **no significa que una template no llegue a las estrategias.**
Significa que **`<StrategyType type="simple">` ignora la template**. Medido el 2026-09-22: en un
proyecto cuya tarea Build declara `type="template"`, **30 de 30** estrategias generadas llevaban el
bloque fijo, cada una con un compañero aleatorio distinto. Los nueve proyectos del maestro de la
issue 9 declaran `type="simple"`. La diferencia es ese atributo y nada más.

Consecuencia práctica, y es una mejora del plan: la puerta obligatoria **no tiene que esperar a la
generación**. El atributo se lee del XML de la tarea antes de construir, gratis, y la comprobación
cara —abrir las estrategias y buscar el bloque— queda como prueba posterior, no como detector.
`sqx/projects/configure.py` lo hace ya en cada configuración:

```
⚠️ TEMPLATE IGNORADA — Build-Task3.xml: names a templateFile but declares type="simple"
```

Verificado contra los proyectos reales: marca `AUDJPY` y `GBPJPY_H1`, y deja pasar el donante de
XAUUSD, que sí declara `type="template"`.

⚠️ Y una trampa que la issue 9 no cubre: `template_check.py` **era ciego a los custom blocks** hasta
el 2026-09-22. Su lista de categorías no incluía `Custom blocks`, así que firmaba por
`MarketPositionIsLong` —que lleva toda estrategia larga— y daba un `25/25 ok` sobre el bloque
equivocado. Como toda template que salga de la cadena nueva fija un custom block, la puerta habría
aprobado en falso siempre. Arreglado; el número publicado de la issue 9 no se mueve, porque las
nueve templates del maestro fijan bloques nativos.

### 8.2 · El punto 4.1 está confirmado: hay que sacarlas del install

Medido en el log del custodio: un sync carga **todos los databanks del proyecto**, no solo el que
toca la tarea — las cinco del proyecto de humo salen cada vez, con sus tiempos individuales
(`Databank 'Retester/RetestOut' loaded - 962 strategies in 4489ms`). Así que un `Rejected` dentro
del proyecto sí cuesta RAM. **La medida pendiente de §7 queda contestada.**

`apply_verdict.py` ya lo aplica: **sin `--into`, las rechazadas se borran tras el registro**.
`--into <databank>` sigue disponible para cuando se quiera dejarlas dentro a propósito.

### 8.3 · El punto 4.5 tiene una guarda

Un databank en `Auto-sync never` deja el directorio vacío, y el ciclo de curación es de ficheros, así
que Python filtraría sobre cero. `apply_verdict.py` **se niega** cuando el directorio no tiene
ningún `.sqx` y explica las dos salidas: `Auto-sync every 1 hour` en el `project.cfx`, o
`-databank action=synctofiles` antes de parar la instalación.

📓 Y una corrección a la lista de verbos: **`synctofiles` existe** y fuerza memoria → disco. La lista
corta de `knowhow/03-driving-sqx.md` tenía seis verbos de menos; la referencia completa es
`internal/web/SQUANT/help.txt`, legible sin arrancar SQX.
