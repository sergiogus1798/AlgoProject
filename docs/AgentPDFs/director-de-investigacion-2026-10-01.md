# El director de investigación: del mercado a la plantilla, con criterio propio

*2026-10-01. Dossier de diseño, nada construido todavía. Bases: el inventario de los pasos 1-6 hecho
hoy sobre el repositorio, el consumo de tokens medido en las transcripciones de este proyecto (349
sesiones, 243 horas activas), el dossier `ideas-de-internet-y-libros-2026-09-27` (§4.1, §4.3 y §4.9) y
los encargos 6, 26, 28, 32 y 40, que este diseño reutiliza en vez de repetir.*

## 0. Lo que pediste y lo que ya decidiste

Que un agente diga solo: «el XAUUSD en H4 es tendencial, le viene bien una plantilla con esta idea
nueva y estos building blocks». Tus respuestas de hoy fijan el marco:

| decisión | tu respuesta |
|---|---|
| qué recibe de entrada | **nada: él decide en qué activo y marco temporal investigar** |
| cuándo corre | **con un botón de la ventana**, nunca solo |
| familias | **las siete** de la cobertura: ruptura, tendencia, reversión, momentum, volatilidad, patrón y sesión |
| activos | **los 19**, XAGUSD y los petróleos incluidos, también para proponer y lanzar; sus costes los cierras tú con alta prioridad |
| marcos | **de M15 a H4**: M15, M30, H1 y H4 |
| reparto | **concentrado**: tres ideas para la mejor celda, no una idea en tres celdas |
| celdas que no pasan los filtros | **no entran**: el director no propone sobre ellas, aunque no haya nada probado ahí |
| quién elige | **las tres van a SQX**, una detrás de otra; tú sólo vetas antes de lanzar |
| bloques nuevos | **sí**: una idea puede necesitar un bloque custom que aún no existe |
| cantera de ideas | **todo**: los datos del perfil, el catálogo de 390 ideas de tus libros y lo que se le ocurra |
| por dónde se empieza | **por este diseño**, antes de tocar código |

## 1. Lo que hay hoy y lo que falta

| pieza | hoy | lo que falta |
|---|---|---|
| carácter del mercado | nada en el código. La única caracterización es la que el `ideaExpert` hizo a mano en `AlgoData/ideas/XAUUSD/2026-10-01-impulso-h4.md` | un estudio que lo mida para todos los activos, igual siempre |
| ideas | `ideaExpert`: tres ideas por activo y marco, medidas sólo en `build` | que alguien le diga **dónde** mirar y **qué familia** buscar |
| plantillas | `templateArchitect` + librería de 6 plantillas (3 de ruptura, 3 de tendencia, 0 del resto) | nada: funciona |
| building blocks | `buildingBlocksExpert` + 4 paletas | **sólo 15 de 767 bloques tienen etiqueta de familia** (encargo 6, sin ejecutar) |
| control de lo probado | `templates/runs.csv`, 9 filas, casi sin veredicto | cruzar plantilla × activo × marco con cuántas sobrevivieron y dónde murieron |
| la ventana | cobertura, paletas, y un «chat» que es una lista fija de preguntas | un panel que enseñe el diagnóstico y la propuesta |
| quién lo encadena | tú, a mano, con `/workflow-start` | el director |

## 2. El diseño en una figura

```
   [1] PERFIL DE MERCADO          [2] MEMORIA                 [3] TAXONOMÍA
   19 activos × 4 marcos          qué se probó, dónde         767 bloques con
   sólo `build`, contra el azar   murió, qué sobrevivió       su familia
   (Python, 0 tokens)             (Python, 0 tokens)          (una vez, encargo 6)
            \                          |                          /
             \                         v                         /
              +------------>  [T] EL TABLERO  <-----------------+
                    una página: las celdas activo × marco × familia
                    ordenadas por señal, hueco de cobertura y rendimiento pasado
                                       |
                                       v
                          [4] EL DIRECTOR (agente)
                    elige la mejor celda, pide tres ideas para ella al
                    `ideaExpert`, y prepara la paleta de bloques de cada una
                                       |
                                       v
                  PROPUESTA en la ventana  -->  TÚ VETAS LA QUE NO QUIERAS
                                       |
                                       v
        por cada idea, en fila en el custodio:
              `templateArchitect` -> proyecto -> `buildingBlocksExpert` -> autopilot
                                       |
                                       v
                     [5] el veredicto vuelve a la MEMORIA y mueve el tablero
```

La regla que ordena todo: **lo que se puede calcular lo calcula Python; el agente sólo lee una
página y razona sobre ella.** El diagnóstico «tendencial o de ruptura» es un número con su
significación, no la opinión de un modelo. Es reproducible, se puede auditar y no cuesta tokens.

## 3. Pieza 1: el perfil de mercado

**Qué responde.** Para cada activo, marco temporal y dirección (largo y corto por separado, regla
dura 13): ¿qué familia de comportamiento hay, con qué fuerza, y da para pagar los costes?

**Sobre qué datos.** Los 19 activos de `assets/`, barras M1 de `AlgoData/bars/` remuestreadas a M15,
M30, H1 y H4. **Sólo el tramo `build` de cada activo**: `oos1` y `oos2` no se leen jamás,
igual que hace el `ideaExpert`.

**Qué mide.** Las siete familias de la cobertura, cada una con sus medidas, y un bloque de contexto.

| familia | medidas | cómo se lee |
|---|---|---|
| **tendencia** | variance ratio de Lo-MacKinlay a varios horizontes; exponente de Hurst; rejilla retrospectiva × permanencia (¿el retorno de las L barras pasadas predice el de las H siguientes?); mapa de Fitschen (comprar a +1 desviación sobre la media: ¿sigue o vuelve?) | VR > 1 y correlación positiva: la dirección persiste |
| **ruptura** | retorno tras cerrar fuera del canal de N barras; tasa de rupturas falsas por año; tamaño característico de la ruptura | la salida del canal continúa más de lo que continuaría por azar |
| **reversión** | retorno tras un extremo (distancia a la media en ATR); vida media de la vuelta; test de estacionariedad | VR < 1 y el extremo se deshace |
| **momentum** | persistencia tras una barra mayor que la media; curva de continuación (¿a partir de cuántos ATR un movimiento sigue?) | un movimiento fuerte sigue, sin nivel ni media de por medio |
| **volatilidad** | autocorrelación del rango; rango de la barra siguiente tras una barra estrecha (NR-k) frente a tras una ancha | la compresión precede a la expansión, y la expansión tiene dirección |
| **patrón** | probabilidad de barra alcista tras cada estado de barra (interior, envolvente, k cierres seguidos) frente a la probabilidad base | un estado de barra desplaza la probabilidad más que el azar |
| **sesión** | retorno por hora, por franja (Asia, Londres, Nueva York) y por día de la semana; ruptura del rango de una franja | la ventaja está en la hora, no en el precio |
| *contexto* | deriva (cuánto sube solo el activo); agrupamiento de la volatilidad; **coste de una operación dividido entre el ATR del marco** | no genera propuestas: dice en qué marcos se puede operar |

Siete familias se solapan más que tres: una vela de impulso es momentum y puede ser a la vez una
ruptura. El perfil lo dice en vez de esconderlo: la correlación entre las puntuaciones de las
familias, por celda, va en el informe.

**Contra qué se compara.** Cada medida se repite sobre la misma serie remuestreada por bloques
(se conserva la volatilidad y la deriva, se rompe el orden). De ahí sale la p de cada medida, y
todas juntas se corrigen con Benjamini-Hochberg (`engines/inference`), porque 19 activos × 4 marcos
× 2 direcciones × ~25 medidas son unas 3.800 pruebas y alguna destacará por azar.

**Tres filtros antes de dar una celda por buena.**

1. **Significativa** tras la corrección.
2. **Paga el doble del coste.** El efecto medio por operación, en dinero, tiene que superar dos
   veces el coste de `assets/` (el mismo criterio «neto 2×» del `ideaExpert`). Una tendencia real que
   no paga el spread no es una celda.
3. **Estable por años.** El signo se repite en la mayoría de los años de `build`. Una celda que
   vive de un solo año se marca como frágil.

**Qué entrega.** Siete puntuaciones de 0 a 100 por celda, una por familia, cada una con
su p, su efecto en múltiplos del coste y su estabilidad; y las medidas en crudo, que es de donde el
`ideaExpert` saca los parámetros (el horizonte donde hay estructura, el tamaño característico de la
ruptura). Vive en `AlgoData/research/profiles/`. Cada medida deja su fila en el ledger: el perfil
también es un barrido y cuenta como tal (encargo 32).

**Dónde va el código.** `studies/research/marketProfile/`, una familia nueva de `studies/` para el
paso 1, con la forma de módulo de `studies/CLAUDE.md`. Reutiliza `core.bars`, `engines/nulls` y
`engines/inference`; el Kaufman y el ATR ya están en `studies/readings/conditionalMap/regime.py`.

**Lo que el perfil no es.** No predice que una plantilla vaya a sobrevivir. Es un punto de partida:
dice dónde hay estructura medible en el precio. Si de verdad orienta bien, lo dirá la pieza 5.

## 4. Pieza 2: la memoria de resultados

Una tabla, una fila por intento (plantilla × activo × marco × dirección):

| columna | de dónde sale |
|---|---|
| plantilla, familia, idea de origen | `templates/registry.csv`, `AlgoData/ideas/` |
| proyecto, fecha, horas de CPU | `projects/registry.csv`, el autopilot |
| estrategias construidas y las que quedan tras cada paso | `autopilot/<proyecto>/<ts>/resumen.md` y el ledger |
| paso en el que murió la población, o supervivientes finales | lo mismo |
| veredicto | `runs.csv` (hoy casi vacío: lo rellena el autopilot al acabar) |

Y un **índice de ideas**: toda idea propuesta, elegida o no, con cuántas hipótesis midió el
`ideaExpert` para llegar a ella. Las ideas descartadas también son ensayos.

Con eso el tablero sabe tres cosas que hoy no sabe nadie: qué celdas están sin tocar, qué familias
han dado supervivientes y en qué clase de activo, y cuántas ideas se han gastado ya en cada celda.
Es la mitad «por plantilla» del encargo 26 y usa el contrato del 32; no se duplica ninguno.

## 5. Pieza 3: la taxonomía de bloques

Es el encargo 6: rellenar `archetypes` (un peso de 0 a 3 por familia) en los 752 bloques que
faltan. Una sola pasada de un agente, y tú corriges en la tabla de paletas de la ventana, que ya
enseña la etiqueta y el peso. Sin esto, el `buildingBlocksExpert` elige entre 767 bloques casi a
ciegas, y es lo que `WORKFLOW.md` marca como pendiente del paso 6.

**Tu decisión de hoy cambia el encargo 6.** Está escrito para tres familias (ruptura, reversión,
tendencia), fijadas el 2026-09-24 con un «no se inventan más». Con siete, cada bloque lleva siete
pesos, y hay que ampliar el encargo, `taxonomy.yaml`, las cuatro paletas y la tabla de la ventana.
Los 15 bloques ya etiquetados conservan sus tres pesos y ganan cuatro.

Dos reglas del dossier de libros que el director aplica al elegir bloques, porque van al corazón de
tu frase «con estos building blocks»:

- **Ortogonalidad** (Tharp, Williams): el hueco aleatorio usa una familia de dato distinta de la
  condición fija. Si la condición fija es precio, el hueco es tiempo, volatilidad o sesión.
- **Tendencia con contratendencia, nunca dos iguales** (Katz, Fitschen): un filtro de tendencia
  sobre una entrada de tendencia sólo encarece la entrada.

## 6. Pieza 4: el director

**El tablero, antes del agente.** `python3 -m studies.research.board` imprime una página con las
celdas ordenadas. El orden lo calcula Python con tres factores, cada uno visible:

| factor | qué premia |
|---|---|
| señal del perfil | celdas que pasan los tres filtros de §3, por tamaño del efecto en múltiplos del coste |
| hueco de cobertura | celdas donde no se ha probado esa familia, o se ha probado poco |
| rendimiento pasado | familias que ya dieron supervivientes en esa clase de activo (§7) |

**Una puerta antes del orden:** sólo entran en el tablero las celdas que pasan los tres filtros de
§3. El hueco de cobertura ordena entre las que pasan; nunca mete una que no pasa.

Y un freno: las celdas donde ya se han gastado muchas ideas bajan, porque cada idea más sube el
listón de las siguientes.

**Lo que hace el agente** (`researchDirector`, nuevo, en `.claude/agents/`):

1. Lee el tablero: una página, no el repositorio.
2. Elige **una celda**, la mejor, y explica por qué, en español y con los números del perfil. Puede
   apartarse del orden del tablero, pero tiene que decir por qué (un activo con costes aún
   provisionales, una celda que es el mismo mercado que la de la propuesta anterior).
3. Lanza al `ideaExpert` con el encargo cerrado: activo, marco, dirección, familia y las medidas
   del perfil que la sostienen. El `ideaExpert` ya no explora a ciegas: busca **tres reglas
   distintas** dentro de una familia que el perfil ya ha señalado.
4. Para cada idea prepara la **paleta de bloques**: qué papel juega el hueco, qué familias de
   bloques entran y con qué peso, aplicando las dos reglas de §5.
5. Entrega la **propuesta**: el diagnóstico de la celda y las tres ideas, cada una con su regla
   exacta, su paleta, los bloques custom que habría que crear, lo que costará construirla (horas de
   custodio) y cómo puede fallar.

**De dónde salen las ideas.** De tres canteras, y la propuesta dice de cuál viene cada una: las
medidas del perfil (el horizonte donde hay estructura, el tamaño característico de la ruptura), el
catálogo de 390 ideas de tus libros, y lo que el agente proponga por su cuenta. Una idea de un libro
trae dentro los ensayos de su autor (Aronson), así que entra en el índice de ideas con esa marca.

**Por qué concentradas.** Las tres comparten activo y marco: un solo preflight, los mismos costes,
ventanas y datos, y tres proyectos que sólo cambian de plantilla. Y la comparación es limpia: la
diferencia de resultado es de la idea, no del mercado. A cambio, dos costes que la propuesta enseña
siempre:

- **Las supervivientes se parecerán.** Tres ideas de la misma familia en el mismo mercado ganan y
  pierden los mismos años; para la cartera cuentan como poco más de una.
- **El listón de la celda sube tres ensayos de golpe.**

**Regla dura 11, sin excepción.** Si una idea admite dos lecturas, el director no elige: la propuesta
la trae como pregunta, y esa idea no se lanza hasta que la contestes. Las otras dos sí pueden ir.

**Lo que pasa cuando lanzas.** Las tres van a SQX salvo la que vetes. El botón, con confirmación
como los otros lanzadores de la ventana (regla dura 3), encadena para cada idea lo que ya existe:
`core.assets` → `templateArchitect` (que crea el bloque custom si falta) → `builder --workflow` →
`buildingBlocksExpert` con la paleta ya decidida → autopilot. **Una detrás de otra**: el custodio
lleva un solo trabajo largo cada vez. Las plantillas y las paletas se pueden preparar las tres
mientras corre el primer build.

**Lo que cuesta en tokens.** Con lo medido hoy en tus sesiones (Opus 5.5):

| tramo | coste aproximado |
|---|---|
| perfil, memoria y tablero | 0 |
| el director leyendo el tablero y escribiendo la propuesta | 3-5 $ |
| el `ideaExpert` buscando tres ideas en una celda | 8-24 $ |
| **una propuesta completa** | **unos 10-30 $** |
| plantilla y paleta de cada idea lanzada (unos 15 $ cada una) | hasta 45 $ |
| **un ciclo entero, con las tres ideas en SQX** | **unos 55-75 $** |

El `ideaExpert` cuesta hoy 7-8 $ por sesión, medido, y ya entrega tres ideas por sesión para un
activo y un marco. Enfocado a una familia, una sesión podría bastar (8 $); si hacen falta tres,
24 $. Está por comprobar. Además del coste en tokens, un ciclo son tres corridas del custodio.

## 7. Pieza 5: el bucle que aprende

1. **El veredicto vuelve solo.** Al terminar el autopilot, la fila de la memoria se cierra con
   cuántas llegaron a cada paso.
2. **El tablero se mueve.** El factor «rendimiento pasado» es la tasa de supervivencia de cada
   familia por clase de activo, con su incertidumbre: con pocos intentos pesa poco, y una familia sin
   probar no se descarta. Hoy, con 9 corridas, ese factor empieza plano.
3. **El listón sube con cada idea.** El ledger ya cuenta ensayos para el Sharpe deflactado
   (`ledger/trials.py`). Las ideas gastadas en una celda entran en esa cuenta, y la propuesta lo
   enseña: «en XAUUSD H4 ya van K ideas».
4. **El perfil se examina a sí mismo.** Cuando haya unas 20-30 corridas cerradas, una lectura
   sencilla: ¿las celdas con puntuación alta dieron más supervivientes que las de puntuación baja?
   Si no, el factor «señal del perfil» pierde peso en el tablero. Esa es la decisión que sale, con
   su coste: cuántas corridas se habrían ahorrado o perdido siguiendo el perfil.

El encargo 28 (¿aporta algo el hueco aleatorio?) y el 40 (probabilidad de que una estrategia
sobreviva) escriben en la misma memoria y la enriquecen; ninguno bloquea este diseño.

## 8. La ventana: el panel «Investigar»

Dentro de la zona de plantillas, con el estilo terminal de siempre. Cuatro vistas:

1. **El mapa.** Activos en filas, marcos en columnas. Cada celda lleva el color de su familia
   dominante y la intensidad de su efecto; gris si no pasa los tres filtros. Al pulsar una celda, sus
   medidas, cada una con su explicación.
2. **La memoria.** La cobertura de hoy, más el embudo de cada intento: construidas, tras cada paso,
   supervivientes.
3. **«Proponer investigación».** El botón que lanza al director. Mientras trabaja, se ve en qué
   paso va.
4. **La propuesta.** Las tres ideas lado a lado, cada una con su casilla para vetarla y sus
   preguntas abiertas si las hay, y «Crear plantillas y lanzar en SQX» con su confirmación. Después,
   la cola: qué idea está en el custodio y cuáles esperan.

## 9. Orden de construcción

| fase | qué | toca SQX | tokens al usarse |
|---|---|---|---|
| 1 | perfil de mercado, con su capítulo del manual | no | 0 |
| 2 | memoria de resultados y que el autopilot escriba el veredicto | no | 0 |
| 3 | taxonomía: ampliar el encargo 6 a siete familias, ejecutarlo, y tu revisión | no | una vez |
| 4 | el tablero, el agente `researchDirector` y la skill que lo lanza | no | 10-30 $ por propuesta |
| 5 | el panel «Investigar» y la cola de las tres ideas | sólo al lanzar | hasta 45 $ por ciclo |
| 6 | el bucle: tasa por familia, cuenta de ideas, examen del perfil | no | 0 |

Las fases 1 y 2 ya son útiles solas: el mapa responde «¿qué es el XAUUSD en H4?» sin agente.
La 3 puede ir en paralelo. La 6 necesita corridas cerradas para tener algo que decir.

## 10. Decisiones cerradas

No queda ninguna abierta. Las seis preguntas de la primera versión están en §0, y las dos que
salieron después se cerraron el mismo 2026-10-01:

- **Celdas grises: no entran.** El director sólo propone sobre celdas que pasan los tres filtros de
  §3. Un hueco de cobertura, por grande que sea, no basta: si ninguna celda de reversión pasa, la
  librería sigue sin plantilla de reversión, y el mapa dice por qué.
- **XAGUSD y los petróleos: como cualquier otro.** Están en el mapa y el director puede proponer y
  lanzar builds sobre ellos si una celda pasa los filtros, aunque sus costes sigan pendientes. Tú
  pones en alta prioridad cerrar esos costes. Mientras no lo estén, la propuesta lo avisa en la
  propia idea: «costes provisionales», porque el filtro «paga el doble del coste» se ha medido
  contra un coste que puede cambiar.

## 11. Lo que no está verificado

- **Que el perfil oriente.** No hay ninguna prueba de que una celda con puntuación alta dé más
  supervivientes. Con 9 corridas no se puede saber; por eso el punto 4 de §7 existe.
- **La nula.** El remuestreo por bloques es la propuesta; la longitud del bloque cambia las p y no
  está elegida. En el dossier `Ajedrez4D` ya salió que esa longitud importa.
- **El tiempo de cálculo del perfil.** 19 activos × 4 marcos × cientos de remuestreos: estimo
  minutos, no lo he medido.
- **El coste del `ideaExpert` enfocado.** Los 7-8 $ son de sus diez sesiones sin perfil.
- **Que siete familias se puedan separar.** Momentum, ruptura y tendencia miden cosas vecinas; puede
  que el perfil dé casi la misma puntuación a las tres y haya que fundirlas.
- **El tramo `build` de cada activo.** No he comprobado que los 19 tengan ventana `build` definida ni
  datos suficientes en ella.
- **El feed de `build`.** En XAUUSD, 2008-2013 es calidad B y el spread anterior a 2017 es un
  modelo. El perfil hereda esas limitaciones en todos los activos.
- **Nada de esto se ha corrido.** Ninguna cifra de este dossier salvo las de tokens (§6) y las del
  inventario (§1) viene de datos.
