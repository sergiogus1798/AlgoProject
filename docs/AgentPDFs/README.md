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

Not covered by `tools/checks.py`: these are hand-triggered deliverables, not generated on every run.
