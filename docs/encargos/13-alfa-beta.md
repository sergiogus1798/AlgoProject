# 13 · Alfa y beta — **interrogante aparcado, no encargo**

**Estado: en espera. Decisión del dueño, 2026-09-24.** Nadie lo coge todavía.

> *«El alpha y beta déjalo como un interrogante para hacer en última instancia.»*

## Por qué está parado

1. **Primero se cierra la secuencia individual.** Los pasos 1 a 21 deciden si una ventaja es real
   y qué forma tiene. Una descomposición factorial no cambia ninguna de esas decisiones.
2. **No hay con qué construir el factor que más valdría.** El factor «retornos de las EAs que ya
   se operan» mide redundancia con lo que ya está en producción, y hoy **éstas son las primeras
   EAs**: no hay cartera contra la que regresar.
3. **El intento anterior salía en una unidad engañosa.** El dueño ya lo hizo hace tiempo y la alfa
   salía siempre minúscula. La causa está identificada: contar los días planos como retorno 0. Con
   una ocupación del 7,4 %, la alfa por día de calendario es **~1/13** de la alfa por día en
   mercado. No estaba mal calculada; estaba dicha en la unidad que la hace parecer nada.

   ⚠️ Y el error contrario, para quien lo retome: **quitar los ceros no mejora la significancia**.
   Sube la media, sube la desviación y baja la n — el t-estadístico apenas se mueve, que es lo
   correcto. Si alguna vez se construye, se reportan las dos alfas y la ocupación, siempre juntas.

## Dónde irá cuando se haga

En **`studies/closing/exposure/`**, el paso 21, que ya está construido y ya tiene montada la antesala:
`occupancy.presence` dice cuánto del movimiento del mercado ocurrió mientras la estrategia tenía
posición y cuánto de ese movimiento tenía el signo correcto. Eso es una beta dicha en los dos
únicos términos que importan antes de montar ninguna regresión — y si sale alta, la regresión
sobra: lo que hay es beta con horario.

Lo que faltaría el día que se levante este interrogante:

- equity **marcada a mercado** por día, no el beneficio imputado al día del cierre (hoy el módulo
  usa lo segundo, que es lo que reporta SQX, y lo declara);
- α con t de **Newey–West**, porque los retornos diarios de posiciones de varios días están
  autocorrelacionados y una t normal miente;
- el **appraisal ratio** (α/σ_ε) como métrica de puerta en lugar del Sharpe bruto;
- betas rodantes, para ver deriva de estilo;
- y la lectura que de verdad interesa: **R² alto = la búsqueda redescubrió un efecto conocido con
  parámetros de más**.
