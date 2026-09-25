# El workflow entero sobre USDJPY H1 — qué funciona y qué no (2026-09-24)

Corrida de validación pedida por el dueño: **no juzga la estrategia, juzga la maquinaria**. Población
pequeña a propósito y cortes artificiales por *net profit* en cada etapa, para que el embudo se
estreche y cada paso reciba una población distinta.

- **Activo** USDJPY (`USDJPY_DukasM1_the5ers`), **H1**, proyecto `TestUSDJPY_Workflow_v1` en el
  custodio, más `TestUSDJPY_crossTF_v1` para el paso 11.
- **Plantilla** `emaCloseAbove`: `AND(la vela cierra por encima de una EMA(50)[1], condición
  aleatoria libre)`, largo, entrada a mercado. **Decisión del dueño: estado, no cruce.**
- **Costes PROVISIONALES** en todo: spread 0.1, comisión 0.0 (¡cero!), slippage 0.05, swap 0/−10.4.
  Ningún número de aquí sirve para juzgar un edge.

## El embudo

| paso | qué corrió | entran | salen | cómo se cortó |
|---|---|---|---|---|
| 6 | build sobre `build` 2008–2017 | — | **50** | 16 s; aceptación silenciada (302 condiciones) |
| 7 | retest OOS sobre `oos1` 2018–2022 | 50 | 50 | 5,4 s |
| 8 | `gate` (7 cribas + monos) | 50 | **17** | veredicto real: estáticas −27, degradación −6 |
| 9 | crossmarket, 9 pares de the5ers | 17 | 17 | 84 s |
| 10 | análisis crossmarket | — | — | **sin comando**: sólo existe el panel |
| 10.5 | variantes escaladas a H4 | 12 | 12 | 4 de 12 `clamped` |
| 11 | retest crossTF H1+H4 | 24 celdas | — | 21 s |
| 12 | lectura crossTF | — | — | 0 survives · 3 inherited · 2 fails · 1 control_failed · 6 unusable **⚠️ reconciliación rota** |
| 13 | MC Retest | 8 | 8 | 5 tareas de 8; MCR 8 tardó 1.022 s |
| 14 | análisis MC Retest | — | — | **bloqueado**: exige las ocho tareas |
| 15 | SPP IS + SPP OOS | 4 | 4 | 79 s y 42 s |
| 16 | `sppUltra` | 4 | **4** | las cuatro `proceed` |
| 16.5 | fábrica de variantes | 4 madres | **240 variantes** | `--sample 60` por madre, 5,6 MB |
| 17–20 | WFC, CSCV, WFM, lectura ciega | — | — | **sin correr: gastan `oos2`** |

Cortes artificiales aplicados con `/curate`, por `net profit`: 17→12 (crossmarket), 12→8 (crossTF),
8→4 (MC Retest). Los `verdict.csv`, los `before-*.csv` y los `rejected-*.csv` quedan en
`AlgoData/reports/TestUSDJPY_Workflow_v1/`.

## Lo que se rompió, y qué se hizo

| # | qué | estado |
|---|---|---|
| 1 | **el clon del donante seguía operando ORO** para cualquier activo ≠ XAUUSD | arreglado: `sqx/projects/resources.py` + guardia en `builder` |
| 2 | un bloque nativo fijo no admite `generate="random"` (`Identification not found`) | entendido y documentado; el periodo va congelado |
| 3 | `export_metrics` sólo leía el maestro · `sync_bars` moría en `markets.FILE` | arreglados, los dos |
| 4 | `retest.ingest` sólo leía el maestro | arreglado (`--role`) |
| 5 | nada copiaba las madres junto al perfil SPP, y la fábrica las busca ahí | arreglado en `export_spp` |
| 6 | **la reconciliación del crossTF falla en todas las celdas H4** (corr −0.20 a −0.34) | `OPEN.md` §34, abierto |
| 7 | el paso 14 exige ocho tareas MCR y sólo pueden existir cinco | `OPEN.md` §37, abierto |
| 8 | el paso 10 no tiene comando, sólo panel | `OPEN.md` §36, abierto |

## Hasta dónde llegó, y qué cuesta

**La cadena se corrió del paso 1 al 16.5, no hasta el 20.** Los pasos 17 (WFC), 18 (CSCV) y 19 (WFM)
no se han corrido: gastan `oos2` y eso es una puerta de un solo sentido. Las 240 variantes están
fabricadas y esperando el retest que las mide, que tampoco se ha corrido.

Los tiempos de cada paso, medidos y con el tamaño de población al que se midieron, están en
`docs/manual/12-rendimiento.md`, sección «Lo que cuesta el workflow de punta a punta». Los tres
titulares:

- **SQX: 2.202 s en total, y el MC Retest es el 89 %** — dentro de él, `OHLC` y `Stress` son el 88 %.
- **Python: todo son segundos menos `crossmarket.report`**, que son 13 minutos a 2.000 sorteos y más
  de 50 sin terminar a los 10.000 de su propio `config.yaml`. Un núcleo.
- **El ciclo parar/arrancar el custodio son ~39 s y se paga una vez por etapa**: aquí, ocho veces,
  unos 5 minutos sólo en abrir y cerrar.

Y el número de memoria que hay que vigilar: `retest.ingest` pica **3,2 GB con 36 corridas**.

## Lo que decide el dueño antes de seguir

1. **Gastar `oos2`.** Los pasos 17 y 19 lo queman y es de un solo sentido. Además `oos2` pide hasta
   2026-08-30 y los datos acaban el 2026-01-16.
2. **Los rangos de spread y slippage del MC Retest**, sin los cuales el paso 14 no existe.
3. **Los umbrales de `assets/_study.yaml`**, hoy inexistentes: esta corrida fue con la aceptación
   silenciada de punta a punta.
