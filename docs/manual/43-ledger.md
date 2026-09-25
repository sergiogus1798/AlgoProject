## 43. El libro mayor de la búsqueda — cuántas cosas se han probado de verdad

### Qué pregunta responde

Cada paso de la cadena cuenta su propio embudo y se le olvida. Cuando llegas al paso 17 con tres
supervivientes, **nadie sabe si salieron de diez mil o de cincuenta** — y esa diferencia no es
contabilidad, es el resultado.

Este módulo es el libro que no se olvida. Escribe **una línea por búsqueda** —una construcción, un
retest, una criba de Python, un umbral aplicado— durante toda la vida de un estudio, y con eso
contesta tres cosas que hoy nadie puede contestar:

1. **El embudo entero**: de cuántas a cuántas, paso a paso, con los umbrales de cada corte.
2. **Cuánta historia se ha gastado**: qué tramos ha mirado alguien, cuántas veces, y si el `oos2`
   sigue siendo virgen de verdad.
3. **Cuántas cosas se han probado en total**, que es el número que el Sharpe desinflado necesita y
   que hoy recibe subestimado — porque se le da la dispersión de un lote de variantes en vez de la
   de todo el estudio.

Y hace cumplir dos reglas que hasta ahora dependían de la buena voluntad de quien corriera la cadena:
**nadie mira el `oos2` si no es el paso 17 o el 19**, y **el paso 20 no se lee hasta que 17, 18 y 19
estén los tres hechos**. No avisa: se niega.

### Cuándo lo usas, y cuándo no

**Lo usas** siempre. Un estudio sin ledger no puede decir lo que vale su superviviente.

**No lo usas para decidir nada por ti**: no puntúa estrategias ni las descarta. Cuenta.

Y **no edites `ledger/thresholds.yaml` para que algo pase**. Un umbral movido después de ver los
resultados es la manera más barata de sobreajustar la cadena entera.

### Antes de empezar

Nada. El fichero de un estudio se crea solo la primera vez que se le escribe, en
`~/Desktop/AlgoData/ledger/<estudio>.jsonl`.

Un **estudio** es un activo + un timeframe + una plantilla o familia de plantillas:
`XAUUSD_M30_DirectionalMomentum`. Es la unidad a la que se le debe la corrección por comparaciones
múltiples: todas las búsquedas que han tocado ese activo con esa plantilla cuentan juntas, venga del
paso que venga.

### Cómo se ejecuta

**Leer un estudio:**

```bash
python3 -m ledger.report --study XAUUSD_M30_DirectionalMomentum
```

**Comprobar que los umbrales escritos siguen siendo los que el código usa:**

```bash
python3 -m ledger.report --check-thresholds
```

**Reconstruir hacia atrás un estudio que ya corrió**, desde lo que dejó en disco:

```bash
python3 -m ledger.backfill \
    --gate ~/Desktop/AlgoData/reports/XAU_ISOOS_ejemplo/Results/2026-09-23/gate \
    --symbol XAUUSD --timeframe M30 --family DirectionalMomentum --write
```

| flag | obligatorio | qué hace |
|---|---|---|
| `--study` | sí (en `report`) | el identificador del estudio |
| `--check-thresholds` | — | compara el registro con el código y sale con error si divergen |
| `--equity` + `--identity` | no | añade el Sharpe desinflado de una superviviente concreta |
| `--gate` | sí (en `backfill`) | el directorio del informe de la puerta |
| `--write` | no | sin él, `backfill` enseña lo que haría y no escribe |

Segundos, y no toca SQX.

### Qué produce

Un `.jsonl` por estudio bajo el data root: **una línea JSON por búsqueda, y nada la reescribe
nunca**. Se añade al final; no hay borrado ni edición, porque un libro que se puede editar después
contesta una pregunta distinta de aquella para la que se hizo.

### Cómo se lee el resultado

```
XAUUSD_M30_DirectionalMomentum · 8 búsquedas · /home/…/AlgoData/ledger/XAUUSD_M30_DirectionalMomentum.jsonl

-- el embudo, paso a paso
        ts  step        criterion segment  n_in  n_out   kept
2026-09-23     8   gate/presencia    oos1   120    115 0.9583
2026-09-23     8     gate/sanidad    oos1   115    112 0.9739
2026-09-23     8   gate/estaticas    oos1   112     64 0.5714
2026-09-23     8 gate/degradacion    oos1    64     45 0.7031
2026-09-23     8       gate/forma    oos1    45     45 1.0000
2026-09-23     8        gate/mono    oos1    45     45 1.0000
2026-09-23     8     gate/familia    oos1    45     45 1.0000
2026-09-23     8 gate/redundancia    oos1    45     45 1.0000
de 120 entraron a 45 supervivientes

-- qué historia se ha gastado
segment  searches steps      first       last
   oos1         8   [8] 2026-09-23 2026-09-23
  build  2008 → 2017  leído 0x
  oos1   2018 → 2022  leído 8x
  oos2   2023 → 2026-08-30  leído 0x  RESERVADO para WFC, WFM

-- la puerta ciega del paso 20
  17 pendiente · 18 pendiente · 19 pendiente
  ledger: el paso 20 es ciego hasta que 17, 18 y 19 estén los tres hechos; faltan [17, 18, 19].
  Mirar dos antes de correr el tercero contamina la decisión de correrlo, y el oos2 es la última bala

-- lo que se ha probado en total: N = 115 candidatos sobre 1 búsqueda(s), sigma = 0.3506 (annualised)
  benchmark con N de la última búsqueda (  115): 0.0570 (por día)
  benchmark con N de el estudio entero  (  115): 0.0570 (por día)
  los dos coinciden: este estudio sólo tiene una búsqueda con distribución registrada
```

**El embudo** se lee de arriba abajo. `kept` es qué fracción sobrevivió a ese corte. Aquí las
estáticas se llevaron casi la mitad (112 → 64) y la degradación otro 30 %.

**El mapa de gasto** es el que contesta «¿sigue siendo holdout mi holdout?». `oos1` leído 8 veces
ya no es fuera de muestra en ningún sentido útil; `oos2` con 0 lecturas sí lo es.

**La puerta ciega** dice qué falta para poder leer el paso 20. Mientras falte uno, cualquier módulo
que llame a `gate.allow_read` revienta en vez de enseñarte números.

**El total probado** es la razón de ser del módulo: `sigma` es la dispersión de los candidatos entre
los que se eligió, y `N` cuántos fueron. Los dos alimentan el Sharpe desinflado. En este estudio los
dos benchmarks coinciden porque **sólo una búsqueda registró su distribución** — el `backfill` sólo
puede recuperar lo que la puerta dejó escrito, y de los pasos anteriores no queda registro. Con dos
búsquedas ya se separan: medido en `tests/test_ledger.py`, al pasar de N=1.600 a N=2.000 el listón
sube de 0,1995 a 0,2031 y el Sharpe desinflado baja de **0,6301 a 0,6000**.

⚠️ **Las unidades no se mezclan.** SQX guarda Sharpes anualizados y las fórmulas de
`core/significance.py` trabajan por observación. Cada línea apunta en qué unidad venían sus
candidatos, y agrupar dos unidades distintas **lanza** en vez de dar un número creíble y falso.

### Un ejemplo completo

La comprobación de umbrales, con salida real:

```
                               key  declarado  en_código  coincide fijado_por         el
           gate.sanidad.min_trades      20.00      20.00      True      dueño 2026-09-23
    gate.degradacion.min_retention       0.00       0.00      True      dueño 2026-09-23
gate.degradacion.max_concentration       1.00       1.00      True      dueño 2026-09-23
           gate.forma.max_dd_ratio       5.00       5.00      True      dueño 2026-09-23
                   gate.mono.max_p       0.50       0.50      True      dueño 2026-09-23
                gate.familia.alpha       0.05       0.05      True      dueño 2026-09-23
              profitShape.max_top5       0.60       0.60      True     agente 2026-09-24
                 profitShape.alpha       0.05       0.05      True     agente 2026-09-24
             entryQuality.dcr_high       0.30       0.30      True     agente 2026-09-24
          parameterCloud.rank_high       0.95       0.95      True     agente 2026-09-24
        parameterCloud.plateau_low       0.15       0.15      True     agente 2026-09-24
            parameterCloud.rho_low       0.20       0.20      True     agente 2026-09-24
                       cscv.blocks      12.00      12.00      True      dueño 2026-09-23

el registro y el código dicen lo mismo en los 13 umbrales declarados
```

Cada fila apunta a dónde lee el código ese número. Si alguien lo cambia en su `config.yaml` y no
aquí, esta orden lo caza y sale con error — que es como está pensado para meterse en un guion.

### Qué NO te dice

- **No sabe lo que no se registró.** Una búsqueda que no llamó al ledger no existió para él, y los
  pasos anteriores a que esto existiera sólo se recuperan si dejaron un artefacto por escrito. Las
  líneas reconstruidas van marcadas `backfill` y llevan la fecha del informe, no la de hoy.
- **No es la fuente de los umbrales todavía.** `thresholds.yaml` es hoy el **registro**: el código
  sigue leyendo cada número de su propio `config.yaml`, y esta orden comprueba que dicen lo mismo.
- **No decide nada.** No puntúa, no descarta y no ordena.

### Si algo falla

- `PermissionError: el paso N no puede mirar oos2` — **no es un fallo, es la puerta**. Si crees que
  ese paso sí debería poder, se arregla en `assets/_policy.yaml`, que es tuyo, y no ensanchando la
  comprobación.
- `ValueError: las búsquedas mezclan unidades de score` — alguien registró Sharpes anualizados y
  otro por observación en el mismo estudio. Hay que decidir cuál y rehacer el registro de esa fase.
- `sin búsquedas registradas todavía` — el estudio no tiene fichero: o el identificador no coincide
  (mira `~/Desktop/AlgoData/ledger/`) o nadie ha escrito nada aún.
