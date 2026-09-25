## 46. Knowhow en fichas — un hecho por archivo, para gastar pocos tokens al consultarlo

### Qué pregunta responde

Dónde está escrito un hecho que ya costó descubrir (cómo se comporta SQX, un formato, un coste, una
lección estadística), y cómo encontrarlo **leyendo lo mínimo**. Desde el 2026-09-25 el `knowhow/` no
son nueve archivos largos, sino 135 fichas pequeñas en 12 carpetas. Cada ficha cuenta un solo hecho,
con la regla arriba y la evidencia debajo.

### Cuándo lo usas, y cuándo no

- Lo usas cada vez que una sesión (tuya o de un agente) necesita un hecho del knowhow, y cada vez
  que alguien descubre uno nuevo y tiene que escribirlo.
- `tools/knowhowmap.py` se corre después de crear, renombrar o cambiar la pregunta `q:` de una ficha.
- **No sirve** para lo que está roto o pendiente (eso va en `OPEN.md`), ni para cómo se usa un
  comando (eso es este manual).

### Antes de empezar

Nada. No toca SQX ni datos: solo lee y escribe archivos markdown dentro de `knowhow/`.

### Cómo se ejecuta

Para **consultar** un hecho, en este orden (cada paso cuesta menos que el siguiente):

```bash
grep -rh '^q:' knowhow/costs/ | grep -i swap           # 1. qué ficha responde
sed '/^## Evidence/q' knowhow/costs/swap-types.md      # 2. solo la regla
cat knowhow/costs/swap-types.md                        # 3. la evidencia, si hace falta discutirla
```

Si no sabes en qué carpeta está, `grep -ril '<palabra>' knowhow/`. La lista de carpetas y el
formato de ficha están en `knowhow/INDEX.md`.

Para **regenerar los índices** de cada carpeta después de tocar fichas:

```bash
python3 tools/knowhowmap.py
```

No tiene flags. Tarda menos de un segundo y no toca SQX.

### Qué produce

Reescribe `knowhow/<carpeta>/INDEX.md` en cada una de las 12 carpetas: una línea por ficha con su
nombre y la pregunta que responde. **Sobrescribe** esos índices enteros; no se editan a mano.

### Cómo se lee el resultado

La consulta del paso 1 devuelve la línea `q:` de la ficha que responde:

```
q: SQX swap types points percent money formula; percent swap annual or nightly 360; convert points to percent; triple swap day per feed WEDNESDAY FRIDAY; tripleSwapOn override asset file
```

El paso 2 devuelve la cabecera: la pregunta, la etiqueta (🔬 medido · 📓 leído en logs · 🤔
inferido), la fecha y la regla.

```
# `percent` swap is an ANNUAL rate (÷100 ÷360); the triple-swap day is per feed
- One night × nights held (3 on the triple day). `pct_annual = points × tick_size × 36000 / reference_price` ...
- `tripleSwapOn`: WEDNESDAY for FX, XAUUSD, XAGUSD; FRIDAY for BRENT, DJ30, NIKKEI225, USA500, USATEC ...
```

`knowhowmap.py` imprime cuántas fichas tiene cada carpeta:

```
authoring 9, columns 4, conditions 8, costs 10, databanks 8, eng 11, export 15, locations 4, perf 10, research 21, sqx-drive 17, sqx-format 18
```

### Un ejemplo completo

Lo que cuesta responder diez preguntas reales, antes (leyendo el archivo entero, como decía el
índice antiguo) y después (grep de `q:` y cabecera de la ficha), medido el 2026-09-25:

| pregunta | antes | después | × |
|---|---:|---:|---:|
| ¿`startOnlyTask` funciona headless? | ~14.600 tok | ~260 tok | 57× |
| ¿Cuántos núcleos tiene el servidor? | ~27.800 tok | ~240 tok | 118× |
| ¿Qué columnas trae `orderstocsv`? | ~13.100 tok | ~240 tok | 54× |
| ¿Un sync borra `.sqx`? | ~4.000 tok | ~440 tok | 9× |
| ¿Cómo se mide la memoria de un pool `fork`? | ~27.800 tok | ~440 tok | 64× |
| ¿Dónde viven los costes de una tarea? | ~14.600 tok | ~350 tok | 42× |
| ¿Qué ventana seleccionó una estrategia? | ~5.800 tok | ~270 tok | 22× |
| ¿Cómo se identifica una estrategia? | ~13.900 tok | ~260 tok | 53× |
| ¿Qué tipos de swap hay? | ~4.200 tok | ~260 tok | 16× |
| ¿Por qué `Param Count` sale mal? | ~2.900 tok | ~230 tok | 13× |
| **total** | **~128.600 tok** | **~3.000 tok** | **43×** |

### Qué NO te dice

- Que un hecho siga siendo verdad hoy. La fecha de la ficha dice cuándo se midió, y una ficha 🤔
  sigue siendo una suposición.
- Todo lo que se sabe de un tema. Si una ficha tiene `see:`, los hechos vecinos están en las
  fichas que nombra.

### Si algo falla

`python3 tools/checks.py` revisa tres cosas del knowhow:

- **`knowhow cards`**: una ficha sin `q:` o sin `tag:`, con más de 12 líneas antes de
  `## Evidence`, con un `see:` que no apunta a ninguna ficha, o de más de 6 KB. La solución es
  recortarla o partirla en dos fichas.
- **`knowhow links`**: algún archivo del repo cita un `knowhow/...` que no existe. Pasa al renombrar
  o borrar una ficha: corrige la cita.
- **`knowhow indexes`**: un `INDEX.md` de carpeta no coincide con sus fichas. Corre
  `python3 tools/knowhowmap.py`.

La regla de escritura: **se edita la ficha que existe, nunca se añade al final**. Si un hecho cambia,
se reescribe la regla y se actualiza `date:`; git guarda la versión anterior.
