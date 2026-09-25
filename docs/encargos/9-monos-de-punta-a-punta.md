# 9 · La población de monos por la cadena entera — encargo autocontenido

**Tu oficio:** Python. Los monos se simulan en Python de punta a punta y SQX no interviene.
**Tu encargo es el control negativo de todo el proyecto**: pasar por los criterios de los veinte
pasos una población sin ningún edge, y contar cuántos salen vivos.

Lee `CLAUDE.md` · `docs/AgentPDFs/WORKFLOW.md` · `nulls/README.md` · `gate/README.md`.

**Depende del encargo 8.** Este estudio es exactamente el que más filas escribe en el ledger, y sin
ledger no se puede contar lo que hizo.

---

## 0 · De dónde sale este encargo

El dueño lo pidió el 2026-09-23 y está escrito en `WORKFLOW.md`:

> *«Si de diez mil monos llegan 4 y de diez mil tuyas llegan 5, ya sabes lo que vale ese 5.»*

Y hay que hacerlo **antes** del primer pase completo de verdad. Después ya se sabe qué sobrevivió, y
el número de monos se convierte en una cifra que se compara con un resultado conocido.

## 1 · Por qué esto y no permutaciones de barras

El plan original era el test de Masters: permutar la serie y reconstruir. Se investigó y **no es
practicable hoy**, y el motivo no es de esfuerzo:

- 🔬 La API de SQX **no tiene verbo de import** — ni `sqcli` ni MCP. `-data` sólo hace
  `action=export` (`knowhow/sqx-drive/project-verb.md`).
- Meter una serie sintética como símbolo propio exige **la GUI del maestro**, que es del dueño.
- El registro de instrumentos vive en `user/data/data.db` y `user/data/History` está **symlinkado
  al del maestro** desde los dos workers: fabricar símbolos toca el almacén compartido.
- No hay motor externo: `strategies/translate/` está **vacío**, así que no existe forma de reevaluar
  una estrategia fuera de SQX.

Lo que sí tenemos ya construido responde **la misma pregunta del Tier B de Masters** — la tasa de
falsos positivos de la cadena entera — sin generar ni una serie: `gate/monkey.py` y el módulo
`nulls/`, con su reconciliación de fills medida (🔬 `open-open` a 0.999985).

## 2 · Lo que construyes

### 2.1 · La población nula — **se simula en Python. Decisión del dueño, 2026-09-24**

Diez mil poblaciones de operaciones de **entrada aleatoria** sobre las mismas barras, la misma
ventana y los mismos costes que la población real, generadas por `nulls/model.py`, que ya hace
exactamente esto y está reconciliado contra los precios reales (🔬 `open-open` a 0.999985).

**Nada de hacer que SQX construya monos.** Se evaluó y el dueño lo descartó: un build con paleta
neutra cuesta horas de licencia, mide el generador además del filtro, y mete en el maestro
estrategias que nadie quiere. En Python son ~35 minutos para 10.000 y no toca SQX.

⚠️ **Lo que el mono tiene fijo, se le regala.** Es la idea que gobierna `nulls/`: emparéjale la
huella de trading —frecuencia, ocupación, duración de las operaciones— y lo que mides son los
filtros; emparéjale también las reglas y no mides nada. Esa huella se toma de la población real,
no se inventa.

### 2.1 bis · La consecuencia que hay que escribir en el informe

Como el mono nace en Python, **no atraviesa las tareas de SQX de la cadena: atraviesa sus criterios**.
Los pasos de Python (8, 10, 12, 14, 16, 17, 18) se le aplican tal cual, con los mismos umbrales. Los
pasos que en las de verdad son una tarea de SQX se le aplican como **el criterio equivalente sobre
sus operaciones**, y cada uno de esos hay que declararlo uno a uno: qué condición de la tarea se
está reproduciendo y qué parte no se puede reproducir.

Eso acota lo que el estudio mide, y hay que decirlo sin adornos: **mide la mortalidad de nuestros
filtros, no la del generador de SQX**. Es justo el número que hace falta —cuántos sin edge cruzan
la cadena— pero no es un pase completo de la maquinaria.

### 2.2 · La cadena, igual que para las de verdad

Los mismos umbrales y las mismas ventanas, aplicados en el mismo orden. **Sin una sola excepción**:
cualquier criterio que se le ahorre al mono infla su supervivencia, y cualquiera que se le aplique de
más la hunde. Las dos direcciones invalidan el control.

Del 7 al 16 sobre `oos1`; 17 y 18 sobre `oos2`. Sí, el mono también mira `oos2` — y el ledger tiene
que registrarlo. Consúltalo con el dueño antes de tocar ese tramo: **es su bala**. El paso 19 (WFM)
es una tarea de SQX y al mono se le aplica su criterio, no la tarea.

### 2.3 · La salida

Un embudo lado a lado, paso a paso: cuántos monos entran y salen de cada criba, contra cuántas
reales. Y el número que justifica el encargo: **cuántos monos llegan al paso 20**.

Con eso, cada umbral de la cadena pasa a tener una cifra que hoy no tiene: su tasa de falsos
positivos. Escríbela en `ledger/thresholds.yaml` al lado de cada umbral.

## 3 · Los dos modos de fallo de este estudio

1. **Una población nula que no es nula.** Si los monos heredan cualquier cosa de la búsqueda real
   —el símbolo está bien, la selección de qué monos entran no— el control está contaminado. Los
   diez mil entran enteros; no se criba antes de empezar.
2. **Medir el filtro en vez del generador.** 🔬 Ya pasó: `MC_Trades` tiene el 99,9 % de sus 757 con
   beneficio OOS positivo porque desciende de una tarea con tres condiciones sobre `main/OOS`,
   mientras la databank `OOS` entera sólo el 26,9 % (`docs/encargos/5-nulos.md` §6bis). Declara de
   qué databank sale cada población y qué condiciones llevaba encima.

## 4 · Coste, ya medido

757 estrategias × 4 peldaños × 2.500 tiradas = **2 min 37 s**; extrapolado a 10.000, ~35 minutos.
El problema es vergonzosamente paralelo porque el sizing no compone sobre el equity, así que no hay
dependencia secuencial entre tiradas.

Lo único que sí cuesta máquina de SQX es **el export de las operaciones de la población real** con
la que se empareja la huella. Mídelo con `perf/` antes: el tiempo de `orderstocsv` sobre 10.000
estrategias es lo único del plan que sigue sin cuantificar.

## 5 · Verificación

1. **El mono pierde dinero, y eso es correcto.** 🔬 Con ocupación del 7,4 % captura ~2.867 $ de la
   subida y paga ~7.756 $ de coste. Si tu población nula gana de media, le has regalado algo.
2. **La reconciliación pasa antes de leer ninguna p.** `nulls/verify.py`, suelo 0.99.
3. **El embudo cuadra con el ledger** fila a fila.

## 6 · Cómo cierras

Página de manual si añades comando (regla dura 8). Devuelve el embudo comparado, el número del paso
20, y **la tasa de falsos positivos de cada umbral escrita en `ledger/thresholds.yaml`**.
