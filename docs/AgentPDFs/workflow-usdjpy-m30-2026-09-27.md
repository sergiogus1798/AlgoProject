# El workflow entero — USDJPY M30, plantilla Donchian, noche del 2026-09-26 al 27

**Encargo del dueño** (26-09, antes de dormir): lanzar el workflow completo en USDJPY M30 con una
plantilla nueva —rotura de la banda superior de Donchian más una condición extra para el largo—,
correr **todos** los tests y reportar cualquier incidencia. Si a un activo le faltaban costes, usar
los de USDJPY: **no hizo falta**, los nueve pares de la familia tienen su fichero en `assets/`.

- **Activo:** USDJPY (`USDJPY_DukasM1_the5ers`), **M30**. Costes PROVISIONALES de
  `assets/symbols/USDJPY.yaml` (spread 0,1, comisión 0, slippage 0,05): ningún número con coste de
  aquí sirve para juzgar si el edge es real.
- **Proyecto:** `Test_USDJPY_donchianUpperCrossUp_M30`, custodio, `builder --workflow`.
- **Registro paso a paso** (comando, entradas, salidas, segundos, incidencia):
  `AlgoData/reports/Test_USDJPY_donchianUpperCrossUp_M30/workflow-steps.csv`.

**Resultado en una línea: la máquina llega de punta a punta, pero el paso 10 da un veredicto falso
y otros cinco módulos tienen fallos que esta corrida ha destapado.** Ninguna estrategia sobrevive:
las 8 del aforo mueren en el MC Retest, y las 3 que se forzaron hasta el final fallan el paso 20.

---

## 0 · La plantilla — `donchianUpperCrossUp` · ⚠️ lectura NO confirmada

Te fuiste a dormir, así que no pude preguntarte (regla 11). Elegí una lectura y **te toca
confirmarla o cambiarla**:

```
AND(
    Close[1] cruza por encima de DonchianChannels(Periodo).Upper[2]   ← fija
    una condición aleatoria libre                                      ← la «condición extra»
)
```

| pregunta | elegido | alternativas |
|---|---|---|
| qué precio rompe | el **cierre** | el máximo, u orden stop sobre la banda |
| estado o evento | **cruce** (dispara una vez) | estado: el cierre *está* encima, dispara en cada barra |
| qué banda | la `Upper` nativa = máximo de los `High` | el bloque viejo `CBlock_BreakoutDonchianLong` usa el máximo de los **cierres**: no es Donchian |
| desfase | **`Upper[2]`**, el canal hasta la barra anterior | `Upper[1]` es imposible: incluye el `High` de la propia barra |
| entrada | a mercado, barra siguiente | stop sobre la banda |

Periodo aleatorio por estrategia (2-220), long, salida de la pila del esqueleto. Bloque nuevo
`CBlock_CloseCrossesAboveDCUpper` (+ su espejo), instalado en los dos workers. Ficha completa:
`AlgoData/templates/library/donchianUpperCrossUp/brief.md`. **200 de 200** estrategias llevan la
rotura (contado a mano: ver incidencia 4).

## 1 · El embudo

| paso | qué | entran | salen | tiempo |
|---|---|---|---|---|
| 5-7 | proyecto, build y OOS | — | 200 | 2,5 min |
| 8 | puerta OOS (sanidad −4, estáticas −9, degradación −8; mono 0) | 200 | 179 | 1 min |
| 8 | SPA/StepM contra buy & hold (anota): 0 de 200 a FWER 0,05; 138 antes de corregir; SPA p = 0,40 | 200 | — | 4 s |
| 8 | edge por coste: 200/200 sobre 2 spreads · calidad del feed: 200/200 «insuficiente» | 200 | — | 10 s |
| 8 | **aforo** (no calidad): top 8 por beneficio IS | 179 | 8 | — |
| 9-10 | crossmarket, 9 pares | 8 | 8 ⚠️ | 1,5 min + 11 s |
| 10.5-12 | crossTF (M30 → H1, H4) | 16 hermanas | 1 sobrevive | 1 min |
| 13-14 | MC Retest, 7 tareas (sin MinDist: entradas a mercado) | 8 | **0** (8 FAIL) | 42 min |
| — | **aforo forzado**: 3 madres, sólo para probar la mecánica | 8 | 3 | — |
| 15-16 | SPP IS y OOS | 3 | 3 «proceed» | 2 min |
| 16.5 | variantes: 5.000 + 3.981 + 2.466, tres patas WFC | 3 | 3 | **2 h 50 min** |
| 19 | WFM, 30 celdas | 3 | 0 predicen (3 «perverse») | 11 min |
| 17 | WFC: ρ −0,21 / −0,30 / −0,45 | 3 | 0 | — |
| 18 | CSCV: PBO del argmax 18 % / 30 % / 38 % | 3 | 3 pasan | — |
| 18.5 | superficies por mercado | 3 | 0 | — |
| 20 | lectura ciega conjunta | 3 | **0** bajo cualquiera de tus 4 reglas | 2 s |
| 21 | exposición: 3/3 «worth_it», 19-26 % del tiempo en mercado | 3 | — | 1 s |
| 22 | mapa condicional | 3 | — | 6 s |
| 23 | estructura: la rotura **aporta** en build en las 3; en oos1 sólo en 9.20.85; el filo vive en la dirección | 3 | — | 4 min |
| 24 | stop ATR (sólo 9.20.85, ver incidencia 6): injerto idéntico, X leídas en meseta | 1 | — | 7 min |
| 25 | edge por coste de la versión con stop: 0 de 22 bajo 2 spreads | 22 | — | 5 s |

Lecturas extra: forma del beneficio y calidad de la entrada (3 madres, descriptivas) y nube de
parámetros (3 madres: «middling»; una «smooth», dos «rough» — corrida con un parche, incidencia 5).

**Lo que dice de la plantilla, con la advertencia de costes:** la rotura Donchian sí lleva algo
dentro de muestra (el estudio estructural lo ve en las tres madres), pero no lo sostiene fuera:
el MC Retest mata a las 8, el WFC sale negativo en las tres —optimizar en IS empeora fuera— y la WFM
las marca «perverse». **Decisión:** en USDJPY M30 esta plantilla no es candidata; no merece otra
pasada con estos costes.

## 2 · Incidencias, de más a menos grave

1. 🔴 **El paso 10 da por buenas estrategias que pierden** (OPEN.md §57). El informe crossmarket
   aprobó 8/8 con el PF del peor mercado entre 1,31 y 1,51; el P/L neto de SQX da PF 0,79-1,07, con
   8 de los 9 mercados por debajo de 1 en todas. El estudio re-valora los trades desde la apertura
   de la barra y nunca resta el sobreprecio de entrada, que es donde SQX mete spread y slippage.
   Todo veredicto guardado del paso 10 sobre estrategias rentables en bruto es sospechoso. No
   apliqué ese veredicto. Ya marcado 🔴 en la fila 10 de `WORKFLOW.md`.
2. 🟠 **La identidad de una estrategia cambia sola** (§58). Tras el MC Retest, SQX reescribió los
   `.sqx` quitando un atributo (`autoGenerated`), la identidad cambió y `/curate` se negó —bien— a
   aplicar el recorte. Lo rehíce desde los ficheros. Arreglarlo mueve todas las identidades
   guardadas: **decisión tuya**.
3. 🟠 **El MC Retest de spread y slippage no prueba nada en USDJPY** (§59): 2 y 1 resultados
   distintos en 1.000 simulaciones. Los rangos en décimas de punto se redondean. Ya pasó esta mañana
   en H1. Los rangos de forex son tuyos.
4. 🟠 **`template_check` da «ok» sobre el bloque equivocado** (§60): desde que tu condición va en un
   grupo de un ítem, comprueba `MarketPositionIsLong`, que llevan todas.
5. 🟠 **La nube de parámetros no lee el panel de las variantes** (§61): busca columnas con el nombre
   antiguo. La corrí parcheando los dos nombres en memoria, sin tocar el código.
6. 🟠 **El stop del paso 24 no se injerta en 2 de 3 madres** (§62): la búsqueda exige un orden de
   atributos que SQX no siempre escribe. El paso 24 corrió sólo con 9.20.85.
7. 🟡 Menores (§63): el builder necesita `--session-from` para USDJPY; `crossTF/config.yaml` está
   fijo en H1 y hay que pasarle M30 a mano; `registry --set` borra la fila entera al actualizar un
   campo (lo rehíce); el auditor nocturno bloquea `execute --clear` porque su línea de comandos
   nombra el custodio; y cuatro cosméticas (fecha de cabecera de la puerta, tabla de control del
   paso 23, SQX leyendo `scaling.parquet`, 3 corridas MCR con 999 simulaciones).

**Lo que funcionó sin tropiezos:** builder, build, puerta, SPA/StepM, edge por coste, curate (con
su guardia de identidad), crossTF, MC Retest sin el crash de esta mañana, SPP, las 11.447 variantes
con sus controles, WFM, ledger y paso 20 ciego, estructura, stop ATR y paso 25.

## 3 · Coste

El 16.5 es la factura de la noche: 2 h 50 min de custodio para tres madres, y **un tercio es SQX
escribiendo a disco** (~6 ficheros/s, 1,25 MB cada uno: ~25 min por pata de 5.000). El JVM llegó a
85 GB de RSS con el heap de 80 g, sin presión de memoria (36 GB libres en el peor momento).

## 4 · Lo que queda

- El proyecto `Test_` ya está retirado (regla 6): `AlgoData/projects/retired/SQX_w2/Test_USDJPY_donchianUpperCrossUp_M30-2026-09-27.tar.gz`, con la WFM. Los resultados siguen en `AlgoData/raw`, `harvest`, `reports` y `strategyPermutations`.
- Confirmar la lectura de la plantilla (§0).
- Tus tres decisiones: identidad (§58), rangos del MC Retest en forex (§59) y, ya abierta, qué es
  «pasar» el paso 20.
