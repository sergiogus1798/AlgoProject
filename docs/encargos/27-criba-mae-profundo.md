# 27 · La criba del MAE profundo — encargo autocontenido

**Tu oficio:** Python. Todo sale de listas de operaciones que ya existen; SQX no interviene.
**Tu encargo es un cribado temprano**: en el paso 8, sobre `build` y `oos1`, encontrar las
estrategias que viven de aguantar operaciones que se fueron muy en contra —3 o 4 ATR— hasta que
volvieron. No elige ningún stop: avisa, con números, de lo que el paso 24 se encontrará al final.

Lee `CLAUDE.md` · `CODESTYLE.md` · `docs/AgentPDFs/WORKFLOW.md` (pasos 8 y 24) · `studies/CLAUDE.md` ·
`core/study/CONTRACT.md` · `studies/closing/atrCalculator/README.md` · `studies/screening/gate/README.md` ·
`ledger/README.md`.

---

**Dónde va:** `studies/screening/maeDepth/`, con la forma de módulo de `studies/CLAUDE.md`
(`config.yaml`, `tooltips.py`, `one.py`, `many.py`, `report.py`). Corre **encadenado tras
`studies.screening.gate.report` sobre su misma cosecha**, igual que `edgeCost` y `feedQuality`, sin
import entre estudios.

## 0 · De dónde sale

Del dossier `docs/AgentPDFs/ideas-de-internet-y-libros-2026-09-27.md`, §1.1 («Construir sin stop») y
§5.4. El dueño, 2026-09-28:

> *«Deberíamos analizar en la zona IS/OOS1 qué estrategias tienen una inusual cantidad de trades en
> el que el MAE es superior a 3 o 4 ATRs. […] Luego ya se analiza al final el SL más adecuado, pero
> al inicio un cribado para no recibir sorpresas al final está bien.»*

**Por qué importa.** La cadena construye sin stop a propósito: un parámetro menos que sobreajustar.
El precio es que la búsqueda genética puede premiar estrategias que ganan **porque nunca cortan**:
una operación que va 5 ATR en contra y vuelve cuenta en el backtest como una ganadora más. Es el
patrón de LTCM y lo que casi todos los libros leídos esa noche señalan (Seykota, Minervini, Williams,
Katz, Aronson, los cinco de riesgo). En el paso 24 se pone un stop, y la estrategia que se opera deja
de ser la que pasó la puerta. Esta criba lo detecta en el paso 8, cuando descartar todavía es barato.

## 1 · Objetivos

1. **Medir, por estrategia y por tramo (`build`, `oos1` por separado)**, cuánto depende su resultado
   de operaciones profundas —las que en algún momento estuvieron a k ATR o más en contra— y en
   particular de las **profundas recuperadas**: profundas que acabaron en ganancia.
2. **Decir cuáles son inusuales** con el criterio del dueño (§3): MAE profundo y duración anómala a la vez.
3. **Un veredicto por estrategia** en `verdict.csv` (`strategy`, `identity`, `verdict`) que `/curate`
   sepa aplicar, con la acción que el dueño elija (§3): marcar o eliminar.
4. **Que el paso 24 no dé sorpresas**: la superviviente que llegue allí ya trae medida su
   dependencia del no-stop.
5. **Dejar su fila en el ledger** por tramo leído, y sus umbrales en `ledger/thresholds.yaml`.

## 2 · Las medidas, por estrategia y por tramo

Para cada operación: el ATR de SQX de la barra cerrada antes de la entrada, y el MAE en unidades de
ese ATR. Para cada k de la lista (por defecto 3 y 4, configurable):

| medida | qué es |
|---|---|
| `n_prof_k` y `frac_prof_k` | operaciones con MAE ≥ k ATR, y su fracción del total |
| `n_rec_k` y `frac_rec_k` | de ellas, las que cerraron en ganancia neta: las **recuperadas** |
| `pnl_rec_k` y `cuota_rec_k` | el P&L neto de las recuperadas, y su fracción del beneficio neto del tramo. Si el neto es ≤ 0, la cuota no se calcula y se dice |
| `neto_cortado_k` | el neto contrafactual si cada operación profunda se hubiera cerrado en −k ATR, con la sensibilidad al deslizamiento de §2.1 |
| `peor_mae` | el MAE máximo del tramo, en ATR, y su fecha |
| `mae_p95_ganadoras` | el percentil 95 del MAE de las ganadoras, en ATR: lo que leerá el paso 24 |

**Transferencia.** Las mismas medidas en `build` y en `oos1`, lado a lado. Una estrategia cuyas
recuperadas pesan poco en `build` y mucho en `oos1` es una señal por sí misma.

### 2.1 · El contrafactual no es una simulación de stop, y se dice

`neto_cortado_k` responde «¿cuánto quedaría si no se aguantara más allá de k ATR?», no «qué haría un
stop». Un stop real se llena con hueco y deslizamiento. `studies/CLAUDE.md` lo prohíbe sin
sensibilidad: se presenta con tres deslizamientos sobre el nivel −k ATR (0, 0,25 y 0,5 ATR por
defecto, configurables), y el texto del informe dice que es una cota, no un backtest. No se busca el
k que más gana: los k están fijados antes de mirar.

## 3 · Qué es «inusual» — decidido por el dueño, 2026-09-28

> *«Quizás por duración: que coincidan un MAE excesivo y una duración de trade a 2,5 desviaciones
> típicas de la media de trades de ese backtest.»*

**Una operación es anómala** cuando cumple las dos cosas a la vez:

- su MAE es ≥ k ATR, y
- su duración es ≥ media + 2,5 desviaciones típicas de las duraciones de las operaciones **de esa
  misma estrategia en ese mismo tramo**. `build` y `oos1` tienen cada uno su media y su desviación.

La duración se cuenta en barras del timeframe de la estrategia, no en horas: un fin de semana no
alarga una operación. La razón del criterio: una operación larga llega a 3 ATR en contra sin nada raro,
sólo por durar. Lo sospechoso es la que dura mucho más de lo normal **y además** se fue muy en contra.
Es el retrato de aguantar una perdedora hasta que vuelve.

Las medidas de §2 se calculan también sólo sobre las anómalas: cuántas hay, cuántas acabaron ganando
y qué parte del beneficio neto viene de ellas.

⚠️ **Una comprobación que el informe tiene que enseñar.** Las duraciones no son normales: tienen una
cola larga a la derecha. Con una distribución así, «media + 2,5 desviaciones» puede marcar pocas
operaciones o bastantes según la forma de la cola. El informe enseña, por estrategia, cuántas operaciones
superan ese corte de duración, antes de cruzarlo con el MAE. Si en una población real el corte no marca
casi nada o marca demasiado, se le enseña al dueño con los números. No se cambia por su cuenta.

### 3.1 · Lo que queda por decidir — pregúntalo antes de construir (regla dura 11)

1. **Los k.** ¿3 y 4 ATR, u otros? ¿Se leen los dos, o manda uno?
2. **Cuándo se marca la estrategia.** El criterio de arriba marca operaciones. Para marcar la
   estrategia hace falta un umbral: por ejemplo, al menos N anómalas, o que las anómalas recuperadas
   den más de un X % del beneficio neto del tramo. Propuesta: el porcentaje del beneficio, porque
   mide la dependencia y no depende del número total de operaciones.
3. **La acción.** ¿Se marca y sigue (`action: mark`, como `feedQuality`), o se elimina con `/curate`?
   Propuesta: marcar en la primera versión, hasta ver cuántas caen en una población real.
4. **El ATR.** Propuesta: el mismo del paso 24, ATR(20) de SQX (Wilder), para que las dos lecturas
   hablen en la misma unidad.

Como columnas informativas, sin decidir nada, van también la fracción de profundas sin el corte de
duración y el decil de la estrategia dentro de su databank.

## 4 · Cómo se construye

- **Datos:** la cosecha de la puerta, `AlgoData/harvest/<P>/<D>/<día>/trades.parquet`, que trae `MAE ($)`,
  `Size`, `Open time`, `Profit/Loss`, `sample` e `identity`. Nada de SQX.
- ⚠️ **El MAE viene en moneda de la cuenta, no en puntos**, y cada operación tiene su tamaño:
  `precio = abs(MAE_$) / (Size · pointValue)` (`studies/CLAUDE.md`). La última fila sin precio de
  cierre se descarta.
- **El ATR es el de SQX**: `engines.market.atr.sqx`, no la media simple de `engines.market.calibrate`
  (`knowhow/export/sqx-atr-is-wilder.md`). Barras con `core.barstore` en el timeframe de la estrategia.
- **El cálculo MAE/ATR ya existe en `studies/closing/atrCalculator/mae.py`.** Un estudio no importa
  otro: con dos usuarios, sube esa función a `engines/market/` y que los dos la usen. Es la regla de
  `studies/CLAUDE.md` para lo compartido, y garantiza que el paso 8 y el paso 24 midan igual.
- **La duración** sale de `Open time` y `Close time`, contada en barras de la estrategia con
  `core.barstore`, no en horas.
- **La puerta del ledger:** `ledger.gate.allow(8, segmento, activo)` antes de abrir nada. Sólo `build`
  y `oos1`; `oos2` está reservado y se rechaza.
- **Umbrales** en `ledger/thresholds.yaml`, leídos con `ledger:<clave>`, con quién los fijó y cuándo.
- **Contrato:** `one.run` y `many.run` devuelven el dict de `core/study/CONTRACT.md`, para que la
  ventana lo pinte sin una vista propia. Dos pestañas: la población (la distribución de
  `cuota_rec_k` con las marcadas) y la estrategia (build y oos1 lado a lado, y el histograma del MAE
  en ATR de ganadoras y perdedoras).
- Una línea `PROGRESS <0..100> <estado>` por avance, para la ventana y el pipeline.

## 5 · Verificación

1. **Caso de respuesta conocida.** Un test con operaciones sintéticas cuyo MAE en ATR se conoce a
   mano: cuántas profundas, cuántas recuperadas, el contrafactual exacto.
2. **Mismo número que el paso 24.** Sobre las mismas estrategias, el MAE en ATR por operación tiene
   que coincidir con el de `atrCalculator` operación a operación. Si no, uno de los dos convierte mal.
3. **Una cosecha real.** `AlgoData/harvest/USDJPY_workflow_profiling_v1/Results/2026-09-26/`: 200
   estrategias, 266.642 operaciones. Informe del tiempo que tarda y de cuántas marca con cada lectura.
4. **El corte de duración, a la vista.** Por estrategia y tramo, la media, la desviación, el corte y
   cuántas operaciones lo pasan, antes de cruzarlo con el MAE.

## 6 · Cómo cierras

- **Capítulo de manual** en `AlgoData/manual-fuentes/` con capturas reales, añadido a su familia en
  `tools/manual.py` (regla dura 8). Sin él, `tools/checks.py` falla.
- Una fila en la tabla del paso 8 de `WORKFLOW.md`.
- Tarjeta en `knowhow/` con lo que se descubra que no sea obvio, por ejemplo qué fracción de una
  población real vive de las recuperadas.
- `python3 tools/depmap.py && python3 tools/checks.py`.
- Lista de ficheros cambiados y **¿Quieres hacer el commit?** (regla dura 12).
