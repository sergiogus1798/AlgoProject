# 5. Retest en mercados adicionales — ¿el sistema gana por acertar CUÁNDO entra, o por estar comprado?

### Qué pregunta responde

Una estrategia long-only que opera en un mercado que sube gana dinero casi haga lo que haga. Eso no
es habilidad: es estar comprado. La pregunta que responde este módulo es otra, y es la única que
importa:

> Si cogemos exactamente el mismo ritmo de operar —el mismo número de operaciones, la misma duración
> de cada una, los mismos huecos entre ellas, el mismo día de la semana y la misma hora— y lo
> colocamos en momentos **al azar** del mismo mercado, ¿habría ganado lo mismo?

Se generan miles de esas versiones al azar y se mira dónde queda la de verdad. Si la de verdad queda
entre las mejores, sus entradas llevan información. Si queda en el montón, lo que había era la
deriva del mercado y nada más.

Se hace sobre mercados que la estrategia **nunca vio** cuando se optimizó. Ahí sus entradas son
efectivamente ciegas, y batir al azar en varios de ellos es algo que el sobreajuste no puede fabricar.

### Cuándo lo usas, y cuándo no

**Lo usas** después de haber pasado tus estrategias por un retest multi-mercado en SQX, para decidir
cuáles siguen adelante.

**No lo usas** para saber si una estrategia está sobreajustada al oro. No lo detecta, y decirlo al
revés es el error más fácil de cometer con este informe. Lo que mide es si el acierto **se traslada**
a otros mercados.

**No lo usas** sobre el propio activo base. La estrategia se optimizó ahí, así que gana a lo aleatorio
por construcción: en la prueba de este módulo sobre oro, las ocho estrategias probadas salieron con
p entre 0.0002 y 0.007. Eso no dice nada bueno de ellas, sólo dice que el código funciona. Por eso el
activo base está fuera de la lista de `strategies/crossmarket/markets.yaml` y fuera de la votación.

**No lo usas** en un mercado donde la estrategia hizo menos de 30 operaciones, ni en uno donde entre
con órdenes pendientes. Ese caso se descarta solo y se te avisa (ver *Qué produce*).

### Antes de empezar

Tres cosas, en este orden:

1. **En SQX**, pasa tus estrategias por una tarea de retest sobre mercados adicionales, y deja el
   resultado en una databank. Los mercados que elijas ahí tienen que ser **los mismos** que estén en
   `strategies/crossmarket/markets.yaml` para ese activo, escritos igual.
2. **Exporta en cuanto termine.** Varias databanks se vacían en cada ciclo de la cadena de tareas, y
   la sincronización horaria borra del disco lo que no está en memoria. Si el retest queda ahí una
   noche, puede no estar por la mañana.
3. **Fija la lista de mercados antes de mirar resultados.** Elegir los mercados después de ver dónde
   funciona convierte la prueba en una selección y los p-valores en decoración.

Comprueba lo que vas a aplicar de costes:

```bash
python3 -m core.assets XAUUSD
```

Que salga `UNDECIDED` **no bloquea este módulo**, y es la única excepción a esa regla en todo el
proyecto. El motivo: aquí no se autoriza nada, se reproduce lo que SQX ya simuló. El coste se recupera
operación a operación de los propios datos exportados (`precio bruto − beneficio reportado`), no se
elige. En el oro eso mide 8 $ por lote y lado, que es exactamente lo que SQX tiene configurado.

### Dónde eliges los mercados

En `strategies/crossmarket/markets.yaml`, un bloque por activo. Se edita a mano y ningún código
cambia al hacerlo:

```yaml
XAUUSD:
  main: XAUUSD_DukasM1_Infinox
  timeframe: M30
  additional:
    - {feed: XAGUSD_DukasM1_Infinox, role: family, data_from: 2003-08-08}
    - {feed: BRENTCMDUSD_ftmo, role: family, data_from: unknown}
```

`feed` tiene que estar escrito **exactamente** como lo llama SQX, y ser el mismo que usaste en la
tarea de retest. `role` es sólo descriptivo, sale en el informe y no cambia ningún cálculo.
`data_from` es la primera fecha con datos de ese mercado: tampoco filtra nada, está para que veas de
un vistazo cuánta ventana común te queda de verdad — los índices no llegan más atrás de 2011-2013,
mientras que las divisas y los metales llegan a 2003.

El activo base va en `main` y **nunca** en `additional`: es el mercado en el que se optimizó.

Todo el código de este análisis está junto en `strategies/crossmarket/`, incluida esa lista. Cada
estudio de estrategias tendrá su propia carpeta igual que esta.

### Cómo se ejecuta

Dos comandos preparan los datos, y el tercero abre el panel — que es ahora la **única** forma de
correr la prueba. No hay comando de línea que la corra solo.

```bash
# 1. Las barras de todos los mercados de la lista (una arranca de SQX por mercado, ~1 min cada una)
python3 -m sqx.export.export_bars --asset XAUUSD --from 2003.01.01 --to 2026.01.01

# 2. Los trades del retest, partidos por mercado (~4 min por cada 200 estrategias)
python3 -m sqx.export.export_retest --project XAUUSD --databank RetestMarkets

# 3. El panel
python3 -m strategies.crossmarket.explorer.serve --project XAUUSD --databank RetestMarkets \
    --asset XAUUSD --export 2026-09-08
```

| flag | obligatorio | qué hace |
|---|---|---|
| `--asset` | sí | activo base. Es la clave que se busca en `strategies/crossmarket/markets.yaml` |
| `--project` | sí | proyecto en el master |
| `--databank` | sí | la databank donde dejaste el retest |
| `--export` | sí (en el paso 3) | la fecha del export del paso 2, `AAAA-MM-DD`. Es la carpeta que va a leer |
| `--from` / `--to` | no, sólo en el paso 1 | ventana de barras. Por defecto 2003-2026 |
| `--port` | no, sólo en el paso 3 | puerto del panel. Por defecto 8766 |

Los pasos 1 y 2 **arrancan SQX** (el worker, nunca el master) y se pueden ejecutar con tu interfaz
abierta. El paso 3 no toca SQX en absoluto: sólo lee ficheros, y abre
`http://127.0.0.1:8766` en tu navegador.

**El cajón de configuración** (▸ arriba de las pestañas) es donde se toca todo lo que antes eran
flags: cuántas versiones al azar (`draws`), qué modelos correr, el umbral de significancia, el suelo
de operaciones mínimas, y los parámetros de las pruebas nuevas (bloque del bootstrap, múltiplos de
coste, fracción de slippage). Cambiar un valor sólo afecta al siguiente análisis que pulses — nada se
escribe a disco, y al recargar el panel vuelve a los valores de fábrica.

**Los cuatro modelos** siguen siendo los mismos, ahora elegibles en el cajón:

| modelo | qué cambia al azar | qué pregunta responde |
|---|---|---|
| `block_shift` | sólo *cuándo* entra, dentro de su mismo semestre y en el mismo día y hora | ¿acierta al elegir el momento? **Es el del veredicto** |
| `segment_permute` | el momento, el orden y las rachas | lo mismo, pero deshaciendo las rachas. Más fácil de batir |
| `resampled_holds` | el momento, y qué duraciones y esperas ocurren | ¿su ritmo de operar, en general, vale algo? |
| `fitted_holds` | el momento y las duraciones, sacadas de una distribución ajustada | ¿un sistema con esa *forma* de duraciones, entrando al azar, iría igual? |

El primero de la lista es el que decide. Los demás están para ver si un resultado **sobrevive a otra
suposición**, nunca para buscar uno que pase: si una estrategia sólo aprueba con un modelo alternativo,
lo que has encontrado es la suposición de ese modelo, no la estrategia. La pestaña "Veredicto" lo dice
en una tabla, y "Explorador de pruebas" te deja mirar cualquier mercado bajo cualquier modelo.

Aviso concreto para tu flota: `fitted_holds` no le encaja. Tus estrategias salen casi siempre al tope
de barras, así que sus duraciones son prácticamente constantes y ninguna distribución las representa
(dispersión 0.05, KS p < 0.001). El panel imprime esos dos números al lado para que se vea.

Sobre `draws`: 5000 no se queda corto de potencia, pero sí fija el p-valor más pequeño que se puede
observar, que es 1/5001 ≈ 0.0002. Si comparas cientos de estrategias entre sí, ese suelo importa;
está explicado en `strategies/crossmarket/POSSIBLE_IMPROVEMENTS.md`.

### Los botones y las pestañas

Arriba: un desplegable de estrategias (marca `· analizada` la que ya tiene resultado guardado) y tres
botones.

| botón | qué hace |
|---|---|
| **Analizar esta estrategia** | Corre las cuatro pruebas de esta ficha — Test 1a bajo los cuatro modelos, exposición, significancia, huella, coste y correlación — sobre todos los mercados adicionales de la estrategia elegida. Barra de progreso, un mercado por paso |
| **Analizar toda la base de datos** | Repite el botón anterior para cada estrategia del export. Es necesario antes de generar el informe, porque el panel es ahora el único sitio donde se corre la prueba |
| **Generar informe** | Escribe `by_market.csv`, `verdict.csv`, `crossmarket.md`, `crossmarket.html` y `manifest.json`, leyendo lo que ya dejó en caché "Analizar toda la base de datos" — si no se ha corrido, el botón lo pide |

Debajo de los botones, una franja fija resume la base de datos completa (cuántas `MANTENER`, la
cifra de suerte) — vacía hasta que "Analizar toda la base de datos" haya corrido al menos una vez.

Las pestañas, con lo que muestra cada una:

| pestaña | qué muestra |
|---|---|
| **Veredicto** | Tabla por mercado, `MANTENER`/`DESCARTAR`/`NO EVALUABLE` y las comprobaciones (`fill_error`, `calendar_kept`, etc.) — igual que antes traía `crossmarket.html` |
| **Exposición** | Test 1c: concentración E, exceso A y su intervalo de confianza, A por unidad de riesgo, y qué fracción del MFE se capturó |
| **Significancia** | Sharpe, cuántas operaciones hacen falta para que ese Sharpe sea distinguible de cero (MinTRL), e intervalos de confianza de PF y expectancy por bootstrap — y la amplitud entre mercados |
| **Huella** | Si la duración de las operaciones se parece a la del oro (KS), y la forma de la distribución de retornos |
| **Coste** | El múltiplo de coste al que la estrategia deja de ganar (breakeven), y cuánto se degrada con un desplazamiento de una barra o con slippage |
| **Correlación** | Matriz de correlación semanal entre los mercados de esa estrategia más el oro, y qué parte de la varianza explica el primer componente (PCA) |
| **Explorador de pruebas** | Dos desplegables — mercado y modelo — para mirar cualquier combinación de las que ya se corrieron, más un botón "Re-ejecutar esta prueba" que la repite con más tiradas sin tocar la caché |

*(Capturas de pantalla del panel real pendientes de añadir aquí — regla 8 exige que sean de una
ejecución real, no inventadas.)*

### Qué produce

En `~/Desktop/AlgoData/reports/<proyecto>/<databank>/<fecha>/crossmarket/`. **Los informes se
acumulan, no se sobreescriben**: cada ejecución crea su carpeta del día.

| fichero | qué lleva |
|---|---|
| `by_market.csv` | una fila por estrategia y mercado, con todo el detalle |
| `verdict.csv` | una fila por estrategia: el veredicto |
| `crossmarket.html` | **el informe ilustrado.** Es por donde se empieza |
| `crossmarket.md` | las mismas conclusiones en texto plano |
| `manifest.json` | qué export leyó, con qué semilla y qué versión del código |

Los pasos 1 y 2 escriben en `AlgoData/bars/<mercado>/H1.csv` (se sobreescribe: las barras son un
hecho del mercado, no de una ejecución) y en `AlgoData/raw/<proyecto>/<databank>/<fecha>/` (con
fecha, inmutable).

### Cómo se lee el resultado

**Empieza por `crossmarket.html`:**

```bash
xdg-open ~/Desktop/AlgoData/reports/XAUUSD/<databank>/<fecha>/crossmarket/crossmarket.html
```

Es un fichero suelto que no carga nada de internet, así que se puede mandar por correo y se abrirá
igual dentro de cinco años. Lleva, en este orden: las cuatro cifras de cabecera, cuántas pasarían por
suerte, la tabla por mercado, **la distribución de los 5.000 backtests aleatorios de cada estrategia
con el backtest real marcado encima**, los cuatro modelos comparados contra el límite de 0,05, la
tabla de comprobaciones, y un glosario que explica cada número. Se dibujan como mucho las doce
estrategias con menor p; el resto están en los CSV.

**Cómo se lee el histograma.** Las barras azules son los 5.000 backtests aleatorios y la línea
naranja es el real. Si la línea cae dentro del montón azul, esa estrategia no hizo nada que el azar
no hiciera. Cuanto más a la derecha del montón, más difícil es explicarla por suerte — y el p-valor
es exactamente qué fracción del montón quedó a su derecha.

Luego, en `crossmarket.md`, la sección "How many of these are luck".** Da dos
números: cuántas estrategias pasarían por pura suerte si los mercados fueran independientes, y
cuántas si sus resultados se parecen entre sí. **El segundo es el bueno.** Ocho mercados movidos por
el mismo factor dólar-y-riesgo se comportan como dos, así que la regla de mayoría es mucho más débil
de lo que parece. Si el número de MANTENER no está cómodamente por encima de esa cifra, ahí no hay
nada, por buenos que se vean los p-valores individuales.

Las columnas de `by_market.csv`, que son las que hay que saber leer:

| columna | qué es | qué valor es bueno |
|---|---|---|
| `real_r` | lo que ganó de verdad por operación, en "barras típicas de ese mercado" | cuanto más alto mejor, pero **no significa nada solo** |
| `null_r` | lo que ganó la versión aleatoria mediana | es la vara de medir; suele rondar cero |
| `edge_r` | la diferencia entre las dos | es el tamaño del efecto |
| `p` | qué fracción de las 5000 versiones al azar igualó o superó a la real | **≤ 0.05 es batir al azar.** Es el número del veredicto |
| `p_<modelo>` | lo mismo bajo cada forma alternativa de aleatorizar | comprobación. Si una estrategia sólo pasa bajo un modelo alternativo, lo que encontraste es esa suposición, no la estrategia |
| `trades` | operaciones en ese mercado | por debajo de 30 el mercado no vota |
| `on_bar_open` | fracción de entradas al inicio de barra | por debajo de 0.95 el mercado no vota: son órdenes pendientes y la comparación deja de ser justa |
| `calendar_kept` | fracción de entradas aleatorias que cayeron en el mismo día y hora que la real | debe ser 1.00. Si no lo es, hay un fallo |
| `atr_ratio` | volatilidad en las entradas reales frente a la media del mercado | cerca de 1. Muy lejos de 1 significa que la estrategia elige barras raras y hay que leer el resultado con cuidado |
| `convention` / `fill_error` | qué precios reproducen los de SQX y con cuánto error | `fill_error` debe ser 0. Si no, el resultado no vale |
| `family` (en `verdict.csv`) | `entry` o `entry+exit` | ver más abajo |

**Sobre `family`.** Cuando la estrategia sale siempre por el tope de barras, la duración de la
operación no dependía del precio, y esto es una prueba limpia de la entrada. Cuando sale por una
señal, la duración sí lleva información, y la versión aleatoria la reutiliza sin poder reproducir de
dónde salía: para esas, el resultado mide entrada **y** salida a la vez. No es peor, es otra cosa, y
no se puede contar como "acierta al entrar".

### Un ejemplo completo

Prueba del módulo sobre el propio oro (2007-2018, 5000 versiones al azar por estrategia). Recuerda
que aquí se espera que gane: es el mercado en el que se optimizaron.

```
8 estrategias en 3.9s (5000 tiradas)

estrategia        n   real_r   null_r    edge  p_shift   p_perm    cal   atr  barcap
1.17.44.csv    1101    0.156   -0.013   0.169   0.0006   0.0010   1.00  1.02    0.48
1.25.34.csv    1038    0.129   -0.003   0.132   0.0072   0.0052   1.00  1.10    0.59
10.15.25.cs    1144    0.133   -0.018   0.151   0.0004   0.0022   1.00  1.03    1.00
14.16.34.cs    1035    0.236   -0.033   0.269   0.0002   0.0004   1.00  1.03    1.00
15.24.36.cs    1230    0.184   -0.010   0.194   0.0002   0.0004   1.00  1.08    0.40
16.20.43.cs     933    0.205   -0.006   0.211   0.0002   0.0002   1.00  1.05    0.17
```

Y la comprobación de que el número mide lo que dice medir: se cogen las operaciones de una estrategia
y se retrasan todas unas cuantas barras, sin tocar nada más. Si el módulo mide acierto en el momento
de entrar, moverlas tiene que estropearlo — y lo hace, de forma ordenada:

```
 desplazo   real_r     edge   p_shift
        0    0.236    0.269    0.0002     <- la real
        1    0.207    0.226    0.0010     <- una hora tarde
        3    0.120    0.120    0.0240     <- tres horas tarde: ya casi no significa nada
        8    0.064    0.072    0.1580     <- ocho horas tarde: indistinguible del azar
       24    0.065    0.098    0.1262
```

### Qué NO te dice

- **No te dice que la estrategia esté sobreajustada o no al activo base.** Mide traslado, no ajuste.
- **No valida la curva de capital.** El número está construido a propósito sin tamaño de posición,
  para que la comparación sea justa. Dice que entra en barras mejores que el azar; no dice que la
  gestión monetaria funcione.
- **No convierte un mercado fallado en un problema.** Que falle en un mercado es información sobre
  dónde vive la ventaja, y es la materia prima del estudio de propiedades de mercado.
- **No corrige por haber probado cientos de estrategias a la vez.** Declara cuántas pasarían por
  suerte; no las quita. Ese es el número que tienes que mirar tú.

### Si algo falla

- **`FileNotFoundError` sobre un fichero de `bars/`** — ese mercado no está exportado. Ejecuta el
  paso 1, o quítalo de `strategies/crossmarket/markets.yaml`.
- **`KeyError` con el nombre del activo** — el activo no tiene bloque en `strategies/crossmarket/markets.yaml`.
- **Un mercado sale con 0 estrategias** — el nombre del feed en `markets.yaml` no coincide con el
  que usó la tarea de retest en SQX. Mira los nombres de carpeta que dejó el paso 2.
- **`fill_error` distinto de 0** — las barras y las operaciones no son del mismo mercado o de la
  misma ventana. El resultado no vale; no lo interpretes.
