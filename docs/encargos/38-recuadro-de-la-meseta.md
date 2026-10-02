# 38 · Market Surfaces: que el recuadro pintado sea la meseta que se mide — encargo autocontenido

**Tu oficio:** Python, solo sobre lotes de variantes que ya existen. No toca SQX.
**Tu encargo:** en los heatmaps por activo del paso 18.5, el recuadro que marca «la región elegida» no
es la región que el estudio mide. Haz que sean la misma, que se vea bien, y que el resultado no pese
megas sin necesidad.

Lee `CLAUDE.md` · `CODESTYLE.md` · `studies/CLAUDE.md` · `core/study/CONTRACT.md` ·
`studies/optimisation/marketSurfaces/README.md` y su `config.yaml` · `measure/region.py` ·
`contract/grids.py` · `studies/optimisation/cloud/README.md` (la meseta de la Nube, que esta copia).

---

## 0 · De dónde sale

Del feedback de la ventana del 2026-09-30, §8.5. El objetivo: en el activo principal se eligió una
combinación de parámetros porque cae en una **meseta**. La pregunta es si en **esa misma región** de
parámetros también hay meseta en los demás activos: un heatmap por activo con la región marcada, y la
performance dentro de la región frente a fuera, en cada activo.

La sesión de esa noche hizo el heatmap por activo. La auditoría del 2026-10-01 encontró que lo pintado
y lo medido no coinciden.

## 1 · Lo que está mal hoy

- **Dos regiones distintas con el mismo nombre.**
  - La tabla «dentro / fuera» usa `region.plateau()`: las variantes a ≤ `region_radius` (2) escalones
    de la madre **en todos los parámetros a la vez** y además a ≤ `region_delta` (20 %) de su
    resultado en el build del activo principal.
  - El recuadro usa `region.box()`: el cuadrado de radio 2 alrededor de la madre en los dos parámetros
    del heatmap, **sin el filtro de delta**.
  - En las 15 madres de H1, la meseta medida es **una sola variante en 7 de 15** (la propia madre),
    mientras el recuadro abarca de 5 a 25 celdas. El dueño ve una región grande que el número de al
    lado no mide.
- **Una meseta de una variante no es una meseta.** El estudio la acepta igual y compara «dentro»
  (un punto) contra «fuera». Hay que decirlo y no dar veredicto de meseta con eso.
- **El recuadro casi no se ve:** su color es `T["faint"]`.
- **Peso:** los JSON de resultado ocupan entre 7 y 23 MB por madre. La ventana los parsea enteros.

## 2 · Objetivos

1. **Una sola región.** El recuadro tiene que dibujar exactamente las celdas cuyas variantes están en
   `plateau()`, proyectadas sobre los dos parámetros del heatmap. Una celda de la proyección cuenta como
   dentro si alguna variante de la meseta cae en ella; dilo en la nota. Si prefieres otra definición
   coherente, propónla, pero dibujo y medida tienen que salir del mismo conjunto.
2. **Meseta mínima.** Un número mínimo de variantes para llamar «meseta» a la región (propón el valor
   con datos de los 15 lotes de H1 y los 6 de M30; lo fija el dueño). Por debajo, el heatmap se pinta
   igual, pero el veredicto dice «sin meseta en el activo principal» en vez de comparar un punto.
3. **Visible.** Borde grueso y en color de acento sobre cualquier celda del heatmap, y la madre marcada
   aparte.
4. **Más ligero.** Mide qué ocupa cada bloque del JSON y quita lo que la ventana no pinta, o redúcelo,
   por ejemplo con menos decimales. Objetivo: menos de 2 MB por madre sin perder nada visible. Cuenta
   lo que pesaba y lo que pesa.
5. **Los 3D**, si caben: el feedback los pedía «idealmente». No son obligatorios en este encargo.

## 3 · Hecho es

- Re-run de las 15 madres de H1 en un directorio temporal: recuadro = meseta en todas, y el informe dice
  cuántas tienen meseta de verdad con el mínimo propuesto.
- Test de respuesta conocida: una rejilla pequeña puesta a mano en la que se sabe qué celdas entran.
- `README.md` y tooltips del estudio al día, y la tarjeta de knowhow si sale algo no obvio.
- El mínimo de variantes, preguntado al dueño antes de fijarlo (regla 11 de `CLAUDE.md`).
