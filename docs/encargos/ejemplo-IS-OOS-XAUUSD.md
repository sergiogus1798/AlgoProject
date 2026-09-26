# Proyecto de ejemplo: el IS y el OOS en dos databanks

Generado el 2026-09-23 a petición del dueño, para que la siguiente sesión tenga datos reales
con los que trabajar en vez de construirlos.

## Dónde está

```
SQX_w2 (custodio) · proyecto  XAU_ISOOS_ejemplo
~/Desktop/SQX_w2/user/projects/XAU_ISOOS_ejemplo/databanks/
    Results/   120 .sqx   ← IS,  2008-2017
    OOS/       115 .sqx   ← OOS, 2018-2022
```

Dos tareas y nada más: `Build strategies 2` escribe en `Results`, y `Retest strategies` lee de
`Results` y escribe en `OOS`.

## Lo que hay que entender

**Una estrategia vive en los dos databanks, y su nombre de fichero es el mismo en ambos.**
115 de los 120 ficheros de `Results` tienen un gemelo en `OOS` con idéntico nombre
(`Strategy 1.10.59.sqx`). Ese nombre es la clave para juntar los dos tramos.

Lo que cambia entre uno y otro es el **resultado**, no la estrategia: el `.sqx` de `Results`
lleva el backtest de 2008-2017 y el de `OOS` el de 2018-2022. Dentro del archivo, cada uno bajo
`Results/Main: XAUUSD_DukasM1_Infinox_LOM_M30/`. El del IS lleva además
`Results/CrossCheck_HigherPrecision/`, porque el crosscheck de alta precisión sólo se hace en la
construcción.

Los 5 que se quedan por el camino no pasaron el retest.

**Un export tiene que leer los dos databanks y unirlos por nombre de fichero.** Es la
consecuencia de que las ventanas estén separadas, que es lo que el dueño quiere: el IS con el
spread de construcción (5.0 / 2.5) y el OOS con el suyo (10.0 / 5).

## Cómo se hizo, por si hay que rehacerlo

```bash
python3 -m sqx.projects.builder Test_XAU_ISOOS_ejemplo --purpose "ejemplo IS/OOS" --timeframe M30 --symbol XAUUSD \
    --template ~/Desktop/AlgoData/templates/library/keltnerUpperCrossUp/template.sqx \
    --role custodian --tasks Build,Retest --only Build-Task3.xml,Retest-Task1.xml \
    --max-strategies 120 --minutes 12
```

⚠️ **Una cosa se tocó a mano y no es la configuración de verdad.** Las condiciones de aceptación
del retest se desactivaron en este proyecto. Con la del donante viva —`AnnualPctReturn > 0`—
pasaron **0 de 120**: ninguna de las Keltner aleatorias gana dinero en 2018-2022. Eso es un
resultado perfectamente normal para un build de humo, pero deja el databank `OOS` vacío y el
ejemplo no serviría para nada. Los filtros de aceptación son trabajo pendiente
(`assets/_study.yaml`, aún sin escribir).

**Estas 120 estrategias no son evidencia de nada.** Prueban la cadena, no la idea.
