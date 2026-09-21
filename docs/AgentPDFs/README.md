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

Stems, then: `<module>-` for a spec, `<module>-rendimiento-` for an audit, `<topic>-` for a dossier.

Not covered by `tools/checks.py`: these are hand-triggered deliverables, not generated on every run.
