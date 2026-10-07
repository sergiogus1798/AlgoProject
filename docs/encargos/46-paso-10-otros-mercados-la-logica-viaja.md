# 46 · Paso 10 (otros mercados): «¿la lógica viaja?» — criterios P1-P9 — encargo autocontenido

> **Plan vivo.** El dueño entregó la propuesta el 2026-10-06 por la noche y cerró cuatro decisiones
> (§0). El Council (Torvalds, Musashi, Feynman; 2026-10-06) revisó el plan de implementación.
> Cada sesión actualiza la tabla de estado.

| parte | qué | modelo | estado |
|---|---|---|---|
| A | núcleo: corridas al azar conjuntas, tamaño por la doctrina, P/L en R, tensor | Opus | **hecho 2026-10-06** — `travel/{cells,sizing,shift,tensor,stat}.py`; batería sintética 11/11 (media z −0,02, desviación 1,08, rechazo 7 % al 5 % nominal y 1 % al 1 %); lecturas elegidas → decisión 7 |
| B | P1: detector de distancias fijas en el XML | Sonnet | **hecho 2026-10-06** — `fixed_distances()`, 8 tests; marca 28 de 6.000 estrategias reales. Sin cubrir: `DeadZonePip` del WAE (350 de 6.000) y `#StopLossInPips#` → decisión 6 |
| C | P2-P9 y controles 7.1 sobre el tensor; `verdict.csv` nuevo; humo sobre las diez | Sonnet | **hecho 2026-10-06** — `travel/{validity,frequency,units,rules,run}.py`; 32 tests; `checks.py` 0 problemas. `run.run` sólo probado por el humo |
| D | informe al dueño con la z de las diez estrategias | Sonnet | **hecho 2026-10-06** — `AlgoData/scratch/paso10_travel/2026-10-07/`; 21 s, 755 MB. **Media de z_conj +1,72 (fuera de ±0,63)** → decisión 8, antes del corte |
| D2 | diagnóstico de la media +1,72 de las diez | Opus | **hecho 2026-10-07** — dos sesgos del aparato (huecos de los feeds de índices en V1: +0,35 z en entradas uniformes; coste en R con ATR alto: +0,12 en las diez), juntos +0,3 a +0,45; quedan ≈ +1,45 que son de las estrategias, concentrados en los años del build. Salida: `AlgoData/scratch/paso10_travel/diagnostico-2026-10-07/` |
| D3 | arreglo de los huecos: validez por (mercado, celda) | Sonnet | **hecho 2026-10-07** — `tensor.displaced_share` y `tensor.exclude`; 10 pares fuera, todos de V1; población uniforme sobre barras reales centrada (V0 +0,01 · V1 +0,08 · V2 0,00 · completa +0,06, error 0,07); 37 tests. Las diez: media +1,56 (antes +1,72): `AlgoData/scratch/paso10_travel/2026-10-07-huecos/` |
| G | juzgar sobre el bruto en R (`travel.judge_on`) | Sonnet | **hecho 2026-10-07** — z sobre el bruto, `e`/τ½/β sobre el neto. Población uniforme centrada (+0,07 ± 0,07). Población de ATR alto: neto +0,98 → bruto **+0,30** (V0 −0,56 · V1 +0,45 · V2 +0,14): queda un resto que no es coste. Las diez: media +1,45, `AlgoData/scratch/paso10_travel/2026-10-07-bruto/` |
| E | **el corte**: `criteria.yaml`, `many.py`, ventana (sin gancho en el paso 9: decisión 2) | Sonnet | **hecho 2026-10-07** — diez reglas en el paso "10"; las diez de referencia: 0 Pasa, 5 Limbo, 5 Falla. **Sin captura de la pestaña Cross Market** (no hay forma de disparar una pestaña con proyecto elegido) |
| F | borrado de lo viejo, manual, knowhow | Sonnet | **hecho 2026-10-07** — el módulo pasa de 6.836 a 1.765 líneas; `verdict.csv` de las diez idéntico tras el borrado; copia de lo borrado sin commit en `AlgoData/scratch/paso10_travel/borrado-2026-10-07/`. Queda: captura de la pestaña, `engines/nulls/placement/*` (candidato a otra pasada), calibración (decisión 5), `e_principal` (encargo 44) |

**Tu oficio:** ingeniero del estudio `studies/transfer/crossmarket`. La parte A es estadística
(Opus); el resto es llevar a código lo ya decidido (Sonnet, regla 17).

**Tu encargo:** que el paso 10 juzgue con P1-P9 de la propuesta, todo medido contra las mismas
corridas al azar, con cada número en un solo sitio editable, y devolver al dueño **la tabla de
z de las diez estrategias de referencia** y el paquete del corte listo para aplicar.

**Lee, en este orden:** `CLAUDE.md` · `CODESTYLE.md` · `studies/CLAUDE.md` ·
`/home/sergioguslw/Desktop/criterios-paso-10-otros-mercados-propuesta.md` (**la especificación;
manda esta copia**, no la de `docs/AgentPDFs/`; ábrela por secciones: §3 el estadístico, §4
amplitud/τ/N_peor, §7 criterios y P9) · `studies/transfer/crossmarket/README.md` ·
`engines/README.md`. **Cuando la propuesta y este encargo no coincidan, manda este encargo.**

## §0 De dónde sale

Dueño, 2026-10-06: «Analiza lo que ya hay implementado y modifícalo/cámbialo o borra si ya no es
necesario (si no está en esa lista no es necesario), o implementa lo nuevo […] con input
parameters configurables». Sus cuatro respuestas de esa noche:

1. El criterio nuevo **sustituye** al vivo en `criteria.yaml`; lo viejo se borra.
2. **P1** va al inicio del paso 9.
3. **`e_principal`** (denominador de P7) queda **sin dato → LIMBO** hasta que el mono del paso 8
   (encargo 44, `studies/screening/gate/level3c.py`) lo entregue. Ninguna estrategia puede dar
   PASA en el paso 10 mientras tanto: aceptado.
4. Hay otra sesión usando SQX esta noche; se puede esperar.

**Lo que el Council cambió del plan** (consenso 2,625 / 3,5): esta noche se construye **al lado**
(partes A-D, sólo ficheros nuevos); el corte y el borrado (E, F) esperan al dueño. Motivos
comprobados: (a) `studies/transfer/crossmarket/` tiene 16 ficheros modificados sin commit de otras
sesiones y `simulate/excess.py` y tres tests **sin seguimiento** — borrarlos es irrecuperable;
(b) el custodian corre un workflow esta noche y lee `criteria.yaml` en cada paso que juzga;
(c) por la decisión 3 el corte no da ningún PASA todavía: no se pierde nada por esperar.
Segundo cambio: la comprobación de §3.10 (media de las diez dentro de ±0,63) es sólo 2σ, mira
sólo la media y un año vacío relleno con 0 la pasa: queda como **humo**; la puerta es una
**batería sintética de respuesta conocida** (parte A).

## §1 El contrato (lo fija este encargo; nadie lo cambia sin tocar esta sección)

**Carpeta nueva:** `studies/transfer/crossmarket/travel/` (con su `README.md`, en inglés). Tests:
`tests/test_crossmarket_travel*.py`. Nada fuera de eso se toca en A-D, salvo **añadir** la
sección `travel:` a `studies/transfer/crossmarket/config.yaml` y sus frases a `tooltips.py`.

**Un número, un sitio:**

| qué | dónde | por qué |
|---|---|---|
| lo que define un cálculo | `config.yaml › travel:` (la ventana lo edita en el cajón del estudio) | cambia los hechos |
| lo que corta Pasa / Limbo / Falla | `pipeline/autopilot/criteria.yaml` paso "10" (zona «Criterios») | cambia el veredicto, no los hechos |
| tamaño por la doctrina | `assets/_build.yaml › money_management` (Amount 1000, ATRPeriod 20, ATRMult 4) | ya vive ahí: se lee, no se copia |
| ventanas V0/V1/V2 | los tramos `build` y `oos1` del activo principal (`core.assetdata`) | se derivan, nunca se escriben |

`config.yaml › travel:` (valores iniciales de la propuesta):

```yaml
travel:
  draws: 5000              # B, corridas al azar (§3.3: 5.000-10.000)
  seed: 20261007           # semilla común a todos los mercados
  shift_unit: year         # year | semester — el bloque dentro del que se desplaza
  shift_step: week         # week | day — unidad del desplazamiento (§3.3.3)
  min_trades_market: 30    # por debajo: suma, pero tau = -inf y no cuenta en N_peor (§7.2)
  worse_z: -1.65           # z_j que define «mercado en contra» (§4.4)
  frequency: {z: 3.5, phi_min: 1.5, phi_max: 3.5}   # P2 (§2.4 b)
  validity: {point_value_margin: 0.02, flat_atr_fraction: 0.02}   # §7.1 (0.02 = 1/50)
  degradation: {min_trades_year: 30, min_years: 4}  # P9 (§7.3)
```

**Columnas de `verdict.csv`** (una fila por estrategia; hechos `crossmarket.verdict_csv.<col>`).
Sin dato = celda vacía (NaN), **nunca 0**:

| prueba | columnas | regla en `criteria.yaml` (parte E) |
|---|---|---|
| 7.1 | `markets`, `markets_valid`, `invalid_fraction` | `invalid_fraction` ≤ 0,25 o Limbo |
| P1 | `fixed_distance` (nº de parámetros de distancia fija) | 0 pasa; si no, Limbo |
| P2 | `freq_off`, `freq_off_fraction` | 0 pasa · 1-2 Limbo · ≥3 o >0,25 Falla |
| P3 | `z_conj`, `p_conj` | ≥2,33 · ≥0 · <0 |
| P4 | `z_conj_v2` (anotadas: `z_conj_v0`, `z_conj_v1`) | ≥0 · >−1,65 · ≤−1,65 |
| P5 | `z_minus_market` (anotada: `minus_market`) | ≥1,65; si no, Limbo |
| P6 | `p_breadth` (anotada: `breadth_count`) | ≤0,10; si no, Limbo |
| P7 | `tau_half`, `e_principal` (vacía hasta el encargo 44) | ≥0,5 · >0 · ≤0; sin dato Limbo |
| P8 | `worse`, `worse_fraction` | ≤1 · 2 · ≥3 o >0,25 |
| P9 | `z_beta`, `e_end` (anotadas: `beta`, `e_end_ratio`) | compuesto de §7.3 |
| anota | `net_t_pooled` (t conjunta sobre el neto, §3.8), `trades` | ninguna |

`markets.parquet` (estrategia × mercado): `z`, `p`, `e` (ventaja por operación frente al azar, en
R), `trades`, `z_freq`, `valid`, `invalid_reason`. La serie `d_y` de P9 va al `crossmarket.json`.

## Parte A — el núcleo (Opus: estadística)

Posee `travel/` salvo los ficheros de B y C. Construye, reutilizando y sin editar
`engines/market/reprice.py` (`costs`, `pnl`, `fills`), `engines/nulls/placement/trade_models.py`
(mira `block_shift` :61 y `semester_shift` :15: la semilla por periodo de calendario es lo que
hace conjunto el sorteo), `inputs/markets.py`, `load.py`:

1. **Tamaño por la doctrina** en el momento de entrada (riesgo `Amount` / (`ATRMult` × ATR(`ATRPeriod`)
   × valor del punto de la ficha)), para la real y para cada corrida — los lotes no se copian (§3.3 punto 3).
2. **P/L en R** (1R = `Amount`) con el repreciado común, el mismo para la real y las al azar (§3.2, §3.11).
3. **El sorteo conjunto:** por año natural un desplazamiento entero (0-51 semanas), el mismo para
   todos los mercados, rígido y con vuelta dentro del año; los años se parten en las fronteras
   de los tramos del principal si no caen en 1 de enero (§3.5).
4. **El tensor** `T[corrida, mercado, celda de calendario]` y el vector real, con las celdas
   asignadas por fecha de cierre; de él salen sin recalcular todas las z de C. Una celda sin
   datos es NaN y se propaga como «sin dato», nunca como 0.

**Puerta de A — batería sintética** (`tests/test_crossmarket_travel.py`, segundos, sin parquet):
con precios sintéticos sin ventaja, 11 mercados y unas 300 estrategias de entrada al azar: media
de z_conj en 0 ± 3 errores estándar, desviación 1 ± 0,1, tasa de rechazo al corte cerca de la
nominal; una deriva plantada en un mercado-año mueve z lo calculado a mano; desplazamiento cero
reproduce lo observado; permutar las etiquetas de mercado no cambia z_conj; escalar `Amount` no
cambia z; misma semilla → salida idéntica; un mismo sorteo desplaza igual todos los mercados; un
mercado sin un año no produce ceros. **Si algo de esto no sale, para e informa: C no empieza.**

Deja en `travel/README.md` la API que C va a usar. Lo no verificado del repreciado (cortos,
comisión no nula, swap de forex en puntos: docstring de `reprice.py`) se anota en el README y en
el informe, no se arregla aquí.

## Parte B — P1, el detector (Sonnet; en paralelo con A)

Posee `sqx/inspect/strategymeta/fixed_distance.py` y `tests/test_strategymeta_fixed_distance.py`.
Una función pura: de un `.sqx` (o su XML) devuelve la lista de parámetros de distancia fija en
puntos o pips — stop, objetivo, trailing, break-even, filtros de distancia (§2.4 a). Se apoya en
`sqx/inspect/strategymeta/rules.py` (`orders` :138, `values` :15, `EXIT_METHODS` :9) **sin
editarlo**; `sqx/projects/buildrules.py:14-17` lista los bloques de salida. Las claves de fórmula
de pips no están documentadas: sácalas de estrategias reales (`.sqx` de los databanks en
`AlgoData/`, y `knowhow/sqx-format/`), y deja la tarjeta en `knowhow/sqx-format/`. Test: un XML
con stop por ATR da lista vacía; uno con stop en pips, no. **No toca** `sqx/projects/crossmarket.py`
ni `ui/daemon/launch/configure.py` (el gancho es de la parte E).

## Parte C — P2-P9 y los controles (Sonnet; tras la puerta de A)

Posee el resto de `travel/` (las reglas, la frecuencia, la validez, el ejecutor) y
`tests/test_crossmarket_travel_rules.py`. Todo desde el tensor de A:

- **7.1 controles por mercado**, una vez por mercado y sin mirar a la estrategia: precios
  alineados (reutiliza el cálculo que hoy alimenta `fill_mismatch`, `verdict/alerts.py:43`),
  valor del punto ficha vs regresión, barras con ATR < `flat_atr_fraction` × mediana excluidas,
  ficha de costes completa. Mercado no válido: fuera de todas las pruebas, listado.
- **P2** con `studies/screening/analysis/centred.py` (`dispersion` :21, `rate_change` :42,
  `centre`), frecuencia del principal sobre build + oos1, centrada por la mediana de cada mercado.
- **P3-P8** (§3.4-3.6, §4.1-4.4) y **P9** (§7.3, la nula de la pendiente con las mismas corridas).
  Mercado ausente: cuenta en contra (§6). P7: `e_principal` se lee si existe; no existe → vacío.
- **El ejecutor**: una función `travel.run(...)` que de un export (`trades.parquet` del databank
  «Retest Markets - Family») escribe `verdict.csv`, `markets.parquet` y `crossmarket.json` con el
  contrato de §1, **en una carpeta que se le pasa** — nunca sobre un resultado existente. Sin
  `__main__` nuevo (eso lo trae la parte E al cambiar `many.py`).

**Puerta de C:** tensor de juguete con P3-P9 calculados a mano; P7 sin `e_principal` → vacío;
ninguna celda sin dato vale 0; las columnas de salida son exactamente las de §1.

## Parte D — humo sobre las diez e informe (Sonnet)

`nice -n 19`, un solo proceso (el custodian corre un workflow: regla 19). Entrada:
`AlgoData/raw/Trade_NIKKEI225_M30_volatilidadL/Retest_Markets_-_Family/2026-10-04/trades.parquet`.
Salida en `AlgoData/scratch/paso10_travel/2026-10-07/` (regla 7). Devuelve la tabla de las diez
(todas las columnas de §1), la media y la desviación de `z_conj`, los mercados no válidos y por
qué, y el tiempo y la memoria que costó. Se espera: cero PASA (P7), cero fallos de ejecución,
`z_conj` centrada cerca de 0. Una media fuera de ±0,63 **no se maquilla**: se informa tal cual.

## Parte E — el corte (espera al dueño)

Condiciones: A-D verdes; el dueño ha hecho commit (o descartado) lo pendiente de otras sesiones en
`studies/transfer/crossmarket/`; ningún workflow en marcha (`.claude/skills/sqx-wait/preflight.sh`).
Un solo agente posee: `criteria.yaml` paso "10" (las reglas de §1; P9 con `all`/`any`; tabla de
verdad en un test), `many.py` y `one.py` (pasan a llamar a `travel.run`), `contract/*` (las
pestañas pintan lo nuevo), `ui/text/columnhelp*.py`, `ui/text/glossary.py`,
`ui/daemon/databank/{table,cells,layout}.py`, `tests/test_autopilot_facts.py`,
`.claude/skills/workflow-simple/steps.md:16`, y el gancho de P1. Puerta: `judge` sobre el
`verdict.csv` de la parte D → todo Limbo, ningún PASA, ningún hecho sin resolver; un hecho ausente
da Limbo (test); `/ui-shot` de la pestaña Cross Market.

## Parte F — borrado y documentos (espera al dueño; tras E)

Primero `git status --porcelain` de cada ruta a borrar: lo que esté sucio y no sea de este
encargo **se deja y se informa**. Se borran: `simulate/{excess,exposure,paired,sweep,correlation,
joint,metrics,realrun,backtest}.py`, `verdict/{breadth,inference,fieller,significance}.py`
(`alerts.py`: sólo quedan los avisos que §6 mantiene como diagnóstico; `simulate/excess.py` lo importa `travel/run.py` para `net_t_pooled` — mover `weekly` y `t` a `travel/` antes de borrarlo), sus tests, lo que de
`mechanics/` y `orchestrate/` ya nadie importe, `POSSIBLE_IMPROVEMENTS.md`, `nulls.*` y lo demás
huérfano de `config.yaml` y `tooltips.py`, `perf/inputs/targets.py:19` y `workloads.py:21,103`.
Puerta: `grep -rn` de cada nombre viejo (`excess_t`, `excess_blind_t`, `markets_effective`,
`stouffer`, `vs_main_half`, `paired_p`, `risk_normalised`, `sharpe_total`, `expectancy_ci_lo`,
`cleared`) vacío en `ui/ pipeline/ studies/ tests/`. Manual: capítulos `05-retest-mercados`,
`30-crossmarket`, `39-crossmarket-lote` (`/manual-chapter`); `WORKFLOW.md:35`; las tarjetas de
`knowhow/research/` que citan lo viejo; `OPEN.md` #22 (`/open-close`). Cierre:
`python3 tools/depmap.py && python3 tools/checks.py`.

## Decisiones tomadas (dueño, 2026-10-07: «lo dejo a tu criterio»)

Resueltas por el agente coordinador; el dueño puede revocar cualquiera. El texto de cada
decisión sigue abajo con sus lecturas.

| nº | resuelto | por qué |
|---|---|---|
| 1 | el corte (E) y el borrado (F) van **después** del diagnóstico de la 8 y del commit del dueño de lo pendiente de otras sesiones en `studies/transfer/crossmarket/` | reescribir `many.py` o borrar `simulate/excess.py` con trabajo ajeno sin commit es irrecuperable; el commit es sólo del dueño (regla 12) |
| 2 | **(a)**: el paso 9 no hace nada; la estrategia se retestea y el estudio la marca (`fixed_distance` > 0 → Limbo). **No hay gancho en el paso 9** | 28 de 6.000: el SQX ahorrado es nada, y (b) y (c) añaden piezas o la descartan sin decirlo |
| 3 | como el 44: lo que calcula en `config.yaml › travel:`, lo que corta en `criteria.yaml` | un sitio por número, los dos editables desde la ventana |
| 4 | de la sección 8 sólo P9; la 8.1 no se encarga todavía | la población sin ventaja del diagnóstico de la 8 cubre lo urgente |
| 5 | las líneas son las de la propuesta, **provisionales**; `dev.on` sigue encendido | no hay poblaciones nula ni plantada pasadas por el paso 10 |
| 6 | **(a)**: `DeadZonePip` y `#StopLossInPips#` no cuentan en P1 | §2.4 nombra distancias de stop, objetivo, trailing y filtros; una regla que no viaja la caza P2 por su frecuencia |
| 7 | se aceptan las cinco lecturas del núcleo | son simétricas entre la real y las al azar |
| 8 | **se lanza el diagnóstico antes del corte** (parte D2) | la propuesta lo exige: encontrar el error, si lo hay, antes de juzgar |
| 9 | 0,25 ATR se queda; pasa a `travel.validity.max_fill_error` en la parte F | sólo cae el cobre, que la propuesta ya señalaba |

## Parte D2 — diagnóstico de la media +1,72 (Opus)

El lado invertido **no** sirve: con un nulo por desplazamiento invierte la real y las al azar
a la vez y z cambia de signo por construcción. Lo que separa las dos lecturas:
(i) **descomponer** el exceso de las diez en movimiento bruto y coste, los dos en R — el coste
en R es spread / (ATRMult × ATR de entrada), así que una estrategia que entra con el ATR alto
paga menos R de coste que sus corridas al azar: los costes no se cancelan del todo, y eso no es
habilidad; (ii) **dos poblaciones sin ventaja sobre las barras reales** de los once mercados —
entradas al azar uniformes, y entradas al azar condicionadas a ATR alto — que deben salir
centradas. Salida en `AlgoData/scratch/paso10_travel/diagnostico-2026-10-07/`.

## Parte D3 — los huecos (Sonnet)

Los feeds de índices tienen huecos de meses en 2011-2015 (HK50 157, 76 y 180 días; UK100 118 y
90; AUS200 111 y 92; USA500 y USATEC 89). Una entrada desplazada que cae en un hueco toma la
barra siguiente, así que las corridas al azar se amontonan tras cada hueco y una población sin
ventaja de entradas uniformes sale en +0,44 en V1. Arreglo, en el espíritu de §7.1 (control de
datos, mecánico, sin mirar a la estrategia): la validez pasa a ser por **(mercado, celda)**; una
sonda de entradas uniformes mide qué parte se desplaza, y el par que supere
`travel.validity.max_displaced_share` (0,20) queda fuera del tensor como sin dato. A 0,20 caen
unos 10 pares y la población uniforme queda en +0,06 ± 0,07. **Puerta:** esa población, repetida,
centrada en las cuatro ventanas (scripts en `scratch/d2/`).

## Dueño, 2026-10-07 (segunda respuesta)

«1. Sí, tu recomendación. 2. Revisa todo el módulo de crossmarket y elimina lo que ya no vaya a
ser necesario, el resto comitéalo.» Por tanto: **decisión 10 = (a)**, se juzga sobre el bruto en
R (parte G, `travel.judge_on: gross`); **el corte (E) y el borrado (F) se aplican ya** — el
borrado alcanza también a los ficheros del módulo con cambios sin commit de otras sesiones que
el diseño nuevo deja sin uso (lo que se conserva se lleva al commit con sus cambios); y **el
commit lo hace el coordinador** al acabar F: el módulo `studies/transfer/crossmarket/` entero y
los ficheros de este encargo, nada más (nunca `git add -A`). Sin SQX en marcha a las 2026-10-07
(preflight: ningún proceso, ningún candado).

## Decisión 10 — resuelta (a)

10. **El coste no se cancela del todo.** El coste en R es spread / (ATRMult × ATR de entrada):
    quien entra con el ATR alto paga menos R que sus copias desplazadas. En las diez pesa poco
    (+0,12 de media; +0,2 a +0,7 en las tres que de verdad entran con ATR alto), pero una
    población sin ventaja que entra con ATR en el tercio alto sale en **+1,20** (30 % de
    rechazo al 5 %). Lecturas: (a) **juzgar sobre el bruto en R** y dejar el coste en `e` — con
    los huecos fuera esa población queda en +0,08; cambia §3.1 de la propuesta («los costes se
    cancelan»); (b) cobrar a cada corrida al azar el coste en R de la entrada real — conserva
    el neto, pero el nulo deja de pagar su propio spread; (c) dejarlo y saber que las
    plantillas de volatilidad llevan ventaja. Recomendado: (a). **El corte espera a esto.**

## Decisiones del dueño — el texto y sus lecturas

1. **El corte y el borrado** (E, F): el Council los sacó de la noche. ¿Se aplican en cuanto hagas
   commit de lo pendiente de las otras sesiones en `studies/transfer/crossmarket/`?
2. **Qué hace el paso 9 con una estrategia de distancia fija (P1).** Lecturas: (a) sólo la marca
   y la retestea igual — no ahorra SQX, sigue en la cadena como Limbo; (b) la saca del retest —
   ahorra SQX, pero al no estar en el databank que se corta, sale de la cadena (en la práctica,
   descartada); (c) la saca del retest y la reinyecta después como Limbo — más piezas.
3. **Los umbrales, ¿a `ledger/thresholds.yaml`?** El encargo 43 (punto 8) pedía mover allí los de
   crossmarket; el 44 dejó los del paso 8 en el `config.yaml` del estudio y en `criteria.yaml`,
   editables desde la ventana. Aquí se ha seguido al 44.
4. **Sección 8 de la propuesta** (prior de la plantilla, factores, régimen, vecindad…): no se
   implementa nada salvo P9. La 8.1 es la de prioridad 1 y además da la población nula para
   calibrar: ¿encargo aparte?
5. **Calibración** (§5 «pendiente antes de fijar las líneas»): las líneas de §1 son las de la
   propuesta, sin calibrar; falta pasar las poblaciones nula y con ventaja plantada.

6. **¿Cuenta como distancia fija el `DeadZonePip` del WAE?** Es un parámetro en pips interno del
   indicador, no una distancia de stop u objetivo; lo llevan 350 de 6.000 estrategias reales.
   Lecturas: (a) no — P1 mira sólo stops, objetivos, trailing, break-even y filtros de distancia,
   como dice §2.4; (b) sí — cualquier parámetro en pips invalida la prueba en otro mercado, y
   esas 350 quedarían «no evaluables». Hoy el detector hace (a). Lo mismo para `#StopLossInPips#`
   (el stop de reserva del money management).

7. **Lecturas que tomó el núcleo (parte A)** donde la propuesta calla:
   (a) los lotes de la doctrina van **sin redondear ni topar** (`Decimals: 2`, `MaxLots: 500` no
   se aplican), en la real y en las al azar; (b) las operaciones de un mercado cerradas
   **después** del fin de oos1 del principal quedan fuera de V0+V1+V2; (c) a las operaciones
   desplazadas **no** se les reaplica el cierre del viernes ni «plano para entrar»: conservan su
   duración en barras; (d) una entrada sobre una barra defectuosa (ATR ínfimo) pasa a la
   siguiente barra válida, en la real y en las al azar; (e) con `shift_step: day` se cuentan días
   hábiles. Además: añadir `travel:` al `config.yaml` cambia su huella, así que **los resultados
   guardados de crossmarket se leen como caducados en la ventana** desde esta noche.

8. **Las diez de referencia no salen centradas: media de `z_conj` +1,72, desviación 1,70** (la
   propuesta, §3.10, pedía ±0,63 y dice que si no, hay un error que encontrar antes de juzgar).
   Por ventana: **V0 +0,14 · V1 +1,63 · V2 +0,75**. Dos lecturas, sin decidir: (a) es lo que §1.1
   predice — en los años que el generador no vio y mercados que tampoco (V0) el aparato está
   centrado, y el exceso vive en los años del build: estrategias ajustadas a la época; (b) hay un
   sesgo en el repreciado o en el sorteo que la batería sintética no ve con datos reales. Cinco de
   las diez dan `z_conj` ≥ 2,33 aunque fallaban el paso 8. Una coincidencia a favor del aparato:
   P2 marca 5 mercados a la Strategy 19.2.363, el ejemplo de §2.4. **El corte (parte E) no se
   aplica hasta resolver esto**; el diagnóstico que lo separa: repetir sobre una población sin
   ventaja por construcción (la 8.1 de la propuesta) o sobre las mismas diez con el lado invertido.
9. **`max_fill_error`** (0,25 ATR, lo que invalida un mercado por precios desalineados; hoy sólo
   cae el cobre, 0,58): la propuesta no da la cifra; se usa la del diagnóstico viejo,
   `config.yaml › diagnostics.max_fill_error`. En la parte F pasa a `travel.validity`.

## Lo que no tocas

El master. `oos2`. En A-D: **ningún fichero existente** fuera de las dos adiciones de §1 —
ni `criteria.yaml`, ni `many.py`/`one.py`, ni `ui/`, ni `engines/`, ni `sqx/projects/`. Ningún
SQX (ni `status`). Ningún commit, rama ni worktree (regla 12).

## Verificación

`python3 -m pytest tests/test_crossmarket_travel*.py tests/test_strategymeta_fixed_distance.py -q`
· los tests viejos siguen verdes (`tests/test_crossmarket_*.py`, `tests/test_autopilot_facts.py`)
· `git status --porcelain` sólo enseña ficheros de la parte · `python3 tools/depmap.py &&
python3 tools/checks.py`.

## Cómo cierras

Qué hiciste · qué verificaste, con la salida pegada · qué dejaste sin hacer y por qué · qué
descubriste para `knowhow/` · la lista de ficheros cambiados. Actualiza la tabla de estado.
