# 25 · Desglose estacional — encargo autocontenido

**Tu oficio:** Python numérico. No toca SQX ni gasta CPU de los workers — sólo lee lo ya exportado
(`metrics/` y el trade export). Nace de la comparación con BuildAlpha del 2026-09-27: el dueño pidió
esta lectura porque hoy no existe nada que diga si el resultado de una estrategia se concentra en
unos meses, unos días de la semana o unas horas — o si está repartido.

Lee `CODESTYLE.md` · `studies/CLAUDE.md` (la forma de un módulo, el contrato) ·
`studies/readings/entryQuality/README.md` (el hermano más cercano: mismo trato de "ratio sobre un
benchmark aleatorio", misma familia) · `studies/readings/monkey/README.md` (por qué la comparación
contra el azar importa más que la lectura descriptiva) · `engines/README.md` §`inference/`.

---

**Dónde va:** `studies/readings/seasonality/`, en la familia `readings/` (`studies/CLAUDE.md`) junto
a `monkey`, `profitShape`, `entryQuality`. No es un paso numerado del WORKFLOW — es una lectura
nueva sobre una estrategia o una población ya cerrada, como `edgeCost` o `structure`. Añade la fila
a la tabla de `studies/readings/README.md` cuando esté.

## 0 · La pregunta, y por qué no basta con un desglose descriptivo

BuildAlpha lo llama "seasonality breakdown": rendimiento agregado por mes, por día de la semana y
por hora. Aquí eso no es el final — **una tabla de "julio rinde mejor" sin más es la clase de
hallazgo que este proyecto ya sabe que es una trampa** (`studies/CLAUDE.md` §«Multiple testing es
la condición por defecto»): con 12 meses, 7 días y 24 horas hay decenas de celdas, y alguna
destacará por azar aunque no haya ningún patrón real.

Así que el encargo tiene dos capas, no una:

1. **El desglose** — P&L, nº de operaciones y win rate por celda de calendario (mes del año, día de
   la semana, hora de apertura), igual que pide el PDF de BuildAlpha.
2. **El contraste contra el azar**, obligatorio antes de enseñar la capa 1 como una lectura: ¿la
   concentración observada es mayor de la que produciría repartir las mismas operaciones al azar
   entre las mismas celdas? Usa `engines/inference` (Benjamini-Hochberg) para corregir por el
   número de celdas comparadas — el mismo principio que ya aplican `gate` y `snoopingScreen`.

**La decisión que debe salir, no una descripción:** si el resultado depende de una ventana de
calendario estrecha, eso es una fragilidad a reportar como tal (una hora, un día de la semana);
si el reparto es indistinguible del azar, dilo también — "esto no aporta nada" es una respuesta
válida (`CLAUDE.md` §«Un análisis termina en una decisión»).

## 1 · Forma del módulo

Sigue la plantilla de `studies/CLAUDE.md`:

```
studies/readings/seasonality/
  config.yaml   granularidad de las celdas (mes / día de semana / hora), umbral de significancia
  tooltips.py
  one.py        una estrategia -> el desglose + el contraste
  many.py       la población, si aplica -- probablemente sí: comparar cuántas estrategias muestran
                concentración real ayuda a saber si el hallazgo es del bloque o del ruido
  report.py
```

Reutiliza lo que ya exista en `core/trades.py` / `core/tradestore.py` para el timestamp de cada
operación — no reimplementes el parseo de fechas del trade export.

## 2 · Decisiones a cerrar por escrito antes de programar

| situación | qué decidir |
|---|---|
| ¿la hora es la de apertura del trade, la de cierre, o ambas se miran por separado? | documenta la elección; abrir y cerrar pueden estar en celdas distintas |
| huso horario del timestamp exportado | comprobar contra `knowhow/` si ya hay una nota sobre esto (broker time vs UTC); si no la hay, medirlo y escribirla |
| población pequeña por celda | con pocas operaciones por hora, el contraste pierde potencia — decide un mínimo de operaciones por celda por debajo del cual la celda se marca "sin datos suficientes", no se omite en silencio |
| solapamiento con `entryQuality` | el benchmark de `eratio.py` ya empareja por hora del día — revisa si se puede reutilizar esa maquinaria en vez de duplicarla |

## 3 · Cómo cierras

`python3 tools/depmap.py && python3 tools/checks.py` → 0 problemas · página de manual en español
con salida real (`docs/AgentPDFs/` primero, `tools/manual.py` después) · añade la fila a
`studies/readings/README.md` · si encuentras algo no obvio sobre el timestamp o el huso horario,
escríbelo en `knowhow/`.
