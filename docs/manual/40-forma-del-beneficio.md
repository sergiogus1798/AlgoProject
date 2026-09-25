## 40. La forma del beneficio — ¿de qué pocas cosas depende el resultado?

### Qué pregunta responde

Una estrategia con mil operaciones y un Sharpe decente parece descansar sobre mil observaciones.
Casi nunca es así. Este comando lee la lista de operaciones —nada más: ni barras, ni SQX— y contesta
tres cosas distintas que apuntan todas al mismo sitio:

1. **Concentración.** ¿Cuánto del beneficio lo ponen las mejores operaciones, los mejores meses, el
   mejor año? ¿Sobrevive el resultado si le quitas las cinco mejores?
2. **Independencia.** ¿Se agrupan ganancias y pérdidas? Si se agrupan, barajar operaciones —que es
   lo que hace el Monte Carlo de SQX— **subestima la caída máxima**, y en la fase de cartera hay que
   remuestrear por bloques y no sueltas.
3. **Rotura.** ¿Cambió la media en algún punto de la muestra? Y si cambió, el tramo que describe la
   estrategia de hoy es el de después, no la media de todo.

### Cuándo lo usas, y cuándo no

**Lo usas** con una estrategia que ya ha pasado el retest OOS y tienes sus operaciones exportadas.
Tarda unos 3 segundos y no toca SQX.

**No lo usas como puerta.** Son tres diagnósticos sobre una estrategia: alguno fallará por azar
aunque la estrategia sea buena. Y la concentración **no es un fallo por sí sola**: un seguidor de
tendencia vive de unas pocas operaciones grandes por diseño. Lo que hace este número es montar la
comparación de verdad, que es contra entradas aleatorias con las mismas salidas (`26-nulos.md` y
`42-calidad-de-la-entrada.md`): si tu concentración se parece a la de un mono, el sesgo lo ponen las
salidas y no la señal.

**Un filtro nuevo sacado de aquí es una búsqueda nueva** y se anota en el ledger. Está escrito en el
PDF del que sale esto y no es una formalidad.

### Antes de empezar

Un `trades.parquet` exportado, por ejemplo con:

```bash
python3 -m sqx.export.export_trades --project XAUUSD --databank MC_Trades \
    --symbol XAUUSD_DukasM1_Infinox
```

### Cómo se ejecuta

```bash
python3 -m strategies.profitShape.report \
    --export ~/Desktop/AlgoData/raw/XAUUSD/MC_Trades/2026-09-19/trades.parquet \
    --strategy "Strategy 35.44.31"
```

| flag | obligatorio | qué hace |
|---|---|---|
| `--export` | sí | el `trades.parquet` |
| `--strategy` | sí | el nombre exacto con el que aparece en el export |
| `--set` | no | cambia un ajuste: `--set run.sample=IST` para leer la muestra de construcción |

**2,9 segundos** y no toca SQX.

### Qué produce

Sólo salida por pantalla, tres bloques. No escribe nada: lo que hay que conservar es la conclusión,
y ésa va al informe de la estrategia.

### Cómo se lee el resultado

**Bloque 1 — concentración.** `mejor 1 %` por encima del 100 % significa que sin esas operaciones la
estrategia pierde dinero. La tabla de recortes es la que de verdad decide: dice qué queda al quitar
las 5, 10 y 20 mejores. Y `media por operación` positiva con `mediana` negativa es la firma de que
todo depende de la cola.

**Bloque 2 — independencia.** Las tres pruebas miran cosas distintas y basta con que falle una:

| prueba | qué mira | cuándo preocupa |
|---|---|---|
| rachas (Wald-Wolfowitz) | si ganadoras y perdedoras se agrupan | `z` por debajo de −2 |
| Ljung-Box | si el tamaño del resultado se autocorrela | `p` por debajo de 0,05 |
| racha perdedora | si la racha real es más larga que barajando | `p` por debajo de 0,05 |

Si sale `clustered`, **eso es una instrucción para la fase de cartera**: bootstrap por bloques, no
barajado de operaciones. El `último retardo con autocorrelación` es el suelo del tamaño de bloque.

**Bloque 3 — rotura.** `CUSUM sup` por encima de 1,36 rechaza la estabilidad al 5 %. La tabla de los
dos lados se imprime siempre, **también cuando no rechaza**, y ahí está la trampa importante ⚠️: los
dos lados pueden ser clarísimamente distintos y el test no rechazar, porque la dispersión por
operación es enorme. Cuando no rechaza, la partición **no es una rotura que el test haya
encontrado** y no se puede contar como tal.

### Un ejemplo completo

```
Strategy 35.44.31 · muestra OOS1 · 1119 operaciones

-- 1 · concentración del beneficio
mejor 1 % de las operaciones 117.1% del total · mejor 5 % 404.6%
media por operación 16.64 · mediana -14.38
         expectancy  sharpe  profit_factor
removed
0            16.644   0.031          1.091
5             6.520   0.013          1.036
10           -1.440  -0.003          0.992
20          -15.022  -0.031          0.919
mejores 3 meses 82.9% · mejor año 2020 99.1% · sin él, esperanza 0.22 sobre 727 operaciones
-> few_trades: el resultado lo sostienen unas pocas operaciones

-- 2 · independencia de las operaciones
rachas 575 contra 559.2 esperadas, z +0.94 (p 0.345)
Ljung-Box sobre operaciones p 0.670 · sobre P&L diario p 0.981 · último retardo con autocorrelación 0
racha perdedora 9 contra mediana 10 y p95 14 barajando (p 0.805)
-> independent: nada contradice que las operaciones sean independientes

-- 7 · ¿cambió la media dentro de la muestra?
CUSUM sup 1.01 contra el crítico 1.36 · candidato en la operación 277 (25% de la muestra, 2020-08-18)
           n    mean  sharpe
segment
before   278  82.548   0.165
after    841  -5.141  -0.009
-> stable: nada indica que la media haya cambiado dentro de la muestra
```

**Qué dice esto de verdad:**

- Las **56 mejores operaciones de 1.119** (el 5 %) aportan cuatro veces el beneficio total: sin
  ellas la estrategia pierde. Quitando sólo **diez**, la esperanza ya es negativa.
- El **99 % del beneficio es de 2020**. Sin ese año, 727 operaciones dejan una esperanza de 0,22 $,
  que es cero con más pasos.
- Y sin embargo la secuencia **no** está agrupada y el CUSUM **no** rechaza. Las tres lecturas no
  se contradicen: esta estrategia no tiene un problema de orden ni de cambio de régimen, tiene un
  problema de que su resultado son unas pocas operaciones de un solo año.
- Fíjate en el bloque 3: 82,5 $ por operación antes y −5,1 $ después, y el test dice `stable`.
  Exactamente la trampa descrita arriba.

### Qué NO te dice

- **Por qué.** La posición de una rotura es un punto de una secuencia, no una explicación, y puede
  caer donde cambió el mercado y no donde cambió la estrategia.
- **Qué tamaño de bloque usar** en el bootstrap de cartera. Da el suelo (el último retardo
  significativo); la selección automática de Politis-White no está implementada.
- **Si la concentración es mala.** Para eso hace falta la comparación contra el mono, que está en
  otro sitio.

### Si algo falla

- `KeyError` con el nombre de la estrategia: el nombre tiene que ser **exacto**, y SQX a veces añade
  un sufijo como `(1)`. Míralos con
  `python3 -c "import pandas as pd; print(pd.read_parquet('...').strategy.unique()[:20])"`.
- Muy pocas operaciones: por debajo de 200 el bloque 3 no se imprime a propósito — un supremo sobre
  una serie corta lo decide su propio ruido.
