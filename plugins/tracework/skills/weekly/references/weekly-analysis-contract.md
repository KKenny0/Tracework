# Weekly Analysis Contract

Use after scope partition and evidence gathering for **brief** and **slides**.
Do not use for **quick**. Analysis runs in the main dialog.

- `brief`: complete the goal loop, then apply **Brief Projection**.
- `slides`: share scope, goal lanes, prior commitments, coverage, work-stream
  state transitions, and truth boundaries with Brief, then branch before
  audience-specific ranking. Use `weekly-slides-contract.md` for **Result Selection**, reopen only selected
  sources, and write one audience-facing PPT-ready Markdown Deck. Run
  **Cognitive Task Decomposition** only when a complex merge/split decision
  requires it. Emit an editable template-native PPTX only when explicitly
  requested and supported.

Return one analysis object per reporting group:

```json
{
  "reporting_group": "work",
  "goal_lanes": [],
  "period_judgment": {
    "original_direction": "",
    "actual_change": "",
    "variance": "",
    "current_decision": "",
    "statement": ""
  },
  "prior_commitment_accounting": [],
  "material_changes": [],
  "unplanned_material": [],
  "portfolio": [],
  "next_commitments": [],
  "decisions_or_support_needed": [],
  "evidence_index": []
}
```

## Goal Resolution

Resolve goals before selecting changes:

1. explicit current-request goal;
2. confirmed prior-Weekly commitment;
3. explicit milestone, plan, or project-goal artifact;
4. a raw entry's recorded local objective or constraint;
5. bounded inference from raw motivation;
6. unknown.

```json
{
  "id": "goal-1",
  "statement": "",
  "source": {
    "kind": "current_request | previous_weekly | goal_artifact | raw_inference | unknown",
    "reference": ""
  },
  "confidence": "confirmed | inferred | unknown",
  "closure_criterion": "",
  "status": "met | advanced | blocked | replanned | not_started",
  "commitment_state": "confirmed | proposed"
}
```

An empty source is `unknown`, not permission to invent a Why. Goals inferred
after work remain `inferred`. An agent recommendation from the prior report
remains `proposed`. Keep unrelated goal lanes separate even when they share a
reporting group. Actions, commits, modules, and effort volume are evidence of
work, not goal sources. If an unknown goal would change selection, grouping,
the period judgment, or next priority, ask once; otherwise continue with the
unknown boundary and do not claim goal progress.

## Prior Commitment Accounting

Account for every prior-period item:

```json
{
  "statement": "",
  "commitment_state": "confirmed | proposed",
  "status": "met | advanced | blocked | replanned | not_started",
  "goal_id": "goal-1",
  "reason": "",
  "evidence_refs": []
}
```

No prior item may disappear. For replanned work, retain the former direction,
evidence trigger, reason, and replacement direction. A rejected suggestion is
not replanned work: retain its proposed origin and recorded rejection without
forcing a goal-status value. Leave unsupported analysis statuses unset; the
absence of a completion record establishes neither `not_started` nor `blocked`.

## Work Streams and Material Changes

First merge entries that describe one state transition. Do not split by commit,
module, day, or archetype when the management meaning is shared.

```json
{
  "id": "temporary-analysis-id",
  "goal_ids": [],
  "project": "Project Name",
  "title": "",
  "status": "done | ongoing | risk | decision",
  "closure_type": "delivery | decision | risk | learning",
  "starting_constraint": "",
  "decisive_move": "",
  "end_state": "",
  "management_meaning": "",
  "remaining_gate": "",
  "closure_criterion": "",
  "management_relevance": "high | medium | low",
  "claim_kind": "outcome | progress | activity",
  "evidence_grade": "verified | recorded | limited",
  "decisions": [],
  "risks": [],
  "source_refs": []
}
```

For Brief, rank by observable end-state significance, management relevance,
evidence strength, and effect on the next decision. For Slides, preserve the
same state transitions and truth boundaries but postpone audience-specific
ranking to Result Selection; do not first produce the Brief ranking. Do not
force a headline count.

Each selected material change keeps a stable id and includes:

```json
{
  "id": "stable-result-id",
  "goal_ids": [],
  "headline": "observable state-change claim",
  "supporting_stream_ids": [],
  "closure_type": "delivery | decision | risk | learning",
  "starting_constraint": "",
  "decisive_move": "",
  "end_state": "",
  "management_meaning": "",
  "remaining_gate": "",
  "closure_criterion": "",
  "evidence_grade": "verified | recorded | limited",
  "evidence_refs": [],
  "metric_evidence": [],
  "state_transition": null,
  "solution_logic": null,
  "result_maturity": {
    "mechanism_complete": "yes | partial | no | not_applicable",
    "effect_validated": "yes | partial | no | not_applicable",
    "production_accepted": "yes | partial | no | not_applicable"
  },
  "department_value": "delivery_speed | quality | production_risk | cost | collaboration | iteration_capacity | null",
  "variance": {
    "kind": "none | blocked | replanned | unplanned",
    "prior_direction": "",
    "trigger": "",
    "reason": "",
    "new_direction": ""
  }
}
```

An outcome requires a deliverable, observable state, recorded effect, or
demonstrably removed risk. Expected impact stays prospective. Every material
change has a goal or `variance.kind: unplanned`; otherwise keep it in portfolio.

## Brief Projection

**Brief only.** Do not create another analysis object. Keep in the body only
what is necessary to reconstruct:

```text
goal state
actual change
material variance
decision or support needed
next commitment
confidence boundary
```

For every candidate block, ask whether removing it changes judgment, action, or
confidence. Keep it only when yes.

Body admission:

- changes a goal status;
- explains a material block, replan, or displacement;
- changes a decision, support request, or resource implication;
- defines a next commitment and closure criterion;
- qualifies a claim as limited, conflicting, or expected-only.

Route complete prior-item accounting, remaining meaningful streams, compact
claim evidence, provenance, coverage, and scope boundaries to the appendix. Use
one fact in one expanded location. Do not use a fixed length or item count.

## Evidence Candidates

Use numeric evidence only when metric, unit, sample, method, and comparison
conditions are stable. Recompute ordering and deltas. If values conflict or
samples are incomparable, expose the conflict and do not recommend a chart.
Never infer a missing baseline or target.

A material state transition may use:

```json
{
  "before": "",
  "intervention": "",
  "after": "",
  "remaining_gate": "",
  "evidence_refs": []
}
```

When a mechanism visual is actually selected, `solution_logic` may preserve the
supported trigger, actors, main flow, material branches, fallbacks, output,
invariants, remaining boundary, diagram route, and evidence refs. It is an
optional visual payload, not a requirement for every result and never proof
that the solution worked.

### Change Explanation Card Projection

**Optional for Brief and Slides.** This is a projection of one existing material
change, not another analysis object. Reuse its conclusion, `state_transition`,
`solution_logic`, management meaning, evidence grade, and evidence refs. In
Slides, apply it only after Result Selection as one semantic composition; it
does not rank results or create slide candidates. Do not add a mode, schema,
configuration field, or rendering dependency.

Admit a card only when all of these hold:

- removing the problem/solution explanation or comparison changes judgment,
  action, or confidence;
- `before` and `after` describe the same object on the same comparison axis;
- both states and the problem are supported by current-period evidence;
- the intervention was actually selected or performed; and
- the result is complex enough that a visual is clearer than compact prose.

Project the existing fields as follows:

| Card role | Existing source |
|---|---|
| conclusion | result conclusion |
| Before / After | `state_transition.before` / `state_transition.after`, grounded by `starting_constraint` / `end_state` |
| problem | `starting_constraint`, plus an evidenced root cause or trigger when present |
| solution | `decisive_move` and `state_transition.intervention`; optional `solution_logic` supplies mechanism detail only |
| formed change | `end_state` plus `management_meaning` |
| evidence and boundary | evidence grade, `state_transition.evidence_refs`, and `state_transition.remaining_gate` |

Truth rules:

- **Problem** starts from `starting_constraint` and states only an evidenced root
  cause or trigger, not a story inferred from commit shape or the eventual
  solution.
- **Solution** starts from `decisive_move` and `state_transition.intervention`;
  `solution_logic` may only add supported mechanism detail. A proposed design is
  visibly labeled `target / not implemented` and stays outside After.
- **After** is the current actual state at the weekly cutoff. It is never a
  target design, expected effect, or implementation used as proof of outcome.
- **Formed change** distinguishes implementation, tested behavior, observed
  effect, and production acceptance. Keep `remaining_gate` adjacent.
- A visual has one proof responsibility and never proves effectiveness by
  itself.

Choose the lightest representation that fits the evidence:

| Evidence shape | Representation |
|---|---|
| comparable state or attributes | Markdown Before/After comparison table |
| deletion, replacement, or contraction | `diff` fence |
| structure, call chain, or data flow | one Mermaid diagram with Before and After subgraphs |
| one case moving through changed steps | aligned `text` trace |
| two or three sentences are clearer | text only |

Use at most one primary visual per card. If the axes drift, the problem lacks
support, After is prospective, or deletion leaves understanding and action
unchanged, downgrade to the compact result or omit the card. Portfolio rows
never become cards merely to improve visual variety.

## Portfolio, Judgment, and Commitments

Keep every meaningful non-headline stream visible:

```json
{
  "stream_id": "",
  "project": "",
  "status": "",
  "bounded_change": "",
  "relationship": "supporting | portfolio | exploration | maintenance",
  "attention": "remaining gate or none",
  "evidence_grade": ""
}
```

Write the weekly judgment after selection. Synthesize the original goal or
missing-source boundary, actual change, material variance, current decision, and
largest remaining gate. Never combine work and personal judgments.

Return only justified next commitments; do not force a count. Keep agreement to
an action separate from agreement to its timing or acceptance conditions. Use
only recorded closure criteria; if absent, say they are not recorded. Additional
writer-suggested criteria remain `proposed`, not prerequisites for agreed work.
Do not turn absent effect measurements into new tasks or gates. A next-week
commitment needs supported next-week timing; retain undated actions as undated
and other dated plans in their actual period. Preserve recorded parallel work
and dependencies rather than deriving a new sequence from report order.

## Evidence

- Raw entries establish recorded intent and status.
- Source refs establish provenance.
- Commits, tests, evals, issue states, and explicit source-of-truth files may
  verify bounded claims.
- General artifact dossiers are navigation or recorded context unless direct.
- Conflicts remain visible and lower confidence.
