# MCPT de la fábrica — Propuesta completa y plan de pruebas

**Fecha:** 2026-10-12 · **Alcance:** toda la fábrica de estrategias (Builder de SQX + filtros + pipeline de validación), por configuración de mercado × marco temporal × bloques × ajustes.
**Origen:** idea de Jaffray Woodriff (*Hedge Fund Market Wizards*), formalizada como *Monte Carlo Permutation Test* por Timothy Masters (*Testing and Tuning Market Trading Systems*), y el artículo «A robust data mining workflow» (Denelio).
**Relación con otros documentos:** complementa al mono del paso 8 (`criterios-implementados-2026-10-12.md`), que es un nulo para *una* estrategia; este documento es un nulo para *el proceso que fabrica* las estrategias.

---

## 0. Resumen en diez líneas

1. Se fabrica una serie de precios sintética que conserva todo lo del mercado real (volatilidad, rachas, calendario, perfil horario, deriva anual, camino intrabarra) **excepto la predictibilidad de la dirección**.
2. Sobre esa serie se repite **la fábrica entera**, idéntica: Builder de SQX, filtros y toda la cascada del pipeline.
3. Se hace lo mismo **K veces sobre el real** (semillas distintas) y **K veces sobre ruido** (series distintas).
4. En cada etapa de la fábrica se cuentan los supervivientes **únicos**.
5. El cociente ruido / real en la última etapa es la **tasa estimada de descubrimientos falsos (FDR)** de la fábrica: qué fracción de lo que entrega la fábrica la entregaría igual un mundo sin nada que encontrar.
6. El cociente etapa a etapa da el **lift** de cada paso del pipeline: si un paso deja pasar igual al ruido que al real, no discrimina.
7. Las estrategias de ruido son **controles negativos con verdad conocida**: calibran empíricamente las líneas (1,65, p95…) de cada paso.
8. Se mide además si la fábrica **repite** lo que encuentra con semillas distintas (en el real debería; en el ruido no).
9. El veredicto es para la **configuración**, no para una estrategia: PASA si FDR ≤ 0,2; NO PASA si FDR ≥ 0,5.
10. Coste dominado por el Builder: $2K$ ejecuciones. La preparación de cada serie cuesta ~2 min y está probada.

---

## 1. Qué pregunta contesta y por qué hace falta

### 1.1 El sesgo que nada en el pipeline actual mide

Antes de que exista ninguna madre, el Builder de SQX recorre cientos de miles o millones de combinaciones de bloques, reglas y parámetros, y se queda con las mejores. Ese es **el sesgo de selección más grande de toda la cadena**.

Lo que ya hay mide otras cosas:

| prueba | qué selección corrige |
|---|---|
| CSCV / PBO (paso 18) | elegir entre las ~5.000 variantes de *una* madre |
| WFC, superficies, WFM (17, 18.5, 19) | estabilidad de los parámetros alrededor de una madre |
| mono (paso 8) | nada: es un nulo para una estrategia fija, sólo válido fuera de muestra |
| **MCPT de la fábrica** | **la búsqueda entera del Builder + todos los filtros posteriores** |

### 1.2 La pregunta, en palabras del artículo

> ¿Qué tan bueno es el ganador que *este mismo proceso de investigación* produce cuando le das datos sin nada que encontrar?

Si el ruido produce tantos supervivientes como el real, el problema no es la estrategia: es la fábrica.

### 1.3 Diferencia con el mono

| | mono (paso 8) | MCPT de la fábrica |
|---|---|---|
| qué es aleatorio | las entradas de una estrategia fija | los **precios** |
| unidad | una estrategia | la configuración de la fábrica |
| corrige la selección | no | **sí**: la selección se repite sobre el ruido |
| válido en el build | no | **sí** |
| frecuencia | por estrategia | una vez por configuración |
| motor | Python sobre operaciones exportadas | SQX (Builder y retests) + Python |

Las dos se complementan; ninguna sustituye a la otra.

---

## 2. El generador de la serie sintética

### 2.1 Requisitos

El nulo debe destruir **sólo** lo que la fábrica podría explotar de forma legítima (la predictibilidad de la dirección) y conservar todo lo demás. Si destruye de más, el ruido es «más fácil» que el mercado real, la barrera sale baja y la fábrica parece mejor de lo que es.

| propiedad | ¿se conserva? | por qué importa |
|---|---|---|
| calendario exacto (sesiones, fines de semana, festivos, rollover) | sí | las estrategias usan filtros horarios y de día |
| zona horaria | sí | idem; error ya encontrado en el primer piloto |
| perfil intradía de volatilidad | sí (exacto) | spread en R, tamaño por la doctrina |
| rachas de volatilidad | sí (exacto) | un mercado con rachas fabrica más patrones falsos (rupturas tras compresión) |
| colas, gaps | sí | SL/TP, deslizamientos |
| camino M1 dentro de cada bloque | sí | decide si se toca antes el SL o el TP |
| deriva de cada año natural | sí (en esperanza) | el resto de la cadena juzga el exceso sobre la deriva anual |
| dirección de un bloque al siguiente | **no** | es lo que se quiere destruir |

**Por qué no la permutación de Masters.** Barajar los retornos en orden independiente destruye las rachas de volatilidad y el perfil horario: una barra de madrugada puede acabar en la apertura de EE. UU. El nulo sale demasiado blando. El primer piloto (barajado) lo confirmó además con un problema práctico: al reasignar timestamps por posición se descuadran las horas cuando faltan minutos.

### 2.2 El volteo de signo alrededor de la deriva anual

Se trocea la serie M1 en **bloques de una barra del marco temporal más pequeño que usen las señales** (si se construye en H1 con filtros de D1, el bloque es la H1). Cada bloque $b$ empieza en el cierre del bloque anterior, de modo que **el gap de apertura pertenece al bloque**.

Retorno logarítmico del bloque:

$$r_b = \ln\frac{C_b}{C_{b-1}}$$

Deriva media por bloque de cada año natural $y$:

$$\mu_y = \frac{1}{n_y}\sum_{b \in y} r_b$$

Retorno sintético del bloque, con $s_b = \pm 1$ al azar con probabilidad ½:

$$r'_b = \mu_{y(b)} + s_b\,\big(r_b - \mu_{y(b)}\big)$$

**Camino dentro del bloque.** Para cada precio M1 $p$ del bloque (apertura, máximo, mínimo y cierre de cada barra M1), con $\varphi \in [0,1]$ la fracción del bloque transcurrida:

$$d = \ln\frac{p}{C_{b-1}}, \qquad d' = s_b\,d + (1 - s_b)\,\mu_{y(b)}\,\varphi, \qquad p' = C'_{b-1}\,e^{d'}$$

- Si $s_b = +1$, el bloque queda idéntico (salvo el nivel de partida).
- Si $s_b = -1$, el bloque se refleja alrededor de la línea de deriva, y **el máximo y el mínimo de cada barra M1 se intercambian**.
- Los bloques se encadenan: $C'_{b}$ es el cierre sintético del bloque $b$ y el punto de partida del siguiente.
- Los logaritmos garantizan precios positivos.

**Propiedades exactas:**
- $|r'_b - \mu| = |r_b - \mu|$: la volatilidad de cada bloque, sus rachas y el perfil por hora son idénticos a los reales.
- $E[s_b\,s_{b+k}] = 0$: la autocorrelación de los retornos sintéticos es nula a partir de un bloque, en cualquier dirección y con cualquier no linealidad que dependa del signo.
- La deriva anual se conserva en esperanza (no exactamente en cada serie; es parte del azar del nulo).

**Lo que se conserva y podría parecer «ventaja»:** cualquier estructura **dentro** de un bloque (p. ej., momentum de minutos dentro de la hora). Por eso el bloque es la barra del marco temporal de las señales: lo que ocurre por debajo de esa escala no es lo que el Builder busca. Se comprueba con un bloque más largo (un día) como prueba de sensibilidad (sección 6, F1).

### 2.3 Qué tramos son sintéticos

**Todo el histórico: build, oos1 y oos2, como un único símbolo continuo.**

Si sólo el build fuera sintético y los tramos fuera de muestra reales, una estrategia de ruido se comportaría al azar en el build real, mientras que un falso positivo verdadero *brilla* en el build real, porque se ajustó a su ruido. Los pasos que comparan dentro y fuera de muestra (SPP IS, WFC, CSCV, degradación) castigarían al ruido mucho más que a los falsos positivos reales y la FDR saldría optimista. Con todo el histórico sintético, una estrategia de ruido recorre exactamente el mismo camino que un falso positivo real: se elige en un build sin significado y se juzga en tramos sin significado.

**Otros mercados (paso 10):** para las estrategias de ruido se usan los mercados adicionales **reales**. La estrategia no tiene ninguna información sobre ellos, así que su resultado allí también es nulo. (Opcional: sintéticos también, con la misma semilla de signos por fecha para conservar la dependencia entre mercados; sólo si el real y el sintético dan resultados muy distintos en ese paso.)

### 2.4 Configuración del símbolo en SQX

- Nombre: `<SIMBOLO>_SYN<kk>` (kk = número de serie).
- **Mismo instrumento** que el real: valor del punto, tamaño del tick, dígitos, spread, comisión, swap, sesiones.
- **Misma zona horaria** que el real (en el piloto: `timezone=EETUS`, que deja el feed en EST+07 como el real).
- Importado en el **master**, con su ventana cerrada (si sólo se importa en el conductor, se pierde en la siguiente copia).
- Ficha de Python `assets/symbols/<SIMBOLO>_SYN<kk>.yaml` generada copiando la del real.

---

## 3. La fábrica que se repite

### 3.1 Definición

La fábrica es **todo** lo que va de los datos a una estrategia «aceptada», con la configuración congelada:

| etapa j | qué es |
|---|---|
| 0 | estrategias generadas por el Builder |
| 1 | pasan los filtros del Builder (y sus tests internos, si los tiene) |
| 2 | únicas tras deduplicar (sección 4.2) |
| 3 | pasan la puerta oos1 (paso 8) |
| 4 | … cada paso siguiente del pipeline, en su orden real (14, 16, 16.5, 17, 18, 18.5, 19, 10…) |
| final | aceptadas por el paso 20 |

**Regla de oro:** las dos ramas usan **exactamente** la misma configuración. Cualquier diferencia (un filtro, un umbral, una versión de SQX) invalida la comparación.

### 3.2 Condición de parada del Builder

Debe ser **la misma en las dos ramas y no por tiempo de reloj**: el Builder puede ir más rápido o más lento sobre la serie sintética y generaría otro número de estrategias. Se fija por **número de estrategias generadas** (o de generaciones). Si en producción se para por tiempo, se mide cuántas genera en ese tiempo sobre el real y se usa ese número para las dos ramas.

### 3.3 Las dos ramas son aleatorias

El Builder genético no es determinista: dos ejecuciones sobre el real con semillas distintas dan bancos distintos. Comparar *una* ejecución real contra la distribución del ruido mezclaría la ventaja con la suerte de la semilla. Por eso:

- **Rama real:** K ejecuciones del Builder sobre el símbolo real, con K semillas distintas.
- **Rama de ruido:** K ejecuciones, cada una sobre una serie sintética distinta (semilla de signos distinta) y con semilla del Builder distinta.

Todas las semillas se anotan. La semilla de los signos se genera con `numpy.random.SeedSequence(semilla_raíz).spawn(K)`.

---

## 4. Lo que se mide

### 4.1 El embudo

En cada ejecución $k$ de cada rama se cuenta $N_{j,k}$, el número de supervivientes **únicos** en la etapa $j$. Medias por rama:

$$\overline{N}^{\,\text{real}}_j = \frac{1}{K}\sum_{k=1}^{K} N^{\text{real}}_{j,k}, \qquad \overline{N}^{\,\text{ruido}}_j = \frac{1}{K}\sum_{k=1}^{K} N^{\text{ruido}}_{j,k}$$

### 4.2 Únicos y familias

El genético cría clones: cuando encuentra un nicho, produce muchas variantes casi idénticas. Contar clones inflaría las dos ramas de forma distinta.

- **Únicos:** se deduplican por la huella (hash) de la lista de operaciones, como en el paso 18.
- **Familias:** se agrupan las estrategias cuyo P/L semanal (por semana de cierre) tiene correlación ≥ 0,9 en el tramo build. Se cuenta también el número de familias.

Se informan las dos cuentas; **la que decide es la de familias**, que es la que no depende del comportamiento del genético.

### 4.3 La tasa de descubrimientos falsos

$$\widehat{\text{FDR}}_j = \min\!\left(1,\ \frac{\overline{N}^{\,\text{ruido}}_j}{\overline{N}^{\,\text{real}}_j}\right)$$

Interpretación: de las estrategias que llegan a la etapa $j$ en el real, qué fracción esperaríamos que llegase igual si no hubiera nada que encontrar. Es la estimación de Storey de la proporción de nulos, con el nulo generado por simulación en lugar de supuesto.

**Si $\overline{N}^{\,\text{real}}_j = 0$:** la FDR no está definida; se informa «sin supervivientes reales».

**Incertidumbre:** bootstrap sobre ejecuciones. Se remuestrean con reposición las K ejecuciones reales y, por separado, las K de ruido; en cada remuestra se recalcula la FDR; 10.000 remuestras; intervalo percentil del 90 %. Con K = 5 el intervalo es ancho: es lo esperado, y por eso el criterio usa también su límite superior.

### 4.4 El lift de cada paso

$$\text{lift}_j = \frac{N^{\text{real}}_j / N^{\text{real}}_{j-1}}{N^{\text{ruido}}_j / N^{\text{ruido}}_{j-1}}$$

(con medias sobre las K ejecuciones). Interpretación:

| lift | significado |
|---|---|
| ≫ 1 | el paso discrimina: deja pasar mucho más al real que al ruido |
| ≈ 1 | **no discrimina**: candidato a quitarse o a recalibrarse |
| < 1 | el paso favorece al ruido: algo está mal (un sesgo, un error de código) |

Su intervalo se saca con el mismo bootstrap. El lift no decide nada automáticamente: es información para revisar el pipeline.

### 4.5 La calibración de las líneas

Las estrategias de la rama de ruido son **controles negativos con verdad conocida**: ninguna tiene ventaja. La tasa de paso del ruido en cada etapa es su **tasa de falsos positivos empírica**:

$$\text{TFP}_j = \frac{N^{\text{ruido}}_j}{N^{\text{ruido}}_{j-1}}$$

Para los pasos con una línea nominal (p. ej., z ≥ 1,65 en una cola ⇒ 5 %), se compara la TFP con su nominal. Si el ruido pasa el paso 8 un 12 % de las veces en lugar de un 5 %, la línea está mal calibrada (colas, dependencia, un sesgo no corregido) y se ve directamente.

**Matiz:** la comparación con el nominal sólo vale para los pasos que juzgan **fuera de muestra**. Para los que miran dentro de muestra, la selección hace que el nominal no aplique; ahí sólo cuenta el lift.

Con pocos supervivientes de ruido, la TFP es imprecisa. Se informa con su intervalo binomial exacto (Clopper–Pearson) sumando todas las ejecuciones de ruido.

### 4.6 La repetibilidad

¿Encuentra la fábrica lo mismo con semillas distintas?

Para dos ejecuciones $a$ y $b$ de la misma rama, $O_{ab}$ es la fracción de familias finales de $a$ que tienen alguna familia en $b$ con correlación semanal ≥ 0,7 en el tramo build. Repetibilidad de la rama:

$$R = \frac{1}{K(K-1)}\sum_{a \ne b} O_{ab}$$

- En el ruido, con series distintas, $R_{\text{ruido}}$ debería ser casi 0.
- En el real se espera $R_{\text{real}} > R_{\text{ruido}}$.
- Si $R_{\text{real}} \approx R_{\text{ruido}}$, cada semilla del real encuentra cosas sin relación entre sí: la fábrica persigue ruido aunque la FDR salga bien.

Se anota; ver el criterio en la sección 5.

### 4.7 El mejor de cada fábrica (sólo anotación)

Lo que propone el artículo: el estadístico del mejor superviviente de cada ejecución, $S_{\max,k}$. Con K pequeño es muy ruidoso. Se anota, y si K ≥ 10 se ajusta una Gumbel a las $S_{\max}$ del ruido y se da la posición del real en ella. No decide.

---

## 5. Criterio (por configuración)

| estado | condición |
|---|---|
| **PASA** | $\widehat{\text{FDR}}_{\text{final}} \le 0{,}2$ **y** límite superior del IC 90 % ≤ 0,5 **y** $R_{\text{real}} > R_{\text{ruido}}$ |
| **LIMBO** | cualquier otro caso que no sea NO PASA; también si $R_{\text{real}} \le R_{\text{ruido}}$ con FDR baja |
| **NO PASA** | $\widehat{\text{FDR}}_{\text{final}} \ge 0{,}5$: más de la mitad de lo que entrega la configuración lo entrega igual el ruido |
| **sin datos** | $\overline{N}^{\,\text{real}}_{\text{final}} = 0$: la configuración no produce nada; no hay nada que juzgar |

**Qué se hace con el estado:**

- **PASA:** la configuración se usa en producción. Sus estrategias siguen pasando por todo el pipeline como siempre.
- **LIMBO:** se amplía K (de 5 a 10). Si sigue en LIMBO, la configuración se usa con la FDR anotada en cada estrategia que salga de ella, y el módulo de fondeo la tiene en cuenta al repartir riesgo.
- **NO PASA:** la configuración no se usa. Se revisa qué cambiar (bloques, marco temporal, filtros, tamaño de la búsqueda) y se vuelve a probar.

**Cuándo se repite:** cuando cambia algo de la fábrica (mercado, marco temporal, bloques, filtros, condición de parada, versión de SQX, o un cambio material en un paso del pipeline). Si no cambia nada, el resultado se reutiliza.

---

## 6. Plan de pruebas

Cada fase tiene un objetivo, qué se hace, cómo se mide el éxito y el tiempo estimado. **No se pasa a la siguiente sin cerrar la anterior.**

### F0 — Prerrequisitos (sin SQX nuevo)

| | |
|---|---|
| **Objetivo** | tener los números y herramientas que todo lo demás necesita |
| **Qué** | (a) medir $T_{\text{build}}$: duración de un Builder de producción, nº de estrategias generadas, nº en el banco; (b) fijar la condición de parada por número de estrategias (sección 3.2); (c) comprobar que el pipeline de Python acepta un símbolo arbitrario (ficha `.yaml`, rutas, nombres de feed); (d) implementar la deduplicación por hash y las familias (sección 4.2) |
| **Éxito** | los cuatro puntos hechos; $T_{\text{build}}$ anotado |
| **Tiempo** | lo que tarde un Builder de producción + ~1 día de código |

### F1 — Validar el generador (sólo Python)

| | |
|---|---|
| **Objetivo** | que la serie sintética sea el nulo que dice ser |
| **Qué** | generar 3 series con el volteo de la sección 2.2 y comparar con el real |
| **Comprobaciones** | (1) precios > 0 y sin huecos de timestamps; (2) timestamps y zona horaria idénticos al real; (3) volatilidad media por hora del día: idéntica (error < 0,1 %); (4) autocorrelación de $\lvert r \rvert$ en los retardos 1–50 bloques: idéntica a la real; (5) autocorrelación de $r$ en los retardos 1–10 bloques: dentro de $\pm 2/\sqrt{n}$; (6) retorno de cada año: compatible con el real dentro de su dispersión esperada; (7) sensibilidad: repetir con bloque = 1 día |
| **Éxito** | (1)–(6) se cumplen |
| **Tiempo** | ~1,5 min por serie (medido en el piloto: 86 s para 7,97 M barras M1 de XAUUSD, 4 GB de RAM; 82 s de los 86 son escribir el CSV) |

### F2 — Prueba de humo en SQX

| | |
|---|---|
| **Objetivo** | comprobar que SQX lee la serie sintética y que en ella no hay ventaja |
| **Qué** | importar una serie (sección 2.4) y retestear en ella, con SQX, ~20 estrategias que hayan pasado el pipeline real |
| **Medida** | el exceso respecto a la deriva de cada una sobre la serie sintética, con su t |
| **Éxito** | la media de las t es ≈ 0 (o ligeramente negativa por los costes), y no salen más t ≥ 1,65 de las que daría el azar (~1 de 20). Si muchas siguen ganando, la serie conserva estructura explotable: acortar el bloque o revisar el generador |
| **Tiempo** | ~2 min de preparación (medido: 28 s de importación, 0,05 s de clonar el proyecto) + 20 retests |

### F3 — Control positivo (recomendado)

| | |
|---|---|
| **Objetivo** | comprobar que el método **detecta** una ventaja cuando la hay (si no, una FDR alta no significaría nada) |
| **Qué** | fabricar una serie sintética con una ventaja plantada: en los bloques que empiezan en una franja horaria concreta, $s_b = +1$ con probabilidad $0{,}5 + \delta$ en lugar de 0,5. Es una ventaja estacional simple que el Builder puede encontrar con un filtro horario |
| **Medida** | ¿la encuentra el Builder? ¿cae la FDR frente a las series sin ventaja? Probar $\delta$ = 0,02 / 0,05 / 0,10 |
| **Éxito** | con el $\delta$ mayor, la fábrica encuentra la ventaja y la FDR baja claramente. Da la **curva de potencia**: qué tamaño de ventaja es capaz de ver el método |
| **Tiempo** | 3 Builders (uno por $\delta$) + embudo |

### F4 — Piloto de punta a punta (K = 1 por rama)

| | |
|---|---|
| **Objetivo** | que todo el embudo funcione de principio a fin y medir el tiempo de cada etapa |
| **Qué** | 1 Builder real + 1 Builder sobre ruido, mismos ajustes y misma condición de parada; exportar los bancos con operaciones; pasar ambos por todo el pipeline |
| **Medida** | tabla del embudo (sección 4.1) y tiempo de cada etapa en cada rama |
| **Éxito** | el embudo se completa en las dos ramas sin intervención manual. **No se sacan conclusiones estadísticas con K = 1** |
| **Tiempo** | $2\,T_{\text{build}}$ / 2 servidores + pipeline de los supervivientes |

### F5 — La prueba (K = 5 por rama, ampliable a 10)

| | |
|---|---|
| **Objetivo** | el veredicto de la configuración |
| **Qué** | 5 Builders reales (semillas distintas) + 5 sobre 5 series sintéticas distintas; embudo completo |
| **Medida** | FDR por etapa con su IC, lift por paso, TFP por paso frente al nominal, repetibilidad, mejor de cada fábrica |
| **Éxito** | estado PASA / LIMBO / NO PASA según la sección 5. Si LIMBO, ampliar a K = 10 |
| **Tiempo** | ver sección 7 |

### F6 — Uso de los resultados

| | |
|---|---|
| **Qué** | (a) decidir qué hacer con los pasos de lift ≈ 1; (b) recalibrar las líneas cuya TFP se aparta del nominal; (c) automatizar todo el ciclo como una tarea del pipeline (`mcpt_fabrica`) que se lanza cuando cambia la configuración |
| **Éxito** | decisiones anotadas; tarea automatizada |

---

## 7. Coste

### 7.1 Fórmula

Con $S$ servidores con licencia de SQX:

$$T_{\text{total}} \approx \underbrace{K \cdot 2\ \text{min}}_{\text{preparar series}} + \underbrace{\frac{2K \cdot T_{\text{build}}}{S}}_{\text{Builders}} + \underbrace{\frac{K\,\big(\overline{N}^{\,\text{real}}_1 + \overline{N}^{\,\text{ruido}}_1\big)\,T_{\text{sup}}}{S}}_{\text{pipeline de los supervivientes}}$$

donde $T_{\text{sup}}$ es el tiempo medio del pipeline por superviviente (retests en SQX, nube, MC, WFM y Python). Si en el ruido sobreviven pocas estrategias, el tercer término lo domina la rama real, y es el mismo coste que ya pagas en producción.

### 7.2 Tabla para los Builders (S = 2)

| $T_{\text{build}}$ | K = 5 | K = 10 | K = 20 |
|---|---|---|---|
| 1 h | 5 h | 10 h | 20 h |
| 4 h | 20 h | 40 h | 80 h |
| 8 h | 40 h | 80 h | 160 h |

La preparación de las series es despreciable al lado: ~10 min para K = 5, ~40 min para K = 20.

### 7.3 Disco

Por serie: el CSV (cientos de MB; se borra tras importar) y el `.dat` de SQX (~95 MB para 14 años de USA500 en el primer piloto). Con K = 20: unos pocos GB. Las series se conservan mientras la configuración siga vigente, para poder repetir el embudo sin regenerarlas.

### 7.4 Recomendación

Empezar con **K = 5 por rama**. Si la FDR sale claramente por debajo de 0,2 o por encima de 0,5, el resultado ya está decidido; si cae en medio, se amplía a 10. Como es una vez por configuración y se reutiliza mientras no cambie, incluso con 8 h por Builder es asumible.

---

## 8. Lo que ya se ha probado

### 8.1 Piloto 1 — USA500, barajado (2026-10-10)

| fase | tiempo |
|---|---|
| generar el CSV (221 MB) | 39,9 s |
| importar en SQX (con conversión a `.dat`) | 14,5 s |
| crear y configurar el proyecto (copiar y cambiar el símbolo) | 0,06 s |
| arrancar el conductor hasta que carga el proyecto | 11 s |
| **total** | **≈ 66 s** |

Todo por línea de comandos. Problemas encontrados, que han dado forma a este documento:

- el símbolo quedó en UTC y el real está en EST+07 → la zona horaria es obligatoria (sección 2.4);
- el símbolo sólo existía en el conductor → hay que importarlo en el master;
- barajar reasigna timestamps por posición y descuadra las horas → se sustituye por el volteo de signo (sección 2.2);
- el feed de USA500 empieza en 2012 → el periodo build de las dos ramas debe ser idéntico.

### 8.2 Piloto 2 — XAUUSD, volteo de signo, todo el histórico (2026-10-11)

| fase | tiempo | nota |
|---|---|---|
| generar la serie (7,97 M barras M1, 142.127 bloques H1) | 86 s, 4 GB de RAM | 82 s son escribir el CSV |
| importar en el custodio | 28 s | `timezone=EETUS` funciona: el feed queda en EST+07, igual que el real |
| clonar el proyecto cambiando sólo el feed | 0,05 s | 17 nombres de feed sustituidos en 6 tareas |

Bloqueos encontrados y resueltos a mano (a automatizar en F0): Python exige una ficha `assets/symbols/XAUUSD_SYN01.yaml` (copiada de la de XAUUSD), y otro bloqueo descrito en el informe del agente.

**Conclusión de los pilotos:** preparar cada serie cuesta ~2 min y es automatizable. **La viabilidad depende sólo de $T_{\text{build}}$.**

---

## 9. Riesgos y cómo se controlan

| riesgo | efecto | control |
|---|---|---|
| el generador conserva estructura explotable | el ruido es «demasiado bueno», la FDR sale alta sin motivo | F1 (autocorrelaciones) y F2 (prueba de humo); sensibilidad con bloque = 1 día |
| el generador destruye de más | el ruido es «demasiado fácil», la FDR sale baja | el volteo conserva volatilidad, rachas, perfil y deriva por construcción (sección 2.2); no usar la permutación de Masters |
| condición de parada distinta entre ramas | conteos no comparables | parada por número de estrategias (sección 3.2) |
| clones del genético | conteos inflados | familias (sección 4.2) |
| K pequeño | intervalos anchos | el criterio usa el límite superior; ampliar a K = 10 si LIMBO |
| el método no tiene potencia | una FDR alta no significaría nada | control positivo (F3) |
| diferencias de configuración entre ramas | la comparación no vale | clonar el proyecto cambiando sólo el feed (probado: 0,05 s); comprobar con un diff de los ficheros del proyecto |
| zona horaria o calendario distintos | filtros horarios en otras horas | F1 comprobación (2) |

---

## 10. Decisiones abiertas

1. **$T_{\text{build}}$** de producción y su condición de parada (F0). Fija K.
2. **Umbrales del criterio:** 0,2 y 0,5 son propuestas. Alternativa más estricta: PASA con FDR ≤ 0,1.
3. **Umbral de familias:** correlación semanal ≥ 0,9 para agrupar y ≥ 0,7 para la repetibilidad. Revisar con los datos del piloto F4.
4. **Otros mercados en la rama de ruido:** reales (propuesto) o sintéticos.
5. **Qué se hace con los pasos de lift ≈ 1:** quitar, recalibrar o mantener como anotación. Decisión del usuario tras F5.
6. **Nombre y ubicación de la tarea** en el pipeline (`mcpt_fabrica`) y si su resultado se guarda junto a cada estrategia (la FDR de su configuración).

---

## Referencias

- J. D. Schwager, *Hedge Fund Market Wizards* (2012), capítulo de Jaffray Woodriff: entrenar el mismo proceso contra un objetivo aleatorio y comparar.
- T. Masters, *Testing and Tuning Market Trading Systems: Algorithms in C++* (2018) y *Permutation and Randomization Tests for Trading System Development* (2020).
- Denelio, «A robust data mining workflow», sección 6 (MCPT de toda la fábrica, 10.000 repeticiones).
- J. D. Storey, «A direct approach to false discovery rates», *JRSS B* (2002): estimación de la proporción de nulos.
- QUSMA, «Doing the Jaffray Woodriff Thing (Kinda)» (2013): implementación con series sintéticas y algoritmo genético.
