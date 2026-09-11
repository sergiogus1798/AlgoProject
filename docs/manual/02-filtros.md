# 2. Barrido de filtros — cuánto te da de verdad filtrar, y a cambio de qué

## Qué pregunta responde

El análisis IS/OOS (página 1) te dice **qué métricas del histórico llevan información** sobre el
futuro. No te dice qué hacer con ellas. Esta página sí:

> *"Si me quedo solo con el 10% de mejor CAGR/Max DD del histórico, ¿cuánto mejora el resultado
> fuera de muestra, cuántas estrategias pierdo, y esa mejora es real o es que he probado muchas
> combinaciones hasta que una salió bien?"*

El comando prueba **210 filtros candidatos** de una tacada — cada métrica IS cortada por arriba y
por abajo al 5, 10, 20, 30 y 50% — y de cada uno reporta la mejora, el intervalo de confianza de esa
mejora y cuántas estrategias sobreviven.

## Cuándo lo usas, y cuándo no

**Lo usas** para decidir dos cosas concretas: qué condiciones de aceptación poner en la generación
de SQX, y con qué criterio cribar un databank antes de pasar al testeo serio.

**No lo usas** con estrategias que ya fueron seleccionadas por su resultado OOS — igual que la
página 1, ahí mides tu propia selección. Tampoco lo uses para elegir *una* estrategia: habla de
poblaciones.

Y no lo uses como coartada: que un filtro salga con ✓ no significa que dé dinero. Significa que la
mejora que muestra no se explica por el azar del muestreo.

## Antes de empezar

Lo mismo que la página 1, y nada más:

1. El CSV de métricas del databank ya exportado
   (`python3 -m sqx.export.export_metrics --project XAUUSD --databank OOS`).
2. Nada de SQX. Este comando no lo toca: puedes correrlo con la GUI abierta.

## Cómo se ejecuta

```bash
cd ~/Desktop/AlgoProject
python3 -m tasks.reports.filters --project XAUUSD --databank OOS
```

| flag | obligatorio | qué hace |
|---|---|---|
| `--project` | sí | nombre del proyecto tal y como aparece en SQX |
| `--databank` | sí | nombre del databank, p. ej. `OOS` |
| `--target` | no | columna OOS a mejorar. Repetible. Por defecto `Sharpe Ratio (OOS)` y `Ret/DD Ratio (OOS)` |
| `--top` | no | cuántos filtros lista por resultado. Por defecto 15 |

**Tarda unos 40 segundos** con 10.000 estrategias y dos objetivos: casi todo es el bootstrap, que
son 2.000 remuestreos por cada filtro candidato.

## Qué produce

```
~/Desktop/AlgoData/reports/XAUUSD/OOS/2026-09-04/filters/
    improvement.md   la tabla de filtros, en texto
    manifest.json    de qué CSV salió y con qué versión del código
```

Va en su propia subcarpeta `filters/` dentro del reporte del día, para no pisar el `manifest.json`
del análisis IS/OOS. Se sobrescribe si lo repites el mismo día; los días anteriores no se tocan.

## Cómo se lee el resultado

```
## Sharpe Ratio (OOS)

Unfiltered: 10,000 strategies · median -0.280 · 25.6% above 0.
108 of the 210 filters judged both improve the median and survive the correction.

| filter                     |  kept | median | Δ median |    95% CI on Δ  | hit % | Δ hit pp |        p | BH |
| CAGR/Max DD % (IS) top 5%  |   511 | -0.020 |   +0.260 | [+0.230,+0.300] |  47.7 |    +22.2 | 5.00e-04 | ✓  |
| Sharpe Ratio (IS) top 5%   |   528 | -0.020 |   +0.260 | [+0.230,+0.300] |  47.9 |    +22.4 | 5.00e-04 | ✓  |
| CAGR/Max DD % (IS) top 10% | 1,018 | -0.030 |   +0.250 | [+0.230,+0.280] |  46.3 |    +20.7 | 5.00e-04 | ✓  |
| PSR (IS) top 10%           | 1,045 | -0.030 |   +0.250 | [+0.220,+0.270] |  45.7 |    +20.2 | 5.00e-04 | ✓  |
| Profit factor (IS) top 20% | 2,019 | -0.050 |   +0.230 | [+0.200,+0.240] |  43.7 |    +18.1 | 5.00e-04 | ✓  |
```

Columna por columna:

| columna | qué es |
|---|---|
| **filter** | la condición. `top 10%` = quedarse con el 10% de valor más alto de esa métrica IS; `bottom` = el más bajo |
| **kept** | cuántas estrategias sobreviven. **Este es el precio del filtro** |
| **median** | la mediana del resultado OOS entre las supervivientes |
| **Δ median** | cuánto sube esa mediana frente a no filtrar. Es la ganancia |
| **95% CI on Δ** | el intervalo de esa ganancia. **Si incluye el 0, la mejora no se distingue del ruido** — es la columna que decide |
| **hit %** | qué porcentaje de las supervivientes acaba por encima del punto de equilibrio (0 para Sharpe y Ret/DD; 1 para profit factor) |
| **Δ hit pp** | lo mismo en puntos porcentuales frente a no filtrar. Suele ser la cifra más intuitiva |
| **p** | p-valor bootstrap. **Tiene suelo en 1/2000 = 5.00e-04**: cuando está pegado ahí, mira el intervalo, no el p |
| **BH** | ✓ = aguanta la corrección por haber probado 210 filtros a la vez |

**Lo que hay que mirar primero es `kept` y `Δ hit pp`**, en ese orden. Un filtro que sube 20 puntos
la tasa de acierto tirando el 90% de las estrategias es una decisión distinta a uno que sube 18
tirando el 80%, y la elección depende de cuántas estrategias necesites al final del embudo.

Un filtro que deja **menos de 200 supervivientes ni se evalúa**. Con 12 estrategias vivas cualquier
mejora es un espejismo, y la regla está fijada de antemano para que no se decida caso por caso.

## Un ejemplo completo

Pregunta: **¿qué condición de aceptación pongo en la generación de XAUUSD?**

```bash
cd ~/Desktop/AlgoProject
python3 -m tasks.reports.filters --project XAUUSD --databank OOS
```

```
210 candidate filters over 10000 strategies, 2 outcomes
  /home/sergioguslw/Desktop/AlgoData/reports/XAUUSD/OOS/2026-09-04/filters/improvement.md
```

En `improvement.md`, para `Ret/DD Ratio (OOS)`:

> Best surviving filter: **Sharpe Ratio (IS) top 5%** — keeps 528 strategies, median 0.015
> (+0.485), hit rate 50.4% (+23.7 pp).

Lectura en cristiano: sin filtrar, **el 26,7%** de las estrategias acaba con Ret/DD positivo fuera
de muestra. Quedándote con el 5% de mejor Sharpe del histórico, **el 50,4%** — casi el doble de tasa
de acierto, a cambio de descartar 19 de cada 20 estrategias generadas.

**Dónde deja de pagar apretar más.** Esa es la pregunta que contesta tener los cortes 5 y 10 juntos:

| corte | sobreviven | acierto OOS |
|---|---:|---:|
| sin filtro | 10.000 | 26,7% |
| top 10% | ~1.020 | 48,6% |
| top 5% | ~510 | 50,4% |

El primer corte compra **22 puntos**; apretar del 10% al 5% compra **menos de 2 más** y te deja la
mitad de estrategias. La curva se aplana: **el 10% es el punto razonable** salvo que necesites lo
mejor de lo mejor y te sobren candidatas.

Una segunda cosa que se ve sola en la tabla: `CAGR/Max DD %`, `CalmarRatio`, `R Expectancy`, `SQN`,
`Profit factor`, `Sharpe` y `Sortino` al 10% dan **prácticamente el mismo resultado**. No son siete
filtros: son siete formas de medir lo mismo. Aplicarlos a la vez no multiplica nada, solo estrecha
el embudo.

## Qué NO te dice

- **No dice que combinando filtros mejore más.** Solo se barren condiciones sueltas. Dos
  condiciones a la vez son otro espacio de búsqueda y necesitan otra corrección.
- **No dice que el filtro valga para otro activo.** Todo esto es XAUUSD y este periodo. Hay que
  repetirlo por activo antes de generalizar nada.
- **No dice nada sobre costes reales.** Son los números de SQX con su configuración de comisiones.
- **No convierte una mejora estadística en dinero.** Sube la proporción de estrategias decentes en
  lo que sale del generador; lo que hagas después con ellas es otro problema.
- **El intervalo no cubre el riesgo de que el periodo OOS sea atípico.** Cubre el muestreo dentro de
  estos datos, no que 2023 se parezca a 2026.

## Si algo falla

| lo que ves | qué pasa |
|---|---|
| `FileNotFoundError: .../metrics.csv` | no has exportado ese databank todavía. Corre `export_metrics` primero |
| `KeyError: 'Sharpe Ratio (OOS)'` | la vista de SQX no trae esa columna en OOS. Pásale `--target` con una que sí exista |
| tarda varios minutos | normal si el databank es mucho mayor de 10.000 estrategias: el bootstrap crece con el número de supervivientes |
