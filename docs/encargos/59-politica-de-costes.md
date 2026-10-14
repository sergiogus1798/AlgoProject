# 59 · Política de costes — primero el recuento barato, después las cinco decisiones

**Tu oficio:** costes de ejecución sobre operaciones ya cosechadas y sobre ticks; Python numérico, sin SQX.
**Opus** para la parte 1 (qué se cuenta y cómo se lee) y para redactar las preguntas con sus cifras;
**Sonnet** para las partes 2 a 5 una vez contestadas (regla 17).
**Tu encargo:** una tabla — cuántas estrategias de una cosecha del NIKKEI225 cambian de signo en `build`
al pasar de 304 a 747 y a 1.000 puntos de spread — y, con ella en la mano, **cinco decisiones del dueño
contestadas y ejecutadas**: spread histórico de los índices, la hora del rollover, el swap abonado a 0, el
comando que calcula el método vigente, y el coste de las salidas por stop. Nada de las partes 2 a 5 se
escribe antes de su respuesta. «Cambia el signo de 3 de 1.000: no merece la pena» es un resultado válido.

Lee `CLAUDE.md` (reglas 5, 7, 8, 9, 11, 16, 20) · `CODESTYLE.md` · `assets/RULES.md` (líneas 85-110 y
230-240) · `studies/data/spread/README.md` · `knowhow/costs/funded-tick-spread-vs-price.md` (sólo la cabecera).

## Estado del plan (lo actualiza cada sesión al cerrar)

| parte | qué | modelo | depende de | estado |
|---|---|---|---|---|
| 1 | recuento de cambios de signo, NIKKEI225 `build` | Opus | nada | sin empezar |
| 2 | spread histórico de los índices | Sonnet | parte 1, pregunta 1 | bloqueada por el dueño |
| 3 | la hora del rollover | Sonnet | pregunta 2 | bloqueada por el dueño |
| 4 | swap abonado a 0 en el resto de activos | Sonnet | pregunta 3 | bloqueada por el dueño |
| 5 | el comando del método vigente y el candado de `--write` | Sonnet | pregunta 4 | bloqueada por el dueño |
| 6 | coste de las salidas por stop | Opus | pregunta 5 | bloqueada por el dueño |

### Bitácora

- 2026-10-11 — Encargo escrito desde la revisión del dueño de los pasos 1 a 7 (§4, puntos 1 a 5).

---

## 0 · De dónde sale

Revisión del dueño del 2026-10-11 (`~/Desktop/revision-pasos-01-07-2026-10-11.md`, §0 y §4): «Los costes no
son comparables entre tramos […] Toda caída de rendimiento entre tramos mezcla pérdida de ventaja con subida
de coste», y de su §4.1: «Antes de decidir, contar sobre una cosecha ya hecha cuántas estrategias cambian de
signo entre 304, 747 y 1.000 puntos (NIKKEI225, `build`)». Las cifras salen del dossier
`docs/AgentPDFs/criterios-implementados-2026-10-12.md` (no lo leas entero: las líneas van en cada parte).

Lo que ya se comprobó en el código el 2026-10-11, y corrige o precisa la revisión:

- La ficha del NIKKEI225 cobra **304,11 / 474,91 / 796,12** puntos en `build` / `oos1` / `oos2`
  (`assets/symbols/NIKKEI225.yaml:32,36,40`); Darwinex midió 747 / 732 / 458 (dossier, líneas 318-324 y
  568-574; el 747 es la media de ticks de la parte medida de `build`, 2017-10 a 2019).
- El método vigente — la firma de fondeo **más ancha**, media ponderada por tiempo en % del precio × el
  precio medio del tramo, factor 1,0, slippage 35 % del spread del tramo — está **descrito**
  (`assets/RULES.md:96-100`, `knowhow/costs/funded-tick-spread-vs-price.md`) pero **ningún comando lo
  calcula**: `studies/data/spread/onboard.py` sigue sacando el spread de los ticks de Darwinex
  (`onboard.py:125`), y su `--write` pisaría una ficha con el método antiguo.
- El swap abonado está a 0, a mano, sólo en `assets/symbols/UKOIL.yaml:130-133` y `USOIL.yaml:51-54`. Hay 28
  fichas; el dossier (líneas 581-585) cuenta 16 activos con un lado abonado.
- Existe un perfil horario del spread, sólo para informar (`studies/data/spread/measure.py:47-61`); nada lo
  lleva a SQX.

## 1 · El recuento (Opus) — lo único que se hace sin preguntar

**Datos.** Una cosecha ya hecha, sin tocar SQX: `AlgoData/harvest/Trade_NIKKEI225_M30_volatilidadL/Results/`
(tres fechas; corrió con la ficha vigente, 304,11 en `build`). Las operaciones se leen como lo hace
`studies/readings/edgeCost/inputs.py:29-56` (`newest`, `trades`, `names`) — reutilízalo, no escribas otro
lector. Si esa cosecha no trae operaciones de `build`, usa otra de `AlgoData/harvest/*NIKKEI225*` y dilo.

**La cuenta.** Por estrategia, el neto de `build` tal como corrió, y revalorado a 747 y a 1.000 puntos: a
cada operación se le resta (spread nuevo − 304,11) × valor del punto × tamaño. Da **dos columnas**, porque
el slippage va al 35 % del spread y se cobra a la entrada y a la salida: «sólo spread» (× 1) y «spread con
su slippage» (× 1,7; `assets/RULES.md:94-97`). Las órdenes son a mercado, así que qué operaciones ocurren
no cambia. Entrega:

| | a 304 (como corrió) | a 747 | a 1.000 |
|---|---|---|---|
| estrategias con neto > 0 en `build` | | | |
| cambian de signo respecto a 304 | — | | |
| mediana del neto / mediana del coste total | | | |

y lo mismo restringido a las que pasaron el paso 8 si la cosecha lo dice. Escribe al pie la advertencia:
la población se **seleccionó** a 304, así que el recuento es una cota inferior de lo que cambiaría un build
hecho a 747 (habría elegido otras). Va a un script en `scratch/` y la tabla a
`AlgoData/audit/costes/nikkei225-cambio-de-signo-<fecha>.md` (regla 7); si el dueño quiere repetirlo en
otros índices, entonces se convierte en una opción de `studies/readings/edgeCost/`, no antes.

**Para ahí y pregunta** (sección 7) con la tabla delante.

## 2 · Spread histórico de los índices (tras la pregunta 1)

Lo que haya decidido el dueño se escribe por `core.assetwrite` (el único escritor de fichas, `assets/RULES.md`),
con `python3 -m core.assets <SÍMBOLO>` antes y después (regla 5; para si sale ≠ 0), en cada índice de
`assets/symbols/` — la ficha no distingue índices (el NIKKEI225 es `class: no_forex`, como el crudo y los
metales): enseña al dueño la lista de `grep -l 'class: no_forex' assets/symbols/*.yaml` y que marque cuáles.
Ninguna ficha se toca en un activo con un proyecto corriendo.

## 3 · La hora del rollover (tras la pregunta 2)

En USDJPY (FTMO, 36 días de ticks) la hora 0 del servidor cotiza a 9,0 × la media y las otras 23 a 0,73 ×
(dossier, líneas 641-650). Antes de construir nada mide, con `studies/data/spread/measure.py:47-61`, qué
fracción de las operaciones de dos cosechas reales entran o salen en esa hora: si es ~0 %, dilo y la
pregunta 2 se contesta sola. La regla 15 prohíbe bloques de reloj en lo que el builder sortea: cualquier
lectura que meta un filtro horario en la estrategia choca con ella y se le dice al dueño.

## 4 · Swap abonado a 0 (tras la pregunta 3)

Tabla previa, sin escribir nada: por activo, el lado abonado, su % anual y desde qué año se aplica hacia
atrás (el largo de USDJPY cobra +0,59 % anual desde 2008). Después, lo decidido, con `core.assetwrite` y el
mismo `why` fechado que llevan `UKOIL.yaml:130-133` y `USOIL.yaml:51-54`.

## 5 · El comando del método vigente (tras la pregunta 4)

Hoy lo que `assets/RULES.md:96-100` describe no lo calcula nadie. Lo construido debe: leer los ticks de las
firmas de fondeo donde ya estén (`AlgoData/INDEX.md`), dar por activo y tramo el spread de la firma más
ancha (el mayor de sus medias de 12 y 3 meses, en % del precio × precio medio del tramo, factor 1,0) y el
slippage al 35 %; imprimir el plan y escribir sólo con `--write`; y **`studies.data.spread.onboard --write`
debe negarse** a pisar una ficha cuyo `why` es del método vigente. Un test con una ficha de juguete que lo
demuestre. Si resulta un comando nuevo (`__main__`), lleva su capítulo (`/manual-chapter`, regla 8) y la
skill `.claude/skills/asset-onboard/SKILL.md` se corrige en la misma tarea.

## 6 · El coste de las salidas por stop (tras la pregunta 5)

Las salidas por stop costaron 1,23-1,24 spreads por pata en FTMO y FundingPips, las salidas por señal
0,44-0,60 (dossier, línea 345; base: las 600 operaciones reales de `knowhow/costs/funded-tick-spread-vs-price.md`).
El modelo cobra plano. Afecta a la versión con stop (paso 24). Lo decidido se aplica donde el dueño diga.

## Lo que no tocas

SQX, en ningún install (ni arrancar, ni parar, ni consultar): este encargo es Python sobre disco ·
`project.cfx` de nadie · `pipeline/autopilot/criteria.yaml` · `oos2` como tramo de juicio (el recuento es
sólo `build`) · las fichas, antes de la respuesta de su parte · el money management (encargo 61) · el
estudio del build (encargo 60) · `OPEN.md` §85 (fondeo).

## 7 · Decisiones del dueño — pregúntalas (regla 11)

**Contestadas por el dueño (2026-10-14)** — lo que sigue manda sobre la lista de abajo:
- 2 → **medir primero** la fracción en la hora 0; si pasa del 1 %, subir el spread medio ponderado (nunca excluir la hora: regla 15).
- 3 → **swap abonado a 0** en los 16 activos. 4 → **modo nuevo de `onboard`** y recalcular las 28 fichas. 5 → **nada**: el 35 % de slippage ya lo cubre.
- Sin objeto por el 65: 1 (NIKKEI se queda en 304).


1. **Spread histórico de los índices.** Lecturas: (a) como hoy — el % de 2026 de la firma más ancha por el
   precio medio de cada tramo (NIKKEI225: 304 / 475 / 796); (b) lo que midió Darwinex donde hay ticks
   (747 / 732 / 458) y el método vigente donde no; (c) el **mayor** de los dos en cada tramo; (d) una cifra
   única para todo el histórico. ¿Y vale para todos los índices o sólo para los que la tabla de la parte 1
   señale?
2. **La hora del rollover.** (a) no modelarla si las estrategias casi no operan en ella (la medida de la
   parte 3 lo dice); (b) subir el spread medio del tramo para que la incluya ponderada por operaciones, no
   por tiempo; (c) excluir esa hora en las tareas de SQX — que es reloj, y la regla 15 lo prohíbe en el
   builder: ¿cuenta una sesión de la tarea como «bloque de reloj»?
3. **Swap abonado a 0.** (a) en los 16 activos con un lado abonado, como el crudo; (b) sólo donde el abono
   supere un % anual que tú fijes; (c) dejarlo. ¿Y el lado que **paga** se queda al peor de FTMO/Hantec?
4. **El comando del método vigente.** (a) un modo nuevo de `studies.data.spread.onboard`, que deja de leer
   Darwinex; (b) un comando aparte, y `onboard` queda sólo para activos sin ticks de fondeo; (c) `onboard`
   se retira. ¿Se recalculan las 28 fichas con él o sólo las nuevas?
5. **Coste de las salidas por stop.** (a) nada: el 35 % de slippage ya lo cubre en media (1,33 × de ida y
   vuelta); (b) un slippage mayor sólo en la tarea que retestea la versión con stop; (c) revalorar en
   Python las salidas por stop a 1,24 spreads al juzgar el paso 24. ¿Con qué cifra?

## Objetivo — un comando

Para las partes 1 a 4 y 6 no lo hay: son una tabla y decisiones; se verifican a ojo (abajo). Para la parte 5:

```
python3 tools/depmap.py && python3 tools/checks.py && python3 -m pytest tests/test_spread_method.py -q
```

**Verificación.** Parte 1: la tabla existe, sus tres columnas suman el mismo nº de estrategias, y a 304
reproduce el neto de la cosecha (diferencia 0). Partes 2 y 4: `python3 -m core.assets <SÍMBOLO>` sale 0 en
cada ficha tocada y su `why` lleva fecha y decisión. Parte 3: la fracción de operaciones en la hora 0, pegada.

## Cómo cierras

Qué hizo · qué verificó, con la tabla y las salidas pegadas · qué dejó sin hacer y por qué (una parte sin
respuesta queda «bloqueada por la pregunta N» en la tabla de estado) · qué descubrió para `knowhow/costs/`
(al menos: el recuento de cambios de signo, editando la ficha que exista) · la lista de ficheros cambiados
y, como última línea, **¿Quieres hacer el commit?**
