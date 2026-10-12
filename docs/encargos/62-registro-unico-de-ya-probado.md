# 62 · Registro único de «ya probado» — una sola respuesta a «¿se probó esta celda?»

**Tu oficio:** contabilidad de búsquedas y corrección por pruebas múltiples; Python sobre tres registros
que ya existen, sin SQX. **Opus**: cambiar cómo se cuenta N es estadística (regla 17).
**Tu encargo:** (1) **un comando de sólo lectura** que, para una celda, diga qué se construyó, qué tramos
se gastaron y cuántas veces — contando los `Test_`; y (2) **dos tablas de «antes y después»** para que el
dueño decida dos cambios que tú **no** aplicas sin su sí: el número de ensayos N por serie de precios en
vez de por plantilla, y Benjamini-Hochberg sobre una familia fijada por propuesta.

> **Cambiar N cambia veredictos estadísticos.** Un N mayor baja el Sharpe deflactado y sube el listón de
> todo lo que se juzga con él; una familia de BH distinta cambia qué celdas del perfil «pasan». No es un
> arreglo de código: es una decisión de estadística, del dueño. La parte 1 no mueve ningún veredicto; las
> partes 2 y 3 sólo los **calculan de las dos maneras** hasta que él elija.

Lee `CLAUDE.md` (reglas 6, 7, 8, 9, 11, 16, 20) · `CODESTYLE.md` · `ledger/README.md` ·
`pipeline/campaign/README.md` · `engines/README.md` (pruebas múltiples) · `studies/research/marketProfile/README.md`.

## 0 · De dónde sale

Revisión del dueño del 2026-10-11 (`~/Desktop/revision-pasos-01-07-2026-10-11.md`). §3: «Un solo registro
de "ya probado". Que cuente los `Test_` y los tramos gastados. Para la campaña, la celda del ejemplo está
sin probar, y tiene `oos1` cribado cuatro veces y 24 filas sobre `oos2`» y «El número de ensayos por serie
de precios, no por plantilla. Hoy otra plantilla sobre el mismo USDJPY M30 empieza la cuenta de cero».
§1: «Aplicar BH sobre una familia fijada por propuesta, no sobre todo lo medido alguna vez. Esa familia
crece cada mañana y mueve los veredictos». Cifras: `docs/AgentPDFs/criterios-implementados-2026-10-12.md:349-363,522,528`
(celda `doubleROCLong` USDJPY M30: 11 proyectos en el registro, todos `Test_`; `oos1` cribado cuatro veces
con cuatro versiones de `criteria.yaml`; 24 filas sobre `oos2`, todas del 2026-10-06) y
`criterios-implementados-2026-10-12.md:36,358,584` (2 celdas de 1.064 pasan el perfil).

Lo que se comprobó en el código el 2026-10-11 — «ya probado» vive en **tres sitios** que no se hablan:

| dónde | qué sabe | qué no sabe |
|---|---|---|
| `AlgoData/projects/registry.csv` (lo escribe `sqx/projects/builder.py`) | todo proyecto creado, `Test_` incluidos: símbolo, marco, plantilla, fecha | resultados; tramos gastados |
| `AlgoData/campaign/ledger.jsonl`, clave `plantilla\|símbolo\|marco\|dirección` | lo que la campaña planeó y lanzó | **ignora los `Test_`**: `pipeline/campaign/plan.py:36-39` sólo mira `Trade_` y `Research_` |
| `AlgoData/ledger/<símbolo>_<marco>_<familia>.jsonl` (el libro de búsqueda) | filas por tramo y criterio, con `n_in`, `n_out`, `segment` (`ledger/study.py:15-17`) | N es **por estudio** — activo, marco y familia de plantilla (`ledger/study.py:21`, `ledger/trials.py:13`): otra familia sobre la misma serie empieza de cero |

Y en el perfil de mercado: BH se aplica sobre **todas las filas que se le pasan**
(`studies/research/marketProfile/many.py:53-71`); la `q` por familia se guarda (`q_family`,
`passes_family`) pero **no es el veredicto**.

## 1 · El comando: «¿se probó esta celda?» (sólo lectura)

`python3 -m ledger.cell <SÍMBOLO> <MARCO> [--template T] [--direction long|short]` (si `ledger/README.md`
pide otro nombre, el suyo). Lee los tres sitios por `core.paths` — no escribe en ninguno, no crea un cuarto
registro — y devuelve una respuesta, texto y `--json`:

- **Construido:** proyectos del registro en esa celda, `Test_`, `Trade_` y `Research_` por separado, con
  fecha y si están retirados.
- **Campaña:** su fila en `campaign/ledger.jsonl` y su estado, si la hay.
- **Tramos gastados:** por tramo (`build`, `oos1`, `oos2`), cuántas filas del libro lo leen, en cuántas
  fechas distintas y con cuántos `criterion` distintos — «`oos1` cribado 4 veces», «24 filas sobre `oos2`».
- **Por serie de precios:** lo mismo sumado sobre **todas** las plantillas y familias de ese símbolo y
  marco, al lado.
- **El veredicto en una línea:** `sin probar` · `construida, sin juzgar` · `oos1 gastado N veces` ·
  `oos2 abierto`.

Comprueba cómo deciden «serie de precios» los nombres del libro (hay `DAX40_H1.jsonl` y
`DAX40_H1_simple_long.jsonl` en la misma carpeta) y qué hay en `AlgoData/ledger/archive/`: dilo en el README.
Un test (`tests/test_ledger_cell.py`) sobre tres registros de juguete: una celda con sólo `Test_` sale
«construida», no «sin probar»; una con filas de `oos2` sale «oos2 abierto». La celda del ejemplo debe dar
11 proyectos, `oos1` × 4 y 24 filas de `oos2` — si no da eso, explica la diferencia, no ajustes la cuenta.
Capítulo del manual por `/manual-chapter` (regla 8).

**Quién lo consulta** — la campaña, el director de investigación, `/template-run` — es la pregunta 1: hasta
su respuesta, el comando existe y nadie cambia de comportamiento.

## 2 · N por serie de precios — la tabla, no el cambio

Sin tocar `ledger/trials.py` ni `ledger/study.py`: una función aparte que calcule, para cada estudio del
libro, el N de hoy (por estudio) y el N si se contara por serie (símbolo × marco, todas las familias y
direcciones — y di qué pasa con las direcciones, pregunta 2). Entrega, en
`AlgoData/audit/ledger/n-por-serie-<fecha>.md`:

| serie | estudios | N hoy (por estudio) | N por serie | listón de Sharpe hoy → por serie | veredictos que cambiarían |
|---|---|---|---|---|---|

Los «veredictos que cambiarían»: busca con `graphify affected "accumulated"` (o `grep -rn 'trials.accumulated\|
ledger.trials' --include=*.py .`) quién lee N — el Sharpe deflactado, el PSR, los pasos que lo usan — y
recalcula con los dos N **sobre lo ya guardado**, sin volver a correr nada en SQX. Nombra las estrategias
del almacén que pasarían de Pasa a no pasar.

## 3 · BH por familia fijada en la propuesta — la tabla, no el cambio

Con las filas que el perfil ya tiene medidas (no midas nada nuevo: cada medida es una mirada más), tres
columnas por celda: `passes` (BH sobre todo, lo de hoy), `passes_family` (ya calculado,
`many.py:67-71`) y «BH sobre la familia de la propuesta» según la lectura que el dueño elija (pregunta 3).
Entrega cuántas celdas pasan con cada una (hoy: 2 de 1.064) y cuáles cambian. Y una comprobación de
estabilidad: recalcula el `passes` de hoy quitando las filas del último mes — ¿cambia alguna celda de
veredicto sólo porque la familia creció?

## 4 · Aplicar (sólo tras el sí del dueño a cada pregunta)

Lo que elija: la campaña y el director leen el comando de la parte 1; `ledger/trials.py` cuenta como diga;
`many.py` da por veredicto la corrección elegida. Cada cambio con su test, y **un cambio de N o de familia
deja una línea en `ledger/criteria-history.jsonl`** (o donde `ledger/README.md` diga que se anota un cambio
de criterio) con fecha, antes, después y la frase del dueño — los veredictos anteriores no se reescriben.

## Lo que no tocas

SQX, en ningún install · `ledger/thresholds.yaml` (mover un umbral es del dueño) · las filas ya escritas de
los tres registros (ni se corrigen ni se rellenan hacia atrás) · `oos2`, ni una medida nueva sobre `oos1`
· `ledger/trials.py`, `ledger/study.py`, `pipeline/campaign/plan.py` y `studies/research/marketProfile/many.py`
**antes** del sí de la parte 4 · `studies/research/memory/ideas.py` (el lector de «Hipótesis medidas» es
otro arreglo) · el estudio del build (encargo 60), que anotará su selección en este mismo libro.

## Decisiones del dueño — pregúntalas (regla 11)

1. **¿Un `Test_` gasta la celda?** (a) sí: la campaña y el director la dan por probada; (b) gasta los
   tramos pero no la celda — se puede relanzar, avisando de que `oos1` ya se miró N veces; (c) sólo informa.
   ¿Y un `Test_` que no pasó del build?
2. **¿Qué es «una serie de precios» para N?** (a) símbolo × marco; (b) símbolo × marco × dirección; (c) el
   símbolo entero, todos los marcos (el H1 y el M30 del mismo activo no son independientes). Con la tabla
   de la parte 2 delante: cada lectura sube N — y el listón — más que la anterior.
3. **¿Cuál es «la familia fijada por propuesta» para BH?** (a) las celdas de la familia de ideas de la
   propuesta (lo que ya calcula `q_family`); (b) las celdas que la propuesta declara antes de medir,
   selladas con ella; (c) todo lo medido hasta la fecha de la propuesta, congelado ese día.
4. **¿Y lo ya juzgado?** Si N cambia: (a) sólo de aquí en adelante; (b) se recalculan los veredictos del
   almacén y se marcan los que caen; (c) se recalculan y se retiran.
5. **Tramos gastados: ¿hay un tope?** Hoy nada impide cribar `oos1` una quinta vez. (a) sólo avisar;
   (b) el comando de workflow se niega a partir de N veces — ¿qué N?

## Objetivo — un comando

```
python3 tools/depmap.py && python3 tools/checks.py && python3 -m pytest tests/test_ledger_cell.py -q \
  && python3 -m ledger.cell USDJPY M30 --template doubleROCLong --json
```

Sale 0 con la parte 1 hecha. Las partes 2 y 3 se verifican a ojo: las dos tablas existen, la columna «hoy»
de cada una reproduce los veredictos vigentes (diferencia 0), y `git diff --stat` no toca
`ledger/trials.py`, `ledger/study.py`, `plan.py` ni `many.py` antes del sí.

## Cómo cierras

Qué hizo · qué verificó, con la salida del Objetivo y las dos tablas pegadas · qué dejó sin hacer y por qué
(la parte 4 queda «bloqueada por la pregunta N» mientras no haya respuesta) · qué descubrió para
`knowhow/` (los tres registros y qué sabe cada uno, en `knowhow/locations/` o `knowhow/pipeline/`, editando
la ficha que exista) · la lista de ficheros cambiados y, como última línea, **¿Quieres hacer el commit?**

```
/loop Lee docs/encargos/62-registro-unico-de-ya-probado.md y ejecútalo entero. Tras cada iteración corre el Objetivo; si sale 0, para el bucle; si no, arregla lo que falló y vuelve a correrlo.
```
