# 38. Exposición — ¿cuánto tiempo de mercado te ha costado ese beneficio?

### Qué pregunta responde

Una estrategia gana un 7 % y el oro, comprado y olvidado, gana un 6 %. Parece un empate. No lo es
si la estrategia estuvo dentro del mercado **cuatro horas a la semana** y el comprador estuvo dentro
las 168: las 164 horas restantes no tuvieron gaps, ni noticias, ni caídas, ni capital inmovilizado.

Este módulo pone esas dos cosas una al lado de la otra: **lo que ganó y el tiempo de mercado que le
costó ganarlo**, contra el buy and hold del mismo activo en la misma ventana.

Es el **último paso de la secuencia**, el 21. No pregunta si la ventaja es real —de eso se
encargan los veinte anteriores—, sino qué forma tiene.

### Cuándo lo usas, y cuándo no

**Lo usas** cuando una estrategia ya ha sobrevivido a la cadena y hay que decidir si merece la pena
operarla en vez de, sencillamente, comprar el activo. También cuando quieres comparar dos
supervivientes que ganan parecido: la que lo consigue con menos horas dentro del mercado es mejor
negocio con el mismo número.

**No lo usas** para decidir si una estrategia tiene edge. Aquí no hay ningún contraste de hipótesis.
Una estrategia con suerte y poca exposición sale igual de bien que una buena con poca exposición.

**Y no lo uses sobre una población ya filtrada por beneficio.** 🔬 Sobre las 757 de
`XAUUSD/MC Trades` salen 755 `worth_it` — y no es que la criba sea inútil: esa databank desciende
de una tarea con tres condiciones de aceptación sobre `main/OOS`, así que el 99,9 % gana dinero
fuera de muestra por construcción. Una criba sobre un eje que ya se cribó no tiene nada que cortar.

### Antes de empezar

1. **Las operaciones exportadas.** `python3 -m sqx.export.export_trades --project ... --databank ...`
   deja `trades.parquet` en `AlgoData/raw/<proyecto>/<databank>/<fecha>/`. El módulo coge siempre el
   export más reciente.
2. **Las barras del feed** en la librería (`python3 -m sqx.export.sync_bars`). El timeframe se
   calcula desde el minuto, no hace falta exportarlo aparte.
3. **La ventana del tramo decidida** en `assets/_policy.yaml` para ese símbolo. Si `oos1` no tiene
   fechas, el módulo se para y te dice dónde ponerlas. No inventa una ventana.

**No toca SQX.** Puedes lanzarlo con la GUI del maestro abierta y con los workers parados.

### Cómo se ejecuta

```bash
python3 -m strategies.exposure.report \
  --project XAUUSD --databank "MC Trades" \
  --feed XAUUSD_DukasM1_Infinox --symbol XAUUSD \
  --strategy "Strategy 1.10.39(1)"
```

| flag | obligatorio | qué hace |
|---|---|---|
| `--project` | sí | proyecto tal y como aparece en SQX |
| `--databank` | sí | databank del que salió el export de operaciones |
| `--feed` | sí | nombre del feed, p. ej. `XAUUSD_DukasM1_Infinox`. De ahí salen las barras |
| `--symbol` | sí | nombre del fichero de activo, p. ej. `XAUUSD`. De ahí salen la ventana y el valor del punto |
| `--strategy` | no | una estrategia y su panel en pantalla. **Si lo omites, pasa las 757 y escribe la tabla** |
| `--set` | no | mueve un mando sin editar el `config.yaml`: `--set gate.min_efficiency=3` |

**Cuánto tarda:** 10 segundos las 757 estrategias de XAUUSD sobre cinco años de M30. Una sola, dos
segundos, casi todo leyendo el parquet.

### Qué produce

Todo en `AlgoData/reports/<proyecto>/<databank>/<fecha>/`:

| archivo | qué es |
|---|---|
| `exposure.csv` | una fila por estrategia con las 30 columnas: ocupación, las tres versiones del buy and hold, el compromiso y el veredicto |
| `exposure.json` | la configuración con la que se corrió, la ventana y cuántas pasaron |
| `exposure_<Estrategia>.csv` / `.json` | lo mismo para una sola estrategia. **Nombre aparte a propósito**: mirar una no pisa la tabla de la población del mismo día |
| `manifest.json` | de qué export salió y con qué versión del código |

### Cómo se lee el resultado

Una que sí merece la pena:

```
Strategy 1.10.39(1) · XAUUSD/MC Trades · muestra OOS1 · 2018-01-01 a 2023-01-01

  EN EL MERCADO           3.71% de las barras, 4.2 h de las 168 de la semana
                          111.2 % de la cuenta comprometido de media mientras opera
  LA ESTRATEGIA           9,184 $   7.57 %   CAGR 1.47 %   DD 4.35 %
  BUY AND HOLD            7,133 $   5.88 %   CAGR 1.15 %   DD 4.71 %
       (equal_risk, 0.141 lotes)

  POR HORA EXPUESTA      204.29 %   ->  34.74x lo que rinde el buy and hold
  EN TOTAL                 1.29x lo que rinde el buy and hold
  RIESGO                   0.92x su drawdown, y 164 h a la semana fuera del mercado

  ESTUVO PRESENTE    en el 4.0% del movimiento del mercado, alineado con el 0.1%

  VEREDICTO          worth_it
```

Línea por línea:

- **EN EL MERCADO.** El 3,71 % de las barras de la ventana tuvo alguna posición abierta: 4,2 horas
  de las 168 que tiene una semana. El 111 % es cuánto de la cuenta está comprometido **mientras
  opera** — por encima del 100 % porque opera con apalancamiento, que es lo normal en CFD.
- **LA ESTRATEGIA / BUY AND HOLD.** Las dos en la misma ventana y sobre el mismo saldo inicial.
- **`equal_risk`, 0.141 lotes.** Es la clave de toda la página. «Buy and hold» son tres frases
  distintas y hay que decir cuál se está diciendo: mantener **un lote** (aquí habría ganado
  50.650 $), mantener **el tamaño medio que usa la estrategia** (45.711 $), o mantener **el tamaño
  cuya volatilidad diaria iguala a la de la estrategia** (7.133 $). Sólo la tercera convierte
  «gana menos que el buy and hold» en una frase sobre la ventaja y no sobre el tamaño de posición.
  El panel usa la tercera y las tres están en el CSV.
- **POR HORA EXPUESTA.** El 7,57 % dividido entre el 3,71 % de ocupación: la tasa a la que gana
  **mientras está dentro**. Los 34,74x son esa tasa contra la del buy and hold, que está dentro el
  100 % del tiempo. ⚠️ **Es una extrapolación, no un retorno que nadie pudiera cobrar**: una
  estrategia que espera un setup no encontraría veintisiete veces más setups. Mide la calidad del
  tiempo gastado.
- **EN TOTAL.** El 1,29x es la comparación honesta y sin extrapolar: gana un 29 % más que el buy and
  hold al mismo riesgo. Está justo debajo para que los dos números no se confundan nunca.
- **ESTUVO PRESENTE.** Cuánto del movimiento del mercado ocurrió mientras tenía posición (4,0 %, es
  decir: prácticamente lo mismo que su ocupación, luego no está eligiendo los tramos buenos) y
  cuánto de ese movimiento tenía la dirección correcta (0,1 %). Un número alto aquí significaría
  que lo que hace es **acertar cuándo estar dentro**, que es beta con horario, no ventaja propia.

Y una que no merece la pena, para ver el contraste:

```
Strategy 14.10.29 · XAUUSD/MC Trades · muestra OOS1 · 2018-01-01 a 2023-01-01

  EN EL MERCADO          21.54% de las barras, 24.4 h de las 168 de la semana
  LA ESTRATEGIA           4,160 $   3.90 %   CAGR 0.77 %   DD 9.42 %
  BUY AND HOLD           14,162 $   13.28 %  CAGR 2.53 %   DD 9.66 %

  POR HORA EXPUESTA       18.11 %   ->  1.36x lo que rinde el buy and hold
  EN TOTAL                 0.29x lo que rinde el buy and hold

  VEREDICTO          not_worth_it
                     - eficiencia 1.36x, por debajo de 2.00x: por hora expuesta no rinde
                       mas que tener el activo
```

Está dentro seis veces más tiempo, gana la cuarta parte y aguanta el mismo drawdown. Por hora
expuesta apenas rinde más que tener el oro: no compensa la molestia.

**El umbral** está en `strategies/exposure/config.yaml`, `gate.min_efficiency`, y hoy vale `2.0` —
«que rinda al menos el doble por hora expuesta». Es una preferencia del dueño, no una ley, y se
mueve ahí o con `--set`. **Ganar menos en total que el buy and hold no es un suspenso** y nunca
dispara un motivo: ésa es justamente la dicotomía que el módulo existe para medir.

### Un ejemplo completo

```bash
$ python3 -m strategies.exposure.report --project XAUUSD --databank "MC Trades" \
    --feed XAUUSD_DukasM1_Infinox --symbol XAUUSD

757 estrategias -> /home/.../AlgoData/reports/XAUUSD/MC_Trades/2026-09-24/exposure.csv
```

Diez segundos. La distribución de esas 757, que es lo que hay que mirar cuando el veredicto no corta:

| | mediana | mínimo | máximo |
|---|---|---|---|
| ocupación | 8,3 % | 1,2 % | 26,6 % |
| horas por semana dentro | 9,4 | 1,4 | 30,1 |
| retorno de la estrategia | 10,8 % | −4,1 % | 22,9 % |
| buy and hold al mismo riesgo | 7,9 % | 3,2 % | 16,0 % |
| eficiencia por hora | 16,3x | −1,1x | 131,5x |
| drawdown contra el suyo | 0,78x | 0,38x | 1,53x |

### Qué NO te dice

- **No dice que la ventaja sea real.** No hay ningún p-valor aquí. Una estrategia afortunada con
  poca exposición sale exactamente igual de bien que una buena con poca exposición.
- **No dice que puedas cobrar la tasa por hora.** `POR HORA EXPUESTA` es una división, no un plan:
  no hay forma de tener veintisiete veces más posiciones.
- **No descuenta swap ni spread al buy and hold.** Una entrada en cinco años es ruido, pero el coste
  de financiación de mantener oro cinco años es real y **no está aquí**. Si el buy and hold sale
  apretado, ese coste juega a favor de la estrategia y no lo estás viendo.
- **No usa equity marcada a mercado.** El beneficio se imputa al día en que la operación **cerró**,
  que es lo que reporta SQX. Eso hace la serie diaria más a saltos y su desviación mayor, así que
  el `equal_risk` mantiene **menos** activo del que mantendría y la comparación es conservadora a
  favor de la estrategia, nunca al revés.
- **No hay alfa ni beta.** Decisión del dueño del 2026-09-24: aparcado hasta cerrar la secuencia
  individual. Lo que sí hay es su antesala — `ESTUVO PRESENTE` dice cuánto del movimiento del
  mercado ocurrió mientras tenías posición y cuánto tenía el signo correcto, que es una beta dicha
  en los únicos dos términos que importan antes de montar una regresión.

### Si algo falla

- **`el tramo oos1 de XAUUSD no tiene fechas decididas`** — la ventana no está en
  `assets/_policy.yaml`. No la inventa: ponla ahí.
- **`IndexError` al buscar el export** — no hay ningún `trades.parquet` para ese proyecto y
  databank. Expórtalo primero.
- **Una estrategia con menos de 30 operaciones o una ventana de menos de 250 días** sale siempre
  `not_worth_it` con el motivo escrito: no es que suspenda, es que no se puede leer.
