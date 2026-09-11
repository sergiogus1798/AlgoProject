# 3. Comparar muestras — ¿se cumplen las conclusiones en otra generación?

## Qué pregunta responde

Las páginas 1 y 2 sacan conclusiones de **una** población: *"filtrando por el 10% de mejor Sharpe IS,
la tasa de acierto OOS sube del 27% al 48%"*. Eso es una **predicción**, y una predicción se
comprueba generando estrategias nuevas y viendo si se cumple.

Esta página compara varias generaciones del mismo activo — la aleatoria de referencia y las que
hiciste después con distintas condiciones o distintos periodos — y responde a dos cosas:

1. **¿Entregó el filtro lo que prometía?** El umbral que salió de la muestra aleatoria se aplica a la
   muestra nueva y se compara lo predicho con lo observado, con su intervalo.
2. **¿Siguen mandando las mismas métricas?** Si la muestra nueva ordena los predictores igual que la
   de referencia, la conclusión aguanta; si los reordena, no era estable.

## Cuándo lo usas, y cuándo no

**Lo usas** cuando tienes **generaciones independientes**: databanks con estrategias nuevas, creadas
en corridas distintas de SQX, o la misma población medida en otro periodo.

**No lo usas para comparar una población con un subconjunto suyo.** Si `OOS-sharpe` no son
estrategias nuevas sino las 10.000 de siempre filtradas, no hay nada que replicar: sabes de antemano
lo que va a salir, y el filtro del panel (página 1) ya te lo enseña. La comparación solo significa
algo entre muestras que no comparten estrategias.

⚠️ **Y no compares correlaciones entre muestras seleccionadas de forma distinta.** Si generaste
`OOS-sharpe` exigiendo Sharpe alto, dentro de esa muestra el Sharpe apenas varía, así que su
correlación con cualquier resultado se desploma **por construcción**. Eso no significa que la
conclusión fallara. El informe lo detecta y lo avisa, y por eso la comparación que manda es la del
**resultado**, no la de la correlación.

## Antes de empezar

Cada databank que quieras comparar necesita su exportación de métricas hecha, **con la misma vista**
(`Export Data View`), para que las columnas coincidan:

```bash
python3 -m sqx.export.export_metrics --project XAUUSD --databank OOS-sharpe
```

El comando usa solo las métricas comunes a todas las muestras y te dice cuántas son.

## Cómo se ejecuta

```bash
cd ~/Desktop/AlgoProject
python3 -m tasks.reports.compare --project XAUUSD --reference OOS \
    --databank OOS-sharpe --databank OOS-rExpectancy --databank OOS-hasta2026
```

| flag | obligatorio | qué hace |
|---|---|---|
| `--project` | sí | nombre del proyecto tal y como aparece en SQX |
| `--reference` | sí | el databank del que salieron las conclusiones. Normalmente la generación **aleatoria** |
| `--databank` | sí | databank a comprobar. **Repetible**: uno por cada muestra |
| `--target` | no | columna OOS a comparar. Repetible. Por defecto `Sharpe Ratio (OOS)` y `Ret/DD Ratio (OOS)` |

**Tarda unos 25 segundos** con tres muestras y dos objetivos. No toca SQX.

## Qué produce

```
~/Desktop/AlgoData/reports/XAUUSD/_comparison/2026-09-04/
    comparison.md    la comparación
    manifest.json    qué muestras, de qué fecha de exportación, con qué código
```

Va en `_comparison/` porque no pertenece a ningún databank: habla de varios a la vez. El guion bajo
lo mantiene separado de las carpetas que sí son databanks.

## Cómo se lee el resultado

### Primera tabla: dónde acabó cada muestra

```
| databank         | strategies | median | hit % | Δ hit pp |  95% CI on Δ   |
| OOS              |     10,000 | -0.280 |  25.6 |        — |              — |
| _selftest_half   |      5,000 | -0.280 |  25.7 |     +0.1 | [-1.4, +1.6]   |
| _selftest_sharpe |      1,043 | -0.030 |  45.8 |    +20.3 | [+17.0, +23.3] |
```

`Δ hit pp` es la diferencia en tasa de acierto contra la referencia, y **el intervalo es lo que
decide**: si incluye el 0, esa muestra no se distingue de la de referencia. Arriba, la primera no se
distingue (era media población al azar) y la segunda sí (era el 10% de mejor Sharpe).

### Segunda tabla: ¿entregó el filtro lo prometido?

```
| filter                    | predicted hit % | % of sample passing |   n | observed hit % |    Δ |  95% CI on Δ  |
| Sharpe Ratio (IS) top 5%  |            47.9 |                50.6 | 528 |           47.9 | +0.0 | [-6.1, +6.1]  |
| CAGR/Max DD % (IS) top 5% |            47.7 |                47.8 | 499 |           47.3 | -0.5 | [-6.9, +5.5]  |
```

| columna | qué es |
|---|---|
| **predicted hit %** | lo que ese filtro consiguió **en la muestra de referencia**. Es la promesa |
| **% of sample passing** | cuánto de la muestra nueva pasa ese mismo umbral. **Cerca de 100% significa que la muestra se generó para cumplirlo** |
| **observed hit %** | lo que consiguen de verdad, en la muestra nueva, las que pasan el umbral |
| **Δ y su intervalo** | observado menos prometido. Si el intervalo incluye el 0, **el filtro cumplió**: no se desvía de lo que prometía |

⚠️ **Seis filas de acuerdo no son seis confirmaciones.** Los filtros de esta lista se solapan casi
del todo (seleccionan prácticamente las mismas estrategias), así que se mueven juntos. Una muestra
con suerte sube las seis a la vez. Mira el intervalo, no cuántas filas apuntan al mismo lado.

### Tercera parte: ¿mandan las mismas métricas?

```
**_selftest_half** ranks the predictors like the reference at ρ +0.995.

**_selftest_sharpe** ranks the predictors like the reference at ρ +0.407.
Selected on 12 metric(s) — # of trades (IS), DoF Ratio (IS), Drawdown (IS), Max DD % (IS) —
whose own correlations are attenuated here by construction.
```

Un ρ cercano a +1 significa que las dos muestras están de acuerdo en qué métricas predicen. Cuando
baja, **mira primero la línea de debajo**: si la muestra fue seleccionada sobre esas métricas, la
caída es aritmética y no dice nada. Si no lo fue, entonces sí: la conclusión no era estable.

## Un ejemplo completo

Las salidas de arriba son de una **prueba del propio comando**, hecha el 2026-09-04 partiendo la
exportación de XAUUSD/OOS en dos muestras artificiales para comprobar que detecta lo que debe:

- `_selftest_half` — media población al azar. **Debe salir "no hay diferencia"**, y sale: +0.1 pp con
  intervalo [−1.4, +1.6].
- `_selftest_sharpe` — el 10% de mejor Sharpe IS. **Debe replicar la predicción**, y sale: predicho
  47.9%, observado 47.9%, Δ +0.0.

Con tus muestras de verdad el comando es el mismo, cambiando los nombres de los databanks. Las dos
muestras de prueba se borraron después: no están en el data root.

## Qué NO te dice

- **No dice por qué una muestra falló.** Dice que lo hizo. La causa —periodo distinto, plantilla
  distinta, otra configuración del generador— la sabes tú, y el informe no puede adivinarla.
- **No corrige por cuántas muestras compares.** Comparar diez muestras y quedarte con la que mejor
  salió es el mismo problema de siempre. Decide de antemano qué esperas de cada una.
- **No compara periodos distintos como si fueran el mismo experimento.** Una muestra "hasta 2026"
  difiere de la referencia en el periodo *y* en las estrategias; si sale distinta, no sabrás cuál de
  las dos cosas lo causó a menos que dejes una fija.
- **No mide dinero.** Tasa de acierto y mediana, con los números y las comisiones de SQX.

## Si algo falla

| lo que ves | qué pasa |
|---|---|
| `FileNotFoundError: .../metrics.csv` | ese databank no está exportado todavía |
| `0 in-sample metrics common to every sample` | las muestras se exportaron con vistas distintas. Re-exporta todas con `Export Data View` |
| una muestra con muy pocas estrategias | los intervalos se abrirán tanto que no dirán nada. Por debajo de ~200 no merece la pena compararla |
