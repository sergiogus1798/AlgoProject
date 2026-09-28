# Ideas de internet y de tus libros — lo que dicen los que ya lo intentaron

**Dossier del dueño, noche del 2026-09-26 al 27.** Pediste todas las ideas, por locas que parezcan, de
una hora de búsqueda por internet y de tus libros de trading algorítmico. Este documento las recoge y te
explica cada una: qué dice la fuente, qué significaría en el proyecto y cuánto creo que vale.

**De dónde sale.**

- **Internet.** Una hora larga de búsqueda: papers académicos (Journal of Finance, RFS, SSRN, arXiv hasta
  septiembre de 2026), la Reserva Federal, el BIS, blogs de practicantes (Carver, Chan, Build Alpha,
  Davey) y foros de MQL5 y StrategyQuant. 89 ideas, cada una con su enlace.
- **Tus libros.** De los 129 ficheros de `~/Desktop/Books` separé los 24 con contenido sistemático o
  cuantitativo. Ocho agentes los leyeron enteros en paralelo, cada uno con su lote, y apuntaron cada idea
  con su página. Salieron unas 630 ideas en bruto.

| lote | libros |
|---|---|
| Aronson | *Evidence-Based Technical Analysis* (2007) |
| Chan | *Quantitative Trading* (2008) y *Algorithmic Trading* (2013) |
| Sistemas | Katz y McCormick, *The Encyclopedia of Trading Strategies* (2000); Fitschen, *Building Reliable Trading Systems* (2013) |
| Tortugas | Tharp, *Trade Your Way to Financial Freedom* (1.ª ed.); Faith, *Way of the Turtle*; Covel, *The Complete Turtle Trader* |
| Intermercado | Katsanos, *Intermarket Trading Strategies*; *Currency Trading and Intermarket Analysis*; *The Commitments of Traders Bible*; *Sentiment in the Forex Market* |
| Análisis técnico cuantitativo | Williams, *Long-Term Secrets to Short-Term Trading*; *New Frontiers in Technical Analysis*; el manual del CMT (capítulos de sistemas, estadística, ciclos y volatilidad) |
| Tendencia y riesgo | Covel, *Trend Following*; Abraham, *The Trend Following Bible*; Taleb, *Fooled by Randomness*; Lowenstein, *When Genius Failed*; Elder (capítulos de sistemas y riesgo) |
| Market Wizards | los tres libros de Schwager, sólo las entrevistas a sistemáticos y las reglas comprobables del resto |

*The Handbook of Technical Analysis* (2016) no se pudo leer: en disco hay un puntero de Git LFS de 134
bytes, no el PDF. El resto de la carpeta es trading manual y no se leyó.

**Cómo se ordenó.** Las ideas repetidas entre libros y web se fundieron en una sola entrada que cita todas
sus fuentes. De unas 720 ideas en bruto quedaron 390 entradas:

| sección | entradas |
|---|---|
| 3 · ¿Es real? | 96 |
| 4 · ¿Dónde buscar? | 156 |
| 5 · Costes, riesgo, cartera y vivo | 94 |
| 6 · Proceso, cultura e interfaz | 44 |

Entre secciones puede quedar algún solape pequeño: ante la duda, los agentes prefirieron repetir una idea a
perderla. Después se agruparon por la pregunta que responden:

1. **Lo que contradice al proyecto.** Va primero porque es lo más valioso: lo que un libro o un paper
   dice en contra de algo que el proyecto hace hoy.
2. **Las treinta mejores**, en un solo ranking.
3. **¿Es real?** Validación y estadística.
4. **¿Dónde buscar?** Hipótesis, familias de plantillas y fuentes de datos.
5. **Costes, riesgo, cartera y operación en vivo.**
6. **Proceso, cultura e interfaz.**
7. **Las locas**, en una lista aparte.
8. **Lo que este dossier no verifica.**

**Cómo leer cada entrada.** Cada idea lleva cuatro etiquetas:

- **Estado.** NUEVA si el proyecto no la tiene. YA EXISTE si ya está construida, y se dice dónde. AMPLÍA si
  mejora algo que existe.
- **Tipo.** Estudio, datos, generación, riesgo, cartera, vivo, proceso o interfaz.
- **Locura.** De 0, práctica estándar, a 3, rara pero interesante.
- **Valor.** De 1 a 5, con su motivo.

**Estado de este dossier.** Nada de lo que hay aquí está aceptado ni construido. Es el catálogo del que
elegir. Una idea que elijas pasa a `docs/encargos/` como encargo, como con las catorce del dossier
`ideas-de-edge-2026-09-26`. Las ideas que sólo tocan la ventana y no cambian ningún módulo se encargaron
esta misma noche a la sesión que construye la interfaz. La sección 6 dice cuáles.

**Una advertencia que hacen los propios libros.** Aronson, en la página 390, avisa de que una regla sacada
de un libro trae dentro los ensayos ocultos de su autor: el libro publica la que funcionó, no las cien que
probó. Casi todos los números que citan Williams, Katsanos o el libro del COT están optimizados sobre toda
la muestra. Ninguna cifra de este dossier es un prior fiable. Cada idea que se construya pasa por el
ledger y por la cadena como cualquier otra.

## 1 · Lo que contradice al proyecto

Es la parte más valiosa de la noche. Aquí están las veintiuna cosas que un libro o un paper dice en contra
de algo que el proyecto hace hoy, agrupadas y con la propuesta de qué hacer con cada una. Ninguna obliga a
cambiar de doctrina. Casi todas se resuelven midiendo en el propio ledger quién tiene razón, en vez de
elegir bando.

### Las cinco que más pesan

#### 1.1 · Construir sin stop

**Qué dicen.** Es la contradicción más repetida de todo el material. Seykota: «los elementos del buen
trading son cortar pérdidas, cortar pérdidas y cortar pérdidas» (*Market Wizards*, p. 81). Minervini
calculó que un tope de pérdida le habría subido el beneficio un 70 % (*Stock Market Wizards*, pp. 97-98).
Tharp y Eckhardt dicen que la salida importa mucho más que la entrada (Tharp, pp. 28-29 y 197-201; Covel,
*Complete Turtle Trader*, p. 79). Williams enseña que el stop no es neutro: con las mismas entradas, un
stop de 500 $ pierde 41.750 $, uno de 1.500 $ gana 116.880 $ y uno de 5.000 $ gana 269.525 $ (pp. 240-243).
Katz añade que las entradas de giro, las contratendencia, esconden su ventaja si no llevan un stop
ajustado (pp. 201 y 211). Aronson dice que las colas gordas inflan el sesgo de minería de datos
(pp. 303-306). Y los cinco libros de riesgo ven en LTCM el mismo patrón: una estrategia que aguanta las
pérdidas hasta que vuelven es una apuesta corta de cola que no se ve en la muestra.

**Lo que dice a favor del proyecto.** Faith encontró que una entrada con ventaja más una salida por tiempo
batía a las salidas con stop, y que añadir un stop de cualquier anchura empeoraba todas las métricas
(*Way of the Turtle*, pp. 140-147). Williams dice que en sistemas siempre dentro del mercado el stop nunca
ayudó (p. 228). Chan cita un estudio en el que los stops degradaban sistemas rentables. Fitschen dice que
los stops rara vez suben el beneficio por operación en sistemas de tendencia.

**El riesgo concreto.** La búsqueda genética, sin stop, puede premiar estrategias cuya ventaja **depende**
de no cortar nunca. El stop del paso 24 cambia después la distribución de operaciones que la puerta aprobó.
Lo que se opera ya no es lo que se validó.

**Qué hacer, sin optimizar ningún stop.** Tres medidas baratas:

1. Volver a pasar las cribas baratas y el mono con el stop del paso 24 ya fijado, y con el **mismo stop
   puesto también al mono**. Marcar las supervivientes cuyo veredicto cambia.
2. Medir por superviviente qué parte del beneficio viene de operaciones que un stop razonable habría
   cortado. Es la dependencia del no-stop.
3. Una bandera de «suave pero frágil»: curva muy lisa, tasa de acierto alta y pérdidas raras pero grandes.
   Esa superviviente va primero a la prueba de choques de precio.

#### 1.2 · El mono no basta como nulo

**Qué dicen.** Cuatro fuentes independientes dicen que el mono de entrada aleatoria es una vara baja:

- **Monos no seleccionados.** Aronson (pp. 274-280 y 441-443): las estrategias de SQX son las ganadoras
  de una búsqueda en `build`, pero el mono del encargo 9 no pasa por ninguna selección. Lo que cuenta ese
  mono es sólo una **cota inferior** de los falsos positivos. En su libro, la mejor de 6.402 reglas sin
  ningún valor gana un 11 % al año. Un test ingenuo le da p = 0,0005. El Reality Check de White le da
  p = 0,82.
- **Colas gordas.** Chan (*Algorithmic Trading*, pp. 16-22): una estrategia de momentum batía a sus monos
  con p < 0,00001, y sin embargo fallaba contra precios sintéticos con la misma media, desviación,
  asimetría y curtosis, con p = 0,117. Sus palabras: «cualquier distribución de rendimientos con curtosis
  alta puede favorecer a una estrategia de momentum». El mono condiciona en el camino real del precio y
  no puede ver esto.
- **Mono con salida de tendencia.** Tharp (pp. 200-201): el test de la moneda de Basso, con entrada al
  azar y una salida trailing de 3 ATR, salía rentable en el 80-100 % de las corridas. Si en un activo eso
  ya gana, una superviviente tiene que batir a ese mono, no al ingenuo.
- **Nulo de modelo.** Brock, Lakonishok y LeBaron (manual del CMT, p. 297): correr la estrategia sobre
  series simuladas con AR y GARCH. Si la ventaja sobrevive ahí, la agrupación de volatilidad basta para
  explicarla.

**Qué hacer.** Monos seleccionados, que son Python puro y no tocan SQX (sección 3). El nulo de mercado
sustituto **no se puede hacer dentro de SQX**: el API no tiene verbo de importación, y un símbolo nuevo
exige la GUI del maestro y toca el almacén de datos compartido (encargo 9, §1; corrección del 2026-09-28).
Sólo es viable con un backtest propio en Python, y hoy sólo para las pocas madres que ya se han traducido.

#### 1.3 · Meseta no es robustez

**Qué dicen.** Katz (p. 45): «la tolerancia de los parámetros no sirve para medir la robustez de un
modelo. Los únicos árbitros son los tests estadísticos y, sobre todo, los de fuera de muestra». Da el
contraejemplo (pp. 100-103): una ruptura de volatilidad rentable en **todos** los juegos de parámetros
dentro de muestra, el peor con +15,5 % al año, y **ninguno** rentable fuera. La versión filtrada con ADX,
99 de 100 rentables dentro, perdía un 20,9 % al año fuera. Faith añade un matiz, no una contradicción:
en una colina suave, operar cerca del pico también vale.

**Por qué importa aquí.** El SPP, la nube de parámetros y la idea aceptada de «operar la meseta» se apoyan
en que la meseta predice. Nadie lo ha comprobado en este proyecto.

**Qué hacer.** Comprobarlo en el ledger: ¿las madres en meseta sobreviven más en `oos1` y `oos2` que las de
pico? Y acompañar cada lectura de meseta con una lectura de deterioro en el tiempo dentro de `build`.

#### 1.4 · La búsqueda genética y el hueco aleatorio

**Qué dicen.** Chan (*Quantitative Trading*, pp. 26-27): redes neuronales, árboles y algoritmos genéticos
«rindieron miserablemente hacia delante». Lo que funciona tiene pocos parámetros y una base económica.
Shaw empieza siempre por una hipótesis estructural y evita «buscar a ciegas en los datos»
(*Stock Market Wizards*, pp. 143 y 145). Williams: «no se puede predecir A con A». Comprar el S&P sólo en
rupturas de los bonos ganó 141.792 $, mientras que las rupturas del propio S&P eran malas (pp. 233-237).
En internet, Neely, Weller y Ulrich encuentran que las reglas simples de FX dejaron de ganar en los
noventa, y que las complejas y menos estudiadas aguantan más.

**Qué hacer.** Dejar que lo decida el ledger. Un A/B controlado entre plantillas con sólo la condición
fija y plantillas con condición fija más hueco aleatorio, juzgado por supervivencia en `oos1` por hora de
CPU. Y para cada superviviente, cuánto de su ventaja viene de la condición fija, que es la hipótesis, y
cuánto del hueco, que es minería.

#### 1.5 · Un solo activo en el build

**Qué dicen.** Katz optimiza un único juego de parámetros sobre toda la cesta de mercados, porque «un buen
sistema debería operar muchos mercados con los mismos parámetros» (p. 80). Fitschen desarrolla sobre
cestas de 37 a 56 mercados con miles de operaciones y llama trampa de sobreajuste al paradigma de un
solo gráfico (p. 24). Dennis tiraba cualquier sistema que no funcionara «en bonos y en judías»
(*Market Wizards*, p. 54). Los libros de tendencia juzgan la regla sobre la cesta entera.

**Dos matices que afectan al cruce de mercados.** Katz encuentra una correlación de sólo 0,15 entre lo
bueno que es un mercado dentro y fuera de muestra (pp. 99 y 107), así que el cruce de mercados no debe
servir para **elegir** en qué mercados operar. Y Faith dice que las diferencias entre mercados de una misma
clase son casi todas ruido, y que excluir un mercado por un mal backtest costó a las Tortugas su mejor
operación (pp. 213-219). Conviene juzgar por clase agregada, no mercado a mercado.

**Qué hacer.** Añadir al cruce de mercados un nivel de mercados **no relacionados**, informativo y no
eliminatorio. Y leer el cruce de mercados como aprobado o suspendido del grupo, nunca como selector.

### El resto, por orden de peso

#### 1.6 · El número de ensayos independientes quizá es demasiado pequeño

Aronson (figura 6.36, pp. 300-302): el sesgo de minería sigue alto hasta que la correlación entre reglas se
acerca a 1. `core/surface/trials.py` agrupa variantes por correlación, por ejemplo 479 variantes en 21
ensayos, y eso probablemente halaga el Sharpe deflactado. El Sharpe deflactado es el Sharpe corregido por
cuántas cosas se probaron. **Qué hacer:** simular paneles nulos con la matriz de correlaciones observada y
usar el N equivalente. Del mismo libro: el exceso de supervivientes de la población no tiene barra de
error, porque los 45 supervivientes de un ejemplo eran sólo 13 estructuras distintas.

#### 1.7 · El stop del paso 24 aplicado igual a toda estrategia

Chan (*Quantitative Trading*, pp. 106-107 y 142-143): «un modelo de reversión nunca recomendará un stop».
Nunca vio que un stop mejorara una estrategia de reversión. El percentil 80-95 del MAE de las ganadoras
corta por construcción entre el 5 % y el 20 % de las ganadoras dentro de muestra. **Qué hacer:** en
estrategias de reversión, un stop de catástrofe justo más allá del peor MAE dentro de muestra, que no
corta ninguna operación. El percentil sólo para las de momentum. No contradice que el stop no se optimice.

#### 1.8 · El ejemplo de nuestra familia lead-lag es simultáneo, no un adelanto

El dossier `ideas-de-edge-2026-09-26` justifica la familia lead-lag con «el oro sigue al dólar». Katsanos
lo midió con rendimientos diarios de 1992 a 2006: r = −0,31 el mismo día y −0,025 al día siguiente, casi
cero en todos los retardos de 1 a 10 días (p. 123). Su aparente adelanto semanal de r = 0,59 es un
artefacto de rendimientos solapados (p. 118). Los libros sólo encuentran adelantos reales en las fronteras
de sesión, cuando el mercado rezagado estaba cerrado o fino, y en reversiones residuales de unas horas.
**Qué hacer:** reformular la familia como «adelantos de frontera de sesión y reversión residual». Esta
corrección afecta a nuestro propio dossier.

#### 1.9 · Las métricas de una ventana fija dependen de dónde corta

Faith (pp. 182-190): Sharpe, factor de beneficio, MAR y CAGR sobre una ventana fija se mueven un 10-15 %
con sólo desplazar la ventana unos meses. El CAGR y el MAR son unas 30 veces más sensibles a los bordes
que su RAR%, la pendiente de la regresión de la equidad logarítmica. El Sharpe deflactado corrige por el
número de ensayos, no por esto. Fitschen añade que una ventana fuera de muestra se juzga contra la banda de
ventanas de igual longitud dentro de muestra, no contra cero (pp. 23-24). **Qué hacer:** métricas robustas
y un desplazamiento de los bordes de la ventana al ordenar supervivientes.

#### 1.10 · La suavidad selecciona fragilidad

Faith (pp. 101-104) y Covel (pp. 164-165 y 192-193): una curva lisa suele esconder más riesgo, no menos.
Harding, en Covel, nota que quitar los mejores rendimientos **sube** el Sharpe, así que el Sharpe castiga
las ventajas con asimetría positiva. Si la función de aptitud de SQX o alguna criba premian la suavidad,
con R², Sharpe o estabilidad, la búsqueda se inclina hacia perfiles de asimetría negativa. **Qué hacer:**
un contrapeso de cola izquierda y la clasificación de cada superviviente como «larga de opción» o «corta
de opción» (sección 5).

#### 1.11 · Los Monte Carlo del proyecto no se calibran

Tres críticas distintas:

- **Cartera.** Faith (pp. 201-203): barajar operaciones infravalora el drawdown, porque las peores caídas
  llegan cuando muchas posiciones se giran juntas. Es exactamente el uso para el que el dueño conserva el
  Monte Carlo. La solución es un bootstrap por bloques de unos 20 días del P&L diario conjunto. Ya está
  anotado en `portfolio/common/monteCarlo/POSSIBLE_IMPROVEMENTS.md`.
- **MC Retest.** Nadie comprueba si sus bandas aciertan. Cuando una estrategia se ve después en datos
  nuevos, ¿cuántas veces rompe su drawdown el percentil 95 y el 99 del MC? Si pasa mucho más que un 5 % y
  un 1 % de las veces, todo umbral sacado del MC es demasiado estrecho.
- **Deslizamiento.** El MC Retest reparte el slippage igual entre tipos de orden. Las órdenes stop en
  niveles de ruptura populares se llenan peor de lo probado (manual del CMT, pp. 535-536 y 572; Dennis en
  *Market Wizards*, p. 51). Y las órdenes límite que sólo tocan y se dan la vuelta, que son las ganadoras,
  no se llenan en real (Fitschen, pp. 27-29 y 274-275).

#### 1.12 · Más datos no es más robusto

Chan (*Quantitative Trading*, pp. 25 y 52-53): sólo es cierto si la serie es estacionaria. Pide buen
rendimiento en los datos recientes. Eckhardt dice lo contrario: los sistemas construidos sobre datos
recientes «se sostienen poco» (*New Market Wizards*, p. 53). **Qué hacer:** leer siempre el P&L del build
año a año y su tendencia, y modelar costes que cambian con el tiempo.

#### 1.13 · Las anomalías de calendario publicadas se gastan

El efecto lunes desapareció en tres décadas y el efecto enero se apagó (manual del CMT, pp. 173-174). El
sistema de un día de avances y retrocesos pasó de 100 $ a 884 millones y colapsó después de 2005 (pp.
146-148). En internet: la deriva nocturna del S&P, que daba un 3,7 % al año en una hora concreta, está en
casi cero desde 2021 según la Fed de Nueva York en julio de 2026. McLean y Pontiff miden que las anomalías
publicadas pierden un 58 % tras publicarse. **Qué hacer:** la familia de calendario aceptada necesita
tests en ventana reciente y la tendencia de su ventaja a la vista, no sólo significación en la muestra
entera.

#### 1.14 · La puerta tira piezas que valen combinadas

Shaw: ineficiencias no rentables por separado lo son donde coinciden (*Stock Market Wizards*, p. 142).
Hite conserva sistemas «no tan buenos por sí solos» por su baja correlación (*Market Wizards*, pp. 90 y
94). Galante: un fondo que perdía contra el índice, combinado con él al 50 %, le ganaba y le partía el
drawdown por la mitad (p. 51). **Qué hacer:** guardar los casi supervivientes para una prueba de
confluencia o de cartera, en vez de borrarlos. Y para candidatas de cartera, la pregunta es su
contribución, no ganar al buy and hold cara a cara.

#### 1.15 · Estadística delicada contra «instrumentos romos»

Eckhardt: «los tests delicados con los que los estadísticos exprimen significación de datos marginales no
tienen sitio en el trading» (*New Market Wizards*, p. 47), porque la varianza de los precios puede ser
infinita. El Sharpe deflactado y cualquier p con supuestos normales son lo que critica. El SPA y el StepM,
que usan bootstrap, lo son menos. **Qué hacer:** no quitar nada, pero mostrar a su lado gemelos robustos,
como la mediana de R, tests de rangos y un Sharpe winsorizado, además de un índice de cola.

#### 1.16 · El mínimo de operaciones

Fitschen (pp. 8-19 y 168-169): «30 operaciones bastan» es falso. Las necesarias crecen con la varianza de
las operaciones y a menudo son miles. El error estándar de la operación media sigue en 75-100 $ con 300 a
1.000 operaciones. Un mínimo de un par de centenares en una estrategia H4 de un solo activo está, según él,
en terreno de sobreajuste.

#### 1.17 · El mapa condicional es una búsqueda de 45 celdas

Aronson: el paso 22 mira 45 celdas y sólo lleva un aviso. Necesita un mínimo de operaciones por celda y un
p por permutación entre celdas.

#### 1.18 · El buy and hold al mismo riesgo puede ser una vara baja

Aronson, razonamiento del agente, sin probar. En una ventana de oro bajista, una estrategia larga sin
ninguna habilidad y poco expuesta debería ganar al buy and hold al mismo riesgo. **Qué hacer:** poner a su
lado un benchmark sin información y sin tendencia en el paso 20 y en la criba de snooping. Se zanja con una
simulación en una ventana bajista.

#### 1.19 · Retirar estrategias que decaen puede ser vender en el fondo

Dunn cayó un 42 % y después subió un 430 % (Covel). Choca con la idea aceptada de la cadencia de la
fábrica y la vida media del edge. **Qué hacer:** que las condiciones de retirada se fijen antes de operar,
con el peor drawdown esperable para esa estrategia, no con la sensación del momento.

#### 1.20 · Señales sin explicación

Renaissance, según el libro de Zuckerman, aceptaba señales estadísticamente significativas que no sabía
explicar, pero con poco capital al principio. El protocolo de Arnott, Harvey y Markowitz pide lo contrario:
una base económica previa. **Qué hacer:** es un matiz para el dueño. La plantilla puede exigir hipótesis y,
aun así, admitir una categoría «sin explicación, en probación», contada aparte en el ledger.

#### 1.21 · Los patrones de apertura necesitan una sesión

Oops!, smash day, las reglas de barra interior de Crabel y la ruptura del rango de apertura necesitan una
apertura de sesión real con hueco. En FX y oro a M30 y H1, la apertura siguiente es casi igual al cierre
anterior. Estas familias no se pueden probar sin reconstruir las barras alrededor de una sesión elegida. La
frontera de sesión de cada activo es una decisión del dueño y hay que preguntarla. Ya está pendiente en
«Lo que bloquea hoy» del WORKFLOW, por las horas UTC de cada sesión.

## 2 · Las treinta mejores, en un solo ranking

Ordenadas por lo que creo que dan contra lo que cuestan. Cada una tiene su entrada completa en la sección
que se indica. Las seis primeras cuestan poco y cambian decisiones que hoy se toman a ciegas.

### Antes de gastar CPU

1. **Probar la condición fija antes del build.** Con cuántas barras dispara, qué rendimiento viene
   después contra el incondicional y contra señales al azar con la misma frecuencia, a qué horizonte. Lo
   proponen, cada uno a su manera, Aronson, Eckhardt, Shaw, Faith y Fitschen, y en internet la tarjeta de
   factor de Alphalens. Son minutos de Python y pueden ahorrar un build entero del custodio. Sección 4.
2. **Una tarjeta de carácter por activo, timeframe y sesión.** Test ADF, exponente de Hurst, variance
   ratio y vida media de la reversión, medidos sólo en `build`. Dicen dónde tiene sentido una plantilla de
   tendencia y dónde una de reversión. Lo proponen Chan, Fitschen con su mapa de tendencia, Aronson y el
   manual del CMT. Sección 4.
3. **Monos seleccionados.** Generar monos en `build`, quedarse con los mejores por la métrica de SQX y
   pasar esos por la cadena. El mono sin seleccionar sólo da una cota inferior de los falsos positivos. De
   Aronson. Sección 3.
4. **Una familia placebo de punta a punta.** Una plantilla cuya condición fija sea una irrelevancia
   conocida, como la fase lunar o un ciclo falso de 23 días. La fracción que sobrevive es la tasa de falsos
   positivos de toda la cadena. De Katz, el manual del CMT y la literatura lunar. Complementa a los
   controles positivos aceptados. Sección 3.
5. **Un control negativo del generador.** Un bloque de ruido puro en el hueco aleatorio, más builds
   limitados a 2, 4, 6 y 8 condiciones. Mide cuánto «compra» un grado de libertad falso en esta cadena. De
   Eckhardt. Sección 3.
6. **Un nulo de mercado sustituto.** Series sintéticas con los mismos momentos, bootstrap por bloques,
   surrogados IAAFT o simulaciones GARCH. Atrapa lo que el mono no ve en estrategias de tendencia. De Chan,
   Brock, Lakonishok y LeBaron, y la web. **No se puede hacer dentro de SQX**, porque no hay forma de
   importar series; sólo con un backtest propio en Python. Sección 3.

### Lo que cambia cómo se lee una superviviente

7. **Volver a pasar la puerta con el stop del paso 24 fijado**, y el mismo stop puesto al mono. Marcar las
   que cambian de veredicto y medir su dependencia del no-stop. Sección 1 y sección 5.
8. **Historias alternativas con barras desplazadas.** Reconstruir las H4 empezando una, dos o tres horas
   más tarde desde las M1 y volver a correr cada superviviente. Una ventaja que sólo existe con una
   alineación es un artefacto, y además se rompería con un bróker de otra hora de servidor o con el cambio
   de hora. De Taleb, «Vs Shifted» de Build Alpha y los foros de MQL5. Sección 3.
9. **Grados de libertad malos.** Marcar todo parámetro cuyo mejor valor lo deciden tres operaciones o
   menos. Se calcula con las listas de operaciones del SPP y de la fábrica de variantes. Es la definición
   exacta de sobreajuste de Eckhardt. Sección 3.
10. **Benchmarks duros.** Que una superviviente de tendencia bata a los seis sistemas de tendencia de libro,
    reescalados al mismo periodo, y al mono con salida trailing de 3 ATR. No sólo al buy and hold. De Faith,
    Tharp, Covel y el momentum de series temporales de AQR. Sección 3.
11. **Calibrar el N efectivo por simulación** antes de dárselo al Sharpe deflactado. De Aronson. Sección 3.
12. **Comprobar en el ledger si la meseta predice la supervivencia.** De Katz. Sección 3.
13. **Un recorte calibrado por el propio proyecto.** La distribución de «métrica en `oos1` entre métrica en
    `build`» por familia, activo y timeframe, sacada del ledger, aplicada a cada estrategia nueva antes de
    enseñarla. Del manual del CMT, con McLean y Pontiff como referencia externa. Sección 3.
14. **La correlación entre supervivientes, medida sólo en días de crisis.** Con el P&L diario ya
    cosechado. La lección de LTCM: todo parecía independiente hasta que las correlaciones se fueron a 1.
    Sección 5.
15. **Calibrar las bandas del MC Retest** contra lo que pasó después en datos nuevos. Sección 5.
16. **Clasificar cada superviviente como larga o corta de opción** por la forma de su pago: asimetría,
    desviación contra desviación a la baja, rendimiento de la estrategia contra el del subyacente. Es la
    única etiqueta de riesgo en la que coinciden los cinco libros de riesgo. Sección 5.

### Donde puede estar el edge

17. **Costes que cambian con el tiempo.** El spread real de cada año sacado del histórico bid/ask de
    Dukascopy, la ventana del rollover de las 17:00 de Nueva York con spreads de 5 a 20 veces, y el
    deslizamiento distinto por tipo de orden. De Chan, la web y el manual del CMT. Sección 5.
18. **Una puerta de mitades para cualquier perfil estacional.** Calcular el perfil de hora, día o mes en
    cada mitad de `build` y correlacionar las dos, con un nulo por permutación. Sólo pasa a SQX lo que
    aprueba. De *New Frontiers in Technical Analysis*. Sección 3.
19. **La familia de ruptura de volatilidad en la apertura de sesión**, con los filtros de rango estrecho
    NR4 y NR7. De Williams y el manual del CMT. Necesita que el dueño fije la sesión. Sección 4.
20. **La familia de los fixings de FX.** El dólar se aprecia antes de los fixings de Tokio, BCE y Londres
    y se deprecia después, un patrón en W durante 21 años y 9 divisas. Journal of Finance, 2024. Aviso:
    con costes minoristas completos, el Sharpe sale negativo. Sección 4.
21. **Un plan de test concreto para la familia lead-lag**, ya reformulada: correlación cruzada no solapada
    por sesión, curva de saturación, reversión residual, prueba de desplazamiento de ±1 barra contra fugas.
    Del agente de intermercado sobre Katsanos. Sección 4.
22. **El intermercado como filtro sobre supervivientes existentes**, contra quitar la misma fracción de
    operaciones al azar. En el sistema del DAX de Katsanos, el factor de beneficio pasó de 1,93 a 4,18 con
    la mitad de operaciones. Sin CPU de SQX. Sección 4.

### Lo que protege después

23. **Una etiqueta de crisis por ventana**: qué episodios con nombre contiene cada ventana de test, como
    2008, el franco suizo en 2015, el COVID o el 5 de agosto de 2024. Y ese último día repetido sobre
    cada superviviente: la biblioteca tiene cinco apuestas correlacionadas al yen. Sección 5.
24. **¿Las mejores estrategias recientes siguen siéndolo o revierten?** Se zanja con el ledger. Decide
    cómo rota la cartera. De Lescarbeau contra Faulkner y Schwager. Sección 5.
25. **La duración mínima de la incubación, calculada.** Con la fórmula de Bailey y López de Prado, y la
    asimetría y curtosis de cada estrategia. Con las condiciones de retirada fijadas en el ledger antes de
    operar. Sección 5.
26. **Una tarjeta de hipótesis previa a cada build**, con justificación, signo esperado y mercados donde
    no debería funcionar. El paso 20 imprime la diferencia entre lo anunciado y lo corrido. Los estudios
    sobre prerregistro enseñan que, si no hay diff automático, casi todos cambian el plan sin decirlo.
    Sección 6.
27. **Métricas robustas con desplazamiento de ventana** para ordenar supervivientes: RAR% y R-cubed de
    Faith. Sección 3.
28. **Un nivel de mercados no relacionados** en el cruce de mercados, informativo. De Dennis. Sección 3.
29. **Guardar los casi supervivientes** para una prueba de confluencia. De Shaw y Hite. Sección 5.
30. **La ficha de estrategia y el cementerio del ledger en la ventana.** Curva underwater, peores
    drawdowns, mapa mensual, consistencia por ventanas, y cada búsqueda del ledger con el paso en que
    murió. Sólo interfaz, encargado esta noche a la sesión de la ventana. Sección 6.

## 3 · ¿Es real? Validación y estadística

Esta sección reúne todo lo que pregunta si una ventaja existe o la ha fabricado la búsqueda: contra qué nulo se compara, cuántas pruebas se hicieron de verdad, cuánta muestra hace falta, qué dice el fuera de muestra, qué trampas de datos inflan un backtest y qué miden realmente las métricas. Las tres ideas más valiosas, a mi juicio: **los monos seleccionados** (el nulo tiene que pasar por la misma selección que las estrategias de SQX, o la tasa de falsos positivos sale por debajo de la real), **los controles negativos de toda la cadena** (una familia placebo o un bloque de ruido metidos en la tubería completa, para medir cuánto "superviviente" fabrica la maquinaria de la nada) y **comprobar si la meseta predice de verdad el fuera de muestra**, porque Katz documenta estrategias rentables con todos los parámetros dentro de muestra y con ninguno fuera.

Abreviaturas de fuentes: Aronson = *Evidence-Based Technical Analysis*; Chan QT = *Quantitative Trading* (2008); Chan AT = *Algorithmic Trading* (2013); Katz = *Encyclopedia of Trading Strategies*; Fitschen = *Building Reliable Trading Systems*; Williams = *Long-Term Secrets to Short-Term Trading*; NF = *New Frontiers in Technical Analysis*; CMT = Kirkpatrick y Dahlquist, *Technical Analysis*; Katsanos = *Intermarket Trading Strategies*; COT Bible = Briese; Tharp = *Trade Your Way to Financial Freedom*; Faith = *Way of the Turtle*; Covel TF = *Trend Following*; Covel CT = *The Complete Turtle Trader*; Taleb = *Fooled by Randomness*; LTCM = Lowenstein, *When Genius Failed*; Elder = *The New Trading for a Living*; MW, NMW, SMW = los tres *Market Wizards* de Schwager (con el entrevistado entre paréntesis); web = notas de la búsqueda en la red.

### 3.1 · Nulos: contra qué comparar una estrategia

#### Monos seleccionados: el nulo tiene que pasar por la misma selección
**Fuente.** Aronson, p. 274-280, 293-296, 441-443; Katz, p. 296-300; web: Masters, permutación con selección (http://www.timothymasters.info/market-trading.html ; https://evidencebasedta.com/montedoc12.15.06.pdf).

**Qué dice.** El minero de datos no observa una media, observa el máximo de N medias, y el nulo correcto es la distribución de ese máximo. El mejor de 2, 10, 50 y 400 sistemas sin ventaja sobre 24 meses sale sesgado +8,5, +22, +33 y +48 %/año. En el caso de estudio de Aronson, el mejor de 6.402 reglas inútiles gana un 10,25 %/año: la p ingenua de una sola regla es 0,0005, la p correcta (White Reality Check y permutación) es 0,82. Unas 320 de las 6.402 pasarían un test del 5 % por puro azar. Katz generaba 10 secuencias de entradas aleatorias dentro de muestra, se quedaba con la mejor como si fuera un parámetro y la llevaba fuera de muestra: perdía 2.243 ± 304 $ por operación.

**Qué significaría aquí.** El encargo 9 (`studies/screening/falsePositives`, aún sin construir) empuja monos por la cadena, pero las estrategias de SQX llegan ya elegidas por una búsqueda genética en `build` y los monos no. Así la tasa de monos que pasan es solo una cota inferior. Arreglo sin importar nada a SQX: generar M monos en `build` con el mismo número de operaciones y la misma distribución de duraciones, quedarse con los K mejores por la misma métrica y filtros que usa SQX (K = tamaño del databank) y pasar esos K por `oos1` y la puerta. Repetir con varios M da la curva "supervivientes frente a tamaño de la búsqueda".

**Estado.** AMPLÍA (diseño del encargo 9; `engines/nulls` y la escalera del mono no sacan el nulo como "mejor de N") — **Tipo.** estudio — **Locura.** 1 — **Valor.** 5

**⚠ Contradice.** La población de monos del encargo 9 tal como está diseñada deja fuera la selección y por tanto infravalora la tasa de falsos positivos de la cadena (Aronson, p. 274-280, 441-443).

#### Correr la estrategia sobre mercados falsos (surrogados), no solo con entradas falsas
**Fuente.** Chan AT, p. 16-22, 37-38; Aronson, p. 160-161, 234-243; CMT, p. 297 (Brock, Lakonishok y LeBaron); Katz, p. 67; web: Masters (https://www.buildalpha.com/monte-carlo-permutation/), bootstrap estacionario por bloques (https://www.susanpotter.net/quant/bootstrap-methods-strategy-robustness/), IAAFT (https://arxiv.org/pdf/1806.02273), mercados sintéticos GAN (https://arxiv.org/pdf/2410.18897), importación de datos propios en SQX (https://strategyquant.com/doc/strategyquant/data/). En contra: Fitschen, p. 161-165; Faith, p. 199-205.

**Qué dice.** Un surrogado es una serie de precios falsa que conserva algunas propiedades del mercado real (distribución de rendimientos, colas, volatilidad agrupada) y destruye otras (la dependencia de la dirección). Chan probó una estrategia de momentum de 12 meses en el bono TU con tres nulos: el gaussiano la aceptaba al 99 %, el de fechas de entrada aleatorias (Lo et al., el equivalente a nuestro mono) no fue superado ni una vez en 100.000, pero 10.000 series sintéticas con la misma media, desviación, asimetría y curtosis la superaron 1.166 veces (p = 0,117, no significativa). "Cualquier distribución con curtosis alta favorece al momentum." Chang y Osler: el hombro-cabeza-hombro real perdía 0,25 % por 10 días y en historias de precios desordenadas 0,03 %. Brock-Lakonishok-LeBaron ajustan paseo aleatorio, AR(1) y GARCH, simulan series y corren la regla exacta. La web añade el bootstrap estacionario por bloques (conserva la volatilidad agrupada, pero hereda la deriva) y el IAAFT (conserva espectro y distribución). Los modelos GAN no capturan todos los hechos estilizados; mejor como universo de estrés que como verdad.

**Qué significaría aquí.** El mono aleatoriza las decisiones sobre el camino real; esto aleatoriza el mercado bajo la lógica fija. Una ventaja que también aparece en surrogados explota colas gruesas o la asimetría de la salida, no predictibilidad. Dos vías: en Python con el backtest que produce la skill `translate` (factible para las madres de los pasos 14-20, no para poblaciones), o importando N series surrogadas a SQX como símbolos propios y reusando la maquinaria del cross-market.

**Estado.** NUEVA (nada permuta barras hoy; el encargo 9 §1 lo aparcó porque no había motor fuera de SQX, y `translate` ya lo resuelve) — **Tipo.** estudio — **Locura.** 2 — **Valor.** 5

**⚠ Contradice.** Chan AT, p. 20-22: el nulo de entradas aleatorias puede ser el más débil para estrategias de tendencia; una estrategia puede batir a sus monos y vivir solo de colas gruesas. Las fuentes discrepan entre sí: Fitschen (p. 161-165) dice que los precios sintéticos por barajado iid "no valen nada" porque destruyen la autocorrelación negativa de rendimientos (coeficientes -0,07 a -0,09 durante unas dos semanas), la fuerte de los rangos (~-0,46 a 3-5 barras) y la correlación entre activos. La conclusión común: si se usan surrogados, que conserven esas estructuras (bloques, GARCH, IAAFT), nunca un barajado iid.

#### Controles negativos de toda la cadena: familias placebo
**Fuente.** Katz, p. 178-203; CMT, p. 452 (Yuan, Zheng y Zhu, 48 países); Tharp, p. 122-125; web: Dichev-Janes y Yuan-Zheng-Zhu (https://personal.lse.ac.uk/yuan/papers/lunar.pdf).

**Qué dice.** Los modelos lunares adaptativos de Katz perdían en la cartera completa dentro y fuera de muestra, pero algunos mercados sueltos parecían buenos en las dos muestras; un modelo de fulguraciones solares daba S&P y trigo rentables en ambas con ~80 % de "probabilidad de ser real" sobre 11-37 operaciones. Su estudio lunar previo en un solo mercado era muy rentable y no se replicó. Tharp cita estudios de tormentas geomagnéticas (Dow bajando de 2 días antes a 3 después). La web recoge ~3-5 %/año de menor rentabilidad en luna llena en bolsas.

**Qué significaría aquí.** Una plantilla cuya condición fija sea un reloj sin mecanismo (fase lunar, índice Kp de NOAA, un ciclo artificial de 23 o 37 días, etiquetas de día de la semana barajadas) se pasa por la tubería entera: build, `oos1`, puerta, cross-market. La fracción de estrategias placebo que sobreviven mide directamente la tasa de falsos positivos de la cadena, sobre todo para hipótesis de calendario. Si pasan más que alfa, alguna criba tiene fugas. Es la pareja de los controles positivos ya aceptados.

**Estado.** NUEVA (hay controles positivos con ventaja plantada; no hay familia placebo de punta a punta) — **Tipo.** estudio — **Locura.** 3 — **Valor.** 5

#### Un bloque de ruido en la ranura aleatoria: el precio de un grado de libertad falso
**Fuente.** NMW (Eckhardt), p. 48.

**Qué dice.** "Añade grados de libertad a un sistema y mira cuánto les sacas. Añade falsos y mira qué sacas. Prueba sistemas con sentido y sin él, con pocos parámetros y derrochadores." Regla práctica: 3-4 grados de libertad bien, 7-8 probablemente demasiados.

**Qué significaría aquí.** Instalar un bloque que sea ruido puro (un indicador calculado sobre un paseo aleatorio o sobre una copia barajada del precio) y hacer un build normal con él disponible en la ranura aleatoria. Medir cuántas veces lo elige el genético, cuánta aptitud dentro de muestra añade y cuánto de él sobrevive a cada paso. Es el control negativo del generador, medido con el generador del proyecto. El barrido de complejidad asociado está en 3.4.

**Estado.** AMPLÍA (controles positivos aceptados; añade el brazo negativo) — **Tipo.** generación — **Locura.** 2 — **Valor.** 5

#### Un peldaño más duro en la escalera: entrada aleatoria con una salida de tendencia canónica
**Fuente.** Tharp, p. 200-201, 236; Covel CT (Eckhardt), p. 79; SMW (Minervini), p. 94; Katz, p. 296-300; Williams, p. 212; web: Davey, prueba del mono por separado para entrada y salida (https://bettersystemtrader.com/113-how-good-are-your-entries-and-exits-really/). En contra: Fitschen, p. 155-157; Faith, p. 140-147.

**Qué dice.** Basso y Tharp: entrada a cara o cruz, siempre en mercado, stop de 3 veces la media exponencial de 10 días del ATR arrastrado desde el cierre, riesgo del 1 %, 10 futuros: rentable en el 80 % de las pasadas con un contrato y en el 100 % con el 1 % de riesgo, acierto del 38 %, con 100 $ de costes por contrato. Eckhardt: "si inicias al azar, lo haces sorprendentemente bien con un buen criterio de liquidación". Minervini: dardos sobre los 200 valores más fuertes con stop del 10 % ganarían dinero. Davey pide que al menos el 70 % de los monos lo hagan peor, por separado para la entrada (salida real) y para la salida (entrada real).

**Qué significaría aquí.** Si en un activo el nulo "entrada al azar + trailing de 3 ATR" ya gana (una prima de tendencia metida en la salida), un superviviente de SQX tiene que batir ese nulo, no solo al mono ingenuo; si no, su "ventaja" es la salida que cualquier moneda habría tenido. Sirve también como prueba de respuesta conocida para la atribución por canales de la escalera. Williams da otro caso de respuesta conocida: una entrada casi aleatoria (signo de la tendencia) con stop y objetivo 3R cuyo beneficio viene de la asimetría y la deriva; el mono con las mismas salidas debería reproducirlo.

**Estado.** AMPLÍA (escalera del mono de `studies/readings/monkey`) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 5

**⚠ Contradice.** Las fuentes chocan de frente. Fitschen (p. 155-157) repitió el experimento con 700.000 entradas aleatorias y esa salida: 0,000025 $ por operación, nada. El beneficio de Basso venía de estar siempre dentro: el stop tocado se convertía en entrada en sentido contrario, y ese "stop and reverse" solo ganaba 239 $/operación en 56 mercados. "Ninguna salida puede ganar dinero con una entrada aleatoria." Faith (p. 140-147), coautor del mismo sistema que Eckhardt, encontró que una entrada con ventaja y una salida por tiempo de 80 días batía a todas las salidas sofisticadas. Consecuencia práctica: en estrategias "siempre dentro" o que invierten con la señal contraria, la salida es la siguiente entrada, y la escalera puede atribuir al canal de mantenimiento una ventaja que es de entrada. Hay que marcar esas estrategias.

#### Mercado sintético de punta a punta como control negativo
**Fuente.** Aronson, p. 82-86, 97-100; web: Build Alpha, "construir sobre datos sintéticos" (https://www.buildalpha.com/synthetic-data-trading-strategies/), importación de datos a SQX (https://strategyquant.com/doc/strategyquant/data/).

**Qué dice.** Patrones, tendencias y "rachas calientes" aparecen de forma rutinaria en datos aleatorios; los expertos no distinguen gráficos reales de gráficos hechos con cambios de precio reales sorteados al azar (Roberts; Arditti y Siegel).

**Qué significaría aquí.** Construir un XAUUSD M1 falso remuestreando rendimientos M1 reales por bloques (destruye toda predictibilidad más allá del bloque, conserva volatilidad y forma de sesión), cargarlo en SQX como símbolo y correr una plantilla completa: build, OOS, puerta. Todo lo que sobreviva es por construcción un falso positivo. Da la tasa de descubrimientos falsos del conjunto build + puerta, que ningún nulo por paso da, porque la búsqueda genética sobre ruido es exactamente el sesgo de minería. El encargo 9 §1 lo vio impracticable porque un símbolo sintético pedía la GUI del maestro; la web dice que SQX importa datos propios desde su Data Manager.

**Estado.** AMPLÍA (idea 1 aceptada y encargo 9) — **Tipo.** estudio — **Locura.** 2 — **Valor.** 4

#### Nulo de filtros: quitar la misma fracción de operaciones al azar
**Fuente.** Katsanos, p. 227-230; Williams, p. 64, 73; NF (Erlanger), p. 94-116; COT Bible, p. 94-112.

**Qué dice.** Katsanos añadió a un cruce de medias en el DAX un filtro de disparidad con el Euro Stoxx: fuera de muestra, 51 operaciones y PF 1,93 pasaron a 26 operaciones y PF 4,18, beneficio neto de 58,9k a 94,8k. Williams: cada filtro bajaba el beneficio neto pero subía la media por operación y bajaba el drawdown. Erlanger apila cuatro filtros elegidos sobre un año de 30 valores y cada paso reduce N.

**Qué significaría aquí.** Todo filtro que mejora la media sobre menos operaciones tiene que batir a quitar el mismo porcentaje de operaciones al azar; si no, su ganancia es selección sobre la muestra. Esto ya existe en `engines/nulls/filter.py` y lo usa la ablación de `studies/readings/structure`. Lo nuevo es aplicarlo a los filtros post hoc que vienen: "el líder está de acuerdo" en lead-lag, COT, reglas de calendario, apagado antes de noticias. Katsanos propone justo eso como la forma más barata de probar la familia lead-lag: un filtro Python sobre las listas de operaciones de los supervivientes, sin CPU de SQX.

**Estado.** YA EXISTE (`engines/nulls/filter.py`, usado en `structure`) · AMPLÍA (a filtros post hoc sobre supervivientes) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 4

#### Nulo anidado: todo dato alternativo contra su gemelo hecho solo con precio
**Fuente.** COT Bible, p. 82-90, 124; libro de sentimiento FX, p. 68-83, 114-115.

**Qué dice.** La posición neta de los fondos en el COT va casi paralela al precio: los especuladores siguen tendencia y los comerciales la reflejan al revés. Klitgaard y Weir: el cambio semanal de la posición especulativa coincide con la dirección del FX en ~75 % de las semanas pero no predice la semana siguiente. Los risk reversals de opciones son en gran parte función del movimiento reciente; los titulares extremos siguen a los grandes movimientos por construcción.

**Qué significaría aquí.** Antes de aceptar un filtro COT, de sentimiento, de opciones o de titulares, la puerta corre el mismo filtro construido solo con precio (signo del rendimiento de 13 semanas, estocástico de precio a 3 años). Si el dato alternativo no bate a su gemelo de precio, es redundante. Probablemente ahorra un proyecto entero de integración de datos.

**Estado.** AMPLÍA (disciplina de nulos y controles aplicada a datos alternativos) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 4

#### Una celda de calendario se compara con el periodo que la contiene
**Fuente.** CMT, p. 174.

**Qué dice.** La fuerza de antes de Acción de Gracias desaparece al descontar la fuerza habitual de noviembre; los efectos de festivos quedan casi todos dentro de la variación aleatoria tras ese ajuste.

**Qué significaría aquí.** En el mapa condicional y en la familia de calendario, el nulo de una celda no es cero ni la media global, sino la media de su periodo padre: la hora contra la media de su sesión, el día de mes contra su mes, el día de la semana contra la deriva de la semana. Evita descubrir diez veces el mismo efecto amplio.

**Estado.** AMPLÍA (`studies/readings/conditionalMap`, familia de calendario) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 3

#### Coste cero para separar "sin información" de "información comida por costes"
**Fuente.** Aronson, p. 31.

**Qué dice.** Cuando se busca detectar información, los costes ocultan el valor de las reglas que invierten a menudo; el caso de estudio se prueba a coste cero. Para operar, los costes van siempre.

**Qué significaría aquí.** Una pasada de la escalera del mono con real y nulo a coste 0 distingue una familia muerta de una familia con información que se comen los costes. Esta segunda es candidata a un marco más lento o a un mercado más barato, no a la basura. `edgeCost` ya barre el coste; esto es el veredicto del nulo a coste 0.

**Estado.** AMPLÍA (`studies/readings/edgeCost`) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 2

#### ¿Distingue el ojo una curva real de una curva de mono?
**Fuente.** Aronson, p. 84-85; Taleb, p. 41-47; NMW, p. 56.

**Qué dice.** En la figura de Siegel (4 gráficos reales, 4 aleatorios) corredores y estudiantes de posgrado acertaron al nivel del azar. Taleb: no se puede ver un resultado realizado sin los no realizados. Un concursante que usó el pronóstico del paseo aleatorio batió a más del 95 % de cientos de participantes.

**Qué significaría aquí.** Un test ciego en la ventana: mezclar la curva OOS de una estrategia con curvas de pasadas nulas del mismo peldaño y ver si el dueño acierta. Requiere que la escalera guarde la curva de algunas pasadas, que hoy no guarda. El abanico permanente de curvas nulas detrás de la real es la parte de interfaz y pertenece a la sección de interfaz.

**Estado.** NUEVA (el nulo tiene que emitir curvas por pasada) — **Tipo.** estudio — **Locura.** 2 — **Valor.** 2

#### Estadísticas descriptivas que un paseo aleatorio ya reproduce
**Fuente.** Libro de sentimiento FX, p. 127-129.

**Qué dice.** EURUSD diario 1999-2006: el mínimo cae bajo S1 el 44 % de los días, el máximo supera R1 el 42 %, S2/R2 el 17 %, S3/R3 el 3 %.

**Qué significaría aquí.** Son estadísticas de rango, no ventaja; un paseo aleatorio con la misma distribución de rangos las reproduce. Su único uso es de prueba de respuesta conocida: comprobar que los bloques pivote de SQX y el remuestreo Python coinciden.

**Estado.** YA EXISTE (tests de respuesta conocida en `tests/`) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 1

### 3.2 · Deriva y referencias: ¿ventaja, o solo el oro subiendo?

#### Batir a la regla de manual de la misma familia, no solo al mono
**Fuente.** Aronson, p. 383-385; Covel TF (Welton), p. 15-16; Faith, p. 131-148; MW (Seykota), p. 77; NMW (Eckhardt), p. 52-53; NMW (Sperandeo), p. 106; Covel CT, p. 142; web: TSMOM, Moskowitz-Ooi-Pedersen (https://www.aqr.com/Insights/Research/Journal-Article/A-Century-of-Evidence-on-Trend-Following-Investing).

**Qué dice.** El índice MLM (cruce de media de 12 meses en 25 futuros) es la prima que cualquiera obtiene sin habilidad; la habilidad es lo que la supera. Welton construyó 120 modelos de tendencia (giros, rupturas, bandas, de 2 semanas a 1 año) y todos se comportaron casi igual en tres décadas: la ventaja está en la familia, no en el parámetro. Faith: seis sistemas de tendencia simples (canal ATR, Bollinger, Donchian 20/10 con filtro, Donchian con salida a 80 días, medias 100/350, triple media) dieron 29-58 % CAGR en 1996-2006 sobre 27 futuros, y el complejo no fue mejor que el simple. Seykota probó unas 100 variantes de cuatro sistemas simples en diez mercados antes de operar. Eckhardt acepta menos rendimiento a cambio de ser distinto de lo que usan los demás. Los Tortugas, ya independientes, operaban igual entre sí aunque decían haber evolucionado por separado.

**Qué significaría aquí.** Para cada superviviente, correr la familia de reglas de manual a la que pertenece (Donchian, medias, bandas y TSMOM con periodos reescalados a M30/H1/H4, mismos costes y ventanas) y decir dónde cae el superviviente en esa distribución y cuánto correlaciona con la mediana. Si un Donchian de dos parámetros iguala al superviviente fuera de muestra, la búsqueda genética solo añadió pruebas que deflactar. La correlación con reglas públicas es además un indicador de saturación: correlación alta, ventaja concurrida que decaerá antes.

**Estado.** NUEVA (las referencias son el mono y comprar y mantener; SPP y meseta responden "mejor que sus vecinos", nada responde "mejor que la regla de manual") — **Tipo.** estudio — **Locura.** 1 — **Valor.** 5

#### La referencia sin información es exposición por deriva, no cero ni comprar y mantener
**Fuente.** Aronson, p. 22-28 (fórmula p. 26; demostración en el apéndice, p. 475-476); Katsanos, p. 172-178; Williams, p. 14-15, 94-95; Chan AT, p. 22-24; NMW (Blake), p. 97; NMW (Sperandeo), p. 104-105. En contra del uso como veto: SMW (Galante), p. 51.

**Qué dice.** El rendimiento de un backtest es componente predictivo más sesgo de posición por tendencia neta del mercado. Una ruleta larga el 90 % de 7.000 días del S&P "gana" 7,31 %/año; larga el 60 %, 1,78 %/año, las dos sin ninguna habilidad. Referencia: ER = p(largo)·ADC - p(corto)·ADC. Atajo equivalente: restar a los log-rendimientos del mercado su media en la ventana y calcular la regla sobre la serie sin tendencia; así cualquier regla sin habilidad espera exactamente 0. Las señales se siguen calculando sobre la serie cruda, y vale para estrategias largo/plano. Williams: el 53,2 % de cierres alcistas es la base, no el 50 %. Chan: una estrategia solo larga que no bate a comprar y mantener en ratio de información no merece ni backtest. Blake: regresar el rendimiento anual de la estrategia sobre el del mercado; una beta grande es exposición. Sperandeo: comprar y mantener perdió dinero de 1896 a 1932 y de 1962 a 1974. Katsanos (p. 172-178): un sistema del SPY con p = 0,0002 contra cero tenía p = 0,216 contra comprar y mantener por operación.

**Qué significaría aquí.** La escalera del mono ya incorpora esto de forma implícita. Pero el SPA/StepM de `snoopingScreen` (paso 8A) y de `blindJoint` (paso 20) usan como única referencia comprar y mantener a igual riesgo. SPA de Hansen y StepM de Romano-Wolf son los tests que controlan el fisgoneo de datos al comparar muchas estrategias con una referencia. Añadir un segundo panel: P&L diario menos (posición de ese día por movimiento medio diario del segmento). Una resta.

**Estado.** AMPLÍA (`studies/screening/snoopingScreen/benchmark.py`, `studies/closing/blindJoint/benchmark.py`) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 4

**⚠ Contradice.** Comprar y mantener a igual riesgo no es siempre un listón más alto: en una ventana bajista una estrategia larga sin información expuesta una fracción f del tiempo tiene un Sharpe de aproximadamente √f por el de comprar y mantener, que es mayor que un número negativo, y sale con exceso positivo (Aronson, p. 22-28, p. 23: una referencia más alta vale, "pero no una menor"). El argumento de √f es inferencia del lector, no probada en datos del proyecto; una simulación de 10 líneas en una ventana bajista lo confirmaría. Galante añade otro matiz: una estrategia que rinde menos que el índice, combinada 1:1 con él, lo batió y redujo a la mitad sus dos peores drawdowns, así que usar "bate a comprar y mantener" como veto puede tirar diversificadores.

#### Betas ocultas: regresar el P&L sobre un factor de tendencia y unos pocos factores de mercado
**Fuente.** Covel TF, p. 13 (Fung y Hsieh); SMW (Shaw), p. 142; LTCM, epílogo p. 233-234; MW (Seykota), p. 80; web: réplica de índices CTA (https://qoppac.blogspot.com/2024/11/cta-index-replication-and-curse-of.html), posicionamiento de seguidores de tendencia (https://macrosynergy.com/research/estimating-the-positioning-of-trend-followers/).

**Qué dice.** Fung y Hsieh modelan el rendimiento de los seguidores de tendencia con factores tipo straddle retrospectivo. El índice SG Trend se replica con ~5 mangas de horizonte (1/3 rápida de 20 días, 2/3 de 125 y 500 días) y el alfa residual no es significativo. Shaw cubre los factores de mercado, divisa, tipos y los "derivados matemáticamente" siempre que no apuesta por ellos. La diversificación de LTCM era de forma, no de fondo: el mismo factor de liquidez movía todo. Seykota: la rentabilidad de la tendencia va por ciclos de popularidad.

**Qué significaría aquí.** En `blindJoint` y en exposición, un segundo benchmark: un factor de tendencia genérico del mismo instrumento (media de 3 Donchian, o las mangas de horizonte), con alfa y beta frente a él. Una estrategia explicada al 90 % por ese factor es beta de tendencia, barata de conseguir y concurrida. Extender a unos pocos factores construidos con barras que ya están en disco (dirección del subyacente, cambio de volatilidad, tendencia genérica, reversión genérica, carry, cesta USD). Y como variable de régimen, el rendimiento a 6-12 meses de un sistema de tendencia canónico ("el tiempo que hace para la tendencia"): si el OOS de un superviviente de tendencia se explica por buen tiempo, el veredicto debe decirlo.

**Estado.** AMPLÍA (`blindJoint` compara solo con comprar y mantener; `exposure` solo con su propio activo) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 4

#### ¿Es oro o es dólar? Partir XAUUSD en sus dos patas
**Fuente.** Katsanos, p. 113-115, 68-72.

**Qué dice.** De 2002 a 2005 el oro subió con fuerza en dólares pero fue lateral y acabó más bajo en euros: "la subida la causó un mercado bajista del dólar, no alcista del oro; la posición correcta era corto en dólar". El índice dólar se reconstruye con una fórmula ponderada de seis cruces (EUR 57,6 %).

**Qué significaría aquí.** Construir XAUEUR = XAUUSD / EURUSD y un dólar sintético con los cruces que ya hay, y regresar el P&L de cada estrategia de oro sobre (rendimiento del dólar, rendimiento del oro en euros). Si toda la ventaja está en la pata dólar, es una estrategia de FX disfrazada, y su familia de cross-market debería ser EURUSD/USDCHF, no la plata. La construcción del dólar sintético como fuente de datos pertenece a la sección de datos.

**Estado.** NUEVA — **Tipo.** estudio — **Locura.** 2 — **Valor.** 4

#### Métricas sin tendencia en cada celda del cross-market y la WFM, y partidas por signo de la deriva
**Fuente.** Aronson, p. 27-29, 123, 25-27.

**Qué dice.** Quitar la tendencia hace comparables reglas con distinto sesgo largo/corto; usar log-ratios, no porcentajes. Una regla larga probada solo en mercados alcistas es una generalización apresurada: gana la tendencia aunque no tenga poder.

**Qué significaría aquí.** El cross-market (9 mercados) y la WFM (30 celdas) comparan la misma estrategia en ventanas y mercados con derivas muy distintas; una estrategia de oro solo larga que pasa en plata en una ventana alcista prueba poco, y una celda que pasa solo por la deriva cuenta como aprobada en la regla de área de la WFM. Añadir las métricas recalculadas sobre barras sin tendencia como segunda columna. Además, el corpus XAUUSD es 100 % compras y el oro subió mucho en `build` y `oos1`: exigir el resultado de cada superviviente partido por subventanas en que el oro bajó.

**Estado.** AMPLÍA (`crossmarket` lee su nulo, pero las métricas de celda de SQX y de la WFM son crudas; `conditionalMap` parte por tercil de tendencia por operación, no por deriva de la ventana) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 3

#### Compararse con los pares, no con cero
**Fuente.** web: Liu, 1.726 estrategias estructuradas comercializadas (https://arxiv.org/abs/2604.18821).

**Qué dice.** Las estrategias vendidas por 10 instituciones con backtest pro forma se debilitan mucho en vivo frente a sus pares y a referencias externas; el backtest reflejaba sobre todo el régimen del factor común antes del lanzamiento.

**Qué significaría aquí.** Leer cada superviviente contra sus pares: los demás supervivientes y monos del mismo activo y periodo. Un superviviente que solo batió a cero cuando todas las estrategias de oro lo hicieron es régimen, no habilidad. Se enlaza con el monocultivo de la población (3.7).

**Estado.** NUEVA — **Tipo.** estudio — **Locura.** 1 — **Valor.** 3

### 3.3 · Pruebas múltiples: cuántas cosas se probaron de verdad

#### Calibrar el N efectivo por simulación en vez de contar grupos
**Fuente.** Aronson, p. 300-302 (figura 6.36), figura 6.55; Katz, p. 63-65, 227-255; web: diversidad de población en búsqueda evolutiva (https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/7016882).

**Qué dice.** La correlación entre reglas reduce el número efectivo de pruebas, pero poco hasta que es muy alta: el sesgo del mejor de 10, 100 o 1.000 "sigue alto hasta que las correlaciones se acercan a 1,0"; con ρ = 0,9 el mejor de 256 no es mejor que uno elegido al azar. Katz corrige con Sidak, p ajustada = 1 - (1 - p_mejor)^m: su mejor de 20 con p = 0,018 pasa a 0,31, pero como parámetros vecinos correlacionan, 20 pruebas equivalen a 5-10 independientes y la p ajustada queda en ~0,15; "la naturaleza de la dependencia entre pruebas nunca se conoce". En sus redes neuronales asumía N efectivo de 13.000-40.000 frente a 88.092 hechos, porque los adyacentes son redundantes.

**Qué significaría aquí.** `core/surface/trials.py` convierte, por ejemplo, 479 variantes en 21 pruebas independientes eligiendo el número de grupos que maximiza la silueta sobre √((1-ρ)/2). Si las variantes correlacionan a 0,5-0,8, el sesgo del máximo de N se parece al del N completo, no al de 21, y el Sharpe deflactado (el Sharpe corregido por cuántas cosas se probaron, cifra titular del ledger) sale halagado. Prueba: simular paneles nulos con la matriz de correlación observada (normal multivariante o bootstrap por bloques del panel real centrado en cero), medir E[máximo Sharpe] y buscar el N independiente cuyo E[máximo] coincide. Si difiere del conteo de grupos, usar ese N. La web añade contar "ideas distintas" por solapamiento de operaciones (el proyecto ya encontró 45 de 231 listas idénticas).

**Estado.** AMPLÍA (`core/surface/trials.py`, `ledger/trials.py` `population_n_eff`) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 5

**⚠ Contradice.** Un N efectivo por grupos de correlación probablemente es demasiado pequeño y halaga el Sharpe deflactado (Aronson, p. 300-302).

#### Un nulo correlacionado para el recuento de aprobados de la población
**Fuente.** Aronson, p. 300-302, 327-328.

**Qué dice.** Cuando se prueban muchas reglas, el nulo se genera en conjunto: cada permutación se aplica igual a todas las reglas, "es importante que se usen los mismos emparejamientos para todas las reglas, para preservar la estructura de correlación".

**Qué significaría aquí.** `engines/inference/excess.py` da exceso = observados - alfa·n sin dispersión. Con 45 supervivientes que son 13 estructuras (una tiene 24), los aprobados llegan en racimos y la varianza del recuento nulo es muchas veces la binomial; un exceso de unos pocos puede ser puro racimo. Correr la escalera con sorteos compartidos entre estrategias del mismo mercado (mismas barras de entrada aleatoria por índice de pasada) da al estadístico "cuántas estrategias tienen p < alfa" una distribución nula empírica, sin cambiar ninguna p individual. Igual para la colocación del cross-market.

**Estado.** AMPLÍA (`studies/screening/monkeyExcess`, `engines/inference/excess.py`) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 4

**⚠ Contradice.** El dueño decidió el 2026-09-25 que el test del mono sea por estrategia sin nulo poblacional. Es compatible con Aronson para nombrar estrategias, pero entonces el exceso se lee como si las estrategias fueran independientes (Aronson, p. 327-328).

#### Guardar todo lo que la búsqueda genera, y el sesgo de truncamiento de los estudios de población
**Fuente.** Aronson, p. 321-327; Taleb, p. 123-124.

**Qué dice.** Un test correcto de minería necesita el universo completo de reglas probadas y sus rendimientos diarios, no solo las ganadoras; "pocos sistemas de minería guardan esta información". Taleb: el estudio del gestor "Robin Hood" funcionaba porque la muestra solo tenía gestores que habían ido mal y se habían recuperado; la simulación correcta empieza con la población viva al principio.

**Qué significaría aquí.** Un build de calibración por familia, pequeño, sin filtros de aceptación y con un databank enorme, captura toda la población generada: el N real, la dispersión real de Sharpes para el Sharpe deflactado y un panel de rendimientos para un nulo del máximo sobre todo lo que produjo el genético. Su cociente con el databank filtrado es un factor de corrección para el ledger. Además, toda lectura de población sobre un databank (por ejemplo, correlación del Sharpe IS con el PF OOS) se hace sobre estrategias ya filtradas: una muestra truncada que atenúa o invierte correlaciones (paradoja de Berkson). `studies/screening/replication` ya lo reconoce y compara resultados en vez de correlaciones; falta ver lo que SQX rechazó.

**Estado.** AMPLÍA (`ledger/trials.py`; `snoopingScreen` "K es la cosecha"; `replication` ya evita correlaciones) — **Tipo.** proceso — **Locura.** 2 — **Valor.** 4

#### Las bifurcaciones del investigador también son pruebas
**Fuente.** Chan QT, p. 53, 109-110; Katz, p. 31-32, 356-359; Williams, p. 61-71, 147-156, 207; NF (Erlanger), p. 97-103; MW (Seykota), p. 82; Aronson, p. 132-141; web: "What survives honest evaluation?" (https://arxiv.org/abs/2608.27734).

**Qué dice.** Elegir entre apertura o cierre, dormir la posición o no, qué universo, a base de backtests repetidos sobre los mismos datos, es fisgoneo como los parámetros (Chan). "Cualquier resolución en la que se examina más de una solución y se elige la mejor es optimización de facto" (Katz). Williams elige subconjuntos de días de la semana y de meses sobre los mismos datos: 2^5 = 32 subconjuntos por lado, 2^12 para los meses. Seykota: si una política de modificación M mejora al sistema S, opera M; las capas superpuestas son sistemas. Katz arma una cartera de "625 % fuera de muestra" eligiendo por mercado después de haber publicado el fuera de muestra de cada uno. El artículo web: un agente LLM que registra toda evaluación y deflacta por número de pruebas no certificó ninguna estrategia descubierta en 2 universos, 2 modelos, hasta 100 candidatas y 5 pasadas.

**Qué significaría aquí.** El ledger cuenta los builds de SQX. Debe contar también: retoques humanos de una plantilla (idea, bloque, reejecución) como pruebas de la misma familia; qué activo, marco, sesión o tipo de salida se probó y se descartó; subconjuntos de días o meses como 2^k; toda capa superpuesta (filtro de volatilidad, apagado por calendario, dimensionado por curva de capital, cortacircuitos), especificada antes y probada como una estrategia; toda exclusión post hoc de un mercado o celda del cross-market o la WFM; y las propuestas del chat de plantillas. Si no, el Sharpe deflactado cuenta de menos.

**Estado.** AMPLÍA (`ledger`) — **Tipo.** proceso — **Locura.** 0 — **Valor.** 4

#### Las ideas de libros traen pruebas ocultas: marcar el origen y aplicar un recorte
**Fuente.** Aronson, p. 390-391, 449-451; Chan QT, p. 53-55; Taleb, p. 131-136; CMT, p. 51, 145-148, 173-174; Katsanos, p. 192-204; COT Bible, p. 130-133; NMW (Eckhardt), p. 49, 51, 55-56; SMW (Lescarbeau, Shaw), p. 107-108, 140, 168-169; MW (Dennis), p. 50; web: McLean-Pontiff (https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2156623), deriva nocturna que desaparece (https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/), Neely-Weller-Ulrich (https://ideas.repec.org/p/fip/fedlwp/2006-046.html).

**Qué dice.** Una regla publicada llega preseleccionada por una búsqueda de tamaño desconocido; meterla en la búsqueda propia hace su p incognoscible (la regla 9:1 de Zweig solo es significativa si Zweig no minó sus tres parámetros). El periodo desde la publicación es fuera de muestra gratuito "tan bueno como el papel", si no se optimiza nada en él. McLean-Pontiff: las anomalías rinden un 26 % menos fuera de muestra y un 58 % menos tras publicarse. El efecto enero, el efecto lunes, el sistema de avances y descensos de un día (de 100 $ a 884 M$ entre 1932 y 2000) y el empuje de Zweig murieron tras publicarse o por cambios de estructura; la deriva nocturna de Boyarchenko y otros pasó de ~3,7 %/año a casi 0 desde 2021. Katsanos publica 14 sistemas de oro todos rentables, optimizados sobre la muestra entera y la mayoría con menos de 30 operaciones; la Biblia del COT publica "35 de 35 mercados rentables" con el mejor par de medias por mercado. Eckhardt: el 98 % de lo que parece bueno en un gráfico no funciona; de ~50 sistemas comerciales revisados, uno tenía valor. Neely: las reglas de medias en FX pasaron de más de 3 %/año a ~0 en los 90. En sentido contrario, Dennis: "podrías publicar las reglas en el periódico y nadie las seguiría".

**Qué significaría aquí.** Esta misma búsqueda en libros alimenta la fábrica con ganadores ajenos. Cada plantilla derivada de un libro, foro o artículo lleva en el ledger `origen: literatura` y su fecha de publicación, recibe un N efectivo mayor o un recorte previo (esperar que pierda entre un tercio y la mitad fuera de muestra), sus parámetros se rederivan por enumeración en vez de copiarse, y los datos posteriores a la publicación sirven como OOS extra de la idea (no de los parámetros ajustados por SQX). El ledger puede medir así el decaimiento de ideas publicadas frente a propias. Ningún número de los libros entra como prior sin volver a probarse con el conteo del ledger.

**Estado.** NUEVA (el ledger registra búsquedas, no la procedencia de la idea) — **Tipo.** proceso — **Locura.** 1 — **Valor.** 4

#### Probabilidad de que un superviviente sea real, paso a paso
**Fuente.** Taleb, p. 113-115, 128-130, 159-160; NMW (Eckhardt), p. 49; Faith, p. xvii.

**Qué dice.** La precisión de un test no significa nada sin la tasa base: con un 5 % de falsos positivos y una enfermedad de 1 en 1.000, la respuesta correcta es ~2 % y menos de 1 de cada 5 médicos acierta. 10.000 gestores mediocres producen 184 historiales de cinco años ganadores. Eckhardt da una tasa base de ~2 % para ideas de gráfico. El embudo de los Tortugas (1.000 candidatos, 40 entrevistados, 13 elegidos, entre un tercio y la mitad fracasaron) se lee siempre contra el tamaño del grupo del que salió.

**Qué significaría aquí.** Las piezas ya existen por separado (BH al nivel alfa, curvas de potencia con ventaja plantada, rendimiento del ledger contra el mono por familia). BH, Benjamini-Hochberg, es el procedimiento que controla la proporción de descubrimientos falsos entre muchos tests. Sintetizarlas en una cifra por paso y familia: P(real | pasó el paso k) = potencia·base / (potencia·base + alfa·(1 - base)), con la base estimada del ledger (familias que replicaron en datos nuevos). Con una base de 1/500, una puerta al 5 % y 80 % de potencia da ~3 %; la página muestra cuántos pasos hacen falta para llegar al 50 %. Cada veredicto lleva el recuento del embudo en cada etapa.

**Estado.** AMPLÍA (BH, curvas de potencia y rendimiento del ledger aceptados por separado) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 4

#### El recorte de Sharpe de Harvey-Liu y el listón t > 3
**Fuente.** web: Harvey, Liu y Zhu (https://people.duke.edu/~charvey/Research/Published_Papers/P118_and_the_cross.PDF).

**Qué dice.** Con la cantidad de factores ya probados en la literatura, un nuevo factor necesita t > 3, no t > 2. Harvey-Liu convierten Bonferroni, Holm o BHY en un "Sharpe recortado" por estrategia.

**Qué significaría aquí.** Un número más en el certificado de cada superviviente, al lado del Sharpe deflactado: el Sharpe recortado por el número de pruebas del ledger. Da al dueño una cifra en unidades de Sharpe, no una probabilidad.

**Estado.** AMPLÍA (`ledger` tiene el Sharpe deflactado) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 3

#### Step-SPA en lugar de StepM para ganar potencia
**Fuente.** web: Hsu, Hsu y Kuan 2010 (https://homepage.ntu.edu.tw/~ckuan/pdf/Step-SPA-20090720.pdf).

**Qué dice.** El SPA por pasos es más potente que el Step-RC de Romano-Wolf (StepM) porque este conserva valores críticos de la configuración menos favorable.

**Qué significaría aquí.** El paso 20 usa StepM. Probar Step-SPA sobre los mismos paneles para ver si nombra estrategias que StepM deja escapar, lo que encaja con la preocupación por la potencia de la idea 2 ya aceptada.

**Estado.** AMPLÍA (`engines/inference/snooping/superior.py`) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 3

#### Intervalos conjuntos: no solo qué estrategia se nombra, sino cuánto puede valer como mucho
**Fuente.** Aronson, p. 446-448.

**Qué dice.** Con minería, los intervalos tienen que ser conjuntos. En su tabla 9.1, intervalos al 80 % que contienen a la vez el rendimiento real de las 6.402 reglas: el de la mejor va de -2,9 % a +23,5 %, cruza el cero.

**Qué significaría aquí.** `snoopingScreen` y `blindJoint` nombran estrategias con StepM. Convertir su valor crítico en una banda da la cota simultánea de cada estrategia: además de "no se nombra ninguna", "la mejor valdría como mucho X". Las cotas superiores son lo que justifica abandonar una familia para siempre.

**Estado.** AMPLÍA (`engines/inference/snooping/superior.py`) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 3

#### Multiplicidad dentro del mapa condicional
**Fuente.** Aronson, p. 99-100, 464.

**Qué dice.** Con 5.000 distritos censales por 80 cánceres, algunos distritos salen muy por encima de la media por azar, y los racimos en datos aleatorios invitan a historias causales. Densidad de datos: si 100 observaciones bastan en 2 dimensiones, hacen falta 1.000 en 3 y 10.000 en 4.

**Qué significaría aquí.** El mapa condicional cruza tercil de volatilidad, tendencia y día de la semana, 45 celdas; con unos cientos de operaciones casi todas las celdas tienen un puñado. Hoy solo lleva un aviso de comparaciones múltiples. Exigir un mínimo de operaciones por celda (y mostrar el n), leer una dimensión cada vez y dar una p por permutación a través de las celdas. Es justo donde nace de ruido un filtro "operar solo los martes".

**Estado.** AMPLÍA (`studies/readings/conditionalMap`, solo aviso) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 3

**⚠ Contradice.** El mapa condicional es una búsqueda de muchas celdas con solo un aviso; un aviso no impide que salga de ahí un filtro (Aronson, p. 99-100, 464).

#### El umbral de la puerta desde el coste de cada error
**Fuente.** Aronson, p. 233-234; Covel CT, p. 67.

**Qué dice.** Aronson: el falso positivo es el error caro, expone capital sin compensación; el falso negativo solo pierde una oportunidad, así que el test se inclina contra el tipo I. A los Tortugas les enseñaron lo contrario: mejor muchas pérdidas pequeñas que perderse una gran tendencia.

**Qué significaría aquí.** Las dos fuentes discrepan, y eso es útil: el coste relativo de rechazar una ventaja real frente a aceptar una falsa no es simétrico ni universal. En vez de un 5 % por convención, elegir los umbrales (q de BH, percentil del mono) a partir de un cociente de costes declarado y de las curvas de potencia con ventaja plantada. La postura actual del proyecto (puerta de un solo sentido, umbrales congelados) encaja con Aronson.

**Estado.** AMPLÍA (curvas de potencia aceptadas; `ledger/gate.py`, `thresholds.yaml`) — **Tipo.** proceso — **Locura.** 1 — **Valor.** 3

#### Corregir dentro de muestra, no corregir el fuera de muestra de una sola madre
**Fuente.** Katz, p. 45.

**Qué dice.** Estadísticos corregidos por pruebas múltiples para los resultados de optimización dentro de muestra; estadísticos normales para el fuera de muestra, que es una sola prueba de un sistema elegido antes. Descartar lo que no sea rentable fuera de muestra.

**Qué significaría aquí.** Apoya la puerta, con un matiz: `oos1` se aplica a una población de cientos de estrategias, así que no es una sola prueba y BH ahí es correcto; solo el `oos2` de una madre se lee sin corregir.

**Estado.** YA EXISTE (BH en la puerta; puerta de un solo sentido en `oos2`) — **Tipo.** proceso — **Locura.** 0 — **Valor.** 2

### 3.4 · Tamaño de muestra, complejidad y grados de libertad

#### Malos grados de libertad: un parámetro decidido por un puñado de operaciones
**Fuente.** NMW (Eckhardt), p. 48.

**Qué dice.** "Supón que un grado de libertad solo afecta a unas pocas tendencias enormes de los datos y por lo demás no cambia cómo opera el sistema. Al pegarse a rasgos accidentales de esa pequeña muestra de grandes tendencias, puede contribuir mucho al sobreajuste, aunque el número total de grados de libertad sea manejable."

**Qué significaría aquí.** Un diagnóstico nuevo entre SPP y profitShape: para cada parámetro, moverlo un escalón (la rejilla de SPP ya lo hace) y mirar qué operaciones cambian. Si la diferencia de P&L entre vecinos la llevan 3 operaciones o menos, o las del 5 % superior en valor absoluto, el parámetro es un "mal grado de libertad": su mejor valor lo han elegido unos pocos accidentes. Hacen falta las listas de operaciones de los vecinos, que la fábrica de variantes casi ya cosecha.

**Estado.** NUEVA — **Tipo.** estudio — **Locura.** 1 — **Valor.** 5

#### Grados de libertad por estrategia, contados frente al número de operaciones
**Fuente.** Chan QT, p. 52-53, 151-153; Chan AT, p. 4-7; Katz, p. 42-43; Tharp, p. 35-37; NMW (Eckhardt), p. 48; NMW (Hull), p. 141.

**Qué dice.** Chan: datos necesarios ≈ 252 por parámetro libre (modelo diario de 3 parámetros, 3 años), nunca más de ~5 parámetros contando umbrales, periodo de mantenimiento y ventanas; "un modelo con pocos parámetros pero muchas reglas está igual de fisgoneado". Katz: correlación corregida por contracción Rc = √(1 - (1 - R²)(N - 1)/(N - P)); unos años de datos diarios no sostienen ni 2-3 parámetros, docenas valen con miles de operaciones. Tharp: 4-5 grados de libertad para todo el sistema. Eckhardt: hay grados de libertad ocultos, estructuras que pueden adoptar formas alternativas; si se prueban varias, el sistema tiene otra oportunidad de ajustarse al pasado. Hull: la complejidad trae además errores de implementación.

**Qué significaría aquí.** Una columna en la puerta y en el ledger: grados de libertad de cada estrategia (parámetros numéricos más condiciones más elecciones estructurales de salida y operadores que el generador pudo hacer) frente a su número de operaciones, y una criba barata de operaciones por grado de libertad. Las estrategias de SQX con 8-12 parámetros sobre 150 operaciones son el caso del que avisa Katz. El Sharpe deflactado cuenta pruebas, no complejidad por estrategia: es un segundo eje.

**Estado.** NUEVA (la plantilla limita a una condición fija más una ranura, pero no hay recuento por estrategia) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 4

**⚠ Contradice.** Tharp (p. 35-37) pone el tope en 4-5 grados de libertad para todo el sistema; una estrategia SQX con condición fija, ranura aleatoria, salidas y sus parámetros puede pasarlo.

#### Fijar el tope de complejidad de la ranura con los datos del propio proyecto
**Fuente.** Aronson, p. 450-451, 456-462; Katz, p. 257-278; NMW (Eckhardt), p. 48; web: parsimonia en programación genética (http://fabian-kostadinov.github.io/2015/01/14/evolving-trading-strategies-with-genetic-programming-punishing-complexity/), Neely-Weller-Ulrich (https://www.sciencedirect.com/science/article/abs/pii/S0378426602003990).

**Qué dice.** Hsu y Kuan probaron 39.832 reglas con White Reality Check: las complejas eran el 8 % de las reglas pero el 82 % (188 de 229) de las significativas. La complejidad óptima se elige en un conjunto de prueba que queda sesgado, así que hace falta un tercero de validación. Katz: "limitar el número y la complejidad de las reglas parece la clave para controlar el demonio del sobreajuste" (máximo 3 reglas). Eckhardt propone un barrido de complejidad. La programación genética sufre "hinchazón" que falla fuera de muestra. Neely, en sentido contrario, ve que las estrategias complejas persisten más que las simples.

**Qué significaría aquí.** Con las cosechas existentes: curva de la métrica OOS frente a la complejidad de la estrategia (condiciones y parámetros, que la criba de redundancia ya lee de las claves del XML), y builds con tope de 2, 4, 6 y 8 condiciones. Si el OOS cae pasadas k condiciones, poner el tope de la ranura aleatoria en k. Es la versión propia de la regla 3-4 de Eckhardt. `oos2` actúa como el tercer conjunto.

**Estado.** AMPLÍA (la redundancia de la puerta lee estructura; no hay curva complejidad-OOS) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 4

#### Contar cuántas operaciones cambia cada condición
**Fuente.** Faith, p. 173-177, 194-195; NMW (Eckhardt), p. 49-50; NMW (Basso), p. 110.

**Qué dice.** Una regla "recortar el 90 % del tamaño con un 38 % de drawdown" subía el MAR de 0,74 a 1,17 pero se disparó una vez, al final del test; con umbral 37 % el sistema pasaba de +45,7 % a -0,4 %/año. Una regla estacional encontrada tras 4.000 pruebas actuaba en 10 ocasiones. "Si una regla cambió algo solo cuatro veces, no tienes base estadística." Eckhardt: no añadas una regla para algo que pasa menos de una vez al año. Basso: los desarrolladores hacen condiciones irrealmente restrictivas para perfeccionar el pasado.

**Qué significaría aquí.** En la ablación de `structure`, informar para cada condición de entrada o salida cuántas operaciones cambia su existencia o su resultado, y marcar como no estimables las que tocan menos de ~20 (o menos de una por año), sea cual sea su aporte. Añadir el par "operaciones eliminadas frente a PF ganado": eliminar muchas subiendo mucho el PF es una condición restrictiva ajustada. El genético añade a menudo condiciones pasajeras así.

**Estado.** AMPLÍA (`studies/readings/structure` ablaciona cada condición pero no cuenta las operaciones afectadas) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 4

#### Mínimo de operaciones derivado, no por costumbre
**Fuente.** Aronson, p. 296-300, 309-314, 394, 441-443; Fitschen, p. 8-19, 168-169; web: MinBTL de Bailey y otros (https://www.davidhbailey.com/dhbpapers/overfit-tools-at.pdf).

**Qué dice.** El número de observaciones es el factor que más pesa en el sesgo de minería: el mejor de 1.024 reglas sin ventaja sale sesgado ~84 %/año con 10 observaciones mensuales y menos del 12 % con 1.000; con 2 observaciones, elegir la mejor de 256 no es mejor que al azar; con muestra suficiente la penalización deja de crecer pasadas ~30 reglas. Con más de 6.000 días, reglas insignificantes salen "significativas". Fitschen: remuestreando 683 operaciones de oro, el error típico de la media sigue en ~100 $ con 300 operaciones frente a una media de 33 $; en 37 materias primas, ~75 $ incluso con 1.000. Las operaciones necesarias escalan con la varianza por operación: los sistemas largos necesitan muchas más. Bailey: con 5 años no caben más de ~45 configuraciones independientes antes de que el Sharpe máximo esperado de puro ruido sea 1.

**Qué significaría aquí.** Una calculadora en el informe del ledger y en el preflight: dado el N esperado de la familia y la dispersión del R por operación del activo, la cantidad de operaciones a la que E[máximo Sharpe de N estrategias nulas] cae por debajo del menor Sharpe que merece operarse; o dicho al revés, imprimir el techo de ruido de la búsqueda y avisar si el Sharpe de aceptación del build está por debajo. El filtro de operaciones mínimas del build es decisión del dueño; esto solo lo informa. Formulado como error típico relativo (error típico del R medio / R medio < k), un H4 de mantenimiento largo pide más operaciones que un M30.

**Estado.** AMPLÍA (`ledger/trials.py`; los filtros del build son del dueño) — **Tipo.** generación — **Locura.** 1 — **Valor.** 4

**⚠ Contradice.** Fitschen (p. 8-19, 168-169): "30 operaciones bastan" es falso; un mínimo de unos pocos cientos en estrategias H4 de un solo activo está, por su criterio, en territorio de sobreajuste.

#### Cuánto hay que esperar para poder verificar una estrategia
**Fuente.** NMW (Hull), p. 139-140; MW (Dennis), p. 51; Faith, p. 158-162; Aronson, p. 186-188.

**Qué dice.** Las primeras 50 apuestas de Hull al blackjack perdieron; calculó cuántas hacían falta para estar seguro de ganar a la larga. Dennis: menos de un año de resultados no dice nada. Faith: con entrada aleatoria y salida por tiempo, en solo 3,5 años (2003-2006) 17 de 100 pasadas aleatorias batieron el MAR 1,54 del mejor sistema real, y la mejor hizo 71,4 % con MAR 2,07. Aronson: la población de una regla es un "futuro práctico inmediato" finito.

**Qué significaría aquí.** Para cada superviviente, "operaciones hasta significancia" ≈ 4σ²/μ² (las que haría falta para t = 2 con su propia media y desviación por operación) al lado de las que tiene, y para el OOS en papel ya aceptado, la espera esperada en meses a su frecuencia de operación. Para las ventanas `oos1` y `oos2`, la fracción de monos que bate a cada superviviente: si supera el 5-10 %, la ventana es demasiado corta y el veredicto es "indecidible", no aprobado o suspenso. El MinTRL de Bailey y López de Prado (longitud mínima de historial) es la versión con asimetría y curtosis, y se trata en la sección de riesgo y vivo.

**Estado.** AMPLÍA (OOS renovable aceptado; `core/significance.py` tiene `min_track_record`) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 4

#### Lo que la muestra no ha visto: colas, regla de tres y drawdown que crece con los datos
**Fuente.** Taleb, p. 96-97; Tharp, p. 32; NMW (Eckhardt), p. 47-48; NMW (Trout), p. 62; NMW (J. Ritchie), p. 136.

**Qué dice.** Con una probabilidad pequeña de bola roja, lo que sabemos de su ausencia crece mucho más despacio que √n; "el mercado nunca bajó un 20 % en 3 meses" se puede refutar pero nunca verificar. Mandelbrot: la varianza de los cambios de precio podría ser infinita; la varianza muestral sigue creciendo con más datos, y octubre de 1987 era un suceso de "unas pocas veces por milenio" que ocurrió en una década. Cualquier estimación clásica del riesgo queda infravalorada. Un Monte Carlo que remuestrea rendimientos empíricos no puede generar una cola mayor que la peor de la muestra.

**Qué significaría aquí.** Para cada superviviente: con N operaciones independientes sin ninguna pérdida mayor de k R, la cota superior al 95 % de P(pérdida > k R) es ~3/N; decirlo como "puede perder más de 5R en hasta 1 de cada N/3 operaciones y los datos no lo descartan" y restar esa "expectativa de cola no vista". Añadir a profitShape un índice de cola (estimador de Hill) del P&L por operación y del diario: si alfa < 2, la maquinaria basada en Sharpe no es formalmente válida para esa estrategia y el veredicto debería apoyarse en tests de rangos. Mostrar el drawdown por subventanas de 1, 2 y 5 años para que se vea crecer: el máximo del backtest es un suelo, no una estimación.

**Estado.** NUEVA (profitShape mide concentración, no índice de cola) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 4

#### Muestra de un solo mercado frente a construir sobre la cesta
**Fuente.** Katz, p. 45, 80, 271-272; Fitschen, p. 24; Covel TF, p. xv, 254-255, 289; Abraham, p. 31; Tharp, p. 78, 316; web: robustez en modo universo, MinervaScore (https://arxiv.org/pdf/2608.23808), Build Alpha "biology-robust" (https://www.buildalpha.com/biology-robust-trading/).

**Qué dice.** Katz no optimizaba por mercado sino un solo juego de parámetros para toda la cartera, "porque un buen sistema debe operar varios mercados con los mismos parámetros"; optimizar por mercado sobreajusta, y la cartera multiplica la muestra. Sus soluciones del genético hacían 43 operaciones en 10 años en 36 mercados: estrategias de sucesos raros que solo se pueden juzgar en conjunto. Fitschen llama trampa de sobreajuste al paradigma de un gráfico y desarrolla sobre cestas de 37-56 mercados. Houthakker probó la tendencia en un solo contrato (trigo), vio años arriba y abajo y concluyó que no funcionaba. Vandergrift: pasar de 18 a más de 40 mercados con las mismas reglas cambió los resultados de forma drástica. MinervaScore exige que un solo juego de parámetros no pierda fuera de muestra en todos los miembros a la vez.

**Qué significaría aquí.** El proyecto construye en un activo y usa el cross-market después como filtro. La alternativa es un experimento, no un cambio: para familias que se esperan universales (tendencia, rupturas), meter una puntuación agrupada de una cesta relacionada en el objetivo del build (SQX permite comprobaciones de mercados adicionales dentro del build, o una reordenación Python con métricas agrupadas). Se pierden ventajas propias del activo; se gana muestra. También hace evaluables las estrategias de sucesos raros que la criba de operaciones mínimas tira por diseño.

**Estado.** AMPLÍA (`crossmarket` pasa de filtro a objetivo) — **Tipo.** generación — **Locura.** 1 — **Valor.** 4

**⚠ Contradice.** Katz (p. 80), Fitschen (p. 24), Covel TF (p. 254-255, 289) y Abraham (p. 31) sostienen que la muestra de un solo activo en H1/H4 es demasiado pequeña y que el mercado cruzado pertenece al objetivo, no solo a una repetición posterior.

### 3.5 · Fuera de muestra, walk-forward y estabilidad de parámetros

#### ¿Predice la meseta la supervivencia? Probarlo en el ledger, y acompañarla de la caída interna
**Fuente.** Katz, p. 45, 100-103; Faith, p. 163-172; MW (Dennis), p. 53; Covel CT (Parker), p. 74-75; Williams, p. 233-237.

**Qué dice.** Katz: "la tolerancia de parámetros no sirve como medida de robustez; muchos modelos muy robustos son muy sensibles a ciertos parámetros; los únicos árbitros son los tests estadísticos y sobre todo el fuera de muestra". Su contraejemplo: una ruptura de volatilidad con entrada límite, solo larga, rentable con todas las combinaciones de parámetros dentro de muestra (la peor +15,5 %/año, la mejor +53 %, p < 0,0002, corregida < 0,02), y fuera de muestra -14,6 %/año, "ninguna combinación la hacía rentable". Con filtro ADX, 99 de 100 combinaciones rentables dentro, -20,9 % fuera. Su lectura: no sobreajuste sino cambio del mercado; la ventaja se apagaba desde mediados de 1988, antes del OOS. A favor de la meseta: Faith (operar cerca del pico de una colina suave, sus vecinos baten a un valor arbitrario), Dennis (aceptar hasta un ~10 % peor dentro de muestra por un juego más central), Parker (cambiar de 50 a 51 días no debe importar) y Williams (cualquier longitud del canal de bonos funcionaba, "no importa cuál").

**Qué significaría aquí.** El proyecto se apoya en la meseta en varios pasos (SPP, nube de parámetros, "operar la meseta"). La meseta detecta sobreajuste a parámetros, no la no estacionariedad. Dos cosas baratas: (1) con el ledger como conjunto de entrenamiento, medir si la puntuación de meseta predice de verdad la supervivencia en `oos1` y `oos2`; (2) acompañar cada lectura de meseta de una prueba de caída dentro del propio `build` (pendiente del P&L por año, o primera mitad frente a segunda).

**Estado.** AMPLÍA (`studies/breakage/spp`, `studies/optimisation/cloud`) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 5

**⚠ Contradice.** "Operar la meseta" como garantía de robustez choca con Katz, p. 45 y 100-103: meseta perfecta dentro de muestra y colapso completo fuera.

#### Validar un perfil estacional antes de gastar CPU: correlación entre mitades
**Fuente.** NF, p. 86-94; Tharp, p. 91-99.

**Qué dice.** Un compuesto estacional se puede construir con datos aleatorios; se valida construyéndolo con la primera y la segunda mitad de la historia por separado y correlacionándolas (Cycle-R: SBUX 0,76; AXP 0,54 a 15 años frente a 0,66 con ventana optimizada de 5, que ya es selección). El "calor" de una zona es la fracción de compuestos móviles pasados en que esa zona también fue fuerte. Tharp: un solo día ("subió 13 de 14 años el 13 de abril") es minería; hay que exigir un racimo de fechas vecinas con la misma señal y una causa, y vigilar que un régimen dé la vuelta al patrón (soja brasileña 1980).

**Qué significaría aquí.** Antes de generar con cualquier familia de calendario o de sesión (hora de la semana, día hábil del mes, mes), calcular la correlación entre mitades del perfil sobre `build`, con un nulo por permutación (barajar años o semanas). Solo las familias con estabilidad significativa merecen CPU de SQX. Añadir la persistencia por celda (fracción de ventanas en que la celda tuvo el mismo signo) y una meseta sobre el eje de fechas (mover entrada y salida ±k días). No optimizar la ventana con esto, o contarla.

**Estado.** AMPLÍA (familia de calendario aceptada; ledger) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 5

#### ¿Se apaga la ventaja dentro del propio build?
**Fuente.** Chan QT, p. 24-25, 28, 52-53; Katz, p. 86-92; CMT, p. 173-174; NMW (Eckhardt), p. 53; SMW (Lescarbeau), p. 105, 107.

**Qué dice.** Chan: la mayoría de las estrategias iban mucho mejor hace 10 años, al menos en backtest; júzgalas por sus años más recientes; "más datos es más robusto" solo vale si el proceso es estacionario, y solo los últimos ~10 años sirven de verdad. Katz: la ruptura de canal por cierre mostraba el borde apagándose desde los 80, "los mercados se volvieron eficientes respecto a ellas". CMT: mostrar siempre la tendencia del efecto en el tiempo junto a su nivel. Eckhardt dice lo contrario sobre la ventana: los sistemas desarrollados solo con datos recientes están "débilmente sostenidos" porque hay menos datos. Lescarbeau: los sistemas que mejor fueron hace poco tienden a ir mejor en el futuro inmediato.

**Qué significaría aquí.** Una pendiente del Sharpe anual (o del R por operación anual) a lo largo del `build`, marcada cuando es negativa y significativa, antes de leer el OOS. `decay` compara IS con OOS y el CUSUM de profitShape busca una rotura; ninguno pregunta si la ventaja IS ya viene bajando año a año. Sobre la ventana: la discrepancia entre Chan y Eckhardt indica que no hay que acortar el build como reacción al decaimiento, sino medir la pendiente y dejar que el ledger decida.

**Estado.** AMPLÍA (profitShape rotura y CUSUM; `studies/screening/decay`) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 4

**⚠ Contradice.** Chan QT, p. 25, 52-53: "más datos no es más robusto" si el proceso no es estacionario; el proyecto construye sobre ventanas largas con costes fijos por segmento. Eckhardt (NMW, p. 53) respalda al proyecto en este punto.

#### Juzgar el fuera de muestra contra la banda de ventanas de igual longitud dentro de muestra
**Fuente.** Fitschen, p. 23-24; NMW (Seidler), p. 61.

**Qué dice.** Fitschen no hace ningún test fuera de muestra: un solo año OOS no tiene referencia (un año malo normal parece un fracaso; su ejemplo, un año de -5.000 $ dentro de la distribución histórica) y reservar datos empeora la escasez que causa el sobreajuste. Seidler: juzgar el P&L contra la distribución de ventanas de la misma longitud del propio backtest.

**Qué significaría aquí.** Leer el `oos1`, la WFM y el `oos2` contra la banda 5-95 % de las ventanas móviles de igual longitud dentro de muestra, no contra cero ni contra la media IS. Evita tirar estrategias buenas tras un año malo normal y aceptar las afortunadas.

**Estado.** AMPLÍA (lectura de WFM y `oos2`) — **Tipo.** proceso — **Locura.** 1 — **Valor.** 4

**⚠ Contradice.** Fitschen (p. 23-24) argumenta contra reservar `oos2` y leerlo como aprobado o suspenso. El contraargumento es que el proyecto busca entre miles de candidatos genéticos, donde el OOS es la única defensa contra el sesgo de selección, mientras Fitschen construye a mano pocos sistemas.

#### BRAC: reconstruir con el mismo procedimiento quitando el último año
**Fuente.** Fitschen, p. 19-24.

**Qué dice.** Construir, rehacer y comparar: registrar cada paso y regla de selección, cortar el último año, reconstruir con el mismo procedimiento y comparar el reconstruido con el original en el año retirado. Si se parecen, hay poco sobreajuste. En un sistema de medias en 37 materias primas cada paso volvía a elegir lo mismo (media de 100 días, filtro de 200, stop de 2.000 $); el mejor parámetro de su Aberration (80 días) siguió siendo el mejor 25 años.

**Qué significaría aquí.** Una prueba de estabilidad del procedimiento, no de una estrategia: repetir build + puerta + selección con el `build` acortado un año y ver si se vuelve a elegir la misma familia, madre o región de parámetros, sin gastar `oos2`. Es hermana de la varianza por semilla del generador ya aceptada, sobre el eje de los datos. Con el genético la reelección exacta es improbable: comparar a nivel de familia o meseta.

**Estado.** AMPLÍA (varianza por semilla aceptada) — **Tipo.** proceso — **Locura.** 1 — **Valor.** 4

#### La estructura de las operaciones no debe cambiar entre dentro y fuera de muestra
**Fuente.** CMT, p. 548.

**Qué dice.** IS y OOS deben diferir en rendimiento pero no de forma material en duración media, rachas máximas, peor operación y pérdida media; y hay que probar la "fragilidad" de una regla que nunca se dispara.

**Qué significaría aquí.** Una criba barata en la puerta: comparar la huella estructural entre `build` y `oos1` (operaciones por mes, barras medias, acierto, pérdida media en R, reparto largo/corto, distribución horaria de entradas) con tests de dos muestras (KS en duración, chi-cuadrado en el histograma horario). Una estrategia cuyo rendimiento aguanta pero cuya estructura cambia (opera tres veces menos, o todo el beneficio OOS viene de otra hora) no es la misma estrategia en OOS: acierta por la razón equivocada.

**Estado.** AMPLÍA (cribas baratas de la puerta; ablación de `structure`) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 4

#### ¿Cambió el mercado entre segmentos? Validación adversaria
**Fuente.** web: adversarial validation (https://arxiv.org/pdf/2112.10078).

**Qué dice.** Entrenar un clasificador que distinga barras u operaciones de un periodo de las de otro: un AUC cercano a 0,5 indica mismo régimen; un AUC alto, con la importancia de variables, dice qué cambió (nivel de volatilidad, spread, tendencia).

**Qué significaría aquí.** Una lectura por activo de "cambio de régimen entre `build` y `oos1`" antes de interpretar cualquier caída IS→OOS. Si el clasificador separa bien los segmentos por la volatilidad, la caída se explica por régimen y no necesariamente por sobreajuste.

**Estado.** NUEVA — **Tipo.** estudio — **Locura.** 1 — **Valor.** 3

#### Validación cruzada combinatoria con purga para todo lo que se ajuste
**Fuente.** web: CPCV (https://en.wikipedia.org/wiki/Purged_cross-validation ; https://towardsai.com/p/l/the-combinatorial-purged-cross-validation-method).

**Qué dice.** La validación cruzada combinatoria purgada (CPCV) genera muchos caminos de backtest y da una distribución del Sharpe en lugar de un solo camino, con purga y embargo para que las etiquetas solapadas no filtren información; de ahí sale la probabilidad de sobreajuste del backtest (PBO).

**Qué significaría aquí.** El proyecto ya tiene CSCV sobre variantes (`studies/optimisation/cscv`). La CPCV con purga aplica a todo lo que se ajuste con datos: el futuro metamodelo del ledger, un clasificador de metaetiquetado, un modelo que explique qué estados de mercado llevan la ventaja. Ninguno de ellos debería validarse con un corte simple.

**Estado.** AMPLÍA (`studies/optimisation/cscv`) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 3

#### Fechas de ruptura estructural registradas de antemano
**Fuente.** Chan QT, p. 91-92, 120; Chan AT, p. 24-25; Williams, p. 77-78.

**Qué dice.** La decimalización (2001) y el fin de la regla del uptick (2007) mataron o inflaron clases enteras de estrategias; esos cambios se anuncian, no hace falta predecirlos. Tras 2008 los volúmenes cayeron a la mitad y la reversión a la media sufrió. Los bonos T operaron distinto tras octubre de 1988 con las sesiones nocturnas; los viernes cambiaron cuando dejó de salir el informe de la Fed de los jueves.

**Qué significaría aquí.** Un calendario pequeño de eventos de estructura de FX y CFD (suelo del SNB en 2011 y su retirada el 15-01-2015, límites de apalancamiento de ESMA en agosto de 2018, eras de tipos negativos, Brexit, marzo de 2020, cambios del feed de Dukascopy). El CUSUM de profitShape busca roturas a ciegas; probar el cambio de media en fechas fijadas antes es un solo test, mucho más potente, y dice por qué murió una ventaja. También sirve para marcar operaciones en esos días (el EURCHF del 15-01-2015 es un relleno que ningún bróker honró).

**Estado.** AMPLÍA (profitShape rotura; calendario económico aceptado) — **Tipo.** datos — **Locura.** 1 — **Valor.** 3

#### Parámetros de nivel frente a parámetros de sincronía
**Fuente.** Katz, p. 201; Fitschen, p. 144-149.

**Qué dice.** En el modelo solar de Katz, mover el desplazamiento uno o dos barras empeoraba la pérdida de -52 $ a -2.000 $ por operación; Katz lo lee como una relación real de sincronía: "si no, pequeños cambios no tendrían efecto". Fitschen: las entradas al 23,6 % de retroceso parecían buenas, pero el barrido mostró el pico en 21 %, no en el número de Fibonacci; "los números son solo números".

**Qué significaría aquí.** La lectura de SPP debería distinguir parámetros de nivel (periodos, umbrales, donde se espera meseta) de parámetros de sincronía (desfases de evento, hora de sesión, retardo de lead-lag), donde un pico puede ser la firma de una ventaja genuina y un perfil plano significa que el parámetro no importa. Y para bloques con constantes "especiales" (Fibonacci, números redondos, 50 %), barrer alrededor: si el valor especial no lo es, se trata como un parámetro cualquiera.

**Estado.** AMPLÍA (reglas de lectura de SPP) — **Tipo.** estudio — **Locura.** 2 — **Valor.** 3

#### Walk-forward correlation en los dos sentidos
**Fuente.** Williams, p. 24-27.

**Qué dice.** Soja 1975-87: el mejor par de medias (5/25) ganó 40k; en 1987-98 perdió 9,1k con 28,6k de drawdown. El mejor par del segundo periodo (25/30) aplicado al primero perdió 28,7k. "El mejor enfoque cíclico nunca se acerca al mejor en el siguiente test."

**Qué significaría aquí.** Apoya la WFC (rango IS frente a rango OOS de las tuplas de parámetros) y "operar la meseta". Extra barato: intercambiar los papeles de `build` y `oos1` y ver si la correlación de rangos es simétrica.

**Estado.** YA EXISTE (WFC, CSCV/PBO, SPP) · AMPLÍA (sentido inverso) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 2

#### Detector de acantilados y lectura del vecindario con una métrica de riesgo
**Fuente.** Faith, p. 163-176, 196-197.

**Qué dice.** Grandes cambios de resultado con cambios mínimos de parámetro son sobreajuste; las superficies buenas parecen colinas. Optimizar da parámetros con más probabilidad de ir bien y un backtest con menos probabilidad de repetirse: el pico sobrepredice. Moviendo el óptimo de Bollinger (350 días, salida -0,8) a (250, 0,0), el RAR% pasa de 59 a 58 pero el R-cúbico de 3,67 a 2,18.

**Qué significaría aquí.** Añadir a la salida de SPP una estadística de "salto máximo entre celdas adyacentes" para que los acantilados sean un número. Leer el vecindario con una métrica de riesgo robusta, porque el rendimiento apenas se mueve mientras el perfil de riesgo se hunde. Informar el recorte esperado como (pico - media de la meseta) al lado de la métrica IS.

**Estado.** YA EXISTE (SPP, nube de parámetros) · AMPLÍA (estadística de acantilado, recorte) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 2

#### Rejillas geométricas de parámetros
**Fuente.** Aronson, p. 398; Katz, p. 257-278.

**Qué dice.** Las ventanas de la ruptura de canal del caso de estudio son 3, 5, 8, 12, 18, 27, 41, 61, 91, 137, 205 (razón ~1,5): la sensibilidad de una ventana es aproximadamente proporcional a su logaritmo. El genético de Katz usaba una escala sesgada para buscar los periodos cortos tan finos como los largos.

**Qué significaría aquí.** En SPP y la fábrica de variantes, pasos geométricos dan un vecindario igual en periodos cortos y largos; los pasos aritméticos sobremuestrean los largos e inflan la "meseta" ahí. Comprobar cómo muestrea SQX los rangos de periodos.

**Estado.** AMPLÍA (`studies/breakage/spp`, `engines/variants`) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 2

#### Los pliegues de walk-forward dan una varianza; el fuera de muestra se gasta una vez
**Fuente.** Aronson, p. 316-319; Katsanos, p. 150-151, 198, 221, 232-250; NMW (M. Ritchie), p. 128.

**Qué dice.** Con pliegues de prueba no solapados se obtienen estimaciones OOS independientes y un intervalo; el OOS "se pierde en cuanto se usa una vez", reduce los datos para minar y el corte es arbitrario. Katsanos reserva un tercer conjunto porque el de prueba reusado durante el genético "no es un verdadero fuera de muestra". M. Ritchie: el software que recomendaba reoptimizar cada semana "ajustaba el programa a la semana pasada".

**Qué significaría aquí.** Apoyo a la WFM y a la puerta de un solo sentido en `oos2`, y a los tres segmentos.

**Estado.** YA EXISTE (`studies/optimisation/wfm`, `ledger/gate.py`) — **Tipo.** proceso — **Locura.** 0 — **Valor.** 1

**⚠ Contradice.** Katsanos (p. 150-151, 198, 221, 233) defiende reoptimizar periódicamente los coeficientes intermercado (la pendiente oro-dólar pasó de -0,29 a 15 años a -0,57/-0,62 a 3). Para estrategias con una beta entre mercados, la salida compatible con el proyecto es calcular la beta en ventana móvil dentro del indicador, "sin optimización, coeficientes por la fórmula" (p. 198), nunca una constante ajustada.

### 3.6 · Transferencia: otros mercados, otros marcos, otros cortes de barra

#### Historias alternativas desplazando los límites de las barras
**Fuente.** Taleb, p. 26-29, 41-47; web: Build Alpha "Vs Shifted" y test de ruido (https://www.buildalpha.com/robustness-testing-guide/ ; https://www.buildalpha.com/noise-test/), DST y hora del servidor (https://www.mql5.com/en/forum/443398/page2), pruebas de robustez de SQX (https://strategyquant.com/doc/strategyquant/types-of-robustness-tests-in-sqx/).

**Qué dice.** Taleb: juzgar un resultado por el coste de las historias alternativas que podían haber ocurrido, no por el camino realizado. Build Alpha reconstruye las barras desplazadas unos minutos (M30 empezando en :05, etc.) y vuelve a operar la estrategia. La web recuerda que las barras H4/D1 de Dukascopy (UTC) no coinciden con las del bróker de MT5 (cierre de Nueva York, con cambio de hora).

**Qué significaría aquí.** La historia alternativa más barata y honesta para una estrategia de barras es el mismo mercado con otros límites de barra: H4 desplazadas 1, 2 y 3 horas, H1 15, 30 y 45 minutos, M30 10 y 20 minutos, todo desde el M1 que ya está en disco, y la estrategia sin tocar. Una ventaja que solo existe con barras alineadas a las 00:00 es un artefacto de un camino (o del reloj del bróker) y morirá el día que la hora del servidor en vivo sea distinta. No baraja operaciones, así que no choca con la postura del dueño sobre el bootstrap. SQX ya perturba el inicio (`MCR 1 Bar`, RandomizeStartingBar) y el OHLC (`MCR 7 OHLC`, que es el test de ruido de Build Alpha), pero ninguna tarea mueve los límites de las barras. El caso concreto del cambio de hora y la hora del bróker pertenece a la sección de costes y ejecución.

**Estado.** NUEVA (crossTF reescala periodos, SPP perturba parámetros, nada perturba la alineación de barras) — **Tipo.** estudio — **Locura.** 2 — **Valor.** 5

#### El cross-market es un aprobado de grupo, no un selector de mercados
**Fuente.** Katz, p. 99, 107; Faith, p. 49-51, 213-219; Covel TF, p. 289.

**Qué dice.** Katz: los mercados con mejores resultados dentro de muestra no son los mejores fuera; en todos sus tests de ruptura la correlación entre el beneficio IS y OOS de cada mercado fue solo 0,15; la elección por grupo (divisas, petróleos) aguantaba, la elección por mercado no. Faith: dentro de una clase, las diferencias entre mercados son sobre todo azar; excluir el café en 1985 por malos resultados costó la mayor operación de los Tortugas (+280 % de la cuenta), y el cacao dio 17 pérdidas seguidas antes de +55.903 $. Las divisas y tipos tienden más limpio, los mercados especulativos (oro, plata, crudo) menos, y los índices agregados son los más difíciles para la tendencia.

**Qué significaría aquí.** Leer el cross-market como aprobado o suspenso del agregado del grupo (fracción de mercados positivos, t agrupado, conteo de signos), no como herramienta para elegir en qué mercados operar un superviviente. Fallar en 1-2 de 9 es lo esperado. Agrupar el rendimiento del ledger por clase (FX, metales y Brent, índices) además de por mercado, y comprobar con datos propios la persistencia IS→OOS por mercado correlacionando el `oos1` por mercado con el `oos2` más adelante.

**Estado.** AMPLÍA (`studies/transfer/crossmarket`) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 4

**⚠ Contradice.** Si el resultado del cross-market se usa para elegir mercados, esa selección tiene poder predictivo casi nulo (Katz, p. 99, 107; ρ = 0,15); y si el veredicto exige pasar en la mayoría de mercados individuales, rechazará ventajas reales (Faith, p. 213-219).

#### Un nivel de mercados no relacionados
**Fuente.** MW (Dennis), p. 54.

**Qué dice.** "Podría operar sin saber el nombre del mercado. En nuestra investigación, si un sistema no funciona para bonos y para soja, no nos interesa."

**Qué significaría aquí.** El cross-market usa 9 mercados relacionados. Dennis era más estricto: una estrategia de oro probada en EURUSD, Brent y un índice, con parámetros en unidades de ATR para que se trasladen. Una estrategia que solo funciona en su grupo puede ser un ajuste al grupo, o un efecto de grupo genuino, y entonces hay que decirlo. Añadir un nivel "no relacionado", informado aparte y sin ser criba dura.

**Estado.** AMPLÍA (`crossmarket`) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 4

**⚠ Contradice.** La transferencia solo a mercados relacionados es una prueba más débil que la de Dennis (MW, p. 54).

#### Si la ventaja solo se traslada mientras los mercados correlacionan, es la misma operación
**Fuente.** Katsanos, p. 25-26, 40-44, 87-95, 285-292.

**Qué dice.** La correlación anual S&P-Nikkei fue de -0,22 a 0,84; S&P-DAX de -0,52 a 0,97; la de bolsa y bonos cambia de signo en crisis; S&P-yen pasó de positiva a negativa en 2005 con el carry trade. "Mira siempre la tasa de cambio de la correlación antes de operarla." La relación yen-bolsa solo apareció con el régimen de carry.

**Qué significaría aquí.** En el cross-market, informar la correlación de cada mercado de la familia con el principal en `build`, `oos1` y `oos2`. Una ventaja que solo se traslada mientras la correlación es alta es la misma operación, no un segundo mercado. Y una relación entre mercados que existe solo en `build` es un régimen, no una ventaja. Como variable del mapa condicional, el régimen de correlación móvil con el líder de la familia.

**Estado.** AMPLÍA (`crossmarket`, `conditionalMap`) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 4

#### ¿Es la celda de construcción la mejor de todo el mapa mercado por año?
**Fuente.** NMW (Schwager sobre Basso), p. 109-110.

**Qué dice.** Un sistema de dos condiciones publicado en un artículo superaba al complejo de Schwager; probado en 25 mercados por 10 años, el ejemplo del artículo era la mejor de 250 celdas mercado-año, y 17 de los 25 mercados perdían tras costes en la década.

**Qué significaría aquí.** Pintar cada superviviente como mapa de calor mercado por año (9 mercados por todos los años, marcando `build` y `oos1`) y calcular el rango de la celda de construcción entre todas. Si el activo y los años en que se construyó son la mejor celda, la "ventaja" es el ejemplo bien elegido por construcción. Los números ya los produce el cross-market; el rango es un número nuevo trivial.

**Estado.** AMPLÍA (`crossmarket`) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 3

#### Una señal validada a un horizonte no vale a otro sin revalidar
**Fuente.** MW (Gelber), p. 169, 171.

**Qué dice.** Los clientes perdían porque operaban a día vista con una investigación de más largo plazo; la investigación acertada usada a otro horizonte pierde.

**Qué significaría aquí.** Una variable de contexto validada a escala diaria no se importa como disparador H1 sin revalidarla a ese horizonte. El crossTF comprueba el sentido contrario (de rápido a lento).

**Estado.** YA EXISTE (crossTF, en el otro sentido) — **Tipo.** proceso — **Locura.** 0 — **Valor.** 1

### 3.7 · Trampas: mirar el futuro, datos que mienten y selección escondida

#### Alineación de dos símbolos: un líder que cierra más tarde filtra el futuro
**Fuente.** Katsanos, p. 92, 102, 169, 234.

**Qué dice.** La correlación diaria S&P frente a DAX o Nikkei no tiene sentido si no se retrasa el S&P un día, porque cierra 4,5 horas después de Europa. Aun así, en su sistema del FTSE Katsanos ejecuta "el mismo día al cierre" usando cierres del CAC 40, cuyos futuros cerraban más tarde. Un indicador de un segundo mercado comparte además los errores de datos de ese segundo feed.

**Qué significaría aquí.** En todo backtest con dos símbolos sobre CFD de 24 horas, la convención de marca de tiempo (apertura o cierre) de los dos feeds tiene que coincidir al segundo, y una barra H4 o diaria del líder tiene que estar completa antes de que abra la barra operada que la usa. El M1 de Dukascopy está en UTC y alineado; el riesgo está en cómo SQX trata un segundo gráfico con otras sesiones o festivos, en el remuestreo Python (etiqueta a derecha o izquierda) y en feeds de bróker con otra zona horaria. Una prueba unitaria para el estudio lead-lag: desplazar el líder +1 barra y comprobar que la ventaja desaparece si era fuga contemporánea; desplazarlo -1 y comprobar que no explota. La calidad del feed tiene que cubrir también el líder y la alineación: una barra M1 que falta en el líder crea una divergencia falsa.

**Estado.** NUEVA — **Tipo.** estudio — **Locura.** 0 — **Valor.** 5

#### Rendimientos solapados fabrican un lead-lag que no existe
**Fuente.** Katsanos, p. 117-123, 133-136.

**Qué dice.** Desplazando el cambio semanal (5 días) del oro frente a mineras, plata, CRB y dólar salen correlaciones "adelantadas" de 0,25 a 0,59 a 1-4 días (mineras frente a oro r = 0,589 a -1), y el autor concluye que las mineras adelantan al oro. La misma prueba con rendimientos diarios no solapados se hunde: mineras a -1 r = 0,092, plata 0,014, dólar -0,025, CRB 0,033. Una ventana de 5 días desplazada 1-4 días comparte 4-1 días consigo misma: la curva es el núcleo triangular del solapamiento de la correlación contemporánea 0,68. En su tabla intradía por tramos, adelanto y retraso valen ~0,65 en todas las filas, la firma simétrica del mismo artefacto; la asimetría real es 0,005-0,012.

**Qué significaría aquí.** Todo estudio lead-lag mide la correlación cruzada con rendimientos no solapados a la barra que se opera (M30/H1), o con errores HAC/Newey-West, y compara la r retrasada con la que implicaría el solapamiento de la contemporánea. Primera comprobación del estudio `leadlag`. El diseño del estudio en sí pertenece a la sección de hipótesis.

**Estado.** NUEVA (salvaguarda para la familia lead-lag aceptada) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 5

**⚠ Contradice.** El ejemplo que motiva la familia lead-lag en `docs/AgentPDFs/ideas-de-edge-2026-09-26.md` ("el oro sigue al dólar") es contemporáneo, no un adelanto: con rendimientos diarios 1992-2006, oro-dólar r = -0,313 a lag 0 y -0,025 a 1 día (Katsanos, p. 123, tabla 7.4).

#### Datos publicados con retraso: la clave es la hora de publicación, no la fecha de referencia
**Fuente.** COT Bible, p. 36, 128-134, 274-277; Aronson, p. 29-30; Katz, p. 4; web: COT de la CFTC (https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm).

**Qué dice.** Las posiciones del COT se tabulan al cierre del martes y se publican el viernes a las 15:30 ET (semanal desde octubre de 2000; antes, publicaciones dobles alternas con 3 o 10 días de retraso). "Cuando trabajas con las fechas reales de publicación descubres que el retraso importa, y mucho": su sistema COT es rentable en 2000-2007 y solo marginal antes. "Los tests que tomaban posición en la apertura siguiente a una señal COT antes de 2002 no son hipotéticos, son imaginarios." Los ficheros públicos solo llevan la fecha de compilación, los festivos movieron publicaciones y las correcciones solo se publican hasta la siguiente. Aronson: la señal al cierre se ejecuta en la apertura siguiente, y los datos con retraso (efectivo de fondos, 2 semanas) se retrasan a su disponibilidad real. Katz: volumen e interés abierto se publican al día siguiente; usarlos el mismo día da "un sistema fabuloso pero imposible".

**Qué significaría aquí.** Para barras OHLC ya está resuelto (la convención de relleno se mide por estrategia y reconcilia a 0,999985). Para toda familia nueva de datos (COT, calendario económico, sentimiento, volatilidad implícita), la unión es marca de publicación + 1 barra, con una prueba unitaria que asegure que ninguna barra anterior a la publicación ve el valor de la semana. COT solo desde 2002. Cuando se construya, va como tarjeta de knowhow.

**Estado.** YA EXISTE (para barras, `engines/market/calibrate.py`) · NUEVA (para datos externos) — **Tipo.** datos — **Locura.** 0 — **Valor.** 4

#### Prueba de truncamiento y desplazamiento de una barra en los dos sentidos
**Fuente.** Chan QT, p. 51-52, 59; Tharp, p. 37; NMW (Eckhardt), p. 49; Williams, p. 16-22; web: prueba de retraso de señal (https://mikeharrisny.medium.com/look-ahead-bias-in-backtests-and-how-to-detect-it-ad5e42d97879), GDELT con Sharpe 5,87 (https://arxiv.org/pdf/2505.16136).

**Qué dice.** Chan: correr el backtest con todos los datos y guardar posiciones; cortar los últimos N días y repetir; las dos listas tienen que coincidir exactamente en el tramo común, o el programa mira el futuro. Tharp: usar información disponible solo después (el cierre de hoy para operar hoy) da resultados "demasiado buenos". Eckhardt: un sistema de estocástico precioso en papel perdía por ordenador porque el panel del indicador estaba desalineado un día con el precio, y como las señales se agrupan en movimientos rápidos, una barra de desfase da la vuelta a un movimiento de 500 puntos. Williams: el mínimo "con mínimos más altos a ambos lados" es mirar el futuro; la confirmación causal es romper el máximo de la barra del mínimo. La web: un artículo de tono de noticias GDELT con Sharpe 5,87 es una lección de fuga en sí mismo; una ventaja real se degrada suave con el retraso, una fuga se hunde.

**Qué significaría aquí.** `entryQuality/delay.py` ya mide lo que se pierde entrando d barras tarde, y el motor de evaluación de `sqx-custom-block` marca átomos con desplazamiento 0. Falta: (1) el desplazamiento de una barra ANTES como detector de fugas o de desalineación SQX-Python (si adelantar mejora muchísimo, hay un error de retardo en un bloque); (2) una prueba en `tests/` que corra cada clasificador de estado (terciles del mapa condicional, etiquetas de régimen) con barras completas y truncadas y exija etiquetas idénticas en el tramo común; (3) para bloques de SQX, retestear con la ventana acabando N días antes y comparar listas de operaciones; (4) un detector de "demasiado bueno" que mande a revisión de código cualquier resultado extremo.

**Estado.** AMPLÍA (`studies/readings/entryQuality/delay.py`; motor de `sqx-custom-block`) — **Tipo.** proceso — **Locura.** 0 — **Valor.** 4

#### Fugas en la elección del universo y de los umbrales
**Fuente.** Fitschen, p. 273-276.

**Qué dice.** Una estrategia de pares elegía los pares por correlación > 0,4 en toda la historia: los que luego se descorrelacionaron quedaban fuera; rehecha bien, la ventaja desapareció. Un rasgo que usaba el beneficio de las 10 últimas operaciones incluía operaciones aún abiertas. "Si los resultados mejoran de forma espectacular al hacer algo, examínalo de cerca."

**Qué significaría aquí.** Auditoría barata: cómo se eligieron los 9 mercados relacionados de cada activo y los cortes de volatilidad o régimen. Si se eligieron por correlación o cuantiles de todo el periodo, `oos2` incluido, hay fuga en todas las lecturas que dependen de ellos. Los terciles se ajustan solo en `build`; el metamodelo del ledger usa solo información cerrada en el momento de decidir. Es extender la puerta de un solo sentido de las ventanas de datos a la selección de universo y umbrales.

**Estado.** AMPLÍA (puerta de un solo sentido) — **Tipo.** proceso — **Locura.** 0 — **Valor.** 4

#### ¿Seleccionó la puerta un régimen? Monocultivo de la población
**Fuente.** Taleb, p. 74, 80; LTCM, epílogo p. 233-234; NMW, p. 58.

**Qué dice.** Los compradores de caídas fueron los más aptos de 1992-1998 por rasgo, no por habilidad; "en un momento dado, los operadores más rentables son probablemente los mejor adaptados al último ciclo"; un cambio de régimen borra la cohorte entera. Los Tortugas, "independientes", fallaron todos juntos en 1991.

**Qué significaría aquí.** Tras la puerta, describir la población superviviente por rasgos: reparto largo/corto, duración, entrada de reversión o de ruptura, hora del día, y correlación de la curva de cada superviviente con la tendencia del precio en `build`. Si el 85 % de los supervivientes de oro son compradores de caídas con sesgo largo construidos en un tramo alcista, la población es una sola apuesta. Informar el número efectivo de rasgos independientes (no solo la redundancia de curvas) y marcar el monocultivo. Complementa el canal de dirección de la escalera.

**Estado.** AMPLÍA (la criba de redundancia mira correlación de curvas, no exposición común al régimen del build) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 4

#### Cobertura de regímenes y crisis de cada segmento
**Fuente.** Katz, p. 44; Taleb, p. 49, 55-56, 93; LTCM, p. 138, epílogo p. 233; Faith, p. 25-27, 180-195, 207-212.

**Qué dice.** Katz: la muestra de desarrollo debe contener mercados alcistas y bajistas, con y sin tendencia, y crisis. Taleb: preferir a quien lleva más tiempo expuesto al suceso raro, condicionado a sobrevivir; las divisas más estables son las más propensas a romperse. LTCM: "ninguna inversión puede juzgarse por medio ciclo"; sus modelos "no llegaban tan atrás". Faith: cuatro estados de mercado (con tendencia o estable, por tranquilo o volátil); un test de 20 años con 13 años de tendencia tranquila y 7 volátiles dice poco de la próxima década; el tamaño efectivo de muestra es el número de episodios de estado distintos, no el de operaciones.

**Qué significaría aquí.** Una tabla de cobertura por segmento (terciles de volatilidad, fracción de tendencia, los cuatro estados de Faith) para `build`, `oos1` y `oos2`, marcando cuando el OOS contiene un régimen que el build no vio, o cuando el OOS cayó justo en el estado favorito de la estrategia. Y una lista por activo de episodios de estrés con nombre (2008, flash crash de 2010, techo del oro de 2011, taper de 2013, SNB 15-01-2015, yuan 2015, Brexit 2016, marzo de 2020, WTI negativo en abril de 2020, gilts 2022) con cómo le fue a la estrategia en cada uno que cayó en sus ventanas. Un superviviente sin ninguno en sus ventanas se etiqueta "no probado en crisis" o "medio ciclo", sean cuales sean sus p. La reproducción de crisis como escenario de riesgo pertenece a la sección de riesgo.

**Estado.** NUEVA (el mapa condicional aplica regímenes al P&L, no al reparto de segmentos) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 4

#### Rescates post hoc y cambios tras un mal periodo
**Fuente.** Aronson, p. 132-141; Chan QT, p. 109-110; Chan AT, p. 91-92, 187-188; NMW (Faulkner), p. 158-159.

**Qué dice.** Explicar un fallo solo es legítimo si la explicación hace una predicción nueva y comprobable que luego se confirma (Neptuno); inventar una razón a posteriori es "inmunizar contra la falsación". Tras una gran pérdida los operadores tocan parámetros para que esa pérdida no hubiera ocurrido, lo que invita a la siguiente. Chan: cuando GLD-GDX dejó de cointegrar en julio de 2008, la hipótesis del petróleo se probó como variable nueva. Faulkner: tras un periodo inusualmente malo, el siguiente suele ser mejor pase lo que pase; quien cambia de sistema en su peor momento atribuirá la mejora al sistema nuevo.

**Qué significaría aquí.** Cuando una estrategia falla en algún mercado y se dice "la plata es distinta", el rescate se escribe como predicción comprobada en datos aún no leídos, o no cuenta, y toda exclusión post hoc va al ledger como prueba extra. Una hipótesis nacida de un fallo puede ser una plantilla nueva (nueva prueba, datos nuevos), nunca un parche sobre la misma estrategia. Todo cambio de la tubería provocado por malos resultados recientes se evalúa contra un control no cambiado en el mismo periodo siguiente, y las estrategias retiradas se siguen en sombra para medir cuánto se "recuperan".

**Estado.** AMPLÍA (mercados declarados de antemano en `_markets.yaml`; las exclusiones post hoc no se registran) — **Tipo.** proceso — **Locura.** 0 — **Valor.** 4

#### Ambigüedad dentro de la barra: resolverla en contra
**Fuente.** Katz, p. 25-26; Fitschen, p. 24-29; Williams, p. 124-125.

**Qué dice.** Cuando varias órdenes pueden llenarse en cualquier orden dentro de una barra (stop y objetivo tocados), un simulador puede producir "el mejor sistema de la historia" que arruina a quien lo opera; mejor uno que resuelva la ambigüedad en contra. Las plataformas suponen que cada precio del rango se negoció (un hueco se salta el stop). El software de Williams no aplicaba el stop el día de entrada, así que su backtest mostraba un stop efectivo más ancho del que operaba.

**Qué significaría aquí.** Toda resimulación Python (`translate`, mono, entryQuality) y toda pasada de SQX en H1/H4 sin precisión M1 o de tick resuelve stop y objetivo en la misma barra de forma pesimista. Un estudio: contar las operaciones cuyo resultado cambia entre resolución optimista y pesimista, y retestear los supervivientes con precisión M1 comparando lo que pasa en la barra de entrada. Las estrategias con muchas operaciones así son sospechosas. El realismo de los rellenos límite y stop pertenece a la sección de costes.

**Estado.** AMPLÍA (reconciliación de `translate`) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 3

#### Datos que halagan la reversión a la media, y precios rancios que fabrican persistencia
**Fuente.** Chan QT, p. 117; Chan AT, p. 83-85; NMW (Blake), p. 93.

**Qué dice.** Una estrategia de reversión compra una cotización baja ficticia y vende en la siguiente correcta, apuntándose un beneficio falso: un 100/110/100 le regala 10 $. Los errores de datos halagan la reversión y los spreads y perjudican al momentum. Blake: los valores liquidativos de fondos municipales casi no marcaban subidas durante tres meses mientras los bonos subían; un alisado del precio fabricaba una persistencia del 80 %.

**Qué significaría aquí.** La atribución de `feedQuality` en el paso 8 debería pesar esto de forma asimétrica: para estrategias que van contra el último movimiento, contar el P&L de operaciones abiertas a k barras de una anomalía marcada. Y una comprobación nueva: autocorrelación de rendimientos a 1 barra por hora del día; las horas donde se dispara (CFD de índices fuera de horario, pausas del Brent, festivos) se marcan como horas de cotización rancia y las estrategias que entran ahí reciben un aviso.

**Estado.** AMPLÍA (`studies/data/feedQuality`) — **Tipo.** datos — **Locura.** 1 — **Valor.** 3

#### Un segundo motor que reconcilie los costes operación a operación
**Fuente.** web: riesgo de implementación, 15 estrategias en 5 motores (https://arxiv.org/abs/2603.20319).

**Qué dice.** Cinco motores de código abierto coinciden exactamente a coste cero; toda la divergencia viene de cómo implementan los costes, y se encontraron 7 defectos (uno divide la comisión por 100 sin avisar). Propone métricas de sensibilidad al motor y un índice de estabilidad de conclusiones.

**Qué significaría aquí.** El asunto abierto #26 del proyecto (comisión aplicada una o dos veces) es exactamente esto. El backtest Python de `translate` reconciliando los costes de SQX operación a operación es el arreglo, y un índice de estabilidad de conclusiones (¿cambia el veredicto con el motor?) un número más en el certificado.

**Estado.** AMPLÍA (reconciliación de `translate`; `OPEN.md` #26) — **Tipo.** proceso — **Locura.** 0 — **Valor.** 3

#### Seleccionar por el resultado: P(rasgo | ganadora) no es P(ganadora | rasgo)
**Fuente.** MW (O'Neil, Ryan), p. 108-110; NMW (Eckhardt), p. 51-52.

**Qué dice.** CANSLIM se construyó estudiando solo los grandes ganadores del pasado y sus rasgos comunes. Eckhardt: "si el 85 % de los techos y suelos tienen la propiedad X, pero X también aparece a menudo en otros sitios, usarla como señal te destrozará".

**Qué significaría aquí.** Todo estudio que perfile las mejores operaciones de una estrategia (por ejemplo MFE/MAE de las grandes ganadoras) compara con los mismos rasgos en todas las operaciones y en entradas aleatorias, como ya hace entryQuality. La prueba previa del bloque fijo con la tasa de disparo y el lift pertenece a la sección de hipótesis.

**Estado.** YA EXISTE (entryQuality contra entradas aleatorias) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 2

#### Correlaciones espurias entre niveles de precio
**Fuente.** Katsanos, p. 34-48; COT Bible, p. 163-166.

**Qué dice.** Las correlaciones entre niveles de precio exageran (S&P-FTSE R² = 0,909 en precios, ρ = 0,43 en rendimientos diarios); usar cambios porcentuales, Spearman para colas gruesas, y mirar el diagrama de dispersión (un solo atípico movió una r de 0,523 a 0,568; tres regímenes con pendientes opuestas hacen inútil una sola r). Tablas de correlación de niveles a 10 años dan "Yahoo 0,73 con el yen" o "Wiseman Dairies 0,94 con el euro"; dos paseos aleatorios dan |r| > 0,7 con frecuencia.

**Qué significaría aquí.** Higiene para el estudio lead-lag y la criba de redundancia: Spearman sobre rendimientos, nunca sobre niveles, y líderes elegidos por vínculo económico y declarados antes de mirar, nunca por barrido de correlaciones. Evitar además líderes que son espejo aritmético (triángulos de FX como EURJPY = EURUSD·USDJPY): el adelanto entre patas de un triángulo está atado por arbitraje (Katsanos, p. 218, 233).

**Estado.** YA EXISTE (la redundancia de la puerta trabaja sobre rendimientos) · AMPLÍA (lista de líderes declarada) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 2

#### Un grafo causal antes de condicionar por otro mercado
**Fuente.** web: inversión causal por factores, López de Prado (https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4205613).

**Qué dice.** El "espejismo de factor" es un resultado estadísticamente válido pero causalmente mal especificado (sesgo de colisionador o de confusor); dibujar un grafo causal con conocimiento del dominio antes de elegir condiciones.

**Qué significaría aquí.** Para condiciones que usan un segundo mercado o un régimen: dibujar el grafo. Ejemplo: una estrategia de oro filtrada por el dólar está confundida por los tipos reales de EE. UU.

**Estado.** NUEVA — **Tipo.** proceso — **Locura.** 1 — **Valor.** 2

### 3.8 · Qué mide cada número: definición de las métricas

#### Un gemelo robusto para cada cifra titular
**Fuente.** NMW (Eckhardt), p. 47; Aronson, p. 206, 250-252; Katsanos, p. 172-178.

**Qué dice.** Eckhardt: los tests clásicos suponen una distribución conocida; si la suposición falla un poco, los estimadores delicados descarrilan y los burdos aciertan más. "Los tests delicados con que los estadísticos exprimen significancia de datos marginales no tienen sitio en el trading. Necesitamos instrumentos estadísticos romos." Aronson: su estadístico es el rendimiento medio diario porque su distribución muestral es casi normal; Sharpe, factor de beneficio y rendimiento/Ulcer tienen colas derechas largas, el remuestreo puede portarse mal y conviene el logaritmo del cociente; con distribuciones asimétricas el test y el intervalo discrepan. Katsanos: el PRR, un factor de beneficio encogido una sigma de los conteos de ganadoras y perdedoras, [(G - √G)/N·gananciaMedia] / [(P - √P)/N·|pérdidaMedia|], mayor que 2 bueno, mayor que 2,5 excelente.

**Qué significaría aquí.** Cada criba que da una p o un Sharpe (puerta, escalera del mono, BH, lectura conjunta) se calcula también sobre un estadístico robusto: mediana del R por operación, media recortada o winsorizada, tests de rangos o signos, Sharpe sobre rendimientos winsorizados, log(PF) en vez de PF, PRR como criba barata de muestra pequeña. Una estrategia que solo pasa con el delicado lleva una marca. Declarar el R medio por operación como estadístico de registro; hoy `engines/nulls/stats.py` imprime varios y no elige, y el README de nulos ya muestra que el estadístico mueve el veredicto más que el nulo (Sharpe 51 % frente a neto 21,5 %).

**Estado.** AMPLÍA (puerta, mono, `blindJoint`; `engines/nulls/stats.py`) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 4

**⚠ Contradice.** Eckhardt (NMW, p. 47): el Sharpe deflactado y cualquier p basada en la normal son el tipo de estimador delicado del que desconfía (SPA/StepM, por bootstrap, menos). No es razón para quitarlos, sí para mostrar sus gemelos robustos y un índice de cola al lado.

#### Métricas robustas al corte de la ventana: RAR%, R-cúbico y ventanas desplazadas
**Fuente.** Faith, p. 182-192.

**Qué dice.** CAGR, MAR y Sharpe son frágiles al inicio y fin de la ventana: quitar un mes al principio y dos al final llevó el MAR de la triple media de 1,39 a 1,61 y el Sharpe de 1,25 a 1,37, porque había drawdowns en los bordes; el CAGR fue ~30 veces más sensible que el RAR%. RAR% = pendiente anualizada de una regresión lineal del logaritmo del capital; R-cúbico = RAR% / (media de los 5 mayores drawdowns por duración media de los 5 más largos / 365); Sharpe robusto = RAR% / σ anualizada de los rendimientos mensuales. Una regla de drawdown ajustada a la curva subió el MAR un 60 % y el RAR% un 0,4 %.

**Qué significaría aquí.** Añadir RAR% y R-cúbico como métricas titulares en la puerta y el ledger. Recalcular cada métrica de ordenación sobre K ventanas desplazadas (quitar 0-3 meses en cada extremo de `oos1`) y usar la mínima o la mediana, marcando las estrategias cuyo rango cambia mucho. El cociente (cambio de la métrica frágil / cambio de la robusta) ante una regla nueva es un detector de sobreajuste.

**Estado.** NUEVA (no se encontraron como métricas en el repositorio) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 4

**⚠ Contradice.** Sharpe, PF, MAR y CAGR sobre una sola ventana `oos1` fija pueden moverse un 10-15 % desplazándola unos meses; el Sharpe deflactado corrige por número de pruebas, no por esto, y las ordenaciones seleccionan en parte dónde cae el corte de un drawdown (Faith, p. 182-190).

#### Qué es 1R en un build sin stop
**Fuente.** Tharp, p. 149-152, 158.

**Qué dice.** Cuando las operaciones no tienen riesgo inicial explícito, agrupar las pérdidas por tramos y tomar la pérdida mínima típica (sin contar las de cero) como 1R del sistema; expresar cada operación en múltiplos de ella. Regla práctica: al menos 100 operaciones y expectativa mayor de 0,5R es un buen sistema a largo plazo.

**Qué significaría aquí.** El proyecto construye sin stop, así que las "métricas en R por operación" ya aceptadas necesitan definir R. Candidatas: la pérdida mínima típica de Tharp, k·ATR en la entrada, la MAE mediana de las perdedoras, o el stop de ATR leído de la MAE del paso 24. Elegir una y congelarla, o R es un parámetro libre.

**Estado.** AMPLÍA (métricas en R aceptadas) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 4

#### El Sharpe castiga la cola derecha, y la suavidad selecciona fragilidad
**Fuente.** Covel TF, p. 102-104, 281, 295; Faith, p. 101-104; Covel CT (Parker, DiMaria), p. 164-165, 192-193; Tharp, p. 142-143, 273, 278-279; NMW (Eckhardt), p. 54, 56; Chan QT, p. 20-21.

**Qué dice.** Meaden: los seguidores de tendencia tienen una desviación mensual de 12,51 frente a una semidesviación de 5,79; el Sharpe penaliza la volatilidad al alza. Harding: quitar los mejores rendimientos sube el Sharpe, "una reducción al absurdo". Faith: LTCM (~40 %/año muy suave) y Amaranth (Sharpe excelente) reventaron; "creo que hay una relación inversa entre la suavidad y el riesgo real"; el MAR con drawdown diario en vez de fin de mes pasa de 1,22 a 0,99. Tharp: un sistema con 90 % de acierto, ganancia media 275 $ y pérdida media 2.700 $ tiene expectativa negativa. Eckhardt: el porcentaje de acierto es el estadístico menos importante y puede estar inversamente relacionado con el rendimiento. Chan: rentable casi todos los meses implica Sharpe anual > 2; un desajuste (Sharpe 2 con 55 % de meses positivos) apunta a un error o a unas pocas operaciones gigantes.

**Qué significaría aquí.** Ordenar y cribar también con una medida de bajada (Sortino, o el cociente desviación/semidesviación como diagnóstico: > 1,3 marca una estrategia con asimetría a la derecha que el Sharpe infravalora). Una marca de "suave pero frágil": R² o Sharpe altos con acierto alto, asimetría negativa y pérdidas raras grandes (por ejemplo acierto > 65 % y peor pérdida > 5 veces la ganancia mediana), que manda la estrategia antes que nada a la prueba de choque de la sección de riesgo. Drawdown siempre sobre capital diario o por barra, nunca de fin de mes. Una consulta al ledger: Spearman del acierto IS contra el rendimiento por riesgo OOS; si es negativo, el acierto pasa a columna de aviso, y ningún filtro del build debe tener un suelo de acierto. El Sharpe deflactado corrige asimetría y curtosis en la significancia, pero no en la ordenación que decide quién llega a él.

**Estado.** AMPLÍA (profitShape mide concentración de ganancias, no la cola de pérdidas; comprobar qué métrica usa la aptitud de SQX) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 4

**⚠ Contradice.** Si la aptitud de SQX o alguna criba de la puerta premia la suavidad (R², Sharpe, estabilidad, σ baja), la búsqueda se inclina hacia perfiles de asimetría negativa cuyo riesgo no se ve dentro de muestra (Faith, p. 101-104; Covel TF, p. 102-104, 281, 295).

#### La función de aptitud del genético es una variable de experimento
**Fuente.** Katz, p. 66-67; Fitschen, p. 67-68, 107-117; CMT, p. 604; Chan QT, p. 97-99.

**Qué dice.** El beneficio neto como aptitud premia sistemas que solo operan los cracs (2-3 operaciones en 10 años). El estadístico t (media sobre error típico de las operaciones o de los rendimientos diarios) combina beneficio, número de operaciones y variabilidad, y "funciona bastante bien". Fitschen: ganancia/dolor = beneficio anual medio / media de los N mayores drawdowns (N = años), usada en cada paso del desarrollo; rehacer los mismos sistemas con beneficio por operación como criterio dio al de materias primas un ~50 % más de beneficio pero 4 veces el drawdown anual medio y 6 veces el máximo (454k frente a 73k). CMT: la evolución explota rarezas poco comunes de los datos. Chan: g = m - s²/2, así que ordenar por rendimiento medio ignora el arrastre de la varianza.

**Qué significaría aquí.** Un A/B barato cuya respuesta es un ajuste directo de SQX, uno de los tipos de decisión que el dueño pide: misma plantilla y mismos datos, aptitud por beneficio neto frente a t o SQN frente a ganancia/dolor, comparando la supervivencia en `oos1` por hora de CPU y el rendimiento contra el mono en el ledger, como una réplica tipo varianza por semilla.

**Estado.** NUEVA (como experimento) — **Tipo.** generación — **Locura.** 0 — **Valor.** 4

#### Probabilidad de ganar en cada ventana móvil, frente al mono
**Fuente.** Covel TF, p. 41, 71; MW (Hite), p. 88-89.

**Qué dice.** Campbell 1980-2003: 56 % de meses rentables, 84 % de años, 79 % de ventanas móviles de 12 meses, 86 % de 24, 90 % de 36, 100 % de 48 y 60. Para Dunn, con periodos de ~3,75 años o más todos los rendimientos son positivos. Hite: evaluar por año natural es arbitrario; lo que quieres saber son las probabilidades de ganar en un periodo de cualquier longitud (simulación: 90 % a 6 meses, 97 % a 12, 100 % a 18; tras 7 años en vivo, 90 %, 99 % y 100 %).

**Qué significaría aquí.** Sobre el capital diario ya cosechado: P(beneficio) y rendimiento mediano en todas las ventanas móviles de 1 a 24 meses, IS frente a OOS, y la ventana más corta con 100 % (y 95 %) de ventanas positivas. La parte de validación es compararlo con la misma curva del mono: un mono con deriva positiva también llega al 100 % con el tiempo, y la distancia entre las dos curvas a 6-12 meses es una medida legible de ventaja. Su uso como presupuesto de paciencia en vivo pertenece a la sección de riesgo.

**Estado.** NUEVA (no hay métrica de ventanas móviles en los estudios) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 4

#### Intervalo de lo que vale la ventaja, no solo una p
**Fuente.** Aronson, p. 234-243, 249-250; Katz, p. 60, 65.

**Qué dice.** El bootstrap de White centra en cero los rendimientos diarios de la regla y los remuestrea con reemplazo: la hipótesis nula es rendimiento esperado ≤ 0 y da un intervalo (en TT-4-91, una ruptura de 91 días, +4,84 %/año sin tendencia, p = 0,0692 e intervalo al 80 % de +0,62 % a +9,06 %). La permutación de Masters empareja las posiciones fijas con un barajado sin reemplazo de los cambios del mercado sin tendencia: la nula es que las señales no llevan información, y no da intervalo porque no afirma nada sobre un parámetro de población. Con 5.000 réplicas, sobre datos sin tendencia, coinciden. Katz: 16 aciertos en 47 operaciones dan un intervalo al 99 % del 17 % al 53 % para el acierto real.

**Qué significaría aquí.** La escalera del mono es de tipo permutación (contenido de información); la puerta da una p pero no un intervalo de lo que vale la ventaja. Añadir a cada superviviente un intervalo bootstrap estacionario por bloques del R medio por operación o del exceso diario: "la ventaja es real (p) y vale entre a y b". La cota inferior es la que `edgeCost` debería comparar. Intervalos binomiales para el acierto y toda proporción.

**Estado.** AMPLÍA (`engines/nulls` da p; `core/significance.py` tiene PSR y longitud mínima de historial; no hay intervalo del rendimiento esperado en el informe de la puerta) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 3

#### Operaciones que no son independientes: n efectivo, rachas y filtros de curva de capital
**Fuente.** Katz, p. 52, 61-66; Katsanos, p. 172-178; Williams, p. 198-199; Tharp, p. 38-39; Covel TF, p. 188-189; Taleb, p. 178-179; NMW (Trout), p. 68; NMW (J. Ritchie), p. 133-134; Faith, p. 259-260; web: Davey sobre operar la curva de capital (https://kjtradingsystems.com/equity-curve-trading.html).

**Qué dice.** Las operaciones de un periodo no son una muestra aleatoria: la dependencia serial puede dejar el n efectivo en la mitad o un cuarto; en el ejemplo de Katz, ρ = 0,21 fuera de muestra hacía que el t exagerara la significancia un 20-30 % (p de 0,139 a ~0,18). La no normalidad no importa por encima de n ~20-30; la dependencia sí. Katsanos mide ρ = 0,28 a 1 retardo antes de cualquier Monte Carlo de barajado. Williams: en sus sistemas del ~65 %, tras tres pérdidas la siguiente ganaba más del 80 %; Tharp lo llama falacia del jugador. Covel y Taleb: las rachas son tan largas como predice una moneda. Trout sube el tamaño cuando gana; la CRT de J. Ritchie tuvo su único año perdedor por triplicar el tamaño a mitad de año en racha. Los Tortugas saltaban una ruptura si la anterior (tomada o no) había ganado. Davey: 9 de cada 10 estrategias algorítmicas no tienen dependencia serial.

**Qué significaría aquí.** `profitShape/dependence.py` ya corre rachas de Wald-Wolfowitz, Ljung-Box y rachas perdedoras contra barajado. Faltan dos cosas: (1) que cada p sobre P&L de operaciones de la puerta o la lectura conjunta lleve la autocorrelación a 1 retardo y la corrección n_ef = n(1 - ρ)/(1 + ρ); (2) que la prueba de dependencia decida algo: solo si hay dependencia serial positiva (z de rachas < -2), medida en operaciones OOS porque las IS están seleccionadas, puede el módulo de cartera usar filtros de curva de capital o tamaño según rendimiento, y siempre probados contra tamaño constante. Añadir E[R | la señal anterior ganó] frente a E[R | perdió], con operaciones en sombra.

**Estado.** YA EXISTE (`studies/readings/profitShape/dependence.py`) · AMPLÍA (corrección de n efectivo, regla de decisión) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 3

#### Métricas de dolor que faltan
**Fuente.** Katz, p. 19; Fitschen, p. 1-5; CMT, p. 546, 549-550, 556; Tharp, p. 150-156; MW (Dennis), p. 59.

**Qué dice.** Stendahl, citado por Katz: beneficio neto sin atípicos, cociente de pérdida (mayor pérdida / beneficio neto), periodo plano más largo. Fitschen: rentabilidad anual media mayor que el drawdown máximo, y múltiplo del drawdown máximo anual medio (el que se vive cada año); tiempo máximo entre máximos de capital; "pocos operadores aguantan un drawdown del 20 %". Chande: banderas rojas con PF > 10, acierto > 70 %, mayor ganadora > 40-50 % del beneficio total (PF ajustado por atípicos < 1, fuera); drawdown ≤ 20 % y ≤ 9 meses. Ruggiero: consistencia por décimas de la muestra. Tharp: en su ejemplo de 103 operaciones todo el beneficio es una operación de 14.256 $, y quitar una sola pérdida de 3.221 $ sube el beneficio un 40 %. Dennis: el 95 % de sus beneficios venía del 5 % de sus operaciones.

**Qué significaría aquí.** profitShape ya mide concentración en pocas operaciones y meses y la consistencia por tramos. Faltan: periodo plano más largo, drawdown máximo anual medio (mejor estimado como la media de los N mayores drawdowns en N años), cociente rentabilidad / drawdown anual medio (invariante al apalancamiento), tiempo bajo el agua, PF ajustado quitando la mejor o las k mejores operaciones, y el lado simétrico: sensibilidad a quitar las k peores pérdidas (un veredicto que cambia con una sola pérdida tiene una cola sin gestionar). Y una comprobación nueva con la salida de SPP: ¿aparece la misma operación atípica en los vecinos de la meseta? Una operación que solo captura la madre es suerte.

**Estado.** AMPLÍA (`studies/readings/profitShape`) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 3

#### Combinar métricas y predictores con pesos iguales o 0/1
**Fuente.** Chan AT, p. 4-7; NMW (Eckhardt), p. 48.

**Qué dice.** Chan: el modelo lineal más extremo usa coeficientes de igual magnitud, R = media(R) + desv(R) · Σ signo(i)·z(i) / n (Kahneman: los pesos iguales no los afectan los accidentes del muestreo), o una suma de rangos con signo (Greenblatt). Eckhardt: la literatura robusta dice que la mejor forma de combinar indicadores no suele ser una ponderación optimizada sino 1 o 0; si vale, peso igual.

**Qué significaría aquí.** Toda puntuación compuesta de supervivientes en la puerta combina métricas por rangos con signo y pesos iguales, no por pesos aprendidos. El metamodelo del ledger ya aceptado empieza como un modelo de z con signo y pesos iguales sobre pocas covariables, no un modelo de aprendizaje automático ajustado.

**Estado.** AMPLÍA (puntuación de la puerta, metamodelo del ledger) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 3

#### Unidades correctas: horas reales, capital diario y R por año
**Fuente.** Chan QT, p. 44-45; NMW (Trout), p. 65; Tharp, p. 131-132, 141-143, 155-157; Katz, p. 124.

**Qué dice.** El Sharpe anualizado es √N_T por el Sharpe por periodo, con N_T los periodos operables del año (1.638 horas para la NYSE, no 252·24). Trout: el mejor operador es el de mejor Sharpe diario, sobre la variación de capital de cada día. Tharp: comparar por expectativa por R por número de operaciones (0,78R × 54 = 42R al año bate a 0,84R × 18 = 15R). Katz: entre sistemas perdedores, el que opera menos parece mejor en beneficio neto; comparar por P&L medio por operación.

**Qué significaría aquí.** Cualquier Sharpe por barra u hora (estudio de exposición) usa las horas reales de sesión del fichero de activo, porque FX 24/5 e índices con cortes difieren. Usar el Sharpe sobre capital diario a mercado, no sobre capital de operaciones cerradas, que esconde drawdowns abiertos. R por año como columna del ledger para comparar M30 con H4. Entre variantes débiles, R medio por operación.

**Estado.** AMPLÍA (exposición; capital diario en variantes; métricas en R aceptadas) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 2

#### Un indicador que elige su mejor ventana necesita umbrales calibrados por simulación
**Fuente.** NF, p. 188-195.

**Qué dice.** El KSDI mide el movimiento en desviaciones típicas y elige para cada lado la ventana n que maximiza el valor; su señal de agotamiento es ±100 (percentil 90 en 80 años) o 2 desviaciones.

**Qué significaría aquí.** El paso "máximo sobre n" es fisgoneo dentro del indicador: su distribución nula no es la normal (es el máximo de z correlacionadas). Todo bloque que maximiza sobre una ventana necesita umbrales calibrados por simulación, no leídos de una campana.

**Estado.** NUEVA (regla de autoría de bloques) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 2

### 3.9 · Dónde vive la ventaja dentro de la estrategia

#### El objeto que se opera no es el que pasó la puerta: volver a pasarla con el stop puesto
**Fuente.** Williams, p. 228-229, 240-243; CMT, p. 553; LTCM, p. 3-10, 21; Aronson, p. 303-306; Katz, p. 201, 211-212; Elder, p. 202, 219; Taleb, p. 73, 110; MW (Seykota), p. 81; NMW, p. 50, 175; SMW (Minervini), p. 97-98. A favor del build sin stop: Faith, p. 140-147; Fitschen, p. 69-72; Katsanos, p. 183-184; Williams, p. 228-229.

**Qué dice.** Mismas entradas del S&P: stop de 500 $, -41.750 $ y 26 % de acierto; de 1.500 $, +116.880 $ y 56 %; de 5.000-6.000 $, +269.525 $ y 70 %, pero mayor pérdida 5.920 $ frente a 2.045 $. En el ejemplo del CMT, añadir stops llevó el rendimiento de 276 % a 6.024 %. Meriwether: "aguanta tus pérdidas hasta que se vuelvan ganancias"; las operaciones de convergencia aguantadas aciertan casi siempre y la vez que no, quien las aguanta ya no está. Aronson: las colas gruesas inflan el sesgo de minería, y con salidas fijas que cortan los extremos el sesgo es mucho menor. Katz: las entradas de giro (lunares, estacionales, ciclos) aciertan con excursión adversa casi nula o fallan mucho, y "funcionan mejor con stops muy ceñidos"; una salida holgada esconde su ventaja. En el otro lado, Faith: con entrada con ventaja y salida por tiempo, añadir un stop de cualquier anchura empeoró todas las métricas en tres sistemas; Williams: en sistemas siempre dentro el stop nunca ayudó; Chan (MTA, citado por Katsanos): los stops empeoran los sistemas rentables y mejoran los no rentables.

**Qué significaría aquí.** El proyecto construye sin stop a propósito y lee el stop de ATR de la MAE en el paso 24, sin optimizarlo (esa postura se respeta). Tres comprobaciones sin optimizar nada: (1) volver a pasar las cribas baratas y la comparación con el mono con el stop de MAE fijo puesto, aplicando el mismo stop al mono y comparando en R porque el stop cambia el tamaño, y marcar los supervivientes cuyo veredicto cambia; (2) medir desde el paso 8 la dependencia del stop: fracción del beneficio que viene de operaciones cuya MAE superó X ATR (las que un stop sensato habría cortado); si es grande, la ventaja de ese superviviente ES no tener stop y se etiqueta de cola corta; (3) en el ledger, comparar la caída IS→OOS de supervivientes de alta y baja concentración (profitShape) para medir el coste del build sin salidas, y buscar familias de giro cuyas ganadoras tengan MAE concentrada cerca de cero, candidatas a que el build sin stop las esté infravalorando.

**Estado.** AMPLÍA (`studies/closing/atrCalculator`, `entryQuality`, `profitShape`) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 5

**⚠ Contradice.** Casi todos los libros tratan el stop como parte del sistema, no como añadido (Elder, p. 202, 219; Taleb, p. 110; Seykota, MW p. 81; LTCM, p. 3-10). La objeción es a la selección: una búsqueda genética puntuada sin stop premia estrategias cuya ventaja es aguantar la excursión adversa, y añadir el stop después cambia el objeto que sobrevivió los pasos 8-23. Aronson (p. 303-306) añade que el build sin stop ni objetivo maximiza las colas que inflan el sesgo de minería. Katz (p. 201, 211-212) añade que puede infravalorar familias de giro en el ledger. Los libros no se ponen de acuerdo entre sí: Faith y Williams (sistemas siempre dentro) apoyan el build sin stop, así que el efecto del stop es propio de cada estrategia y hay que medirlo, no suponerlo.

#### Cuánto de la ventaja pone la hipótesis y cuánto la ranura aleatoria
**Fuente.** Chan QT, p. 26-27; Chan AT, p. xi-xii, 4-7; SMW (Shaw), p. 143, 145, 167; web: Renaissance según Zuckerman (https://bagerbach.com/books/the-man-who-solved-the-market/).

**Qué dice.** Chan: redes neuronales, árboles y algoritmos genéticos ajustan muchos parámetros, y "cada vez que aparecía un modelo cuidadosamente construido que parecía maravilloso en backtest, rendía miserablemente después"; lo que funciona tiene pocos parámetros, es lineal, simple y con base económica. "En vez de lanzar tantos indicadores o reglas a una serie para ver cuál es rentable, práctica que invita al fisgoneo, intentamos destilar la propiedad fundamental de la serie con un modelo simple." Shaw evita buscar patrones a ciegas: empieza por una hipótesis estructural y la prueba, y "lo más habitual es que los datos no permitan rechazar la eficiencia del mercado". Renaissance, en cambio, admitía señales significativas sin explicación, pero con poco capital al principio.

**Qué significaría aquí.** La condición fija de la plantilla es la hipótesis; la ranura aleatoria y el genético son minería ciega por diseño, compensada estadísticamente por el ledger y la deflación. Dos cosas: (1) que la separación del mérito de cada superviviente entre condición fija y ranura aleatoria (la ablación de `structure` ya existe) sea una cifra titular; (2) un A/B controlado en el ledger: plantillas solo con la condición fija (cero condiciones libres) frente a condición fija más ranura, comparando su rendimiento frente al mono tras multiplicidad. Si las familias genéticas no rinden por encima del mono, la alternativa de Chan es primero medir el mercado y luego plantillas sin condiciones libres. El matiz de Renaissance ("capital de prueba" para señales sin explicación) contradice la regla pura de fundamento previo y es una decisión del dueño.

**Estado.** AMPLÍA (ablación de `structure`; diseño de plantillas) — **Tipo.** proceso — **Locura.** 1 — **Valor.** 4

**⚠ Contradice.** El enfoque de minería genética en sí: Chan QT (p. 26-27) y Chan AT (p. 4-7) argumentan contra la ranura aleatoria de SQX; Shaw (SMW, p. 143, 145) pide hipótesis primero. El contraargumento del proyecto son los nulos y el ledger; el A/B lo decidiría con datos.

#### El canal de la salida: respuesta al impulso, perfil por duración y lo que pasa después de salir
**Fuente.** Chan QT, p. 66; Williams, p. 45-55; NF, p. 302-307; CMT, p. 267, 571; Covel TF, p. 318-319; Elder, p. 244-247; SMW (Minervini), p. 97-98; Faith, p. 64-71; web: salida aprendida como diagnóstico (https://tr8dr.github.io/RLp1/).

**Qué dice.** Chan: cambiar solo el momento de ejecución (apertura en vez de cierre) llevó el Sharpe de 0,25 a 4,43 en bruto. Williams, con la misma entrada en el S&P y stop de 3.000 $: objetivo de 500 $, -8.150 $ con 59 % de acierto; de 1.000 $, +13.737 $; salida al cierre, +39.075 $; al cierre siguiente, +68.312 $; al sexto cierre, +71.600 $ y 251 $/operación. Solo cambió el tiempo de mantenimiento. CMT: el riesgo crece con el tiempo y la recompensa no; una salida por tiempo pesa igual todas las entradas y es la adecuada para evaluarlas. Blackstar: en 18.000 operaciones casi todo el beneficio viene de las mantenidas más de un año. Elder y Minervini revisaban qué hacía el precio tras cada salida; Minervini descubrió que un tope de pérdida del 10 % habría subido el beneficio un 70 % porque "las ganadoras solían funcionar desde el principio". Faith: la curva E_n (MFE/MAE a n días) de una ruptura de 20 días es < 1 a corto plazo y 1,20 a 70 días: la entrada solo tiene ventaja a su propio horizonte.

**Qué significaría aquí.** El canal de mantenimiento de la escalera da un número; esto da la forma, siempre frente al mono con el mismo horizonte: (1) curva del P&L frente a una salida por tiempo a N barras (1..50), la "respuesta al impulso" de la entrada, que dice si la salida propia añade algo sobre una salida por tiempo y dónde deja de crecer el exceso; (2) curva de retraso de la salida (salir d barras antes o después), el gemelo de la de entrada que ya existe; (3) R medio por tramo de duración; (4) deriva del precio en las N barras tras cada salida, por tipo de salida (señal, stop, tiempo), frente a salidas aleatorias con la misma distribución de duraciones: deriva a favor tras salidas por señal es salir pronto, reversión tras stops es un stop dentro del ruido; (5) la cota de "salida perfecta a posteriori" frente a la real, un número gratis desde la MFE. `entryQuality/eratio.py` ya tiene la curva E_n con banda aleatoria; superponer la duración mediana de la estrategia muestra si la salida corta antes del pico.

**Estado.** AMPLÍA (`entryQuality` eratio y delay; canal de mantenimiento de la escalera) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 4

#### La escalera condicional de excursión adversa, frente al mono
**Fuente.** NF (Kase), p. 166-176.

**Qué dice.** Sobre 150.000 barras de futuros: si se toca la línea de aviso (rango medio de dos barras), P(tocar Dev1) ≈ 80 % y P(tocar Dev3) ≈ 45 %; P(Dev2 | Dev1) ≈ 80 %. Los múltiplos de ATR ignoran la dispersión de los rangos, y el riesgo crece con √(duración de la barra).

**Qué significaría aquí.** Un diagnóstico barato de calidad de entrada, más fino que la MAE media: P(la MAE llega al nivel j | llegó al nivel i) para las operaciones de la estrategia frente a las del mono. Si la continuación condicional de la estrategia es menor que la del mono, sus entradas tienen apoyo real. El uso para colocar el stop del paso 24 pertenece a la sección de riesgo.

**Estado.** AMPLÍA (`entryQuality` MFE/MAE frente a aleatorio) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 3

#### Probar la regla y su contraria
**Fuente.** Aronson, p. 21-22; Tharp, p. 79; Fitschen, p. 134-137; Katz, p. 148-150.

**Qué dice.** Aronson prueba cada regla y su inversa, porque un patrón que se cree alcista puede ser bajista, y para entradas sin interpretación obvia ambos sentidos son candidatos; dobla el universo y la multiplicidad. Tharp: imaginar el lado contrario de cada operación. Fitschen y Katz, dos probadores cuidadosos sobre la misma clase de activos, discrepan en el signo de la divergencia: Fitschen encuentra rentable desvanecer la divergencia precio-momentum en materias primas, Katz encuentra la divergencia MACD con entrada límite entre las pocas entradas rentables en ambas muestras; depende de la definición.

**Qué significaría aquí.** A nivel de familia: construir la condición fija en las dos polaridades como control; si la plantilla negada genera estrategias que pasan la puerta a un ritmo parecido, la condición fija no lleva información y trabaja la ranura (y cuenta como 2 pruebas en el ledger). A nivel de estrategia: el gemelo invertido (mismas entradas y salidas, lado contrario) debería perder la ventaja bruta más 2 veces los costes; si queda cerca de cero tras costes, la "ventaja" es ruido del tamaño del coste. Todo bloque "conocido" importado de un libro necesita prueba en los dos sentidos.

**Estado.** AMPLÍA (`structure` hace ablación e inversión de órdenes por estrategia; nada prueba la polaridad de la condición fija a nivel de familia) — **Tipo.** generación — **Locura.** 1 — **Valor.** 3

#### El conjunto de variantes frente a la madre seleccionada
**Fuente.** Aronson, p. 455-457; Chan QT, p. 54-55; web: estrategias conjunto (https://www.buildalpha.com/trading-ensemble-strategies/).

**Qué dice.** Hsu y Kuan: votar o tomar posiciones fraccionarias sobre todas las reglas de un tema (por ejemplo 2.040 reglas OBV, 1.158 cortas y 882 largas, dan 0,135 unidades cortas) es simple y ha resultado útil. Chan: mejor decidir por la media de varios juegos de parámetros que por el mejor.

**Qué significaría aquí.** Apoya "operar la meseta" ya aceptado, y añade una prueba limpia de si la selección aporta algo: ¿bate fuera de muestra el conjunto de todas las variantes de una estructura en el databank de build (no solo las supervivientes) a la madre seleccionada? Si sí, la selección no añade nada.

**Estado.** YA EXISTE ("operar la meseta" aceptado) · AMPLÍA (prueba conjunto frente a madre) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 3

#### Leer la ablación como interacciones, no como efectos que se suman
**Fuente.** Katz, p. 121-122, 129; Chan QT, p. 60.

**Qué dice.** Katz: "las variables interactúan: aunque cada una tenga su efecto, combinadas pueden no mantenerlo"; el efecto del tipo de orden cambió entre medias simples, exponenciales y triangulares y entre IS y OOS, y la media adaptativa esperada como la mejor estuvo entre las peores. Chan: quitar condiciones una a una mirando el conjunto de prueba y eliminar toda condición cuya retirada no lo empeore, aunque empeore el de entrenamiento; nunca añadir condiciones para mejorar el de prueba.

**Qué significaría aquí.** Un factorial completo pequeño (tipo de orden por variante de la condición fija por activo) con una lectura tipo ANOVA de dos vías diría qué efectos son estables. Sobre la ablación: Chan actuaría sobre ella para simplificar la estrategia; el proyecto la mantiene como diagnóstico. Una estrategia ablacionada que no es peor OOS podría sustituir a la madre si la decisión se toma antes de `oos2` y cuenta como prueba en el ledger.

**Estado.** AMPLÍA (`structure`) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 2

**⚠ Contradice.** Leve: "diagnóstico, nunca selección" en `structure` frente a Chan QT, p. 60, que simplifica según la ablación. La razón del proyecto (seleccionar sobre una lectura reintroduce fisgoneo) se sostiene si la simplificación se cuenta en el ledger.

#### Indicadores redundantes inflan la confianza, no la información
**Fuente.** Aronson, p. 42-46; Covel CT, p. 142-143.

**Qué dice.** La confianza sube con el acuerdo de las entradas, lo que solo está justificado si no son redundantes; muchos indicadores miden lo mismo con otro nombre. El pensamiento configural humano se limita a ~3 variables.

**Qué significaría aquí.** La redundancia de la puerta cubre estrategias entre sí, y debe usar la correlación del P&L diario en OOS y el solapamiento de señales, no solo la similitud de reglas: estrategias distintas en apariencia de una misma plantilla pueden ser la misma operación. Dentro de una estrategia (RSI > 70 y estocástico > 80 es una idea dos veces), una comprobación previa barata: correlación de las series booleanas de la condición fija y de la ranura sobre las barras de build.

**Estado.** YA EXISTE (redundancia de la puerta; ablación de `structure`) · AMPLÍA (solapamiento dentro de la estrategia) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 2

#### Promediar entradas nunca gana dentro de muestra, y puede ganar fuera
**Fuente.** Chan AT, p. 72-74.

**Qué dice.** Schoenberg y Corwin: con probabilidad constante de una excursión más profunda, entrar todo a un nivel siempre bate a promediar; como la volatilidad no es constante, promediar puede dar mejor Sharpe realizado fuera de muestra.

**Qué significaría aquí.** Una trampa del genético: la optimización dentro de muestra siempre preferirá un solo umbral. Si alguna vez se permiten entradas múltiples en SQX, compararlas solo fuera de muestra.

**Estado.** NUEVA (menor) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 1

### 3.10 · Calibrar el propio aparato

#### ¿Aciertan las bandas del Monte Carlo? Contarlas contra datos posteriores
**Fuente.** LTCM, p. 63-65, 124-130, 228-229.

**Qué dice.** La carta de riesgo de Merton y Scholes decía que "solo un año de cada cincuenta debería perder al menos un 20 %"; perdió un 77-90 % en meses. Fama: un movimiento de 5 sigmas debería salir una vez en 7.000 años. Tras las pérdidas los socios "volvieron a probar todos sus modelos y concluyeron que junio era una aberración esperada". Las probabilidades de cola de los modelos nunca se contrastaron con frecuencias realizadas.

**Qué significaría aquí.** Sobre toda la población de estrategias que pasaron el MC Retest de SQX y luego se observaron en un segmento nuevo (el `oos2` de la WFM, o el OOS en papel más adelante), contar cuántas veces el drawdown máximo, el peor mes o la racha perdedora realizados superaron los percentiles 95 y 99 del MC. Si está calibrado, ~5 % y ~1 %. Un 20 % de excesos significa que las perturbaciones (spread, deslizamiento, parámetros) infravaloran las colas reales y que toda expectativa y umbral de retirada derivados del MC deben ensancharse por el factor medido. Un test de excesos tipo Kupiec sobre los pronósticos de riesgo de la propia tubería, una vez por trimestre.

**Estado.** NUEVA (`studies/breakage/mcRetest` existe; sus pronósticos no se contrastan con datos posteriores) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 5

**⚠ Contradice.** Taleb (p. 110), LTCM (epílogo p. 234-235) y Covel TF (p. 180, 227) se oponen a derivar números de riesgo del mismo pasado que produjo la ventaja; el stop leído de la MAE IS y las bandas del MC Retest son eso. Antes de fijar umbrales en vivo con ellos, hay que comprobar su calibración.

#### Un recorte calibrado por familia: cuánto se deja cada estrategia al salir de la muestra
**Fuente.** CMT, p. 531, 550 (Hill, Pruitt y Hill); Chan AT, p. 7; Aronson, p. 320-321; web: McLean-Pontiff (https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2156623).

**Qué dice.** Regla de practicantes: esperar la mitad del beneficio probado y el doble del drawdown. Chan: la mayoría estaría contenta con un Sharpe en vivo mejor que la mitad del del backtest. Markowitz-Xu: H' = R + B(H - R), con H el rendimiento observado de la mejor regla, R la media de todas las probadas y B entre 0 y 1 a partir de la varianza dentro de cada regla, la varianza entre medias, el número de reglas y de periodos; "puede funcionar sorprendentemente bien, pero también fallar estrepitosamente". McLean-Pontiff: -26 % fuera de muestra, -58 % tras publicarse.

**Qué significaría aquí.** Cambiar la regla popular por el número propio: desde el ledger, la distribución de (métrica `oos1` / métrica `build`) de toda estrategia que pasó los filtros del build, por familia, activo y marco. Cada informe nuevo muestra la métrica de build ya multiplicada por el recorte calibrado y su dispersión; más adelante, la misma cadena para `oos2`/`oos1` y vivo/`oos2`. Es también la medida más limpia de cuánto sobreajusta el build por familia. En paralelo, una contracción empírica de Bayes (James-Stein) sobre la cosecha, B = 1 - σ²_ruido / σ²_total, da una predicción previa del Sharpe OOS de cada superviviente que se puede contrastar con toda cosecha de `oos1` archivada (el estudio de decaimiento midió una retención mediana de 0,45 en una población sin seleccionar). El Sharpe deflactado da una probabilidad; esto da un valor esperado.

**Estado.** AMPLÍA (ledger, Sharpe deflactado; `decay` mide la retención a posteriori) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 5

#### La caída de dentro a fuera de muestra es primero regresión a la media
**Fuente.** Aronson, p. 262-265, 272-274.

**Qué dice.** La variación aleatoria sola haría que el OOS saliera mejor tan a menudo como peor; "el mercado cambió" es poco plausible como explicación rutinaria. El sesgo de minería (azar más selección) explica la caída sistemática con menos supuestos. El rendimiento observado puede ser criterio de selección o estimador, no las dos cosas.

**Qué significaría aquí.** Para cada cosecha, calcular la retención que predice la selección sobre ruido (los Sharpes IS de la cosecha, su ruido muestral σ/√n, contraídos como en la entrada anterior) e imprimirla junto a la retención observada en `decay` e `isOos`. Retención observada cerca de la predicha: toda la caída es selección. Claramente por debajo: hay algo más (régimen, costes). Evita contar por defecto la historia de "el mercado cambió".

**Estado.** AMPLÍA (`studies/screening/decay`, `studies/screening/isOos`) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 3

### Las de locura 3 de esta sección
Controles negativos de toda la cadena: familias placebo (fase lunar, índice Kp, ciclos falsos, días de la semana barajados).

## 4 · ¿Dónde buscar? Hipótesis, familias y datos

Esta sección reúne todo lo que responde a «qué construir y dónde»: mapas del mercado que se miran antes de gastar CPU, pruebas del bloque del dueño antes de la plantilla, reglas para diseñar plantillas y el generador, las familias de hipótesis concretas (rupturas, reversión, sesión, calendario, entre mercados), los regímenes como condición, el diseño de salidas y cada fuente de datos nueva. Las tres ideas que considero más valiosas son: (1) la **tarjeta de información del bloque**, que mide si la condición fija de una plantilla predice algo por sí sola antes de ninguna construcción en SQX (cinco libros llegan a ella por caminos distintos); (2) el **estudio `leadlag`** con sus dos trampas (retornos solapados y cierres asíncronos), que convierte la familia entre mercados, ya aceptada, en una prueba ejecutable con veredicto por par; (3) la **tarjeta de carácter del mercado** (Hurst, variance ratio, vida media, rejilla de retrospectiva por horizonte), que dice por activo y marco temporal si hay que buscar tendencia o reversión.

Nota de lectura. Los libros citan resultados muy seleccionados dentro de la muestra. Ninguna cifra de estas fichas sirve como prior sin volver a probarla bajo el recuento de ensayos del ledger.

### 4.1 · Mapas del mercado antes de construir

#### Tarjeta de carácter del mercado (Hurst, variance ratio, ADF, vida media)
**Fuente.** Chan, *Algorithmic Trading*, p. 39-50, 63, 92-96, 134-137; Chan, *Quantitative Trading*, p. 126-133, 140-142; Aronson, *Evidence-Based Technical Analysis*, p. 345, 369-371; Kirkpatrick y Dahlquist, *Technical Analysis* (CMT), p. 38-39; Tharp, *Trade Your Way to Financial Freedom*, p. 169-170, 197-199, 213-214; web: Macrosynergy, Hurst (https://macrosynergy.com/research/detecting-trends-and-mean-reversion-with-the-hurst-exponent/); Chan, blog (http://epchan.blogspot.com/2016/04/mean-reversion-momentum-and-volatility.html).

**Qué dice.** Tres medidas dicen si una serie tiende a seguir o a volver. El test ADF mide si el siguiente movimiento depende del nivel (reversión). El exponente de Hurst (la varianza crece como tau^2H; H<0,5 revierte, H>0,5 sigue) y el variance ratio de Lo-MacKinlay (varianza de q barras dividida entre q veces la de una barra; VR>1 tendencia, VR<1 reversión) miden la velocidad de difusión. La vida media sale de una regresión Ornstein-Uhlenbeck: se regresa el cambio contra el nivel desviado, theta es la pendiente y la vida media es -ln2/theta (GLD-GDX unos 10 días; USD.CAD 115 días, y aun así una reversión lineal con esa retrospectiva ganaba). Chan insiste en que estas pruebas son más significativas que un backtest porque usan todas las barras y no solo las operaciones. Kaufman añade el efficiency ratio (movimiento neto de 10 barras dividido entre la suma de movimientos; exige >0,6) y recuerda que los mercados tienden solo un 15-25% del tiempo. La reversión intradía de ciertas sesiones es invisible a pruebas diarias.

**Qué significaría aquí.** Un estudio de datos, solo sobre el segmento `build`, por símbolo x marco temporal x sesión: ADF, H, VR(q) para q = 2..200 con z robusto, vida media y su estabilidad año a año. Sirve para enrutar familias (plantillas de reversión solo donde H<0,5 o VR<1 en su horizonte, de tendencia donde VR>1), para fijar retrospectivas como k x vida media en vez de dejarlas libres, y como covariable del ledger (si el rendimiento de una familia no sigue al carácter medido, el edge no es el que dice la plantilla). También como eje de régimen del mapa condicional (VR móvil). Ojo: `drivers.py` de crossmarket calculaba Hurst y VR diarios (oro 0,500 / 0,966, plata 0,478 / 0,738, Brent 0,495 / 0,982) y se retiró el 2026-09-16 junto con la regresión de impulsores; esta tarjeta es otro uso, sin regresión.

**Estado.** NUEVA (existió una versión diaria dentro de crossmarket, retirada) — **Tipo.** estudio · datos — **Locura.** 1 — **Valor.** 5

#### Mapa de tendencia: ¿a +1 desviación sobre la media sigue o revierte?
**Fuente.** Fitschen, *Building Reliable Trading Systems*, p. 31-44, 34-35.

**Qué dice.** Comprar lo que cierra 1 desviación sobre la media de 20 barras frente a lo que cierra 1 desviación por debajo, mantener un mes y comparar con comprar y mantener. En diario: acciones contratendencia (débil +1,56%/mes frente a 0,71% del B&H), materias primas tendencia (fuerte +158 $ frente a 66 $), FX en conjunto contratendencia, pero los pares con USD siguen tendencia (+210 $) y los cruces GBP, CAD, CHF revierten; un par que junta una divisa de tendencia y otra de reversión no hace ninguna de las dos cosas (-12 $). En horario (media de 10 barras, salida al cierre del día siguiente) acciones, materias primas y FX siguen tendencia (FX +9,17 $ frente a -11,64 $). La tendencia puede cambiar de signo con el marco temporal.

**Qué significaría aquí.** Un estudio previo de minutos por activo x marco temporal (M30/H1/H4, y D como contexto) con una banda nula por bootstrap de bloques. Decide si la condición fija debe ser de tendencia o de reversión en ese activo y marco antes de gastar CPU, y da al ledger una columna explicativa. La división entre divisas de tendencia y de reversión sugiere qué cruces incluir.

**Estado.** NUEVA — **Tipo.** estudio — **Locura.** 0 — **Valor.** 5

#### Rejilla retrospectiva x permanencia (dónde viven el momentum y la reversión)
**Fuente.** Chan, *Algorithmic Trading*, p. 134-137 (Box 6.1, Tabla 6.1).

**Qué dice.** Se correlaciona el retorno de las L barras pasadas con el de las H siguientes, sobre muestras sin solape, para una rejilla de (L, H). En el bono TU sale reversión a 1 día y momentum en (250, 25) con correlación 0,27 y p 0,02, que Hurst (0,44) y VR (no significativo) no veían porque promedian horizontes. Se elige el (L, H) con mejor compromiso correlación/p como retrospectiva y periodo de permanencia.

**Qué significaría aquí.** Un mapa de calor por símbolo y marco temporal con p-valores, corregido con BH porque la rejilla misma es una prueba múltiple, solo sobre `build`. Dice antes de generar nada en qué horizontes hay estructura explotable; los periodos de los indicadores y el horizonte de salida de la plantilla deberían caer donde el mapa es significativo. Es una vista natural para la ventana.

**Estado.** NUEVA — **Tipo.** estudio · datos — **Locura.** 1 — **Valor.** 4

#### Curva de continuación: ¿a partir de qué tamaño un movimiento sigue?
**Fuente.** Schwager, *New Market Wizards* (Eckhardt), p. 51.

**Qué dice.** Eckhardt explica las tendencias como un descuento discontinuo de escenarios improbables que la gente ignoraba hasta que «aparecen a la vista»: los movimientos de un tamaño característico tienen más probabilidad de lo aleatorio de ser el comienzo de un ajuste discontinuo. El problema de inferencia es separar esos comienzos de las oscilaciones al azar.

**Qué significaría aquí.** Por activo y marco: P(el movimiento se extiende otras x ATR | ya se ha movido k ATR desde un extremo local) en función de k, frente a la misma curva sobre la serie barajada o con bootstrap de bloques. Donde la curva real sube sobre la nula, esa k es el «tamaño característico» del activo, la distancia de ruptura que debería usar una plantilla.

**Estado.** NUEVA — **Tipo.** estudio — **Locura.** 1 — **Valor.** 4

#### Persistencia tras un movimiento superior a la media
**Fuente.** Schwager, *New Market Wizards* (Blake), p. 93-94.

**Qué dice.** En fondos sectoriales, un día con cambio mayor que el cambio medio del sector fue seguido por un día del mismo signo el 70-82% de las veces; fondos de renta variable un 60%; acciones individuales con fuerza relativa un 55%, no operable tras costes. Con 2-3 días de permanencia, la mitad del beneficio llega el primer día. Blake ordenaba por volatilidad x persistencia: un mercado persistente pero quieto no paga los costes.

**Qué significaría aquí.** Un escaneo barato por activo y marco: P(siguiente barra del mismo signo | |retorno| > k veces el |retorno| medio) en función de k, con intervalo binomial, frente a la curva sobre retornos barajados. Es la versión de una barra de la curva de continuación. Hay que publicar persistencia x movimiento medio / coste, no solo la persistencia.

**Estado.** NUEVA — **Tipo.** estudio — **Locura.** 0 — **Valor.** 4

#### Estudio de los mejores movimientos («oráculo»): qué los precede
**Fuente.** Tharp, *Trade Your Way to Financial Freedom*, p. 69-71.

**Qué dice.** Paso 5 de su modelo: elegir el marco temporal, encontrar los 50-100 mejores movimientos históricos (arriba y abajo) en muchos mercados, anotar qué tienen en común antes de empezar, cómo se desarrollan y cómo acaban. Después medir la tasa de falsos positivos: cuántas veces aparece el rasgo común sin gran movimiento.

**Qué significaría aquí.** Generación de hipótesis al revés de lo habitual: etiquetar los k mayores movimientos futuros normalizados por ATR por activo y marco, y calcular la frecuencia condicional de cada condición del vocabulario de SQX en las N barras previas frente a su frecuencia incondicional (lift y tasa de falsos positivos). Sale una lista ordenada de candidatas a condición fija. Solo sobre `build`. Lleva dentro la trampa P(rasgo | ganador) frente a P(ganador | rasgo) (ver 4.2).

**Estado.** NUEVA — **Tipo.** generación — **Locura.** 1 — **Valor.** 4

#### Perfiles de retorno futuro por percentiles de cada rasgo (bar-scoring)
**Fuente.** Fitschen, *Building Reliable Trading Systems*, p. 119-131.

**Qué dice.** Para cada criterio (RSI, desviaciones a la media, volumen, rango, tipo de barra en 8 clases) se reparten todas las barras en 20 grupos de igual tamaño y se anota el retorno medio a 1-5 días de cada grupo; la puntuación de una barra es la suma de sus grupos. Hallazgos: en materias primas los mejores retornos a 5 días no están en los extremos sino en los grupos 5-6 desde arriba; son contratendencia a un día y tendencia a semanas; volúmenes muy bajos y muy altos preceden subidas. Un BRAC (reconstruir con el último año apartado) mostró un 10-15% de inflación dentro de la muestra. Hace falta mucha muestra por grupo.

**Qué significaría aquí.** Un diagnóstico por activo y marco: perfiles de 20 grupos del retorno futuro de rasgos estándar. Dice si las condiciones de umbral de SQX (x > nivel) tienen la FORMA correcta o si hacen falta condiciones de banda (a < x < b). También una capa de ordenación para cartera cuando varias estrategias disparan a la vez.

**Estado.** NUEVA — **Tipo.** estudio — **Locura.** 1 — **Valor.** 4

#### Tasa de rupturas falsas como serie de congestión
**Fuente.** Schwager, *Market Wizards* (Dennis), p. 49, 56; Schwager, *Market Wizards* (Marcus, Kovner), p. 20-21, 36-38, 43; Chan, *Quantitative Trading*, p. 119, 140.

**Qué dice.** Dennis atribuye sus malos años a mercados laterales con muchas rupturas falsas y, tras 1987-88, a «más rupturas falsas» por la multitud de seguidores de tendencia computarizados. «Evita el medio como la peste»: el plazo intermedio es donde se amontonan. Marcus: antes las rupturas tenían oleadas de compradores lentos; ahora todos ven el punto a la vez y las rupturas falsas son mucho más frecuentes. Chan: la competencia acorta el horizonte óptimo del momentum («una semana en backtest puede funcionar solo con un día ahora») y lleva a cero la reversión.

**Qué significaría aquí.** Un estudio de mercado: por activo y año, la proporción de rupturas de N barras (N = 20, 55, 100 en H1/H4/D) que se deshacen x ATR en k barras. Es un indicador de régimen y de congestión para el mapa condicional, y dice qué horizontes de ruptura están saturados. Más una consulta al ledger: ¿sobreviven peor OOS las estrategias de permanencia intermedia? Y una lectura de «deriva del horizonte» para estrategias de tendencia: por año de `build`, el P&L medio en función de las barras mantenidas o el momento del pico de MFE; un pico que se adelanta año tras año es congestión y la salida fija será lenta OOS (ruidoso con los recuentos habituales).

**Estado.** NUEVA — **Tipo.** estudio — **Locura.** 1 — **Valor.** 4

#### Tablas actuariales de la edad del tramo (swing)
**Fuente.** Schwager, *New Market Wizards* (Sperandeo), p. 100-102, 106; Williams, *Long-Term Secrets to Short-Term Trading*, p. 206.

**Qué dice.** Sperandeo estudió los tramos del Dow desde 1896: el tramo alcista intermedio mediano sube un 20% en unos 107 días, cifra estable antes y después de 1945. Cuando un movimiento supera la extensión o duración mediana, las probabilidades de seguir caen claramente; un techo en un mercado «de 80 años» es más fiable que el mismo patrón en uno «de 20». Octubre de 1989: 200 días sin corrección de 15 días frente a la mediana de 107; 7 de 8 veces el precio volvió por debajo. Lo usa como probabilidades, nunca como objetivo. Williams cancelaba entradas tras 18 barras seguidas de subida (cifra anecdótica).

**Qué significaría aquí.** Segmentar el precio en tramos (ZigZag a k ATR) y construir la curva de supervivencia de extensión (en ATR) y duración (en barras). Luego (1) mapa condicional: P&L de cada estrategia por percentil de edad del tramo al entrar (¿las de reversión solo funcionan en tramos viejos y las de tendencia en jóvenes?); (2) un bloque «percentil de edad del tramo» como condición fija.

**Estado.** NUEVA — **Tipo.** estudio · generación — **Locura.** 1 — **Valor.** 4

#### Pantalla de estacionariedad: qué símbolos merecen plantillas de reversión
**Fuente.** Chan, *Quantitative Trading*, p. 126-133 (Ej. 7.2-7.3).

**Qué dice.** Correlación y cointegración no son lo mismo: la primera es de retornos a corto plazo, la segunda de niveles a largo plazo (KO/PEP correlacionan 0,48 sin cointegrar; GLD/GDX cointegran, CADF t = -3,36). Algunos cruces de divisas, como CAD/AUD (dos divisas de materias primas), son estacionarios por sí solos.

**Qué significaría aquí.** Para plantillas de reversión, elegir los símbolos cuyo precio está más cerca de ser estacionario (ADF, Hurst, VR, vida media sobre `build`), como AUDNZD, AUDCAD o pares tipo EURCHF, en vez de aplicar reversión a mayores con tendencia o al oro. Se integra en la tarjeta de carácter.

**Estado.** NUEVA — **Tipo.** datos — **Locura.** 1 — **Valor.** 4

#### Contracción y expansión del rango: la huella del agrupamiento de volatilidad
**Fuente.** Williams, *Long-Term Secrets*, p. 27-33.

**Qué dice.** En todos los mercados y marcos, los rangos alternan racimos de rangos pequeños con rangos grandes; tras rangos grandes vienen pequeños. Hay que entrar antes de la barra de gran rango, cuando los rangos «se han secado», y no perseguir mercados calientes. Lo muestra en S&P diario, 5, 30 y 60 minutos.

**Qué significaría aquí.** El estudio: autocorrelación del log del rango por activo y marco y distribución condicional del rango siguiente tras una barra NR-k (la más estrecha de k) frente a tras una WR-k. Dice qué activos merecen la familia de compresión (ver 4.4, donde está la familia).

**Estado.** AMPLÍA (familia de régimen de volatilidad aceptada; añade el estudio de huella) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 3

#### Tabla de probabilidades base condicionadas de la barra
**Fuente.** Williams, *Long-Term Secrets*, p. 14-15 (Tablas 1.1, 1.2).

**Qué dice.** Comprar en la apertura y salir al cierre todos los días da un 53,2% de cierres alcistas, no un 50%. Tras uno o dos cierres bajistas seguidos la proporción cambia respecto a esa base: su prueba de que el mercado no es una moneda. Él mismo dice que nunca operaría las tablas; lo que importa es la desviación respecto a la base.

**Qué significaría aquí.** Un escaneo previo por activo y marco: P(barra alcista | k barras bajistas previas), P(alcista | barra interior), etc., comparado con la P(alcista) incondicional y con el mono de misma deriva, nunca con 50%. Es un menú de estados de barra con sesgo antes de construir.

**Estado.** AMPLÍA (el mapa condicional lee P&L por régimen a posteriori) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 3

#### Previsibilidad por horizonte y ritmo de los tramos de 2-4 días
**Fuente.** Schwager, *New Market Wizards* (Raschke), p. 115-116, 119.

**Qué dice.** Solo los movimientos a corto plazo se pueden predecir con precisión; la precisión cae mucho con el horizonte. Los mercados van de mínimos relativos a máximos relativos cada 2-4 días. Predecir dirección, no magnitud; sin objetivos.

**Qué significaría aquí.** Un estudio de previsibilidad por horizonte: tasa de acierto o coeficiente de información de un conjunto fijo de señales simples en función del horizonte (1..50 barras), y la distribución de la duración de los tramos (barras entre giros de ZigZag) frente a un paseo aleatorio de igual volatilidad. Si los tramos reales se agrupan en 2-4 días, una salida por tiempo a ese horizonte es una elección natural sin optimizar.

**Estado.** NUEVA — **Tipo.** estudio — **Locura.** 1 — **Valor.** 3

#### Tendencia por horizonte (proporción de días con ADX>20)
**Fuente.** Fitschen, *Building Reliable Trading Systems*, p. 171-173.

**Qué dice.** Sobre 56 materias primas, la proporción de días con ADX de 14 y 20 días por encima de 20 es bastante constante año a año; con ADX de 40 y 80 oscila mucho. Desde 2000 solo 3 de 12 años superaron la media en tendencias largas, frente a 7 en cortas. El drawdown anual del sistema de tendencia pasó de unos 75 k$/año antes de 2006 a unos 275 k$/año después.

**Qué significaría aquí.** Una serie por activo de «tendencia por horizonte» como eje de régimen barato y como pista de marco temporal (las tendencias cortas han sido más fiables recientemente). Se combina con el mapa de tendencia.

**Estado.** AMPLÍA (mapa condicional, motor de regímenes) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 2

#### Modelo de análogos: superponer una época pasada
**Fuente.** Schwager, *Market Wizards* (Jones), p. 67.

**Qué dice.** El mercado de los 80 superpuesto al de los años 20 mostró una correlación notable y «clavó» el desplome de 1987.

**Qué significaría aquí.** Un estudio de vecinos más próximos: para la ventana actual de un activo, las k ventanas históricas más parecidas (retornos y volatilidad normalizados) y qué vino después, frente a una nula de ventanas al azar. Casi seguro sobreajustado (un único acierto famoso es el «ejemplo bien elegido» en estado puro); solo como curiosidad con nula estricta.

**Estado.** NUEVA — **Tipo.** estudio — **Locura.** 3 — **Valor.** 1

### 4.2 · Probar el bloque del dueño antes de la plantilla

#### Tarjeta de información del bloque: P(resultado | señal) frente a P(resultado | sin señal)
**Fuente.** Aronson, *Evidence-Based TA*, p. 73-79 (tabla de enfermeras de Smedslund, p. 77); Schwager, *New Market Wizards* (Eckhardt), p. 51-52; Schwager, *Stock Market Wizards* (Shaw), p. 143; Tharp, *Trade Your Way*, p. 24-25, 31, 71; Schwager, *Market Wizards* (O'Neil), p. 108-109; web: Alphalens (https://github.com/quantopian/alphalens ; https://alphalens.ml4trading.io/notebooks/overview.html).

**Qué dice.** La gente juzga una señal por la casilla confirmatoria (señal y resultado a la vez) e ignora las otras tres. En la tabla de Smedslund (37/17/33/13) P(enfermedad | síntoma) = 0,685 y P(enfermedad | sin síntoma) = 0,717, es decir, ninguna relación, y el 85% de las enfermeras vio una. La prueba correcta usa las cuatro casillas (chi-cuadrado sobre la tabla 2x2). Eckhardt: «si el 85% de techos y suelos tienen la propiedad X, pero X aparece también en otros sitios, usarla como señal te destrozará». Tharp: casi nadie mide con qué frecuencia sigue el resultado a una señal; un patrón puede ir seguido de un gran movimiento solo el 20% de las veces. LeBeau-Lucas: una entrada al azar acierta 45-55% a horizontes fijos; una real, 55% o más, sobre todo a 1-5 días. La versión web es Alphalens: tratar la condición como factor, retornos futuros a 1..N barras por cuantil, curva de decaimiento del coeficiente de información y rotación.

**Qué significaría aquí.** Entre los pasos bloque y plantilla, medir la condición fija sola sobre las barras de `build`: tasa de disparo, retorno futuro y MFE/MAE (la máxima excursión favorable y adversa) a h barras cuando la condición es verdadera frente a falsa y frente a disparos colocados al azar con la misma tasa, por dirección y horizonte, con p de permutación. Si la distribución condicional es igual a la incondicional, el hueco aleatorio de SQX cargará con toda la estrategia y la idea del dueño no se estará probando. Minutos de Python, cero CPU de SQX, y un prior por idea para el ledger. No bloquea: la condición fija puede ser legítimamente un filtro (ver la ficha siguiente).

**Estado.** NUEVA (entryQuality mide MFE/MAE de las entradas de estrategias terminadas; nada mide el bloque solo antes de construir) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 5

#### Evaluar la condición fija como filtro aplicado a entradas aleatorias
**Fuente.** Faith, *Way of the Turtle*, p. 64-72; Schwager, *Stock Market Wizards* (Minervini), p. 94.

**Qué dice.** El E-ratio a n días es la media de MFE/ATR dividida entre la media de MAE/ATR tras la señal. Entrada aleatoria: E5 1,01, E50 0,997. 70.000 entradas aleatorias restringidas por un filtro de tendencia (largo solo si EMA50 > EMA300) dan E70 = 1,27, más que la ruptura sola (1,20); ruptura más filtro 1,33 y E120 cerca de 1,6. El valor del filtro se mide aparte, alimentándolo con entradas aleatorias. Minervini: dardos sobre las 200 acciones de mayor fuerza relativa con un stop del 10% ganarían dinero.

**Qué significaría aquí.** Puntuar la condición fija como permiso aplicado a las entradas del mono: ¿sube el E_n o la esperanza de entradas aleatorias? Aísla lo que aporta el bloque del dueño sin necesitar el hueco aleatorio, y ordena candidatas a condición fija antes de construir. El E-ratio con banda aleatoria ya existe en entryQuality (`eratio.py`) para estrategias terminadas; lo nuevo es aplicarlo al bloque desnudo como filtro.

**Estado.** AMPLÍA (entryQuality `eratio.py`; escalera del mono) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 5

#### Curva de potencia de la entrada: P&L abierto medio por barras desde la entrada
**Fuente.** Fitschen, *Building Reliable Trading Systems*, p. 45-64; Faith, *Way of the Turtle*, p. 64-71.

**Qué dice.** Para una regla de entrada, acumular el beneficio abierto medio de TODAS sus señales desde el día 0 al 150 en toda la cesta, comparando entradas con la misma retrospectiva (10/20/40/80). Se tabulan pico, número de entradas, pico x entradas, beneficio máximo por día y el día en que ocurre. En materias primas ganan Donchian y ruptura de 2 desviaciones; la media simple y el estocástico son flojos. Las entradas populares muestran un RETRASO: la media de 10 días no es rentable hasta el día 20. Faith: una ruptura de 20 días tiene E5 0,99 y E70 1,20; la ventaja solo existe en el horizonte propio del sistema, y por debajo de 10 días es menor que 1 (ventaja contratendencia a corto).

**Qué significaría aquí.** Un estudio a nivel de plantilla sobre la condición fija: la curva de potencia por activo y marco frente a la de entradas aleatorias. Da (a) si la condición empuja algo antes de que SQX añada nada, (b) el horizonte natural (día pico) para la salida de la plantilla, (c) una firma de retraso que sugiere entrada con límite o retrasada, y (d) si la misma señal tiene una ventaja contratendencia temprana que otra plantilla podría operar. Superponer la mediana de permanencia de la estrategia sobre la curva e(k) muestra si la salida corta antes de que madure la ventaja.

**Estado.** AMPLÍA (entryQuality tiene MFE/MAE y e(k) frente a aleatorio; falta el perfil temporal completo del bloque) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 5

#### Salida estándar para comparar familias de entrada en igualdad
**Fuente.** Katz y McCormick, *Encyclopedia of Trading Strategies*, p. 77-78, 86; Kirkpatrick y Dahlquist (CMT), p. 267.

**Qué dice.** Para comparar entradas se fija la salida: stop 1 ATR(50), objetivo 4 ATR(50), máximo 10 barras, todas las salidas al cierre para evitar ambigüedad dentro de la barra. Stops y objetivos en unidades de volatilidad; tamaño igualado a volatilidad constante en dólares y sin capitalización, para que los t-tests sobre retornos en dólares sean válidos y se vea si el sistema decae. El CMT: una salida por tiempo da el mismo peso a todas las entradas probadas.

**Qué significaría aquí.** Un «banco de familias»: para cada familia del ledger, evaluar su condición fija sola con la salida estándar de Katz en cada activo, un número comparable por familia x activo x marco antes de cualquier búsqueda en SQX. Decide qué familias merecen CPU.

**Estado.** AMPLÍA (tabla de rendimiento del ledger, entryQuality) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 4

#### Criba del vocabulario de bloques por consistencia entre mercados
**Fuente.** Williams, *Long-Term Secrets*, p. 238-240.

**Qué dice.** Comprar al cierre si cierra en el 65% superior del rango y salir 5/10/15/20 días después fue rentable en todos los mercados probados. Las formaciones de velas más alcistas, probadas igual, no funcionaron entre mercados. Comprar nuevos máximos de X días también es rentable.

**Qué significaría aquí.** Un bloque candidato se gana su sitio en el vocabulario solo si su retorno a horizonte fijo bate al mono en la mayoría de los 9 mercados relacionados: el paso crossmarket aplicado a bloques sueltos, antes de construir. Poda el espacio de búsqueda del generador. Probablemente las velas caen y la fuerza de cierre pasa.

**Estado.** AMPLÍA (crossmarket, aplicado aguas arriba a nivel de bloque) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 4

#### Probar la polaridad inversa de la condición fija a nivel de familia
**Fuente.** Aronson, *Evidence-Based TA*, p. 21-22; Fitschen, *Building Reliable Trading Systems*, p. 134-137 frente a Katz y McCormick, p. 148-150.

**Qué dice.** Para cada regla «tradicional» probar también la inversa (salida negada), porque un patrón que se cree alcista puede ser bajista; con entradas sin interpretación obvia, ambas direcciones son candidatas. Duplica el universo de reglas y la multiplicidad. Caso real: Fitschen encuentra rentable DESVANECER las divergencias en materias primas, mientras Katz encuentra rentable operar la divergencia del MACD. El signo de una señal de manual no está resuelto y depende de la definición.

**Qué significaría aquí.** Construir la plantilla en las dos polaridades (idea del dueño y su negación) como control: si la negada produce estrategias que pasan la puerta a un ritmo parecido, la condición fija no lleva información y trabaja el hueco aleatorio. Cuenta en el ledger como 2x ensayos. Cualquier bloque de divergencia se prueba en ambos sentidos y con ambas definiciones.

**Estado.** AMPLÍA (structure hace ablación e inversión por estrategia; nada prueba la polaridad a nivel de familia) — **Tipo.** generación — **Locura.** 1 — **Valor.** 3

#### Solapamiento entre la condición fija y la del hueco aleatorio
**Fuente.** Aronson, *Evidence-Based TA*, p. 42-46.

**Qué dice.** La confianza sube cuando las entradas coinciden, pero solo está justificado si no son redundantes; muchos indicadores miden lo mismo con otro nombre. El razonamiento configural humano llega a unas 3 variables.

**Qué significaría aquí.** Una comprobación previa: correlación de las series booleanas de la condición fija y de las del grupo del hueco aleatorio sobre `build`. Una plantilla con RSI>70 Y Estocástico>80 tiene una idea dos veces. La ablación de structure lo mostraría a posteriori.

**Estado.** YA EXISTE en parte (redundancia de la puerta, ablación de structure) / AMPLÍA a condiciones dentro de la estrategia — **Tipo.** estudio — **Locura.** 0 — **Valor.** 2

#### Probar los vecinos de cualquier número «mágico»
**Fuente.** Fitschen, *Building Reliable Trading Systems*, p. 144-149.

**Qué dice.** Entradas largas en acciones al 23,6% de retroceso del último tramo Donchian de 14 días parecían buenas (unos 32% anualizados a 5 días), pero un barrido de 5%, 10%... puso el pico en 21%, no en 23,6%. En materias primas los retrocesos de Fibonacci señalaban reversión de tendencia, no continuación, con pérdidas crecientes al 38,2%.

**Qué significaría aquí.** Regla para bloques construidos sobre constantes «especiales» (Fibonacci, números redondos, 50%): barrido tipo SPP alrededor de la constante; si el valor especial no es especial, se abandona la historia y se trata como un parámetro más.

**Estado.** YA EXISTE (vecindario de parámetros de SPP), aplicado a la autoría de bloques — **Tipo.** proceso — **Locura.** 0 — **Valor.** 2

### 4.3 · Reglas para diseñar plantillas y priors por familia

#### Plantillas solo con condición fija frente a condición fija más hueco aleatorio
**Fuente.** Chan, *Quantitative Trading*, p. 26-27; Chan, *Algorithmic Trading*, p. xi-xii, 4-7; Schwager, *Stock Market Wizards* (Shaw), p. 143, 145, 167.

**Qué dice.** Chan: redes neuronales, árboles y ALGORITMOS GENÉTICOS ajustan muchos parámetros y «inevitablemente funcionaron fatal en adelante»; los datos financieros tienen pocos puntos independientes. Lo que funciona tiene base económica, pocos parámetros, es lineal y se optimiza en ventana móvil. En vez de lanzar indicadores contra una serie, hay que destilar su propiedad fundamental con un modelo simple; «un modelo con pocos parámetros pero muchas reglas es igual de vulnerable». Shaw: no busca patrones a ciegas; parte de una hipótesis estructural y la prueba, y lo más frecuente es no poder rechazar la eficiencia.

**Qué significaría aquí.** Dos cosas. (1) Un A/B controlado en el ledger: plantillas con la condición fija y cero condiciones libres frente a fija más hueco aleatorio, comparando rendimiento frente al mono tras multiplicidad. (2) Como titular de cada superviviente, qué parte de su edge viene de la condición fija (la hipótesis) y qué parte del hueco aleatorio (lo minado); la ablación de structure ya lo permite.

**⚠ Contradice.** El hueco aleatorio y la búsqueda genética son minería ciega por diseño (Chan, *Quantitative Trading*, p. 26-27; *Algorithmic Trading*, p. xi-xii; Shaw, SMW p. 143). El ledger y la deflación lo compensan estadísticamente; el A/B lo zanjaría con datos.

**Estado.** AMPLÍA (ledger, diseño de plantillas, ablación de structure) — **Tipo.** proceso · generación — **Locura.** 1 — **Valor.** 4

#### Rejilla preparación x disparador («baraja cargada»)
**Fuente.** Williams, *Long-Term Secrets*, p. 104, 113, 117-120, 128; *New Frontiers in Technical Analysis*, p. 94-116; Tharp, *Trade Your Way*, p. 72, 125-126.

**Qué dice.** Williams nunca opera un patrón solo («precio prediciendo precio»): exige una preparación (día de la semana, día del mes, tendencia de otro mercado, sobrecompra) y luego un disparador (Oops!, smash day, ruptura GSV). Ejemplo: Oops! en bonos solo con la media de 9 días cayendo, 81% y 373 $; Oops! en S&P tras el día 17 del mes, ventana documentada por Merrill desde 1962. *New Frontiers*: sesgo, preparación, disparador y seguimiento, con la comparación «mismas operaciones ignorando el sesgo». Tharp: lo que predice un giro solo abre una ventana; se entra con una ruptura de volatilidad dentro de ella y se sale si la ventana pasa sin beneficio.

**Qué significaría aquí.** La forma «una condición fija + un hueco aleatorio» es exactamente preparación x disparador. Generar sobre una rejilla 2-D (filas: preparaciones de calendario, entre mercados o régimen; columnas: disparadores) y registrar el rendimiento por celda en el ledger, extendiendo la tabla familia x activo al par preparación x disparador. Marcar las preparaciones con prior externo (literatura previa) para darles otro prior en el meta-modelo.

**Estado.** AMPLÍA (forma de plantilla; tabla de rendimiento del ledger) — **Tipo.** proceso · generación — **Locura.** 1 — **Valor.** 4

#### Regla de ortogonalidad: el hueco aleatorio usa otra familia de datos
**Fuente.** Tharp, *Trade Your Way* (LeBeau), p. 179-184; Williams, *Long-Term Secrets*, p. 233-237; Kirkpatrick y Dahlquist (CMT), p. 537.

**Qué dice.** Los filtros construidos sobre la misma serie de precio solo sobreajustan («casi puedes predecir la historia con un oscilador, una media y ciclos»); varios indicadores ayudan si cada uno se basa en un TIPO de dato distinto: tiempo, secuencia de precio, fundamental, volumen, amplitud, volatilidad. «Operar un índice solo con precio es muy difícil porque tu competencia usa mucha más información.» Williams: «no se puede predecir A con A»; comprar el S&P solo cuando los bonos rompen su máximo de 14 días ganó 141.792 $, mientras la ruptura del propio S&P era miserable, y cualquier longitud de canal del bono funcionaba.

**Qué significaría aquí.** Restringir el grupo del hueco aleatorio a una familia de datos distinta de la condición fija (fija de patrón de precio, hueco de tiempo, régimen de volatilidad, otro mercado o calendario) y guardar en el ledger el par de familias de cada plantilla para responder si los pares ortogonales baten a los de la misma familia frente al mono. Abre un espacio que el constructor de precio propio no alcanza: señales sin ningún precio del activo operado.

**⚠ Contradice.** El constructor usa solo el OHLC del activo operado; lead-lag está aceptado, pero el argumento del libro es más fuerte: las mejores señales pueden no contener precio del activo (Williams, p. 233-237).

**Estado.** NUEVA (el tipo de dato del hueco no está restringido ni registrado) — **Tipo.** generación — **Locura.** 1 — **Valor.** 4

#### Combinar un elemento de tendencia con uno de contratendencia, nunca dos iguales
**Fuente.** Katz y McCormick, p. 106, 121-122, 128-130; Fitschen, *Building Reliable Trading Systems*, p. 89-105.

**Qué dice.** Los mejores modelos de Katz mezclan ambos: comprar un retroceso con límite tras una señal de tendencia, o poner una entrada con stop o filtro ADX sobre un modelo contratendencia. Añadir un filtro de tendencia a un modelo ya de tendencia es redundante y solo encarece la entrada. Rebote en una media creciente y media simple con entrada en stop fueron de los mejores. Los efectos interactúan: los del tipo de orden cambiaban entre SMA, EMA y triangular y entre dentro y fuera de muestra. Fitschen: comprar la apertura tras un cierre bajista y salir en la apertura siguiente ganaba 19 $ por operación; con cierre > cierre de hace 20 días, 36 $ largo y 21 $ corto.

**Qué significaría aquí.** Clasificar cada bloque como tendencia o contratendencia y restringir el grupo del hueco aleatorio al tipo opuesto al de la condición fija, eligiendo el tipo de orden en consecuencia (límite para fijas de tendencia, stop para fijas contratendencia). Regla de autoría de grupos aleatorios, barata. Las ablaciones deben leerse como interacciones, no como efectos que se suman.

**Estado.** NUEVA — **Tipo.** generación — **Locura.** 1 — **Valor.** 4

#### El tipo de orden como canal: ruptura con stop, retroceso con límite
**Fuente.** Katz y McCormick, p. 90-92, 155-177; Schwager, *New Market Wizards* (Eckhardt), p. 51; Schwager, *Market Wizards* (Seykota), p. 80-81.

**Qué dice.** La misma ruptura de canal, entrando al día siguiente con límite en el punto medio de la barra de ruptura, pasó dentro de muestra de negativa a +33% anual; fuera de muestra siguió negativa pero mucho mejor («el mercado retrocedía tras la mayoría de rupturas»). Algunos mercados responden a límites (S&P, eurodólar) y otros no. Para modelos estacionales la mejor orden fue el stop (confirmación). Eckhardt, en contra: comprar retrocesos es comodidad psicológica; si el retroceso es grande, la tendencia tiene más probabilidad de girar; comprar fuerza. Seykota: entrada por encima del mercado, nunca en reacciones.

**Qué significaría aquí.** Un estudio de plantilla: misma condición fija, entrada a mercado frente a stop frente a límite a un x% de retroceso, aislando el canal del tipo de orden. Y un A/B de familias en el ledger: mismo filtro de tendencia, entrada en ruptura frente a entrada en retroceso, por activo. Los libros discrepan; que lo zanje el ledger.

**Estado.** AMPLÍA (structure tiene inversión de orden) — **Tipo.** generación — **Locura.** 0 — **Valor.** 4

#### Tarjeta de mecanismo: quién paga, qué predice y dónde debe fallar
**Fuente.** Aronson, *Evidence-Based TA*, p. 332-333, 376-386; Covel, *Trend Following*, p. 115-120, 271-272; Schwager, *New Market Wizards* (Trout), p. 65; web: Arnott, Harvey y Markowitz, protocolo de backtesting (https://people.duke.edu/~charvey/Research/Published_Papers/P138_A_backtesting_protocol.pdf).

**Qué dice.** Un backtest rentable sin teoría es un resultado aislado y quizá afortunado. Preferir edges que son el pago por un servicio (transferencia de riesgo, liquidez), más duraderos que las ineficiencias; la teoría predice dónde debe funcionar y dónde no (Kestner 1990-2001: Sharpe de tendencia 0,604 en 29 futuros frente a 0,046 en 31 acciones). Druz: saber a quién le vas a quitar el dinero. Lo: todo se describe por su valor añadido. Trout escaneaba todos los mercados y desfases, pero una relación tenía que «tener sentido» (la libra de hace 40 días prediciendo el S&P se tiraba aunque acertara). El protocolo de Arnott-Harvey-Markowitz pide motivación económica ex ante.

**Qué significaría aquí.** Un campo obligatorio en la autoría de plantillas: qué prima o sesgo cosecha (presión de coberturas, provisión de liquidez, infrarreacción a noticias, anclaje), quién paga («seguidores tardíos que entran en la ruptura») y la predicción falsable («funciona en oro y Brent, no en índices»; «el beneficio se agrupa cerca de publicaciones»; «falla en el tercil de baja volatilidad»). Así crossmarket y el mapa condicional prueban la predicción en vez de solo describir, y la tabla de rendimiento del ledger se corta por mecanismo. El ledger puede medir si las familias con justificación sobreviven más que las sin ella, es decir, si «tener sentido» es un prior útil.

**Estado.** NUEVA (las plantillas llevan lógica, no mecanismo) — **Tipo.** proceso — **Locura.** 1 — **Valor.** 4

#### Parámetros en unidades de volatilidad y umbrales como percentil de su propia historia
**Fuente.** Aronson, *Evidence-Based TA*, p. 154-155, 158; Schwager, *Stock Market Wizards* (Cook), p. 61-62; Kirkpatrick y Dahlquist (CMT), p. 258-259; Covel, *Trend Following*, apéndice E p. 383 (Mulvaney).

**Qué dice.** Chang y Osler fijaron sus 10 umbrales de zigzag como V x {1,5 ... 6,0}, con V la desviación de los cambios diarios de 100 días, para que un algoritmo sirva a instrumentos de volatilidad distinta. Cook usaba el percentil 5 y 95 de la historia de su TICK acumulado como sobreventa y sobrecompra. El CMT: los filtros de % fijo ignoran la volatilidad, y la desviación del precio incluye la tendencia; usar ATR o la volatilidad alrededor de la tendencia. Mulvaney: la volatilidad se puede prever y la dirección no; detectar tendencias nacientes cuando el cambio de precio supera la volatilidad estimada.

**Qué significaría aquí.** Una convención de autoría: todo nivel en unidades de ATR o de desviación de residuos, umbrales como percentil móvil del propio indicador, nunca desviación de precios en bruto (el ancho de Bollinger en un mercado con tendencia es en parte tendencia). Bloque base: «movimiento de k x ATR en N barras». Deberían transferirse mejor en crossmarket y crossTF; comparar en el ledger la supervivencia entre mercados de estrategias en unidades de ATR frente a unidades brutas.

**Estado.** AMPLÍA (crossTF reescala periodos; nada impone umbrales en unidades de volatilidad) — **Tipo.** generación — **Locura.** 1 — **Valor.** 3

#### Prior por clase de activo y por lado
**Fuente.** Aronson, *Evidence-Based TA*, p. 381-386; Katz y McCormick, p. 86-92, 104-108, 124-129, 144-152; Faith, *Way of the Turtle*, p. 216-219; Fitschen, p. 34-35; Schwager, *Market Wizards* (Kovner), p. 43; (Dennis), p. 54.

**Qué dice.** La tendencia paga en futuros de materias primas y divisas (presión de coberturas), no en acciones; la contratendencia a corto paga en acciones (prima de liquidez), sobre todo tras caídas con volumen decreciente (Cooper: 44,95%/año largo-corto frente a 17,91% del B&H). Katz: rupturas rentables en ambas muestras en divisas y petróleo; metales, ganado y granos perdían; restringir a divisas fue lo único que hizo rentable una ruptura fuera de muestra tras costes (36% dentro, 17,7% fuera). Los largos baten a los cortos casi siempre en materias primas; Fitschen lo confirma: los largos ganan 2-3 veces lo de los cortos. Faith: divisas y tipos tienen las tendencias más limpias, los mercados especulativos (oro, plata, crudo) son más difíciles, los índices agregados los peores; dentro de una clase las diferencias son sobre todo azar. Kovner: los índices tienen mucha más contratendencia a corto; las materias primas tienden por escasez física. Dennis: los índices están cerca del azar.

**Qué significaría aquí.** Un prior para la tabla de rendimiento familia x activo: tendencia primero en FX, Brent y metales; reversión corta en CFD de índices (con un bloque nuevo «caída con tick volume decreciente»); largos y cortos evaluados por separado en materias primas, y la construcción solo larga como familia legítima. Comprobar explícitamente «los CFD de índices rinden menos en plantillas de tendencia» y agrupar resultados por clase, no por mercado.

**Estado.** AMPLÍA (tabla de rendimiento del ledger aceptada; añade un prior con teoría y un nivel de clase) — **Tipo.** generación — **Locura.** 1 — **Valor.** 3

#### Prior por familia de indicador: el marcador de Katz y los osciladores
**Fuente.** Katz y McCormick, p. 144-152, 203-212, 349-356; Schwager, *New Market Wizards* (Eckhardt), p. 51-52; Schwager, *New Market Wizards* (Trout), p. 68; Schwager, *Market Wizards* (Hite), p. 93.

**Qué dice.** Promediado por familia, $ por operación fuera de muestra frente a entradas aleatorias (-2.100 ± 300): reglas evolucionadas por GA +3.271 $; redes pequeñas -860; estacionalidad -966; medias (cruce, pendiente, soporte) unos -1.500, algo mejor que el azar; rupturas cerca del azar fuera de muestra; osciladores y ciclos iguales o peores; RSI sobrecompra/sobreventa claramente peor que el azar. Solo la divergencia del MACD con límite fue rentable en ambas muestras (12,5% y 19,5% anual). El RSI de reversión con límite sí funcionó en metales. Eckhardt, Trout y Hite, tres fuentes sistemáticas independientes: los osciladores de sobrecompra y sobreventa tienen esperanza casi nula («lo que ganan en consolidaciones lo pierden en tendencias»). Los ciclos flexibles se ajustan a cualquier serie; el Fourier riguroso no encuentra ciclos sistemáticos.

**Qué significaría aquí.** Prior del ledger: grupos del hueco aleatorio dominados por cruces de umbral de RSI o estocástico probablemente malgastan búsqueda; prior negativo para bloques de ciclos; la búsqueda genética en sí (lo que hace SQX) fue la mejor familia, lo que apoya bloques compuestos frente a los de manual. Una predicción falsable para el mapa condicional: una estrategia de sobrecompra/sobreventa debe ganar en el tercil de poca tendencia y perder en el de mucha; si no muestra esa división, su edge viene de otra parte.

**Estado.** AMPLÍA (tabla de rendimiento del ledger, mapa condicional) — **Tipo.** generación — **Locura.** 0 — **Valor.** 3

#### Mercados menos observados y nichos de poca capacidad
**Fuente.** Schwager, *Market Wizards* (Kovner, Marcus), p. 20-21, 36-38, 43; Chan, *Quantitative Trading*, p. 27; web: Neely, Weller y Ulrich, AMH en FX (https://www.sciencedirect.com/science/article/abs/pii/S0378426602003990 ; https://s3.amazonaws.com/real.stlouisfed.org/wp/2011/2011-021.pdf).

**Qué dice.** Kovner: cuanto más observado un patrón, más señales falsas; los cruces son mejores porque «mucha menos gente los mira». Chan: preferir estrategias de capacidad demasiado pequeña para instituciones. Neely-Weller-Ulrich: el beneficio ajustado a riesgo de reglas de medias y filtros en FX cayó de más del 3%/año a finales de los 70 y 80 a cerca de 0 en los 90; las reglas menos estudiadas decayeron menos, y las complejas persisten más que las simples.

**Qué significaría aquí.** Un A/B barato por elección de activo: familias de ruptura o tendencia en cruces (EURJPY, AUDNZD...) frente a mayores, mismo marco y costes; si «menos observado» importa, los cruces darán más supervivientes que baten al mono por ensayo. Prior en contra de cruces de medias simples en mayores (la ventana de Dukascopy, desde 2003, ya es posterior al decaimiento). Tensión con la parsimonia: el edge restante estaría en construcciones menos estudiadas o más complejas.

**Estado.** AMPLÍA (tabla de rendimiento del ledger) — **Tipo.** generación — **Locura.** 1 — **Valor.** 3

#### Familia de «puntos focales»: las señales por defecto de los indicadores más usados
**Fuente.** *New Frontiers in Technical Analysis*, p. 14-18, 44-45.

**Qué dice.** Datos de uso de Bloomberg: RSI 44% del uso de indicadores, MACD 22%, Bollinger 12%, estocástico 9%, DMI 5%, Ichimoku 4,5% (el 54% de sus usuarios en Asia). Señales por defecto: RSI que recruza 30/70, cruce MACD/señal, cierre fuera de Bollinger, cruce de %D en 20/80, +DI > -DI con ADX > 25.

**Qué significaría aquí.** Una familia con los parámetros exactos de manual (RSI(14) 30/70, MACD(12,26,9), BB(20,2)) por activo y marco frente al mono. O funcionan (se autocumplen, el flujo se agrupa en los puntos focales) o están arbitrados (y entonces la hipótesis es DESVANECERLOS). SQX aleatoriza parámetros y rara vez cae justo en los valores por defecto. Extensión loca: Ichimoku en cruces de yen solo en sesión de Tokio.

**Estado.** NUEVA — **Tipo.** generación — **Locura.** 2 — **Valor.** 3

#### Gramática completa de eventos de umbral para osciladores
**Fuente.** Aronson, *Evidence-Based TA*, p. 421-429, 438-440.

**Qué dice.** Un oscilador con umbral superior e inferior tiene 4 eventos de cruce; una regla binaria es un par de ellos, lo que da 12 tipos de regla incluidas las inversas. 12 tipos x 39 entradas x 2 desplazamientos x 3 retrospectivas = 2.808 reglas. Los mismos 12 tipos sirven para divergencias.

**Qué significaría aquí.** Con la regla 11 (ambiguo, preguntar): «cruza por encima de 70» tiene varias lecturas. La tabla de 12 tipos es un menú listo para enseñar al dueño, y un grupo aleatorio con los 12 tipos deja que SQX los pruebe, con la multiplicidad registrada.

**Estado.** AMPLÍA (autoría con sqx-custom-block y sqx-random-group) — **Tipo.** generación — **Locura.** 0 — **Valor.** 2

#### Entrar escalonado: solo si cada tramo es una buena operación por sí mismo
**Fuente.** Fitschen, *Building Reliable Trading Systems*, p. 165-167; Chan, *Algorithmic Trading*, p. 5-6, 72-74; Schwager, *New Market Wizards* (Lipschutz), p. 31.

**Qué dice.** Fitschen: comprar a 1 desviación bajo la media de 10 días y añadir a 2 desviaciones mejoró las estadísticas porque la entrada a 2 desviaciones es mejor por sí misma; nunca vio una señal de continuación más fuerte que una buena entrada de tendencia. Chan: con probabilidad constante de una excursión más profunda, entrar todo en un nivel siempre gana a promediar dentro de muestra, pero como la volatilidad no es constante, escalonar puede dar mejor Sharpe fuera de muestra; la reversión lineal mantiene una posición proporcional al z-score, sin umbrales que ajustar. Lipschutz gana acertando solo el 20-30% escalando dentro y fuera.

**Qué significaría aquí.** Para la fábrica de variantes: una variante de entrada escalonada solo es legítima si la condición del añadido pasa las mismas pruebas sola; si no, es apalancamiento disfrazado. La búsqueda genética siempre preferirá un umbral único dentro de muestra; si se permiten entradas múltiples, compararlas solo fuera de muestra. Un estudio en Python puede comparar las operaciones de umbral con un tamaño lineal (-k x z) sobre la misma señal para ver si su información es monótona.

**Estado.** NUEVA — **Tipo.** generación — **Locura.** 1 — **Valor.** 2

### 4.4 · El generador de SQX y generadores alternativos

#### A/B de la función de aptitud de la búsqueda genética
**Fuente.** Katz y McCormick, p. 66-67, 257-278; Fitschen, *Building Reliable Trading Systems*, p. 67-68, 107-117; Kirkpatrick y Dahlquist (CMT), p. 604; Covel, *Trend Following*, p. 102-104, 281, 295.

**Qué dice.** El beneficio neto como aptitud premia sistemas que solo operan los desplomes (2-3 operaciones en 10 años). El estadístico t (media sobre error estándar) combina beneficio, número de operaciones y variabilidad y «funciona bastante bien»; Katz usaba un t reescalado de retornos diarios sobre toda la cartera. Fitschen: desarrollar con una métrica de riesgo desde el primer paso; ganancia sobre dolor = beneficio anual medio dividido entre la media de los N mayores drawdowns (N = años). Rehacer los mismos sistemas con beneficio por operación como criterio dio al de materias primas un 50% más de beneficio pero 4 veces el drawdown anual medio y 6 veces el máximo. El CMT: la evolución explota rarezas poco comunes de los datos. Covel: el Sharpe penaliza la volatilidad al alza; quitar los mejores retornos SUBE el Sharpe (Harding); desviación típica 12,5 frente a semidesviación 5,8 en seguidores de tendencia.

**Qué significaría aquí.** «La métrica que debe optimizar la búsqueda genética» es una de las decisiones del dueño. Experimento: misma plantilla, mismos datos, aptitud beneficio neto frente a t o SQN (Sharpe x raíz del número de operaciones) frente a ganancia sobre dolor, comparando supervivencia en oos1 por hora de CPU en el ledger, como una réplica de la variación de semilla. Una aptitud tipo Sharpe prefiere sistemáticamente las estrategias de convexidad corta; conviene mirar Sortino o el cociente desviación/semidesviación junto al Sharpe.

**Estado.** NUEVA como experimento — **Tipo.** generación — **Locura.** 0 — **Valor.** 4

#### Construir con un solo conjunto de parámetros sobre una cesta de mercados
**Fuente.** Katz y McCormick, p. 45, 80, 227-255, 271-272; Fitschen, *Building Reliable Trading Systems*, p. 24; Covel, *Trend Following*, p. 289.

**Qué dice.** Katz no optimizaba por mercado, solo para toda la cartera: «un buen sistema debería poder operar variedad de mercados con los mismos parámetros; optimizar por mercado lleva a sobreajuste». La optimización conjunta multiplica la muestra. Su red neuronal entrenada en toda la cartera funcionó mejor que el intento en un solo mercado, que «no funciona en absoluto». Las estrategias de sucesos raros (43 operaciones en 10 años sobre 36 mercados) solo se pueden juzgar agrupadas. Fitschen llama trampa de sobreajuste al paradigma de un gráfico y desarrolla sobre cestas de 37-56 mercados. Houthakker probó tendencia en un contrato y concluyó que no funcionaba.

**Qué significaría aquí.** Hoy se construye en un activo y crossmarket es un retest posterior. La alternativa es una aptitud agrupada sobre una cesta relacionada durante la construcción (verificaciones de mercados adicionales dentro de la construcción de SQX, o reordenar en Python por métricas agrupadas). Pierde edges específicos del activo; gana tamaño de muestra. Experimento para familias que se esperan universales (tendencia, ruptura).

**⚠ Contradice.** Construir en un solo activo en H1/H4 es, para Katz (p. 80) y Fitschen (p. 24), una muestra demasiado pequeña; crossmarket debería estar en el objetivo, no solo como retest.

**Estado.** AMPLÍA (crossmarket pasa de filtro a objetivo) — **Tipo.** generación — **Locura.** 1 — **Valor.** 4

#### Confluencia de estrategias que no pagan costes por separado
**Fuente.** Schwager, *Stock Market Wizards* (Shaw), p. 142, 168; Schwager, *Market Wizards* (Hite), p. 90, 94.

**Qué dice.** Shaw: una ineficiencia sola puede no superar los costes; cuando varias coinciden, el beneficio esperado puede superarlos. Ilustración de Schwager: dos estrategias de +100 $ brutos frente a 110 $ de coste; el subconjunto donde ambas coinciden da +180 $. Hite mantiene sistemas «no tan buenos por sí mismos» por su baja correlación.

**Qué significaría aquí.** Por activo y marco, tomar la población que batió al mono en P&L BRUTO pero falló tras costes, y medir la esperanza neta del subconjunto de barras donde k ≥ 2 de ellas señalan la misma dirección. Necesita control de multiplicidad (los subconjuntos son una búsqueda nueva que el ledger debe contar). Convertiría trabajo descartado en supervivientes.

**⚠ Contradice.** La puerta juzga cada estrategia sola frente a costes y nulas y borra las que fallan (Shaw, SMW p. 142); habría que guardar un grupo de «casi aprobadas».

**Estado.** NUEVA — **Tipo.** estudio · generación — **Locura.** 2 — **Valor.** 4

#### Inflar las comisiones durante la construcción
**Fuente.** Katsanos, *Intermarket Trading Strategies*, p. 240.

**Qué dice.** El soporte de NeuroShell sugería subir las comisiones durante la optimización «para penalizar más las malas operaciones y que el sistema las evite», devolviendo el exceso después. El GA además descartaba entradas moderadamente correlacionadas (r≈0,5).

**Qué significaría aquí.** Una palanca de generación barata: construir en `build` con spread x1,5-2 y retestear a costes reales en oos1. Los supervivientes quedan sesgados hacia más edge por operación (lleva edge-por-coste al generador). El multiplicador de coste es un parámetro de búsqueda y se registra en el ledger como otra búsqueda.

**Estado.** NUEVA — **Tipo.** generación — **Locura.** 2 — **Valor.** 3

#### Periodos muestreados en escala logarítmica y largo y corto construidos por separado
**Fuente.** Katz y McCormick, p. 257-278; Aronson, *Evidence-Based TA*, p. 398.

**Qué dice.** El GA de Katz es casi SQX: cromosoma de 3 genes (índice de plantilla + 3 parámetros), cruce solo entre genes, escala no lineal para buscar los periodos cortos (2, 3, 4) tan finamente como los largos (30, 50, 90), aptitud t sobre la cartera, largo y corto evolucionados por separado por la asimetría. El mejor modelo largo fue rentable fuera de muestra con los tres tipos de orden, pero con unas 4 operaciones al año en 36 mercados; el corto falló. «Restringir el número y la complejidad de las reglas es la clave para controlar el demonio del sobreajuste.» Aronson: rejillas geométricas (3, 5, 8, 12, 18, 27... razón 1,5), porque la sensibilidad de una retrospectiva va con su logaritmo.

**Qué significaría aquí.** Comprobar cómo muestrea SQX los rangos de periodo y pasar a escala logarítmica si es aritmética (una rejilla aritmética sobremuestrea periodos largos). Construir largo y corto por separado en materias primas e índices, donde se espera asimetría. El límite de reglas ya existe (fija + un hueco).

**Estado.** AMPLÍA (diseño de plantillas; configuración de la construcción) — **Tipo.** generación — **Locura.** 0 — **Valor.** 3

#### Meta-etiquetado y explicación por operación (SHAP)
**Fuente.** web: López de Prado, meta-labeling y triple barrera (https://www.newsletter.quantreo.com/p/the-triple-barrier-labeling-of-marco ; https://medium.com/@caneradilirfanoglu/advances-in-financial-machine-learning-part-3-backtesting-a9d70f0832c2); SHAP en finanzas (https://arxiv.org/pdf/2208.08790 ; https://rpc.cfainstitute.org/research/reports/2025/explainable-ai-in-finance).

**Qué dice.** Meta-etiquetado: el modelo primario da el lado (aquí, la estrategia de SQX) y un modelo secundario de ML predice P(la operación gana) a partir de rasgos en la entrada, para dimensionar u omitir. Las etiquetas de triple barrera (objetivo, stop, tiempo) ya tienen un análogo en `barrier.py` de nulls. SHAP sobre un modelo que predice «la operación gana» con rasgos del estado de entrada (volatilidad, tendencia, hora, día, distancia al fix, hueco, entropía) da una explicación por operación y, en global, qué estados llevan el edge; extiende el mapa condicional de cortes de una dimensión a interacciones.

**Qué significaría aquí.** Un estudio sobre las operaciones de los supervivientes, validado con CPCV (validación cruzada combinatoria con purga), nunca usado para seleccionar. El dueño aceptó el ledger como meta-modelo que da prior y nunca filtra; un meta-etiquetado que omite operaciones es un filtro y tendría que pasar la puerta como una estrategia nueva.

**Estado.** NUEVA (triple barrera existe en nulls) — **Tipo.** estudio · generación — **Locura.** 1 — **Valor.** 3

#### Clasificador universal entre mercados sobre rasgos de forma
**Fuente.** Katz y McCormick, p. 227-255; Katsanos, *Intermarket Trading Strategies*, p. 232-250.

**Qué dice.** Entradas de la red: 18 diferencias de precio con espaciado creciente, cada una dividida por la raíz del salto, y el vector escalado a longitud unidad (conserva la forma, quita la amplitud). Objetivos: el %K lento invertido en el tiempo y banderas de giro. 88.092 hechos de toda la cartera; tamaño elegido por correlación corregida por encogimiento con un N efectivo de 13.000-40.000, no mirando fuera de muestra. La mayoría se hundió fuera de muestra pero perdió mucho menos por operación que los perdedores típicos; la red pequeña con entrada en stop fue algo rentable. Katsanos: en FTSE, la regresión simple ganó; entre redes, las entradas más simples (ROC de los líderes) ganaron y añadir filtros convencionales empeoró.

**Qué significaría aquí.** Una familia de ML fuera de SQX: clasificador entre mercados sobre rasgos de forma normalizados, cuya salida se usa como indicador personalizado o filtro. Si alguna vez se alimenta un modelo con rasgos entre mercados, empezar con retornos simples de los líderes a 2-3 horizontes. Lección reutilizable: contar N efectivo (etiquetas solapadas son redundantes) y elegir la complejidad por encogimiento.

**Estado.** AMPLÍA (ledger como meta-modelo aceptado; familia nueva de ML) — **Tipo.** generación — **Locura.** 2 — **Valor.** 3

#### Minería de alfas con LLM desde el chat de plantillas
**Fuente.** web: AlphaAgent KDD 2025 (https://arxiv.org/html/2502.16789v2); Chain-of-Alpha (https://arxiv.org/pdf/2508.06312); QuantaAlpha (https://arxiv.org/pdf/2608.12841); AQuA (https://arxiv.org/pdf/2608.31041); «What survives honest evaluation?» (https://arxiv.org/abs/2608.27734).

**Qué dice.** AlphaAgent mide la originalidad por distancia de árbol sintáctico frente a los factores existentes, comprueba que el factor corresponde a la hipótesis y controla la complejidad. Hay variantes evolutivas y agentes que se mejoran solos (2026). En cambio, el artículo de 2026 que evalúa agentes LLM con herramientas sin look-ahead, registrando cada evaluación y deflactando por número de ensayos, encontró que TODAS las estrategias descubiertas por LLM fallaron la certificación (2 universos, 2 modelos frontera, hasta 100 candidatas, 5 ejecuciones).

**Qué significaría aquí.** El chat de la ventana que redacta plantillas podría proponer con una «distancia de originalidad frente a la librería» y escribir primero la hipótesis económica, con una comprobación de que el bloque la cumple. Pero cada propuesta del chat cuenta como ensayo en el ledger, igual que las de SQX.

**Estado.** NUEVA — **Tipo.** generación · proceso — **Locura.** 2 — **Valor.** 3

#### Pronósticos continuos en vez de dentro/fuera
**Fuente.** web: Carver, velocidad de operar (https://qoppac.blogspot.com/2020/04/how-fast-should-we-trade.html ; https://www.cxoadvisory.com/big-ideas/a-few-notes-on-systematic-trading/).

**Qué dice.** Pronósticos continuos escalados a media absoluta 10 y topados en ±20, en lugar de señales binarias; límite de velocidad: los costes no deben pasar de un tercio del Sharpe antes de costes.

**Qué significaría aquí.** SQX produce reglas binarias. Un estudio en Python podría convertir la señal de un superviviente en pronóstico continuo (por ejemplo, distancia al umbral en ATR) y ver si el tamaño proporcional mejora el riesgo ajustado. El límite de velocidad es materia de costes (sección R).

**Estado.** NUEVA — **Tipo.** generación — **Locura.** 1 — **Valor.** 2

#### Regresión simbólica como generador de condiciones
**Fuente.** web: PySR / SymbolicRegression.jl (https://arxiv.org/pdf/2305.01582).

**Qué dice.** Frontera de Pareto explícita entre precisión y complejidad al buscar fórmulas.

**Qué significaría aquí.** Un generador alternativo fuera de SQX para condiciones «de fórmula», cuyas salidas se convierten en bloques personalizados. Cada fórmula probada cuenta como ensayo.

**Estado.** NUEVA — **Tipo.** generación — **Locura.** 2 — **Valor.** 2

#### Modelos fundacionales de series temporales (Kronos)
**Fuente.** web: Kronos (https://arxiv.org/abs/2508.02739); evaluaciones (https://arxiv.org/pdf/2606.27100 ; https://arxiv.org/pdf/2607.05291).

**Qué dice.** Los modelos generales (TimesFM R² -2,8%, Chronos -1,4%) no sirven sin ajuste sobre retornos. Kronos (Tsinghua, NeurIPS 2025, 12.000 millones de velas de 45 bolsas) reporta mejor RankIC y un +22% de fidelidad como generador sintético.

**Qué significaría aquí.** Muy especulativo: su pronóstico como rasgo de régimen para el meta-etiquetado, o como generador de velas sintéticas para universos de estrés.

**Estado.** NUEVA — **Tipo.** generación · datos — **Locura.** 3 — **Valor.** 1

### 4.5 · Familias de un solo mercado: rupturas y volatilidad

#### Ruptura de volatilidad desde la apertura de sesión (apertura ± k x unidad de volatilidad)
**Fuente.** Williams, *Long-Term Secrets*, p. 57-61, 71-72, 121-129; Kirkpatrick y Dahlquist (CMT, Crabel), p. 385-387; web: Zarattini-Aziz ORB y réplica en CFD (https://www.mql5.com/en/blogs/post/776235 ; https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4729284).

**Qué dice.** La expansión explosiva del rango inicia tendencias que duran hasta una explosión opuesta. Medida de tres formas: cierre ± k x rango (327 $ por operación), máximo/mínimo previo ± k x rango (313 $), APERTURA de mañana ± k x rango (389 $, más acierto en todas las pruebas). El rango de ayer solo «hace maravillas» como unidad. Otras unidades: el «Talon» (el mayor de máximo de hace 3 días menos mínimo de hoy y máximo de ayer menos mínimo de hace 3 días) y el GSV, media de 1-4 días de los «tramos fallidos» (apertura menos mínimo en días alcistas, máximo menos apertura en bajistas) x 180%. Crabel: estiramiento = media de 10 días de la distancia de la apertura al extremo más cercano; la ORB (ruptura del rango de apertura) funciona mejor tras días NR4/NR7/interiores; cuanto antes se penetra, mejor, y si no se penetra en los primeros minutos se cancela. La ORB de Zarattini-Aziz dio +0,13R con 24% de acierto en QQQ; una réplica independiente en CFD de NQ, SPX, DOW, DAX y FTSE 2015-2026 reprodujo el bruto (el color de la primera vela de 5 minutos tiene un pequeño edge direccional real frente a dirección aleatoria en 4 de 5 índices y fuera de muestra), pero «en una cuenta de CFD el edge es del tamaño del spread»: neto cero, fuera de muestra 2021-26 +0,06R.

**Qué significaría aquí.** Una familia de bloques de nivel: apertura de sesión ± k x {rango previo, GSV, estiramiento de Crabel, ATR, Talon}, con preparaciones {NR4, NR7, día interior, HV(6) < 0,5 x HV(100)}, una expiración de órdenes pendientes tras k barras y el corte «barras desde la apertura al entrar» en el mapa condicional. La comparación de anclas (cierre, extremo, apertura) es un estudio controlado en sí. En M30/H1 hay que definir la sesión por activo: pregunta al dueño, no suposición. La réplica en CFD es la lección: edge-por-coste antes que nada.

**Estado.** NUEVA (SQX tiene entradas genéricas Highest/Lowest + ATR, no un ancla de apertura de sesión; la librería tiene 5 plantillas de indicador) — **Tipo.** generación — **Locura.** 0 — **Valor.** 5

#### Compresión y luego expansión de volatilidad
**Fuente.** Williams, *Long-Term Secrets*, p. 27-33; Tharp, *Trade Your Way*, p. 182-183, 207; Schwager, *Market Wizards* (Jones), p. 68; Covel, *The Complete TurtleTrader* (Parker), p. 85-86; Katsanos, *Intermarket Trading Strategies*, p. 288-290; Kirkpatrick y Dahlquist (CMT, Raschke), p. 386.

**Qué dice.** Tras rangos pequeños vienen grandes; no perseguir mercados calientes. Tharp: tendencia + rango estrecho (rango de 5 días ≤ 0,6 x rango de 50) + señal «puede añadir fácilmente 10-15 céntimos por dólar arriesgado» a un sistema de tendencia. Jones: el único sistema que le funcionó parte de que los mercados se mueven con fuerza cuando se mueven; una expansión súbita tras rango estrecho, que la naturaleza humana quiere desvanecer. Parker: las mejores tendencias empiezan con N (ATR) muy bajo en la ruptura, y el tamaño por N pone entonces posiciones grandes (unidades de soja 2,5 veces mayores al inicio que al final). Katsanos: SD x ADX / MA por debajo de 0,11 y luego ruptura de Bollinger en 3 días, «mejor que el ancho de Bollinger o el ADX solos». Raschke: rupturas NR4 o de día interior solo si HV(6) < 0,5 x HV(100).

**Qué significaría aquí.** Registrar la familia en el ledger (bloques rango5/rango50, ATR5/ATR50, NR-k, SD x ADX) y leer su rendimiento. El +0,10-0,15R de Tharp es un tamaño de efecto falsable con una ablación sobre supervivientes de ruptura. Un corte del mapa condicional: P&L de rupturas por percentil de ATR al entrar frente a su propio año; si las entradas de ATR bajo llevan la R, la compresión es condición fija y el tamaño inverso al ATR hace trabajo real. Dos libros independientes coinciden.

**Estado.** AMPLÍA (familia de régimen de volatilidad aceptada: da el disparador y un tamaño de efecto) — **Tipo.** generación — **Locura.** 0 — **Valor.** 4

#### La apertura y los niveles de referencia de la sesión como anclas
**Fuente.** Williams, *Long-Term Secrets*, p. 12, 33-36; *New Frontiers in Technical Analysis* (Erlanger), p. 125-131; Schwager, *New Market Wizards* (Trout), p. 63.

**Qué dice.** Los días alcistas de gran rango abren cerca del mínimo y cierran cerca del máximo; la apertura «es el precio más importante del día». Un 87% de los días cierra sobre la apertura cuando la caída desde la apertura queda por debajo del 20% del rango previo; casi nulo un gran cierre alcista tras una caída del 70-80%. Erlanger: soporte, pivote y resistencia fijados en la apertura, más el máximo y mínimo de las dos últimas horas de la sesión previa, que «un día después aún actúan»; los extremos del rango de apertura (1/5/30/60 min) dan el sesgo; una ruptura que falla y vuelve es giro. Trout: la gente pone stops justo encima del máximo de ayer y debajo del mínimo.

**Qué significaría aquí.** Un vocabulario de «estructura de sesión» que los bloques genéricos de SQX no tienen: pivotes H/L/C de la sesión previa, extremos de sus últimas N horas, rango de apertura tras k barras, «largo solo con precio sobre la apertura de hoy». Dos estudios causales antes de construir: (a) la relación entre la excursión desde la apertura hasta la barra k y el resto del recorrido (la versión ingenua es tautológica: condicionar solo a lo ocurrido hasta la barra k); (b) si el precio reacciona en el nivel de las 2 últimas horas más que en niveles placebo a la misma distancia. En FX y oro la «apertura» es ambigua: definirla por sesión (Londres, NY) preguntando al dueño.

**Estado.** NUEVA — **Tipo.** generación · estudio — **Locura.** 1 — **Valor.** 4

#### Rupturas violentas: cuanto peor el fill, mejor la operación
**Fuente.** Schwager, *Market Wizards* (Kovner), p. 38, 43.

**Qué dice.** La libra/marco rompió un rango de un año defendido por el BoE; tras 3,01 no hubo operaciones hasta 3,035. «Ese tipo de ruptura violenta y rápida es mucho más fiable que una típica... Fills terribles. Cuanto peores los fills, mejor la operación.»

**Qué significaría aquí.** (1) Una condición para plantillas de ruptura: rango o hueco de la barra de ruptura en ATR por encima de un umbral (velocidad de la ruptura). (2) Un aviso de realismo: justo las mejores rupturas son aquellas donde el fill en el nivel es menos alcanzable; en M1, medir a qué distancia del nivel estuvo el primer precio negociable en las mejores operaciones y reprecificarlas.

**Estado.** AMPLÍA (familia nueva; realismo de fills de edgeCost) — **Tipo.** generación · estudio — **Locura.** 1 — **Valor.** 3

#### Ruptura de máximos históricos o de varios años
**Fuente.** Schwager, *Market Wizards* (Hite, citando a Seykota), p. 93.

**Qué dice.** «Cuando un mercado hace un máximo histórico te está diciendo algo... el mero hecho de que el precio esté en un máximo nuevo dice que algo ha cambiado.»

**Qué significaría aquí.** Una familia de ruptura de máximo histórico o plurianual, y la distancia al máximo histórico como condición fija. El oro hizo máximos históricos en serie en 2024-25: prueba natural. Se empareja con la familia de «reacción fallida a la noticia» (4.6).

**Estado.** AMPLÍA (familia nueva) — **Tipo.** generación — **Locura.** 0 — **Valor.** 3

#### El ancho de Bollinger invierte el signo de la regla
**Fuente.** *New Frontiers in Technical Analysis*, p. 25-27, 44.

**Qué dice.** Con ancho de banda grande, un cierre bajo la banda inferior es alcista (reversión); con ancho pequeño, un cierre sobre la superior es alcista (ruptura). La primera prueba de una banda suele ir seguida de otra.

**Qué significaría aquí.** Un bloque condicionado al régimen: el mismo evento de banda con dirección opuesta según el percentil del ancho. Es una interacción que el hueco aleatorio no puede descubrir. Y una prueba para toda estrategia de bandas: ¿cambia de signo su P&L entre terciles de ancho?

**Estado.** AMPLÍA (familia de régimen de volatilidad; mapa condicional) — **Tipo.** generación — **Locura.** 1 — **Valor.** 3

#### Fuerza de cierre (CLV): dónde cierra la barra dentro de su rango
**Fuente.** Williams, *Long-Term Secrets*, p. 36-43, 238-240.

**Qué dice.** Poder comprador = cierre menos mínimo, vendedor = máximo menos cierre. Los mínimos se forman con cierres en o cerca del mínimo, varios seguidos sobre todo; vale en 15 min, horario, diario, semanal y mensual. Comprar cuando el cierre está en el 65% superior del rango y mantener 5-20 días fue rentable en todos los mercados.

**Qué significaría aquí.** Una familia de bloques «k cierres seguidos en el q superior o inferior del rango» como agotamiento contrario, o un CLV suavizado (suma de cierre menos mínimo entre suma de rangos en n barras) como oscilador del hueco aleatorio; también un corte del mapa condicional. SQX tiene Williams %R, no rachas de CLV.

**Estado.** NUEVA — **Tipo.** generación — **Locura.** 0 — **Valor.** 3

#### Indicadores de tendencia con menos parámetros: Congestion Index, KSDI, Kalman
**Fuente.** Katsanos, *Intermarket Trading Strategies*, p. 156-160; *New Frontiers in Technical Analysis*, p. 188-195; Chan, *Algorithmic Trading*, p. 74-83.

**Qué dice.** Congestion Index = cambio % de X barras dividido entre (HH-LL)/LL, suavizado EMA3; ±20 inicio de tendencia, >85 y giro agotamiento; cruzó 20 ocho días antes que el VHF en abril de 2007 y el ADX no lo vio. KSDI = ln(máximo actual / mínimo de hace n barras) dividido entre volatilidad x raíz de n, es decir, el movimiento en desviaciones; n distinto para subidas y bajadas; ojo, elegir el n que maximiza es minería dentro del indicador y sus umbrales deben calibrarse por simulación, no con una normal. Kalman: un solo filtro da media adaptativa y banda (media ± k raíz de Q), con Ve menor para operaciones grandes (media ponderada por volumen y tiempo).

**Qué significaría aquí.** Candidatos a bloque que sustituyen pares media/Bollinger por un solo parámetro. Su valor es tener menos parámetros, algo que la búsqueda genética no premia por sí sola; probar con la tarjeta de información del bloque contra la versión clásica.

**Estado.** NUEVA (como bloques) — **Tipo.** generación — **Locura.** 1 — **Valor.** 2

#### Capitulación: entrar tras un día de pánico de k sigmas
**Fuente.** Schwager, *New Market Wizards* (Hull), p. 144-145, 147; Schwager, *Market Wizards* (Weinstein), p. 158.

**Qué dice.** Hull hacía pocas operaciones direccionales, contra la noticia dominante y en el clímax del pánico (McDonnell Douglas tras el miedo al DC-10; largo durante la suspensión del CME tras 1987). Weinstein: ir contra esa histeria gana «el 95% de las veces».

**Qué significaría aquí.** El análogo solo de precio: tras un día bajista de k sigmas con expansión de rango o tick volume, entrada larga a horizonte fijo, k y horizonte preregistrados, dentro de las familias de régimen de volatilidad. Pocos eventos y poca potencia; una familia para registrar, no una prioridad.

**Estado.** AMPLÍA (familia de régimen de volatilidad) — **Tipo.** generación — **Locura.** 1 — **Valor.** 2

#### Cascadas de stops de los seguidores de tendencia
**Fuente.** Schwager, *Stock Market Wizards* (Bender), p. 123-124.

**Qué dice.** Oro 1993: muchos CTA entraron largos sobre 400 $ con stops ligados a la volatilidad; Bender calculó que una caída hacia 390 $ dispararía una reacción en cadena; el oro fue a 390 y «casi de inmediato a 350». La distribución correcta es distinta en cada mercado y periodo.

**Qué significaría aquí.** Una familia loca: tras una gran ruptura de N barras (donde entran los seguidores de tendencia), un retroceso a entrada menos k ATR (donde se agrupan sus stops) acelera en vez de sostener. Y un aviso para el paso del stop ATR: un stop de múltiplo de ATR está justo donde están todos los demás.

**Estado.** NUEVA — **Tipo.** generación — **Locura.** 3 — **Valor.** 2

### 4.6 · Familias de un solo mercado: reversión, patrones fallidos y niveles

#### Desvanecer el hueco: Oops!, huecos de sesión y hueco de fin de semana
**Fuente.** Williams, *Long-Term Secrets*, p. 113-117; Fitschen, *Building Reliable Trading Systems*, p. 138-143; Chan, *Algorithmic Trading*, p. 92-96, 156-157; web: huecos de fin de semana del XAUUSD (https://www.mql5.com/en/articles/23609 ; https://www.earnforex.com/guides/forex-weekly-gap-statistics/ ; https://www.aioka.io/blog/gold-trading-strategy-weekend-gap-risk).

**Qué dice.** Oops!: apertura bajo el mínimo del día anterior y stop de compra en ese mínimo. S&P (sin miércoles ni jueves) 82%+, 438 $ por operación, unos 1,5 días; bonos 86%. «El patrón a corto más fiable que he investigado.» Fitschen, 56 materias primas 2000-2011: 10 de 12 configuraciones de hueco perdían operando en la dirección del hueco; los huecos de barra que salen de una congestión (rango de 10 días < 1-2 desviaciones) son contratendencia, y los que no salen de congestión y van con la tendencia de 20 días continúan. Chan, en sentido OPUESTO: comprar cuando la apertura supera el máximo previo en más de 1 desviación y salir al cierre dio en FSTX 13% anual y Sharpe 1,4, y en GBPUSD (apertura de Londres, cierre 17:00 ET) 7,2% y Sharpe 1,3; mecanismo: stops acumulados de noche que se disparan en cascada. Web: en XAUUSD hubo huecos de 5 $ o más en un 35% de las semanas y de 10 $ o más en un 18% (últimos 3 años), con estudios de tasa de relleno por tamaño.

**Qué significaría aquí.** En FX y oro 24h casi no hay huecos diarios salvo el lunes; la adaptación es por sesión: apertura de Londres o NY fuera del rango de la sesión previa y vuelta a su borde, huecos de apertura de contado en CFD de índices, apertura del domingo frente al cierre del viernes. Probar desvanecer y seguir como UNA familia, con la congestión como interruptor que cambia el signo. Necesita que el dueño elija la definición de sesión.

**Estado.** NUEVA (familia de sesión aceptada; estos bloques no existen) — **Tipo.** generación — **Locura.** 1 — **Valor.** 4

#### Retroceso dentro de la tendencia
**Fuente.** Williams, *Long-Term Secrets*, p. 94-95; Fitschen, *Building Reliable Trading Systems*, p. 89-105; Katz y McCormick, p. 128-130.

**Qué dice.** S&P comprando cada día y saliendo al cierre siguiente: 52% y 134 $. Tras tres cierres bajistas: 58% y 353 $. Tendencia alcista (C > C[30]) con retroceso (C < C[9]): 57% y 421 $; solo lunes 59% y 672 $. La nula correcta es el 52% de la deriva, no el 50%. Fitschen: el retroceso con filtro de tendencia paga los costes; un filtro de tendencia más largo (cierre frente a cierre de hace 70 días) subió el beneficio por operación más de un 40% y sacó del 2008 al sistema solo largo; un filtro de alta volatilidad (no entrar con rango medio de 20 días > umbral) y salir cuando se supera llevó la ganancia sobre dolor de 1,23 a 2,44.

**Qué significaría aquí.** Tres candidatos de una línea para el hueco aleatorio, con evidencia de muestra grande: «la barra previa cerró contra la señal», «el cierre frente al de hace N barras coincide», «ATR en divisa de la cuenta bajo X». Y la plantilla canónica de retroceso en tendencia (dos condiciones de signo de ROC), que no está en la librería.

**Estado.** NUEVA (la plantilla); AMPLÍA el diseño de grupos aleatorios — **Tipo.** generación — **Locura.** 0 — **Valor.** 4

#### Filtro de momentum sobre una entrada de reversión: los movimientos pequeños revierten, los grandes no
**Fuente.** Chan, *Algorithmic Trading*, p. 92-96, 106, 140.

**Qué dice.** Buy-on-gap solo compra acciones que abrieron más de 1 desviación abajo PERO con apertura sobre la media de 20 días; «las que cayeron poco tienen más probabilidad de revertir que las que cayeron mucho» (noticias). Imponer un filtro de momentum a la reversión suele mejorar su consistencia. CL: comprar si el precio < hace 30 días Y > hace 40 días, Sharpe 1,1.

**Qué significaría aquí.** Una forma de plantilla: condición fija = contramovimiento de tamaño acotado (1-2 ATR, no más) + filtro de tendencia en sentido contrario a un horizonte más largo; hueco aleatorio libre. Con el calendario económico, excluir barras de noticias de las entradas de reversión.

**Estado.** AMPLÍA (librería de plantillas) — **Tipo.** generación — **Locura.** 0 — **Valor.** 3

#### Rupturas fallidas: trampa del especialista, 2B, hikkake y barra interior
**Fuente.** Williams, *Long-Term Secrets*, p. 108-113; Schwager, *New Market Wizards* (Sperandeo), p. 105-106; Kirkpatrick y Dahlquist (CMT, Crabel y Chesler), p. 381-384.

**Qué dice.** Trampa del especialista (Wyckoff): tendencia, caja de 5-10 días, cierre más allá de la caja; si en 1-3 días se rompe el extremo opuesto de la barra de ruptura, era falsa: girar. Funciona en 5, 30 y 60 minutos. Sperandeo, 2B: prueba fallida del máximo reciente, más fiable si se penetra y se vuelve por debajo; los stops se agrupan justo más allá del máximo, se disparan, y si el movimiento era solo de stops se da la vuelta: «el último suspiro del mercado», su patrón «más fiable». Crabel: tras una barra interior, comprar la apertura siguiente si está sobre el cierre interior: 68% en S&P 1982-86; hikkake: una ruptura de barra interior que falla y atraviesa el extremo opuesto en 3 barras se convierte en la señal.

**Qué significaría aquí.** Bloques exactamente especificables (penetrar el máximo de N barras en x ATR y cerrar de vuelta en m barras) probados en pares emparejados con su ruptura (ruptura frente a su fallo), para que el ledger aprenda por activo en qué régimen está. Por la regla 11, las lecturas (qué máximo, cuánta penetración, cuántas barras) se preguntan. En FX/oro M30/H1 las variantes basadas en la apertura degeneran (apertura ≈ cierre previo): usar barras de sesión.

**⚠ Contradice.** Oops!, smash day, las reglas de barra interior de Crabel y la ORB necesitan una apertura real con hueco; en FX y oro M30/H1 no se pueden probar sin reconstruir las barras alrededor de una sesión elegida por el dueño (Williams cap. 7; CMT cap. 17).

**Estado.** NUEVA — **Tipo.** generación — **Locura.** 1 — **Valor.** 3

#### La señal fallida como señal: el extremo que no revierte y la noticia que no mueve
**Fuente.** Briese, *The Commitments of Traders Bible*, p. 101-108, 141-143, 213-220, 265; Schwager, *New Market Wizards* (lecciones de Schwartz y Lipschutz), p. 179; (McKay), p. 44; Schwager, *Market Wizards* (Hite), p. 93.

**Qué dice.** Los mercados bajistas ignoran las señales de compra del COT y los alcistas las de venta; «que el mercado ignore las señales de venta confirma la tendencia alcista»; el oro rompió en 2007 tras un fallo de señal de venta. Si el movimiento adverso temido de la noche o el fin de semana no llega, «debe haber fuerzas muy poderosas a favor». McKay mira la respuesta del mercado a la noticia, no la noticia; Hite: un mercado que no responde a una gran noticia es «una gran venta».

**Qué significaría aquí.** Dos familias solo de precio, probables hoy sin datos externos: (1) extremo de un oscilador contrario alcanzado y luego nuevo extremo de precio en contra en N barras: operar en la dirección del fallo; (2) hueco o primera hora contra la tendencia recuperado del todo al cierre o en n barras: continuación. Con el calendario económico (actual frente a previsión), el precio moviéndose contra la dirección de la sorpresa es la señal.

**Estado.** NUEVA — **Tipo.** generación — **Locura.** 2 — **Valor.** 3

#### Patrones de emoción extrema: día exterior bajista, smash day y smash day oculto
**Fuente.** Williams, *Long-Term Secrets*, p. 95-98, 101-108.

**Qué dice.** Día exterior con cierre bajo el mínimo previo y apertura siguiente aún más baja: comprar la apertura; S&P 109 operaciones, 85%, 477 $; bonos desde 1990 57 operaciones, 82%. Smash day: cierre bajo el mínimo previo, entrada si al día siguiente supera el máximo del smash day. Smash oculto: cierre alcista pero en el 25% inferior del rango y bajo la apertura; comprar si al día siguiente supera su máximo. Sirve en tendencias fuertes o en rupturas fallidas de rango.

**Qué significaría aquí.** Bloques SmashBuy(k) e HiddenSmashBuy(q = 0,25) con entrada en stop en el máximo de la barra de preparación: pocos parámetros, independientes del marco, buenos como condición fija. Las muestras diarias son diminutas; en H1 el recuento sería mucho mayor. Prueba de invariancia al estilo crossTF: misma definición en M30/H1/H4/D1 frente al mono.

**Estado.** NUEVA (bloques); AMPLÍA crossTF (prueba de invariancia) — **Tipo.** generación — **Locura.** 1 — **Valor.** 3

#### Niveles obvios: números redondos, máximo y mínimo de ayer, stops apiñados
**Fuente.** Chan, *Algorithmic Trading*, p. 167; Schwager, *New Market Wizards* (Trout), p. 63-64, 66; Elder, *The New Trading for a Living*, p. 220-221.

**Qué dice.** Osler: una vez roto un soporte o resistencia de FX (niveles publicados por bancos o números redondos cercanos), el precio sigue un rato porque se disparan stops agrupados. Trout: «los mercados casi siempre llegan al número redondo»; stops justo encima del máximo de ayer y debajo del mínimo, que los locales barren; nunca pongas stops en sitios obvios. Elder: los stops de la multitud se agrupan bajo mínimos obvios y números redondos, donde el mercado tiene «una costumbre asombrosa» de volver antes de girar; poner 77,94 y no 78.

**Qué significaría aquí.** (1) Un bloque de nivel «número redondo más cercano» (XAUUSD 10/50 $, EURUSD 00/50 pips, índices 100) y la condición «cierra cruzando un nivel redondo» para plantillas de ruptura. (2) Un estudio falsable: P(tocar el siguiente nivel redondo en N barras | está a d de él) frente a la misma probabilidad para niveles no redondos a igual distancia (imán frente a freno). (3) Ruptura del máximo o mínimo de ayer: seguir o desvanecer, probado en ambos sentidos. (4) Comprobar si el stop ATR leído del MAE cae sistemáticamente en un nivel obvio, y la tasa de barrido y rebote de stops en mínimos y redondos frente a desplazados una fracción de ATR.

**Estado.** NUEVA — **Tipo.** generación · estudio — **Locura.** 2 — **Valor.** 3

#### Divergencia precio-momentum con una definición programable
**Fuente.** Katz y McCormick, p. 144-152; *New Frontiers in Technical Analysis*, p. 177-187; Fitschen, p. 134-137; Aronson, *Evidence-Based TA*, p. 452.

**Qué dice.** Katz: la divergencia del MACD (precio con mínimo más bajo en 1-6 barras, mínimo del oscilador al menos 4 barras antes y más alto, oscilador girando) con entrada en límite fue «radicalmente distinta» del resto: 12,5% anual dentro y 19,5% fuera, ambos lados rentables; con RSI fue terrible. *New Frontiers*: el pico del momentum debe coincidir con el del precio con 1-3 barras de tolerancia, un nuevo extremo de precio antes de confirmar la anula, filtrar picos demasiado cerca de cero, máximo 89 barras entre picos; los cruces de zonas de sobrecompra no son fiables. Fitschen, en cambio: desvanecer las divergencias es lo prometedor en materias primas. Aronson: la transformada de Fisher de osciladores normalizados por canal (distribución en U) los hace casi normales; «solo una conjetura interesante».

**Qué significaría aquí.** Un bloque de divergencia preciso (tolerancia, regla de anulación, separación máxima) que el vocabulario de SQX expresa mal, probado en ambos sentidos y con ambas definiciones antes de fiarse de un libro. Variante Fisher de estocástico o Williams %R para plantillas de reversión, contrastada con la tarjeta de información del bloque.

**Estado.** NUEVA (bloque) — **Tipo.** generación — **Locura.** 1 — **Valor.** 3

#### Estructura de tramos anidados como niveles y como estado de tendencia
**Fuente.** Williams, *Long-Term Secrets*, p. 16-22, 133-136; Kirkpatrick y Dahlquist (CMT), p. 455-457.

**Qué dice.** Mínimo de corto plazo: barra con mínimos más altos a ambos lados; intermedio: mínimo de corto con mínimos de corto más altos a ambos lados; largo: un nivel más arriba. Se confirma cuando el precio supera el máximo de la barra que hizo el mínimo. Una tendencia rota al violar el mínimo antes de un nuevo máximo es mejor señal de giro que al violarlo tras un máximo más bajo. CMT: en tendencia alcista el pico del ciclo cae a la derecha del punto medio (traslación a la derecha); si la traslación mengua, la tendencia mayor está girando.

**Qué significaría aquí.** Una familia de bloques «nivel de tramo anidado» (último mínimo intermedio, mínimo largo confirmado) y un estado de tendencia sin parámetros (último tramo roto, tipo A/B; cociente de duración de tramos alcistas y bajistas). Ojo: la definición ingenua «mínimo con mínimos más altos a ambos lados» ES look-ahead; la confirmación causal no. El Fractal de SQX tiene 2 barras de retraso.

**Estado.** NUEVA — **Tipo.** generación — **Locura.** 1 — **Valor.** 3

#### Perfil de tiempo en precio: punto de control, área de valor y «huecos»
**Fuente.** *New Frontiers in Technical Analysis*, p. 231-247.

**Qué dice.** En una ventana, el nivel con más tiempo o volumen es el punto de control; el área de valor tiene un 68% de la actividad. El equilibrio (perfil gordo) alterna con el desequilibrio (perfil flaco, movimientos verticales). Los movimientos verticales dejan huecos de poca actividad que, al revisitarse, se atraviesan rápido.

**Qué significaría aquí.** (a) Bloques de nivel calculados solo con precio (tick volume opcional): punto de control, bordes del área de valor, distancia al nodo de poca actividad más cercano. (b) Primero un estudio barato que falsa la afirmación: la velocidad de barra es mayor dentro de zonas previas de poca actividad, neta del régimen de volatilidad. (c) La «gordura» del perfil como variable de régimen.

**Estado.** NUEVA — **Tipo.** generación — **Locura.** 2 — **Valor.** 3

#### Anclas: proximidad al máximo de 52 semanas
**Fuente.** Aronson, *Evidence-Based TA*, p. 352-354.

**Qué dice.** George y Hwang: la proximidad al máximo de 52 semanas predice mejor que el retorno pasado, da más beneficio y no revierte (anclaje). El momentum de 6-12 meses persiste; las tendencias de 3-5 años revierten; el momentum con volumen alto es 2-7% más fuerte.

**Qué significaría aquí.** Bloques (cierre - máximo de N_largo) / ATR, con N_largo = un año de barras, y su gemelo por abajo. Evidencia de acciones; su transferencia a FX y oro es desconocida.

**Estado.** NUEVA (como bloques) — **Tipo.** generación — **Locura.** 1 — **Valor.** 2

#### Canal de 3 barras en la dirección del tramo
**Fuente.** Williams, *Long-Term Secrets*, p. 136-138.

**Qué dice.** Con tendencia de tramo alcista, comprar en la media de 3 barras de los mínimos y recoger en la media de 3 barras de los máximos; opuesto en bajista; barras de 5-60 minutos; una vez 30 ganadoras seguidas.

**Qué significaría aquí.** Una plantilla de reversión en tendencia con límite y objetivos pequeños, muy sensible a costes: probablemente muere en el preflight de costes en M30/H1. Buen caso de prueba para ese preflight.

**Estado.** NUEVA (plantilla); YA EXISTE el preflight de costes que la juzgará — **Tipo.** generación — **Locura.** 1 — **Valor.** 2

### 4.7 · Sesión, hora y calendario

#### Cambio de mes indexado por día hábil (TDM)
**Fuente.** Williams, *Long-Term Secrets*, p. 87-92, 147-156; web: In Gold We Trust, anomalías de calendario en el oro (https://ingoldwetrust.report/nuggets/calendar-anomalies-and-the-gold-market/?lang=en).

**Qué dice.** Indexar el mes por días hábiles (1..22), no por fechas, para que la regla siempre sea operable. S&P comprando la apertura del día hábil 1 y saliendo en la primera apertura con beneficio, stop 1.500 $: 129 operaciones 1982-98, +73.437 $, 85% de acierto. Bonos: día 18, salida al tercer cierre, 250 $ por operación; con filtro de oro bajista +100 $ y la mitad de drawdown. Los peores meses (enero, febrero, octubre) son selección dentro de muestra. El cambio de mes es el efecto de calendario con más confirmación independiente fuera de muestra (Ariel 1987, Lakonishok-Smidt 1988). La web documenta cambio de mes y día de la semana también en el oro.

**Qué significaría aquí.** La PRIMERA familia de calendario a probar: plantilla de cambio de mes (entrar entre TDM-3 y +1, salir N días después) en CFD de índices y oro. SQX tiene DayOfMonth, pero los contadores de día hábil y «días hábiles hasta fin de mes» son un bloque personalizado. Elegir meses a mano cuenta como 2^12 subconjuntos o no se hace.

**Estado.** AMPLÍA (familia de calendario aceptada; aporta la indexación y la cuenta atrás) — **Tipo.** generación — **Locura.** 0 — **Valor.** 5

#### Puerta de validez de cualquier perfil estacional: correlación entre mitades (Cycle-R) y «calor»
**Fuente.** *New Frontiers in Technical Analysis*, p. 86-94; Tharp, *Trade Your Way*, p. 91-99; Chan, *Quantitative Trading*, p. 143-151.

**Qué dice.** Un compuesto estacional se puede construir con datos aleatorios; se valida construyéndolo con la primera y la segunda mitad de la historia por separado y correlacionándolas (SBUX 0,76; AXP 0,54). El «calor» de una zona es la fracción de compuestos móviles pasados en que esa zona también fue fuerte. Tharp: un patrón de fecha única («subió 13 de 14 años el 13 de abril») es minería; fiarse de un RACIMO de fechas vecinas con causa fundamental, y vigilar que el régimen no invierta la estacionalidad (soja brasileña 1980). Chan: con una operación al año, comprobar desplazando las fechas de entrada y salida.

**Qué significaría aquí.** Antes de generar con cualquier familia de calendario o sesión (hora de la semana, TDM, mes), calcular la correlación entre mitades del perfil sobre `build` con una nula de permutación (barajar años o semanas), y el calor por celda (celda x ventana, pintable como franja). Solo las familias con estabilidad significativa merecen CPU. El efecto debe sobrevivir a una meseta sobre el eje de fechas (±k días). No optimizar la retrospectiva sobre el propio Cycle-R, o contarlo.

**Estado.** AMPLÍA (familia de calendario aceptada; ledger) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 5

#### Dónde se gana en el día: descomponer el P&L por tramo de sesión
**Fuente.** Williams, *Long-Term Secrets*, p. 212-213; web: sesgo de Londres en el oro (https://www.sprottmoney.com/blog/gold-manipulation-london-bias-1970-2024); momentum nocturno de Lou-Polk-Skouras (https://arxiv.org/pdf/2010.01727); deriva nocturna y su desaparición (https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3560269 ; https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/); Renaissance según Zuckerman (https://bagerbach.com/books/the-man-who-solved-the-market/).

**Qué dice.** Williams: el hueco nocturno es el público, de la apertura al cierre los profesionales; usa aperturas en todas sus medidas. Oro: mantener del fix de la tarde al de la mañana (noche) frente al día de Londres tuvo históricamente signos opuestos. Boyarchenko-Larsen-Whelan: casi el 100% de la prima de la renta variable de EE UU se ganaba entre las 02:00 y 03:00 ET (apertura europea); la Fed de NY en julio de 2026 la da por desaparecida (unos 3,7%/año a casi 0 desde 2021). Renaissance: la subida de final del día continúa en la apertura siguiente; el viernes por la mañana predice el cierre de la tarde.

**Qué significaría aquí.** Un estudio sobre cada estrategia y sobre comprar y mantener: qué parte del P&L se gana en Asia, Londres, NY, o noche frente a sesión de contado en índices. Dice dónde vive el edge, marca estrategias que dependen del hueco (riesgo de hueco y swaps que el MC Retest no ve) y siembra familias de hora. La deriva nocturna es además un caso de libro de vida media tras publicar: familia de hora en CFD de índices con comprobación de decaimiento incorporada.

**Estado.** AMPLÍA (mapa condicional por hora y sesión; exposure) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 4

#### Los fixes de divisas: patrón en W alrededor del reloj y fin de mes
**Fuente.** web: Krohn, Mueller y Whelan, JF 2024 (https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3521370 ; https://wrap.warwick.ac.uk/id/eprint/177333/1/WRAP-foreign-exchange-fixings-returns-around-clock-Mueller-2023.pdf); Ranaldo 2009 (https://papers.ssrn.com/sol3/papers.cfm?abstract_id=960209); Melvin y Prins 2015, fix de las 16:00 a fin de mes (https://forexdetox.substack.com/p/the-4-pm-london-fix-anomaly-at-month ; https://piphawk.com/guides/month-end-rebalancing-fx-flows).

**Qué dice.** El USD se aprecia hacia los fixes (Tokio 9:55 JST, BCE, WM/R 16:00 Londres) y se deprecia después: un patrón diario en W, 9 divisas, 21 años, explicado por riesgo de inventario; Sharpe negativo a costes minoristas completos y 0,5-0,7 con spreads de dealer. Ranaldo: las divisas locales se deprecian en su horario laboral. Melvin y Prins: la apreciación relativa de la bolsa de un país predice la depreciación de su divisa antes del fix de fin de mes, con reversión parcial después (reequilibrio de coberturas).

**Qué significaría aquí.** Una familia de hora del día muy bien fundamentada (tiempo hasta el fix como condición) y una familia de fin de mes por reequilibrio, que necesita el retorno relativo de índices del mes (otra razón para los CFD de índices en AlgoData). También una lección de costes: el edge es del orden del spread.

**Estado.** AMPLÍA (familias de sesión y calendario aceptadas) — **Tipo.** generación — **Locura.** 1 — **Valor.** 4

#### Volatilidad relativa a la misma franja horaria (volumen en el tiempo)
**Fuente.** *New Frontiers in Technical Analysis*, p. 36-44.

**Qué dice.** El volumen intradía tiene una «sonrisa» (apertura fuerte, mediodía flojo, cierre fuerte); comparar el volumen actual con una media móvil mezcla peras con manzanas. VAT = volumen medio de la misma franja en los últimos X días; una subida con volumen acumulado menor que el medio acumulado no tiene apoyo.

**Qué significaría aquí.** Un bloque «rango (o tick volume) relativo a la media de la misma hora en N días», la volatilidad ajustada por la estacionalidad intradía. Las rupturas medidas contra el rango esperado de la hora no se disparan en cada apertura de Londres solo porque la apertura siempre es volátil. Dukascopy M1 trae tick volume. También un corte del mapa condicional.

**Estado.** AMPLÍA (familia de estacionalidad intradía de volatilidad aceptada) — **Tipo.** generación — **Locura.** 1 — **Valor.** 4

#### Deriva intradía de retorno y momentum intradía en índices
**Fuente.** Schwager, *New Market Wizards* (Blake), p. 97; Chan, *Algorithmic Trading*, p. 163-164; web: Gao, Han, Li y Zhou, JFE 2018 (https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2440866 ; https://www.sciencedirect.com/science/article/abs/pii/S0304405X18301351).

**Qué dice.** Blake: un fondo sectorial de energía cotizaba cerca de su mínimo temprano; comprar a las 10, 11 o 12 y vender al cierre ganó el 90-95% de las veces uno o dos años, hasta que una comisión lo mató. Chan: los ETF apalancados deben comprar tras días alcistas y vender tras bajistas cerca del cierre; comprar DRN si del cierre previo a 15 minutos antes del cierre sube más de 2%, salir al cierre: 15% anual, Sharpe 1,8. Gao y otros: la primera media hora predice la última en SPY y 10 ETF, más en días volátiles o de noticias; en FX es débil (solo AUDUSD y USDJPY dentro de muestra, fuera de muestra negativo).

**Qué significaría aquí.** Un escaneo de estacionalidad de RETORNO (no solo de volatilidad): retorno medio y acierto de la hora h al cierre por activo y día de la semana, con estabilidad año a año; muy barato en M1, y el resultado es una plantilla directa (entrar a la hora h, salir a la H). Una familia para CFD de índices (US500, NAS, DJ30, DAX): retorno desde el cierre previo de contado más allá de ±x desviaciones a T-15/30 min, seguir hasta el cierre de contado. Precaución para FX.

**Estado.** AMPLÍA (familia de sesión: añade deriva de retorno) — **Tipo.** estudio · generación — **Locura.** 0 — **Valor.** 3

#### En horas de poca liquidez el movimiento revierte, en horas de mucha continúa
**Fuente.** Schwager, *New Market Wizards* (Trout), p. 64, 66.

**Qué dice.** El volumen tiene forma de U en casi todos los mercados. Trout sostenía posiciones en el mediodía ilíquido porque mover el precio es barato entonces; un movimiento hecho por locales se desvanece porque se van a casa planos.

**Qué significaría aquí.** Una hipótesis direccional concreta para la familia aceptada: condicionar un bloque de ruptura al percentil de tick volume de la hora. Y las estrategias cuyas entradas se agrupan en horas ilíquidas deberían llevar más deslizamiento en el modelo de costes.

**Estado.** AMPLÍA (familia de sesión; costes por hora) — **Tipo.** generación — **Locura.** 1 — **Valor.** 3

#### Heterogeneidad de la volatilidad por día de la semana, separada de la dirección
**Fuente.** Williams, *Long-Term Secrets*, p. 82-86.

**Qué dice.** Bajo un paseo aleatorio el rango, el |apertura-cierre| y el cambio neto serían homogéneos entre días. No lo son: S&P con rangos mayores martes y viernes, bonos jueves y viernes; S&P lunes de apertura a cierre alcista un 57%; la libra el miércoles 55% y +18 $, que se comen los costes; el oro, aleatorio.

**Qué significaría aquí.** Probar la heterogeneidad de la volatilidad (rango y |O-C| por día y hora) como pregunta aparte de la dirección: la estacionalidad de la volatilidad es mucho más estable y es lo que debe atacar la familia de estacionalidad intradía. Kruskal-Wallis por activo y marco con BH entre activos, y toda tabla de calendario impresa neta del spread del activo.

**Estado.** AMPLÍA (familia de estacionalidad de volatilidad; mapa condicional por día) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 3

#### Nula anidada: cada celda contra su periodo contenedor
**Fuente.** Kirkpatrick y Dahlquist (CMT), p. 174.

**Qué dice.** La fortaleza previa a Acción de Gracias desaparece al descontar la fortaleza habitual de noviembre; los efectos de festivos quedan casi todos en la variación aleatoria tras ese ajuste.

**Qué significaría aquí.** Para cualquier celda de calendario u hora, la nula no es cero ni la media global sino la media del periodo que la contiene (celda horaria frente a su sesión, TDM frente a su mes, día frente a la deriva semanal). Evita descubrir el mismo efecto amplio diez veces como efectos estrechos.

**Estado.** AMPLÍA (mapa condicional, familia de calendario) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 3

#### Los efectos de calendario publicados decaen
**Fuente.** Kirkpatrick y Dahlquist (CMT), p. 146-148, 173-174; Schwager, *Stock Market Wizards* (Lescarbeau, Shaw), p. 107-108, 140; web: McLean y Pontiff (https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2156623).

**Qué dice.** El efecto lunes se deterioró en tres décadas hasta no haber diferencia entre días; el efecto enero de las pequeñas «no ha funcionado muy bien»; el efecto enero funcionó más del 90% de los años desde los años 20 y luego falló seis años seguidos tras publicarse. El sistema de amplitud de un día (100 $ a 884 millones sin costes, 1932-2000) se hundió tras 2005. McLean-Pontiff: las anomalías pierden un 26% fuera de muestra y un 58% tras publicarse.

**Qué significaría aquí.** Las anomalías conocidas (día de la semana, cambio de mes, «vende en mayo») son las más probablemente arbitradas o rotas. Marcar cada hipótesis de calendario como publicada o nueva en el ledger, probar subventanas recientes por separado y mostrar siempre la tendencia temporal del edge junto a su nivel.

**⚠ Contradice.** Matiza la familia de calendario aceptada (CMT, p. 173-174).

**Estado.** AMPLÍA (familia de calendario; vida media del edge) — **Tipo.** proceso — **Locura.** 0 — **Valor.** 3

#### Estacionalidad del oro y de las materias primas con receta sin fugas
**Fuente.** Katz y McCormick, p. 155-177; Chan, *Quantitative Trading*, p. 143-151; Katsanos, *Intermarket Trading Strategies*, p. 115-117; web: In Gold We Trust (https://ingoldwetrust.report/nuggets/calendar-anomalies-and-the-gold-market/?lang=en); NBER (https://www.nber.org/system/files/working_papers/w12413/w12413.pdf).

**Qué dice.** Oro: enero y febrero fuertes (Año Nuevo chino), septiembre a noviembre fuertes (Diwali, bodas indias; Katsanos lo ve en septiembre-diciembre con 20 años de COMEX, distorsionado por la tendencia de 2002), verano débil; flujos fiscales del USD en abril. Chan: el efecto enero murió tras publicarse, pero las estacionalidades de materias primas con demanda real persisten (gasolina 13-25 de abril, rentable cada año 1995-2008). Katz: esperado por fecha a partir de las mismas fechas de otros años, cambios divididos por ATR(50) y recortados a ±2 ATR para que cada año pese igual; dentro de muestra dejar un año fuera (jackknife), fuera de muestra solo años pasados; la mejor entrada fue cruce + confirmación estocástica en STOP: 1.677 $ por operación y 19,6% anual fuera de muestra. «Invertir» cuando el mercado no está de acuerdo destruía el resultado.

**Qué significaría aquí.** Priorizar Brent (temporada de conducción, mantenimiento de refinerías) y oro frente a índices; construir el perfil con la receta de Katz (jackknife, ATR recortado) y entrada en stop; la robustez es un SPP sobre desplazamientos de fecha. Con pocas operaciones por año el Sharpe deflactado del ledger los aplastará, con razón, salvo que haya muchos años. Esperar que la condición mes del año del oro no pase BH (unos 13 años x 4 meses).

**Estado.** AMPLÍA (familia de calendario aceptada) — **Tipo.** generación — **Locura.** 1 — **Valor.** 3

#### Pre-FOMC en índices
**Fuente.** web: Lucca y Moench 2015 (https://www.newyorkfed.org/research/staff_reports/sr512.html); QuantSeeker (https://www.quantseeker.com/p/trading-the-fed-the-pre-fomc-drift).

**Qué dice.** La renta variable ganaba más del 80% de su prima en las 24 horas previas a las reuniones programadas del FOMC; no en bonos, FX ni materias primas (entonces). En 2024 y después se dice que «sigue viva».

**Qué significaría aquí.** Una familia de calendario para CFD de índices y una comprobación: cuánto del P&L de un superviviente vive en ventanas pre-FOMC. Necesita el calendario económico.

**Estado.** AMPLÍA (familia de calendario; calendario económico aceptado) — **Tipo.** generación — **Locura.** 1 — **Valor.** 3

#### Contar como ensayos los subconjuntos de días de la semana
**Fuente.** Williams, *Long-Term Secrets*, p. 61-71.

**Qué dice.** Su ruptura en bonos restringida a compras martes y jueves y ventas miércoles y jueves: el beneficio bajó de 73 k$ a 56 k$, las operaciones a la mitad, el $ por operación de 113 a 173 y el drawdown de 10.031 $ a 3.500 $. Luego k asimétrico por lado (compra 40%, venta 200% del rango): 83% y 251 $.

**Qué significaría aquí.** Es selección dentro de muestra de manual (5 días x 2 lados). El filtro de día es barato en SQX, pero cada subconjunto cuenta en el ledger (2^5 = 32 por lado, no 1). Buen ejemplo para el capítulo de multiplicidad.

**Estado.** YA EXISTE (familia de calendario, mapa por día); AMPLÍA el recuento del ledger — **Tipo.** proceso — **Locura.** 0 — **Valor.** 3

#### El viernes que cierra en el extremo
**Fuente.** Schwager, *Market Wizards* (Dennis), p. 48; (Schwartz), p. 131.

**Qué dice.** Todos los granos cerraron en máximos anuales un viernes; Dennis compró al cierre y el lunes abrió al límite alcista. «Como mínimo, no tengas un corto en pérdidas un viernes si el mercado cierra en máximos, ni un largo si cierra en mínimos.» Schwartz: un viernes bajista suele ir seguido de un lunes bajista.

**Qué significaría aquí.** Una hipótesis de calendario: cierre semanal en o cerca del máximo de N semanas y continuación en el hueco o el primer día del lunes. Y una prueba de estructura de salida: P&L de posiciones mantenidas el fin de semana cuando el viernes cierra en el extremo adverso frente al resto. El hueco de fin de semana es real en oro, índices y Brent.

**Estado.** AMPLÍA (familia de calendario) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 3

#### Vencimientos de opciones: el corte de las 10:00 de NY y el anclaje al strike
**Fuente.** web: vencimientos de opciones FX (https://investinglive.com/orders/fx-option-expiries-for-11-september-10am-new-york-cut/ ; https://investingbridge.eu/blog/fx-option-expiries-strike-clusters-price/); Schwager, *New Market Wizards* (Hull), p. 146.

**Qué dice.** En FX, los vencimientos al corte de las 10:00 de NY anclan el precio a los grandes strikes y la volatilidad sube después del corte; hay listas diarias de vencimientos. Hull: una acción tiene el doble de probabilidad de acabar a 1/4 de punto del strike al vencimiento, por las coberturas de los creadores de mercado; su firma lo opera.

**Qué significaría aquí.** Una condición «tiempo hasta el corte de NY» y una familia de ruptura tras el corte. Para índices y oro: en vencimientos mensuales o trimestrales, ¿cierra más cerca de niveles redondos de strike y se comprime la volatilidad al final de la sesión? Se reutiliza la maquinaria de números redondos. Necesita un calendario de vencimientos.

**Estado.** NUEVA / AMPLÍA (familia de calendario) — **Tipo.** generación · datos — **Locura.** 2 — **Valor.** 2

#### Calendario del petróleo: API el martes, EIA el miércoles
**Fuente.** web: StoneX (https://futures.stonex.com/blog/eia-vs-api-weekly-crude-oil-inventory); EIA (https://www.eia.gov/petroleum/supply/weekly/).

**Qué dice.** API martes 16:30 ET, EIA miércoles 10:30 ET; las reuniones de la OPEP+ pesan más que la estacionalidad.

**Qué significaría aquí.** Eventos del Brent para el calendario económico y un corte «miércoles 10:30 ET» en el mapa condicional del Brent.

**Estado.** AMPLÍA (calendario económico aceptado) — **Tipo.** datos — **Locura.** 1 — **Valor.** 2

#### Hoja de ruta mensual por día hábil, dentro y fuera de muestra
**Fuente.** Williams, *Long-Term Secrets*, p. 89-91.

**Qué dice.** El movimiento medio diario por día hábil proyectado al año siguiente; 1998 siguió más o menos el mapa construido con datos hasta 1996.

**Qué significaría aquí.** Un gráfico por activo: retorno acumulado medio por TDM (o por hora de la semana en intradía) en `build`, superpuesto a oos1, con bandas bootstrap. Diagnóstico de estabilidad del calendario; el estudio es trivial y necesita el panel de retornos por barra.

**Estado.** NUEVA — **Tipo.** estudio — **Locura.** 1 — **Valor.** 2

### 4.8 · Entre mercados: lead-lag, divergencias y cestas

#### El estudio `leadlag`: la familia aceptada convertida en una prueba con veredicto por par
**Fuente.** Katsanos, *Intermarket Trading Strategies*, p. 102-136, 117-128, 285-297; Laïdi, *Currency Trading and Intermarket Analysis*, p. 135-160; Briese, *COT Bible*, p. 114-127.

**Qué dice.** Sumando los cuatro libros: (1) las correlaciones contemporáneas son grandes y bastante estables (oro-plata 0,6-0,8; oro-DXY -0,3 a -0,5 diario; EUR-GBP 0,7; cruces de yen frente a bolsa -0,3 a -0,5 en regímenes de carry); (2) el adelanto real a resolución diaria o semanal es casi cero una vez quitado el artefacto del solape; (3) los adelantos reales están en las fronteras de sesión (apertura del DAX frente al cierre previo del S&P r = 0,42; cierre de EE UU hacia el yen en la franja fina 21:00-01:00 UTC) y en residuos de regresión que revierten en horas (la divergencia DAX-ES se cerró en 2 h); (4) la correlación sube con el horizonte y se satura, y el horizonte de saturación es el tiempo de alcance; (5) las relaciones cambian de signo por régimen, así que hace falta una puerta de acoplamiento.

**Qué significaría aquí.** Un estudio Python por par preregistrado, sobre Dukascopy M1 remuestreado a M5/M15/M30/H1, con retornos sin solape: (a) correlación cruzada a desfases -12..+12 con IC por bootstrap de bloques, separada por tramo de sesión (Asia, Londres, solape NY, NY tarde, rollover) y por año, con la asimetría (r adelantado menos r retrasado) como estadístico; (b) curva correlación-horizonte; (c) reversión del residuo: z-score del residuo de N barras escalado por beta y retorno futuro del rezagado por decil; (d) prueba de alineación desplazando el líder ±1 barra; (e) prueba anidada contra el momentum propio del rezagado (tipo Granger); (f) coste por hora del preflight. Sale una tabla de decisión par x sesión x horizonte con esperanza neta, recuento de ensayos para el ledger y un sí/no por par para construir una plantilla de dos símbolos o un filtro sobre supervivientes. Solo datos en disco, más un CFD de índice para la pata del yen.

**⚠ Contradice.** El ejemplo que motiva la familia en `docs/AgentPDFs/ideas-de-edge-2026-09-26.md` («el oro sigue al dólar y a los tipos reales») es contemporáneo, no un adelanto: oro frente a DXY r = -0,313 a desfase 0 y -0,025 a un día, |r| < 0,03 a 1-10 días (Katsanos, p. 123, Tabla 7.4). La hipótesis debería reformularse como «adelantos en fronteras de sesión y reversión de residuos».

**Estado.** AMPLÍA (familia lead-lag aceptada: este es su plan de prueba) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 5

#### Trampa: el lead-lag medido con retornos solapados de varios días es un artefacto
**Fuente.** Katsanos, *Intermarket Trading Strategies*, p. 117-123 (Tablas 7.3 frente a 7.4); Briese, *COT Bible*, p. 82-90, 124.

**Qué dice.** Desplazando el cambio SEMANAL (5 días) del oro contra XAU, plata, CRB y dólar salen correlaciones «adelantadas» de 0,25-0,59 a 1-4 días (XAU frente a oro 0,589 a -1), y Katsanos concluye que «XAU adelanta al oro». La misma prueba con retornos DIARIOS sin solape se hunde: XAU a desfase 1 r = 0,092, plata 0,014, dólar -0,025. Una ventana de 5 días desplazada 1-4 días comparte 4-1 días consigo misma: la curva semanal es sobre todo el núcleo triangular del r contemporáneo de 0,68. Briese: la retroalimentación medida mensualmente parece invertida frente a la semanal; la agregación crea retroalimentación aparente.

**Qué significaría aquí.** La primera comprobación del estudio `leadlag`: correlación cruzada con retornos sin solape en la barra que se opera, o con errores HAC/Newey-West, y comparar el r desfasado con el que implica el solape del r contemporáneo.

**Estado.** NUEVA (salvaguarda de la familia aceptada) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 5

#### Trampa: cierres asíncronos y alineación de barras filtran el futuro
**Fuente.** Katsanos, *Intermarket Trading Strategies*, p. 92, 102, 169, 234, 281; Chan, *Algorithmic Trading*, p. 10-16.

**Qué dice.** La correlación diaria S&P frente a DAX o Nikkei no tiene sentido sin desplazar el S&P un día, porque cierra 4,5 h después de Europa. Aun así Katsanos ejecuta su sistema de FTSE «el mismo día al cierre» usando cierres del CAC, cuyos futuros cerraban más tarde. Chan: los cierres asíncronos de distintas bolsas hacen falsos los diferenciales entre mercados. Katsanos: una entrada de otro mercado aísla del mal tick de la serie operada, pero al revés, una condición de dos símbolos duplica la exposición a anomalías del feed; una barra M1 que falta en el líder crea una divergencia falsa. En FX no hay cinta oficial: los proveedores agregan bancos distintos, filtran atípicos y usan horas de cierre diario distintas (p. 281); Chan: el FX es fragmentado y las cotizaciones dependen del lugar.

**Qué significaría aquí.** En todo backtest de dos símbolos sobre CFD 24h, la convención de marca de tiempo (apertura o cierre de barra) de AMBOS feeds debe coincidir al segundo, y la barra diaria o H4 del líder debe estar completa antes de que abra la barra operada que la usa. Dukascopy M1 está en UTC y alineado; el riesgo está en (a) cómo trata SQX un segundo gráfico con plantillas de sesión o festivos distintos, (b) el remuestreo en Python (etiqueta derecha o izquierda), (c) feeds de bróker con otra hora de servidor. Prueba unitaria de alineación: desplazar el líder +1 barra y ver que el edge desaparece si era fuga contemporánea; -1 y ver que no explota. feedQuality debe cubrir el feed del líder y la alineación de ambos.

**Estado.** NUEVA — **Tipo.** estudio · datos — **Locura.** 0 — **Valor.** 5

#### Mapa de líderes preregistrado para los feeds propios
**Fuente.** Katsanos, *Intermarket Trading Strategies*, p. 21, 97, 218, 233, 285-297; Laïdi, *Currency Trading and Intermarket Analysis*, p. 105-110, 231-237; Briese, *COT Bible*, p. 163-166.

**Qué dice.** Yen/USD frente a S&P pasó de r = -0,09 (11 años) a -0,373 (2006-07), frente al TNX de -0,08 a -0,49; el carry invirtió la correlación S&P-yen en 2005. AUDJPY sigue de cerca al All Ordinaries; AUD/USD sigue al oro (r = 0,46 semanal) más que a la bolsa australiana. El AUD sigue al cobre, el CAD al petróleo, el NZD a la leche. Para el DAX, Katsanos eligió el CAC y no el Euro Stoxx 50 porque comparte 13 acciones con el DAX (y ganó el CAC). Las tablas de correlación de niveles minadas son espurias («Yahoo 0,73 con el JPY», «Wiseman Dairies 0,94 con el EUR»).

**Qué significaría aquí.** Una lista `leaders` por activo principal, escrita ANTES de mirar (como ya hace `_markets.yaml` en crossmarket): AUDJPY, CADJPY, EURJPY, GBPJPY ← CFD de índice de EE UU o UE (riesgo), y CADJPY también ← Brent; AUDUSD ← XAUUSD; USDCAD ← Brent; XAUUSD ← DXY sintético y XAGUSD; EURUSD → GBPUSD. Los líderes deben compartir un impulsor, no aritmética: en FX la identidad triangular (EURJPY = EURUSD x USDJPY) está atada por arbitraje y no se opera a costes minoristas. Comprobar que la relación existe en cada segmento (build, oos1, oos2): si solo existe en `build` es régimen. El cobre entra en la lista de deseos del segundo proveedor.

**Estado.** AMPLÍA (familia lead-lag: la lista concreta de pares y la disciplina de `_markets.yaml`) — **Tipo.** proceso · generación — **Locura.** 1 — **Valor.** 5

#### Cierre de la bolsa de EE UU hacia el yen en la franja fina de 21:00 a 01:00 UTC
**Fuente.** Laïdi, *Currency Trading and Intermarket Analysis*, p. 146-147.

**Qué dice.** Entre el tercer trimestre de 2007 y el primero de 2008 el S&P caía a menudo un 1,5-1,8% en la última media hora; el yen ganaba contra casi todo, «sobre todo acelerado entre el cierre de la sesión de EE UU (16:00 EST) y la apertura de Tokio (20:00 EST), cuando el volumen es menor», y podía prolongarse en la sesión de Tokio.

**Qué significaría aquí.** El adelanto intradía más concreto de los cuatro libros. Prueba: signo y tamaño del retorno del CFD de índice de EE UU en la última hora de NY (20:00-21:00 UTC, con horario de verano) hacia el retorno de AUDJPY, EURJPY, GBPJPY y CADJPY de 21:00 a 00:00 y de 00:00 a 03:00 UTC. El coste importa: los spreads de rollover de 21:00-22:00 UTC son los más anchos del día. Necesita un feed de CFD de índice en AlgoData. Construible como plantilla de hora más segundo símbolo.

**Estado.** NUEVA (instancia concreta de la familia lead-lag) — **Tipo.** estudio · generación — **Locura.** 1 — **Valor.** 5

#### Lo entre mercados como FILTRO sobre supervivientes que ya existen
**Fuente.** Katsanos, *Intermarket Trading Strategies*, p. 227-230, 296-302; Williams, *Long-Term Secrets*, p. 72-73, 76-77, 233-237.

**Qué dice.** Cruce de medias del DAX con interruptor CI, fuera de muestra 2004-07: 51 operaciones, PF 1,93, 1.156 € de media. Añadiendo «ningún largo con disparidad DAX-ESTX negativa»: 26 operaciones, PF 4,18, 3.645 € de media; el beneficio neto solo de 58,9 k a 94,8 k. EURUSD de tendencia con «CRB sobre su media de 35 y TNX bajo su media de 5» para largos: fuera de muestra 62 a 38 operaciones, PF 1,70 a 4,08, drawdown de 11,9 k€ a 7,95 k€ (y la correlación CRB-euro se dobló de 0,26 a 0,57 entre dentro y fuera). Williams: ruptura del S&P solo larga si el bono cierra sobre el de hace 5 días: $ por operación de 228 a 281 y drawdown de 13.025 $ a 5.250 $. Un filtro sube el $ por operación y baja el drawdown a costa de exposición.

**Qué significaría aquí.** La forma más barata de probar la familia no son plantillas nuevas: tomar los supervivientes de la puerta en XAUUSD o cruces de yen, añadir «el líder está de acuerdo» (signo del retorno de N barras o disparidad) como filtro Python sobre sus listas de operaciones, y compararlo con quitar al azar la misma fracción de operaciones. Coste en estrategias y ganancia en PF por operación, como pide el dueño. Sin CRB ni TNX, los sustitutos son la media de XAU, XAG y Brent (o AUD y CAD) como cesta de materias primas y USDJPY como el sustituto de mercado más cercano de los tipos de EE UU.

**Estado.** NUEVA — **Tipo.** estudio — **Locura.** 1 — **Valor.** 5

#### El adelanto vive en la frontera de sesión y cambia de líder según qué bolsa está abierta
**Fuente.** Katsanos, *Intermarket Trading Strategies*, p. 102-105, 133-136.

**Qué dice.** Cambio diario del DAX frente al del S&P del día anterior: r = 0,134. Hueco de apertura del DAX frente al cambio previo del S&P: r = 0,422. Con futuros que cierran a la misma hora, DAX-S&P diario sube de 0,13 a 0,55. Con rendimientos de 30 minutos, antes de las 15:30 CET el ESTX adelanta levemente al ES y tras la apertura de EE UU se invierte; el DAX va detrás de ambos en todos los tramos. Regla: usar señales entre mercados solo cuando el mercado subyacente está CERRADO y el liderazgo pasa al que sigue abierto. Pero adelanto ≈ retraso ≈ 0,65 en cada fila, el patrón simétrico del artefacto de solape: la asimetría real es de 0,005-0,012.

**Qué significaría aquí.** Probar lead-lag y sesión juntas (lead-lag condicionado a la hora): el movimiento de A durante las horas en que B está fino hacia la primera hora líquida de B. Copiar el diseño (dividir por tramo de sesión, quitar horas con una pata cerrada, alinear husos), no los números. El estadístico es la asimetría con IC por bootstrap de bloques.

**Estado.** AMPLÍA (familias lead-lag x sesión) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 4

#### Curva de correlación frente a horizonte: el horizonte de saturación es el tiempo de alcance
**Fuente.** Katsanos, *Intermarket Trading Strategies*, p. 106-109, 124-130.

**Qué dice.** La correlación DAX-ES de retornos de k días sube de 0,617 (1 d) a 0,803 (5 d) y 0,824 (10 d) y luego se aplana. Intradía, DAX-ESTX se aplana a unos 75 min (0,877 a 5 min, 0,908 a 75); DAX-ES sigue subiendo. Oro-dólar tiene su pico en retornos de 9 días (-0,433). Ley empírica r_i = r_j (T_i/T_j)^0,01 a 0,04. Recomienda horizontes de 5-10 días o unos 75 min para indicadores entre mercados.

**Qué significaría aquí.** Es el efecto Epps (la correlación se encoge a horizontes cortos por negociación asíncrona y ruido). Una curva por par de feeds (M1 → 1 min a 1 día) dice a qué tamaño de barra tiene señal una condición de dos símbolos y cuánto tarda en alcanzar el rezagado. Sale la retrospectiva recomendada del segundo símbolo y una recomendación de marco (M30, H1 o H4).

**Estado.** NUEVA — **Tipo.** estudio — **Locura.** 1 — **Valor.** 4

#### Correlación móvil inestable: puerta de acoplamiento y régimen de correlación
**Fuente.** Katsanos, *Intermarket Trading Strategies*, p. 25-26, 34-48, 87-95, 252-268.

**Qué dice.** La r anual S&P-Nikkei fue de -0,22 a 0,84; S&P-DAX de -0,52 a 0,97; bolsa-bonos cambia de signo en crisis; S&P-yen se invirtió en 2005 con el carry; oro-S&P en abril de 2003. «Mira siempre la tasa de cambio de la correlación antes de operarla.» En su sistema de petroleras solo operaba valores con r de 300 días ≥ 0,5 con el XOI, lo que «mejoró el rendimiento y bajó el drawdown»; los sistemas de divergencia fallan en periodos de desacople temporal. Es la mejora práctica más consistente del libro. Higiene: las correlaciones de niveles exageran (S&P-FTSE R² = 0,909 en precios frente a ρ = 0,43 en retornos diarios), un solo atípico mueve r y los racimos en un diagrama de dispersión (S&P-Nikkei, 3 regímenes con pendientes opuestas) dejan sin sentido un único r: usar Spearman sobre cambios y mirar la dispersión.

**Qué significaría aquí.** Toda plantilla de dos símbolos necesita una segunda condición fija «correlación móvil(A, B, N) > umbral», o que el hueco aleatorio la elija de un grupo que la contenga. En el mapa condicional, un eje «régimen de correlación del principal con el líder de su familia». En crossmarket, publicar la correlación de cada mercado con el principal en build, oos1 y oos2: un edge que solo se transfiere con correlación alta es LA MISMA operación, no un segundo mercado.

**Estado.** AMPLÍA (diseño de plantillas lead-lag; mapa condicional; interpretación de crossmarket) — **Tipo.** generación · estudio — **Locura.** 0 — **Valor.** 4

#### Bloque de residuo entre mercados: el movimiento esperado del rezagado
**Fuente.** Katsanos, *Intermarket Trading Strategies*, p. 130-131, 145, 150-151, 192-204, 221, 233; Aronson, *Evidence-Based TA*, p. 433-438.

**Qué dice.** DAX horario +0,2%, ES 0%; r = 0,797, desviaciones 0,185 y 0,239: el ES esperado es +0,12%, y superó al DAX en 0,16% en las 2 horas siguientes. Divergencia = Y_pred - Y_real, con Y_pred = r x sd(Y)/sd(X) x X. Los 14 sistemas de oro del libro (1995-2007) fueron todos rentables, PF 2,9-35, pero con 16-38 operaciones y optimizados en toda la muestra; el coeficiente del dólar en la regresión del oro derivó de -0,29 (15 años) a -0,57/-0,62 (3 años). Aronson: la divergencia debe escalarse por par (doble normalización) y el residuo de una relación de cointegración es la versión con fundamento, que puede incluso predecir una tercera serie.

**Qué significaría aquí.** Un indicador personalizado: residuo del retorno de N barras del principal frente al del líder escalado por beta, en z-score, con beta calculada en ventana móvil dentro del indicador (su forma «sin optimización, coeficientes por fórmula»), nunca una beta fija ajustada. Pares candidatos: XAUUSD ← XAGUSD; XAUUSD ← -EURUSD o DXY sintético; AUDUSD ← XAUUSD; CADJPY ← BRENT; AUDJPY ← CFD de índice; EURJPY ← EURUSD y USDJPY. Como bloque de SQX necesita el segundo símbolo dentro de SQX; si no, precalculado en Python como serie extra.

**⚠ Contradice.** Katsanos defiende reoptimizar periódicamente los coeficientes (p. 150-151, 198, 221, 233), en contra de «operar la meseta y gastar oos2 una vez» para cualquier estrategia que dependa de una beta ajustada entre mercados. La salida coherente con el proyecto: beta móvil calculada dentro del indicador.

**Estado.** NUEVA — **Tipo.** generación — **Locura.** 1 — **Valor.** 4

#### Seis indicadores de divergencia entre dos mercados en un grupo aleatorio
**Fuente.** Katsanos, *Intermarket Trading Strategies*, p. 138-149; Williams, *Long-Term Secrets*, p. 138-145.

**Qué dice.** (1) Fuerza relativa = EMA3(A/B) normalizada por el oscilador de momentum. (2) Divergencia de Bollinger = EMA3[(BOL2-BOL1)/BOL1 x 100], con BOL = 1+(C-MA+2SD)/4SD; comprar en un pico sobre +10 a +30 (oro frente a plata, 20 días, ±15). (3) Disparidad = c x DS2 - DS1, con DS = (C-MA30)/MA30 x 100 y c el signo de la correlación (oro frente a DXY: c = -1, ±3%); la variante de Ruggiero solo señala con signos opuestos. (4) Divergencia de pendientes de regresión ajustadas por volatilidad (oro frente a CRB). (5) Divergencia de z-scores = corr x (Z2-Z1) (oro frente a euro, 250 días). Normalizador: MA3(Ind-LL200) x 100 / MA3(HH200-LL200); comprar bajo 30 y luego sobre 40. Esperar a que el indicador haga pico y gire. Williams añade un sexto, el Will-Spread: 100 x principal / secundario (bonos/oro; S&P/bonos) y EMA(5) - EMA(20) de ese diferencial en barras de 15-30 minutos; comprar al cruzar cero SI la barra siguiente supera el máximo de la barra del cruce (con la ventana de principio de mes, 1997: 13 operaciones, 10 ganadoras).

**Qué significaría aquí.** El vocabulario que necesita un grupo aleatorio de «segundo símbolo». Autorizarlos con sqx-custom-block si SQX puede referenciar un segundo gráfico en una condición; si no, precalcularlos en Python como serie de «divergencia». Ponerlos en UN grupo aleatorio y contarlos como seis ensayos por horizonte en el ledger. La confirmación «la barra siguiente rompe el extremo de la barra de señal» es un filtro genérico útil para el hueco aleatorio.

**Estado.** NUEVA — **Tipo.** generación — **Locura.** 1 — **Valor.** 4

#### EUR adelanta a GBP (y a AUD): la prueba más barata con dos feeds limpios
**Fuente.** Katsanos, *Intermarket Trading Strategies*, p. 295-297.

**Qué dice.** Correlación semanal EUR-GBP 0,73 síncrona; con el euro adelantado 1 día 0,58 y 2 días 0,47, frente a retrasado 0,51 y 0,37: «el euro adelanta a todas las demás divisas». EUR adelanta a AUD (0,48/0,38 frente a 0,45/0,34). La relación EUR-GBP es estable entre años (0,73-0,77).

**Qué significaría aquí.** La asimetría es pequeña (0,07-0,10) y medida con ventanas solapadas, así que es HIPÓTESIS, no evidencia. Prueba en EURUSD frente a GBPUSD M1 (mismo reloj): correlación cruzada de retornos sin solape de 5/15/30 min a desfases ±1..±6 por sesión. Si hay adelanto a M5-M30, una plantilla de GBPUSD con condición sobre el retorno de N barras del EURUSD es la primera plantilla lead-lag a construir.

**Estado.** NUEVA — **Tipo.** estudio · generación — **Locura.** 1 — **Valor.** 4

#### Índice dólar sintético con los propios feeds de FX
**Fuente.** Katsanos, *Intermarket Trading Strategies*, p. 68-72.

**Qué dice.** DXY = 50,14348112 x EURUSD^-0,576 x USDJPY^0,136 x GBPUSD^-0,119 x USDCAD^0,091 x USDSEK^0,042 x USDCHF^0,036. El EUR pesa el 57,6% y r(EUR, DXY) = -0,98. Correlación mensual con el DXY: oro -0,51, plata -0,33, crudo -0,26, AUD -0,66.

**Qué significaría aquí.** Con EURUSD, GBPUSD, USDCAD, USDCHF y USDJPY en M1 (el SEK, un 4,2%, se quita y se renormaliza), una serie DXY M1 en AlgoData como segundo gráfico «dólar» para plantillas de oro, plata y Brent, o como estado de tendencia del dólar precalculado; importable a SQX como símbolo personalizado. El impulsor entre mercados más importante del oro, construible con lo que ya está en disco.

**Estado.** NUEVA — **Tipo.** datos — **Locura.** 1 — **Valor.** 4

#### Separar el XAUUSD en «dólar» y «oro propiamente dicho»
**Fuente.** Katsanos, *Intermarket Trading Strategies*, p. 113-115.

**Qué dice.** En 2002-2005 el oro subió mucho en USD pero fue lateral y acabó más bajo en EUR: «la subida la causó un mercado bajista del dólar, no uno alcista del oro; la posición correcta era corto dólar». En caídas fuertes del dólar oro y petróleo correlacionan casi perfectamente.

**Qué significaría aquí.** Construir XAUEUR = XAUUSD/EURUSD (y el DXY sintético) y regresar el P&L de cada estrategia de XAUUSD sobre (retorno del dólar, retorno del oro en EUR). Si el edge está todo en la pata del dólar, es una estrategia de FX disfrazada y su familia de crossmarket debería ser EURUSD/USDCHF, no la plata. Idea de generación: construir en SQX sobre XAUEUR como instrumento sintético (oro sin dólar).

**Estado.** NUEVA — **Tipo.** estudio · datos · generación — **Locura.** 2 — **Valor.** 4

#### Régimen de apetito por riesgo para cruces de yen y divisas de alto rendimiento
**Fuente.** Laïdi, *Currency Trading and Intermarket Analysis*, p. 135-160.

**Qué dice.** Cuatro indicadores de apetito por riesgo: índices de bolsa, VIX (>30 miedo, <20 complacencia), posiciones especulativas del COT en JPY y CHF, y diferenciales high yield. En las 13 mayores caídas de 1999-2007 (S&P -5% a -25%) el VIX subió 36-147%, los diferenciales 11-73% y el interés especulativo neto en JPY/CHF subió en 9 de 13. Semana del 17 de agosto de 2007: yen +6% frente al USD, +15% frente al AUD. Los periodos de VIX bajo son de acumulación de carry: se venden JPY y CHF.

**Qué significaría aquí.** Un estado de riesgo con los propios feeds (tendencia y volatilidad realizada del CFD de índice, más la amplitud de los cruces de yen) como eje del mapa condicional de todas las estrategias de cruces de yen y AUD, y como condición de generación («largo AUDJPY solo con la volatilidad realizada del índice en su tercil bajo»). El VIX es externo; la volatilidad realizada del índice es un sustituto gratuito. Es el impulsor documentado dominante de los cruces de yen, cuatro de los feeds.

**Estado.** AMPLÍA (familia de régimen de volatilidad; mapa condicional) — **Tipo.** estudio · generación — **Locura.** 1 — **Valor.** 4

#### Momentum transversal y rotación dentro del propio universo
**Fuente.** Aronson, *Evidence-Based TA*, p. 350-352; Chan, *Algorithmic Trading*, p. 144-147; Abraham, *Trend Following Bible*, p. 90-92, 96; Faith, *Way of the Turtle*, p. 118-120, 271-272; Katsanos, *Intermarket Trading Strategies*, p. 264-277; *New Frontiers in Technical Analysis*, p. 49-83; Schwager, *New Market Wizards* (Blake), p. 95.

**Qué dice.** La mayor parte de la evidencia de información pasada viene de ordenar un corte transversal, no de temporizar un mercado. Chan: ordenar 52 materias primas por retorno de 12 meses, largo arriba, corto abajo, un mes: Sharpe 1,37 (2005-07) y -33% anual en 2008-09. Abraham: ordenar mercados por la media de tres ROC semanales (2, 5, 7) y solo tomar rupturas largas arriba y cortas abajo: la ordenación es «el universo» y la ruptura el disparador. Faith: con señales simultáneas, largo el más fuerte y corto el más débil del grupo ((precio - precio de hace 3 meses)/N); los últimos mercados en señalar se movían menos y perdían más. RRG de *New Frontiers*: ratio y momentum de fuerza relativa, rotación horaria. Blake: el fondo mejor clasificado o liquidez.

**Qué significaría aquí.** Tres usos. (1) Un estudio sobre la salida de crossmarket: etiquetar cada operación con el rango de momentum transversal de su mercado al entrar (entre los 10) y leer P&L por rango; si el edge se concentra arriba para largos, una puerta de fuerza relativa es una familia nueva y una regla para elegir en qué mercado relacionado desplegar. (2) Un bloque de rango de fuerza relativa (momentum de 3 meses normalizado por ATR dentro de su grupo), precalculado. (3) Una familia de cesta a nivel de cartera, fuera del modelo de un símbolo de SQX.

**Estado.** NUEVA — **Tipo.** estudio · generación · cartera — **Locura.** 1 — **Valor.** 4

#### Cestas homogéneas: el «banco de peces» es más persistente que cada miembro
**Fuente.** Schwager, *New Market Wizards* (Blake), p. 94.

**Qué dice.** Si cada acción tiene un 55% de probabilidad, un grupo homogéneo de 99 se comporta como 99 monedas: P(mayoría) cerca del 75%; con 9 monedas, 62%. La persistencia sube con la homogeneidad; una muestra de 15 componentes anticipa la señal del sector un día.

**Qué significaría aquí.** Construir cestas sintéticas homogéneas con los mercados que ya hay (índice USD con los pares del dólar; metales XAU+XAG; los cruces de yen; el grupo de índices) y (a) probar si la persistencia de la cesta supera a la de cada miembro, (b) usar la señal de la cesta para operar el miembro con mejor volatilidad ajustada por coste. En SQX, la cesta como símbolo personalizado para señales y el miembro para operar; en Python primero como estudio. Una razón estructural de edge que el generador de un símbolo no puede encontrar.

**Estado.** NUEVA — **Tipo.** generación — **Locura.** 2 — **Valor.** 4

#### Instrumentos sintéticos de relación: ratios y diferenciales como mercados nuevos
**Fuente.** Tharp, *Trade Your Way* (Thomas), p. 99-103; Schwager, *Market Wizards* (Kovner), p. 38; Chan, *Algorithmic Trading*, p. 74-83; web: oro/plata cointegrados 2015-2025 (https://papers.ssrn.com/sol3/Delivery.cfm/5710242.pdf?abstractid=5710242&mirid=1 ; https://backtrader.readthedocs.io/en/latest/strategies-series/en/11-pairs-trading.html).

**Qué dice.** Los diferenciales dejan operar relaciones que no existen de otro modo (cruces, oro frente a plata, S&P frente a bonos); pueden adelantar a sus patas y tienen menos riesgo. Kovner prefería largo yen / corto marco a posiciones netas en dólar. Chan: filtro de Kalman para una ratio de cobertura dinámica. Web: oro y plata cointegrados y con reversión en 2015-2025, con ratio de Kalman y filtro de régimen.

**Qué significaría aquí.** Construir series sintéticas con los propios feeds (ratio XAU/XAG, Brent/XAU, índice/índice) y lanzar la construcción de SQX sobre ellas como si fueran mercados; se operan en MT5 con dos patas (SQX no opera diferenciales de forma nativa). También fuente lead-lag: ¿adelanta la ratio XAU/XAG al XAU? El coste de dos patas es la pega. Primer estudio de pares cuando llegue la cartera.

**Estado.** NUEVA — **Tipo.** generación — **Locura.** 2 — **Valor.** 3

#### Rasgos entre mercados alternativos: fuerza de divisa contra el oro y residuo tras el factor USD
**Fuente.** Laïdi, *Currency Trading and Intermarket Analysis*, p. 32-38; Schwager, *Stock Market Wizards* (Masters, Shaw), p. 114, 142.

**Qué dice.** Graficar cada divisa contra el oro quita «la otra pata» del par; la divisa contra la que menos subió el oro es la más fuerte, y se compra la más fuerte contra la más débil (2001-08: el oro +90,5% frente al AUD, +123% frente al CAD, lo máximo frente al USD: largo AUDUSD). Correlación a seis meses con el oro: USDX -0,53, EUR +0,53, AUD +0,53. Masters opera cuando el movimiento de una acción está dominado por fuerzas propias y no de mercado; Shaw cubre los factores que no quiere apostar.

**Qué significaría aquí.** Un estado transversal de «fuerza» por divisa calculado con los feeds (el oro en EUR, GBP, JPY, CAD, CHF, AUD vía XAUUSD y los pares del USD); operar un par solo cuando sus dos patas están en extremos opuestos del ranking. Y una familia FX de residuo: descomponer cada par en un factor USD (o JPY, EUR) más un residuo, y operar los movimientos del residuo. Valor predictivo sin probar.

**Estado.** NUEVA — **Tipo.** datos · generación — **Locura.** 2 — **Valor.** 3

#### Modelo de oro con tres predictores no colineales
**Fuente.** Katsanos, *Intermarket Trading Strategies*, p. 50-55, 149-156.

**Qué dice.** Añadir predictores de uno en uno y parar cuando el cambio de r² es casi nulo; quitar los de tolerancia 1-r²_j < 0,20. Tres bastan. Oro con rendimientos de 9 días (donde oro-dólar tiene su pico): R² XAU 0,484, +plata 0,549, +dólar 0,587, +CRB 0,592; el CRB tiene r = 0,44 con el oro pero correlación parcial casi nula. G9 = 0,07 + 0,216 XAU9 + 0,166 S9 - 0,43 D9. La correlación semiparcial r_y1(2) = (r_y1 - r_y2 r_12) / raíz(1 - r_12²) sirve para pesar predictores.

**Qué significaría aquí.** Sin mineras de oro, el modelo propio es plata + DXY sintético (+ AUDUSD). Comprobar si su R² con rendimientos de 9 días en 2013-2026 sigue cerca de 0,5. La correlación parcial decide qué segundos símbolos debe ver una plantilla de oro (evitar EURUSD y DXY juntos) y limita la multiplicidad de la búsqueda.

**Estado.** NUEVA — **Tipo.** estudio · generación — **Locura.** 1 — **Valor.** 3

#### Disparador de una divergencia: esperar a que el rezagado empiece a responder
**Fuente.** Katsanos, *Intermarket Trading Strategies*, p. 196-197.

**Qué dice.** La divergencia puede seguir creciendo sin revertir. Entrada: (1) el oscilador de la divergencia hace pico y vuelve a cruzar 80/20; (2) el mercado operado confirma (estocástico de 5 días cruza su media de 3); (3) el ROC del líder apunta en la dirección esperada; (4) señal extendida 3 días por asincronía; (5) divergencia mínima ≥ 0; salida por tiempo a 50 barras porque las salidas de divergencia escasean.

**Qué significaría aquí.** Esqueleto de plantilla lead-lag: condición fija «divergencia extrema y girando» + hueco aleatorio (SQX elige la confirmación), que encaja con la forma por defecto del dueño. Estos sistemas no tienen salida natural: el grupo de salidas necesita una salida por número de barras.

**Estado.** NUEVA — **Tipo.** generación — **Locura.** 0 — **Valor.** 3

#### Grafo causal antes de elegir condiciones de otro mercado o de régimen
**Fuente.** web: López de Prado, inversión causal por factores (https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4205613 ; https://www.adialab.ae/research-series/a-protocol-for-causal-factor-investing ; https://rpc.cfainstitute.org/sites/default/files/docs/research-reports/rf_lopezdeprado_causalityprimer_online.pdf).

**Qué dice.** «Espejismo de factor»: estadísticamente válido pero causalmente mal especificado (sesgo de colisionador o de confusor); construir un grafo causal (PC/LiNGAM + conocimiento del dominio) antes de elegir condiciones.

**Qué significaría aquí.** Para condiciones que usan un segundo mercado o regímenes, dibujar el grafo: por ejemplo, una estrategia de oro filtrada por DXY está confundida por los tipos de EE UU. Complementa la tarjeta de mecanismo.

**Estado.** NUEVA — **Tipo.** proceso — **Locura.** 1 — **Valor.** 2

#### Posicionamiento estimado de los CTA como variable de congestión
**Fuente.** web: replicación del índice CTA (https://qoppac.blogspot.com/2024/11/cta-index-replication-and-curse-of.html); Macrosynergy, posicionamiento de seguidores de tendencia (https://macrosynergy.com/research/estimating-the-positioning-of-trend-followers/ ; https://arxiv.org/pdf/2607.19497).

**Qué dice.** El índice SG Trend se replica con unas 5 mangas de horizonte (1/3 rápida de 20 días, 2/3 de 125 y 500 días) y su alfa residual no es significativa. Macrosynergy estima el posicionamiento de los seguidores de tendencia a partir de precios.

**Qué significaría aquí.** El posicionamiento CTA estimado con los propios precios como variable de condicionamiento: tendencia saturada, riesgo de reversión. (La regresión de un superviviente sobre las mangas es una prueba de «beta de tendencia», sección V.)

**Estado.** NUEVA — **Tipo.** estudio · datos — **Locura.** 1 — **Valor.** 2

#### Oro liderando solo frente a oro con todo el complejo de materias primas
**Fuente.** Laïdi, *Currency Trading and Intermarket Analysis*, p. 46-47.

**Qué dice.** La subida del oro empezó en el tercer trimestre de 2001, un año antes que el resto de materias primas; si la subida del oro va acompañada del resto (2003, 2004, 2007), el USD está bajo presión secular; si el oro sube solo, el dólar tiene más opciones de aguantar.

**Qué significaría aquí.** Una etiqueta de régimen para estrategias de XAUUSD (oro liderando con XAG y Brent planos frente a subida amplia) en el mapa condicional. Régimen lento con pocos episodios independientes.

**Estado.** AMPLÍA (mapa condicional) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 2

#### Relaciones macro lentas: bonos adelantan 1-2 años, ratio oro/petróleo, USDJPY antes de la Fed
**Fuente.** Katsanos, *Intermarket Trading Strategies*, p. 23, 28; Laïdi, *Currency Trading and Intermarket Analysis*, p. 169-183, 249-254.

**Qué dice.** Los bonos hicieron techo en octubre de 1998, 18 meses antes que la bolsa; «no se puede usar en un sistema». Oro-petróleo correlacionan 0,78 mensual en niveles (1972-2007, correlación espuria de niveles con tendencia); ratio media unos 15; las cinco últimas recesiones de EE UU vinieron precedidas de una caída del 20-30% de la ratio. En cuatro ciclos de subidas de la Fed el diferencial 10-2 hizo pico 8-13 meses antes y el USDJPY tocó fondo 2-21 meses antes.

**Qué significaría aquí.** Fuera de escala para generar en M30-H4 y con muestras de 4-5 episodios; como mucho etiquetas de régimen lentas para el mapa condicional si un segundo proveedor trae rendimientos.

**Estado.** NUEVA (poco valor) — **Tipo.** datos · estudio — **Locura.** 1 — **Valor.** 1

### 4.9 · Regímenes: como condición de generación y como eje del mapa condicional

#### Cuatro estados de mercado (tendencia o lateral x tranquilo o volátil)
**Fuente.** Faith, *Way of the Turtle*, p. 25-27, 180-182, 207-212.

**Qué dice.** Estable-tranquilo, estable-volátil, tendencia-tranquila, tendencia-volátil. Los seguidores de tendencia adoran la tendencia tranquila; los de contratendencia, el lateral volátil. Una prueba de 20 años con 13 años de tendencia tranquila y 7 volátiles dice poco de la década siguiente (la secuencia QQQVVQ es n = 6). El tamaño efectivo de la muestra es el número de episodios de estado cubiertos, no el de operaciones.

**Qué significaría aquí.** El mapa condicional separa volatilidad y tendencia por separado; la celda natural es el estado conjunto 2x2. Y añadir a cada informe la mezcla de estados de build, oos1 y oos2: un superviviente cuyo OOS cayó en su estado favorito tiene un OOS poco representativo.

**Estado.** AMPLÍA (mapa condicional) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 3

#### Alineación con el marco temporal superior
**Fuente.** Abraham, *Trend Following Bible*, p. 121-127; *New Frontiers in Technical Analysis*, p. 94-116.

**Qué dice.** Operar el marco inferior solo en la dirección del superior (signo y pendiente del MACD semanal para operaciones diarias; diario para horarias), entrar en un retroceso del marco inferior con una orden stop un tick más allá del extremo de las dos barras previas, movida cada barra hasta ejecutarse o hasta que gire la tendencia superior. *New Frontiers*: el sesgo mensual como puerta en su tabla de filtros apilados.

**Qué significaría aquí.** Un eje del mapa condicional: la operación va con o contra la tendencia del marco superior (H4 para H1, D1 para H4). Si las operaciones en contra tienen esperanza negativa, el filtro de marco superior es una plantilla nueva de condición fija, revalidada en datos frescos (canal DMA de H4/D1 como fija, disparador de H1 en el hueco). Bloque de generación: entrada de retroceso con orden stop hacia la tendencia.

**Estado.** AMPLÍA (el mapa condicional mide tendencia por efficiency ratio, no alineación con otro marco) — **Tipo.** estudio · generación — **Locura.** 0 — **Valor.** 3

#### Semáforo de volatilidad: verde todo, ámbar solo salidas, rojo fuera
**Fuente.** Schwager, *Market Wizards* (Hite), p. 90; Fitschen, *Building Reliable Trading Systems*, p. 89-105.

**Qué dice.** Cuando la volatilidad de un mercado sesga en contra la relación rentabilidad-riesgo esperada, Mint deja de operarlo: verde toma todas las señales, ámbar solo salidas, rojo liquida y no toma ninguna; volatilidad en ventanas de 10 a 100 días (café 1986: fuera a 1,70 $, se perdieron la subida a 2,80 y el hundimiento a 1,00). Fitschen: un filtro de alta volatilidad con salida de las posiciones abiertas al superarse llevó la ganancia sobre dolor de 1,23 a 2,44; los filtros de baja volatilidad subían el beneficio por operación pero no la ganancia sobre dolor.

**Qué significaría aquí.** El mapa condicional ya divide por tercil de volatilidad; la decisión a la que debe llevar es esta capa preregistrada (sin entradas nuevas en el decil superior de volatilidad de la historia del activo, por ejemplo), probada fuera de muestra y contada como ensayo en el ledger.

**Estado.** AMPLÍA (mapa condicional hacia una decisión) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 3

#### «Tiempo de tendencia»: el rendimiento reciente de un sistema de tendencia canónico como régimen
**Fuente.** Schwager, *Market Wizards* (Seykota), p. 80.

**Qué dice.** Los periodos de éxito de los sistemas de tendencia aumentan su popularidad; al crecer los usuarios y pasar los mercados a lateral, dejan de ser rentables y echan a los que tienen poco capital. La rentabilidad de la tendencia va por ciclos.

**Qué significaría aquí.** Un eje del mapa condicional: retorno móvil de 6-12 meses de un sistema de tendencia canónico en el mismo activo. Pregunta por superviviente: ¿explica el tiempo de tendencia su resultado OOS? Si un superviviente de tendencia solo tuvo buen tiempo de tendencia, el veredicto debe decirlo.

**Estado.** AMPLÍA (mapa condicional) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 3

#### Indicadores externos de riesgo como ejes: el mismo ayuda a una estrategia y mata a otra
**Fuente.** Chan, *Algorithmic Trading*, p. 184-186; Chan, *Quantitative Trading*, p. 119-126.

**Qué dice.** Con el VIX > 35 el día anterior, el buy-on-gap (reversión) mejora y el momentum de hueco del FSTX se hunde (Sharpe 1,4 a 0,16). Candidatos: VIX, diferencial TED, HYG, MXN, específicos (petróleo para GLD-GDX). Las crisis son raras, así que es fácil espiar datos. Chan prefiere minar puntos de giro con muchos predictores candidatos en ventana móvil a modelos de cambio de régimen.

**Qué significaría aquí.** Añadir ejes externos al mapa condicional (tercil del VIX, un sustituto de riesgo como la tendencia de AUDJPY o MXN, tendencia del DXY), solo descriptivos como manda el dueño, con el intervalo visible en las pocas operaciones de cada celda de crisis. Necesita una serie diaria de VIX o DXY en AlgoData (o el DXY sintético).

**Estado.** AMPLÍA (mapa condicional; segundo proveedor aceptado) — **Tipo.** estudio · datos — **Locura.** 1 — **Valor.** 3

#### Pendiente del ADX: los osciladores solo funcionan con el ADX cayendo
**Fuente.** Tharp, *Trade Your Way* (LeBeau-Lucas), p. 215-216.

**Qué dice.** Mientras el ADX sube, los osciladores de sobrecompra y sobreventa no funcionan; funcionan con el ADX bajando. Un salto de 15 a 20 es mejor señal de tendencia que de 25 a 27.

**Qué significaría aquí.** Una hipótesis condicional directa para el mapa: dividir las operaciones de supervivientes de reversión por la pendiente del ADX al entrar. Si se cumple, «ADX cayendo» es candidata a condición fija de plantillas de oscilador.

**Estado.** AMPLÍA (eje nuevo del mapa condicional) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 2

#### Volatilidad de la volatilidad y dirección del cambio de volatilidad
**Fuente.** Chan, *Algorithmic Trading*, p. 24-25; Covel, *Trend Following*, apéndice E p. 383.

**Qué dice.** Tras 2008 el volumen se redujo a la mitad, la volatilidad media bajó pero los estallidos súbitos subieron (flash crash de 2010, agosto de 2011): las estrategias de reversión, que «prosperan con una volatilidad alta pero constante», perdieron, y el momentum entró en un mercado bajista de varios años. Mulvaney: condicionar a si la volatilidad sube o baja, no solo a su nivel.

**Qué significaría aquí.** Dos ejes para el mapa condicional además del tercil de volatilidad: la volatilidad de la volatilidad (la reversión necesita volatilidad estable, no alta) y el signo del cambio de volatilidad.

**Estado.** AMPLÍA (mapa condicional) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 2

#### Regímenes por modelo oculto de Markov: útiles solo si se ajustan en build y se prueban como ensayo
**Fuente.** Chan, *Quantitative Trading*, p. 119-126; web: QuantStart, HMM (https://www.quantstart.com/articles/market-regime-detection-using-hidden-markov-models-in-qstrader/); HMM acoplado USDCHF-oro (https://arxiv.org/pdf/1308.0900).

**Qué dice.** Chan: los HMM suponen probabilidades de transición constantes y nunca dicen CUÁNDO cambiará el régimen; «inútiles para operar». En la web: HMM en oro con emisiones de retornos, volatilidad y rango en walk-forward; evitar el estado de alta volatilidad mejoró el Sharpe en un estudio; QuantStart usó un HMM ajustado antes de 2005 sin cambios en 2005-2014 (fuera de muestra real). Un HMM acoplado filtra USDCHF con la dinámica del oro: lead-lag a través de estados ocultos.

**Qué significaría aquí.** Una advertencia para la familia de régimen de volatilidad: la etiqueta debe poder calcularse al entrar (el mapa condicional ya lo hace) y un filtro con régimen HMM se prueba como un ensayo más del ledger, no se acepta por elegante. Como corte del mapa, «estado HMM ajustado solo en build».

**Estado.** AMPLÍA (mapa condicional, familia de régimen de volatilidad) — **Tipo.** generación · estudio — **Locura.** 1 — **Valor.** 2

#### Entropía de permutación como filtro de previsibilidad
**Fuente.** web: https://link.springer.com/article/10.1007/s10614-026-11347-2 ; https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7512194/.

**Qué dice.** Operar solo en ventanas de entropía baja; la entropía cae antes de las crisis.

**Qué significaría aquí.** Un corte barato del mapa condicional, «tercil de entropía», calculado con las barras.

**Estado.** NUEVA — **Tipo.** estudio — **Locura.** 2 — **Valor.** 2

#### Relación señal-ruido del ciclo dominante como régimen (no como entrada)
**Fuente.** Katz y McCormick, p. 203-212.

**Qué dice.** Banco de filtros wavelet en cuadratura para periodos 3-30; operar solo si la potencia del pico supera 1,5 veces la de los filtros a 2 o más de distancia. Funcionaba con «precisión de reloj» en un seno barrido con ruido y perdió dentro y fuera de muestra; solo el S&P aguantó. «Lo teóricamente atractivo u obvio tiende a no funcionar.»

**Qué significaría aquí.** La medida de ciclo dominante con puerta de SNR es una variable de régimen utilizable (cíclico o no) aunque sea mala como entrada, si existe un motor FFT o wavelet. Prior: no priorizar familias de temporización de ciclos.

**Estado.** AMPLÍA (mapa condicional) — **Tipo.** estudio — **Locura.** 2 — **Valor.** 2

#### Dónde cierra la barra dentro de su rango, año a año, como monitor de cambio estructural
**Fuente.** Schwager, *Market Wizards* (Schwartz), p. 131.

**Qué dice.** «El mercado cierra cerca del máximo o del mínimo del día mucho más a menudo que antes»: dentro del 2% del extremo el 20% del tiempo en dos años, «imposible por azar»; lo atribuía a la negociación programada.

**Qué significaría aquí.** La distribución de la posición del cierre en el rango (por barra y por día) por año es un monitor barato de cambio estructural por activo: un desplazamiento señala régimen (nuevos participantes, nueva estructura de sesión, cambio de feed). También un control de feedQuality: un feed cuyos cierres diarios caen demasiado en los extremos puede tener errores de frontera de sesión.

**Estado.** AMPLÍA (feedQuality; mapa condicional) — **Tipo.** datos · estudio — **Locura.** 1 — **Valor.** 2

### 4.10 · Diseño de salidas y tiempo de permanencia

#### Curva de respuesta al impulso: P&L frente a salida por tiempo a N barras
**Fuente.** Williams, *Long-Term Secrets*, p. 45-55; Kirkpatrick y Dahlquist (CMT), p. 571; Covel, *Trend Following*, apéndice A p. 318-319.

**Qué dice.** S&P «comprar la apertura del lunes si está bajo el cierre del viernes», stop 3.000 $: objetivo de 500 $ -8.150 $ con 59% de acierto; objetivo de 1.000 $ +13.737 $; salida al cierre +39.075 $; al cierre siguiente +68.312 $; al sexto cierre +71.600 $ y 251 $ por operación. Solo cambió el periodo de permanencia. El CMT: el riesgo crece con el tiempo y la recompensa no; no mantener más allá del momento en que acaba la recompensa. Covel: 18.000 operaciones de máximo histórico con stop de 10 ATR; casi todo el beneficio de operaciones de más de un año; permanencia media 305 días.

**Qué significaría aquí.** Para una entrada fija, la curva de P&L frente a salida por tiempo N (1..50) contra la de entradas aleatorias al mismo N, y la R media por tramo de permanencia. La forma dice dónde vive el edge en el tiempo, si la salida propia añade algo sobre una salida por tiempo simple, y si la salida de SQX o la longitud de la ventana OOS truncan el edge (beneficio solo en las más largas) o si es un scalp a merced del spread (solo en las más cortas). Argumento directo contra objetivos pequeños fijos en la generación.

**Estado.** AMPLÍA (canal de «permanencia» de la escalera del mono; entryQuality) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 4

#### Lo que pasa en las primeras barras predice el destino de la operación
**Fuente.** Schwager, *New Market Wizards* (Sperandeo, Raschke), p. 103, 107, 116; Schwager, *Market Wizards* (Dennis), p. 54; (Ryan), p. 110; Schwager, *Stock Market Wizards* (Masters, Cook), p. 117, 164; *New Frontiers in Technical Analysis*, p. 302-307; Tharp, *Trade Your Way*, p. 246-247, 256.

**Qué dice.** Seis entrevistados por separado: «debería funcionar pronto o está mal». Sperandeo: con su mayor tamaño debería ganar al instante. Dennis: pérdida tras una o dos semanas, estás equivocado; en tablas tras mucho tiempo, probablemente también. Ryan: tener beneficio el primer día es de los mejores indicadores. Masters: cada operación tiene una ventana de tiempo. *New Frontiers*: una posición debe moverse a favor en un tiempo prefijado o salir antes del stop; cono de beneficio esperado y bandas de riesgo que crecen con la volatilidad; los brackets fijos 1:3 son «ineficaces». Tharp: antes de usar un stop temporal, medir cuántas veces una posición no hace nada 3 días y luego despega.

**Qué significaría aquí.** Un diagnóstico de entryQuality: P(la operación acaba positiva | P&L tras sus primeras k barras ≤ 0 o > 0), k = 1..5, y la tabla «R final media dado el R abierto a la barra k», leída como el stop del MAE, sin búsqueda. Si la curva es empinada, una salida temprana preregistrada (no optimizada) se prueba en structure. Un bloque de salida «salir en la barra k si MFE < x ATR». Una vista de cono de caminos de operaciones (mediana y cuantiles del P&L por barra desde la entrada) frente al cono raíz de t de una entrada aleatoria.

**Estado.** NUEVA (salida); AMPLÍA entryQuality — **Tipo.** estudio — **Locura.** 0 — **Valor.** 4

#### Calidad de la salida: qué hizo el precio después de salir
**Fuente.** Schwager, *Stock Market Wizards* (Minervini), p. 97-98, 102; Elder, *The New Trading for a Living*, p. 244-247.

**Qué dice.** Minervini estudió qué pasaba tras vender: descubrió que mantenía perdedoras demasiado; limitar pérdidas al 10% habría subido el beneficio un 70% quitando solo unas pocas ganadoras, porque «las ganadoras solían funcionar desde el principio». Elder revisa cada operación dos meses después y descubrió stops demasiado ajustados y salidas cortas que perdían las tendencias grandes.

**Qué significaría aquí.** Una lectura de «calidad de salida» junto a entryQuality: para cada operación, el camino del precio en las N barras TRAS la salida (en ATR, en la dirección de la operación), por tipo de salida (señal, stop, tiempo), frente a salidas aleatorias con la misma distribución de permanencia. Continuación persistente tras salidas por señal = salidas prematuras; rebote tras stops = stop en el ruido (lo que querría saber el paso del stop ATR). Diagnóstico, sin optimizar.

**Estado.** NUEVA (entryQuality mide excursiones durante la operación, no después) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 4

#### El stop depende del tipo de estrategia: catastrófico para reversión, del MAE para momentum
**Fuente.** Chan, *Quantitative Trading*, p. 106-107, 142-143, 156; Chan, *Algorithmic Trading*, p. 182-184; Katz y McCormick, p. 201, 211-212; Williams, *Long-Term Secrets*, p. 198, 228-229, 240-243; Faith, *Way of the Turtle*, p. 262-263; Fitschen, p. 69-79; Abraham, p. 26-27; Katsanos, p. 183-184, 215.

**Qué dice.** Chan: un stop solo ayuda si el precio va a empeorar durante la operación (momentum); un modelo de reversión, reevaluado sobre una posición perdedora, da la MISMA señal y nunca recomienda stop; «nunca he visto una estrategia de reversión cuyo Sharpe mejore con un stop», aunque eso es sesgo de supervivencia, así que el único stop lógico es uno más allá del peor drawdown intradía del backtest, que nunca salta en él. Katz: las entradas de punto de giro (lunar, estacional, ciclos) aciertan con casi nula excursión adversa o fallan mucho y «funcionan mejor con stops muy ajustados». Williams: las mismas entradas del S&P con stop de 500 $ -41.750 $, de 1.500 $ +116.880 $, de 5.000 $ +269.525 $; y en sistemas siempre dentro los stops nunca ayudaron. Faith: un cruce de medias sin stop tiene un stop implícito. Fitschen: un stop disparado al cierre y ejecutado en la apertura siguiente suele ganar al stop en reposo; en tendencia, solo el de 3 desviaciones mejoró la ganancia sobre dolor. Abraham: decidir antes si toca o si hace falta cierre más allá. Katsanos cita a W. Chan: los stops degradan los sistemas rentables y mejoran los no rentables.

**Qué significaría aquí.** Para el paso 24 (stop ATR leído del MAE, sin optimizar): etiquetar cada estrategia como de reversión o de momentum; para reversión, ofrecer la columna que el informe no tiene, un stop justo más allá del MÁXIMO MAE dentro de muestra de TODAS las operaciones (corta cero operaciones), y publicar cuántas operaciones cortaría cada regla; para momentum, el percentil del MAE como ahora. Medir primero el stop implícito que ya da la lógica de salida. Evaluar disparo intrabarra frente a cierre más allá y siguiente apertura, y que la semántica coincida con lo que hará el EA de MT5. Para familias de punto de giro, una MAE bimodal (casi cero en ganadoras) indica que la construcción sin stop puede estar ocultando su edge.

**⚠ Contradice.** El percentil 80-95 del MAE de las ganadoras corta por construcción un 5-20% de ganadoras dentro de muestra; para reversión Chan predice que baja el edge (*Quantitative Trading*, p. 106-107, 142-143; *Algorithmic Trading*, p. 183-184). Y Katz (p. 201, 211-212) dice que una construcción sin stop infravalora sistemáticamente las familias de punto de giro en el ledger.

**Estado.** AMPLÍA (`studies/closing/atrCalculator`) — **Tipo.** riesgo · estudio — **Locura.** 0 — **Valor.** 4

#### Vida media de la reversión como salida fija, y salida por la señal opuesta
**Fuente.** Chan, *Quantitative Trading*, p. 140-143; Chan, *Algorithmic Trading*, p. 47.

**Qué dice.** La vida media Ornstein-Uhlenbeck, estimada sobre toda la serie y no solo sobre los pocos días con operación, es mucho más robusta que un periodo de permanencia optimizado en el backtest: usar la media como objetivo y la vida media como permanencia máxima. Para momentum, salir cuando el modelo de entrada da la vuelta es un casi-stop justificado sin parámetro extra; para reversión, tope de beneficio cuando el precio toca el umbral de entrada opuesto.

**Qué significaría aquí.** Calcular la vida media por símbolo x marco (y por tercil de volatilidad) en `build`; en plantillas de reversión, máximo de barras en operación = 1-2 vidas medias, FIJO, lo que quita un parámetro libre a la búsqueda genética. Comprobar en las estrategias de reversión existentes su permanencia media frente a la vida media del mercado. Salidas por defecto: tendencia por señal opuesta (sin stop ni objetivo), reversión en la media o banda opuesta o tras N vidas medias.

**⚠ Contradice.** Fijar la permanencia con las operaciones del backtest «está plagado de sesgo de espionaje de datos» (Chan, *Quantitative Trading*, p. 140-141); SQX optimiza las barras de salida sobre operaciones.

**Estado.** NUEVA — **Tipo.** generación — **Locura.** 1 — **Valor.** 4

#### Escalera de excursión adversa condicional (DevStops de Kase)
**Fuente.** *New Frontiers in Technical Analysis*, p. 166-176.

**Qué dice.** Los múltiplos de ATR ignoran la variabilidad de los rangos: dos mercados con el mismo ATR y distinta dispersión necesitan stops distintos. TRD = máx(H, H[1], C[2]) - mín(L, L[1], C[2]); línea de aviso = TRD medio (50% de salir por ruido), Dev1/2/3 = media + 1/2,2/3,6 desviaciones (corrección por asimetría). Tabla empírica de 150.000 barras: si se toca la línea de aviso, P(tocar Dev1) cerca del 80% y P(Dev3) del 45%; P(Dev2 | Dev1) cerca del 80%. El riesgo crece con la raíz de la duración de la barra.

**Qué significaría aquí.** Para el paso del stop: la distancia debe salir de los cuantiles de la excursión adversa, no de su media (leer el cuantil empírico del MAE en unidades de TRD). Y un diagnóstico barato: P(el MAE llega al nivel j | llegó al i) para las operaciones propias frente a las del mono; si la continuación condicional de la estrategia es menor, sus entradas tienen apoyo real. La raíz de t sirve para reescalar stops en crossTF.

**Estado.** AMPLÍA (stop ATR del MAE; entryQuality) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 4

#### ¿Carga el edge la entrada o la salida? Una disputa que el ledger debe zanjar
**Fuente.** Faith, *Way of the Turtle*, p. 140-147; Covel, *The Complete TurtleTrader* (Eckhardt), p. 79; Tharp, *Trade Your Way*, p. 28-29, 197-201, 233-235; Covel, *Trend Following*, p. 262, 288.

**Qué dice.** Faith: Donchian con salida por tiempo a 80 días y SIN stop dio 57,2% de CAGR y MAR 1,31, frente a 29,4% y 0,80 de la versión con salida de ruptura: «una entrada con edge puede explicar toda la rentabilidad»; añadir stops de cualquier anchura empeoró todas las métricas en tres sistemas, y la salida por tiempo fue la que menos perdió al añadir 5 meses. Eckhardt, coautor del mismo sistema: «las liquidaciones son muchísimo más importantes que las iniciaciones; si inicias al azar te va sorprendentemente bien con un buen criterio de liquidación». Tharp: la entrada es «probablemente lo menos importante». Covel: un indicador técnico explica un 10% del éxito.

**Qué significaría aquí.** Una salida por tiempo fija es la más estable fuera de muestra y la más limpia para juzgar una entrada; conviene tenerla como salida canónica. Y publicar para cada superviviente qué canal (momento de entrada frente a permanencia o salida) lleva la R, agregado por familia de plantilla en el ledger.

**⚠ Contradice.** Tharp y Eckhardt argumentan contra una tubería que pone su esfuerzo generativo en plantillas de ENTRADA y construye sin stop; Faith, del mismo campo, apoya la postura del proyecto. Defendible pero sin probar por estrategia.

**Estado.** YA EXISTE en parte (canales de la escalera del mono) — **Tipo.** estudio · generación — **Locura.** 0 — **Valor.** 3

#### Salida por barra de volatilidad adversa (2 ATR en contra en una barra)
**Fuente.** Tharp, *Trade Your Way*, p. 261-262, 265.

**Qué dice.** Un movimiento de un solo día de 2 veces la volatilidad diaria media en contra es de las mejores salidas (y buena entrada inversa); flota sobre un trailing de 3 ATR, que tras 4R de beneficio se ajusta a 1,6 ATR. Diseñado desde los objetivos, «sin pruebas».

**Qué significaría aquí.** Un estudio de solo lectura para supervivientes sin stop: qué fracción de las grandes perdedoras tuvo pronto una barra adversa de 2 ATR y qué fracción de las ganadoras; si la proporción está muy desequilibrada, es una salida catastrófica candidata que no necesita búsqueda de parámetros.

**Estado.** NUEVA — **Tipo.** estudio — **Locura.** 1 — **Valor.** 3

#### Salida en la primera apertura con beneficio
**Fuente.** Williams, *Long-Term Secrets*, p. 61, 72, 157.

**Qué dice.** Bonos, apertura ± 100% del rango previo, stop de 1.500 $ o 50% del rango, salida en la primera apertura con beneficio: 73.468 $, 80% de acierto, 651 operaciones, drawdown 10.031 $ (1990-98). En mercados lentos, retrasarla 1-2 días. Sus tres únicas salidas: stop en dinero, esta, y giro con la señal opuesta.

**Qué significaría aquí.** Un bloque de salida «salir en la primera apertura de barra con P&L abierto > 0» (más un máximo de barras, y la variante retrasada a partir de k barras). Da acierto muy alto y media pequeña: aísla la calidad de la entrada, útil como salida de control en la escalera del mono.

**Estado.** NUEVA (bloque de salida) — **Tipo.** generación — **Locura.** 1 — **Valor.** 3

#### Objetivos de beneficio: ablación en vez de doctrina
**Fuente.** Covel, *Trend Following*, p. 22, 40, 263-264, apéndice E p. 383; Elder, *The New Trading for a Living*, p. 215-218; Schwager, *Market Wizards* (Dennis), p. 53; Katz y McCormick, p. 309-313.

**Qué dice.** Covel y Mulvaney: los objetivos implican predicción, limitan el beneficio y son una forma de estimación de la media «insostenible». Elder, en contra: «suficiente» es la palabra clave; exige objetivos y relación 2:1. Dennis: «esta estructura significa sube y esta significa ya no sube, pero nunca sube tanto y no más» (la soja «nunca» se movía más de 50 céntimos y subió 8 $). Katz, con entradas aleatorias: objetivos amplios ganan a ajustados (objetivo de 0,5 ATR, 69% de acierto y esperanza mucho peor; mejor 4,5 ATR con 39%); stop fijo óptimo 1-2 ATR; poca interacción entre ambos; superficies suaves.

**Qué significaría aquí.** En structure, si un superviviente tiene objetivo, quitarlo (sustituirlo por trailing o por tiempo) y comparar esperanza y asimetría OOS; y en el ledger, rendimiento por tipo de salida. No derivar objetivos del tamaño histórico de los movimientos (MFE). La superficie plana de Katz apoya que un stop leído del MAE hacia 1,5-2 ATR pierde poco frente al óptimo.

**Estado.** AMPLÍA (structure ablaciona entradas, no salidas) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 3

#### Devolución del beneficio abierto y trailing que se acelera
**Fuente.** Fitschen, *Building Reliable Trading Systems*, p. 79-85; Abraham, *Trend Following Bible*, p. 88-89, 101; Schwager, *New Market Wizards* (M. Ritchie), p. 127-130; (Eckhardt), p. 55; Katz y McCormick, p. 313-332.

**Qué dice.** Fitschen: el trailing ideal se ajusta más rápido cuando la operación se vuelve parabólica; pasar la media del trailing de 80 a 70/60/50/40 días cada vez que el beneficio supera otra desviación redujo el drawdown máximo con poco coste; el parabólico de Wilder a 0,02 quitó 150 $ por operación. Abraham: sus mayores drawdowns llegan justo tras sus mayores beneficios abiertos. M. Ritchie: si protegiera el beneficio abierto como el cerrado nunca participaría en un movimiento largo (el oro devolvió un 25% en un día en 1980 y seguía con gran beneficio). Eckhardt: tras un golpe de suerte a favor es legítimo pensar en retroceso; en el stop, nunca. Katz: la mejor salida sobre entradas aleatorias fue un stop inicial de 2,5 ATR, un stop tipo EMA de un solo sentido y un objetivo «que encoge» desde 5,5 ATR un 10% de la distancia por barra, máximo 30 barras: la pérdida por operación aleatoria bajó de -2.243 $ a -1.236 $.

**Qué significaría aquí.** Una medida de calidad de salida con datos que ya hay: la devolución (MFE menos realizado) por operación, en distribución, frente al mono con las mismas salidas, y si el drawdown de la cartera se predice por el beneficio abierto en el pico. Variantes de salida con valores por defecto del libro, sin optimizar, para structure o la fábrica de variantes una vez fijada la madre. No extender la lógica del MAE a protección de beneficio sin mirar la devolución de las mejores operaciones.

**Estado.** AMPLÍA (entryQuality MFE/MAE; structure) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 3

#### Curva de retraso también para la salida
**Fuente.** Chan, *Quantitative Trading*, p. 23, 66.

**Qué dice.** El mismo modelo de reversión actualizado en la apertura en vez del cierre pasó de Sharpe 0,25 a 4,43 bruto (de -3,19 a 0,78 neto). Si el deslizamiento medio resulta ser una ganancia, conviene retrasar deliberadamente la orden.

**Qué significaría aquí.** entryQuality tiene la curva de retraso de la entrada; falta la de la SALIDA (salir d barras antes o después), que muestra si la regla de salida lleva información o es solo un tiempo fijo; es la medida directa del canal de permanencia de la escalera. Leer el signo de la curva de entrada como decisión de diseño: si es positiva a d = 1, la estrategia debería entrar una barra tarde.

**Estado.** AMPLÍA (entryQuality `delay.py`) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 3

#### Señal en el marco lento, entrada en el rápido («acecho»)
**Fuente.** Tharp, *Trade Your Way*, p. 172, 179-180, 198-199.

**Qué dice.** Con la señal ya dada, bajar a un marco menor para encontrar el momento de menor riesgo; ruptura, retroceso y nueva ruptura como entrada de bajo riesgo con stop ajustado. Wyckoff: «no compres rupturas, espera la prueba del retroceso».

**Qué significaría aquí.** Para un superviviente de H4, un refinamiento mecánico: tras la señal de H4, entrar en el primer retroceso de M30 de k ATR(M30) en N barras (o saltarse la operación), comparando R por operación y número de operaciones. Es lo inverso de crossTF. El parámetro añadido se paga en el ledger.

**Estado.** NUEVA — **Tipo.** estudio — **Locura.** 1 — **Valor.** 3

#### Asimetría por dirección: las bajadas van más rápido
**Fuente.** Elder, *The New Trading for a Living*, p. 160; Schwager, *New Market Wizards* (Yass), p. 151-152.

**Qué dice.** Elder: las tendencias bajistas se mueven el doble de rápido que las alcistas. Yass: las puts fuera de dinero cuestan más que las calls porque un desplome siempre es más probable que una euforia nocturna.

**Qué significaría aquí.** Para supervivientes de ambos lados, comparar por dirección la velocidad del MFE (barras hasta el MFE), la permanencia y la distancia del stop; si es asimétrica, una regla de salida simétrica desperdicia edge en un lado: hipótesis de parámetros de salida separados por lado, validada como nueva. Sobre todo en índices.

**Estado.** AMPLÍA (canal de dirección de la escalera del mono) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 2

#### Salidas aprendidas como diagnóstico del edge que la salida deja sobre la mesa
**Fuente.** web: «Learning the Exit» (https://tr8dr.github.io/RLp1/); parada óptima con RL (https://arxiv.org/html/2604.02035).

**Qué dice.** Dada la entrada, aprender cuándo salir con una recompensa que penaliza drawdown y permanencia.

**Qué significaría aquí.** Choca con la postura de no optimizar stops, así que solo como diagnóstico: cuánto edge deja la salida sobre la mesa = cota superior (salida óptima a posteriori, gratis a partir del MFE) frente a la real.

**Estado.** NUEVA — **Tipo.** estudio — **Locura.** 2 — **Valor.** 2

#### Entradas conservadoras, salidas liberales; salidas evolucionadas con pocas reglas
**Fuente.** Katz y McCormick, p. 285-289, 333-347.

**Qué dice.** Una señal de salida no necesita la fiabilidad de la entrada: una entrada perdida es una oportunidad; una salida perdida puede ser catastrófica, así que se toleran salidas por falsa alarma; salir de largos cuando otros compran para que el deslizamiento juegue a favor. Una salida neuronal mejoró dentro de muestra y no fuera; una salida evolucionada por GA de 3 reglas mejoró en ambas muestras. Menos parámetros, mejor fuera de muestra.

**Qué significaría aquí.** Si alguna vez se buscan salidas en SQX, mantenerlas como listas cortas de reglas; las señales de salida de un modelo más débil son aceptables.

**Estado.** YA EXISTE (la plantilla limita el número de reglas) — **Tipo.** generación — **Locura.** 0 — **Valor.** 2

### 4.11 · Fuentes de datos nuevas

#### COT: unirlo por la fecha de PUBLICACIÓN, no por la del martes
**Fuente.** Briese, *The Commitments of Traders Bible*, p. 36, 128-134, 274-277; Katz y McCormick, p. 4; Aronson, *Evidence-Based TA*, p. 29-30, 382-383; web: CFTC (https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm); informe TFF (https://www.financialresearch.gov/hedge-fund-monitor/datasets/tff/).

**Qué dice.** Las posiciones se tabulan al cierre del martes y se publican el viernes a las 15:30 ET (semanal desde octubre de 2000; antes, publicaciones dobles alternas con 3 o 10 días de retraso; el informe combinado de opciones y futuros no llegó a la paridad de publicación hasta enero de 2002). «Cuando trabajas con las fechas reales de publicación descubres que el retraso importa, y mucho»: su sistema de medias del COT es rentable en 2000-2007 y «apenas» antes. «Las pruebas que entraban en la apertura semanal siguiente a una señal COT antes de 2002 no son hipotéticas, son imaginarias.» Los archivos públicos solo traen la fecha de compilación; los festivos movieron publicaciones. Para FX, el informe TFF y su categoría «Leveraged Money» son lo más predictivo a corto y medio plazo (gratis en la CFTC). Aronson: la presión de coberturas (comerciales vendedores netos en subidas) es lo que paga al seguidor de tendencia; y todo dato publicado con retraso se retrasa hasta su disponibilidad real. Katz: usar valores del mismo día da «un sistema fabuloso pero imposible de operar».

**Qué significaría aquí.** Si el COT entra como filtro o condición (oro, plata, crudo y futuros de divisas mapeados a los CFD), la clave de unión es fecha de publicación + 1 barra (conservador: primera barra tras el viernes 21:00 UTC), con una prueba unitaria que afirme que ninguna barra anterior ve el dato de la semana. Solo 2002 en adelante (los datos del proyecto empiezan en 2003). Escribirlo como ficha de knowhow cuando se construya. La misma regla vale para el calendario y cualquier macro.

**Estado.** NUEVA — **Tipo.** datos — **Locura.** 0 — **Valor.** 5

#### Calendario económico: sorpresa frente a consenso, y usarlo para volatilidad y exclusión, no para dirección
**Fuente.** Tharp, *Trade Your Way* (LeBeau), p. 89; *Sentiment in the Forex Market*, p. 24-44; Aronson, *Evidence-Based TA*, p. 376-379; Chan, *Algorithmic Trading*, p. 163; Schwager, *New Market Wizards* (Sperandeo), p. 103; Schwager, *Market Wizards* (Jones), p. 64; Schwager, *Stock Market Wizards* (Cohen), p. 146.

**Qué dice.** Un informe se juzga contra lo esperado: una cosecha un 10% menor es bajista si se esperaba un 15%; la primera reacción suele ser exagerada o errónea. *Sentiment*: la correlación móvil de 36 meses DXY-NFP fue negativa 215 meses y positiva 158; las siete sorpresas de NFP de más de 2 desviaciones movieron el dólar a favor 3 veces y en contra 4; sirve como variable de volatilidad, no de dirección. Aronson: si el edge es infrarreacción o sobrerreacción a noticias, su beneficio debe agruparse en las publicaciones. Chan no encontró momentum en EURUSD tras FOMC o IPC; Clare y Courtenay sí en GBPUSD 10 minutos tras datos del Reino Unido (datos hasta 1999). Sperandeo se queda plano ante incertidumbres legislativas; Jones no arriesga antes de informes clave. Cohen, 15 minutos antes de la Fed, deja órdenes lejos del precio «por si el mercado hace una tontería».

**Qué significaría aquí.** Guardar consenso y dato real para que el rasgo sea la sorpresa. Primeros usos: (1) atribución: parte del P&L de operaciones abiertas a través de una publicación de primer nivel frente a la parte del tiempo expuesto (una estrategia que dice explotar infrarreacción debe mostrar concentración; una que la muestra sin decirlo es una apuesta de volatilidad de noticias); (2) capa preregistrada «plano antes de evento de alto impacto», con y sin; (3) eje del mapa condicional y filtro de exclusión para entradas de reversión; (4) familias cortas: deriva o reversión tras la primera barra y órdenes límite a ±k ATR alrededor de la publicación (solo con fills modelados en M1, y cuidado con la selección adversa). M30 es probablemente demasiado lento para el momentum de publicación.

**⚠ Contradice.** Usado de forma direccional, el calendario va contra *Sentiment in the Forex Market*, p. 24-44 (muestra pequeña: es una cautela).

**Estado.** AMPLÍA (calendario económico aceptado) — **Tipo.** datos · estudio — **Locura.** 0 — **Valor.** 4

#### Qué puede y qué no puede hacer el COT: probarlo contra su gemelo de precio
**Fuente.** Briese, *The Commitments of Traders Bible*, p. 82-90, 114-127, 130-133; Laïdi, *Currency Trading and Intermarket Analysis*, p. 45-46.

**Qué dice.** Klitgaard y Weir (Fed de NY, 1993-2003): el cambio semanal de la posición especulativa coincide con la dirección del FX el 75% de las semanas y explica el 30-45% del movimiento de esa semana, pero NO predice la siguiente. Wang: índice COT de especuladores > 80% y coberturistas < 20% predicen hasta unas 8 semanas; por debajo de 4 semanas, nada; el signo cambia por sector (divisas +69% anual siguiendo a los especuladores, materias primas -82%). La posición de los fondos es casi un espejo del precio. La tabla de «35 de 35 mercados rentables» del propio Briese usa el mejor par de medias por mercado, dentro de muestra, sin costes (oro 140 $ por operación). Laïdi: los especuladores del oro pasaron de un récord de 201.859 netos largos a 74.343 netos cortos mientras el oro subía de 750 $ a 895 $.

**Qué significaría aquí.** El COT es un ahora-casting de quién mueve el precio esta semana y una señal débil de prima de riesgo a 4-8 semanas con signo sectorial: para estrategias M30-H4, como mucho variable de régimen semanal. Antes de construir ninguna tubería, la puerta debe probar el filtro contra el mismo filtro hecho solo con precio (signo del retorno de 13 semanas, estocástico de 3 años); si el COT no le gana a su gemelo, sobra. Requisitos: efecto a 4-8 semanas, signo preregistrado por clase, filtro Python sobre listas de operaciones de supervivientes frente a quitar al azar la misma fracción, dos parámetros como máximo contados en el ledger.

**⚠ Contradice.** El COT como condición de SQX choca con el horizonte de permanencia del proyecto (Briese, p. 124-127).

**Estado.** AMPLÍA (disciplina de control positivo y modelo anidado aplicada a datos alternativos) — **Tipo.** estudio · datos — **Locura.** 1 — **Valor.** 4

#### Volatilidad implícita y opciones: VIX, GVZ, OVX, CVOL y risk reversals
**Fuente.** Kirkpatrick y Dahlquist (CMT, Connors), p. 97, 386; *Sentiment in the Forex Market*, p. 114-115; Schwager, *New Market Wizards* (Yass), p. 152-153; web: CME CVOL (https://www.cmegroup.com/market-data/cme-group-benchmark-administration/cme-group-volatility-indexes.html ; https://www.cmegroup.com/education/articles-and-reports/introduction-to-the-cme-group-volatility-index-cvol.html); risk reversals y carry (https://www.nber.org/papers/w14473 ; https://qoppac.blogspot.com/2019/10/skew-and-expected-returns.html ; https://www.risk.net/cutting-edge/7959625/harvesting-the-fx-skew-premium).

**Qué dice.** Connors: VIX 5-10% sobre su media de 10 días con el índice sobre su media de 200 = excelente momento para comprar; los suelos se señalan mejor que los techos. Existen índices de volatilidad implícita para los activos del proyecto: VIX (US500, US30), VSTOXX (UE), GVZ (oro), OVX (petróleo), índices de volatilidad FX de CBOE. CME CVOL (desde 2023) cubre 32 productos, incluidos EUR, JPY, GBP, AUD, CAD, CHF, oro, plata y crudo; implícita menos realizada es la prima de riesgo de volatilidad. Risk reversal de 25 delta: correlaciona con el precio, sus extremos avisan de giros; Brunnermeier-Nagel-Pedersen: riesgo de desplome del carry y liquidez de financiación; un RR hacia calls de JPY avisa de deshacer carry, aunque explica poco de la asimetría futura realizada. Yass: la información aparece primero en las opciones.

**Qué significaría aquí.** Una variable de régimen diaria (usada desde la sesión siguiente): estiramiento de la implícita como preparación para plantillas de reversión en índices, tercil de prima de volatilidad al entrar como eje del mapa condicional, condición para familias de ruptura de volatilidad, y un régimen de «riesgo de desplome» para los cruces de yen de la librería. Necesita un segundo feed alineado; el RR no es gratis (Bloomberg, CME) y hay que probarlo contra su gemelo de momentum de precio.

**Estado.** NUEVA (fuente de datos no presente) — **Tipo.** datos — **Locura.** 1 — **Valor.** 4

#### El hueco de datos: no hay CFD de índices en AlgoData
**Fuente.** Comprobación del proyecto (AlgoData/bars: 10 FX, XAU, XAG, BRENT); Katsanos, *Intermarket Trading Strategies*, p. 285-292; Laïdi, *Currency Trading and Intermarket Analysis*, p. 146-147.

**Qué dice.** Katsanos y Laïdi ponen los índices de bolsa en el centro de las relaciones de los cruces de yen y del AUD (S&P-yen r = -0,37 diario en 2006-07; AUDJPY frente al All Ordinaries; cierre de EE UU hacia el yen).

**Qué significaría aquí.** Antes de las pruebas lead-lag de cruces de yen, sincronizar al menos un CFD de índice de EE UU (US500 o NAS100) y uno europeo (GER40) en M1 con el mismo paso de feedQuality. También lo necesitan el cambio de mes, el pre-FOMC, el momentum intradía, la ORB y el fix de fin de mes. Barato y con mucha palanca.

**Estado.** NUEVA — **Tipo.** datos — **Locura.** 0 — **Valor.** 4

#### Volumen de ticks, volumen firmado y desequilibrio de órdenes
**Fuente.** Kirkpatrick y Dahlquist (CMT), p. 414-415; Chan, *Algorithmic Trading*, p. 164-168, 185; Aronson, *Evidence-Based TA*, p. 381-386; web: volumen de ticks como sustituto del real (https://globalprime.medium.com/why-is-tick-volume-important-to-monitor-56a936eea70d ; https://www.elitetrader.com/et/threads/interpreting-dukascopy-tick-data.352792/).

**Qué dice.** El volumen iniciado por compradores menos el iniciado por vendedores tiene gran capacidad predictiva de los retornos siguientes, aunque las reglas de volumen clásicas mostraron poca correlación (Williams, Kaufman-Chaikin). El desequilibrio de tamaños bid/ask y el flujo firmado predicen movimientos a corto; un flujo negativo grande en activos de riesgo es un indicador adelantado de riesgo. El volumen de ticks en FX al contado se parece al volumen real (Marney 2011). Cooper: acciones que caen con volumen decreciente suben la semana siguiente.

**Qué significaría aquí.** Dukascopy M1 trae tick volume, y los ticks traen bid y ask con volúmenes. Rasgos nuevos que SQX no calcula con OHLC: tercil de tick volume al entrar (corte del mapa condicional), bloque «pico de volumen», caída con volumen decreciente, desequilibrio firmado por barra con la regla del tick y su delta acumulado de sesión. Primero como estudio (¿predice el desequilibrio de la barra el retorno siguiente más allá del propio retorno de la barra, frente al mono?), y solo si lo hace, exportarlo como serie extra. Es un solo proveedor; a M30 el efecto del flujo probablemente ya no está.

**Estado.** NUEVA — **Tipo.** datos — **Locura.** 2 — **Valor.** 3

#### Barras de rango igual como otro «marco temporal»
**Fuente.** *New Frontiers in Technical Analysis*, p. 211-215.

**Qué dice.** Construir barras con ticks o M1 cerrando cada una cuando su rango verdadero alcanza un objetivo fijo; las barras quedan homogéneas (variación de rango 0,65% frente a 3,03% en barras de 30 minutos de GOOG), conservan huecos y precios reales. Ejemplo de RSI: señales antes y el doble de ganancia (una anécdota).

**Qué significaría aquí.** Las barras de tiempo de FX y oro llevan la sonrisa de volatilidad del día; las de rango la quitan. Experimento de datos: construir series de rango igual desde Dukascopy M1 e importarlas en SQX como «marco» (SQX importa OHLC arbitrario). Si la misma plantilla rinde más fuera de muestra en barras de rango que en M30/H1, el eje temporal era ruido. Coste: la ejecución en MT5 necesita un constructor de barras en el EA y fills con precios M1 dentro de la barra.

**Estado.** NUEVA — **Tipo.** datos — **Locura.** 2 — **Valor.** 3

#### Datos exógenos: cuanto más difíciles de conseguir, más valen
**Fuente.** Katz y McCormick, p. 4, xix; Schwager, *New Market Wizards* (Weiss), p. 72-73.

**Qué dice.** Además de precios: COT, encuestas de sentimiento, ratios put-call, titulares cuantificados, series económicas, meteorología, manchas solares. «Cuanto más esotérico y difícil de obtener el dato, mayor su valor.» Volumen e interés abierto se publican al día siguiente. Weiss investigaba hasta 150 años atrás donde había datos.

**Qué significaría aquí.** SQX construye solo con OHLC; una familia nueva puede inyectar una serie exógena como indicador personalizado, siempre retrasada a su publicación. Para variables de contexto diarias (edad del tramo, régimen) se pueden usar historias diarias más largas de un segundo proveedor, solo para la variable de contexto.

**Estado.** AMPLÍA (segundo proveedor y calendario aceptados) — **Tipo.** datos — **Locura.** 1 — **Valor.** 3

#### Índice COT, índice de movimiento, triple acuerdo y pseudo-COT de cruces
**Fuente.** Briese, *The Commitments of Traders Bible*, p. 94-112, 158-163, 268-273; *Sentiment in the Forex Market*, p. 97-108.

**Qué dice.** Índice COT = 100 x (neto - mínimo de N) / (máximo de N - mínimo de N), N = 3 años (13 semanas a corto); comerciales ≥ 90% = clímax comprador (alcista), ≤ 5% = clímax vendedor. Índice de movimiento = índice COT menos su valor de hace 6 semanas; ±40 puntos marcan el fin de una reacción, y si no reinicia la tendencia avisa de cambio mayor. En tendencias alcistas las señales de venta de comerciales son prematuras. *Sentiment*: el índice solo dio extremos tempranos o falsos (DXY octubre de 2004 = 0 y el dólar siguió cayendo); actuar solo cuando índice compuesto, % largo de especuladores y % largo de comerciales están los tres en 0 o 100; el interés abierto tiene un ciclo trimestral de vencimientos (usar ratios, no niveles). Pseudo-COT: un índice dólar sumando las posiciones netas invertidas de sus divisas en el IMM; cruces como neto de la divisa base menos neto de la cotizada (EURJPY = COT EUR - COT JPY).

**Qué significaría aquí.** Si se construye un filtro COT, el triple acuerdo es la definición preregistrada (menos grados de libertad que ajustar un umbral), y el pseudo-COT da serie a todos los pares FX del proyecto, cruces de yen incluidos, con datos gratuitos de la CFTC. Máximo dos parámetros (N, umbral), contados en el ledger.

**Estado.** NUEVA — **Tipo.** datos — **Locura.** 1 — **Valor.** 3

#### Rupturas estructurales en los datos alternativos
**Fuente.** Briese, *The Commitments of Traders Bible*, p. 39-44, 72-74, 188-189.

**Qué dice.** En 2006 la CFTC dejó contar como «comerciales» a los dealers de swaps (traders de índices de materias primas); en el mercado alcista del cobre de 2005-06 el índice COT comercial siguió dando compras todo el camino porque «comerciales» estaban comprando. «Cuando un indicador empieza a dar señales raras, desenchúfalo hasta que recupere un patrón fiable.» Los cambios de contrato necesitan ajuste manual. (Del autor de la nota: desde 2009 existen los informes Disaggregated y TFF, historia desde 2006.)

**Qué significaría aquí.** Toda serie externa (COT, sentimiento, VIX) necesita un registro documentado de rupturas estructurales y una regla de seguimiento (tasa de acierto móvil del filtro frente a su banda histórica) antes de poder filtrar una estrategia en vivo.

**Estado.** AMPLÍA (vida media del edge; procedencia de datos) — **Tipo.** datos · proceso — **Locura.** 0 — **Valor.** 3

#### Sentimiento minorista y consenso
**Fuente.** *Sentiment in the Forex Market*, p. 109-112; Schwager, *New Market Wizards* (Eckhardt), p. 51; web: Myfxbook community outlook (https://apify.com/xtracto/myfxbook-community-outlook); IG client sentiment (https://www.ig.com/uk/trading-strategies/_how-to-trade-using-ig-client-sentiment-240912).

**Qué dice.** SSI de FXCM: ratio de posiciones minoristas largas frente a cortas en 7 mayores, dos veces al día; contrario en tendencias (más del 50% largo favorece la debilidad), y el CAMBIO de signo del ratio es mejor señal de giro que su extremo. Web: contrario en extremos > 65% / < 35%, historia raspable pero corta y no gratuita. Eckhardt: la opinión contraria sobre el consenso alcista de boletines no funciona; COMPRAR con consenso extremadamente alcista fue marginalmente rentable (el grupo medido no es representativo).

**Qué significaría aquí.** Sin historia limpia: solo como serie recogida hacia delante («OOS en papel»), quizá desde el propio bróker vía el enlace MT5. Si se prueba, como confirmación de tendencia y asimétrico (solo largos), no como contrario.

**Estado.** NUEVA — **Tipo.** datos · vivo — **Locura.** 2 — **Valor.** 2

#### Noticias y atención mediática: titulares extremos, portadas, GDELT, Google Trends
**Fuente.** *Sentiment in the Forex Market*, p. 44-83; Abraham, *Trend Following Bible*, p. ~176; web: GDELT + FinBERT (https://arxiv.org/pdf/2505.16136); titulares puntuados con LLM (https://arxiv.org/pdf/2504.16063); Preis, Moat y Stanley 2013 (https://www.nature.com/articles/srep01684 ; https://www.nature.com/articles/srep01801).

**Qué dice.** Titulares con palabras extremas marcaron giros a corto (anécdotas: «Yen Surges» del 6 de febrero de 2007 y luego USDJPY +200 pips en 4 días); las portadas de revista marcan extremos de varios meses (Economist «Euroshambles», seis semanas antes del mínimo del EURUSD). Abraham: cuando el Wall Street Journal habla de un mercado, se acaba la operación. Web: el tono diario de GDELT con FinBERT predice EURUSD y USDJPY al día siguiente con un Sharpe declarado de 5,87 (inverosímil, una lección de fuga en sí misma); los titulares puntuados por LLM predicen retornos del día siguiente; las búsquedas de «debt» en Google precedieron movimientos, casi desacreditado fuera de muestra.

**Qué significaría aquí.** Una serie de atención por instrumento (recuento diario de titulares extremos o artículos en GDELT, o Trends para «gold price», «oil price», «yen») como eje del mapa condicional: ¿las operaciones de tendencia en pico de atención tienen peor P&L futuro? Barato a resolución diaria, probablemente redundante con «gran movimiento reciente» (los titulares siguen a los movimientos): siempre contra el mono y contra el gemelo de momentum. Y un caso para el detector de «demasiado bueno».

**Estado.** NUEVA — **Tipo.** datos · estudio — **Locura.** 3 — **Valor.** 2

#### Mercados de predicción como sorpresa frente a probabilidad implícita
**Fuente.** web: Fed 2026 (https://www.federalreserve.gov/econres/feds/files/2026010pap.pdf); CNBC (https://www.cnbc.com/2026/09/14/prediction-markets-efficient-win-lose-beat.html).

**Qué dice.** El error de Kalshi sobre el tipo de fondos federales iguala al de los previsores profesionales a 150 días y su IPC batió al consenso de Bloomberg; distribuciones continuas. Solo un 3% de los traders de Polymarket aporta la precisión; Polymarket adelanta a Kalshi en formación de precios.

**Qué significaría aquí.** La sorpresa frente a la probabilidad implícita del mercado en FOMC o IPC como variable de régimen de evento. Historia corta (2023+).

**Estado.** NUEVA — **Tipo.** datos — **Locura.** 3 — **Valor.** 2

#### Amplitud de mercado para los CFD de índices (con su advertencia)
**Fuente.** Kirkpatrick y Dahlquist (CMT), p. 133-161; Schwager, *New Market Wizards* (Raschke), p. 116-117.

**Qué dice.** Ratio avance/descenso de 10 días > 1,91: 30 señales 1947-2010, +17,9% medio al año siguiente, un fallo; impulso de amplitud de 5 semanas > 1,65: +17,6%. Pero el sistema A/D de un día (100 $ a 884 millones, 1932-2000, sin costes) se hundió tras 2005, el índice de valores sin cambio murió con la decimalización y el impulso de Zweig dejó de disparar tras 1994; la mayoría de señales de amplitud a corto fallaron tras 2000. Raschke compraba con el TICK de la NYSE en un extremo que deja de caer; el 19 de octubre de 1987 el gran descuento de los futuros frente al contado le dio seguridad de una apertura más alta.

**Qué significaría aquí.** Series diarias de amplitud (A/D de NYSE, % de componentes sobre su media de 50/200, nuevos máximos menos mínimos) como régimen externo para CFD de índices, aplicado desde la sesión siguiente; la base (CFD frente a cierre del índice de contado) necesitaría un segundo proveedor. La forma «extremo que deja de caer» se puede expresar con precio (un oscilador que deja de hacer nuevos mínimos n barras). Las historias de colapso son la mejor evidencia de la vida media del edge.

**Estado.** NUEVA (datos) — **Tipo.** datos — **Locura.** 1 — **Valor.** 2

### 4.12 · Higiene de datos para las familias nuevas

#### Series continuas: huecos de roll en Brent y CFD de índices
**Fuente.** Chan, *Algorithmic Trading*, p. 12-16; Schwager, *New Market Wizards* (M. Ritchie), p. 128.

**Qué dice.** Encadenar vencimientos cercanos crea retornos falsos en los días de roll; el ajuste aditivo mantiene bien el P&L pero no los retornos (y puede dar precios negativos); el ajuste por ratio al revés. Los diferenciales necesitan aditivo y las ratios multiplicativo. M. Ritchie desarrolló seis meses sobre una serie «perpetua» interpolada de un proveedor antes de ver que mostraba movimientos y beneficios que ningún contrato real permitía: «nunca volví a fiarme del trabajo de otro».

**Qué significaría aquí.** Brent y los índices de Dukascopy son CFD sobre futuros: comprobar si el M1 trae huecos de roll (y si SQX los cobra como swap o como salto de precio); un hueco de roll en una barra de Brent es un movimiento falso que operan tanto rupturas como reversión. feedQuality debería marcar huecos en fechas de roll conocidas, decir qué ajuste lleva la serie y permitir informar P&L sin las operaciones que cruzan un roll. El CFD del bróker puede hacer el roll de otra manera.

**Estado.** AMPLÍA (feedQuality; contraste con el feed del bróker) — **Tipo.** datos — **Locura.** 0 — **Valor.** 4

#### Anomalías del feed: confirmarlas con el mercado hermano y saber a quién favorecen
**Fuente.** Chan, *Quantitative Trading*, p. 42-43, 117; Chan, *Algorithmic Trading*, p. 83-85; Katz y McCormick, p. 7-9.

**Qué dice.** Calcular retornos con todas las combinaciones OHLC e inspeccionar los días de más de 4 desviaciones: un extremo real coincide con noticias o con un movimiento de todo el mercado; si no, el dato es sospechoso. Una estrategia de reversión compra una cotización baja ficticia y vende en la siguiente correcta, con beneficio falso; los diferenciales amplifican los errores; los errores favorecen a reversión y diferenciales y perjudican al momentum. Katz: rango estandarizado = rango de la barra / rango medio de 20 barras; en S&P limpio la distribución cae suavemente hasta cero hacia 7; valores de 8-10 eran desplomes reales.

**Qué significaría aquí.** Separar choques reales de ticks malos comprobando si un mercado hermano (XAGUSD para XAUUSD, DXY sintético para los mayores) se mueve en la misma barra; aplicar el umbral de rango estandarizado a las barras H1/H4 remuestreadas que opera SQX y a los feeds de crossmarket (donde los huecos de roll parecen desplomes); pesar la atribución de feedQuality de forma asimétrica: P&L de operaciones de reversión entradas a k barras de una anomalía marcada.

**Estado.** AMPLÍA (`studies/data/feedQuality`) — **Tipo.** datos — **Locura.** 0 — **Valor.** 3

#### El precio rancio fabrica persistencia
**Fuente.** Schwager, *New Market Wizards* (Blake), p. 93.

**Qué dice.** Los valores liquidativos de fondos municipales no mostraron casi subidas en tres meses mientras los bonos subyacentes sí tenían días alcistas: algún suavizado del valor liquidativo creaba la persistencia de más del 80%. Le funcionó porque cambiar era gratis y el fondo absorbía el coste, y se fue apagando (del 80% a menos del 70%).

**Qué significaría aquí.** Una autocorrelación de desfase 1 concentrada en horas ilíquidas o de mercado cerrado (índices fuera de horario, pausas del Brent, festivos) es un artefacto de cotizaciones rancias, no un edge, y no se puede ejecutar al precio modelado. Control: autocorrelación de desfase 1 por hora del día; las horas donde se dispara se marcan como horas rancias y las estrategias cuyas entradas se agrupan en ellas llevan aviso.

**Estado.** AMPLÍA (feedQuality) — **Tipo.** datos — **Locura.** 1 — **Valor.** 3

#### Calendario de fechas de cambio estructural del mercado, preregistrado
**Fuente.** Chan, *Quantitative Trading*, p. 91-92, 120; Chan, *Algorithmic Trading*, p. 24-25; Williams, *Long-Term Secrets*, p. 77-78.

**Qué dice.** La decimalización (2001) y la eliminación de la regla del uptick (2007) mataron o inflaron clases enteras de estrategias; son cambios anunciados, sin necesidad de predicción. Los bonos del Tesoro cambiaron cuando llegó la sesión nocturna en 1988; al dejar de publicarse el informe de la Fed del jueves, los viernes cambiaron.

**Qué significaría aquí.** Un pequeño archivo de eventos de estructura FX y CFD (suelo del SNB en 2011 y su retirada en enero de 2015, límites de apalancamiento ESMA en agosto de 2018, eras de tipos negativos, Brexit, marzo de 2020, paso de brókers a spreads raw, cambios del feed de Dukascopy, cambios de horario de sesión de CFD y de hora de servidor). Contrastar la media en fechas PREREGISTRADAS es mucho más potente que el escaneo ciego del CUSUM de profitShape (una prueba, no un barrido) y dice POR QUÉ murió un edge. Y marcar o excluir operaciones en esos días (EURCHF del 15 de enero de 2015 es el fill de manual que ningún bróker respetó).

**Estado.** AMPLÍA (CUSUM de profitShape; calendario económico aceptado) — **Tipo.** datos — **Locura.** 1 — **Valor.** 3

### Las de locura 3 de esta sección
Modelo de análogos · Modelos fundacionales de series temporales (Kronos) · Cascadas de stops de los seguidores de tendencia · Noticias y atención mediática · Mercados de predicción como sorpresa frente a probabilidad implícita.

## 5 · Costes, riesgo, cartera y operación en vivo

Esta sección reúne lo que pasa entre una estrategia que ha sobrevivido al pipeline y el dinero real: lo que cuesta operarla (spread, slippage, swap, rollover, fills), cómo se pone el stop en un sistema construido sin él, qué colas y crisis no ve el backtest, cuánto arriesgar por operación, cómo se combinan estrategias sin que sean la misma apuesta, y cómo se vigila, se incuba y se retira una estrategia en MT5. Casi todo es para el módulo de cartera y el enlace con MT5, que aún no existen, pero bastantes ideas se pueden medir ya con los trades exportados.

Las tres ideas más valiosas: **medir cuánto depende cada superviviente de no tener stop** (el build sin stop puede estar seleccionando estrategias de cola corta, que ganan porque nada las corta), **la correlación entre supervivientes calculada solo en días de estrés** (en calma parecen independientes y en la crisis caen juntas), y **comprobar si las bandas del MC Retest se cumplen** en los segmentos posteriores (si el 99 % se rompe una de cada cinco veces, ningún umbral de riesgo derivado de él vale).

### 5.1 · Lo que cuesta de verdad: spread, slippage, swap y comisión

#### El coste decide antes que la señal: veredicto en unidades de Sharpe
**Fuente.** chan_quantitative, p. 23 y Ej. 3.7 p. 61-65; katz_encyclopedia, p. 86-92; tharp_freedom, p. 243, 275-278; web: Carver, «How fast should we trade» (https://qoppac.blogspot.com/2020/04/how-fast-should-we-trade.html); web: réplica ORB en CFD (https://www.mql5.com/en/blogs/post/776235); web: Krohn-Mueller-Whelan, fixes FX (https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3521370).

**Qué dice.** Una reversión a la media de 5 minutos en ES pasa de Sharpe +3 a -3 con 1 punto básico por operación, y la reversión de Khandani-Lo de 0,25 a -3,19 con 5 pb. Los breakouts de Katz eran rentables con coste cero en todos los lookbacks y perdían IS y OOS con 3 ticks de slippage y 15 $ de comisión. Carver pone un «límite de velocidad»: los costes no deben pasar de un tercio del Sharpe antes de costes. Tharp: si un sistema genera un millón de beneficio neto, probablemente genera más de un millón en costes. El ORB de índices en CFD y el patrón de los fixes FX tienen un edge bruto real del tamaño del spread, y neto cero.

**Qué significaría aquí.** edgeCost ya reconstruye el bruto y lo compara con el coste. Faltan dos números por superviviente: coste/Sharpe bruto (regla de Carver, con el tercio como línea roja) y coste bruto total / beneficio neto (si pasa de 1, un error de 2x en el coste da la vuelta al veredicto). Ambos salen de lo que edgeCost ya calcula.

**Estado.** AMPLÍA (studies/readings/edgeCost) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 4

#### Spread y swap que cambian con los años
**Fuente.** chan_quantitative, p. 24-25; chan_algorithmic, p. 113-122, 139-141.

**Qué dice.** «La mayoría de las estrategias funcionaban mucho mejor hace 10 años, al menos en un backtest»: los spreads eran más anchos entonces y aplicar el coste de hoy a todo el histórico regala rentabilidad a los primeros años. Lo mismo con el swap: el diferencial de tipos de 2008, el de tipos cero y el de 2023 no se parecen, y un swap fijo en 15 años de build valora mal a las estrategias que mantienen posiciones.

**Qué significaría aquí.** RULES.md ya separa spread_is y spread_oos fuera de forex, pero forex lleva un solo spread para todos los años. Dukascopy trae ticks bid y ask: medir el spread mediano real por año y símbolo desde el propio feed, y recostear los trades exportados por año de entrada (o al menos mostrar el P&L por año recosteado). Un edge que solo vive en los primeros años al coste de hoy es probablemente un artefacto de coste. Lo mismo con una serie histórica de swaps.

**Estado.** AMPLÍA (assets spread_is/spread_oos; edgeCost) — **Tipo.** datos — **Locura.** 1 — **Valor.** 4

#### La ventana de rollover: spreads de 5 a 20 veces
**Fuente.** web: fxnx, «Rollover window» (https://fxnx.com/en/blog/rollover-window-when-swap-posts-why-spreads-widen); web: Myfxbook, holding through 5 pm (https://www.myfxbook.com/community/general/holding-trades-through-5-pm/3363989,1); currency_intermarket, p. 146-147.

**Qué dice.** Entre las 16:55 y las 17:15 de Nueva York los spreads se abren un 500-2000 %: los majors llegan a 20 pips y el oro está peor, con swap triple el miércoles. Un backtest de spread fijo llena ahí entradas y salidas a coste normal sin avisar. Laïdi señala además que la hora 21:00-22:00 UTC es la de spreads más anchos del día en los feeds, justo donde vive su efecto «cierre de Wall Street → yen». En cuentas de prop firm, la pérdida flotante que se dispara en el rollover puede romper el límite diario.

**Qué significaría aquí.** Un cálculo en Python sobre los trades exportados, sin SQX: cuántas entradas y salidas de cada superviviente caen en la ventana de rollover, y su P&L recosteado a un spread de rollover. Y una variante «no operar 16:50-17:20 NY» para comparar. Encaja en edgeCost, que ya desglosa por hora.

**Estado.** NUEVA — **Tipo.** estudio — **Locura.** 0 — **Valor.** 4

#### El slippage depende del tipo de orden y de lo concurrido del nivel
**Fuente.** cmt_complete2, p. 535-536, 572, 575; schwager_mw, p. 51 (Dennis), p. 38, 43 (Kovner).

**Qué dice.** Las señales populares de breakout disparan a la vez para muchos traders, así que el slippage es mayor que el modelado. Los stops a favor del movimiento casi nunca se llenan al precio probado y los límites de salida suelen llenar mejor. Dennis: un sistema que pone stops donde hay muchos stops tendrá «deslizamientos por encima de la media» y, si no se ajusta el resultado, «parece estupendo en papel y rinde peor en el mundo real». Kovner: los breakouts violentos que saltan un nivel sin operaciones son los más fiables, «cuanto peores los fills, mejor el trade»; justo los mejores trades son los de fill menos alcanzable.

**Qué significaría aquí.** El MC Retest perturba spread y slippage igual para todos los tipos de orden. Un modelo de coste condicionado: más slippage en entradas stop y stops de salida (mayor en niveles redondos u obvios, aperturas de sesión y noticias), cero o negativo en límites de salida. Medible en M1: el movimiento adverso medio en el primer minuto tras cruzar el nivel frente a un minuto cualquiera. Recostear los mejores trades de breakout con el primer precio operable tras el nivel. Las estrategias de breakout deberían degradarse más que las de reversión.

**⚠ Contradice.** El slippage uniforme del MC Retest (MCR 2 Spread, MCR 3 Slippage) favorece a las estrategias de entrada stop, que son la mayoría de las familias de breakout (cmt_complete2 p. 535-536, 572).

**Estado.** AMPLÍA (MC Retest; edgeCost) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 4

#### Cuánto del beneficio es swap: el carry disfrazado
**Fuente.** katsanos_intermarket, p. 281-282, 289, 299-300; taleb_fooled, p. 93-95; chan_algorithmic, p. 113-122, 139-141.

**Qué dice.** Un diferencial de 1,49 % en USDJPY se convirtió en un COSTE de 665 $ al año en un bróker minorista (largo USD pagado a FF-0,5 %, corto JPY cobrado a Libor+1,5 %). El sistema de yen de Katsanos perdía 2.700 $ en precio y ganaba 20.700 $ de carry. Taleb: las posiciones estables de alto interés (peso mexicano, rublo) dan rentabilidades tranquilas hasta una caída del 40 % donde el peor caso era un 4 %. Chan: en futuros el total es spot más roll, el roll domina en Brent y es la causa principal del momentum de series temporales.

**Qué significaría aquí.** Para cada superviviente que duerme posiciones: separar P&L en movimiento de precio y swap (o roll en Brent e índices), decir si su dirección neta coincide con el lado de carry positivo, y mirar su P&L en los días de deshacer carry del activo (JPY agosto 2024, octubre 2008). Una estrategia cuyo edge es sobre todo carry es una venta de volatilidad encubierta. El estudio structure ya separa movimiento, spread y carry, pero solo para la inversión.

**Estado.** AMPLÍA (structure, edgeCost; swaps por tarea) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 4

#### Un segundo motor que reconcilie los costes trade a trade
**Fuente.** web: «Implementation risk», arXiv 2603.20319 (https://arxiv.org/abs/2603.20319).

**Qué dice.** 15 estrategias en 5 motores de backtest de código abierto coinciden exactamente con coste cero: toda la divergencia viene de cómo se implementan los costes. Encontraron 7 defectos de motor (Backtrader divide la comisión entre 100 sin avisar). Proponen métricas: sensibilidad al motor, intervalo de incertidumbre de implementación, índice de estabilidad de la conclusión.

**Qué significaría aquí.** El issue abierto #26 (la comisión porcentual cobrada una vez o dos) es exactamente esto. El replay en Python de translate, reconciliando los costes de SQX trade por trade, es el arreglo; y el veredicto podría llevar un índice de estabilidad: ¿cambia la conclusión si el coste se implementa de la otra forma?

**Estado.** AMPLÍA (translate; edgeCost ya reconcilia bruto contra SQX) — **Tipo.** proceso — **Locura.** 0 — **Valor.** 4

#### El coste depende de la hora y de cómo se ejecuta
**Fuente.** schwager_nmw, p. 47 (Eckhardt), p. 63-66 (Trout).

**Qué dice.** Trout: en bonos un bróker paciente llena en el bid y el coste real es medio tick; en el S&P el coste suele superar el spread porque la oferta desaparece. Un sistema de bonos con 40 $ de esperanza por lote funciona con 10 $ de comisión y medio tick de slippage, y pierde dinero con 30 $ y un tick. Ahorró un 6 % anual controlando el slippage y otro 6 % bajando comisiones. El volumen tiene forma de U durante el día y las horas flojas son más caras de mover. Eckhardt: comprar en el bid y vender en el ask pudo ser el 100 % de su éxito como corro.

**Qué significaría aquí.** Que edgeCost informe el edge bajo dos ejecuciones, «paciente» (entrada limitada) y «agresiva» (a mercado), y con slippage dependiente de la hora (más caro en horas de poco volumen de ticks). En vivo, una hoja diaria de slippage por mercado: precio de relleno menos precio al enviar la orden.

**Estado.** AMPLÍA (costes por tarea; edgeCost) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 3

#### Inflar la comisión durante el build
**Fuente.** katsanos_intermarket, p. 240.

**Qué dice.** El soporte de NeuroShell recomendaba subir la comisión durante la optimización para que el sistema evitara las operaciones malas, y devolver el exceso después.

**Qué significaría aquí.** Una palanca de generación barata: construir en SQX con el spread por 1,5 o 2 en `build` y hacer el retest a coste real en oos1. Los supervivientes quedarían sesgados hacia más edge por operación, llevando el edge-by-cost al generador. Debe registrarse en el ledger como otra búsqueda (el multiplicador de coste es un parámetro de búsqueda).

**Estado.** NUEVA — **Tipo.** generación — **Locura.** 2 — **Valor.** 3

### 5.2 · Fills y ejecución: lo que el backtest regala

#### Las órdenes límite: el fill por contacto miente
**Fuente.** fitschen_reliable, p. 24-29, 273-276; schwager_nmw, p. 149-151 (Yass); chan_quantitative, p. 42; web: CME 2026, «The limits of limit orders in retail FX/CFD» (https://www.cmegroup.com/articles/2026/the-limits-of-limit-orders-in-retail-fx-cfd-trading.html).

**Qué dice.** En vivo no te llenan los límites que tocan y se dan la vuelta (los ganadores) y siempre te llenan los que siguen de largo (los perdedores). El scalper de 5 minutos de Fitschen, con 15,90 $ por operación en backtest, se llevaría «casi todas las perdedoras y solo la mitad de las ganadoras». Un backtest suyo llenaba 10 de 10 en la apertura frente a 8 de 10 en vivo, y escogía fills al azar donde el vivo se llevaba los peores. Yass: «si quieren hacer esa operación contigo, lo probable es que pierdas». Chan: los máximos y mínimos de la barra vienen de impresiones mínimas o ticks malos, y el error «casi siempre infla» el resultado. La CME describe brókers B-book que sesgan contra los límites.

**Qué significaría aquí.** SQX llena límites y objetivos al tocar. Una prueba de estrés: exigir que el precio atraviese el límite en k ticks (o eliminar la mitad de los fills que solo tocan) y ver si sobrevive; y comparar el P&L de las señales llenadas con el hipotético de las no llenadas. Además, la parte del P&L que viene de entradas o salidas a menos de k puntos del máximo o mínimo de la barra. La tarea MCR 4 MinDist perturba esto en global; esto lo atribuye trade a trade.

**Estado.** AMPLÍA (MCR 4 MinDist; entryQuality) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 4

#### Bid y ask: las compras disparan en el ask, los stops de largos en el bid
**Fuente.** web: MetaTrader 5, testing features (https://www.metatrader5.com/en/terminal/help/algotrading/testing_features); web: Dukascopy strategy tester (https://www.dukascopy.com/wiki/en/manuals/jforex4-desktop/strategy-tester/).

**Qué dice.** En MT5 un buy stop se activa con el Ask y el stop loss de un largo con el Bid. Con barras solo bid y un spread fijo, las entradas stop y las salidas se valoran mal justo cuando el spread se abre (rollover a medianoche, noticias).

**Qué significaría aquí.** Dukascopy tiene también barras ask. Descargar el ask M1 y recalcular los fills de las entradas stop y de los stops de salida de cada superviviente con el lado correcto del libro, comparando con lo que SQX asumió.

**Estado.** NUEVA — **Tipo.** datos — **Locura.** 0 — **Valor.** 4

#### Ambigüedad dentro de la barra: resolverla siempre en contra
**Fuente.** katz_encyclopedia, p. 25-26; williams_longterm, p. 124-125; fitschen_reliable, p. 24-29; web: ruido de microestructura en M1 (https://www.mql5.com/en/articles/22938).

**Qué dice.** Cuando stop y objetivo se tocan en la misma barra, un simulador optimista fabrica «el mejor sistema de la historia» que arruina al que lo opera; conviene un simulador que resuelva la ambigüedad de forma pesimista. Williams no podía modelar el stop del día de entrada y su backtest mostraba un stop más ancho del que operaba. Fitschen: la plataforma supone que se negoció cada precio del rango, y un hueco salta el stop. En M1 hay rebote bid-ask, cotizaciones viejas y errores.

**Qué significaría aquí.** Contar, por estrategia, los trades cuyo resultado cambia entre resolución optimista y pesimista dentro de la barra; muchas de esas y la estrategia es sospechosa. Y repetir los supervivientes con precisión M1 (o tick) para comparar los resultados de la barra de entrada.

**Estado.** AMPLÍA (reconciliación de translate) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 3

#### El momento de ejecución es una variable de primer orden
**Fuente.** chan_quantitative, p. 66 (Ej. 3.8); schwager_nmw, p. 66, 70-71 (Trout).

**Qué dice.** El mismo modelo de reversión actualizado en la apertura en vez del cierre pasó de Sharpe 0,25 a 4,43 bruto, y de -3,19 a 0,78 neto. Trout cree que ejecutar a ciegas (apertura, cierre, horas fijas) le haría ganar «la mitad, quizá menos».

**Qué significaría aquí.** La curva de retraso de entryQuality mide esto para las entradas; falta la curva de retraso de las salidas. Y un «margen de ejecución» por superviviente: el P&L si cada entrada hubiera conseguido el mejor frente al peor precio M1 de la barra de entrada, para ver cuánto del edge depende del fill.

**Estado.** AMPLÍA (entryQuality, retraso) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 3

#### Si el slippage medio es a favor, retrasa la orden
**Fuente.** chan_quantitative, p. 23.

**Qué dice.** El slippage puede tener cualquier signo; si en promedio es una ganancia, retrasa deliberadamente la orden unos segundos.

**Qué significaría aquí.** En vivo: registrar precio de señal frente a precio de relleno por operación; un signo persistente es información. El análogo en backtest es la curva de retraso de entryQuality leída al revés: si entrar una barra tarde mejora, la estrategia debería entrar una barra tarde. Leer el signo de esa curva como decisión de diseño, no solo como fragilidad.

**Estado.** AMPLÍA (entryQuality, retraso) — **Tipo.** vivo — **Locura.** 2 — **Valor.** 2

### 5.3 · Datos del bróker, horario y paridad con MT5

#### Horario de verano y hora del servidor: las barras H4 del bróker no son las de Dukascopy
**Fuente.** web: foro MQL5 sobre DST (https://www.mql5.com/en/forum/443398/page2); web: Elite Trader, DST en backtests (https://www.elitetrader.com/et/threads/handling-dst-transitions-when-backtesting-a-time-based-strategy.385151/); taleb_fooled, p. 26-29, 41-47 (historias alternativas por fase de barra).

**Qué dice.** El histórico de Dukascopy está en UTC; los brókers MT5 suelen usar la hora del servidor GMT+2/+3 (cierre de Nueva York). Londres y Nueva York cambian de hora con 1 a 3 semanas de desfase al año. Las fronteras de las barras H4 y D1 difieren, y una estrategia construida sobre H4 en UTC opera barras distintas en vivo. Las familias por hora del día deben definirse en hora local de la bolsa, no en UTC. La nota de Taleb propone reconstruir las barras con fronteras desplazadas como historia alternativa.

**Qué significaría aquí.** Reconstruir las barras al desfase del bróker (con su DST) desde el M1 y repetir el retest de los supervivientes. Un edge que solo existe con barras alineadas a 00:00 UTC morirá el día que el servidor del bróker tenga otra hora. La prueba general de desplazar fronteras de barra pertenece a la sección de validación; aquí interesa el caso concreto del bróker elegido.

**Estado.** NUEVA — **Tipo.** datos — **Locura.** 1 — **Valor.** 4

#### El roll de los futuros dentro de los CFD de Brent e índices
**Fuente.** chan_algorithmic, p. 12-16; schwager_nmw, p. 128 (Mark Ritchie).

**Qué dice.** Unir contratos frontales crea rentabilidades falsas en las fechas de roll. El ajuste aditivo mantiene bien el P&L y mal las rentabilidades; el multiplicativo al revés. Mark Ritchie pasó seis meses desarrollando sistemas sobre una serie «perpetua» interpolada antes de ver que mostraba movimientos y beneficios que ningún contrato real permitía: «nunca volví a fiarme del trabajo de otro».

**Qué significaría aquí.** Brent y los CFD de índices de Dukascopy son series continuas sintéticas. feedQuality debería detectar saltos en las fechas de vencimiento del futuro subyacente y decir qué ajuste lleva la serie, y cada estudio debería poder dar el P&L quitando los trades que cruzan un roll. Un hueco de roll es un movimiento falso que los breakouts y las reversiones «operan». El CFD del bróker puede además rolar distinto que Dukascopy.

**Estado.** AMPLÍA (feedQuality; contraste con el feed del bróker, aceptado) — **Tipo.** datos — **Locura.** 0 — **Valor.** 4

#### Paridad de indicadores y de trades entre SQX, Python y MT5
**Fuente.** katz_encyclopedia, p. 139-140; chan_algorithmic, p. 4, 30; tharp_freedom, p. 316-317; web: QuantConnect, reconciliation (https://www.quantconnect.com/docs/v2/cloud-platform/live-trading/reconciliation).

**Qué dice.** TradeStation calculaba el Slow %K como EMA del Fast %K en vez de la media de 3 barras, y las funciones anidadas devolvían valores erróneos sin avisar. Chan: si backtest y vivo son el mismo programa y solo cambia el feed, el look-ahead es imposible. Tharp: un breakout trivial ejecutado en tiempo real y luego rehecho sobre los MISMOS datos dio resultados distintos. QuantConnect superpone la curva viva sobre el backtest del mismo periodo con el mismo código.

**Qué significaría aquí.** SQX exporta MQL5 y su motor es Java: no son el mismo programa. Antes del vivo: (1) una prueba de paridad por indicador (Stochastic, RSI de Wilder o SMA, ATR, Keltner) entre SQX, Python y MT5 sobre las mismas barras, que localiza el fallo más barato que reconciliar trades; (2) correr el EA exportado en el Strategy Tester de MT5 sobre las mismas barras y comparar trade a trade con SQX; (3) ya en vivo, reproducir cada semana los últimos días de barras vivas en el backtest y comparar con los fills.

**Estado.** AMPLÍA (translate reconcilia Python con SQX; falta MQL5) — **Tipo.** vivo — **Locura.** 0 — **Valor.** 4

#### Dos brókers en paralelo para medir la ejecución real
**Fuente.** chan_quantitative, p. 72-74, 77; web: CME 2026 limit orders (https://www.cmegroup.com/articles/2026/the-limits-of-limit-orders-in-retail-fx-cfd-trading.html); web: transparencia de ejecución (https://bjftradinggroup.com/broker-execution-transparency/); schwager_nmw, p. 95-97 (Blake).

**Qué dice.** La comisión es una parte pequeña del coste; la calidad de ejecución puede ganar a un bróker más barato por más que la diferencia de comisión, y eso solo se aprende operando la misma estrategia en varias cuentas a la vez. Una ejecución justa muestra slippage SIMÉTRICO; los B-book sesgan contra límites y hacia stops. Blake vio cómo la contraparte le cerraba el edge (límite de 500.000 $ a 100.000 $ dos días después de un artículo, luego una comisión de 0,75 %).

**Qué significaría aquí.** Con el enlace MT5: el mismo EA en dos cuentas demo o reales, registrando fill contra señal, spread al relleno y swap. Alimenta assets/ con el slippage real y sustituye el provisional «slippage = medio spread». Un test de signos sobre (fill − cotización) por bróker da un número duro para elegir bróker, y la asimetría creciente es aviso temprano de que el bróker restringe una estrategia rentable.

**Estado.** AMPLÍA (contraste con el feed del bróker, aceptado; añade la ejecución) — **Tipo.** vivo — **Locura.** 0 — **Valor.** 3

#### Backtestear sobre el feed del sitio donde operas
**Fuente.** chan_algorithmic, p. 10-11, 83-85; katsanos_intermarket, p. 281; tharp_freedom, p. 25-27.

**Qué dice.** El FX está fragmentado y los spreads difieren entre plataformas; los proveedores no coinciden en máximos, mínimos ni cierres diarios («usa el mismo proveedor que tu bróker o el vivo será distinto»). El feed del bróker de Chan disparaba operaciones de pares perdedoras que desaparecieron al cambiar a un feed de terceros.

**Qué significaría aquí.** Apoyo al contraste con el feed del bróker ya aceptado. En vivo, correr la lógica de señal del EA sobre dos feeds (bróker y Dukascopy) y alertar cuando discrepen.

**Estado.** YA EXISTE (contraste con el feed del bróker y segundo proveedor, aceptados) — **Tipo.** datos — **Locura.** 0 — **Valor.** 2

### 5.4 · El stop: construir sin él y ponerlo después

#### Medir cuánto depende cada superviviente de no tener stop
**Fuente.** lowenstein_ltcm, p. 3-10, 21; elder_newtfal, p. 202, 219; taleb_fooled, p. 73, 110; covel_trendfollowing, p. 262-263; abraham_tfbible, p. 84; schwager_mw, p. 81 (Seykota); schwager_nmw, p. 50, 175; schwager_smw, p. 97-98 (Minervini).

**Qué dice.** El credo de Meriwether era «aguanta las pérdidas hasta que se vuelvan ganancias»; Hilibrand dobló una operación hipotecaria perdedora de 400 millones. Las operaciones de convergencia que se aguantan contra el movimiento aciertan casi siempre, y la vez que no, el que las aguanta ya no está cuando convergen. Seykota: los tres elementos del buen trading son cortar pérdidas, cortar pérdidas y cortar pérdidas. Minervini descubrió que un tope de pérdida del 10 % le habría subido el beneficio un 70 % quitando pocos ganadores, porque los ganadores funcionaban desde el principio. Todos los libros de esta familia tratan el stop como parte del sistema.

**Qué significaría aquí.** El proyecto construye sin stop a propósito y lee el stop del MAE en el paso 24 (sin optimizar, postura respetada). El riesgo es de selección: una búsqueda genética puntuada sin stop premia estrategias cuyo edge es aguantar la excursión adversa hasta que vuelve (reversión sin stop, el patrón de LTCM). Medida mínima, desde el paso 8: la parte del beneficio que viene de trades cuyo MAE pasó de X ATR (los que un stop sensato habría cortado). Si es grande, el edge del superviviente ES la ausencia de stop: se etiqueta de cola corta y la versión con stop es la que hay que validar.

**⚠ Contradice.** El build sin stop (lowenstein_ltcm p. 3-10; elder_newtfal p. 202, 219; schwager_mw p. 81): la versión con stop añadida después no es el objeto que pasó los pasos 8 a 23.

**Estado.** AMPLÍA (atrCalculator; entryQuality MFE/MAE) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 5

#### Volver a pasar el filtro con el stop puesto, y dar el mismo stop al mono
**Fuente.** williams_longterm, p. 240-243; cmt_complete2, p. 553 (Box 22.2).

**Qué dice.** Mismas entradas de day trading en el S&P: stop de 500 $ → -41.750 $ y 26 % de aciertos; 1.500 $ → +116.880 $ y 56 %; 5.000-6.000 $ → +269.525 $ y 70 %, pero pérdida máxima de 5.920 $ frente a 2.045 $. En el ejemplo de la CMT, añadir stops llevó la rentabilidad de 276 % a 6.024 % («tan grande que probablemente no es fiable»). El stop puede crear o destruir un sistema.

**Qué significaría aquí.** Tras leer el stop del MAE, la versión con stop debe pasar al menos los filtros baratos y la comparación con el mono, con el mismo stop aplicado a las entradas aleatorias, y medirse en R porque el ancho del stop cambia el tamaño. Un stop que corta la cola derecha de ganadores que se recuperan puede destruir el edge sin que nadie lo vea. Marcar los supervivientes cuyo veredicto cambia.

**⚠ Contradice.** Williams p. 228 dice lo contrario para sistemas siempre dentro (el stop nunca ayudó), lo que apoya el build sin stop. Juntas, las dos observaciones dicen que el efecto del stop depende de la estrategia y hay que medirlo, no suponerlo.

**Estado.** AMPLÍA (atrCalculator, paso 24) — **Tipo.** proceso — **Locura.** 0 — **Valor.** 4

#### Para las estrategias de reversión: stop más allá del peor MAE, que nunca salte en el histórico
**Fuente.** chan_quantitative, p. 106-107, 142-143, 156; chan_algorithmic, p. 182-184.

**Qué dice.** En una catástrofe el stop se llena en el hueco y realiza la pérdida en vez de evitarla. Un modelo de reversión, si se vuelve a evaluar sobre una posición perdedora, da la MISMA señal: nunca recomienda un stop, y un stop ahí «suele significar salir en el peor momento». «Nunca he backtestado una estrategia de reversión cuya APR o Sharpe mejorara con un stop», pero eso es sesgo de supervivencia: las que se volvieron tendencia no están en el catálogo. Solución: un stop «mayor que la máxima excursión intradía del backtest», que no altera ningún trade histórico y evita la ruina si el régimen cambia. Para momentum, la propia señal contraria es el stop natural.

**Qué significaría aquí.** atrCalculator lee X de los percentiles 80-95 del MAE de los ganadores IS, que por construcción corta entre un 5 y un 20 % de los ganadores. Añadir una columna: más allá del MAE MÁXIMO IS de todos los trades (corta cero trades IS), y etiquetar cada estrategia como de reversión o de momentum. El informe diría qué regla usó y cuántos trades IS habría cortado (cero para la regla de reversión).

**⚠ Contradice.** Aplicar la misma regla de percentil a todos los tipos de estrategia (chan_quantitative p. 106-107, 142-143; chan_algorithmic p. 183-184).

**Estado.** AMPLÍA (studies/closing/atrCalculator) — **Tipo.** riesgo — **Locura.** 0 — **Valor.** 4

#### Las entradas de giro necesitan stops ajustados: el build sin stop puede infravalorarlas
**Fuente.** katz_encyclopedia, p. 201, 211-212.

**Qué dice.** Los modelos lunares, estacionales y de ciclos «aciertan los giros solo un porcentaje de las veces»: cuando aciertan, el mercado se mueve enseguida casi sin excursión adversa; cuando fallan, la pérdida es grande. «Funcionan mejor con stops muy ajustados»; el stop holgado de 1 ATR dejaba sangrar los fallos.

**Qué significaría aquí.** Una familia cuyos ganadores tienen el MAE concentrado cerca de cero (distribución bimodal a nivel de familia) es candidata a una variante con stop ajustado aunque el build sin stop salga mediocre. entryQuality es el sitio para detectarlo. Fitschen (p. 69-72) apoya al proyecto para sistemas de tendencia.

**⚠ Contradice.** El build sin stop puede sesgar el ledger contra toda la clase de familias de contratendencia y giro (katz_encyclopedia p. 201, 211-212).

**Estado.** AMPLÍA (entryQuality; atrCalculator) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 4

#### Stop catastrófico en el servidor del bróker, siempre
**Fuente.** elder_newtfal, p. 224-225; katz_encyclopedia, p. 285-289; faith_turtle, p. 262-263.

**Qué dice.** Los stops mentales fallan: el stop blando de 2.000 $ de un amigo de Elder acabó en una pérdida de 40.000 $. Cada operación lleva una orden dura GTC en un nivel «donde de ningún modo esperas que llegue el precio». Katz: el stop real en el ordenador y uno catastrófico lejano en el bróker, para evitar la caza de stops. Los Turtles nunca dejaban stops en el bróker.

**Qué significaría aquí.** En el EA de MT5: además de la lógica de salida, un SL duro en el servidor a distancia catastrófica (por ejemplo el stop del MAE por 2, o la peor excursión adversa histórica), para que una caída del EA, del VPS, una desconexión o un bróker congelado no conviertan una pérdida normal en ruinosa. El backtest debería incluir ese stop lejano para conocer su coste (raro).

**Estado.** NUEVA (el paso 24 lee un stop normal, no uno catastrófico) — **Tipo.** vivo — **Locura.** 0 — **Valor.** 4

#### Presupuesto roto: trades que pierden más que el stop por huecos
**Fuente.** covel_trendfollowing, Apéndice A p. 315-317.

**Qué dice.** Con los trades normalizados por el riesgo inicial (R), un 2 % perdió más que el stop presupuestado por huecos nocturnos; la proporción por año fue de 0 a 5,8 % (pico en 1987). Los atípicos positivos (más de 1R) fueron del 0 al 72 % por año: el edge llega a rachas.

**Qué significaría aquí.** Con el stop leído del MAE, contar por año cuántos trades habrían salido más allá del stop (hueco del domingo, noticias) y por cuántos R. Oro, Brent e índices abren con hueco el domingo. Es la cola real de una estrategia MT5 con stop, invisible en un build sin SL. Informar «peor pérdida en R» y «% de trades con pérdida mayor de 1,5R».

**Estado.** AMPLÍA (atrCalculator) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 4

#### Distancia del stop desde la dispersión del rango, y la escalera condicional de excursión
**Fuente.** newfrontiers_ta, p. 166-176 (Kase DevStops).

**Qué dice.** Los múltiplos de ATR ignoran la variabilidad de los rangos: dos mercados con el mismo ATR y distinta dispersión necesitan stops distintos. DevStop = media del rango verdadero de dos barras más 1, 2,2 o 3,6 desviaciones (corrección por asimetría). Tabla empírica sobre 150.000 barras: si se toca la línea de aviso, P(tocar Dev1) ≈ 80 % y P(tocar Dev3) ≈ 45 %; P(Dev2 | Dev1) ≈ 80 %. El riesgo crece con la raíz del tiempo.

**Qué significaría aquí.** Para el paso 24: la distancia del stop desde los cuantiles de la excursión adversa, no desde su media. Y un diagnóstico barato: P(el MAE llega al nivel j | llegó al i) para los trades de la estrategia frente a los del mono; si la continuación condicional es menor que la del mono, las entradas tienen apoyo real. La raíz del tiempo sirve para comprobar crossTF al reescalar stops.

**Estado.** AMPLÍA (atrCalculator; entryQuality) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 4

#### Tocar o cerrar: la semántica del stop debe ser la misma en backtest y en vivo
**Fuente.** abraham_tfbible, p. 26-27; fitschen_reliable, p. 69-72, 76-79.

**Qué dice.** El plan debe decir de antemano si tocar el stop ATR cierra o hace falta un cierre más allá: tocar se revierte a menudo, cerrar puede agrandar la pérdida. Fitschen: para contratendencia en acciones, disparar con el cierre y salir en la apertura siguiente ganó al stop intradía; para tendencia en commodities, solo un stop de 3 desviaciones de 20 cierres mejoró el gain-to-pain. Los stops dejados de noche en sesiones ilíquidas reciben fills «raros».

**Qué significaría aquí.** Calcular el stop del MAE con las dos semánticas (toque intradía en bid/ask frente a cierre más allá y salida en la apertura siguiente) y hacer que la elegida coincida con lo que hará el EA. El MAE medido en máximos y mínimos M1 implica semántica de toque. Relevante por los spreads nocturnos de FX y oro.

**Estado.** AMPLÍA (atrCalculator) — **Tipo.** riesgo — **Locura.** 0 — **Valor.** 3

#### No poner el stop donde lo pone todo el mundo
**Fuente.** schwager_nmw, p. 63 (Trout); elder_newtfal, p. 220-221; schwager_smw, p. 123-124 (Bender).

**Qué dice.** La gente pone los stops justo encima del máximo de ayer y debajo del mínimo; los locales van a por ellos. Consejo: nunca en sitios obvios, 10 ticks dentro o 10 fuera. Elder: los stops de la masa se agrupan bajo mínimos obvios y números redondos (77,94 $, no 78 $). Bender: en 1993 los stops de los CTA, función de la volatilidad, estaban donde él calculó; el oro bajó a 390 $ y enseguida a 350 $ mientras cada stop disparaba el siguiente.

**Qué significaría aquí.** Comprobar si el stop del paso 24 cae sistemáticamente cerca del máximo o mínimo del día anterior o de un número redondo. Y un test en M1: tasa de toque y posterior reversión de stops hipotéticos justo en mínimos de swing o números redondos frente a la misma distancia desplazada una fracción de ATR. Si los niveles obvios se barren más de lo normal, desplazar el stop (regla fija, no optimización). Un stop en múltiplo de ATR está donde están todos los demás stops en ATR.

**Estado.** NUEVA — **Tipo.** estudio — **Locura.** 2 — **Valor.** 3

#### Salida por un día de volatilidad adversa, sin buscar parámetros
**Fuente.** tharp_freedom, p. 261-262, 265.

**Qué dice.** Un movimiento de un solo día de 2 veces la volatilidad diaria media contra la posición es una de las mejores salidas (y buena entrada inversa). Flota por encima de un trailing de 3 ATR; tras 4R de beneficio el trailing se estrecha a 1,6 ATR. Diseñado desde los objetivos, «sin pruebas».

**Qué significaría aquí.** Un estudio de solo lectura para supervivientes sin stop: qué fracción de las grandes perdedoras tuvo pronto una barra adversa de 2 ATR, y qué fracción de las ganadoras. Si la proporción es muy desigual, es candidata a salida catastrófica sin búsqueda de parámetros.

**Estado.** NUEVA — **Tipo.** estudio — **Locura.** 1 — **Valor.** 3

#### Medir el stop implícito antes de añadir uno
**Fuente.** faith_turtle, p. 262-263.

**Qué dice.** Los sistemas de cruce de medias sin stop «tienen un stop implícito»: el cruce limita la pérdida.

**Qué significaría aquí.** Antes de leer el stop del MAE, medir el stop que la lógica de salida ya da (distribución de la peor pérdida por trade en ATR). Si está acotada, un stop duro quizá solo añada coste.

**Estado.** AMPLÍA (atrCalculator) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 2

#### Apoyo de los libros a construir sin stop (y dónde discrepan)
**Fuente.** katsanos_intermarket, p. 183-184, 215, 294; faith_turtle, p. 140-147; williams_longterm, p. 79-80, 198, 228-229; katz_encyclopedia, p. 309-313; fitschen_reliable, p. 69-72.

**Qué dice.** El estudio MTA de William Chan: «correlación negativa significativa entre el valor añadido por los stops y la rentabilidad de la estrategia; los stops perjudicaban a las rentables y mejoraban a las no rentables». Faith: con una entrada con edge y salida por tiempo, añadir stops de cualquier ancho empeoró todas las métricas en tres sistemas. Williams: en sistemas siempre dentro, el stop recorta un 10-15 % los aciertos y hasta un tercio el beneficio por trade; la mayoría de sus suscriptores perdía por stops demasiado cerca. Katz: con entradas aleatorias la superficie stop/objetivo es suave, con óptimo en 1-2 ATR (mejor 1,5) y poca interacción. Discrepan: en el sistema intradía de e-mini de Katsanos un stop de 1,6 ATR(8) subió el beneficio de 50,7k a 59,2k $ y un trailing de Bollinger recortó los drawdowns del sistema de yen; Harriman vio pérdidas grandes 50 veces más frecuentes que ganancias grandes en cuentas de bróker.

**Qué significaría aquí.** Apoyo a no optimizar el stop y a leerlo del MAE: la superficie es tan plana que un stop leído cerca de 1,5-2 ATR pierde poco frente al óptimo. También aviso contra cualquier filtro que premie el porcentaje de aciertos.

**Estado.** YA EXISTE (build sin stop; atrCalculator) — **Tipo.** riesgo — **Locura.** 0 — **Valor.** 2

### 5.5 · Colas, crisis y escenarios de estrés

#### Comprobar si las bandas del MC Retest se cumplen después
**Fuente.** lowenstein_ltcm, p. 63-65, 124-130, 228-229.

**Qué dice.** La carta de riesgo de Merton y Scholes decía que «solo un año de cada cincuenta perdería al menos un 20 %»; perdió entre un 77 y un 90 % en meses. Pérdida diaria «esperada» de 34-45 millones. Fama: un movimiento de 5 sigmas debería darse una vez cada 7.000 años. El epílogo: «una tormenta perfecta que llega una vez cada cien años», que había ocurrido muchas veces. Nadie contrastó las probabilidades de cola con las frecuencias reales; tras las pérdidas «revisaron todos sus modelos y concluyeron que junio fue una aberración esperada».

**Qué significaría aquí.** Sobre toda la población que pasó el MC Retest de SQX y luego se observó en un segmento fresco (oos2 en el WFM, o el paper OOS), contar cuántas veces el drawdown máximo, el peor mes o la peor racha real superaron el percentil 95 y 99 del MC. Si está calibrado, romperán en torno al 5 % y al 1 %. Una tasa del 20 % significa que las perturbaciones (spread, slippage, parámetros) subestiman las colas, y cada expectativa y umbral de retirada derivado del MC debe ensancharse por el factor medido. Un test de excedencias tipo Kupiec sobre las propias previsiones de riesgo del pipeline, una vez por trimestre.

**Estado.** NUEVA (mcRetest existe; sus previsiones no se contrastan con datos posteriores) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 5

#### Convexidad: ¿la estrategia es una opción comprada o vendida?
**Fuente.** covel_trendfollowing, p. xv, 20, 102-104, 143, 305; faith_turtle, p. 101-104; covel_completeturtle, p. 164-165, 192-193; tharp_freedom, p. 142-143, 273, 278-279; schwager_nmw, p. 54, 56 (Eckhardt), p. 151-152 (Yass); chan_algorithmic, p. 60-61, 151-154.

**Qué dice.** La tendencia es una opción larga: el stop limita la pérdida, la tendencia deja abierta la ganancia, y la prima se paga como una serie de pequeñas pérdidas. La reversión «funciona casi siempre, y luego para y te quedas sin negocio» (Parker), «fuera del negocio cada ocho años». Un sistema con 90 % de aciertos, ganancia media de 275 $ y pérdida media de 2.700 $ tiene esperanza negativa. Faith: «creo que hay una relación inversa entre la suavidad de las rentabilidades y el riesgo real»; LTCM y Amaranth eran suaves. Con drawdown diario en vez de a fin de mes, el MAR pasó de 1,22 a 0,99. Meaden: desviación típica mensual de los seguidores de tendencia 12,51 frente a semidesviación 5,79; el Sharpe castiga la volatilidad al alza. Eckhardt: el mercado «te acuna con técnicas de alto porcentaje de acierto que suelen perder de forma desastrosa».

**Qué significaría aquí.** Etiquetar cada superviviente como convexidad larga o corta con datos, no con el nombre de la plantilla: asimetría de R por trade y de los meses, ganancia media/pérdida media frente al porcentaje de acierto, cociente desviación/semidesviación, y un gráfico de la rentabilidad mensual de la estrategia frente a la del subyacente (sonrisa = opción larga, ceño = opción corta). Un aviso en el gate: acierto mayor del 65 % y peor pérdida mayor de 5 veces la ganancia mediana manda la estrategia primero a la prueba de shock. Calcular el drawdown en equity diaria o por barra, nunca a fin de mes. Informar la cola izquierda por lado (largos y cortos) sin mezclar.

**⚠ Contradice.** Si la fitness de SQX o algún filtro del gate premia la suavidad (R², Sharpe, estabilidad), la búsqueda favorece los perfiles de asimetría negativa cuyo riesgo no se ve en la muestra (faith_turtle p. 101-104; covel_trendfollowing p. 102-104).

**Estado.** AMPLÍA (profitShape mide concentración de ganancias, no la cola izquierda ni la convexidad) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 5

#### Inyectar los peores días de la historia del activo
**Fuente.** covel_trendfollowing, p. 153-155, 180; tharp_freedom, p. 79; faith_turtle, p. 86-96, 118-121; schwager_nmw, p. 110-112 (Basso); chan_quantitative, p. 91-92, 120; web: BIS sobre el deshacer del carry del yen, agosto 2024 (https://www.bis.org/publ/qtrpdf/r_qt2409a.htm).

**Qué dice.** «Vivimos siete inundaciones de las de cada cien años»; el VaR mide volatilidad, no riesgo. El hueco nocturno de octubre de 1987 produjo un drawdown del 65 % en un sistema cuyo máximo en backtest era la mitad: «el test histórico habría subestimado el drawdown por un factor de 2»; Faith perdió 11 de 20 millones en una noche. Método: reproducir los peores días de choque de los últimos 30-50 años contra las posiciones probables y dimensionar para que el peor quede por debajo del 50 %. Tharp: imaginar un choque de 1-2 días contra ti, el peso roto, perder las comunicaciones. Basso ensayaba escenarios de película. El EURCHF del 15 de enero de 2015 es un fill que ningún bróker respetó. El 5 de agosto de 2024 el Nikkei cayó un 12,4 %.

**Qué significaría aquí.** Una prueba de estrés por superviviente: aplicar los huecos históricos del activo (SNB 2015, Brexit, marzo 2020, 2008, agosto 2024) a sus posiciones abiertas en esas fechas Y en fechas aleatorias, más un hueco sintético de 5, 10 y 20 ATR con posición abierta, e informar el golpe en R y si sobrevive. Con un build sin stop la cola de hueco no se mide en ningún otro sitio: el MC Retest perturba spread, slippage y parámetros, no huecos. Excluir o marcar los trades de días de fills imposibles.

**⚠ Contradice.** Los drawdowns del backtest están subestimados unas 2 veces por los choques de precio (faith_turtle p. 92-95, 111; tharp_freedom p. 32); cualquier filtro por drawdown o dimensionado posterior hereda ese sesgo.

**Estado.** NUEVA (el MC Retest no perturba huecos) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 4

#### Etiqueta de cobertura de crisis en cada veredicto
**Fuente.** taleb_fooled, p. 49, 55-56, 93; lowenstein_ltcm, p. 138, 233; web: BIS agosto 2024 (https://www.bis.org/publ/bisbull90.pdf).

**Qué dice.** Preferir al trader expuesto más tiempo al suceso raro (y que ha sobrevivido) antes que al más rentable; los ganadores de un corte transversal son los mejor adaptados al último ciclo; las divisas más estables son las más propensas a romper. «Ninguna inversión puede juzgarse con medio ciclo»: los beneficios de LTCM fueron en parte prestados contra el día en que el ciclo girase, y sus modelos «no llegaban tan atrás».

**Qué significaría aquí.** Una lista por activo de episodios de estrés con nombre (2008, flash crash 2010, techo del oro 2011, taper 2013, SNB enero 2015, CNY agosto 2015, Brexit y flash del GBP 2016, marzo 2020, WTI negativo abril 2020, gilts 2022, yen agosto 2024). Cada estudio muestra cuáles caen en build, oos1 y oos2 y cómo le fue a la estrategia en cada uno. Si sus ventanas no contienen ninguno: «no probada en crisis», sean cuales sean sus p-valores. Si solo contienen un régimen del activo: «medio ciclo». Para las de convexidad corta, sus ventanas deben incluir al menos un episodio del riesgo que venden. Barato: un YAML de fechas y una intersección.

**Estado.** NUEVA — **Tipo.** estudio — **Locura.** 0 — **Valor.** 4

#### P&L en los meses extremos del mercado
**Fuente.** covel_trendfollowing, p. xix-xx, 13.

**Qué dice.** En octubre de 2008 los seguidores de tendencia ganaron entre un 5 y un 40 % mientras el mundo perdía; su valor se concentra en los meses extremos («crisis alpha»).

**Qué significaría aquí.** En el mapa condicional, una variable nueva: el decil de rentabilidad mensual (o de movimiento absoluto) del instrumento y de un proxy de riesgo como el US500. P&L en las colas frente al cuerpo. Para una estrategia sola dice si su edge es «volatilidad larga» (gana en choques) o «volatilidad corta» (gana en calma y muere en choques); para la cartera, es la propiedad de diversificación clave.

**Estado.** AMPLÍA (conditionalMap tiene terciles de volatilidad, tendencia y día, no meses de cola) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 4

#### Regla de tres: la cola que la muestra no puede descartar
**Fuente.** taleb_fooled, p. 96-97.

**Qué dice.** Con una probabilidad pequeña de bola roja, lo que sabemos de su ausencia crece mucho más despacio que la raíz de n; una bola roja lo cambia todo. «El mercado nunca cayó un 20 % en 3 meses» se puede refutar, nunca verificar con datos.

**Qué significaría aquí.** Para cada superviviente, con N trades independientes (o N meses) y ninguna pérdida mayor de k R, el límite superior al 95 % de P(pérdida > k R) es aproximadamente 3/N. Informarlo como «puede perder más de 5R en hasta 1 de cada N/3 trades y los datos no lo descartan», y multiplicado por una pérdida plausible da una «esperanza de cola no vista» que restar a la observada. Las estrategias que parecen seguras solo porque N es pequeño quedan penalizadas a la vista.

**Estado.** NUEVA — **Tipo.** estudio — **Locura.** 1 — **Valor.** 4

#### Huecos de fin de semana: el riesgo del viernes
**Fuente.** schwager_mw, p. 48 (Dennis); web: MQL5, huecos del oro (https://www.mql5.com/en/articles/23609); web: EarnForex, estadística de huecos semanales (https://www.earnforex.com/guides/forex-weekly-gap-statistics/); web: Aioka, riesgo de hueco del oro (https://www.aioka.io/blog/gold-trading-strategy-weekend-gap-risk).

**Qué dice.** Todos los granos cerraron un viernes en máximos anuales; Dennis compró al cierre y el lunes abrió al límite. «Como mínimo, no tener un corto con pérdida el viernes si el mercado cierra en máximos, ni un largo si cierra en mínimos.» En XAUUSD, huecos de 5 $ o más en un 35 % de las semanas y de 10 $ o más en un 18 % (últimos 3 años).

**Qué significaría aquí.** Por superviviente: la parte de su P&L y de sus peores trades que viene de posiciones que pasan el fin de semana, el P&L cuando el cierre del viernes está en el extremo adverso frente al resto, y una variante «plano el viernes» para comparar. El riesgo de hueco es real en oro, índices y Brent.

**Estado.** NUEVA — **Tipo.** estudio — **Locura.** 1 — **Valor.** 4

#### Plano antes de eventos binarios y ventanas de noticias
**Fuente.** schwager_nmw, p. 103 (Sperandeo); schwager_mw, p. 64 (Jones); sentiment_fx, p. 24-44; aronson_ebta, p. 376-377; web: Benzinga, sistemas y noticias (https://www.benzinga.com/Opinion/26/06/53097073/trading-systems-and-market-news-how-to-handle-cpi-fomc-and-unexpected-events); web: reglas de noticias de prop firms (https://www.tradingplace.us/prop-firm-guide/news-and-overnight-rules/).

**Qué dice.** Sperandeo: «ante una propuesta fiscal u otra gran incertidumbre legislativa, ahora me pongo plano de inmediato». Jones: no arriesgar mucho antes de informes clave, «eso es jugar, no operar». Los datos macro no dan dirección fiable (las sorpresas de NFP de más de 2 sigmas movieron el dólar a favor 3 veces y en contra 4), pero sí disparan volatilidad. Las prop firms prohíben operar en ventanas de noticias (T1 ±30 min, CPI ±15 min). Lo importante es si el SISTEMA se validó en esas condiciones, no una regla general. Un edge concentrado en publicaciones sin pretenderlo es una apuesta de volatilidad con riesgo de slippage.

**Qué significaría aquí.** Con el calendario económico aceptado: partir los trades de cada superviviente dentro y fuera de ventanas de noticias, y probar un único overlay preregistrado «plano antes de un evento de alto impacto» (P&L y peor caso con y sin aguantar el evento). En la cartera fondeada, la regla de noticias de la prop firm es una restricción.

**Estado.** AMPLÍA (calendario económico, aceptado) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 3

#### Índice de cola: cuándo el drawdown de la muestra no significa nada
**Fuente.** tharp_freedom, p. 32; schwager_nmw, p. 47-48 (Eckhardt), p. 62 (Trout), p. 136, 143 (J. Ritchie, Hull).

**Qué dice.** Las distribuciones de precios tienen varianza casi infinita: la varianza muestral crece al añadir datos y toda estimación de riesgo con muestra finita queda corta. «Cualquier estimación clásica del riesgo estará significativamente subestimada.» Un Monte Carlo que remuestrea rentabilidades empíricas no puede generar una cola mayor que la peor de la muestra.

**Qué significaría aquí.** Añadir a profitShape un estimador de índice de cola (Hill) sobre R por trade y P&L diario, y el drawdown en función de la longitud de la submuestra (1, 2, 5 años) para enseñar cómo crece. Marcar las estrategias cuyo peor trade en oos1 supera con mucho el máximo del build. Si el índice es menor que 2, la maquinaria basada en Sharpe no es formalmente válida y el dimensionado posterior debe usar riesgo consciente de colas, no sigma.

**Estado.** AMPLÍA (profitShape) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 3

### 5.6 · Drawdown y expectativas realistas

#### El descuento propio: cuánto se pierde del build al OOS y del OOS al vivo
**Fuente.** cmt_complete2, p. 531, 550; chan_algorithmic, p. 7; web: McLean-Pontiff (https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2156623).

**Qué dice.** Espera en vivo más o menos la mitad del beneficio probado y el doble del drawdown, y usa el doble del MDD optimizado para dimensionar (Hill, Pruitt y Hill 2000). Chan: «la mayoría estaría contenta con un Sharpe en vivo mejor que la mitad del de su backtest». McLean y Pontiff: las anomalías rinden un 26 % menos fuera de muestra y un 58 % menos tras publicarse, así que lo esperable en vivo es el backtest por 0,4-0,75.

**Qué significaría aquí.** Sustituir la regla popular por el número del proyecto: del ledger, la distribución de (métrica oos1 / métrica build) de todas las estrategias que pasaron los filtros del build, por familia, activo y timeframe. Cada informe nuevo muestra la métrica del build ya multiplicada por ese descuento calibrado y su dispersión. Cuando existan oos2 y vivo, la misma razón oos2/oos1 y vivo/oos2 da la cadena de descuentos, y comparar con el 0,5 de Chan contrasta el deflated Sharpe. Es también la medida más limpia de cuánto sobreajusta el build por familia.

**Estado.** AMPLÍA (ledger, deflated Sharpe; decay midió retención mediana 0,45 en una población sin seleccionar) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 5

#### Ventanas rodantes: cuánto hay que aguantarla para que esté siempre arriba
**Fuente.** covel_trendfollowing, p. 41, 71; schwager_mw, p. 88-89 (Hite).

**Qué dice.** En Dunn, «para periodos de unos 3,75 años o más, todas las rentabilidades son positivas». Campbell 1980-2003: 56 % de meses positivos, 84 % de años, 79 % de ventanas de 12 meses, 86 % de 24, 90 % de 36 y 100 % de 48 y 60. Hite: «evaluar por año natural es muy arbitrario»; en simulación el 90 % de las ventanas de 6 meses, el 97 % de las de 12 y el 100 % de las de 18 eran rentables, y tras 7 años en vivo 90 %, 99 % y 100 %.

**Qué significaría aquí.** Desde la equity diaria ya cosechada para WFC y CSCV: P(beneficio) y rentabilidad mediana en toda ventana de L meses (L = 1 a 24), IS frente a OOS, y la ventana más corta con 100 % (y 95 %) de ventanas positivas. Lo nuevo es compararlo con el mono: una entrada aleatoria con deriva positiva también llega al 100 % algún día, y la distancia entre las dos curvas a 6-12 meses es una medida legible del edge. Es además la paciencia que se le da en vivo antes de retirarla.

**Estado.** NUEVA — **Tipo.** estudio — **Locura.** 0 — **Valor.** 4

#### Empezar el día equivocado: distribuciones por fecha de arranque
**Fuente.** fitschen_reliable, p. 183-189, 191-213.

**Qué dice.** Para una cuenta pequeña el riesgo relevante es el punto más bajo por debajo del capital INICIAL, no el pico-valle (que incluye beneficio no realizado devuelto). Construir una curva que empiece en cada trade histórico, registrar la peor caída bajo el inicio y el beneficio del primer año, y dibujar ambos como distribuciones acumuladas («60 % de probabilidad de que tu caída desde el inicio sea menor de 7.400 $»). Usa el orden real de los trades; solo varía la fecha de inicio.

**Qué significaría aquí.** Una alternativa sin remuestreo al bootstrap de trades, compatible con la postura del dueño: la distribución, sobre fechas de inicio, de rentabilidad del primer año, caída máxima bajo el inicio y tiempo hasta el primer máximo nuevo. Responde a «¿y si hubiera empezado en el peor momento?» para blindJoint, exposure y la cartera.

**Estado.** NUEVA — **Tipo.** estudio — **Locura.** 0 — **Valor.** 4

#### Cuántos trades o meses hacen falta para saber si funciona (MinTRL)
**Fuente.** schwager_nmw, p. 139-140 (Hull); schwager_mw, p. 51 (Dennis); web: MinTRL de Bailey y López de Prado (https://portfoliooptimizer.io/blog/the-probabilistic-sharpe-ratio-bias-adjustment-confidence-intervals-hypothesis-testing-and-minimum-track-record-length/); web: MinTRL con colas gruesas, Choufani 2026 (https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7024958).

**Qué dice.** Las primeras 50 apuestas de blackjack de Hull perdieron; calculó cuántas apuestas hacían falta para estar seguro de ganar a largo plazo. Dennis: menos de un año de resultados no dice nada. Ejemplo de MinTRL (longitud mínima del historial para afirmar que el Sharpe supera un umbral): Sharpe 2 frente a 1 al 95 % → 2,73 años con datos diarios normales; con asimetría -0,72 y curtosis 5,78 → 4,99 años con datos mensuales.

**Qué significaría aquí.** Para cada superviviente: «trades hasta significancia», el número de trades con el que su media y desviación por trade darían t = 2 (unos 4·σ²/μ²), junto a los que tiene; y, dada su frecuencia y su propia asimetría y curtosis, los meses de paper o vivo necesarios para confirmarla o rechazarla con una potencia fijada. La duración de la incubación sale de la matemática, no de la costumbre, y se ve qué supervivientes no se podrán verificar nunca en un tiempo razonable.

**Estado.** AMPLÍA (core/significance tiene PSR y min-track-record; datos frescos como OOS renovable, aceptado) — **Tipo.** vivo — **Locura.** 0 — **Valor.** 4

#### Las métricas de dolor: drawdown medio anual, tiempo plano y gain-to-pain
**Fuente.** fitschen_reliable, p. 1-5, 67-68, 107-117; katz_encyclopedia, p. 19; cmt_complete2, p. 549-550, 556; williams_longterm, p. 154; tharp_freedom, p. 47-57, 66; covel_trendfollowing, Apéndice F p. 387-389.

**Qué dice.** Fitschen define un sistema operable antes de desarrollarlo: rentabilidad anual mayor que el drawdown máximo, rentabilidad múltiplo del drawdown máximo MEDIO anual (el que vives cada año) y el tiempo más largo entre máximos de equity. Los 20 mejores CTA de Barclay 2005-2010 promediaban un 28 % anual con un drawdown de 5 años pocos puntos por debajo, e incluso el mejor tuvo 12 meses a +1 %. Gain-to-pain = beneficio anual medio / media de los N mayores drawdowns (N = años); desarrollar con beneficio por trade dio al sistema de commodities un 50 % más de beneficio pero 4 veces el drawdown anual medio y 6 veces el máximo. Katz: «periodo plano más largo» y razón de pérdida. Chande: drawdown menor del 20 % y de 9 meses. Williams: drawdown no mayor del 15 % del beneficio (dependiente de la longitud del test). Tharp y Basso: los objetivos (drawdown y su duración tolerables, más del 15 % o más de un año es «mortal») antes que la búsqueda. Mechanica: porcentaje de días en máximos nuevos.

**Qué significaría aquí.** Columnas que profitShape y la lectura conjunta quizá no tienen: drawdown máximo medio anual (mejor como media de los N mayores drawdowns que por año natural), tiempo más largo bajo el agua, y rentabilidad anual / drawdown medio anual como cifra invariante al apalancamiento. Una ficha de objetivos por familia de activos (R/año objetivo, drawdown y duración máximos) de la que derivar los umbrales del gate para que no sean un montón de números sueltos. El tiempo plano lo arregla la combinación con otra estrategia, no más reglas.

**Estado.** AMPLÍA (profitShape; lectura conjunta) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 3

#### La hoja de pérdidas serias, antes de ir a vivo
**Fuente.** covel_trendfollowing, p. 106-107; abraham_tfbible, cap. 10 p. 161-190.

**Qué dice.** Dunn entregaba a cada inversor la lista de todas las pérdidas pasadas de más del 25 % (8 en 26 años; la peor, 52 % en 4 meses en 1976): «esto pasó y volverá a pasar». Tabla de recuperación: un 50 % de caída necesita un +100 %. Los dos modelos en vivo de Abraham (2010-2012) subieron un poco y luego estuvieron 17 meses sin máximo nuevo, con meses de pequeñas pérdidas y pequeñas ganancias entre raros ganadores.

**Qué significaría aquí.** Por estrategia, una tabla de episodios de drawdown (profundidad, fecha de pico, valle y recuperación, duración) para IS, OOS y los percentiles del MC, con el gráfico bajo el agua. Y, desde OOS y MC, la distribución de «tiempo hasta el primer máximo nuevo tras el lanzamiento». Compromete al dueño con lo que es un dolor normal antes del primer trade, para reconocer 17 meses planos como normales (o no).

**Estado.** AMPLÍA (profitShape y CUSUM existen; la tabla de episodios probablemente no) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 3

#### La probabilidad de un año perdedor como titular
**Fuente.** schwager_nmw, p. 95 (Blake).

**Qué dice.** «Puedes diversificar muy bien simplemente haciendo suficientes operaciones al año. Con un 70 % a favor y cincuenta operaciones, es muy difícil tener un año negativo.»

**Qué significaría aquí.** P(año perdedor), calculada desde el porcentaje de aciertos, el payoff y los trades por año (binomial o bootstrap de un año de trades), es un titular más útil para el dueño que el Sharpe de una estrategia sola.

**Estado.** NUEVA — **Tipo.** estudio — **Locura.** 0 — **Valor.** 3

### 5.7 · Tamaño de posición y apalancamiento

#### Kelly como asignador y como freno: f = m/s², medio Kelly y techo por la peor pérdida
**Fuente.** chan_quantitative, p. 17, 19, 95-106, 112-113; chan_algorithmic, p. 170-180; aronson_ebta, p. 348.

**Qué dice.** Con rentabilidades gaussianas, el apalancamiento óptimo es f = m/s² (en vector F = C⁻¹M para varias estrategias) y el crecimiento máximo g = r + S²/2: es el Sharpe, no la rentabilidad, lo que fija el crecimiento. Usar medio Kelly, y el apalancamiento final es el mínimo entre medio Kelly y (drawdown tolerable en un periodo / peor pérdida histórica de un periodo). Recalcular F cada día con una ventana (6 meses para tenencias de un día) desapalanca poco a poco una estrategia que decae, sin interruptor. Con colas gruesas: maximizar el crecimiento logarítmico sobre 100.000 rentabilidades de una Pearson ajustada a los cuatro primeros momentos; medio Kelly aún dio un drawdown del 96 %, y hizo falta 1/7 de Kelly para un 50 %. Bajo un tope de apalancamiento muy inferior a Kelly, suele ser óptimo concentrar en la estrategia de mayor crecimiento. Aronson: una moneda que paga 2 a 1 tiene Kelly 0,25, y apostar el 0,58 arruina pese a la esperanza positiva; dimensionar desde el edge corregido (encogido o cota inferior), no el del backtest.

**Qué significaría aquí.** El asignador natural del módulo de cartera: comparar Kelly, la simulación Pearson y el crecimiento histórico por estrategia, tomar el mínimo y mostrar el drawdown de cada uno. La simulación paramétrica complementa el bootstrap de trades que el dueño reserva para dimensionar. El Kelly con ventana móvil es también un interruptor de retirada sin umbral arbitrario.

**Estado.** NUEVA (módulo de cartera sin construir) — **Tipo.** cartera — **Locura.** 0 — **Valor.** 4

#### Kelly con restricción de drawdown, y el drawdown de la prop firm como restricción
**Fuente.** web: Busseti, Ryu y Boyd 2016 (https://stanford.edu/~boyd//papers/pdf/kelly.pdf); web: QuantInsti (https://blog.quantinsti.com/risk-constrained-kelly-criterion/).

**Qué dice.** El Kelly con restricción de riesgo es un problema convexo con una cota P(caída hasta α) ≤ β; gana al Kelly fraccional con el mismo riesgo de drawdown.

**Qué significaría aquí.** Dimensionado de cartera; y para cuentas fondeadas la restricción ES el drawdown de la prop firm. Encaja con portfolio/CLAUDE.md, que ya dice que las reglas de la cuenta fondeada son restricciones y no filtros posteriores.

**Estado.** NUEVA — **Tipo.** cartera — **Locura.** 1 — **Valor.** 4

#### Probabilidad de pasar el examen de la prop firm
**Fuente.** web: QuantVPS, estadísticas de prop firms (https://www.quantvps.com/blog/prop-firm-statistics); web: Prop Firm Trading Tools (https://propfirmtradingtools.com/).

**Qué dice.** Monte Carlo sobre la distribución de trades con las reglas de la firma (pérdida diaria 5 %, total 10 %, objetivo 8-10 %). Las tasas de aprobación son del 5-10 % (FTMO 9-10 %), y los fallos de la primera semana vienen del límite diario. El riesgo por trade que maximiza P(aprobar) tiene forma de U invertida.

**Qué significaría aquí.** Para portfolio/funded: dado un superviviente o una cartera, el riesgo por trade que maximiza P(aprobar) y P(cobrar). Aquí el bootstrap de trades es legítimo (la postura del dueño lo reserva para dimensionar). Resuelve la pregunta abierta 6 de DECISIONS.md desde los datos.

**Estado.** NUEVA — **Tipo.** cartera — **Locura.** 0 — **Valor.** 4

#### El volatility targeting es procíclico: suelo de volatilidad y tope de apalancamiento
**Fuente.** lowenstein_ltcm, p. 60-66, 138; schwager_nmw, p. 30 (Lipschutz), p. 110-111 (Basso); web: Moreira-Muir 2017 (https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2659431); web: Cederburg y otros (https://www.sciencedirect.com/science/article/abs/pii/S0304405X2030132X).

**Qué dice.** LTCM apuntaba a una volatilidad de cartera: «si la cartera estaba demasiado tranquila, se endeudaban más». En julio de 1998 los modelos decían que el riesgo diario había bajado de 45 a 34 millones mientras el apalancamiento subía a 31:1. Lipschutz: en los periodos de baja volatilidad el tamaño crecía para capturar movimientos cada vez más pequeños, y un discurso de Gorbachov movió el dólar un 1 % en ocho minutos sin liquidez. Basso adoptó el tamaño por volatilidad tras devolver el 80 % de 500.000 $ en plata en una semana. Moreira y Muir: escalar por 1/varianza realizada sube el Sharpe de muchos factores, incluido el carry FX; Cederburg y otros no ven mejora fuera de muestra en 103 estrategias.

**Qué significaría aquí.** Si se adopta el tamaño inverso a la volatilidad (lo más probable), dimensionar con max(volatilidad corta, larga, un suelo tomado de la volatilidad de crisis del instrumento o su percentil 25 de largo plazo), limitar el multiplicador (por ejemplo, no más de 1,5 veces el tamaño medio) y nunca subir el tamaño para mantener la rentabilidad cuando el edge por trade encoge. Comprobable sobre la equity diaria: con y sin suelo, comparar los peores días. Y para una estrategia sola: ¿escalar sus trades por 1/ATR² en la entrada mejora el resultado ajustado por riesgo? Medible en Python sobre los trades existentes.

**Estado.** NUEVA (cartera) — **Tipo.** cartera — **Locura.** 0 — **Valor.** 4

#### ¿Operar la curva de capital o subir tras ganar? Primero medir la dependencia
**Fuente.** katz_encyclopedia, p. 52; williams_longterm, p. 198-199; schwager_nmw, p. 44 (McKay), p. 68 (Trout), p. 129, 133-134 (J. Ritchie); faith_turtle, p. 259-260; covel_trendfollowing, p. 108-110; web: Davey, equity curve trading (https://kjtradingsystems.com/equity-curve-trading.html).

**Qué dice.** Si ganancias y pérdidas vienen en rachas, un metasistema que solo opera tras un ganador puede explotarlo; si no, es inútil. Williams: en sus sistemas del 65 %, tras tres pérdidas seguidas la siguiente ganaba más del 80 % y añadía una unidad. Trout y McKay suben el tamaño cuando ganan. En cambio, el único año perdedor de CRT fue por casi triplicar el tamaño a mitad de año en una buena racha; a tamaño constante habría sido ganador. Menos del 50 % de las cuentas cerradas de CTA siempre rentables ganaron dinero, porque los clientes entran tras rachas y salen tras drawdowns. JWH: tras drawdowns del 10 al 30 %, casi todas las ventanas de 12 meses siguientes fueron rentables (+52 a +96 %), 4 meses del valle al nuevo máximo. Davey: 9 de cada 10 estrategias algorítmicas no tienen dependencia serial. Los Turtles saltaban la señal si la anterior (tomada o no) habría ganado.

**Qué significaría aquí.** profitShape (dependence.py) ya prueba rachas y Ljung-Box. Convertirlo en decisión: solo si los resultados muestran dependencia positiva (z de rachas < -2) puede la cartera usar dimensionado por curva de capital; y probarlo contra tamaño constante en OOS. Añadir la rentabilidad a 3, 6 y 12 meses condicionada a la profundidad del drawdown actual: si es mayor tras drawdowns profundos, el filtro de curva de capital perjudica a esa estrategia; si es menor, la estrategia está muriendo. Y E[R | señal anterior ganó] frente a E[R | perdió], con trades sombra. Todo en trades OOS, nunca IS. Cambios de tamaño solo por calendario, nunca tras una racha.

**Estado.** AMPLÍA (profitShape dependence.py → regla de cartera) — **Tipo.** cartera — **Locura.** 1 — **Valor.** 4

#### Kelly y optimal f fallan en la práctica: riesgo fraccional fijo
**Fuente.** fitschen_reliable, p. 159-161, 176-183; williams_longterm, p. 173-184.

**Qué dice.** Un juego del 60 % a la par jugado a Kelly (20 %) dio un drawdown máximo medio del 77 % en 100 apuestas; un trader aguantaría el 1-2 %. El optimal f del sistema de commodities (f = 0,91) quebró en 2 años: los trades se solapan y el beneficio abierto oscila durante los trades. El riesgo fraccional fijo (tamaño = % del capital / distancia al stop) ganó al optimal f en rentabilidad y drawdown; el fixed ratio de Ryan Jones fue peor que ambos. Williams: Kelly con 65 % y R = 1,3 da un 38 % de la cuenta, ganancias espectaculares y luego de 2,1 millones a 700.000 $; Vince: Kelly supone payoffs fijos. Su regla: contratos = saldo × 10-15 % / mayor pérdida histórica; el beneficio sube más rápido que el drawdown hasta un 14-21 % de riesgo y luego al revés.

**Qué significaría aquí.** Para cartera y vivo: dimensionar en R con riesgo fijo, nunca Kelly ni optimal f calculados sobre listas de trades cerrados. El denominador «mayor pérdida» debería ser un cuantil alto de la distribución de pérdidas del OOS o del MC, no el máximo histórico, que casi seguro se superará. Y nunca dimensionar desde trades IS.

**⚠ Contradice.** Discrepa de «Kelly como asignador y como freno»: Chan defiende Kelly fraccional con techo; Fitschen y Williams lo desaconsejan salvo a fracciones muy pequeñas. Ambos coinciden en que el Kelly completo arruina.

**Estado.** YA EXISTE en parte (métricas en R, aceptadas; dimensionado fuera de la secuencia individual) — **Tipo.** cartera — **Locura.** 0 — **Valor.** 3

#### La curva de la ballena: no optimizar el tamaño, quedarse al final de la parte lineal
**Fuente.** schwager_nmw, p. 53 (Eckhardt); williams_longterm, p. 173-184.

**Qué dice.** Nunca planear arriesgar más de un 2 % por operación. El rendimiento frente al tamaño es lineal al principio, se aplana porque los drawdowns obligan a operar más pequeño, llega a un pico («el espiráculo») y se desploma: un tamaño algo por encima del óptimo da rendimiento negativo. «El tamaño es lo único que no quieres optimizar. El óptimo está justo antes del precipicio.» Williams dibuja la misma curva de rentabilidad y drawdown contra el riesgo, con su rodilla.

**Qué significaría aquí.** En el módulo de cartera, dibujar el crecimiento geométrico frente a la fracción con el bootstrap de trades (donde el dueño lo mantiene) y elegir el final de la parte lineal, no Kelly; informar la curva y la distancia al pico.

**Estado.** NUEVA (cartera) — **Tipo.** cartera — **Locura.** 0 — **Valor.** 3

#### Riesgo por volatilidad o por distancia al stop: la base importa más que el porcentaje
**Fuente.** tharp_freedom, p. 292-298; covel_trendfollowing, p. 33, 45, Apéndice F p. 387-389; covel_completeturtle, p. 85-86.

**Qué dice.** El mismo breakout 55/21 en 10 commodities 1981-91 con 1 millón: 1 % de riesgo → 7,2 % anual y 13,2 % de drawdown; 1 % de volatilidad (ATR de 20 días) → 40 % anual y 49,5 % de drawdown; el sistema rompe al 7,5 % de volatilidad o por margen. Menos de un 1 % con dinero ajeno, más de un 3 % es «pistolero». Dunn: cuanto más volátil el mercado, menos opera; riesgo diseñado como «un 1 % de probabilidad de perder un 20 % o más en un mes». Mechanica: contratos = mín(2 % / riesgo hasta el stop, 2 % / (2 × ATR de 15 días)). Parker: las mejores tendencias empiezan con N muy bajo y el tamaño por N pone una posición enorme (unidades de soja 2,5 veces mayores al inicio que al final).

**Qué significaría aquí.** Sin stop en el build, el porcentaje de riesgo no está definido: el tamaño por volatilidad ATR es la única opción coherente, y el doble tope protege de que un stop ajustado infle el tamaño. Presentar la curva de dimensionado (rentabilidad, drawdown y ruina contra el % de riesgo), no un solo número. Plantear el presupuesto como probabilidad de cola mensual (P(mes < -10 %) ≤ 1 %) resuelta desde la distribución mensual OOS. Comprobar en el mapa condicional si las entradas con ATR bajo respecto a su año concentran el R: si sí, el tamaño inverso al ATR hace trabajo real.

**Estado.** NUEVA (cartera) — **Tipo.** cartera — **Locura.** 0 — **Valor.** 3

#### Margen y stop-out del bróker como restricción simulada
**Fuente.** lowenstein_ltcm, p. 46-48, 150-175.

**Qué dice.** Sin colchones de margen el fondo podía «caer hasta cero»; las llamadas de margen llegan cuando los precios están peor; «el inversor muy apalancado e ilíquido tiene que acertar todos los días».

**Qué significaría aquí.** El simulador de cartera debe seguir el nivel de margen de MT5 trade a trade (apalancamiento por instrumento, niveles de margin call y stop-out del bróker, subidas de margen de fin de semana de algunos brókers CFD) y dar el nivel mínimo alcanzado en el peor camino histórico y del MC. Se rechaza cualquier configuración que se acerque al stop-out. La liquidación forzosa en el peor momento es el mecanismo concreto de ruina de una cuenta CFD minorista.

**Estado.** NUEVA — **Tipo.** cartera — **Locura.** 0 — **Valor.** 3

#### Techo de apalancamiento con visión perfecta
**Fuente.** covel_trendfollowing, p. 287 (Hite).

**Qué dice.** Hite miró el precio de fin de año de cada mercado y se preguntó qué apalancamiento habría aguantado el 1 de enero sabiéndolo: ni con visión perfecta del precio final era sostenible más de 3:1, porque el camino no se podía predecir.

**Qué significaría aquí.** Para cada instrumento y horizonte de tenencia de la estrategia, el apalancamiento máximo que sobrevive una apuesta direccional con visión perfecta dada la excursión adversa dentro del periodo (desde barras M1). Es un techo absoluto para cualquier lote en MT5 en ese instrumento y timeframe: lo que esté por encima tiende a la ruina con cualquier edge. Barato con las barras en disco.

**Estado.** NUEVA — **Tipo.** cartera — **Locura.** 2 — **Valor.** 3

#### Meta-labeling: un segundo modelo que decide el tamaño o si se salta la operación
**Fuente.** web: Quantreo, triple barrera (https://www.newsletter.quantreo.com/p/the-triple-barrier-labeling-of-marco); web: López de Prado, backtesting (https://medium.com/@caneradilirfanoglu/advances-in-financial-machine-learning-part-3-backtesting-a9d70f0832c2).

**Qué dice.** El modelo primario da el lado (aquí, la estrategia de SQX); un modelo secundario de ML predice P(el trade gana) desde variables en la entrada y decide el tamaño o saltarlo. Las etiquetas son los propios trades del superviviente.

**Qué significaría aquí.** Una capa de dimensionado sobre los supervivientes, con barrier.py de nulls para etiquetar. Debe validarse con CPCV (validación cruzada purgada) y contarse en el ledger como búsqueda; nunca decidido con el mismo OOS que seleccionó la estrategia.

**Estado.** NUEVA — **Tipo.** cartera — **Locura.** 2 — **Valor.** 3

#### Pirámides, promediar y salidas parciales
**Fuente.** fitschen_reliable, p. 165-167; chan_algorithmic, p. 72-74; faith_turtle, p. 260-266; covel_completeturtle, p. 87-92; tharp_freedom, p. 265.

**Qué dice.** Promediar a la baja vale cuando la entrada añadida es buena por sí sola (comprar a 1 desviación bajo la media de 10 días y añadir a 2 mejora porque la entrada a 2 es mejor); Fitschen nunca vio una señal de continuación mejor que una entrada de tendencia propia. Schoenberg-Corwin: entrar todo en un nivel siempre gana en muestra a escalonar, pero con volatilidad variable escalonar puede dar mejor Sharpe fuera. Los Turtles añadían cada ½N hasta 4 unidades con stops a 2N de la última (Faith), o cada 1N hasta 5 con stop de ½N (Covel): las «reglas Turtle» públicas no son una sola. Tharp: escalar salidas es dimensionado inverso: tamaño completo en las peores pérdidas y mínimo en las mejores ganancias.

**Qué significaría aquí.** Para la fábrica de variantes y el vivo: una variante de entrada escalonada solo vale si la condición añadida pasa por sí sola los mismos tests (si no, es apalancamiento disfrazado), y solo se compara fuera de muestra. En vivo, prohibir por defecto las salidas parciales; cualquier regla de salida parcial se prueba contra salida completa sobre los mismos trades. Un benchmark «Turtle» debe decir qué variante usa.

**Estado.** NUEVA — **Tipo.** cartera — **Locura.** 1 — **Valor.** 2

#### Riesgo de ruina y la caída más grande que asumes que llega mañana
**Fuente.** abraham_tfbible, p. 82-83; tharp_freedom, p. 310-312; schwager_nmw, p. 68-69 (Trout), p. 147.

**Qué dice.** Al 1 % por operación tienes unos 100 «bocados de manzana», al 10 % solo 10 («he tenido cerca de 10 perdedoras seguidas»). Ruina ≈ e^(-2a/d), con a la rentabilidad media y d su desviación; «tu peor drawdown siempre está por delante». LEED de Gallacher: elige la mayor caída que tolerarás y asume que ocurre mañana; N posiciones durante un año exponen como una posición durante N años. La mayoría de los especuladores pequeños quedan fuera antes de que su idea pueda probarse, por tamaño excesivo. Una buena gestión del dinero con un edge negativo solo asegura perder más despacio.

**Qué significaría aquí.** Combinar la racha perdedora más larga observada (profitShape ya la contrasta) con el riesgo por trade previsto para dar un «margen de rachas hasta la ruina» (cuántas pérdidas seguidas más que la peor observada aguanta la cuenta), con e^(-2a/d) como número de control. Un capital mínimo por estrategia desde su peor rango diario en R y el número de estrategias abiertas a la vez. Dimensionar para sobrevivir al doble del peor drawdown histórico (colas gruesas).

**Estado.** AMPLÍA (profitShape, rachas) — **Tipo.** cartera — **Locura.** 0 — **Valor.** 2

#### Operar menos apalancado cuando se pierde
**Fuente.** faith_turtle, p. 257-258; schwager_mw, p. 81, 84 (Seykota); schwager_nmw, p. 140, 142 (Hull), p. 175-176; chan_quantitative, p. 104-105; chan_algorithmic, p. 170-171.

**Qué dice.** Turtles: por cada 10 % de pérdida sobre la cuenta original, operar como si la cuenta fuera un 20 % menor, hasta volver al capital de inicio de año. Seykota: reducir el riesgo sistemáticamente en los drawdowns, «acercarse al dinero seguro de forma asintótica». Hull: si pierdes la mitad, apuesta la mitad. Schwager: tras perder un 10-20 %, parar, analizar y volver pequeño. Pero todo esquema de apalancamiento constante vende en las pérdidas, y si muchos hacen lo mismo el riesgo se contagia (agosto de 2007). Faith avisa de que las reglas disparadas por drawdown se sobreajustan fácilmente a una curva.

**Qué significaría aquí.** Un overlay de cartera a probar contra tamaño constante con el bootstrap por bloques conjunto, solo en versión precomprometida y contado como prueba en el ledger. Evaluar por Sharpe o ulcer, no por rentabilidad.

**Estado.** NUEVA (cartera) — **Tipo.** cartera — **Locura.** 0 — **Valor.** 2

### 5.8 · Límites de riesgo y overlays

#### Los overlays son sistemas: se preespecifican, se prueban fuera de muestra y cuentan como pruebas
**Fuente.** schwager_mw, p. 82 (Seykota), p. 90 (Hite); katz_encyclopedia, p. 356-359.

**Qué dice.** Seykota sobre variar el tamaño: «si tuvieras una política M que mejora el sistema S, quizá te iría mejor operando M». Hite: cuando la volatilidad de un mercado estropea la relación rentabilidad/riesgo esperada, deja de operarlo; semáforo verde (todas las señales), amarillo (solo salidas), rojo (liquidar y no tomar ninguna), con volatilidad de 10 a 100 días. En 1986 salió del café a 1,70 $, se perdió la subida a 2,80 $ y el desplome a 1,00 $. Katz montó una cartera eligiendo un modelo y orden por mercado «por significancia en muestra» y declaró 544 % anual IS y 625 % OOS, pero el libro ya había publicado los OOS por mercado y varias elecciones se justificaban por su comportamiento OOS: una selección contaminada.

**Qué significaría aquí.** Cada overlay (filtro de volatilidad, regla de plano ante eventos, dimensionado por curva de capital, circuit breakers) se especifica antes de probarlo, se prueba fuera de muestra como una estrategia y se cuenta en el ledger; si no, la capa de overlays es una búsqueda sin contabilizar. Lo mismo al montar la cartera: elegir por mercado desde una matriz de resultados ya vistos se registra como búsqueda. El mapa condicional ya parte por tercil de volatilidad: la decisión en que debería acabar es justo un overlay preregistrado (sin entradas nuevas en el decil más alto de volatilidad del activo, por ejemplo).

**Estado.** AMPLÍA (ledger; conditionalMap → decisión de overlay) — **Tipo.** proceso — **Locura.** 0 — **Valor.** 4

#### El reglamento de siete puertas de Abraham
**Fuente.** abraham_tfbible, p. 84-90, 100-102.

**Qué dice.** Siete puertas antes de cualquier operación: (1) solo mercados más fuertes o más débiles por ROC suavizado; (2) riesgo hasta el stop duro de ~1 % (0,75-1,25 %) del capital BASE (cerrado, sin beneficio abierto); (3) el MACD del timeframe superior de acuerdo; (4) máximo 10 largos y 10 cortos; (5) riesgo máximo por contrato de 2.000-2.500 $ sea cual sea la cuenta; (6) máximo 5 % de riesgo total por sector; (7) ninguna operación nueva mientras el beneficio abierto pase del 20 % del capital base. Margen/capital ≤ 15 %. Las operaciones que no pasan se descartan, no se redimensionan.

**Qué significaría aquí.** Un reglamento completo y numérico para cuando empiece la cartera. Dos notas: dimensionar sobre capital base (sin beneficio abierto) es una elección anti-pirámide que conviene comparar con el capital total; y las puertas hacen las entradas dependientes del camino (una señal se salta porque no hay hueco), así que la cartera se simula trade a trade, nunca sumando curvas.

**Estado.** NUEVA (cartera sin construir) — **Tipo.** cartera — **Locura.** 0 — **Valor.** 4

#### Interruptores diarios y mensuales de pérdida
**Fuente.** schwager_nmw, p. 66-68 (Trout); elder_newtfal, p. 208-213; cmt_complete2, p. 576-577; web: Robot Wealth y práctica de kill switch (https://github.com/silvermanreid21-dot/Quant-Trading-Desk).

**Qué dice.** Trout: salir de cualquier operación que pierda más del 1,5 % del capital; con un -4 % en el día, todo plano hasta mañana; con un -10 % en el mes, plano hasta el mes siguiente; tamaño máximo por mercado fijado cada inicio de mes. La regla del 4 % le costó el 9 de enero de 1991 pero la mantiene por días como el 19 de octubre de 1987. Elder, regla del 6 %: ninguna operación nueva en el resto del mes cuando las pérdidas realizadas del mes más el riesgo abierto llegan al 6 % del capital de inicio de mes; 2 % máximo por operación. Bryant: cerrar el modelo de cartera con un 20 % de pérdida. Práctica de kill switch: parada por fichero, interruptor diario (-5 %), presupuesto de riesgo del libro.

**Qué significaría aquí.** Simular estos interruptores sobre la equity diaria ya cosechada y sobre la secuencia OOS, y medir su efecto en rentabilidad, drawdown máximo y tiempo bajo el agua frente a la secuencia sin cortar Y frente a pausas colocadas al azar de la misma duración total (para no premiar al interruptor por operar menos). Si las pérdidas no se agrupan, el interruptor solo cuesta dinero.

**Estado.** NUEVA (cartera y vivo sin construir) — **Tipo.** cartera — **Locura.** 0 — **Valor.** 3

#### Pérdida máxima por escenario, no por probabilidad, y el «dinero de la casa»
**Fuente.** taleb_fooled, p. 15.

**Qué dice.** Nero sale tras una pérdida predeterminada, nunca vende opciones desnudas y «nunca se pone en situación de perder más de, digamos, un millón, sea cual sea la probabilidad»; la cantidad varía con los beneficios acumulados del año.

**Qué significaría aquí.** Una pérdida máxima dura por estrategia y por cartera definida por escenario (¿y si el precio salta X % contra todas las posiciones abiertas a la vez?), no por una probabilidad de VaR. El presupuesto crece con el beneficio realizado del año y vuelve a encoger tras pérdidas, lo que limita el riesgo al principio del año.

**Estado.** NUEVA (vivo sin construir) — **Tipo.** vivo — **Locura.** 0 — **Valor.** 3

#### Beneficio abierto devuelto: los mayores drawdowns llegan tras los mayores beneficios abiertos
**Fuente.** abraham_tfbible, p. 88-89, 101; schwager_nmw, p. 127-130 (M. Ritchie); fitschen_reliable, p. 79-85.

**Qué dice.** Abraham: sus mayores drawdowns llegan cuando el beneficio abierto es mayor; por eso no abre nada nuevo con beneficio abierto por encima del 20 % del capital base, o estrecha el stop. Mark Ritchie, al revés: «si protegiera el beneficio abierto con el mismo cuidado que el cerrado, nunca participaría en un movimiento largo»; el oro en 1980 devolvió un 25 % en un día y siguió siendo un gran beneficio. Fitschen: devolver beneficio abierto es la verruga principal de la tendencia.

**Qué significaría aquí.** Una afirmación comprobable: por trade, la fracción del beneficio máximo abierto (MFE) devuelta antes de salir, frente al mono con las mismas salidas; y, a nivel de cartera, si la profundidad del drawdown la predice el beneficio abierto en el pico. Si es grande y sistemático, una regla de estrechar con la volatilidad es candidata (como hipótesis nueva, no ajustada). Sale del MFE/MAE ya calculado.

**Estado.** AMPLÍA (entryQuality MFE/MAE) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 3

### 5.9 · Construcción de cartera y correlación

#### La correlación en días de estrés: «en una crisis las correlaciones van a uno»
**Fuente.** lowenstein_ltcm, p. 41-42, 168, 181, 233-234; chan_algorithmic, p. 170-171; chan_quantitative, p. 104-105; schwager_nmw, p. 58; web: BIS, agosto 2024 (https://www.bis.org/publ/bisbull90.pdf).

**Qué dice.** Los valores de LTCM «podían no tener relación, pero los tenían los mismos inversores, lo que los unía en momentos de estrés»; «nuestras pérdidas entre estrategias estaban correlacionadas a posteriori»; «diversificados en forma, no en sustancia: la misma apuesta en todas sus permutaciones». Chan: muchos fondos con las mismas posiciones convirtieron la pérdida de uno en el crash cuant de agosto de 2007. Los Turtles fallaron todos juntos en 1991. En agosto de 2024, volatility targeting, risk parity y CTAs redujeron riesgo a la vez; la librería tiene AUDJPY, CADJPY, EURJPY, GBPJPY, USDJPY y NIKKEI225: cinco apuestas de yen correlacionadas.

**Qué significaría aquí.** El filtro de redundancia mide la correlación en toda la muestra. Añadir la misma matriz solo en días de estrés (5 % de mayor movimiento absoluto del activo o de un proxy de riesgo, o las crisis con nombre) y en los peores días de los propios supervivientes, y dar el número efectivo de estrategias independientes en calma y en estrés. Dos supervivientes con ρ 0,1 en total y 0,8 en días de estrés son una sola estrategia a efectos de riesgo. Usa el P&L diario ya cosechado.

**Estado.** AMPLÍA (filtro de redundancia del gate, correlación incondicional) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 5

#### ¿Persisten los resultados de las estrategias o revierten? Medirlo antes de rotar
**Fuente.** schwager_smw, p. 105, 107 (Lescarbeau), p. 127; schwager_nmw, p. 158-159 (Faulkner).

**Qué dice.** Lescarbeau: «los sistemas tienen una vida», y «los que mejor han ido en el pasado reciente también tienden a ir mejor en el futuro inmediato», así que se apoya en los ganadores recientes. Schwager suele aconsejar entrar en un gestor tras un periodo por debajo de la media. Faulkner: tras un periodo malo, el siguiente suele ser mejor por regresión a la media. Las dos voces más experimentadas discrepan.

**Qué significaría aquí.** El ledger y los datos de variantes y WFC tienen cientos de estrategias con rendimiento fechado. Ordenar los supervivientes por rendimiento en la ventana t y medir la correlación de rangos con la ventana t+1, por activo, timeframe y familia, con el mono de referencia. La respuesta decide la regla de rotación de la cartera (apoyarse en ganadores recientes o comprar la caída de estrategias) y calibra el trabajo de vida media del edge.

**Estado.** NUEVA (amplía vida media del edge y ledger como meta-modelo) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 5

#### El MC de cartera por bloques de P&L diario conjunto, no barajando trades
**Fuente.** faith_turtle, p. 199-205; fitschen_reliable, p. 161-165.

**Qué dice.** Reordenar trades elimina el movimiento conjunto de pérdidas simultáneas entre mercados al final de las tendencias (oro, plata y azúcar giraron juntos en mayo-junio de 2006; el hueco de 1987 golpeó a la vez mercados no correlacionados) y la correlación serial de los días malos; barajar la curva de equity en trozos de 20 días la conserva. Fitschen: barajar trades cerrados ignora el beneficio abierto devuelto dentro de los trades, las entradas agrupadas por día y por grupo, y reglas como un trade por mercado y día; «el Monte Carlo no te dice nada útil más allá de tus estadísticas de desarrollo». El MC hereda además el sesgo de la optimización.

**Qué significaría aquí.** Para dimensionar la cartera, remuestrear bloques (bootstrap estacionario, unos 20 días hábiles) de la matriz de P&L diario de todas las estrategias a la vez, no extracciones independientes de trades. Ya figura en portfolio/common/monteCarlo/POSSIBLE_IMPROVEMENTS.md; esto es apoyo de los libros para subirlo de prioridad.

**⚠ Contradice.** El dueño mantiene el bootstrap de trades precisamente para dimensionar la cartera, y ese es el uso en el que Faith dice que subestima el drawdown (faith_turtle p. 201-203; fitschen_reliable p. 161-165).

**Estado.** AMPLÍA (portfolio/common/monteCarlo) — **Tipo.** cartera — **Locura.** 0 — **Valor.** 4

#### Clones del plateau: el mismo trade sumado varias veces
**Fuente.** covel_completeturtle, p. 126-128, 142-143; schwager_mw, p. 38 (Kovner).

**Qué dice.** Cuatro Turtles pasaron un año construyendo una plataforma de test y vieron que combinar S1 y S2 daba un peor caso del -80 % en vez del -50 % creído, porque ambos sistemas tomaban a menudo el mismo breakout a la vez. Memo de Dennis de 1986: «drawdowns reales muy por encima de los teóricos... habéis estado operando hasta el doble de grande de lo que pensábamos»; todos los tamaños a la mitad. Ya independientes, los Turtles operaban igual. Kovner: «ocho posiciones muy correlacionadas son una posición ocho veces mayor».

**Qué significaría aquí.** Al combinar supervivientes (vecinos del plateau, variantes, plantillas del mismo activo), medir el solapamiento de señales (fracción de barras en que k estrategias están en la misma dirección en el mismo activo) y dimensionar sobre la posición conjunta. La fábrica de variantes y «operar el plateau» producen justo estos clones correlacionados. El filtro de redundancia debería usar la correlación del P&L diario OOS y el solapamiento, no solo el parecido de reglas.

**⚠ Contradice.** «Operar el plateau» multiplica el riesgo correlacionado en la cartera: dimensionados por separado, los vecinos repiten el error S1+S2 (covel_completeturtle p. 126-128).

**Estado.** NUEVA (nada mide el solapamiento de entradas entre supervivientes) — **Tipo.** cartera — **Locura.** 0 — **Valor.** 4

#### Calor de cartera, límites por grupo y stop-outs conjuntos
**Fuente.** covel_trendfollowing, p. 254-259; faith_turtle, p. 118-120, 255-257; fitschen_reliable, p. 191-213, 221-232; covel_completeturtle, p. 96-97; schwager_nmw, p. 49-50 (Eckhardt).

**Qué dice.** Seykota: el calor es la suma del riesgo abierto (2 % en 5 instrumentos = 10 %); la rentabilidad sube con el calor hasta un punto y luego baja. Vandergrift: la mayoría de las pérdidas vinieron de uno o dos sectores correlacionados tocando la pérdida máxima juntos. Turtles: máximo 4 unidades por mercado, 6 en grupo muy correlacionado, 10 en poco correlacionado, 12 por dirección; los límites «ahorraron a Rich más de 100 millones» en octubre de 1987. Riesgo neto largo/corto = lado mayor − lado menor/2 (4 largos y 3 cortos = 2,5 unidades), y mercados correlacionados cuentan como uno. Fitschen: diversificar entre grupos poco correlacionados en vez de doblar los mejores mercados (gain-to-pain de 4,09 a 7,56); topes de riesgo abierto y de operaciones abiertas bajan la caída desde el inicio. Eckhardt: operar un tamaño razonable y recortar cuando la exposición es demasiado alta, en vez de dimensionar cada estrategia para su peor caso.

**Qué significaría aquí.** Para el módulo de cartera: tope del riesgo abierto total y por grupo de correlación (XAU+XAG, índices, pares USD, cruces de yen), con los grupos sacados del historial de stop-outs conjuntos, no solo de la correlación de rentabilidades. Ya se puede preparar: con el retest cross-market, contar cuántas veces los trades perdedores de los supervivientes coinciden en el tiempo entre mercados relacionados («tasa de stop-out conjunto»). Los 9 mercados relacionados son un «grupo»: limitar la exposición en vez de operar todos los mercados en que pasa una estrategia.

**Estado.** AMPLÍA (la redundancia existe a nivel de población; calor y stop-out conjunto son nuevos) — **Tipo.** cartera — **Locura.** 0 — **Valor.** 4

#### El último del grupo en dar señal es el peor
**Fuente.** faith_turtle, p. 118-120, 255-257, 271-272; fitschen_reliable, p. 191-213.

**Qué dice.** Los límites por grupo también filtraban mercados rezagados: «los mercados que daban señal los últimos a menudo no se movían tanto y era más probable que perdieran». Con varias señales a la vez, comprar el más fuerte y vender el más débil del grupo (cambio de precio en 3 meses / N). Fitschen: operar el primero en dar señal de cada grupo.

**Qué significaría aquí.** Una hipótesis comprobable con la salida del cross-market: cuando la misma estrategia da señal en varios de los 9 mercados relacionados en poco tiempo, ordenar las señales por orden (primera o última) o por fuerza relativa y comparar sus resultados. Si los rezagados rinden peor, una regla «primeros 2 del grupo» o «el más fuerte del grupo» es un filtro de cartera con un coste claro en trades.

**Estado.** NUEVA — **Tipo.** cartera — **Locura.** 1 — **Valor.** 4

#### Contribución marginal: admitir una estrategia solo si mejora el libro
**Fuente.** web: descomposición de Euler del Sharpe (https://arxiv.org/pdf/1807.09864); web: contribución marginal al Sharpe (https://hal.science/hal-03189299v2/file/Computation_Marginal_Contribution_Sharpe_ratio.pdf); schwager_smw, p. 51 (Galante); fitschen_reliable, p. 4, 241-244; schwager_mw, p. 90, 94 (Hite); faith_turtle, p. 219-221.

**Qué dice.** Admitir un superviviente en la librería solo si su Sharpe incremental al libro existente es positivo neto de coste; preregistrar el incremental esperado frente al real e informarlo. Galante: un fondo corto que rendía mucho menos que el índice, combinado 1:1 con el Nasdaq, le habría ganado tras costes de préstamo y habría recortado sus dos peores drawdowns de 20 %/13 % a 10 %/5 %. Fitschen: el sistema de acciones (contratendencia) y el de commodities (tendencia) a medio riesgo cada uno subieron el gain-to-pain por encima de 4, mejor mezcla 55/45. Hite guarda sistemas «no muy buenos por sí solos» por su baja correlación. Faith: el lado largo (R³, rentabilidad de regresión dividida por drawdowns medios y su duración, 1,19) y el corto (0,41) del Bollinger Breakout juntos dan R³ 5,20; quitar el lado corto débil sería un error.

**Qué significaría aquí.** Criterio de aceptación de la cartera, que además evita que la fábrica llene el libro con 20 copias de tendencia en oro. Guardar un grupo de «casi supervivientes» (pasaron el nulo, fallaron un filtro secundario) para medir su aportación marginal. Evaluar los lados largo y corto por separado Y juntos antes de amputar uno.

**⚠ Contradice.** El gate juzga cada estrategia sola, y la comparación directa de blindJoint contra buy-and-hold usada como veto puede tirar diversificadores reales (schwager_smw p. 51; schwager_mw p. 90, 94).

**Estado.** NUEVA (criterio de cartera) — **Tipo.** cartera — **Locura.** 1 — **Valor.** 4

#### Confluencia: estrategias que no pagan sus costes pueden pagarlos cuando coinciden
**Fuente.** schwager_smw, p. 142, 168 (Shaw); aronson_ebta, p. 455-457; web: Build Alpha, ensembles (https://www.buildalpha.com/trading-ensemble-strategies/); web: Malizzi, ensembles (https://joshmalizzi.substack.com/p/what-is-an-ensemble-lets-talk-about).

**Qué dice.** Shaw: «una sola ineficiencia puede no bastar para cubrir costes; cuando coinciden varias, pueden dar un beneficio esperado mayor que los costes». Ejemplo de Schwager: dos estrategias de +100 $ bruto frente a 110 $ de coste; el subconjunto donde coinciden promedia +180 $. Hsu-Kuan: votos y posiciones fraccionarias dentro de un tema (2.040 reglas OBV, 1.158 cortas y 882 largas → 0,135 unidades cortas). Los ensembles que operan cuando k de n coinciden reducen la varianza.

**Qué significaría aquí.** Por activo y timeframe, tomar la población que ganó al mono en P&L BRUTO pero falló tras costes, y medir la esperanza neta del subconjunto de barras donde k ≥ 2 de esas estrategias independientes señalan la misma dirección. Es una búsqueda nueva: control de multiplicidad y registro en el ledger. Convierte trabajo descartado en supervivientes. Y una prueba limpia: ¿el ensemble de todas las variantes de una estructura gana al madre seleccionado fuera de muestra? Si sí, la selección no aporta.

**Estado.** NUEVA (el voto dentro de un tema apoya «operar el plateau», ya aceptado) — **Tipo.** cartera — **Locura.** 2 — **Valor.** 4

#### ¿Una sola apuesta en muchas permutaciones? Factores y monocultivo
**Fuente.** lowenstein_ltcm, p. 233-234; taleb_fooled, p. 74, 80; schwager_smw, p. 114 (Masters), 142 (Shaw), 147 (Cohen).

**Qué dice.** Los muchos trades «diversificados» de LTCM eran todos cortos de liquidez y crédito; dos operaciones lo rompieron. Taleb: los supervivientes de un periodo comparten el rasgo que el periodo premió (comprar caídas en 1992-1998); un cambio de régimen barre a toda la cohorte. Shaw cubre los factores de mercado, divisa y tipos cuando no apuesta por ellos. Cohen: un 40 % mercado, 30 % sector, 30 % el valor.

**Qué significaría aquí.** Regresar el P&L diario de cada superviviente sobre unos pocos factores construidos con las barras en disco (dirección del subyacente, cambio de volatilidad, un factor de tendencia genérico, uno de reversión, swap/carry, cesta USD) y agruparlos por vector de exposición; dar la parte del riesgo de la población que explica el primer factor. Y describir la población tras el gate por rasgos (porcentaje de largos, tenencia, reversión frente a breakout, hora, correlación con la tendencia del build): si el 85 % de los supervivientes del oro son compradores de caídas en un segmento alcista, la población es una apuesta, no muchas.

**Estado.** NUEVA (el filtro de redundancia trabaja sobre correlación de equities) — **Tipo.** estudio — **Locura.** 1 — **Valor.** 4

#### Pesos iguales como la referencia que toda optimización debe batir
**Fuente.** schwager_nmw, p. 48 (Eckhardt); covel_completeturtle, p. 114-126; web: HRP (https://en.wikipedia.org/wiki/Hierarchical_Risk_Parity); web: Quantpedia, HRP (https://quantpedia.com/hierarchical-risk-parity/); web: Carver, handcrafting (https://qoppac.blogspot.com/2018/12/portfolio-construction-through_14.html).

**Qué dice.** Eckhardt: la mejor forma de combinar indicadores suele ser 1 o 0 y, si valen, con el mismo peso; lo mismo con los trades, a tamaño completo o nada. Dennis asignaba capital a los Turtles a ojo (uno recibió 20 veces más, al mejor ajustado por riesgo le recortaron) y Keefer argumentó que el reparto igual habría ganado más. HRP (agrupar y bisecar) frente a pesos iguales: los iguales suelen ganar fuera de muestra. Carver: pesos iguales difíciles de batir; agrupar jerárquicamente por correlación, ponderar por volatilidad dentro del grupo y multiplicadores de diversificación (IDM 1-2,5 multiactivo, 1-1,4 en una sola clase).

**Qué significaría aquí.** Por defecto del módulo de cartera: pesos iguales (o riesgo igual) como línea base que cualquier ponderación optimizada debe batir fuera de muestra, y la construcción de Carver como método estándar. Nunca asignar por la estrategia favorita; registrar cualquier excepción discrecional en el ledger como «estrategia» aparte a puntuar. Responde a la pregunta abierta 3 de DECISIONS.md.

**Estado.** NUEVA (cartera) — **Tipo.** cartera — **Locura.** 0 — **Valor.** 3

#### Mezclar momentum y reversión en la cartera
**Fuente.** chan_algorithmic, p. 60-61, 151-154; covel_trendfollowing, p. 143, 305.

**Qué dice.** El momentum tiene pérdida limitada por posición y ganancia abierta, se beneficia de cisnes negros y curtosis, pero se hunde años tras las crisis (el momentum de 1929 tardó 30 años en recuperarse). La reversión da consistencia que invita a apalancarse demasiado y pérdidas raras catastróficas. Añadir momentum a una cartera de reversión sube el Sharpe y baja el drawdown.

**Qué significaría aquí.** Clasificar cada superviviente como de tipo reversión o momentum (por su entrada, a favor o en contra del último movimiento, y por la asimetría del payoff) y exigir que la cartera mezcle ambos, con un tope a la parte de riesgo en estrategias convergentes y un test de cola más estricto para ellas (su OOS es el que más probablemente se saltó «el octavo año»).

**Estado.** NUEVA (cartera) — **Tipo.** cartera — **Locura.** 0 — **Valor.** 3

#### Tamaño por convicción frente a tamaño igual
**Fuente.** schwager_nmw, p. 48 (Eckhardt); schwager_mw, p. 20 (Marcus); schwager_smw, p. 166 (Cohen).

**Qué dice.** Eckhardt: cada operación a tamaño completo o nada, y «los traders de gráficos ponen más tamaño en las que les gustan: mala idea». Marcus hizo todo su beneficio en las operaciones que cumplían todos sus criterios, con 5 o 6 veces el tamaño. Las ganancias de Cohen vienen del 5 % de sus operaciones, grandes.

**Qué significaría aquí.** El módulo de cartera se lo encontrará: el tamaño por convicción solo es legítimo si una nota medible (por ejemplo el número de estrategias en confluencia) predice el P&L fuera de muestra. Si no, tamaño igual.

**Estado.** NUEVA (cartera) — **Tipo.** cartera — **Locura.** 1 — **Valor.** 3

#### Rotación por fuerza relativa entre estrategias y mercados
**Fuente.** katsanos_intermarket, p. 264-277; newfrontiers_ta, p. 49-83; schwager_nmw, p. 95 (Blake).

**Qué dice.** Katsanos: fuerza relativa frente al S&P suavizada 150 días cruzando su media de 120, con más filtros, y salida con fuerza relativa bajo su media de 90; 2000-07, cartera de futuros PF 10,45 y Sharpe 2,3 frente a 0,1 de la diversificada estática; los stops perjudicaron. Gráfico de rotación relativa (RRG): RS-Ratio frente a RS-Momentum, los elementos giran de líder a debilitándose a rezagado a mejorando. Blake: tener solo la luz verde más brillante y liquidez si todas están en rojo.

**Qué significaría aquí.** Una capa de rotación sobre los 9 mercados de _markets.yaml o sobre el grupo de estrategias vivas: la misma señal evaluada en todos, capital al de mejor (volatilidad × fiabilidad reciente), condicionada a que se confirme la persistencia de resultados (ver «¿Persisten los resultados de las estrategias o revierten?»). Un RRG del grupo de estrategias como vista de vigilancia.

**Estado.** NUEVA (cartera) — **Tipo.** cartera — **Locura.** 1 — **Valor.** 2

#### Diversificar por estrategias, timeframes y efectos
**Fuente.** schwager_nmw, p. 65-66 (Trout), p. 154 (Yass); chan_quantitative, p. 153-154; katz_encyclopedia, p. 271-272; web: MinervaScore (https://arxiv.org/pdf/2608.23808); web: Build Alpha, biology-robust (https://www.buildalpha.com/biology-robust-trading/); covel_trendfollowing, p. 70-71.

**Qué dice.** Trout lleva docenas de modelos a la vez, el mismo patrón en datos horarios, diarios y semanales. Yass: diversificar y luego apalancar hasta el riesgo de una posición no diversificada probablemente rinde más. Chan: las carteras de beta baja tienen más Sharpe; risk parity de Qian 23/77 a 1,8x. Katz: estrategias de eventos raros (43 trades en 10 años en 36 mercados) que solo valen en cartera. Build Alpha: redundancia por EFECTO, muchas estrategias por efecto. Covel cuenta meses con signo frente al S&P (96 ambos positivos, 150 opuestos, 41 ambos negativos) en vez de dar ρ.

**Qué significaría aquí.** Los hermanos reescalados que sobreviven a crossTF también son diversificadores a operar juntos, no solo una comprobación. Construir la cartera por efectos (varias estrategias por efecto, varios efectos) y asignar por contribución al riesgo. En el paso de exposición, la tabla 2x2 de signos mensuales y el recuento de «ambos negativos»: los meses en que la estrategia no diversifica al subyacente.

**Estado.** AMPLÍA (crossTF para cartera; exposure) — **Tipo.** cartera — **Locura.** 0 — **Valor.** 2

#### Dar más peso a lo que lleva más tiempo sobreviviendo fuera de muestra
**Fuente.** taleb_fooled, p. 55-56, 163-164.

**Qué dice.** Pasados los 40, pocas dolencias te matan: la esperanza de vida condicional crece con la edad alcanzada; seleccionar por años de exposición condicionados a sobrevivir.

**Qué significaría aquí.** Al repartir entre estrategias vivas, ponderar por el tiempo sobrevivido fuera de muestra (paper y vivo), no solo por el rendimiento reciente; y probar en el ledger si la vida restante del edge es mayor en familias que ya sobrevivieron más. Necesita años de datos en vivo.

**Estado.** AMPLÍA (vida media del edge, aceptada) — **Tipo.** cartera — **Locura.** 2 — **Valor.** 2

### 5.10 · Operación en vivo: incubación, vigilancia y retirada

#### Condiciones de retirada preregistradas y sacadas de su propia distribución
**Fuente.** taleb_fooled, p. 101-107; covel_trendfollowing, p. 41-44, 108-110; abraham_tfbible, p. 5, 88-89; web: Robot Wealth, «A quant's approach to drawdown» (https://robotwealth.com/a-quants-approach-to-drawdown/).

**Qué dice.** Los datos pueden refutar, nunca confirmar; «un trader sin un punto que le haga cambiar de opinión no es un trader». Dunn perdió un 27,1 % (1976) y un 32 % (1981) y luego ganó +500 % y +300 %; tras un -42 % en 12 meses su mayor cliente retiró el 70 %, y el mes siguiente fue +18 % y los 36 siguientes +430 %. JWH: 4 meses del valle al nuevo máximo tras caídas del 20-30 %. Abraham compra gestores en drawdown. Robot Wealth: comparar el drawdown vivo con la distribución de drawdowns esperada dada la propia distribución de rentabilidades y la duración, no con el máximo del backtest.

**Qué significaría aquí.** Cuando un superviviente pasa a paper o vivo, escribir en su manifiesto los hechos observables que lo refutarían (esperanza de 6 meses bajo el percentil 5 de su OOS, drawdown más allá del percentil 99 del MC, que la ablación de la condición fija deje de importar con datos frescos), congelados en el ledger como un umbral, antes del primer trade. El módulo vivo solo comprueba esas condiciones y el certificado imprime «el drawdown a partir del cual está rota con un 95 %». Nada se decide sobre la marcha.

**⚠ Contradice.** Una fábrica que retira estrategias que decaen puede vender en el fondo: decaimiento y drawdown normal se parecen en tiempo real (covel_trendfollowing p. 41-44, 108-110; abraham_tfbible p. 5, 88-89).

**Estado.** AMPLÍA (umbrales congelados y ledger existen; las condiciones de retirada por estrategia son nuevas) — **Tipo.** vivo — **Locura.** 0 — **Valor.** 4

#### Reconciliar cada día el vivo con el backtest
**Fuente.** chan_quantitative, p. 89-91, 108; schwager_nmw, p. 61 (Seidler), p. 110 (Basso); web: QuantConnect, reconciliation (https://www.quantconnect.com/docs/v2/cloud-platform/live-trading/reconciliation); web: auditoría de fills en vivo (https://www.mql5.com/en/forum/482148).

**Qué dice.** Comparar los trades del paper con el programa de backtest ejecutado sobre los mismos datos recientes; toda diferencia no explicada por coste o retraso es un fallo. Si el vivo rinde menos, en este orden: fallos, ¿coinciden los trades?, ¿coste mayor del modelado?, iliquidez; solo después data snooping (probarlo quitando reglas: si el backtest se hunde, estaba fisgado) y cambio de régimen. Seidler: a corto plazo, cumplir el plan importa más que la equity. Basso perdió una señal de plata por una visita familiar: 30.000 $ por contrato en una cuenta de 5.000 $. Una auditoría de 50.000 fills FX reales: slippage asimétrico y de cola gruesa, según sesión, profundidad y enrutado; el XAUUSD salta 40 puntos a través de los stops en la apertura de Londres; el slippage del tester de MT5 es un retraso de milisegundos, sin sentido.

**Qué significaría aquí.** La reconciliación de translate es la mitad offline. La mitad viva: un trabajo diario que rehace el backtest sobre los días operados y lo compara con el historial de deals de MT5, con la lista ordenada como veredicto; un monitor de señales perdidas (cada señal que el backtest tomaría sobre barras vivas debe tener su orden, y profitShape ya dice lo fatal que es perder una); y una tabla de fills vivos para ajustar un modelo de slippage por sesión y ventana de noticias.

**Estado.** AMPLÍA (reconciliación de translate; la mitad viva sin construir) — **Tipo.** vivo — **Locura.** 0 — **Valor.** 4

#### Vigilancia secuencial: métricas móviles contra la banda propia, sin mirar de más
**Fuente.** cmt_complete2, p. 576-577; williams_longterm, p. 167-168; schwager_nmw, p. 117 (Raschke); web: BOCPD en MQL5 (https://www.mql5.com/en/articles/23482); web: PSR en vivo (https://www.quantconnect.com/research/17112/probabilistic-sharpe-ratio/); web: CME, Backtesting de Harvey (https://www.cmegroup.com/education/files/backtesting.pdf); web: LuxAlgo, live decay tracking (https://www.luxalgo.com/library/concept/live-decay-tracking/); web: conformalrisk (https://github.com/WatchTree-19/conformalrisk).

**Qué dice.** Bryant: factor de beneficio de las últimas 20 operaciones con su media y un t-test contra el historial; suma de las últimas 30 siempre positiva; z-test del porcentaje de aciertos reciente; test de rachas. Williams: «la señal más segura de que un sistema falla es una racha de pérdidas mayor que las vistas antes». BOCPD (detección bayesiana de cambios en línea): la posterior de la longitud de racha colapsa ante una ruptura en media o varianza. PSR (Sharpe probabilístico) en vivo: P(Sharpe vivo ≥ Sharpe del backtest × descuento), y apagar si el PSR de «Sharpe verdadero > 0» baja de un suelo fijado. El SPRT de Wald (test secuencial de razón de probabilidades) da la decisión más rápida con errores fijados. La predicción conformal da bandas con cobertura garantizada en muestra finita. Raschke: las posiciones pequeñas se descuidan y causan las mayores pérdidas.

**Qué significaría aquí.** El panel del módulo vivo: las métricas móviles de cada estrategia dentro de su banda OOS (no IS), con tests secuenciales (CUSUM, SPRT, BOCPD) en lugar de «t-test de las últimas 20», que infla el error por mirar repetidamente. La racha perdedora viva contra la ley binomial de longitud de rachas dado su porcentaje de aciertos (no hace falta barajar). Alarmas automáticas uniformes para todas las estrategias, sin depender de la atención.

**Estado.** NUEVA (módulo vivo sin construir) — **Tipo.** vivo — **Locura.** 0 — **Valor.** 4

#### Seguir en sombra las estrategias retiradas: la regresión a la media engaña a toda «mejora»
**Fuente.** schwager_nmw, p. 158-159 (Faulkner); chan_quantitative, p. 109-110.

**Qué dice.** Tras un periodo inusualmente malo, el siguiente probablemente es mejor pase lo que pase: «si el trader cambia de sistema cuando peor le va, lo más probable es que mejore aunque el nuevo sea igual o peor, y atribuirá la mejora al sistema nuevo». Chan: tras una gran pérdida, los traders cambian los parámetros para que esa pérdida no hubiera ocurrido, y así invitan a la siguiente.

**Qué significaría aquí.** Regla de proceso para la fábrica: todo cambio disparado por malos resultados recientes (un filtro nuevo, un retoque de plantilla, sustituir una estrategia viva que decae) se evalúa contra un control NO cambiado en el mismo periodo siguiente, nunca contra el periodo malo que lo disparó. Seguir en sombra las estrategias retiradas: una retirada en su peor drawdown «se recuperará» en sombra, y así se mide. Todo cambio a una estrategia en vivo es una prueba nueva del ledger.

**Estado.** NUEVA (proceso; amplía vida media del edge) — **Tipo.** proceso — **Locura.** 0 — **Valor.** 4

#### El bróker también es una posición: riesgo de contraparte
**Fuente.** abraham_tfbible, p. xiv-xvii, 2, 5.

**Qué dice.** MF Global (2011) congeló las cuentas y «vaporizó» 1.600 millones de fondos segregados; las posiciones no se pudieron cerrar en días. Sobrevivieron quienes tenían el dinero en el Tesoro o repartido entre varios intermediarios; Abraham nunca pone más del 5 % del patrimonio familiar en una idea o gestor y saca el efectivo «al menor olor a humo».

**Qué significaría aquí.** Reglas del módulo vivo: nunca todas las estrategias en un solo bróker; tope de capital por bróker; reserva fuera del bróker; y un simulacro documentado de «el bróker o el terminal no responden 3 días con posiciones abiertas» (exposición en riesgo = suma del riesgo abierto en ese bróker). Los brókers de CFD son contrapartes, no bolsas.

**Estado.** NUEVA (vivo sin construir) — **Tipo.** vivo — **Locura.** 0 — **Valor.** 4

#### Incubación y rampa de tamaño: subir despacio, bajar rápido
**Fuente.** elder_newtfal, p. 151-153, 210-212; web: Davey, incubación (https://bettersystemtrader.com/113-how-good-are-your-entries-and-exits-really/); web: notas sobre Renaissance (https://bagerbach.com/books/the-man-who-solved-the-market/); schwager_smw, p. 143.

**Qué dice.** Elder: empezar a una fracción del tamaño; subir un escalón tras dos periodos rentables y bajar uno tras cualquier periodo perdedor; el paper engaña por fills perfectos y emociones distintas. Davey incuba con datos vivos y sin dinero durante meses. Renaissance permitía señales significativas sin explicación, pero con poco capital al principio. D. E. Shaw dejó la renta fija tras las pérdidas de 1998, de una familia de cola desconocida.

**Qué significaría aquí.** El calendario de despliegue: cada estrategia promovida empieza, por ejemplo, a 1/5 de su riesgo objetivo; subir exige dos periodos seguidos con el P&L vivo Y el slippage vivo frente al backtest dentro de banda (el contraste con el feed del bróker da la segunda prueba); cualquier fallo baja un escalón. Las familias nuevas, más pequeñas hasta ver su cola en vivo. Un «capital de prueba» para señales sin justificación económica es un matiz a la regla de justificar ex ante, a decidir por el dueño. La duración de la incubación sale del MinTRL (sección de drawdown).

**Estado.** AMPLÍA (paper OOS; contraste con el feed del bróker, aceptados) — **Tipo.** vivo — **Locura.** 0 — **Valor.** 3

#### Sobre de previsión de dos lados: salirse por arriba también es una alarma
**Fuente.** tharp_freedom, p. 54-55 (Basso).

**Qué dice.** Basso escribía el mejor y el peor caso de cada escenario (40 % mejor, 10 % peor, 15-25 % medio, 25 % peor drawdown). Un año ganó más del 40 % y lo trató como un fallo del plan: «nuestro riesgo era demasiado alto y también podíamos salirnos por abajo», y recortó el riesgo.

**Qué significaría aquí.** En vivo, un sobre por estrategia desde la distribución OOS o WFM (R mensual, drawdown móvil) con alarma al salir por cualquiera de los dos lados. Salirse por arriba es síntoma de cambio de régimen o de apalancamiento oculto tanto como por abajo.

**Estado.** NUEVA (vivo sin construir) — **Tipo.** vivo — **Locura.** 1 — **Valor.** 3

#### Mirar el vivo a baja frecuencia
**Fuente.** taleb_fooled, p. 56-59 (Tabla 3.1).

**Qué dice.** Una estrategia de 15 % de rentabilidad y 10 % de volatilidad sube el 93 % de los años, el 67 % de los meses, el 54 % de los días y el 50,02 % de los segundos. Ruido/señal de 0,7 al año, 2,32 al mes y 30 a la hora; mirar a alta frecuencia solo enseña varianza y agota al operador.

**Qué significaría aquí.** La vista viva de la ventana arranca en P&L mensual contra la banda esperada, no en P&L por tick; las decisiones de retirada solo se toman a fin de mes contra bandas precalculadas. Para cada estrategia, P(positivo) a 1 día, 1 semana, 1 mes y 1 trimestre desde su OOS, junto al número vivo.

**Estado.** NUEVA (vivo sin construir) — **Tipo.** vivo — **Locura.** 0 — **Valor.** 3

#### Separar el decaimiento de la estrategia del de su mercado
**Fuente.** web: decay de estrategia frente a decay del mercado (https://skills.himanshujangir.com/skills/strategy-performance-decay-detection-vs-market-wide-decay/); web: Liu, arXiv 2604.18821 (https://arxiv.org/abs/2604.18821).

**Qué dice.** Comparar el vivo con las bandas de variabilidad del propio backtest, con bootstrap por bloques para distinguir decaimiento de ruido y p-valores de ruptura estructural. Si todas las estrategias de un activo se degradan a la vez, es régimen, no la estrategia. Liu: 1.726 estrategias estructuradas de 10 instituciones pasan mal al vivo y se debilitan mucho frente a sus PARES; los backtests reflejan sobre todo el régimen común antes del lanzamiento.

**Qué significaría aquí.** En el panel vivo, comparar cada estrategia con las demás del mismo activo y periodo (y con sus monos), no con cero: una estrategia que solo ganó a cero cuando todas las de oro ganaban es régimen. Evita retirar una estrategia sana por un mal momento del mercado, o quedarse con una que solo iba con la ola.

**Estado.** NUEVA — **Tipo.** vivo — **Locura.** 0 — **Valor.** 3

#### Volver a admitirla cada trimestre como si fuera nueva
**Fuente.** taleb_fooled, p. 186-188.

**Qué dice.** Las creencias dependen del camino; la prueba es si comprarías hoy la posición: «si no tuvieras el cuadro, ¿lo comprarías al precio actual?».

**Qué significaría aquí.** Cada trimestre, pasar los datos frescos desde el lanzamiento de cada estrategia viva por los mismos umbrales del gate que a un candidato nuevo (con el paper OOS como muestra nueva); si hoy no la admitiría, se retira, por mucho apego que haya. Va con las condiciones de retirada preregistradas.

**Estado.** AMPLÍA (paper OOS y vida media del edge, aceptados) — **Tipo.** vivo — **Locura.** 0 — **Valor.** 3

#### La lista de preguntas críticas como última página del dosier
**Fuente.** covel_trendfollowing, Apéndice G p. 395-396.

**Qué dice.** 14 preguntas: mayor drawdown real y simulado y peor día; meses perdedores seguidos; frecuencia de drawdowns; cortos o graduales; recuperación media y más larga; riesgo por operación cuantificado; circunstancias para parar; mercados donde falla siempre y por qué; velocidad de adaptación a la volatilidad; manejo de latigazos; regla de parar y reanudar; principios del stop; beneficio de diversificación.

**Qué significaría aquí.** Casi todas las respuestas están repartidas por los estudios; lo nuevo es forzar una respuesta explícita a «¿cuándo la paramos?» y «¿dónde falla y por qué?» (los fallos del cross-market) antes de que salga del pipeline. Una página del dosier rellena sola donde hay datos y marcada «sin respuesta» donde no.

**Estado.** AMPLÍA (veredicto del pipeline) — **Tipo.** proceso — **Locura.** 0 — **Valor.** 3

#### No anular la estrategia a mano, y si se hace, puntuarlo
**Fuente.** schwager_nmw, p. 50 (Eckhardt), p. 136 (J. Ritchie); covel_completeturtle, p. 129-133; williams_longterm, p. 128.

**Qué dice.** Eckhardt operaba su cuenta con anulaciones y la de un socio de forma mecánica a la vez: la mecánica fue mejor; las anulaciones que «ganan al sistema» se recuerdan y el coste diario de anular se olvida. En abril de 1988 Dennis perdió un 55 % con su capa discrecional y sus alumnos, que seguían las reglas, un 10-12 %. Williams: «tómalas todas», si escoges, escoges las perdedoras. Joe Ritchie: llevar una idea direccional en una cuenta aparte para separar los resultados.

**Qué significaría aquí.** En vivo, ninguna anulación; si el dueño anula, registrar cada anulación como sombra y comparar sombra contra real cada mes. Donde se pueda, llevar cada canal (largos y cortos, por ejemplo) como estrategias con libro propio, para que la atribución siga en vivo.

**Estado.** NUEVA (registro de anulaciones en vivo; el proyecto ya es sistemático) — **Tipo.** vivo — **Locura.** 0 — **Valor.** 2

#### Que el bróker no pueda leer tus órdenes
**Fuente.** faith_turtle, p. 155-157, 262-263, 268-272.

**Qué dice.** Un sistema popular cuyas órdenes a la apertura siguiente eran predecibles fue adelantado hasta su peor drawdown en 20 años. Los Turtles usaban límites, nunca dejaban stops en el bróker, a veces mandaban órdenes señuelo y variaban el momento de entrada; en mercados rápidos esperaban a que se estabilizara en vez de ir a mercado.

**Qué significaría aquí.** En el enlace MT5: aleatorizar la ejecución en una ventana pequeña alrededor de la apertura de barra, evitar órdenes pendientes en niveles redondos o de canal visibles para el bróker, y medir el slippage por tipo de orden en el registro vivo para devolverlo a los costes por tarea. Importa más con brókers de CFD que ven el libro.

**Estado.** NUEVA (vivo sin construir) — **Tipo.** vivo — **Locura.** 1 — **Valor.** 2

#### Pausar el sistema durante las crisis personales del operador
**Fuente.** tharp_freedom, p. 247-249, 262-263.

**Qué dice.** Cerrar posiciones durante un divorcio, un duelo, un nacimiento, una mudanza, agotamiento, euforia o viajes.

**Qué significaría aquí.** Un interruptor manual «operador no disponible» en el módulo vivo que aplana o congela entradas nuevas y, sobre todo, registra lo que las estrategias habrían hecho durante la pausa, para que el dueño aprenda lo que cuesta pausar.

**Estado.** NUEVA (vivo) — **Tipo.** vivo — **Locura.** 1 — **Valor.** 1

### Las de locura 3 de esta sección
Ninguna entrada de esta sección llega a locura 3; las más raras (locura 2) son: Si el slippage medio es a favor, retrasa la orden · Inflar la comisión durante el build · No poner el stop donde lo pone todo el mundo · Techo de apalancamiento con visión perfecta · Meta-labeling: un segundo modelo que decide el tamaño · Confluencia: estrategias que no pagan sus costes pueden pagarlos cuando coinciden · Dar más peso a lo que lleva más tiempo sobreviviendo fuera de muestra.

## 6 · Proceso, cultura e interfaz

Esta sección recoge cómo trabajar, cómo registrar y cómo mirar: el pre-registro de cada idea antes de gastar CPU, qué más debe contar el ledger además de lo que SQX prueba, cómo medir la propia fábrica, la reproducibilidad, la psicología del investigador y todas las ideas de interfaz para la ventana.
Las tres que considero más valiosas: **contar como ensayo todo retoque humano y toda capa añadida** (el Sharpe deflactado solo es tan honesto como su N), **la tarjeta de hipótesis con predicción y criterio de muerte escrita antes del build** (con un diff automático entre lo prometido y lo ejecutado), y **la etiqueta de procedencia de cada idea** (las ideas sacadas de libros, incluida esta misma lista, llegan preseleccionadas y deben pagar una penalización).
En interfaz, la pieza más rentable ya es construible hoy con datos en disco: la ficha de rendimiento de una estrategia (caídas, meses, salidas por motivo).

### 6.1 · Pre-registro: escribir antes de mirar

#### Predicción falsable y criterio de muerte antes de cada build, y calibración de quien predice
**Fuente.** aronson_ebta, p. 47, 52-53, 58-59, 64-66; covel_completeturtle, p. 183-184 (el test de calibración de Eckhardt); web: pre-registro con diff plan contra ejecución (https://github.com/azizruziboev/quant-research-showcase ; https://pmc.ncbi.nlm.nih.gov/articles/PMC11874590/ ; https://www.quantconnect.com/announcements/16153/solving-the-replication-crisis-in-finance/); web: protocolo Arnott-Harvey-Markowitz (https://people.duke.edu/~charvey/Research/Published_Papers/P138_A_backtesting_protocol.pdf).

**Qué dice.** Los meteorólogos y los apostadores de carreras están calibrados porque hacen predicciones probabilísticas explícitas y reciben respuesta rápida. Una predicción sirve si dice de antemano qué resultado cuenta como error y cuándo se juzga. El analista que decide solo cuándo dejar de buscar siempre encuentra una regla buena. Eckhardt pedía intervalos del 90 % a diez preguntas y la mayoría fallaba 4-5 de 10: exceso de confianza. En la web, la mayoría de estudios pre-registrados hicieron cambios no declarados, así que el pre-registro solo funciona si el sistema compara plan y ejecución de forma automática. El protocolo AHM tiene 7 bloques: motivación económica ex ante, tests múltiples, datos y muestra, validación cruzada, dinámica, complejidad y cultura.

**Qué significaría aquí.** Antes de cada build de plantilla, una fila del ledger con: fracción esperada que pasa la puerta, p mediana esperada contra el mono, intervalo del 90 % del número de supervivientes y el criterio de muerte ("si sobreviven menos de X en el paso 8, la familia está muerta"). Tras la corrida el ledger puntúa la predicción (Brier o log score) y acumula un historial de calibración del dueño y, más adelante, del metamodelo. El paso 20 imprime el diff entre la tarjeta y lo que de verdad se corrió. Da además una regla de parada por familia, para no reconstruirla con retoques hasta que algo pase.

**Estado.** AMPLÍA (el ledger registra N ensayos; nada registra predicciones ni criterios de muerte antes de la corrida) — **Tipo.** proceso — **Locura.** 1 — **Valor.** 4

#### Tarjeta de mecanismo: quién paga y dónde no debería funcionar
**Fuente.** aronson_ebta, p. 332-333, 381-386; covel_trendfollowing, p. 115-120, 271-272 (Harris, Druz, Andrew Lo); schwager_nmw, p. 65 (Trout), p. 51 (Eckhardt: "sé promiscuo al investigar, no al operar"); schwager_smw, p. 143, 145, 167 (Shaw, hipótesis primero); web: protocolo AHM (enlace arriba); web: Renaissance según Zuckerman (https://bagerbach.com/books/the-man-who-solved-the-market/).

**Qué dice.** Un backtest rentable sin teoría es un resultado aislado y quizá de suerte. Mejor los edges explicados como pago por un servicio (transferencia de riesgo, liquidez), que duran más que las ineficiencias. Kestner 1990-2001: tendencia con Sharpe 0,604 en 29 futuros contra 0,046 en 31 acciones. Druz: "sabe a quién le vas a quitar el dinero". Lo: toda estrategia se describe por su valor añadido; "nunca verás un backtest malo". Trout escanea todo mercado por todo retardo y luego tira lo que no tiene sentido (la libra de hace 40 días prediciendo el S&P). Shaw parte de una hipótesis estructural y lo más común es no poder rechazar la eficiencia.

**Qué significaría aquí.** Campo obligatorio en cada plantilla de la librería: qué prima o sesgo cosecha (presión de coberturistas, provisión de liquidez, infrarreacción a noticias, anclaje), quién pierde y la predicción que implica ("funciona en oro y Brent, no en índices"; "falla en el tercil de baja volatilidad"). Los pasos de cross-market y el mapa condicional pasan a ser una prueba de esa predicción, no un informe. La tabla de rendimiento del ledger se puede cortar por mecanismo, y medir si las familias con mecanismo sobreviven más que las que no lo tienen, lo que convierte "tener sentido" en un prior medido. Encaja con la regla 11 del proyecto (lo ambiguo se pregunta) en el primer eslabón.

**⚠ Contradice.** Renaissance permitía señales significativas sin explicación, con capital pequeño de prueba al principio (web, Zuckerman). Es un matiz a la regla pura de "sin mecanismo no hay plantilla": el dueño decide si admite un carril de "capital a prueba" para señales sin razón.

**Estado.** NUEVA (las plantillas llevan lógica, no mecanismo) — **Tipo.** proceso — **Locura.** 1 — **Valor.** 4

#### Declarar antes el universo y la regla de paso; toda exclusión posterior cuenta como ensayo
**Fuente.** aronson_ebta, p. 132-141; katsanos_intermarket, p. 218, 233; katz_encyclopedia, p. 356-359.

**Qué dice.** Explicar un fracaso solo es legítimo si la explicación hace una predicción nueva que luego se confirma (Neptuno). Inventar la razón después de ver el resultado vacía la hipótesis ("inmunización frente a la falsación"). Katsanos eligió líderes por vínculo económico y evitando espejos mecánicos (el Euro Stoxx comparte 13 acciones con el DAX). Katz montó una cartera "elegida por significación in-sample" que daba 625 %/año fuera de muestra, pero varias elecciones se justificaban por lo ya visto fuera de muestra.

**Qué significaría aquí.** La lista de mercados y la regla de paso de crossmarket, crossTF y WFM ya están fijadas antes (`_markets.yaml`). Falta que toda exclusión posterior de un mercado o de una celda ("la plata es distinta") se escriba como predicción a comprobar en datos no leídos, o se registre en el ledger como ensayo adicional. Para la familia lead-lag: una lista `leaders` por activo principal, declarada antes de mirar, sin patas de un mismo triángulo de divisas. Toda selección de mercados a partir de una matriz ya vista es una búsqueda y va al ledger.

**Estado.** AMPLÍA (los mercados están predeclarados; las exclusiones posteriores no cuentan como búsqueda) — **Tipo.** proceso — **Locura.** 0 — **Valor.** 3

#### Condición de falsación congelada al promover una estrategia
**Fuente.** taleb_fooled, p. 101-107.

**Qué dice.** Los datos pueden refutar, nunca confirmar. Una teoría sin condición bajo la cual sea falsa es charlatanería. "Un trader que no tiene un punto que le haría cambiar de opinión no es un trader."

**Qué significaría aquí.** Cuando una superviviente pasa a papel o a vivo, su manifiesto recoge los hechos observables que la falsarían ("expectativa móvil de 6 meses bajo el percentil 5 de su distribución OOS", "drawdown más hondo que el percentil 99 del MC", "la ablación de la condición fija deja de importar en datos nuevos"), congelados en el ledger como un umbral, antes de la primera operación. El módulo en vivo solo comprueba esas condiciones y nada se decide sobre la marcha.

**Estado.** AMPLÍA (umbrales congelados y ledger existen; las condiciones de muerte por estrategia son nuevas) — **Tipo.** proceso — **Locura.** 0 — **Valor.** 4

#### Una tarjeta de objetivos por familia de activos de la que salgan todos los umbrales
**Fuente.** tharp_freedom, p. 47-57, 66; fitschen_reliable, p. 1-5.

**Qué dice.** Un asignador de CTAs aconseja dedicar al menos la mitad del desarrollo a los objetivos: rentabilidad objetivo, drawdown máximo tolerable, cuánto dura un drawdown aceptable (más del 15 % o más de un año es "mortal" para los clientes de Basso), riesgo por operación 0,8-1 %, capacidad. Fitschen define "operable" así: rentabilidad anual mayor que el drawdown máximo, rentabilidad múltiplo del drawdown máximo anual medio, y un tiempo máximo entre máximos de equity. "Pocos traders aguantan un drawdown del 20 %."

**Qué significaría aquí.** Escribir una vez, por familia de activos, la tarjeta (R/año objetivo, DD máximo, duración máxima del DD, operaciones mínimas al año) y derivar de ella los filtros del build y los umbrales de la puerta, para que la puerta no sea un montón de números sin relación.

**Estado.** AMPLÍA (`ledger/thresholds.yaml` congela umbrales; aquí se atan a un objetivo declarado) — **Tipo.** proceso — **Locura.** 0 — **Valor.** 2

#### Umbrales desde el coste de cada error, no desde el 5 % de costumbre
**Fuente.** aronson_ebta, p. 233-234; covel_completeturtle, p. 67.

**Qué dice.** Aronson: el falso positivo expone capital sin compensación y el falso negativo solo pierde una oportunidad, así que el test debe inclinarse contra el error de tipo I. A las Tortugas les enseñaron lo contrario: mejor muchas pérdidas pequeñas que perder una gran tendencia (el falso negativo cuesta más). Las dos fuentes discrepan sobre qué error es caro.

**Qué significaría aquí.** Las dos cosas son ciertas en sitios distintos: en la selección de estrategias (Aronson) y dentro de una estrategia que ya opera (Tortugas). Para la puerta: declarar un cociente de costes entre rechazar un edge real y aceptar uno falso, y con las curvas de potencia con edge plantado (ya aceptadas) elegir el q de BH y el percentil del mono por cálculo, no por convención.

**Estado.** AMPLÍA (curvas de potencia aceptadas; falta el cociente de costes que las convierte en umbral) — **Tipo.** proceso — **Locura.** 1 — **Valor.** 3

### 6.2 · El ledger: contar todo lo que se prueba

#### Todo retoque humano es un ensayo, también los grados de libertad escondidos
**Fuente.** katz_encyclopedia, p. 31-32; chan_quantitative, p. 53; williams_longterm, p. 61-71, 207; schwager_nmw, p. 48 (Eckhardt); taleb_fooled, p. 113-115, 128-130, 134-136.

**Qué dice.** Katz: quien prueba, retoca y vuelve a probar quedándose con lo mejor ha optimizado aunque no corriera ningún optimizador. Chan: abrir en la apertura o al cierre, dormir la posición o no, qué universo, elegidos a base de backtests, son snooping igual que los parámetros. Williams elige días de la semana por lado sobre los mismos datos: 5 días por 2 lados son 2^5 = 32 subconjuntos por lado, no uno; y tras un año de 50 k a 1 M "siguió criando" el sistema y lo arruinó. Eckhardt: las alternativas estructurales probadas son grados de libertad ocultos. Taleb: el que va cambiando 1,83 % a 1,2 % encuentra la regla superviviente.

**Qué significaría aquí.** El ledger cuenta las búsquedas de SQX. Debe contar también cada iteración idea → bloque → re-corrida como ensayo de la misma familia, cada horquilla del investigador (activo, TF, sesión, tipo de salida probados y abandonados) y cada subconjunto elegido a mano (días, horas). Sin eso el Sharpe deflactado subestima N.

**Estado.** AMPLÍA (`ledger/trials.py` cuenta búsquedas de SQX, no las del humano) — **Tipo.** proceso — **Locura.** 0 — **Valor.** 4

#### Las capas añadidas también son sistemas: especificarlas antes y contarlas
**Fuente.** schwager_mw, p. 82 (Seykota).

**Qué dice.** "Si tuvieras una política de modificación M exitosa para el sistema S, quizá te iría mejor operando M."

**Qué significaría aquí.** Cada capa (filtro de volatilidad, regla de ir plano en fechas, tamaño según la curva de equity, cortacircuitos) se especifica antes de probarla, se prueba fuera de muestra como una estrategia y cuenta como ensayo en el ledger. Si no, la etapa de capas y de cartera se convierte en una búsqueda sin contar.

**Estado.** AMPLÍA (el ledger no conoce las capas) — **Tipo.** proceso — **Locura.** 0 — **Valor.** 4

#### Etiqueta de procedencia: las ideas de libros llegan preseleccionadas
**Fuente.** aronson_ebta, p. 390-391, 449-451; chan_quantitative, p. 53-55; taleb_fooled, p. 131-136; schwager_smw, p. 107-108, 140, 168-169 (Lescarbeau, Shaw); schwager_mw, p. 50 (Dennis, en contra); cmt_complete2, p. 173-174; faith_turtle, p. 105-106, 152-158; williams_longterm, p. 104, 113, 117-120, 128; schwager_nmw, p. 49, 51, 55-56; web: McLean-Pontiff (https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2156623 ; https://arxiv.org/pdf/2512.11913).

**Qué dice.** Una regla publicada llega elegida entre una búsqueda de tamaño desconocido, y meterla en tu búsqueda hace su p-valor incognoscible (la regla 9:1 de Zweig es significativa solo si Zweig no minó sus tres parámetros). Chan: todo el periodo desde la publicación es fuera de muestra genuino para la idea. El efecto enero funcionó más del 90 % de los años desde 1920 y falló seis años seguidos tras publicarse; el efecto lunes se fue desvaneciendo en tres décadas. McLean-Pontiff: las anomalías rinden un 26 % menos fuera de muestra y un 58 % menos tras publicarse. De ~50 sistemas comerciales, uno tenía valor; un 98 % de lo que se ve bien en un gráfico no funciona. Los sistemas más imitados (cruce de medias, RSI 30/70, Donchian 20) mueren antes. En contra, Dennis: "podrías publicar las reglas en el periódico y nadie las seguiría".

**Qué significaría aquí.** La columna `origin` del registro de plantillas ya existe (hoy vale "authored"). Ampliarla a propia / libro / foro / paper, con fecha de publicación y marca de "bloque de manual". Tres usos: penalización de N o prior recortado (esperar que lo publicado pierda de un tercio a la mitad) en el deflactado; los datos posteriores a la publicación como OOS gratis para la idea, no para los parámetros ajustados por SQX; y medir en el ledger la caída de lo publicado frente a lo original. Los parámetros de una idea de libro se re-derivan enumerando, no se copian. Esta misma lista de ideas es un conjunto de supervivientes.

**Estado.** AMPLÍA (existe la columna `origin` en `AlgoData/templates/registry.csv`; no hay penalización ni fecha) — **Tipo.** proceso — **Locura.** 1 — **Valor.** 4

#### Registrar y puntuar cada vez que el dueño corrige un veredicto mecánico
**Fuente.** aronson_ebta, p. 463-470; schwager_nmw, p. 50 (Eckhardt, experimento natural), p. 133-134 (Joe Ritchie); covel_completeturtle, p. 114-126 (carta de Keefer), p. 129-133 (Dennis); williams_longterm, p. 128.

**Qué dice.** Meehl 1954 y sucesores: en 136 estudios las reglas igualan o superan al experto en el 96 %; modelo r = 0,64 contra expertos 0,33 en 9 campos; el experto que retoca la salida del modelo lo empeora; usa 3-5 pistas, es inconsistente y gana confianza con datos irrelevantes. Eckhardt operó su cuenta con correcciones y la de un socio de forma mecánica: ganó la mecánica. CRT tuvo un solo año perdedor, el que casi triplicaron el tamaño a mitad de año tras una racha. Dennis perdió un 55 % en un mes con su capa discrecional mientras sus alumnos perdían un 10-12 %. Asignar capital a las Tortugas a ojo no tuvo relación con su rendimiento. Williams: si eliges qué señales tomar, eliges las perdedoras.

**Qué significaría aquí.** Cuando el dueño corrige un veredicto (mantener una DUDOSA, rescatar lo que mató la puerta, elegir supervivientes a ojo en la ventana), queda en el ledger con su razón, y se puntúa la corrección contra el veredicto mecánico en los datos nuevos siguientes. Con el tiempo responde con datos si mirar curvas ayuda. En vivo: toda corrección se registra como sombra y se compara con la regla intacta cada mes.

**⚠ Contradice.** williams_longterm, p. 77, 245-248: "no es un enfoque 100 % mecánico"; los sistemas se combinan con juicio. Peso bajo: sus propios tests son selección in-sample y la discreción no es comprobable.

**Estado.** NUEVA — **Tipo.** proceso — **Locura.** 1 — **Valor.** 3

#### Medir la población entera que genera SQX, no solo lo que guarda
**Fuente.** aronson_ebta, p. 321-327.

**Qué dice.** El Reality Check de White necesita los rendimientos de todas las reglas probadas; "pocos sistemas de minería guardan esta información valiosa".

**Qué significaría aquí.** Un build de calibración por familia, pequeño, sin filtros de aceptación y con databank enorme, en el custodio. Da el N real, la sigma real de los Sharpe para el deflactado y un panel de rendimientos para un nulo del máximo sobre todo lo que produjo la búsqueda genética. El cociente entre esto y el databank filtrado es un factor de corrección para el ledger.

**Estado.** AMPLÍA (`ledger/trials.py`; snoopingScreen asume que K es la cosecha) — **Tipo.** proceso — **Locura.** 2 — **Valor.** 4

#### Las propuestas del chat de plantillas cuentan como ensayos
**Fuente.** web: "What survives honest evaluation?" (https://arxiv.org/abs/2608.27734); web: AlphaAgent y otros (https://arxiv.org/html/2502.16789v2 ; https://arxiv.org/pdf/2508.06312 ; https://arxiv.org/pdf/2608.12841 ; https://arxiv.org/pdf/2608.31041).

**Qué dice.** Un agente LLM que descubre estrategias solo con herramientas validadas, sin mirada al futuro, registrando cada evaluación y deflactando por número de ensayos: todas las estrategias descubiertas por LLM fallaron la certificación (2 universos, 2 modelos, hasta 100 candidatos, 5 corridas). AlphaAgent mide originalidad por distancia de árbol sintáctico contra lo ya existente y comprueba que el factor corresponde a la hipótesis.

**Qué significaría aquí.** Toda plantilla propuesta por el chat de la ventana pasa por el ledger igual que las de SQX, y cada propuesta cuenta como ensayo. Posible extra: una distancia de originalidad contra la librería y una comprobación de que el bloque dice lo que dice la hipótesis.

**Estado.** NUEVA — **Tipo.** proceso — **Locura.** 1 — **Valor.** 3

#### Un fallo engendra una plantilla nueva, nunca un parche
**Fuente.** chan_algorithmic, p. 91-92, 187-188; chan_quantitative, p. 109-110.

**Qué dice.** GLD-GDX dejó de cointegrar el 14-07-2008 (pico del petróleo, costes de minería); añadir USO la hizo cointegrar otra vez 2006-2012. No añadir reglas a ciegas: buscar una razón y probarla. Y tras una gran pérdida no reajustar para que esa pérdida no hubiera ocurrido: invita a la siguiente.

**Qué significaría aquí.** El mapa condicional sigue siendo descriptivo para seleccionar. Una hipótesis nacida de un fallo se convierte en una plantilla nueva, con su fila de ledger y su familia, probada en datos nuevos. En vivo, todo cambio a una estrategia operada es un ensayo nuevo.

**Estado.** AMPLÍA (proceso, ledger) — **Tipo.** proceso — **Locura.** 0 — **Valor.** 2

#### Cada veredicto lleva el embudo con sus cuentas
**Fuente.** faith_turtle, p. xvii, 47; schwager_nmw, p. 103-104 (Sperandeo).

**Qué dice.** De 1.000 candidatos a Tortuga se entrevistó a 40 y se eligió a 13; entre un tercio y la mitad fracasaron. De 38 alumnos de Sperandeo ganaron 5, que ganaron más de lo que perdieron los otros 33.

**Qué significaría aquí.** Todo veredicto de superviviente imprime las cuentas de cada etapa (construidas → OOS → puerta → … → superviviente), para leerla siempre contra el tamaño del grupo del que salió. La fábrica se mide por rendimiento por ensayo, no por medias.

**Estado.** YA EXISTE en parte (embudo del ledger en la zona Ledger; falta en cada veredicto) — **Tipo.** proceso — **Locura.** 0 — **Valor.** 2

### 6.3 · Medir la propia fábrica (meta-investigación)

#### El retoque tras un mal periodo siempre parece funcionar: comparar contra un control
**Fuente.** schwager_nmw, p. 158-159 (Faulkner); chan_quantitative, p. 109-110.

**Qué dice.** Tras un periodo anormalmente malo, el siguiente suele ser mejor pase lo que pase. El trader que cambia de sistema en lo peor mejorará aunque el nuevo sea igual o peor, y lo atribuirá al sistema nuevo.

**Qué significaría aquí.** Cualquier cambio en el pipeline disparado por malos resultados recientes (un filtro nuevo, un retoque de plantilla, sustituir una estrategia viva que decae) se evalúa contra un control que no cambió en el mismo periodo siguiente, nunca contra el mal periodo que lo disparó. Para la vida media del edge: seguir en sombra las estrategias retiradas, porque una retirada en su peor drawdown "se recuperará" en sombra y eso hay que medirlo.

**Estado.** NUEVA — **Tipo.** proceso — **Locura.** 0 — **Valor.** 4

#### Recorte empírico propio: cuánto cae cada familia de build a OOS, y de OOS a vivo
**Fuente.** cmt_complete2, p. 531, 550 (Hill, Pruitt y Hill 2000); chan_algorithmic, p. 7; web: McLean-Pontiff (enlace arriba).

**Qué dice.** La regla de oficio: espera la mitad del beneficio y el doble del drawdown en vivo. Chan: la mayoría estaría contenta con un Sharpe en vivo mayor que la mitad del backtest.

**Qué significaría aquí.** Sustituir la regla de oficio por el número propio: desde el ledger, la distribución de (métrica oos1 / métrica build) de toda estrategia que pasó los filtros del build, por familia × activo × TF. Cada informe nuevo muestra la métrica del build ya multiplicada por ese recorte, con su dispersión. Luego oos2/oos1 y vivo/oos2 dan la cadena de recortes, y el recorte vivo/backtest por familia se compara con 0,5.

**Estado.** AMPLÍA (ledger, Sharpe deflactado) — **Tipo.** estudio — **Locura.** 0 — **Valor.** 5

#### Brazo A/B: plantillas solo con la condición fija contra fija más hueco aleatorio
**Fuente.** chan_quantitative, p. 26-27; schwager_smw, p. 143, 145.

**Qué dice.** Chan: redes, árboles y algoritmos genéticos "rindieron miserablemente hacia delante"; lo que funciona tiene pocos parámetros, es lineal y con base económica. Shaw: hipótesis primero, no minería a ciegas.

**Qué significaría aquí.** El hueco aleatorio es justo donde Chan dice que vive el sobreajuste. Hacer de la plantilla "una condición fija y cero aleatorias" un brazo de primera clase del experimento, y comparar su rendimiento contra el mono en el ledger con el de la forma actual.

**⚠ Contradice.** chan_quantitative, p. 26-27 y chan_algorithmic, p. xi-xii, 4-7: la búsqueda genética de SQX es exactamente lo que Chan dice que falla.

**Estado.** AMPLÍA (ledger, diseño de plantilla) — **Tipo.** proceso — **Locura.** 1 — **Valor.** 4

#### La función de aptitud de SQX es una variable de investigación
**Fuente.** cmt_complete2, p. 604.

**Qué dice.** Las funciones de aptitud de un algoritmo genético que parecen obvias dan malos resultados porque la evolución explota rarezas poco comunes de los datos.

**Qué significaría aquí.** Misma plantilla, mismos datos, dos o tres funciones de aptitud (beneficio neto, Ret/DD, una métrica de estabilidad), comparar el rendimiento en oos1 contra el mono, registrado en el ledger como una réplica más, igual que la varianza de semilla.

**Estado.** AMPLÍA (varianza de semilla del generador, elección de aptitud) — **Tipo.** proceso — **Locura.** 0 — **Valor.** 3

#### Creencias de profesional convertidas en consultas al ledger
**Fuente.** covel_completeturtle, p. 34-35.

**Qué dice.** El test de selección de las Tortugas tenía 63 afirmaciones verdadero/falso: "nunca te arruinas recogiendo beneficios", "el beneficio medio debe ser 3-4 veces la pérdida media", "un porcentaje muy alto de operaciones debe ser ganador", "promediar a la baja es bueno".

**Qué significaría aquí.** Varias son afirmaciones comprobables sobre la población propia, por ejemplo "las supervivientes con ganancia media / pérdida media ≥ 3 decaen menos fuera de muestra que las de alta tasa de acierto". Una fuente barata de hipótesis pre-registradas para el ledger.

**Estado.** NUEVA — **Tipo.** proceso — **Locura.** 1 — **Valor.** 2

#### Ante la caída del edge, no acortar la ventana de build
**Fuente.** schwager_nmw, p. 53 (Eckhardt); chan_quantitative, p. 25, 52-53 (en contra); schwager_mw, p. 169, 171 (Gelber).

**Qué dice.** Eckhardt: los datos recientes son menos significativos porque hay menos, y los sistemas hechos solo con ellos se apoyan en poco. Chan dice lo contrario: solo los últimos ~10 años son adecuados. Gelber: los clientes perdían porque operaban a un horizonte de días con una investigación hecha a más largo plazo.

**Qué significaría aquí.** Una respuesta tentadora y equivocada a la caída de edges es acortar los segmentos de build; el proyecto debería zanjarlo en su propio ledger, no por doctrina. Y una señal validada a un horizonte no se importa a otro sin revalidar (crossTF comprueba el sentido contrario).

**⚠ Contradice.** chan_quantitative, p. 25, 52-53: "más datos no es más robusto" si el proceso no es estacionario; el proyecto construye sobre ventanas largas.

**Estado.** YA EXISTE (segmentos de build largos); aviso para el trabajo de vida media — **Tipo.** proceso — **Locura.** 0 — **Valor.** 2

### 6.4 · Reproducibilidad

#### Prueba de paridad por indicador entre SQX, Python y MT5
**Fuente.** katz_encyclopedia, p. 139-140; schwager_nmw, p. 141 (Hull); chan_quantitative, p. 107.

**Qué dice.** TradeStation calculaba el %K lento como media exponencial en vez de la media simple de 3 barras, y funciones anidadas devolvían valores erróneos sin avisar: "si hay discrepancias, revisa los indicadores". Hull: un recuento más complicado, aunque más exacto, produce más errores al llevarlo. Chan: que un colaborador reproduzca el backtest por su cuenta, como en la ciencia.

**Qué significaría aquí.** Estocástico, RSI (suavizado de Wilder o simple), ATR, Keltner pueden diferir entre SQX, Python (`/translate`) y MT5. Una prueba dorada por indicador y por bloque (exportación de SQX contra Python contra MT5 sobre las mismas barras) antes del vivo. `/translate` ya reconcilia operaciones; la prueba por indicador es más barata y localiza el fallo. La complejidad tiene así una justificación operativa además de la estadística.

**Estado.** AMPLÍA (`/translate`, pruebas doradas de `tests/`) — **Tipo.** proceso — **Locura.** 0 — **Valor.** 3

#### Cada corrida de estudio como fila de experimento comparable
**Fuente.** web: Two Sigma / W&B (https://wandb.ai/site/articles/architecting-alpha-the-modern-quant-lifecycle/ ; https://youngandcalculated.substack.com/p/how-quant-hedge-funds-actually-build).

**Qué dice.** Tuberías de datos versionadas; un backtest de 2020 se reproduce byte a byte. El registro de experimentos es el sistema de verdad.

**Qué significaría aquí.** Cada corrida ya lleva manifiesto y `config_hash`. Falta el hash de las entradas y la comparación entre corridas en la ventana (qué cambió de config o de datos entre dos resultados).

**Estado.** AMPLÍA (manifiesto, `config_hash`, "reproducir un informe desde su manifiesto" aceptado) — **Tipo.** proceso — **Locura.** 0 — **Valor.** 2

#### Las reglas "canónicas" no son una sola: declarar la variante
**Fuente.** covel_completeturtle, p. 87-92; faith_turtle, p. 260-261.

**Qué dice.** Covel añade unidades cada 1N con tope de 5 y stop de ½N el primer día; Faith, que lo operó, cada ½N con tope de 4 y stops de 2N.

**Qué significaría aquí.** Si se monta un zoo de sistemas canónicos como referencia, cada uno declara su variante, y las diferencias entre fuentes se tratan como incertidumbre de parámetro.

**Estado.** NUEVA (nota de calidad) — **Tipo.** proceso — **Locura.** 0 — **Valor.** 1

### 6.5 · Cultura y psicología del investigador

#### El cementerio de ideas es un producto, no un residuo
**Fuente.** schwager_smw, p. 140-141 (Shaw); web: Man AHL (https://www.man.com/insights/overfitting-and-its-impact-on-the-investor).

**Qué dice.** Shaw: "es tan importante saber qué no funciona como qué sí"; no revela anomalías muertas para que la competencia no se aproveche. "El juego ha terminado para la mayoría de los efectos fáciles." Man AHL: una cultura que premia el fracaso de investigación de calidad sobreajusta menos.

**Qué significaría aquí.** Guardar los resultados negativos con el mismo cuidado que los positivos (el ledger ya lo hace) y mostrarlos en la ventana como salida de primera clase (ver Interfaz). Prior realista: plantillas de un indicador en mayores de divisas líquidas deberían fallar.

**Estado.** YA EXISTE (ledger); la vista es nueva — **Tipo.** proceso — **Locura.** 0 — **Valor.** 3

#### Revisión adversaria independiente antes de promover
**Fuente.** lowenstein_ltcm, p. 233 (epílogo), p. 17-18.

**Qué dice.** La gran debilidad de LTCM fue la ausencia de control independiente de los traders: todos los socios se sentaban en las reuniones de riesgo y todos asentían. Un grupo cerrado subió el apalancamiento mientras el edge encogía.

**Qué significaría aquí.** Antes de pasar una superviviente a papel o a vivo, un agente aparte (o una lista fija que corre el agente auditor) argumenta en contra usando solo el dossier: cobertura de crisis, convexidad, correlación en estrés con lo que ya opera, dependencia del stop, calibración de sus bandas MC. Las objeciones quedan en el manifiesto junto a la decisión del dueño, que sigue decidiendo.

**Estado.** NUEVA — **Tipo.** proceso — **Locura.** 0 — **Valor.** 3

#### La lista de preguntas críticas como última página del dossier
**Fuente.** covel_trendfollowing, Apéndice G p. 395-396.

**Qué dice.** 14 preguntas: DD mayor real y simulado y peor día; más meses perdedores seguidos; frecuencia de DD; recuperación media y máxima; ¿está cuantificado el riesgo por operación?; ¿en qué circunstancias se para?; ¿en qué mercados falla siempre y por qué?; velocidad de adaptación a la volatilidad; reglas de parada y reanudación; beneficio de diversificación.

**Qué significaría aquí.** Casi todas las respuestas existen repartidas entre estudios. Lo nuevo es forzar respuesta explícita a "¿cuándo la paramos?" y "¿dónde falla y por qué?" antes de que salga del pipeline. Una página rellenada sola donde hay datos y marcada "sin respuesta" donde no.

**Estado.** AMPLÍA (veredicto del pipeline) — **Tipo.** proceso — **Locura.** 0 — **Valor.** 3

#### Cultura Renaissance: todos leen todo el código, se cobra por el fondo
**Fuente.** web: Zuckerman, "The Man Who Solved the Market" (https://bagerbach.com/books/the-man-who-solved-the-market/ ; https://www.cnbc.com/2019/11/05/how-jim-simons-founder-of-renaissance-technologies-beats-the-marke).

**Qué dice.** p < 0,01 y luego "¿se puede explicar?"; un único modelo para todos los activos; todo el mundo lee todo el código; bonus sobre el fondo, no sobre el individuo; señales sin explicación admitidas con capital pequeño al principio.

**Qué significaría aquí.** Para una fábrica de una persona con agentes: todos los agentes y sesiones leen el mismo código y el mismo ledger (ya es la regla de una carpeta, una rama), y un carril opcional de "capital a prueba" para lo significativo sin mecanismo, a decidir por el dueño.

**Estado.** YA EXISTE en parte (una carpeta, una rama) — **Tipo.** proceso — **Locura.** 1 — **Valor.** 2

#### Apoyo bibliográfico a reglas que el proyecto ya tiene
**Fuente.** aronson_ebta, p. 186-188, 316-319; katz_encyclopedia, p. 45, 124; chan_quantitative, p. 107, 109-110, 157-162; schwager_nmw, p. 49, 128, 147; williams_longterm, p. 207; taleb_fooled, p. 113-115; fitschen_reliable, p. 161-165.

**Qué dice.** OOS se gasta una vez y el walk-forward da varianza (Aronson); la población de rendimientos es un futuro finito, lo que apoya el horizonte de validez de cada veredicto; estadísticos in-sample corregidos por tests múltiples y OOS sin corregir solo cuando es un único test preelegido (Katz; nota: oos1 sobre cientos de estrategias no es un único test, así que BH ahí es correcto y solo oos2 de una madre admite lectura sin corregir); comparar sistemas débiles por operación, no por beneficio neto; la reproducción independiente (`/translate`); no reajustar tras una gran pérdida; el crecimiento viene de más estrategias, no de más apalancamiento; la reoptimización semanal ajusta la semana pasada (Ritchie); la gestión monetaria no rescata un edge negativo (Hull); el sistema "criado" en exceso se arruina (Williams); el mejor de muchos historiales no es habilidad (Taleb); el Monte Carlo barajando operaciones no dice nada útil (Fitschen, apoyo a la postura del dueño).

**Qué significaría aquí.** Citas para el manual y para defender el diseño de la puerta de un solo sentido, los umbrales congelados, el ledger y el MC fuera de la secuencia individual. Nada que construir.

**Estado.** YA EXISTE (puerta de oos2, `ledger/`, `thresholds.yaml`, `/translate`, postura sobre el MC) — **Tipo.** proceso — **Locura.** 0 — **Valor.** 1

#### Ejemplos de manual de por qué mienten los óptimos publicados
**Fuente.** katsanos_intermarket, p. 192-204; cot_bible, p. 130-133, 163-166, 180-181, 190-192, 200-209; katz_encyclopedia, p. 356-359; schwager_nmw, p. 109-110; williams_longterm, p. 61-71.

**Qué dice.** Los 14 sistemas de oro intermercado de Katsanos son todos rentables (PF 2,9-35) pero optimizados sobre toda la muestra, con 16-38 operaciones cada uno, y el coeficiente del dólar derivó de -0,29 a -0,6. La tabla COT "35 de 35 mercados rentables" es el mejor par de medias por mercado, in-sample y sin costes (140 $/operación en oro). Correlaciones de niveles de precio como "Yahoo 0,73 con el yen". El 625 % OOS de Katz con OOS ya mirado. El ejemplo de un artículo era la mejor de 250 celdas mercado-año y 17 de 25 mercados perdían tras costes. Williams elige días y lados sobre los mismos datos.

**Qué significaría aquí.** Un capítulo del manual con estos casos, para explicar al lector por qué existen el ledger, el deflactado y la puerta de oos2. Y una regla: ningún número de estos libros se importa como prior sin re-probarlo.

**Estado.** YA EXISTE (ledger, DSR, puerta de oos2); ejemplos para el manual — **Tipo.** proceso — **Locura.** 0 — **Valor.** 2

#### Priors por hacinamiento: lo menos observado, mejor
**Fuente.** chan_quantitative, p. 27, 157-162.

**Qué dice.** Mejor las estrategias de capacidad demasiado pequeña para las instituciones (demasiado frecuentes, pocos instrumentos, operaciones estacionales raras): esos nichos no se arbitran.

**Qué significaría aquí.** Un prior del ledger que pesa las familias por hacinamiento esperado: CFDs menos concurridos (Nikkei, plata, Brent) y sesiones raras antes que EURUSD H1. Difícil de medir; se apoya en la etiqueta de procedencia.

**Estado.** NUEVA (como prior) — **Tipo.** proceso — **Locura.** 1 — **Valor.** 1

### 6.6 · Interfaz

**Lo que se encargó esta noche.** Siete piezas de esta subsección no cambian ningún módulo de análisis y
leen datos que ya existen en disco. Se encargaron a la sesión que construye la ventana, con criterios de
aceptación y un test por pieza, sin hacer commit:

1. **La ficha de la estrategia**, como primera pestaña de Estrategia. Curva underwater, los cinco peores
   drawdowns con fechas, mapa mensual, barras anuales, consistencia por ventanas de 3 a 24 meses,
   intervalo de Wilson del acierto y concentración en el 5 % mejor de las operaciones.
2. **Equidad y esperanza por tipo de salida**, dentro de la ficha.
3. **Una paleta de comandos con Ctrl+K**, para ir a cualquier zona, estrategia o estudio escribiendo.
4. **El cementerio del ledger**: cada búsqueda registrada, viva o muerta en el paso k.
5. **Los meses contra el subyacente**, una tabla de 2×2 que resalta los meses en que los dos pierden.
6. **Una galería de operaciones por cuantil**, cinco operaciones de los cuantiles 0, 25, 50, 75 y 100 %,
   nunca sólo la mejor.
7. **Las coordenadas paralelas del lote de variantes**, sin ninguna columna de `oos2`.

Las demás entradas de esta subsección necesitan que un estudio calcule algo nuevo, o una decisión tuya, y
no se encargaron. El encargo completo está en `scratch/ui-order-2026-09-27.md`.

#### Ficha de rendimiento de una estrategia (caídas, meses, años, rachas)
**Fuente.** web: tear sheet de quantstats/pyfolio (https://github.com/ranaroussi/quantstats ; https://www.quantrocket.com/codeload/quant-finance-lectures/quant_finance_lectures/Lecture33-Portfolio-Analysis-with-pyfolio.ipynb.html); covel_trendfollowing, p. 70-71, 106-107 (Dunn, Campbell); chan_quantitative, p. 20-21; abraham_tfbible, p. 161-190; fitschen_reliable, p. 1-5, 67-68; katz_encyclopedia, p. 19, 60, 65; schwager_mw, p. 59 (Dennis).

**Qué dice.** La ficha clásica: curva bajo el agua, tabla de las 5 peores caídas con fechas, mapa de calor mensual, barras anuales. Dunn entrega a cada inversor la lista de todas sus pérdidas de más del 25 %: "pasó y volverá a pasar". Campbell 1980-2003: 56 % de meses rentables, 84 % de años, 79 % de ventanas de 12 meses, 100 % de 48 meses. Chan: casi todos los meses rentables implica Sharpe anual mayor que 2; un Sharpe 2 con 55 % de meses positivos apunta a un error o a unas pocas operaciones gigantes. Abraham estuvo 17 meses bajo el agua justo tras arrancar. Fitschen y Katz: el periodo plano más largo es lo que mata psicológicamente; el drawdown máximo anual medio. Katz: 16 aciertos en 47 operaciones dan un intervalo del 99 % de 17 %-53 %. Dennis: el 95 % del beneficio salía del 5 % de las operaciones.

**Qué significaría aquí.** En la zona Estrategia, una ficha calculada por el demonio desde la cosecha (`equity.parquet`, `trades.parquet`): curva bajo el agua, tabla de episodios de caída (profundidad, pico, valle, recuperación, duración), mapa mensual, barras anuales, % de meses y años positivos al lado del Sharpe, periodo plano más largo, ventanas móviles rentables por longitud, intervalo de la tasa de acierto, y cuota del beneficio del 5 % mejor de operaciones con la línea de referencia de Dennis. Todo aritmética sobre datos que ya existen. Prepara al dueño para lo que es un dolor normal antes del vivo.

**Estado.** NUEVA (ninguna vista de la ventana pinta drawdowns ni meses; `profitShape` mide concentración y CUSUM) — **Tipo.** interfaz — **Locura.** 0 — **Valor.** 4

#### Curva de equity por motivo de salida
**Fuente.** elder_newtfal, p. 244-247.

**Qué dice.** El diario de Elder etiqueta cada salida (objetivo, stop, zona de valor, "no va a ninguna parte", "no aguanté el dolor") y pinta una curva por táctica de salida y por fuente de ideas: "cuando ves la curva de 'no aguanté el dolor', nunca vuelves a operar sin stop".

**Qué significaría aquí.** La exportación de operaciones de SQX ya trae `Close type` en `trades.parquet`. Por superviviente: cuántas operaciones, neto, media, acierto y curva por tipo de cierre (señal, objetivo, stop, "Exit After X Bars", fin de sesión). Si las salidas por tiempo pierden en media, la entrada puede estar bien y fallar la regla de mantener. Complementa a `structure`, que ablaciona entradas pero no salidas.

**Estado.** NUEVA — **Tipo.** interfaz — **Locura.** 0 — **Valor.** 3

#### Paleta de órdenes con Ctrl+K
**Fuente.** web: paleta de comandos y Bloomberg (https://github.com/Zenith-options/frontend/issues/37 ; https://corporatefinanceinstitute.com/resources/equities/bloomberg-functions-shortcuts-list/).

**Qué dice.** Todo descubrible desde una línea de órdenes con búsqueda difusa y órdenes recientes; atajos desactivados dentro de los campos de texto; atajos persistentes.

**Qué significaría aquí.** Ctrl+K abre una caja que busca a la vez zonas, proyectos, databanks, estrategias y estudios ("XAUUSD Strategy 17.9.39 profitShape") y lleva allí fijando la selección global. Hoy la ventana no tiene ningún atajo.

**Estado.** NUEVA — **Tipo.** interfaz — **Locura.** 0 — **Valor.** 3

#### Vista del cementerio: todas las búsquedas del ledger y dónde murieron
**Fuente.** web: Man AHL (enlace arriba); schwager_smw, p. 140-141; web: Sankey (https://www.storytellingwithdata.com/blog/what-is-a-sankey-diagram ; https://www.metabase.com/glossary/sankey-diagram).

**Qué dice.** Premiar el fracaso bien hecho reduce el sobreajuste. Un Sankey, mejor que un embudo, muestra dónde cayó cada estrategia y por qué ruta.

**Qué significaría aquí.** La zona Ledger enseña un estudio cada vez. Una pestaña nueva con todos los estudios del ledger: familia, activo, TF, último paso alcanzado, n que entró y salió en cada paso, fecha y estado (viva o muerta en el paso k). El Sankey por estrategia a través de databanks no es posible todavía porque la identidad cambia entre databanks de un proyecto; el de cuentas por paso sí.

**Estado.** AMPLÍA (zona Ledger de un estudio; matriz de cobertura por plantilla) — **Tipo.** interfaz — **Locura.** 0 — **Valor.** 3

#### Abanico de curvas nulas detrás de la curva real, y el test ciego
**Fuente.** taleb_fooled, p. 41-47; aronson_ebta, p. 84-85.

**Qué dice.** Taleb: "ya no puedo ver un resultado realizado sin referencia a los no realizados". Siegel mezcló 4 gráficos reales y 4 aleatorios: brokers y alumnos de Aronson acertaron al azar.

**Qué significaría aquí.** En la página del mono, la equity OOS de la estrategia sobre un abanico de equities de entradas aleatorias (bandas 5-50-95), mismas salidas y costes: se ve si destaca y cuándo se separó. El bloque `cone` ya existe en la ventana. Y un test ciego: mezclar la curva OOS real con curvas del nulo del mismo peldaño y ver si el dueño la distingue, para saber si leer curvas aporta algo.

**Estado.** NUEVA (el mono guarda hoy `nulls.csv` por estadístico, no curvas por sorteo; necesita que el estudio emita bandas, así que no es solo interfaz) — **Tipo.** interfaz — **Locura.** 2 — **Valor.** 3

#### Tabla 2×2 de signos mensuales contra el buy-and-hold
**Fuente.** covel_trendfollowing, p. 70-71.

**Qué dice.** Campbell contra el S&P en 287 meses: ambos positivos 96, opuestos 150, ambos negativos 41. La no correlación contada, no como rho.

**Qué significaría aquí.** En el paso de exposición, la tabla 2×2 de meses y la cuenta "ambos negativos": los meses en que la estrategia no diversifica al subyacente. Meses de la estrategia desde la cosecha; meses del subyacente desde las barras.

**Estado.** AMPLÍA (paso de exposición) — **Tipo.** interfaz — **Locura.** 0 — **Valor.** 2

#### Galería de operaciones por cuantiles, nunca la mejor sola
**Fuente.** tharp_freedom, p. 29-31 (Eckhardt).

**Qué dice.** El ojo pesa los casos sobresalientes y unos pocos ejemplos bien elegidos convencen; hace falta algo parecido a un doble ciego.

**Qué significaría aquí.** La ventana nunca enseña el gráfico de la "mejor operación" sin la mediana y la peor al lado. Cualquier galería elige operaciones por cuantil de P&L o al azar.

**Estado.** NUEVA (como regla de interfaz; hoy no hay galería) — **Tipo.** interfaz — **Locura.** 0 — **Valor.** 2

#### Resumen de promoción: cinco preguntas puntuadas 0/1/2
**Fuente.** elder_newtfal, p. 238-242; tharp_freedom, p. 243, 275-278.

**Qué dice.** El "Apgar" de Elder: cinco preguntas de 0 a 2, se opera solo con 7 o más y ningún cero; la puntuación simple gana al juicio clínico. Tharp: un sistema que gana un millón probablemente genera más de un millón en costes.

**Qué significaría aquí.** El dossier resumido en cinco líneas puntuadas (bate a su nulo y a su referencia de familia; sobrevive a los episodios de estrés que contiene; convexidad aceptable; correlación en estrés con lo vivo aceptable; no depende del stop), promoción solo con 7 o más y sin ceros. Una línea extra: costes brutos modelados / beneficio neto, donde más de 1 significa que un error de 2× en costes cambia el veredicto.

**Estado.** AMPLÍA (veredicto del pipeline; varias entradas necesitan su estudio antes) — **Tipo.** interfaz — **Locura.** 0 — **Valor.** 3

#### Veredicto primero, curvas después
**Fuente.** aronson_ebta, p. 463-470.

**Qué dice.** El experto que mira el resultado del modelo y lo retoca lo empeora.

**Qué significaría aquí.** Las páginas presentan el veredicto antes que las curvas.

**Estado.** YA EXISTE (`ui/desktop/blocks/verdict.py`, cabecera de `ResultView`) — **Tipo.** interfaz — **Locura.** 0 — **Valor.** 1

#### Coordenadas paralelas de los parámetros de un lote de variantes
**Fuente.** web: Sankey y coordenadas paralelas (https://www.storytellingwithdata.com/blog/what-is-a-sankey-diagram).

**Qué dice.** Coordenadas paralelas de los parámetros de un lote coloreadas por el resultado OOS.

**Qué significaría aquí.** Sobre `strategyPermutations/<P>/<S>/metrics.parquet`, un eje por parámetro y color por el beneficio en oos1, para ver si el lote es meseta o pico. Nunca con las columnas de oos2, que el lote contiene: leerlas gastaría la puerta.

**Estado.** NUEVA — **Tipo.** interfaz — **Locura.** 1 — **Valor.** 2

#### Mapa de calor mercado × año con el rango de la celda del build
**Fuente.** schwager_nmw, p. 109-110.

**Qué dice.** El ejemplo del artículo era la mejor de 250 celdas mercado-año; 17 de 25 mercados perdían en la década.

**Qué significaría aquí.** Pintar cada superviviente como mapa mercado × año (9 mercados, todos los años, build y oos1 marcados) y dar el rango de la celda del build entre todas. Si el activo y los años donde se construyó son la mejor celda, el "edge" es el ejemplo bien elegido.

**Estado.** AMPLÍA (crossmarket; hoy no escribe cifras por año, así que requiere cambio en el estudio) — **Tipo.** interfaz — **Locura.** 0 — **Valor.** 3

#### Hoja de ruta del mes por día hábil, build contra oos1
**Fuente.** williams_longterm, p. 89-91.

**Qué dice.** El recorrido medio por día hábil del mes (TDM) construido con datos hasta 1996 anticipó los giros de 1998.

**Qué significaría aquí.** Un gráfico por activo del rendimiento acumulado medio por TDM (o por hora de la semana en intradía) en build, superpuesto con oos1 y bandas bootstrap. Necesita un panel de rendimientos por barra que calcule un estudio.

**Estado.** NUEVA — **Tipo.** interfaz — **Locura.** 1 — **Valor.** 2

#### Gráfico de rotación relativa de la cartera de estrategias
**Fuente.** newfrontiers_ta, p. 49-83.

**Qué dice.** RS = A/B suavizado con medias de 10/30; RS-Ratio y RS-Momentum normalizados; el gráfico de rotación relativa (RRG) coloca cada elemento que gira líder → debilitándose → rezagado → mejorando.

**Qué significaría aquí.** Para la cartera futura: la fuerza relativa de la equity de cada estrategia contra el buy-and-hold de su activo, en un RRG del grupo de estrategias vivas o candidatas. Vista de seguimiento, no prueba de edge.

**Estado.** NUEVA (cartera no construida) — **Tipo.** interfaz — **Locura.** 1 — **Valor.** 2

#### Reglas de pintura: dispersión detrás de cada r, tiempo medio de mantenimiento sobre la curva E
**Fuente.** katsanos_intermarket, p. 34-48; faith_turtle (E-ratio, ver notas de turtles).

**Qué dice.** Una correlación de niveles exagera (S&P-FTSE R² 0,909 en precios, ρ 0,43 en rendimientos diarios); un atípico o tres regímenes en la nube hacen inútil un r. Faith: la curva E por horizonte dice a qué horizonte culmina la entrada.

**Qué significaría aquí.** Toda cifra de correlación en la ventana tiene al lado su nube de puntos, en Spearman sobre rendimientos. Y sobre la curva e(k) de `entryQuality` (que ya existe con banda aleatoria), una marca del tiempo medio de mantenimiento de la estrategia para ver si la salida corta antes del pico. Lo segundo debería emitirlo el estudio como referencia, porque la ventana no inventa texto sobre los datos.

**Estado.** AMPLÍA (`entryQuality/eratio.py`, bloque `scatter`) — **Tipo.** interfaz — **Locura.** 0 — **Valor.** 2

### Las de locura 3 de esta sección
Ninguna llega a 3. Las más atrevidas (locura 2): medir la población entera que genera SQX, el abanico de curvas nulas con test ciego del dueño.

## 7 · Las locas

Pediste escucharlas aunque parezcan locas. Aquí están todas las que los agentes marcaron con locura 3 o 2,
con el subtema donde está su entrada completa. Algunas sirven, paradójicamente, para lo contrario de lo que
parece: una plantilla lunar es el mejor control negativo de la cadena, porque no debería sobrevivir nunca.

### Locura 3: raras pero interesantes

- **Controles negativos de toda la cadena: familias placebo.** Entrada en 3.1.
- **Modelo de análogos: superponer una época pasada.** Entrada en 4.1.
- **Modelos fundacionales de series temporales (Kronos).** Entrada en 4.4.
- **Cascadas de stops de los seguidores de tendencia.** Entrada en 4.5.
- **Noticias y atención mediática: titulares extremos, portadas, GDELT, Google Trends.** Entrada en 4.11.
- **Mercados de predicción como sorpresa frente a probabilidad implícita.** Entrada en 4.11.

### Locura 2: poco habituales

- **Correr la estrategia sobre mercados falsos (surrogados), no solo con entradas falsas.** Entrada en 3.1.
- **Un bloque de ruido en la ranura aleatoria: el precio de un grado de libertad falso.** Entrada en 3.1.
- **Mercado sintético de punta a punta como control negativo.** Entrada en 3.1.
- **¿Distingue el ojo una curva real de una curva de mono?.** Entrada en 3.1.
- **¿Es oro o es dólar? Partir XAUUSD en sus dos patas.** Entrada en 3.2.
- **Guardar todo lo que la búsqueda genera, y el sesgo de truncamiento de los estudios de población.** Entrada en 3.3.
- **Parámetros de nivel frente a parámetros de sincronía.** Entrada en 3.5.
- **Historias alternativas desplazando los límites de las barras.** Entrada en 3.6.
- **Familia de «puntos focales»: las señales por defecto de los indicadores más usados.** Entrada en 4.3.
- **Confluencia de estrategias que no pagan costes por separado.** Entrada en 4.4.
- **Inflar las comisiones durante la construcción.** Entrada en 4.4.
- **Clasificador universal entre mercados sobre rasgos de forma.** Entrada en 4.4.
- **Minería de alfas con LLM desde el chat de plantillas.** Entrada en 4.4.
- **Regresión simbólica como generador de condiciones.** Entrada en 4.4.
- **La señal fallida como señal: el extremo que no revierte y la noticia que no mueve.** Entrada en 4.6.
- **Niveles obvios: números redondos, máximo y mínimo de ayer, stops apiñados.** Entrada en 4.6.
- **Perfil de tiempo en precio: punto de control, área de valor y «huecos».** Entrada en 4.6.
- **Vencimientos de opciones: el corte de las 10:00 de NY y el anclaje al strike.** Entrada en 4.7.
- **Separar el XAUUSD en «dólar» y «oro propiamente dicho».** Entrada en 4.8.
- **Cestas homogéneas: el «banco de peces» es más persistente que cada miembro.** Entrada en 4.8.
- **Instrumentos sintéticos de relación: ratios y diferenciales como mercados nuevos.** Entrada en 4.8.
- **Rasgos entre mercados alternativos: fuerza de divisa contra el oro y residuo tras el factor USD.** Entrada en 4.8.
- **Entropía de permutación como filtro de previsibilidad.** Entrada en 4.9.
- **Relación señal-ruido del ciclo dominante como régimen (no como entrada).** Entrada en 4.9.
- **Salidas aprendidas como diagnóstico del edge que la salida deja sobre la mesa.** Entrada en 4.10.
- **Volumen de ticks, volumen firmado y desequilibrio de órdenes.** Entrada en 4.11.
- **Barras de rango igual como otro «marco temporal».** Entrada en 4.11.
- **Sentimiento minorista y consenso.** Entrada en 4.11.
- **Inflar la comisión durante el build.** Entrada en 5.1.
- **Si el slippage medio es a favor, retrasa la orden.** Entrada en 5.2.
- **No poner el stop donde lo pone todo el mundo.** Entrada en 5.4.
- **Techo de apalancamiento con visión perfecta.** Entrada en 5.7.
- **Meta-labeling: un segundo modelo que decide el tamaño o si se salta la operación.** Entrada en 5.7.
- **Confluencia: estrategias que no pagan sus costes pueden pagarlos cuando coinciden.** Entrada en 5.9.
- **Dar más peso a lo que lleva más tiempo sobreviviendo fuera de muestra.** Entrada en 5.9.
- **Medir la población entera que genera SQX, no solo lo que guarda.** Entrada en 6.2.
- **Abanico de curvas nulas detrás de la curva real, y el test ciego.** Entrada en 6.6.

## 8 · Lo que este dossier no verifica

- **Nada se puede importar en SQX desde el proyecto.** Varias entradas de las secciones 3 y 4 proponen
  cargar series propias en SQX como símbolos: surrogados, un mercado sintético, un DXY sintético, barras
  de rango. La web dice que SQX importa datos desde su Data Manager, pero eso es la GUI. El API no tiene
  verbo de importación, y un símbolo nuevo exige la GUI del maestro y toca el almacén compartido
  (encargo 9, §1). Esas entradas sólo son viables con un backtest propio en Python.

- **Ninguna cifra de los libros se ha reproducido aquí.** Son las que dan los autores, casi siempre
  optimizadas sobre la muestra entera. Aronson avisa de que una regla sacada de un libro trae dentro los
  ensayos ocultos de su autor.
- **Las páginas** son las impresas cuando el agente las vio, y si no, la del PDF. En *Evidence-Based
  Technical Analysis*, la página del PDF es la impresa más 16. El texto de Tharp es la primera edición de
  1998, no la segunda que figura en el nombre del fichero.
- **Los estados YA EXISTE y AMPLÍA** salen de búsquedas en el repositorio hechas por los agentes, no de
  una auditoría. Puede haber piezas construidas que no encontraron.
- **Las cifras de internet** son las que publican sus fuentes. Algunas son claramente infladas, como el
  Sharpe de 5,87 de un modelo de noticias sobre EURUSD. Se dejaron como lección, no como prior.
- **Dos afirmaciones son razonamiento de un agente, no un resultado:** que el buy and hold al mismo riesgo
  puede ser una vara baja en ventanas bajistas, y que la agrupación de `core/surface/trials.py` halaga el
  Sharpe deflactado. Las dos se zanjan con una simulación.
- ***The Handbook of Technical Analysis*** no se leyó: en disco sólo está el puntero de Git LFS.
- **La lectura de algunos libros narrativos fue por palabras clave** en sus capítulos de relato: el centro
  de *When Genius Failed*, los perfiles de *Trend Following* y la parte de diario de *The Trend Following
  Bible*. Los capítulos de método se leyeron enteros.
