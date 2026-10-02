# 6 · Etiquetar la taxonomía de bloques — siete familias

> **Ampliado el 2026-10-01 a siete familias** (decisión del dueño al diseñar el director de
> investigación, `docs/AgentPDFs/director-de-investigacion-2026-10-01.md` §0 y §5). El encargo se
> escribió el 2026-09-24 para tres familias con un «no se inventan más»; el dueño lo cambió: ahora son
> **las siete de la cobertura** — ruptura, tendencia, reversión, momentum, volatilidad, patrón y sesión.
> Cada bloque lleva siete pesos. El resto del diseño (la escala, la regla de `form`, el criterio sobre
> los `0`) no cambia.
>
> **Estado: hecho el 2026-10-01** en una pasada por reglas (§11). Los 767 bloques llevan siete pesos; tú
> corriges **por regla**, no bloque a bloque (§11 es la tabla).

El trabajo cabe en una frase: **rellenar el campo `archetypes` de cada bloque de
`sqx/blocks/taxonomy.yaml`.** Nada más.

---

## 1 · Qué existe ya, y por qué

El builder de StrategyQuant X puede sortear **767 bloques**. Con tantos, genera estrategias que
mezclan un filtro de reversión a la media con un disparador de ruptura: combinaciones que dan buen
backtest y no describen ninguna hipótesis. El dueño quiere que, al construir sobre una plantilla de
ruptura, el builder solo pueda sortear bloques que peguen con una ruptura. Y el director de
investigación necesita saber, de cada bloque, a qué tipo de idea sirve.

```
sqx/blocks/taxonomy.yaml     767 bloques en 83 categorías
```

Una fila:

```yaml
BookTriggers_user:                    # la categoría de SQX, es la clave padre
  CBlock_BBBreakoutUp:
    roles: [signal]                   # derivado, NO lo toques
    origin: own                       # derivado, NO lo toques
    form: BBBreakoutUp                # derivado, NO lo toques
    groups: [BookTriggers]            # derivado, NO lo toques
    archetypes: {breakout: 3, mean_reversion: 0, trend: 1, momentum: 2, volatility: 1, pattern: 1, session: 1}
```

**Todo lo que no sea `archetypes` se regenera de la instalación y se pisa** (`python3 -m sqx.blocks.taxonomy`
conserva las etiquetas).

## 2 · Lo único que se escribe: siete pesos

`archetypes` es **un peso por familia**, siempre las siete claves:

| familia | clave | qué es |
|---|---|---|
| ruptura | `breakout` | el precio sale de un rango, un nivel o una banda, y se espera continuación |
| reversión | `mean_reversion` | el precio se ha estirado respecto de un centro, y se espera vuelta |
| tendencia | `trend` | la dirección persiste: orden de medias, pendiente, fuerza direccional |
| momentum | `momentum` | la velocidad o la aceleración del precio: osciladores de impulso, cruces de señal, pendiente de un oscilador |
| volatilidad | `volatility` | el tamaño del movimiento, no su dirección: ATR, anchura de banda, desviación, compresión y expansión |
| patrón | `pattern` | una forma de barras o de velas (envolventes, martillos, huecos, fractales) |
| sesión | `session` | cuándo ocurre: hora, día de la semana, mes, máximos y mínimos de una sesión |

Las claves de las tres primeras son las de siempre; las cuatro nuevas son las mismas palabras que el
registro de cobertura de la ventana (`ui/daemon/coverage.py`).

| valor | significa |
|---|---|
| `0` | **excluir**: este bloque contradice la tesis de esa familia |
| `1` | neutro: puede aparecer, sin preferencia |
| `2` | encaja |
| `3` | es característico de esa familia |

Un bloque con `archetypes: {}` queda **sin etiquetar** y no entra en ninguna paleta. Ya no hay
ninguno.

## 3 · La regla que decide el 90 % de los casos

**Etiqueta por lo que dice `form`, nunca por el nombre del indicador.** Un mismo indicador produce
bloques opuestos:

| bloque | `form` | por qué |
|---|---|---|
| `BBBarOpensAboveUpAfterOpenBelow` | abre por encima de la banda superior tras haber abierto por debajo | ruptura: el precio escapa de la banda |
| `BBBarOpensBelowUpAfterOpenAbove` | abre dentro de la banda tras haber abierto por encima | reentrada: reversión, y `breakout: 0` |

El primero es una **transición hacia fuera**; el segundo, una **reentrada**. Casi todas las familias
de bloques de SQX vienen en ambas formas y significan cosas distintas.

## 4 · Las reglas de criterio

1. **Un `0` es la decisión cara, y hay que justificarla.** Excluir estrecha la búsqueda; solo se
   pone cuando el bloque **contradice** la tesis, no cuando «no es muy de esa familia» (para eso
   está el `1`). De 5.369 pesos, solo 38 son `0`, y 14 de ellos son los dos bloques en ceros (§11).
2. **Un bloque puede ser característico de dos familias.** `ATR` mide volatilidad y lo usan tanto la
   ruptura como la reversión. Una oscilación acotada (RSI) es reversión y momentum a la vez.
3. **Lo neutro se etiqueta neutro.** Comparadores, constantes y precios crudos (`Close`, `High`,
   `Ask`): `1` en las siete.
4. **La dirección la pone la plantilla, no el bloque.** Con la regla dura 13 (una dirección por
   plantilla) «cierra por debajo de la banda inferior» es reversión para un largo y ruptura para un
   corto. Esos bloques de estado llevan `2` en ruptura **y** en reversión (§12, pregunta 1).
5. **Un bloque no clasificable lleva siete `0`** y se lista; queda fuera de toda paleta hasta que el
   dueño diga qué calcula (§12).

## 5 · Qué hace una paleta con esto

Una paleta construida con estas etiquetas gobierna **solo los huecos libres** de una plantilla. Un
hueco **atado a un grupo aleatorio** sortea ese grupo e ignora la paleta; un bloque **fijo** se salta
la paleta también (`knowhow/authoring/block-vocabulary.md`). Por eso `groups` está en la tabla:
no cambia cómo se etiqueta un bloque, pero explica por qué una etiqueta no siempre llega al builder.

## 6 · Cómo se consulta

```python
from sqx.blocks.taxonomy import family_blocks
family_blocks("volatility", min_weight=2)             # {clave de bloque: peso}, de mayor a menor
family_blocks("session", 3, role="signal")            # solo los que juegan de señal
```

Las paletas (`sqx/blocks/palette.py`) leen la columna de su `family`; `FAMILY_ES` tiene las siete.
Las cuatro paletas actuales (`ruptura_base`, `reversion_base`, `tendencia_base`, `timeRangeBreakout`)
siguen siendo de `breakout`, `mean_reversion` y `trend`, con sus `overrides` a mano, que ganan sobre la
taxonomía: no se han reescrito. No hay todavía paleta base de las cuatro familias nuevas (§12).

## 7 · El orden de trabajo original (tres familias, 2026-09-24)

Por lotes: propios del dueño (171) → `Comparisons`, `Price`, `Bar And Time` → `Indicators` → categorías
nativas. Con la ampliación el orden dejó de importar: se hizo en **una pasada por tipo de bloque**
(§11), porque 752 etiquetas a mano no se pueden corregir, y 43 tipos sí.

## 8 · Lo que NO se toca

- Solo `archetypes` en `taxonomy.yaml`; lo demás se regenera.
- Ninguna instalación de SQX, ningún worker, ningún build. No gasta CPU.
- No se reordena el fichero ni se añaden campos. Las familias son las siete.

## 9 · Cómo se cierra

`python3 -m sqx.blocks.taxonomy` relee la instalación y conserva lo etiquetado: su salida tiene que
decir `etiquetas 767 puestas, 0 por poner`. **No se ha ejecutado en la tanda del 2026-10-01** (lee
la instalación del maestro y el encargo prohibía tocar SQX); correrlo es la verificación pendiente.
La estructura la vigila `tests/test_taxonomy.py`: 767 bloques, siete pesos cada uno, de 0 a 3.

## 10 · Los 15 bloques que ya estaban etiquetados

Llevaban **un solo peso** (`breakout`), no tres como decía el dossier. Se conservó ese `breakout`
tal cual y los otros seis salen de las reglas de §11: con `breakout: 2`
`ATRRising`, `ATRPercentRankAboveLevel`, `ATRPercentRankRising`, `StdDevRising`, `CBlock_StrongCandle`;
con `breakout: 3` `CBlock_BreakoutDonchianLong`, `CBlock_CandleBreakoutLong`, `CBlock_TimeBreakoutLong`,
`DonchianChannels`, `Highest`, `HighestInRange`, `SessionHigh`, `CBlock_ATRRankHighVol`,
`CBlock_SqueezeOff`, `CBlock_WAEPosAboveExplosion`.

## 11 · Las reglas, por tipo de bloque (corrige aquí)

Orden de los pesos: **ruptura · reversión · tendencia · momentum · volatilidad · patrón · sesión**.
Cada fila es un *tipo* de bloque; cambiar la fila cambia todos sus bloques de golpe (el script que las
aplica está en `scratch/research-director/label_taxonomy.py`, fuera de git). Entre paréntesis, cuántos
bloques.

### Neutros y de sesión

| tipo | bloques | R · Rv · T · M · V · P · S | por qué |
|---|---|---|---|
| comparadores (`IsGreater`, `CrossesAbove`, `Not`…), constantes, `FixedPips`, `AlwaysTrue/False` (29) | `Comparisons`, `Other`, `Bar Range` | 1 · 1 · 1 · 1 · 1 · 1 · 1 | no son de ninguna familia |
| precios crudos (`Close`, `Ask`, `Open`…) (6) | `Price` | 1 en todo | idem |
| precios del periodo anterior (`HighD`, `CloseW`, `OpenM`…) (12) | `Price` | 2 · 2 · 1 · 1 · 1 · 1 · 2 | niveles que sirven de ruptura y de rechazo, y dependen del calendario |
| máx./mín. de sesión (`SessionHigh/Low`) (2) | `Price` | 3 · 1 · 1 · 1 · 1 · 1 · 3 | ruptura de rango de sesión |
| apertura/cierre de sesión (2) | `Price` | 1 · 1 · 1 · 1 · 1 · 1 · 3 | es un momento del día |
| Heiken Ashi (4) | `Price` | 1 · 1 · 2 · 1 · 1 · 2 · 1 | velas suavizadas: tendencia y forma |
| hora, minuto, día de la semana (14) | `Bar And Time` | 1 · 1 · 1 · 1 · 1 · 1 · 3 | sesión pura |
| mes, semana del mes, primer/último día (9) | `Bar And Time` | 1 · 1 · 1 · 1 · 1 · 1 · 2 | estacionalidad, más débil que la hora |

### Osciladores, impulso y distancia

| tipo | bloques | R · Rv · T · M · V · P · S | por qué |
|---|---|---|---|
| oscilador acotado, cruce o estado respecto de un nivel (RSI, Estocástico, CCI, %R, DeMarker, MFI, Laguerre, DVO, RVI, Schaff, DSS, QQE, WaveTrend, Smoothed RSI) (≈54+) | nativas | 1 · 3 · 1 · 2 · 1 · 1 · 1 | el extremo es sobrecompra/sobreventa: reversión |
| oscilador, cruce de línea o de señal (22) | nativas | 1 · 2 · 1 · 3 · 1 · 1 · 1 | cruce de impulso |
| oscilador, sube/baja (29) | nativas | 1 · 1 · 1 · 3 · 1 · 1 · 1 | la dirección del impulso |
| oscilador, cambia de dirección (18) | nativas | 1 · 2 · 1 · 3 · 1 · 1 · 1 | giro: momentum, y es un disparador de reversión |
| impulso no acotado: MACD, OSMA, Momentum, ROC, AO, Bulls/Bears (nivel, línea, pendiente) (≈52) | nativas | 1 · 1 · 2 · 3 · 1 · 1 · 1 | velocidad del precio, con sesgo de tendencia |
| impulso, giro (12) | nativas | 1 · 2 · 1 · 3 · 1 · 1 · 1 | idem de los osciladores |
| distancia al centro: Disparity, DPO, CMMA (nivel/cruce) (14) | nativas y propias | 1 · 3 · 1 · 1–2 · 1 · 1 · 1 | cuánto se ha alejado: reversión |
| distancia, sube/baja (2) | propias | 1 · 1 · 2 · 3 · 1 · 1 · 1 | cambia la distancia: impulso |
| `Directional Momentum` propios (6) | propias | 1 · 1 · 2 · 3 · 1–2 · 1 · 1 | el dueño los nombró momentum |
| Woodies CCI: tendencia/ZLR (4), Famir (2), Vegas (2), ruptura de cero (2) | nativas | tendencia 1·1·3·2; Famir 1·3·1·2; Vegas 1·2·1·2; ruptura de cero 1·1·2·3 | la lógica del sistema Woodies |

### Tendencia

| tipo | bloques | R · Rv · T · M · V · P · S | por qué |
|---|---|---|---|
| medias y direccionales: MA, HMA, KAMA, DEMA, LinReg, VWAP, SuperTrend, PSAR, Vortex, Gann, Didi, DI, Aroon, Ehlers MAMA (estado, línea, pendiente) (≈110) | nativas y propias | 1 · 1 · 3 · 2 · 1 · 1 · 1 | la dirección persiste |
| tendencia, giro (8) | nativas | 1 · 1 · 2 · 2 · 1 · 1 · 1 | cambio de dirección: tendencia más débil |
| «abre por encima de la media tras abrir por debajo» y cruces de medias (4+8) | nativas y `CrossMAs` | 2 · 1 · 2–3 · 2 · 1 · 1 · 1 | cruce: transición |
| VWAP anclado: estado respecto del precio (2) / pendiente (4) | nativas | 1·2·2·1·1·1·2 / 1·1·3·2·1·1·2 | ancla de sesión: sirve de centro y de tendencia |
| ADX alto/sube/cruza hacia arriba (3) | nativas | 2 · 1 · 3 · 1 · 1 · 1 · 1 | fuerza de tendencia |
| ADX bajo/baja/cruza hacia abajo (3) | nativas | 1 · 2 · 1 · 1 · 1 · 1 · 1 | rango: reversión |
| Ichimoku: ruptura de la nube (2) | nativas | 3 · **0** · 2 · 1 · 1 · 1 · 1 | ruptura estructural |
| `SuperTrendInRange` (1) | nativas | 1 · 3 · **0** · 1 · 1 · 1 · 1 | «sin tendencia»: contradice tendencia |

### Bandas, extremos y rupturas

| tipo | bloques | R · Rv · T · M · V · P · S | por qué |
|---|---|---|---|
| BB/KC/Highest/Lowest: abre fuera de la banda tras abrir dentro (6) | nativas | 3 · 1 · 1 · 1 · 1 · 1 · 1 | ruptura de manual |
| **reentrada**: abre dentro tras abrir fuera (6) | nativas | **0** · 3 · 1 · 1 · 1 · 1 · 1 | la ruptura ha fallado: contradice continuación |
| cierra/abre fuera del borde exterior (estado) (8) | nativas | 2 · 2 · 1 · 1 · 1 · 1 · 1 | **ambiguo por dirección** (§12, pregunta 1) |
| cierra/abre dentro del borde (estado) (8) | nativas | 1 · 2 · 1 · 1 · 1 · 1 · 1 | vuelta al centro |
| banda superior sube / inferior baja (expansión) (4) | nativas | 2 · 1 · 1 · 1 · 3 · 1 · 1 | la volatilidad se abre |
| banda superior baja / inferior sube (contracción) (4) | nativas | 1 · 2 · 1 · 1 · 3 · 1 · 1 | la volatilidad se cierra |
| Donchian, Highest, Lowest, ruptura por tiempo, ruptura por ATR (propios) | propias y `Indicators` | 3 · **0** o 1 · 1–2 · 1–2 · 1–2 · 1 · 1–2 | ruptura de rango; los propios llevan `0` en reversión |
| `CBBBreakoutUp/Down` (2) | propias | 3 · **0** · 1 · 2 · 1 · 1 · 1 | cruce de la banda: ruptura |

### Volatilidad y régimen

| tipo | bloques | R · Rv · T · M · V · P · S | por qué |
|---|---|---|---|
| ATR, ATR %, ATR rank, StdDev, Ulcer: sube/mayor/cruza arriba (13) | nativas | 2 · 1 · 1 · 1 · 3 · 1 · 1 | expansión |
| ídem: baja/menor/cruza abajo (13) | nativas | 1 · 2 · 1 · 1 · 3 · 1 · 1 | compresión |
| `Indicators` de rango y volatilidad (ATR, BB width, TrueRange, StdDev, Ulcer, CUSUM, WAE…) | `Indicators` | 2 · 1 · 1 · 1 · 3 · 1 · 1 | miden tamaño, no dirección |
| Choppiness, CSSA, Entropía (nativos y de `Indicators`) | nativas | 1 · 2 · 2 · 1 · 2 · 1 · 1 | régimen: sin dirección propia |
| Choppy (>61,8) / Trending (<38,2) propios | propias | 1·3·**0**·1·1·1·1 / 1·**0**·3·1·1·1·1 | umbrales explícitos |
| Hurst >0,5 / <0,5 propios | propias | 1·**0**·3·1·1·1·1 / 1·3·**0**·1·1·1·1 | persistencia frente a antipersistencia |
| Entropía alta (desorden) / baja | propias | 1·2·**0**·… / 1·1·2·… | desorden contradice tendencia |
| KER alto / bajo | nativas | 2·1·3·… / 1·3·1·… | eficiencia = tendencia |
| `VolatilityRegime_user`: vol alta y Squeeze off | propias | 3 · 1 · 1 · 1 · 3 · 1 · 1 | explosión |
| ídem: vol baja / Squeeze on | propias | 1 · 2 · 1 · 1 · 3 · 1 · 1 / 2 · 2 · 1 · 1 · 3 · 1 · 1 | compresión: espera de ruptura |
| `StructuralBreak_user`: KS on / Wasserstein alto | propias | 2 · 1 · 1 · 1 · 3 · 1 · 1 | cambio de distribución |
| ídem: KS off / Wasserstein bajo | propias | 1 · 2 · 1 · 1 · 2 · 1 · 1 | distribución estable |
| TTM Squeeze (momentum) (4) y Squeeze propios | nativas y propias | 1 · 1 · 2 · 3 · 2 · 1 · 1 | momentum bajo compresión |
| volumen medio / volumen sube-baja (4) | nativas | 2 · 1 · 1 · 2 · 2 · 1 · 1 | participación |
| `MeanReversion_user` (ZScore estirado, 2) | propias | **0** · 3 · 1 · 1 · 1 · 1 · 1 | el dueño lo llamó reversión |
| WAE propios (8) | propias | 3 · 1 · 2 · 3 · 2 · 1 · 1 (explosión) / 1 · 2 · 1 · 1 · 2 · 1 · 1 (por debajo) | Waddah Attar |

### Patrones

| tipo | bloques | R · Rv · T · M · V · P · S | por qué |
|---|---|---|---|
| velas de continuación: Marubozu, ventanas, tres soldados, mat hold, tasuki, líneas separadas, lado a lado, tres líneas (16) | La City | 2 · 1 · 2 · 2 · 1 · 3 · 1 | el patrón sigue la dirección |
| velas de reversión: martillo, envolvente, harami, cruz, estrella, pinzas, tres dentro/fuera, kicker… (42 La City + 6 nativas) | La City y nativas | 1 · 2 · 1 · 1 · 1 · 3 · 1 | el patrón invierte |
| indecisión: doji, peonza (2+1) | La City y nativas | 1 · 1 · 1 · 1 · 1 · 3 · 1 | no dice dirección |
| fractales (2), DTW (1) | nativas | 1 · 2 · 1 · 1 · 1 · 3 · 1 / 1·1·1·1·1·3·1 | forma |
| IBS (4) | propias | 1 · 3 · 1 · 1 · 1 · 2 · 1 | posición en la barra: reversión clásica |
| ruptura con mecha corta / larga, vela fuerte | propias | 2 · 1 · 1 · 1–2 · 1 · 2–3 · 1 | forma de la vela de ruptura |
| `Volume Profile`: cambio de valor (2) / POC (2) | nativas | 2·1·2·1·1·1·2 / 1·1·2·1·1·1·2 | migración del valor |
| Pivots, TPO, Volume Profile (nivel); Fibo | `Indicators` | 2·2·1·1·1·1·2; 1·2·1·1·1·1·2; 1·2·1·1·1·1·1 | niveles de referencia |

### `BookTriggers_user` (26, uno por uno por ser del dueño)

Aroon/Didi: 1·1·3·2. `BBBreakout`: 3·**0**·1·2. `NormMACD`, `QQECross`, `RMICross`, `SMICross`,
`TRSICross`: 1·2·1·3. `QQEMod`: 1·1·2·3. `PMaxFlip`: 2·1·3·1·2. `RSIVWMA` y `StochOTT`: 1·2·2·2.
`StochWeights`: 1·3·1·2 (cruce desde debajo de la mitad).

### Todo en ceros

`CBlock_BarsLargerRSI` y `CBlock_BarsLargerRSI_2` (`BarsLargerRSI(Int2, Double3, Int4)`): sin `help`,
con un `form` que no explica qué comparan. Quedan fuera de toda paleta hasta saberlo.

## 12 · Preguntas para el dueño

1. **Estados de banda según la dirección.** `BBBarClosesBelowDown` («cierra por debajo de la banda
   inferior») es reversión si la plantilla es larga y ruptura si es corta. Hoy llevan `2` en ruptura
   y en reversión (8 bloques de BB/KC en estado «fuera de la banda»). ¿Prefieres decidirlo por
   plantilla, o que la etiqueta lleve un lado?
2. **Qué calcula `BarsLargerRSI`** (2 bloques en ceros).
3. **Paletas de las cuatro familias nuevas.** No existe ninguna paleta base de momentum, volatilidad,
   patrón ni sesión; las cuatro actuales son de las tres primeras. ¿Se crean, o las hace el
   `buildingBlocksExpert` por plantilla?
4. **`SRPercentRank`** (4 bloques + 2 valores): el `help` es ambiguo («below Level» en el de
   «above»). Etiquetado como niveles de soporte/resistencia (2·2·1·1·1·1·1).
5. **Ruptura frente a estado en las bandas de SQX.** El nombre `BarClosesAboveUp` no dice si es
   cruce o estado; se tomó como estado. Si SQX lo evalúa como cruce, subir `breakout` a 3.
