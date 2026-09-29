# Admisión de FundingPips — 2026-09-29

Estado: **candidata, bloqueada por la puerta G1**. Se sigue (catálogo semanal, ofertas diarias),
pero no entra en el universo de compra, ni en los avisos, ni en los estudios. Protocolo: `/firm-onboard`.

## Las puertas

| puerta | resultado | evidencia |
|---|---|---|
| G1 EAs | 🔴 **abierta, probablemente en contra**: según terceros que citan su centro de ayuda, los EAs de terceros sólo se permiten como gestores de operaciones o de riesgo, y usar cualquier otro EA para operar anula la evaluación o el cobro. **No dice si un EA propio generado con SQX cuenta como «de terceros».** | [Trading Conduct and Security Standards](https://help.fundingpips.com/hc/en-us/articles/34505029138449-Trading-Conduct-and-Security-Standards) (no se puede abrir de forma automática; lo citan fxempire, tradingfinder, propvator) |
| G2 MT5 | 🟡 abierta: las reseñas dicen que sí | terceros |
| G3 España | 🟡 abierta | — |
| G4 historial | 🟡 abierta | — |
| G5 reglas modelables | 🟡 las reglas existen, pero sólo las conocemos de terceros | propfirmsfinder (actualizada 2026-05-01) y otras reseñas |
| G6 trampas para EAs | depende de G1 | — |

## El catálogo

**Manual.** Su web tiene un control anti-bots (Vercel) y su centro de ayuda Cloudflare: no se puede
leer con código, y **no se fuerza** esa protección. El catálogo está tecleado en
`AlgoData/funding/manual/fundingpips.yaml` a partir de fuentes de terceros, **todo sin confirmar**:
precios de propfirmsfinder ÷ 0,8 (lo que muestran lleva un código del −20 % aplicado; coinciden con
los precios de lista que citan otras reseñas).

| programa | 5k | 10k | reglas (sin confirmar) |
|---|---|---|---|
| 2-Step Standard | 36 $ | 66 $ | +8 % / +5 %, diaria 5 %, máxima 10 % estática, 3 días por fase |
| 2-Step Pro | 29 $ | 55 $ | +6 % / +6 %, diaria 3 %, máxima 6 % estática; reparto 80 % |
| 1-Step | 59 $ | 99 $ | +10 %, diaria 3 %, máxima 6 % estática, 3 días |
| Zero (instantánea) | 69 $ | 99 $ | sin objetivo, diaria 3 %, máxima 5 % trailing |

El reparto en 2-Step Standard y 1-Step dependería de la frecuencia de cobro (semanal 60 %, quincenal
80 %, a demanda 90 %, mensual 100 %); reembolso tras el cuarto cobro en esos dos.

## Preguntas para ti (o para su soporte)

1. **¿Se puede operar con un EA propio generado con StrategyQuant X?** Sin un sí, FundingPips no
   sirve para este proyecto.
2. Si es que sí: comprueba en su web los precios y reglas de la tabla (son 8 cifras en tu universo)
   y pon `confirmed: true` en el fichero, o dímelo y lo hago yo.

**No la doy de alta hasta que se resuelva la pregunta 1.**
