# 12 · Tests estructurales: ablación, inversión y el mono dentro de SQX — encargo autocontenido

**Tu oficio:** Python que reescribe XML de estrategias, y una corrida en el custodio para
comprobar que lo que escribiste carga y opera. **No toques el maestro.**

Lee `CODESTYLE.md` · `sqx/variants/build/README.md` · `knowhow/sqx-format/` §formatos ·
`CLAUDE.md` reglas duras 2, 3, 4 y 10. No necesitas más.

Sale del PDF del dueño `PARAMETER_SPACE_TESTS.pdf`, sección D (D1, D2, D3), revisado contra el
repositorio el 2026-09-24. Los tres comparten **una sola capacidad que hoy no existe**: editar la
*lógica* de una estrategia, no sus valores.

---

**Dónde va** (refactorización del 25-09, `docs/MAPA-DE-CARPETAS.md`): la fábrica y la corrida en `sqx/structural/` (§2); la lectura de las ablaciones — qué bloque sostiene el filo — en `studies/readings/structure/` (ya creada con su `README.md`). Forma de
módulo: `studies/CLAUDE.md`; contrato del resultado: `core/study/CONTRACT.md`.

## 0 · Por qué no está hecho ya

`sqx/variants/build/rewrite.py` sabe escribir una variante, pero sólo toca
`<variable><id>NAME</id>…<value>N</value>`, y `set_values` revienta a propósito si el nombre no es
una variable de la estrategia. Eso cubre todo el espacio de parámetros y nada del espacio de reglas.

**Ya está hecha la mitad barata del D1**, y no necesita SQX: `engines/nulls/filter.py` compara un filtro
contra quitar al azar la misma fracción de operaciones (p empírica, estadísticos **por operación**
porque un filtro cambia el número de trades). Lo que le falta es la lista de operaciones *sin* el
filtro, y eso es lo que fabricas aquí.

## 1 · La ruta ya está investigada — no la vuelvas a buscar

🔬 Medido el 2026-09-24 sobre `P00000.sqx` de `Strategy_17-9-39`. Dentro de
`strategy_Portfolio.xml`:

```xml
<Rules><Events><Event key="OnBarUpdate">
  <Rule name="Trading signals" type="Signal" …>
    <signal variable="33333333-1111-1111-3333-333333333333">   <!-- entrada -->
      <Item key="AND">
        <Block><Item category="DirectionalMomentum_user" key="CBlock_SqueezeMomentumPos"
                     oppositeBlockKey="CBlock_SqueezeMomentumNeg" …/></Block>
        <Block><Item key="DICrossUp" name="DI+ crosses above DI-" …/></Block>
      </Item>
    </signal>
    <signal variable="33333333-1111-2222-3333-333333333333">   <!-- salida -->
  </Rule>
  <Rule name="Long entry" type="IfThen">  … BooleanVariable → EnterAtMarket
```

De ahí salen las tres decisiones de diseño, y son más simples de lo que el PDF supone:

**D1 — la ablación es borrar un `<Block>`, no inyectar un TRUE.** Un `<Item key="AND">` con un
término menos *es* la condición neutralizada; con un `OR`, borrar el bloque es el FALSE que pide el
PDF. No hace falta ningún bloque «siempre cierto» en el vocabulario, que era el bloqueo que se temía.

**D2 — hay dos inversiones posibles y no son la misma.** SQX declara `oppositeBlockKey` en los
custom blocks, así que se puede invertir *la condición*; y la regla `IfThen` se puede cambiar de
`Long entry` a `Short entry`, que invierte *la dirección de la orden* dejando las entradas donde
están. **El PDF pide la segunda** —mismos instantes de entrada, dirección opuesta—, así que ésa es
la que se construye. La primera, si la construyes, es otro test y se llama de otra manera.

⚠️ Y una ventaja de este corpus: las estrategias XAUUSD generadas **no llevan stop, ni target, ni
trailing** (`studies/CLAUDE.md`). La advertencia del PDF sobre asimetría SL/TP no aplica todavía
aquí, así que la inversión es casi espejo exacto. Escríbelo en el informe, porque dejará de ser
cierto en cuanto una población lleve stops.

**D3 — el mono dentro de SQX es el único de los tres que puede resultar imposible.** Necesita un
hash entero sembrado de `(timestamp, seed)` dentro de un custom block, y el PDF avisa —con razón—
contra los hashes basados en `sin()`, que son estadísticamente malos. **Primero mira qué hay**:
`python3 -m sqx.inspect.vocabulary` lista lo que este install puede componer. Si no hay operaciones
enteras (XOR, desplazamientos, módulo sobre enteros de 64 bits), **párate y dilo**: el módulo
`studies/readings/monkey/` ya responde esa pregunta fuera de SQX con la reconciliación medida (`open-open` a
0.999985), y forzar un generador malo dentro de SQX es peor que no tenerlo.

## 2 · Lo que construyes

Carpeta nueva `sqx/structural/`, forma de la casa (decide / escribe / lee de vuelta, como
`sqx/variants/`). Reutiliza `rewrite.SHAPES`, el sello `variant_id` y el borrado de `<Fingerprint>`:
esas tres trampas ya están resueltas y volver a pisarlas sería gratuito.

| entregable | qué es |
|---|---|
| **la fábrica** | una madre + qué bloque se quita (o la dirección invertida) → un `.sqx` por ablación, con su manifiesto |
| **la corrida** | reutiliza `sqx.variants.execute` sobre el custodio; **un trabajo y `bin/sqx-worker.sh --role custodian stop`** |
| **la lectura** | ΔM por condición, en expectativa **por operación** y Sharpe, nunca en beneficio total |
| **el enlace con `engines/nulls/filter.py`** | con los trades de la ablación y los de la madre, el contraste contra filtro aleatorio |

## 3 · Verificación — sin esto no has entregado nada

1. **Que carga y opera.** Una ablación cargada en el custodio tiene que devolver un backtest con un
   número de operaciones **distinto** al de la madre y coherente con haber quitado un filtro (más
   operaciones al quitar un filtro de entrada). Si vuelve con las mismas operaciones exactas, SQX
   ignoró tu edición y todo lo demás es decoración: es el mismo fallo que `OPEN.md` §9.
2. **El control de identidad.** La madre reconstruida por tu fábrica **sin** quitar nada tiene que
   reproducir el backtest de la madre. Es el canario del módulo.
3. **La inversión.** Con este corpus sin stops, el P&L bruto invertido debe salir ≈ −P&L bruto
   original. Si sale positivo, o la inversión no se aplicó o el edge vive en la salida y no en la
   entrada — y distinguir esas dos cosas es el trabajo.
4. `python3 tools/depmap.py && python3 tools/checks.py` → 0 problemas.

## 4 · Cómo cierras

- Página de manual (regla dura 8), en español, con salida real.
- **Escribe en `knowhow/sqx-format/`** lo que midas sobre si SQX acepta un `AND` con un solo
  bloque y si respeta una regla `IfThen` reescrita. Son dos hechos que hoy nadie tiene, y el segundo
  decide si D2 es viable.
- Si D3 resulta imposible por el vocabulario, **bórralo del encargo y escribe por qué** en
  `knowhow/conditions/`. Un «no se puede, y éste es el motivo» cierra la pregunta para siempre;
  dejarla abierta hace que se vuelva a investigar cada seis meses.

## 5 · La regla que manda sobre todo esto

Diagnóstico, nunca selección. Una ablación que mejora el resultado **no** es una estrategia mejor
que haya que adoptar: es una condición que no aportaba. Quitarla es decisión del dueño, se anota en
el ledger (encargo 8) y se revalida aparte.
