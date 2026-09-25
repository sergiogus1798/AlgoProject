# 39. Crossmarket por lotes — el paso 10 sin abrir el panel

## Qué pregunta responde

Si una población entera de estrategias sigue ganando en los mercados que **nunca vio**, y escribe la
respuesta como una lista de supervivientes que el paso siguiente de SQX puede leer. Es la mitad
automática del paso 10 del workflow: el panel de `strategies/crossmarket/explorer/` sigue siendo
donde se mira **una** estrategia con lupa; esto es para cribar las ochenta.

La pregunta concreta que contesta es **amplitud**: en cuántos de los mercados declarados el
intervalo de confianza de la esperanza por operación queda por encima de cero. Se eligió ésa y no un
p-valor porque la amplitud no necesita creerse ningún modelo: que la esperanza de una estrategia
supere cero en un mercado al que nunca se ajustó es aritmética. Los p de los modelos de colocación
salen en el CSV al lado, y **no deciden nada**.

## Cuándo lo usas, y cuándo no

- **Sí**: después de correr la tarea `Retest Markets - Family` de tu proyecto y exportar sus
  operaciones, cuando quieres que el paso 13 (MC Retest) sólo vea a los que transfieren.
- **No**: para entender *por qué* una estrategia falló en un mercado. Eso es el panel, que dibuja la
  curva, la matriz de correlación y la cartera combinada. Un CSV no te dice eso.
- **No** como única lectura de un edge: el veredicto aquí es un suelo, no un dictamen.

⚠️ **Esto guarda un resultado en disco.** El informe por lotes se había quitado en 2026-09-15
precisamente por eso —un número guardado se puede leer como respuesta a una pregunta para la que no
se calculó— y volvió el 2026-09-24 a petición del dueño, para que la cadena corra sin humano. El
propio comando te lo recuerda al terminar.

## Antes de empezar

Tres cosas, y las tres fallan de forma clara si faltan:

1. **La tarea corrida y exportada.** `python3 -m sqx.export.export_retest --project <P>
   --databank "Retest Markets - Family" --role custodian` deja el `trades.parquet` que esto lee.
2. **Las barras M1 de TODOS los mercados de la familia** en la librería, porque cada celda se
   puntúa contra su propio mercado: `python3 -m sqx.export.sync_bars --check` te dice qué falta y
   sin el flag las trae. Son ~8,6 M de barras y ~140 MB por par.
3. **El activo declarado** en `assets/_markets.yaml`, que es de donde sale la lista de mercados.

No toca SQX, así que puedes lanzarlo con la GUI del maestro abierta.

## Cómo se ejecuta

```bash
python3 -u -m strategies.crossmarket.report \
    --project TestUSDJPY_Workflow_v1 \
    --databank Retest_Markets_-_Family \
    --asset USDJPY \
    --export 2026-09-24 \
    --set nulls.draws=2000
```

| flag | obligatorio | qué hace |
|---|---|---|
| `--project` | sí | el proyecto tal y como aparece en SQX |
| `--databank` | sí | la carpeta de la exportación, **con guiones bajos** donde el databank lleva espacios |
| `--asset` | sí | el activo base, p. ej. `USDJPY`. Decide la lista de mercados |
| `--export` | sí | la fecha de la exportación, `AAAA-MM-DD` |
| `--floor` | no | fracción de mercados que tienen que superar cero para conservarla. Por defecto `0.5` |
| `--set` | no | cualquier knob de `config.yaml`, p. ej. `nulls.draws=2000` |

⚠️ **Pon el `-u` de Python.** Y no lo canalices a `tail`: una tubería retiene la salida hasta el
final y un lote de una hora se vuelve indistinguible de un cuelgue.

**Lo que tarda.** Medido el 2026-09-24 en tres tamaños, un solo núcleo, y el coste NO es por
estrategia: es **por operación**, porque unas estrategias llevan ocho veces más que otras.

> **coste ≈ (3,36 + 0,00168 × sorteos) ms por operación**

| operaciones | sorteos | tiempo |
|---|---|---|
| 44.660 | 500 | 171 s |
| 133.240 | 500 | 507 s |
| 158.415 | 500 | 630 s |
| 12,0 M (500 estrategias × 10 mercados) | 500 | **14 h** |
| 12,0 M | 10.000 (el de `config.yaml`) | **~67 h** |

Antes de lanzarlo, **cuenta las operaciones** y multiplica; no cuentes estrategias:

```bash
python3 -c "import pandas as pd; f=pd.read_parquet('.../trades.parquet'); print(len(f))"
```

Baja los sorteos para probar la cadena; súbelos para publicar un p. El suelo de amplitud apenas se
mueve con ellos, porque no depende de un nulo. Y el desglose de por qué cuesta lo que cuesta está en
`docs/manual/12-rendimiento.md`: el resumen es que corre en **1 de 96 núcleos** y que ahí está el
único arreglo que importa.

## Qué produce

Un fichero, y **sobrescribe** el de la misma exportación:

```
~/Desktop/AlgoData/reports/<PROYECTO>/<DATABANK>/<FECHA>/crossmarket/verdict.csv
```

Catorce columnas. Las tres primeras son el contrato con `/curate` (`strategy`, `verdict`, `reason`);
las once siguientes son para que no tengas que creerte el veredicto a ciegas.

## Cómo se lee el resultado

Salida real de la corrida del 2026-09-24 sobre `TestUSDJPY_Workflow_v1`:

```
8 estrategias x 9 mercados a 2,000 sorteos — minutos por estrategia.
  [1/8] Strategy 11.1.50    DESCARTAR solo 0 de 9 mercados con la esperanza por encima de cero (0% < 50%)
  ...
  [8/8] Strategy 6.1.81     DESCARTAR solo 0 de 9 mercados con la esperanza por encima de cero (0% < 50%)

0 de 8 pasan el suelo de amplitud -> .../crossmarket/verdict.csv
```

Y la tabla, recortada a lo que se mira:

| strategy | verdict | cleared/markets | under_alpha | edge_r | worst_pf | pf_cv | family |
|---|---|---|---|---|---|---|---|
| Strategy 11.1.50 | DESCARTAR | 0 / 9 | 0 | −0,059 | 0,907 | 0,068 | entry+exit |
| Strategy 23.1.71 | DESCARTAR | 1 / 9 | 2 | 0,046 | 0,982 | 0,045 | entry+exit |
| Strategy 23.1.60 | DESCARTAR | 0 / 9 | 0 | 0,076 | 0,893 | 0,063 | entry+exit |

Cómo se lee cada columna:

- **`cleared` / `markets`** — la que decide. Mercados cuyo intervalo de la esperanza queda por
  encima de cero, sobre los que tienen operaciones. `0 de 9` es una respuesta, no un fallo.
- **`under_alpha`** — cuántos mercados dieron p ≤ 0,05 en el modelo de colocación. **Informativo.**
  Un 2 con `cleared` 1 dice que el p viene de un modelo y la esperanza no lo acompaña.
- **`edge_r`** — el efecto mediano en unidades del propio rango del mercado. Signo primero: en
  negativo la estrategia pierde en la mediana de los mercados ajenos.
- **`worst_pf`** — el profit factor del peor mercado. **Por debajo de 1 es que ahí pierde dinero.**
  Un buen candidato tiene el peor mercado cerca de 1, no una media alta con un desastre dentro.
- **`pf_cv`** — dispersión del profit factor entre mercados. Alto = funciona en uno y en los demás no.
- **`family`** — `entry` si todas las salidas son el tope de barras, `entry+exit` si no. Con
  `entry+exit` **esto no es una prueba del *timing* de entrada**, es una prueba conjunta, y así hay
  que contarlo.
- **`missing`** — mercados en los que la estrategia no disparó ni una vez. Es un resultado sobre la
  estrategia, no un dato que falte. Si no disparó en **ninguno**, su fila lo dice y no se calcula
  nada más: no hay nada que juzgar. (Hasta el 2026-09-24 ese caso tumbaba el lote entero con un
  `KeyError: 'bar_cap'`, y salió con la novena estrategia real que se probó.)
- **`warnings`** — avisos que la estrategia acumuló entre mercados. 25-27 sobre nueve mercados es
  normal cuando los costes son provisionales: casi todos son ése.

### Aplicarlo

```bash
python3 -m sqx.curate.apply_verdict --project <P> --databank "Retest Markets - Family" \
    --verdict .../crossmarket/verdict.csv --role custodian          # mira primero
python3 -m sqx.curate.apply_verdict ... --apply                    # con el custodio parado
```

## Un ejemplo completo

```bash
# 1. exporta las operaciones de la tarea, con el custodio parado
bin/sqx-worker.sh --role custodian stop
python3 -m sqx.export.export_retest --project TestUSDJPY_Workflow_v1 \
    --databank "Retest Markets - Family" --role custodian

# 2. asegúrate de tener las barras de los nueve pares
python3 -m sqx.export.sync_bars --check

# 3. juzga la población entera
python3 -u -m strategies.crossmarket.report --project TestUSDJPY_Workflow_v1 \
    --databank Retest_Markets_-_Family --asset USDJPY --export 2026-09-24 \
    --set nulls.draws=2000

# 4. aplica el veredicto para que el MC Retest sólo vea a los supervivientes
python3 -m sqx.curate.apply_verdict --project TestUSDJPY_Workflow_v1 \
    --databank "Retest Markets - Family" --role custodian \
    --verdict ~/Desktop/AlgoData/reports/TestUSDJPY_Workflow_v1/Retest_Markets_-_Family/2026-09-24/crossmarket/verdict.csv
```

## Qué NO te dice

- **No dice que el edge sea real.** Dice que sobrevive a cambiar de mercado, que es una condición
  necesaria y nada más. Un mono largo en nueve pares correlacionados también puede pasarlo.
- **No corrige por multiplicidad entre estrategias.** Cribar ochenta estrategias con este suelo es
  ochenta pruebas, y el CSV no lo paga. Eso es el ledger global (`docs/encargos/8-ledger-global.md`).
- **No es una prueba del timing de entrada** cuando `family` dice `entry+exit`.
- **No sustituye al panel.** Sin la curva y la matriz de correlación no se ve si los nueve mercados
  son nueve observaciones o una repetida nueve veces.
- **Con costes provisionales, no juzga nada de nivel.** Mira la columna `warnings`.

## Si algo falla

- **`KeyError: 'AUDJPY_DukasM1_the5ers'`** — falta ese feed en la librería de barras. Es el fallo
  más común. `python3 -m sqx.export.sync_bars` lo trae; son minutos por feed.
- **`FileNotFoundError` en `trades.parquet`** — la exportación no existe con esa fecha o ese nombre
  de databank. Ojo a los guiones bajos: `Retest Markets - Family` se exporta a
  `Retest_Markets_-_Family`.
- **Salida vacía durante media hora** — no está colgado: o le falta el `-u`, o lo canalizaste a
  `tail`. Mira `ps -o etime,time` del proceso; si el tiempo de CPU sube, está trabajando.
