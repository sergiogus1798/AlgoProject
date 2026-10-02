# 40 · El cerebro con probabilidades: una regresión logística que predice si una estrategia sobrevive — encargo autocontenido

**Tu oficio:** Python sobre lo que ya está en `AlgoData`. No toca SQX.
**Tu encargo:** convertir el prototipo `scratch/cerebro/logit.py` en un estudio de verdad que diga,
para cada estrategia de un paso del workflow, **la probabilidad de que pase el paso siguiente** (y, cuando
haya datos, el oos2). Esa probabilidad se tiene que poder comprobar con nuestros resultados, no con la
opinión de un modelo. Y tiene que acabar en una regla de `pipeline/autopilot/criteria.yaml` que diga
cuántas estrategias cuesta y qué gana.

Lee `CLAUDE.md` · `CODESTYLE.md` · `studies/CLAUDE.md` · `core/study/CONTRACT.md` ·
`pipeline/autopilot/README.md` · `pipeline/autopilot/criteria.yaml` · `pipeline/autopilot/facts.py` ·
`studies/screening/gate/README.md` · `ledger/thresholds.yaml`.

---

## 0 · De dónde sale

Conversación del 2026-10-01. El dueño preguntó si Jev (TypeSafe AI, un modelo que devuelve
decisiones con probabilidad) podía ser el juez de cada paso. Respuesta: no. Su probabilidad es la
confianza del modelo en su lectura del texto, no la probabilidad de que la estrategia tenga ventaja.
Tampoco está calibrada con nuestros datos ni se puede auditar. La alternativa que le gustó es un modelo
propio entrenado con nuestras estrategias, que da probabilidades que se pueden comprobar. Corre en
local: no gasta tokens al usarse.

## 1 · El prototipo ya corrido (2026-10-01)

`scratch/cerebro/logit.py` (no está en git). Datos: los cinco `metrics/XAUUSD/{OOS, OOS-Sharpe,
OOS-Rexpect, OOS-Rexpect2, OOS-Rsquared}/metrics.csv`, 49.124 estrategias tras quitar las que repiten
firma IS.
- **Objetivo:** `Profit factor (OOS) > 1`. La tasa base es 0,276.
- **Entradas:** las 21 métricas IS, con `sign·log1p|x|` y estandarizadas.
- **Modelo:** regresión logística L2 (λ=1), con Newton en numpy porque `sklearn` no está instalado.
- **Validación:** se deja fuera un databank entero, se entrena con los otros cuatro y se rota.

| databank de prueba | AUC del modelo | AUC de la mejor métrica IS sola | PF>1 en el 20 % mejor (base) |
|---|---|---|---|
| OOS | 0,730 | 0,706 | 0,453 (0,255) |
| OOS-Sharpe | 0,685 | 0,632 | 0,469 (0,291) |
| OOS-Rexpect | 0,740 | 0,668 | 0,571 (0,323) |
| OOS-Rexpect2 | 0,692 | 0,639 | 0,437 (0,268) |
| OOS-Rsquared | 0,701 | 0,632 | 0,411 (0,243) |

**Calibración:** buena. Por deciles, lo predicho frente a lo real va de 0,04→0,02 a 0,53→0,49, y el
resto de deciles quedan a ±0,04.

**Como filtro** (corte en p ≥ 0,3): se queda el 46 % de la población. Entre las que se quedan, el
41 % tiene PF OOS > 1; entre las descartadas, el 17 %. Se pierde el 32 % de las ganadoras. Con
p ≥ 0,4 se queda el 26 %, sube al 45 % y se pierde el 59 %.

**Pesos:** mandan `DoF Ratio` (−), `# of trades` (+) y `Sharpe` (+). DoF y trades son casi colineales
(DoF ≈ trades / parámetros), así que **no leas cada peso por separado**.

## 2 · Lo que el prototipo NO prueba (hay que resolverlo)

1. **Un solo símbolo y una sola ventana OOS.** Dejar fuera un databank no es dejar fuera un periodo:
   las cinco poblaciones ven el mismo OOS de XAUUSD. Falta validar en otro símbolo (USDJPY tiene
   cosechas en `harvest/`) y en otro tiempo.
2. **PF OOS > 1 es un objetivo flojo.** El objetivo útil es «pasa el paso siguiente del autopiloto»
   y, al final, oos2 o MT5. Hacen falta runs completos con su `verdict.csv`, y hoy hay muy pocos.
   Construye el estudio para que el objetivo sea un parámetro.
3. **Las cinco poblaciones salieron de builds con fitness distintos**: no son una muestra al azar de
   lo que genera SQX.

## 3 · Lo que hay que construir

- Un estudio bajo `studies/` (el sitio exacto lo dice `studies/CLAUDE.md`) que hable el contrato de
  `core/study/`. Entra: un paso y el objetivo. Sale: la `p` de cada estrategia como dato del autopiloto,
  la tabla de calibración y la tabla de cortes (qué se queda, % de aciertos dentro y fuera, ganadoras
  perdidas).
- Entrenar siempre dejando fuera un **grupo** (un proyecto o un símbolo), nunca filas sueltas: las
  estrategias de un mismo build se parecen y la validación saldría inflada.
- Su capítulo del manual (regla 8) y su ficha en `knowhow/` con lo de §1 y §2.

## 4 · Lo que decide el dueño, no tú

- **El objetivo:** PF OOS > 1, pasar el paso siguiente, pasar oos2… (regla 11: pregunta).
- **El corte de `p` en `criteria.yaml`:** se le enseña la tabla de cortes con su coste y su ganancia,
  y elige él.
- Si se instala `scikit-learn` (`pip install --user`, sudo pide contraseña) o se sigue con numpy.
