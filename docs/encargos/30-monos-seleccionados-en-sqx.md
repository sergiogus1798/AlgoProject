# 30 · Monos seleccionados dentro de SQX — encargo autocontenido

**Tu oficio:** SQX en el custodio, un snippet Java y Python para leer el resultado.
**Tu encargo es el control negativo que el encargo 9 no puede dar:** poblaciones de estrategias de
entrada aleatoria **construidas y seleccionadas por el propio Builder de SQX**, con la misma
selección que las estrategias reales, pasadas por la cadena de verdad. Cuántas sobreviven es la tasa
de falsos positivos de la cadena **con la selección incluida**.

Lee `CLAUDE.md` (reglas duras 1-6, 10 y 11) · `docs/AgentPDFs/WORKFLOW.md` · `docs/encargos/9-monos-de-punta-a-punta.md` ·
`.claude/skills/template-run/SKILL.md` · `studies/screening/gate/README.md` · `ledger/README.md` ·
`knowhow/conditions/no-seeded-hash-in-sqx.md`.

---

## 0 · De dónde sale

Aronson (*Evidence-Based Technical Analysis*, pp. 274-280 y 441-443): las estrategias de SQX son las
ganadoras de una búsqueda sobre `build`, y un mono sin seleccionar no pasa por esa búsqueda. Por eso
la tasa de monos que sobreviven sólo es **una cota inferior** de los falsos positivos. En su libro, la
mejor de 6.402 reglas sin valor gana un 11 % al año: un test ingenuo le da p = 0,0005 y el Reality
Check de White, p = 0,82. Dossier `docs/AgentPDFs/ideas-de-internet-y-libros-2026-09-27.md`, §1.2.

El 2026-09-24 el dueño descartó que SQX construyera monos (encargo 9, §2.1). **El 2026-09-28 lo reabre**,
después de ver el plugin WinRateEdge, y ha instalado su bloque aleatorio en el maestro:

> *«Sí, abre las dos cosas. Ya tienes además instalado en el SQX master el bloque random.»*

Los dos encargos se complementan. El 9 pasa monos de Python por los **criterios** de la cadena sin
selección. Éste pasa monos de SQX por la **cadena real**, con la selección del Builder. La diferencia
entre los dos números es lo que cuesta la selección.

## 1 · El bloque, tal como es — 🔬 leído del código el 2026-09-28

El plugin WinRateEdge (https://strategyquant.com/codebase/strategy-vs-random-edge-testing-winrateedge-results-panel/,
copia en `~/Downloads/codebase-strategy-vs-random-edge-testing-winrateedge-results-panel/`) trae
`RandomEntry.java`, instalado en `~/Desktop/SQX/user/extend/Snippets/SQ/Blocks/RandomEntry/`:

```java
@BuildingBlock(name="(RAND) Random Entry", display="Random Entry (#Probability#%)", returnType = ReturnTypes.Boolean)
public class RandomEntry extends ConditionBlock {
    @Parameter(name="Probability", defaultValue="5", minValue=0.01, maxValue=100, step=0.01)
    public double Probability;
    public boolean OnBlockEvaluate() throws TradingException {
        return Math.random() * 100 < Probability;
    }
}
```

- En cada barra dispara con probabilidad `Probability` %.
- ⚠️ **`Math.random()` no tiene semilla.** Dos backtests de la misma estrategia dan operaciones
  distintas. Nada de lo que produce se puede reproducir.
- **Sólo está en el maestro.** Ni el conductor ni el custodio lo tienen. El maestro es del dueño y en
  él no se construye nunca (regla dura 3).
- El plugin trae también un panel para el Retester, que no está instalado ni hace falta: su prueba
  es una z sobre la tasa de acierto, más débil que la escalera del mono del proyecto.

### 1.1 · Lo que la falta de semilla rompe, y lo que no

- **No rompe el control.** Un mono seleccionado se eligió por un `build` con suerte. Su retest en
  `oos1` es una tirada nueva e independiente, y eso es exactamente lo que dice la hipótesis nula: no
  hay nada que se transfiera. La cadena lo tiene que matar al ritmo del azar.
- **Sí rompe todo paso que vuelva a correr el `build`**: el MC Retest, el SPP, las variantes y la
  ablación del paso 23 no reproducen el `build` que se seleccionó. Para un mono, cada uno de esos
  pasos es otra tirada. El informe lo dice en cada paso.
- **Sí rompe la reproducibilidad** de los informes desde su manifest.

### 1.2 · La versión con semilla — la construyes tú

Un segundo bloque, `RandomEntrySeeded`, en el mismo sitio y con la misma forma, que cambia
`Math.random()` por un número pseudoaleatorio que sale de mezclar un parámetro `Seed` con la hora de la
barra. Java tiene aritmética entera de 64 bits, así que un mezclador serio (SplitMix64) cabe en diez
líneas. Con él:

- el mismo backtest da siempre las mismas operaciones;
- `Seed` es un **grado de libertad puro sin información**. Es justo el bloque de ruido de la parte C
  del encargo 28, que lo usa;
- las plantillas `.tpl` de MT4/MT5 no importan: un mono nunca va a MetaTrader.

Si el Builder deja a la búsqueda genética mover `Seed`, seleccionar semillas con suerte **es** la
selección que este encargo quiere medir.

## 2 · Objetivos

1. **Llevar los dos bloques al custodio**, y al conductor si hace falta para retests cortos, sin tocar
   el maestro.
2. **Construir poblaciones de monos** con el Builder, en las mismas condiciones que una población real
   (§3).
3. **Pasarlas por la cadena real**, empezando por el retest de `oos1` y la puerta, y contar.
4. **Dejarlo en el ledger** como población nula, para que sea la columna `mono@paso` de la tabla de
   rendimiento por familia del dossier de edge.

## 3 · El diseño

**Emparejar todo menos la entrada.** El mono se construye en un proyecto propio, `Test_monos_<activo>_<TF>_<n>`,
con `sqx.projects.builder --workflow` (regla dura 10), y con lo mismo que la población real que controla:
activo, timeframe, ventanas, costes de `assets/`, salidas de `assets/_build.yaml`, función de aptitud,
filtros de aceptación y tamaño de la databank. La única diferencia: la condición de entrada es el bloque
aleatorio y nada más, sin hueco y sin otras condiciones. Un mono con un indicador al lado ya no es un mono.

**Qué puede mover la búsqueda.** Con el bloque sin semilla, la búsqueda sólo mueve la probabilidad y
los parámetros de salida. Con el de semilla, también la semilla. Ninguna de esas cosas tiene información
sobre el precio futuro, **salvo una**: cuánto tiempo pasa dentro del mercado. En el oro alcista, un mono
que opera mucho y aguanta mucho gana por deriva. Eso no es un fallo del control: es la exposición que
también pueden estar capturando las estrategias reales, y la puerta tiene que verla igual en las dos.

## 4 · Decisiones del dueño antes de construir — pregúntalas (regla dura 11)

1. **¿Con o sin semilla?** Propuesta: con semilla para todo, porque es reproducible. El bloque sin
   semilla se queda como comprobación de que los dos dan la misma tasa.
2. **¿La probabilidad fija o libre?** Libre deja a la búsqueda elegir frecuencia y exposición, como hace
   con las reales. Fija en la frecuencia media de la población real mide sólo la suerte. Propuesta:
   libre, dentro del rango de frecuencias que tiene la población real.
3. **Cuántos builds de monos** por población real. Propuesta: tantos como builds tuvo la real, con el
   mismo tiempo cada uno.
4. **Hasta dónde llegan en la cadena.** Propuesta: primero `oos1` y la puerta. Si sobrevive alguno,
   se sigue con él por los pasos de SQX como cualquier superviviente, hasta donde la política deje.
5. **Qué activo y qué población real** se controlan primero.

## 5 · Cómo se construye

1. **El snippet con semilla**, en `sqx/blocks/snippets/RandomEntrySeeded/` del repo, con su README y un
   test de Python que reproduzca el mezclador y compruebe la frecuencia de disparo sobre barras reales.
2. **La instalación en el worker**, con el worker parado, siguiendo el protocolo de las reglas duras
   1-3: `ListAgents`, los proyectos recientes y la cola del log del día. Si otra sesión lo usa, se espera.
   🤔 **Sin probar:** cómo compila SQX un snippet Java en un worker sin GUI. Copia los ficheros a
   `user/extend/Snippets/SQ/Blocks/<Bloque>/` del worker, arráncalo y comprueba con
   `python3 -m sqx.inspect.vocabulary --diff custodian` que el bloque aparece. Si no aparece, **para y
   pregunta**: puede exigir compilarlo en la GUI, que es del dueño. Lo que descubras va a `knowhow/`.
3. **La reproducibilidad del de semilla, antes de nada más.** El mismo retest dos veces: las mismas
   operaciones, una a una. Y el sin semilla dos veces: operaciones distintas. Si el de semilla no se
   reproduce, no sigas.
4. **Los builds de monos**, uno a uno en el custodio, arrancando y parando sólo con
   `bin/sqx-worker.sh`. Entre arranque y recogida, sólo `-project action=status`. Pulso cada ~3 minutos.
5. **El retest de `oos1`, la cosecha y la puerta**, con las herramientas que ya existen (`/oos-gate`) y
   el mismo `config.yaml` que la población real.
6. **El ledger:** filas con la familia `mono_sqx` y una marca de población nula, para que nunca se
   mezclen con las reales en ningún recuento de supervivientes.
7. **El informe:** el embudo de los monos al lado del de la población real, paso a paso, y al lado del
   de los monos de Python del encargo 9 cuando exista. En `AlgoData/reports/…/monosSQX/`, con la forma de
   contrato de `core/study/CONTRACT.md`.
8. **La limpieza:** los proyectos `Test_` se retiran al acabar (regla dura 6).

## 6 · Verificación

1. **El mono seleccionado no conserva nada.** De media, el `oos1` de los monos seleccionados tiene que
   parecerse al de monos sin seleccionar. Si los seleccionados rinden más fuera, algo se transfiere, y lo
   más probable es la exposición a la deriva (§3). Dilo con números.
2. **El mono pierde dinero después de costes.** Como en el encargo 9: si la población nula gana de
   media fuera, le has regalado algo.
3. **El bloque dispara a la frecuencia que dice.** Con probabilidad p, la fracción de barras con entrada
   tiene que estar dentro del intervalo binomial de p.
4. **El embudo cuadra con el ledger** fila a fila.

## 7 · Cómo cierras

- Capítulo de manual en `AlgoData/manual-fuentes/` con capturas reales, y su familia en `tools/manual.py`
  (regla dura 8).
- Tarjetas en `knowhow/`: cómo se instala y compila un snippet en un worker, y la tasa de falsos positivos
  que salga.
- Actualizar `knowhow/conditions/no-seeded-hash-in-sqx.md` con lo que se compruebe.
- `python3 tools/depmap.py && python3 tools/checks.py`.
- Lista de ficheros cambiados y **¿Quieres hacer el commit?** (regla dura 12).
