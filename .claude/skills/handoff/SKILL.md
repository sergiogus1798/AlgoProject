---
name: handoff
description: Write the prompt that hands this session's unfinished work to a fresh session — self-contained, in Spanish, with the state, the exact next step, the model to use and what not to touch. Use when the owner asks for a prompt for the next agent, instance or session, says the context is full or he is running out of tokens, or asks to continue this in another chat.
---

# /handoff

A fresh session knows nothing of this one. The prompt is its whole context, so it must be cheap
to read and leave nothing to re-derive — but it points at files, it does not copy them.

1. **Settle the tree first.** List the files this session changed and ask **¿Quieres hacer el
   commit?** (rule 12). Uncommitted work is named in the prompt as uncommitted, file by file.
2. **Put the durable part where it lives**, not in the prompt: a finding → `/doc`; an open
   problem → `OPEN.md`; a multi-session plan → its encargo's state table (`/encargo`). The
   prompt then links them.
3. **Write the prompt, in Spanish**, with exactly these parts:

   ```markdown
   # Continúa: <tarea en una línea>
   **Modelo:** <sonnet si es mecánico (regla 17) · opus si hay que diseñar, decidir o hacer estadística>
   ## Objetivo            lo que pidió el dueño, con sus palabras y la fecha
   ## Hecho               qué está terminado y verificado — con fichero:línea o la orden que lo prueba
   ## Siguiente paso      la primera orden exacta que hay que ejecutar, y las que siguen
   ## Decisiones del dueño  las ya tomadas (no se reabren) y las que hay que preguntarle (regla 11)
   ## No toques           workers ocupados y por quién, ficheros de otras sesiones, lo que el dueño vetó
   ## Lee sólo esto       3-6 rutas con el tramo: `OPEN.md` §N, la skill, el encargo, la ficha
   ## Cómo cierras        verificación, lista de ficheros cambiados, «¿Quieres hacer el commit?»
   ```

   - State of SQX is stated, not guessed: run `.claude/skills/sqx-wait/preflight.sh` and paste
     which worker is up, its lock and the running project. A run in flight gets its wait command.
   - Token budget and parallel sessions are named when the owner gave them.
   - No transcript, no history of what was tried and dropped — only what changes the next step.
     Under ~60 lines.
4. **Deliver:** save it to `scratch/handoff-<tema>-<YYYY-MM-DD>.md` (throwaway, not in git) and
   print it in the reply inside one code block, ready to paste.

Anything you could not verify before the handoff goes under «Siguiente paso» as the first thing to
check, never under «Hecho».
