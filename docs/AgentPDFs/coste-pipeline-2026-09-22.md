# Qué cuesta el pipeline — medido el 2026-09-22

Informe de costes para optimizar el proceso global. **Todo lo que hay aquí está medido en esta
máquina**, no estimado. Lo que no pude medir está marcado como tal y se dice por qué.

La instrumentación ya no es un script aparte: `pipeline/ledger/cost.py` mide **todas** las etapas de
**todas** las corridas y lo escribe en el `state.json` de cada madre. Muestrea los **dos** árboles de
procesos — el de Python y el JVM de SQX, que `getrusage` no ve — y anota el pico de cada uno, los
segundos de reloj y los bytes que la carpeta de trabajo ganó o perdió.

---

## 1 · La corrida completa, etapa por etapa

`Strategy 17.9.39`, XAUUSD M30, **2.000 variantes**, retest con cross-check en XAGUSD, arrancando
con el custodio apagado:

| etapa | segundos | % del total | RSS SQX | RSS Python | disco |
|---|---:|---:|---:|---:|---:|
| `sppultra` | 2,1 | 1,1 % | — | 112 MB | 0 |
| `design` | 1,2 | 0,6 % | — | — | 0,4 MB |
| `build` | 5,2 | 2,7 % | — | 296 MB | **28,0 MB** |
| **`ran`** | **180,7** | **95,0 %** | **21.142 MB** | 219 MB | 0,6 MB |
| `collected` | 0,5 | 0,3 % | — | — | 0,2 MB |
| `wfc` | 0,5 | 0,3 % | — | — | 0,1 MB |
| `verdict` | 0,1 | 0,1 % | — | — | 0 |
| **TOTAL** | **190,2 s** | | **21,1 GB** | 296 MB | 29,3 MB |

**Todo el trabajo está en una etapa.** `ran` es el 95 % del tiempo y el 100 % de la memoria. Las
otras seis juntas son 9,6 segundos. Cualquier optimización que no toque `ran` es cosmética.

## 2 · Lo que cuesta el cross-check en otro mercado

Misma estrategia, mismas 2.000 variantes, lo único que cambia es el cross-check:

| | `ran` segundos | RSS SQX | por variante |
|---|---:|---:|---:|
| solo XAUUSD | ~95 | ~12,0 GB | 47 ms |
| XAUUSD + XAGUSD | 180,7 | 21,1 GB | 90 ms |
| **coste del segundo mercado** | **+90 %** | **+76 %** | **+43 ms** |

Es casi exactamente lineal: **un mercado adicional cuesta otro backtest completo**, en tiempo y en
memoria. Tres mercados serían ~270 s y ~30 GB. El custodio tiene 48 GB de heap, así que el techo
está en **unos 4-5 mercados simultáneos** antes de tocarlo.

⚠️ **Y no lo aprovechas.** El export del databank **no trae ni una columna del mercado adicional**
— lo comprobé: cero columnas con `market`, `addit` o `XAG` en la cabecera. Así que ahora mismo el
cross-check cuesta el doble de todo y sus resultados no se pueden leer por esta vía. **Es la
optimización más rentable que hay sobre la mesa**: o se encuentra la vista/export que los expone, o
se apaga hasta entonces y la corrida va al doble de velocidad.

## 3 · Coste unitario

| cosa | tiempo | disco | memoria |
|---|---:|---:|---:|
| fabricar una variante | **2,6 ms** | **14,0 KB** | — |
| retestear una, 1 mercado | 47 ms | — | — |
| retestear una, 2 mercados | 90 ms | — | — |
| el registro de una madre (sin las variantes) | — | **~500 KB** | — |

Escalado, por **madre**:

| variantes | fabricar | disco | retest 1 mercado | retest 2 mercados |
|---:|---:|---:|---:|---:|
| 2.000 | 5,2 s | 28 MB | 95 s | 181 s |
| 5.000 | 13 s | **70 MB** | 235 s | 450 s |

**Las 3 madres × 5.000 variantes que pediste**: 39 s de fabricación, **210 MB**, y entre **12 min**
(un mercado) y **22 min** (dos) de retest. Es barato. El cuello de botella del encargo no era este.

## 4 · Memoria

- **El JVM de SQX es toda la memoria del sistema.** Pico medido **21,1 GB** con dos mercados, ~12 GB
  con uno. Python nunca pasa de **296 MB**, y ese pico es la fabricación (el `.sqx` padre se
  mantiene en memoria para no releerlo 2.000 veces).
- El heap del custodio está en **48 GB** (`sqcli.config -Xmx48g`) y `coreUsage 48`. Con un mercado
  va sobradísimo; con cuatro empezaría a apretar.
- ⚠️ **El maestro declara `coreUsage -1`**, es decir los 96 núcleos. Si el maestro está generando a
  la vez que corre esto, se pelean por la CPU. No lo he tocado — es tu configuración — pero es un
  factor que no aparece en ninguna medición porque el maestro estuvo apagado todo el rato.

## 5 · Disco

`AlgoData`: **7,27 GB de un presupuesto de 90**. Por ramas, lo que importa:

| rama | hoy | presupuesto | comentario |
|---|---:|---:|---|
| `snapshots` | 4,78 GB | 20 GB | un snapshot del maestro son ~4,5 GB |
| `raw` | 1,96 GB | 40 GB | los exports fechados |
| `bars` | 0,30 GB | 3 GB | |
| `variants` | ~0 | 15 GB | aquí caen los lotes fabricados |
| `pipeline` | 0,03 GB | 1 GB | **los registros, que sobreviven al borrado** |

El borrado con red funciona y está medido: `cleanup --apply` liberó **70,0 MB** de variantes y dejó
**520 KB** de registro. Con 100 madres a 5.000 variantes serían 7 GB de pico si no se borrara entre
medias; borrando, el residuo permanente es **50 MB**.

## 6 · Tokens de Claude

Esta sesión, desde tu encargo hasta este informe: **~105.000 tokens**. El reparto aproximado,
porque es lo que te sirve para decidir:

| en qué | share | por qué |
|---|---:|---|
| depurar por qué SQX no hacía nada | **~55 %** | dos comportamientos silenciosos, sin error en ningún log |
| escribir código y documentación | ~30 % | `cost.py`, `harness.py`, la página del manual |
| ejecutar y medir | ~15 % | esperas y sondeos |

**La lección de coste es esa primera fila.** Un fallo de SQX que no escribe nada en ningún log
cuesta entre diez y cincuenta veces más que escribir el código que lo usa. Cada uno de esos
comportamientos está ahora en `knowhow/03-driving-sqx.md` con su medición, y ese es el único motivo
por el que la próxima vez será barato.

Lo que abarata tokens, por orden de efecto:

1. **Sondear con un comando, no con un bucle de espera.** Los bucles de espera en segundo plano
   generan mucha salida y poca información.
2. **Probar el caso limpio primero.** Perdí un buen rato leyendo un `optimizationProfile.bin` que
   venía dentro del fichero desde el maestro. Sobre una variante fabricada, que no tiene ese
   miembro, la pregunta se responde a la primera.
3. **Que el fallo hable.** `collect.py` aborta diciendo *«los controles devuelven el MISMO
   resultado»*. Eso son cero tokens de depuración la próxima vez.

---

## 7 · Las tres optimizaciones que yo haría, por rentabilidad

1. **Resolver o apagar el cross-check de mercado.** Cuesta el 48 % del tiempo total y sus resultados
   no se leen. Apagarlo deja la corrida en ~100 s.
2. **Lotear el retest.** `ran` carga las 2.000, corre y exporta en bloque. Con 5.000 el JVM pasaría
   de 21 GB; por lotes de 2.000 el techo de memoria deja de depender del tamaño del lote.
3. **No refabricar para reanudar.** Hoy `build` es de 5-13 s y no duele, pero con el diseño completo
   y varios mercados el orden de magnitud cambia.

## 8 · La medición que falta, y por qué

**No pude medir el coste de un SPP nuevo**, que era parte del encargo. El SPP se ejecuta en el
custodio — el log lo demuestra, una línea por parámetro — pero **no deja nada**: ni
`optimizationProfile.bin` en la estrategia, ni registros en el databank de salida, con o sin
condiciones de aceptación. El retest normal en el mismo arnés sí funciona, que es el control.

Medido y escrito en `knowhow/03-driving-sqx.md`. Mientras eso no se resuelva, una rejilla de diseño
solo puede salir de un SPP que **haya corrido el maestro**, y por tanto las dos SPP por madre que
pediste no se pueden hacer desde aquí.
