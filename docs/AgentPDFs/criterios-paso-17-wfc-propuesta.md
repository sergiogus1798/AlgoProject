# Paso 17 — Walk Forward Correlation (WFC): propuesta de rediseño

**Fecha:** 2026-10-07 · **Alcance:** el estudio del paso 17 (`studies/optimisation/wfc/`).
**Referencia:** `criterios-paso-17-wfc-2026-10-07`. Complementa la propuesta del paso 16.5 (`criterios-paso-16.5-nube-propuesta.md`), de la que sale el lote de variantes.

---

## 0. La pregunta del paso

> **Si ordeno las variantes de una madre por lo que ganaron dentro de muestra, ¿ese orden se parece al de fuera? Y lo que elegiría un optimizador, ¿gana fuera?**

La primera parte es la pregunta de Tinsley, y su medida principal sigue siendo la **correlación de rangos** (ρ de Spearman). La segunda es lo que la ρ no ve: la ρ mide si la nube está inclinada, no en qué cuadrante está. En la corrida de referencia, G tiene 324 de 332 variantes ganando dentro y fuera y ρ = 0,01; 13.3.390 tiene 134 de 220 ganando dentro y perdiendo fuera y ρ = +0,35.

**Qué tiene de distinto este paso:** es la **primera prueba desde el paso 8 que lee datos que nadie ha usado para elegir** (oos2). Por eso su PASA puede contar como evidencia, a diferencia de los pasos 14 a 16. Lo que dice ese PASA es «dentro de esta familia, elegir por el pasado no lleva a algo que pierda fuera»; no dice que la madre tenga ventaja.

---

## 1. Las tres composiciones

| # | dentro (IS) | fuera (OOS) | papel |
|---|---|---|---|
| **1** | build+oos1 | oos2 | **decide** |
| 2 | build | oos1+oos2 | se anota |
| 3 | build | oos2 | se anota |

**Por qué decide la (1).** Lo que el WFC imita es a un optimizador eligiendo con todo lo que ha visto. Cuando la madre llega aquí, ya se han visto build (donde se optimizó) y oos1 (con el que el paso 8 la eligió). Lo único que nadie ha visto es oos2.

**Cómo se leen la (2) y la (3) al lado de la (1):**

| comparación | qué cambia | qué dice |
|---|---|---|
| (3) frente a (1) | el lado de dentro: con o sin oos1 | si la (1) sale claramente mejor, haber visto oos1 ayuda a elegir; si sale peor, oos1 empuja la elección hacia algo que no se repite |
| (2) frente a (3) | el lado de fuera: con o sin oos1 | si la (2) sale claramente mejor, oos1 fue un periodo especialmente bueno para la familia; si sale peor, especialmente malo |

**Lo que no se puede leer.** Las tres comparten oos2: que coincidan **no es una confirmación**. Cada una lleva su propio nulo (sección 4), así que se sabe si una diferencia supera el ruido.

**Bloque ciego.** Las tres leen oos2, así que se calculan juntas, dentro del bloque ciego (17, 18, 18.5, 19), y sólo después de que los criterios de esta propuesta estén escritos en `criteria.yaml`. Se apuntan las tres en el ledger como miradas (hoy sólo se apunta la pedida).

Se quita la composición `build → oos1` sola, que hoy también se calcula.

---

## 2. Qué variantes entran

Del lote del paso 16.5:

1. **Fuera los controles** (canarios y pares inertes) y los **duplicados exactos** (mismo resultado al céntimo en todos los tramos). Hoy G cuenta 332 puntos de los que sólo 203 son distintos, y F lleva 9 copias exactas de la madre.
2. **Suelo de dentro:** al menos $15 \times k$ operaciones en la ventana de dentro, con $k$ = número de parámetros **vivos** (no cuentan los congelados ni los desplazamientos). Es un suelo de grados de libertad: con pocas operaciones por parámetro, una variante se ajusta al ruido.
3. **Suelo de fuera:** al menos **10 operaciones por año** de la ventana de fuera. Fuera no hay nada que ajustar; sólo hace falta que el exceso por año se pueda medir.

| ventana de fuera | años | suelo de fuera |
|---|---|---|
| oos2 | 2,75 | 28 |
| oos1+oos2 | 6,75 | 68 |

| madre | vivos | suelo de dentro (15 × k) | operaciones de la madre en build+oos1 |
|---|---|---|---|
| C | 12 | 180 | 287 |
| E | 6 | 90 | 227 |
| G | 13 | 195 | 324 |

**Comprobación:** si la madre no cumple el suelo, se avisa y el suelo no se aplica a esa madre.

**Sensibilidad:** se anota la ρ de la composición (1) también sin suelos. Las variantes que operan poco no son una muestra al azar: son una zona concreta del espacio. En la corrida de referencia, bajar el suelo por lado de 50 a 30 movió la ρ de G de 0,01 a 0,28.

---

## 3. La medida: el exceso por año

Con las operaciones de cada variante (el retest las exporta todas), el exceso de cada operación es el del paso 14:

$$\text{exceso}_j = \text{P/L}_j - \text{lado}_j \times \text{lotes}_j \times vp \times \sum_{\text{barras } b \text{ dentro}} \mu_{\text{año}(b)}$$

con $\mu_{\text{año}}$ la deriva media por barra del año natural de cada barra. Para cada variante $i$ y cada ventana $W$:

$$e^{W}_i = \frac{\sum_{j \in W} \text{exceso}_j}{\text{años de } W}$$

*Decisión del dueño, 2026-10-08: la deriva que se resta es la del proyecto (año de apertura, ponderada por 1/ATR — la misma del paso 8), no la de esta fórmula.*

**Por qué el exceso y no el beneficio neto.** El documento del paso 17 mide que, sin ventaja, la ρ la decide sobre todo **quién opera más**: en un periodo alcista, las variantes más expuestas ganan más dentro y fuera, y eso fabrica un orden que no viene de la lógica. El exceso quita lo que el mercado pagó por estar dentro.

**Por qué por año.** Las ventanas tienen longitudes distintas (build+oos1 son unos 12 años; oos2, 2,75). Por año, el nivel de dentro y el de fuera se pueden comparar.

Para el nulo hace falta además la **serie diaria del exceso** de cada variante en la ventana de fuera, $d_{i,t}$: la ganancia del día menos la deriva cobrada ese día por la posición abierta.

---

## 4. La correlación y su nulo

### 4.1 La ρ

$$\rho = \operatorname{Spearman}\left(e^{\text{IS}}_i,\; e^{\text{OOS}}_i\right)$$

sobre las variantes que pasan los filtros de la sección 2.

### 4.2 Por qué no vale el intervalo de Fisher

El intervalo de hoy trata 300 variantes como 300 observaciones independientes. No lo son: operan los mismos días y, si un día fue malo, fue malo para casi todas. Medido en la corrida de referencia (build → oos1), la ρ de una familia sin ventaja tiene una desviación de 0,09 a 0,41 (mediana 0,26), no los 0,05–0,07 que supone la fórmula: un «N efectivo» de 8 a 145 (mediana 17) donde la fórmula usa de 220 a 477. Con la fórmula, una familia sin ventaja sale «Fiable» un 8 % de las veces en mediana y hasta un 22,5 %; la fórmula supone prácticamente un 0 %.

### 4.3 El nulo de volteo de signos

Fabrica «la misma familia, sin ventaja», conservando cómo se parecen las variantes entre sí:

1. a cada **día** de la ventana de fuera se le sortea un signo $s_t \in \{+1, -1\}$, **el mismo para todas las variantes**;
2. el exceso de fuera de cada variante en ese sorteo es $e^{\text{OOS},(b)}_i = \frac{1}{\text{años}}\sum_t s_t\, d_{i,t}$;
3. el lado de dentro se deja fijo;
4. se calcula $\rho^{(b)} = \operatorname{Spearman}\big(e^{\text{IS}}_i,\; e^{\text{OOS},(b)}_i\big)$;
5. se repite $B = 2000$ veces.

Con eso, para la ρ observada:

$$p_{+} = \frac{1 + \#\{b : \rho^{(b)} \ge \rho\}}{1 + B} \qquad p_{-} = \frac{1 + \#\{b : \rho^{(b)} \le \rho\}}{1 + B}$$

### 4.4 Clasificación del orden

| orden | condición | lectura |
|---|---|---|
| **positivo** | $p_+ \le 0{,}05$ | lo mejor de dentro tiende a ser lo mejor de fuera, más de lo que daría el ruido |
| **neutro** | ni lo uno ni lo otro | el orden de dentro no dice nada fuera |
| **perverso** | $p_- \le 0{,}05$ | lo mejor de dentro tiende a ser lo peor de fuera |

**El 0,30 de Tinsley** se mantiene como etiqueta: un orden positivo con $\rho \ge 0{,}30$ se anota como **«fuerte»**. No cambia el estado.

**Por construcción**, una familia cuyo orden es puro ruido sale «perversa» como mucho un 5 % de las veces. Es la tasa de falsos positivos de esa parte de la regla.

---

## 5. El nivel: ¿lo que elegiría el optimizador gana fuera?

$$\tilde e^{\,\text{OOS}}_{\text{top}} = \operatorname{mediana}\left(e^{\text{OOS}}_i \;:\; i \in \text{top } 20\,\%\ \text{por } e^{\text{IS}}\right)$$

El top son las variantes con $e^{\text{IS}}$ mayor o igual que el percentil 80 de dentro (con empates puede ser algo más del 20 %; se anota cuántas son).

**Gana** si $\tilde e^{\,\text{OOS}}_{\text{top}} > 0$: el grupo que elegiría un optimizador tiene, en su variante típica, exceso positivo fuera de muestra.

---

## 6. El criterio

Sólo con la composición (1):

| orden \ nivel | el top gana fuera | el top no gana fuera |
|---|---|---|
| **positivo** | **PASA**: elegir sirve y lo elegido gana | **NO PASA**: el orden se mantiene, pero todo pierde |
| **neutro** | **PASA**: meseta plana; los parámetros dan igual y la idea gana | **NO PASA** |
| **perverso** | **LIMBO**: gana, pero optimizar empeora; en real habría que operar el centro de la meseta, no el óptimo | **NO PASA** |
| sin dato | LIMBO (menos de 30 variantes tras los filtros, o la madre sin operaciones en oos2) | |

**Lo que corrige respecto a hoy:**

- **E y G** (todas ganan; el orden da igual) salen «No fiable» con el veredicto actual y el paso 20 las marca DESCARTAR. Con este criterio, si su top gana en oos2, PASA, que es lo que son: una meseta plana.
- **Ningún orden salva a una familia cuyo top pierde fuera** (el caso de 13.3.390 y de F, que hoy pueden tener la persistencia más alta).
- **«Indeciso = fabrica más puntos»** desaparece: más variantes no añaden caminos de precios.

```yaml
"17":
  cut: <databank del bloque ciego>
  segment: oos2
  rules:
    - fact: wfc.c1.estado          # PASA / LIMBO / NO PASA según la tabla
      pass: "== pasa"
      fail: "== no_pasa"
  missing: limbo
```

Los nombres de los hechos son orientativos (sección 9).

---

## 7. Lo que se anota sin decidir

| hecho | qué es |
|---|---|
| ρ, $p_+$, $p_-$, p5 y p95 del nulo, de las **tres** composiciones | la medida de Tinsley con su incertidumbre real |
| etiqueta «fuerte» | orden positivo con $\rho \ge 0{,}30$ |
| $\tilde e^{\,\text{OOS}}_{\text{top}}$ y $\tilde e^{\,\text{OOS}}_{\text{todas}}$, de las tres | el nivel |
| $R_{\text{sel}}$ | retención de la prima de selección (abajo) |
| ρ de la (1) sin suelos de operaciones | sensibilidad al suelo |
| cuadrantes de la nube (++, +−, −+, −−) | en qué cuadrante está, que la ρ no ve |
| número de variantes por filtro | trazabilidad |

**Retención de la prima de selección.** Cuánto de la ventaja que tiene el top dentro sobrevive fuera:

$$R_{\text{sel}} = \frac{\tilde e^{\,\text{OOS}}_{\text{top}} - \tilde e^{\,\text{OOS}}_{\text{todas}}}{\tilde e^{\,\text{IS}}_{\text{top}} - \tilde e^{\,\text{IS}}_{\text{todas}}}$$

1 = se conserva entera; 0 = elegir no sirve; negativo = selección perversa. Es la misma idea de retención de los pasos 8 a 14, aplicada a la selección. Se acompaña de sus percentiles en el mismo nulo de volteo.

**La figura** de la ventana se mantiene (la nube con sus cuadrantes), con la recta y la etiqueta de la **ρ de Spearman**, no del Pearson.

---

## 8. Lo que se quita

| pieza | motivo |
|---|---|
| veredicto Fiable / Indeciso / No fiable con el intervalo de Fisher | el intervalo es de 2 a 7 veces demasiado estrecho (sección 4.2) |
| su lectura en el paso 20 con `sin_fallo` | se sustituye por el estado de la sección 6 |
| persistencia del top y su exceso | dice lo mismo que la ρ, sólo en orden y con más ruido (nulo de ±0,17 a ±0,34); en la corrida, ninguna madre la supera en las dos ventanas |
| `exceso_persistencia_minimo` | además mezcla oos2 con una ficha calibrada sólo en oos1 |
| mediana del ratio de Sharpe fuera/dentro | su nulo va de −1,2 a +1,2; divide un Sharpe de SQX por uno de Python |
| Pearson y pendiente | la pendiente depende de la longitud de las ventanas; Pearson, de un punto suelto |
| composición `build → oos1` sola | sustituida por las tres de la sección 1 |
| «Spearman 44,53 %» en la tarjeta | un coeficiente no es un porcentaje |
| Sharpe «superpuestos» mezclados en un montón | mismo defecto que el panel 2 del SPP |

---

## 9. Arreglos de código sin los que no hay regla posible

1. **El extractor de hechos** devuelve 0 filas: busca carpetas y el WFC escribe un fichero (`pipeline/autopilot/facts.py:222`). Afecta también a 18 y 18.5.
2. **La cola del piloto** añade el 17 «a ciegas» y nunca lo juzga (`pipeline/autopilot/tail.py:107-110`). Hay que juzgarlo al cerrar el bloque ciego.
3. **El nombre** que firma el resultado (`Strategy_10.11.484`) no casa con el del databank (`Strategy 10.11.484`).
4. **El sellado de oos2** debe estar en el estudio, no depender de `ALGO_AUTONOMOUS`.
5. **Las tres composiciones** con claves distintas: hoy `build__oos1+oos2` y `build+oos1__oos2` colapsan en la misma clave.
6. **El rho, sus p y los percentiles del nulo como números**, no como texto.

---

## 10. Decisiones abiertas

1. **El paso 20:** cómo combina el estado del WFC con los del CSCV, el 18.5 y la WFM. Se decide al llegar al 20.
2. **Calibración:** pasar una población sin ventaja (y una con ventaja plantada) por los pasos 16.5 y 17 para medir cuántas caen en cada casilla de la tabla. La parte «perversa» está calibrada por construcción; la de nivel no.
3. **Top del 20 %:** es el de hoy. Con 1.000 variantes son 200; se puede revisar si conviene un 10 %.
4. **Número de sorteos del nulo:** 2.000 da un error de simulación de ±0,5 puntos en un p de 0,05.
