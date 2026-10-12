# Monthly source review before delivery

Use this procedure after drafting and before presenting a final review or writing
`YYYY-MM.summary.md`. It applies to conversation-only and vault runs alike.
The template supplies a layout; source evidence determines which fields exist.
An automated score or a writer's own claim that it checked the facts is not a
completed source review.

## 1. Fix the evidence and draft versions

Keep the selected month, reporting groups, project slugs, effective raw entries,
period-end states and scoped conversation evidence available together. Keep
editorial context separate. Use the preparation helper's coverage dates; count
records separately from distinct dates. Leave unmeasured coverage unknown.

Before writing prose, note the material facts that must survive for each project:
its actual change, verification scope, month-end state, unresolved conflicts and
explicitly confirmed arrangements. This prevents a repair from passing by
removing a meaningful project's result. Preserve the draft as version 1.

For file-backed runs, retain draft and source snapshots in the already permitted
temporary workspace and record their SHA-256 hashes. For conversation-only or
local runs, retain the exact versions in working context; create no files solely
for this procedure. Changed evidence or draft text invalidates its prior review.

## 2. Perform a separate source-first review

Use a separate reviewing agent when available, giving it the complete scoped
sources and draft, without the writer's reasoning or a previous pass verdict.
The delivery agent must inspect the cited evidence itself before accepting that
review. Otherwise perform a distinct source-first pass yourself and record
`same_agent_source_pass`; do not describe it as an independent reviewer.
Do not require the user to perform this technical check.

Read the original source material again, then inspect every claim-bearing part
of the draft: opening, prose, lists, tables, evidence appendix and execution
metadata. For each substantive claim, identify its source location and check:

- **Ownership:** reporting group and project match. Apply a shared status to
  multiple projects only when each project's sources support it.
- **Lifecycle:** implementation, merge, deployment and acceptance are different
  states. Use explicit period-end state and applicable corrections. Preserve
  unknown status as unknown.
- **Verification:** keep sample, environment, metric and comparison conditions
  attached to the result. Preserve real scoped improvements; extrapolation to
  production, reproducibility or business value needs its own evidence.
- **Knowledge:** distinguish absence of supplied data, absence of a record,
  confirmed absence of an action, and an unresolved question. Describe what the
  source establishes. A missing result does not establish that no test occurred.
- **Arrangements:** distinguish confirmed next steps, conditional decisions and
  explicitly labeled suggestions. Missing dates or metrics alone do not create
  a task, deadline, resource request or delivery gate.
- **Completeness:** retain material non-headline projects and real scoped
  completion. An unrelated unmeasured business outcome does not reopen a
  completed document change.

Record findings against the exact draft version using source locations and
report locations. For a paragraph or table with several claims, check each one;
a supported sentence does not validate its neighbors. Compare repeated claims
across the whole report. A footnote cannot repair an overstated opening.

Keep a compact review record in working context:

- source version/hash and draft version/hash;
- reviewer mode (`separate_agent_plus_delivery_check` or `same_agent_source_pass`);
- checked report sections and material project facts;
- findings: report location, source location, supported/unsupported/uncertain,
  and the concrete discrepancy;
- revision count and final disposition: `source_reviewed` or `draft_unresolved`.

This is an agent's source-grounding judgment, not proof that the underlying work
was independently tested. Do not upgrade evidence grades because review passed.

## 3. Correct once, then review the complete new version

If findings are correctable from existing evidence, make at most one consolidated
revision in this invocation. Count every rewriting intervention, whether by an
automated repair, another agent or yourself, against this one-revision budget.
Retain version 1 and record who changed what. Resolve the issue in every occurrence
while preserving the informative opening and material supported results.

Reread the complete revised report against the sources, including unchanged
sections. Do not inherit passes from the previous version. New scope mistakes
or unresolved findings leave the report at `draft_unresolved`; do not keep
retrying to obtain a pass. A later user-requested revision is a separate run.

## 4. Deliver only the reviewed version

Mark `source_reviewed` only when every substantive claim is supported or accurately
states source uncertainty, required material facts remain, and no review finding
is unresolved. Source uncertainty may legitimately remain in a final report;
uncertainty about whether the report accurately reflects its sources may not.

Apply BOTH this disposition and the existing report-context write policy:

- `source_reviewed` with complete, write-permitted context: present the final
  report or save that exact version to the normal review path. Existing outputs
  still require the established update permission; retain scope separation.
- Partial or blocked context: retain its draft/blocked status even if the visible
  claims passed. Follow the existing explicit-save and no-write rules.
- `draft_unresolved`: return a clearly labeled conversation draft with concise
  unresolved findings. Preserve any existing final report. Save a separate
  `.draft.md` only if the user explicitly asks AND the context permits draft
  writes; never substitute it for `.summary.md`.
- Local/no-vault mode: conversation only for every disposition.

Report the actual disposition, reviewer mode and revision count alongside the
usual execution metadata. Keep the detailed review working notes out of the
management narrative. Any further factual edit requires another complete review
before delivery; an earlier pass does not attach to new text.
