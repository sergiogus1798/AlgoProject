# docs/AgentPDFs — raw-numbers specs written to feed a future reasoning agent

Each file here is a from-the-source-code specification of one module's output: every number it
produces, its exact formula, and nothing else — no conclusions, no thresholds presented as answers.
The point is to hand a future Claude instance (or any other reasoning agent) the raw material to
derive its own rules, without inheriting this project's current, partly provisional, judgement calls.

Conventions:

- One `.md` + one `.pdf` per document, same stem, dated `<topic>-YYYY-MM-DD.{md,pdf}`. The date is
  when it was generated, not when the module was last touched — regenerate and re-date after any
  change that would make a formula or a default value here wrong.
- The current system's own thresholds (`gates.py`, `scoring.py`, or equivalent), when included at
  all, live in their own clearly labelled appendix — never mixed into the raw definitions.
- Any empirical numbers (percentiles observed on a real databank, say) are stamped with exactly
  which databank, which export date, and which config they came from.
- **The `.pdf` also carries the visual side the `.md` alone cannot**: real chart screenshots (a
  histogram, a cone, an overlay — whatever figure types the module draws), generated from an actual
  strategy, named in the text and never invented, plus a full real report rendered end to end and
  merged in as a closing appendix — so an agent that can only read gets the same picture a human
  opening the HTML would see. The `.md` keeps the images as `![](file.png)` references to files that
  live only in the temp scratchpad that built it; open the `.pdf` to see them.

## And a fourth kind: outbound briefs

`capabilities-2026-09-24` is not a spec, an audit or a dossier: it is a **briefing written to be
handed out of this project**, to a reasoning agent that is helping design new tests and has never
seen the code. It says what the toolchain can do, inventories every analysis already implemented or
commissioned, and — the part that earns its length — lists the hard constraints and the measured
facts that make most obvious proposals unbuildable here.

Two conventions of its own:

- **It is in English, deliberately.** Its reader is an agent working in English, not the owner. It
  is the one file in this folder that is not to be translated.
- **It is an inventory, so it goes stale.** Re-date and regenerate it whenever a module is added or
  a commission is fulfilled — a brief that under-reports what exists invites duplicate work, which
  is the exact failure it was written to prevent.

`catalogo-para-la-ui-2026-09-25` is the second of this kind and the counter-example to the first
convention: it is **in Spanish**, because it briefs an agent helping design the desktop application,
whose labels and whose conversation are in Spanish. So the rule is not "outbound means English" — it
is **the language of the conversation the document is walking into**, and each one says which it
chose and why on its last page.

`paneles-flask-inventario-2026-09-25` is the third, also in Spanish and for the same reader: what
the three Flask panels of `strategies/*/explorer/` offer — every tab, selector, knob and drawing —
so the window's «Estudios» zone reproduces their depth instead of thinning it. Its last section is
the ten-point contract that zone has to keep.

Regenerate the PDF with the manual's own stylesheet; there is no committed tool for a single
dossier, and `tools/manual.py` holds the `STYLE` any ad-hoc renderer should import.

## A second kind of document lives here too

`montecarlo-rendimiento-2026-09-20` is not a raw-numbers spec: it is a **performance and memory
audit** of a module, written for the owner rather than for a future agent. It keeps the same
conventions — dated `.md` + `.pdf` pair, figures generated from real measurements and never
invented, every empirical number stamped with the databank and export it came from — but it does
carry conclusions and recommendations, which the specs above deliberately do not. Keep the two
kinds distinguishable by their stem: `<module>-` for a spec, `<module>-rendimiento-` for an audit.

## And a third kind: design dossiers

`plataforma-unificada-2026-09-20` is neither a raw-numbers spec nor a performance audit: it is a
**feasibility study and design dossier**, written for the owner and for whoever picks the question
up later. It records a question that was investigated but not acted on — here, whether SQX and
AlgoProject can be wrapped in one application — together with the evidence found, the architecture
proposed, the effort estimated and, explicitly, what was never tested.

Its conventions are the same (dated `.md` + `.pdf`, every empirical claim stamped with the command
that produced it), plus two of its own:

- **A closing appendix lists what was NOT verified.** A dossier that reads as certain is worse than
  no dossier, because it gets built on.
- **Findings that outlive the document go to `knowhow/` in the same task.** The dossier keeps the
  narrative and the plan; `knowhow/` keeps the facts. Where the two disagree, `knowhow/` wins, and
  the dossier says so.

`protocolo-robustez-2026-09-21` is the second dossier, and differs from the first in one way worth
knowing: **it is being acted on.** It carries the implementation plan for the XAUUSD robustness
protocol, with the lots already built marked as such and the rest specified in enough detail for
several agents to work in parallel against the contracts in its §2. Its status table is the
authoritative answer to "what is left", and it is updated as lots land.

`plan-ejecucion-2026-09-21` is the third dossier, and the first written to be **dispatched rather
than read**. It splits the whole remaining programme into two lanes — one agent organising the three
SQX installations, several agents writing Python — with every task a self-contained brief: what to
read, what to do, how to verify it, what to hand back. Its §7 supersedes the status table and the
blockers section of `protocolo-robustez-2026-09-21`; the rest of that dossier stands. It deliberately
excludes the desktop shell.

Stems, then: `<module>-` for a spec, `<module>-rendimiento-` for an audit, `<topic>-` for a dossier.

Not covered by `tools/checks.py`: these are hand-triggered deliverables, not generated on every run.
