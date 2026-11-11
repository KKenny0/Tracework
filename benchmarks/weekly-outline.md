# Weekly Brief Benchmark

## Goal

Verify that Weekly produces a scoped, objective-anchored management judgment
from raw evidence: intended direction, actual change, material variance,
current decision, and next commitment. It must keep every meaningful stream
visible without inventing a retrospective Why. When slides are explicit, it
must resolve the communication job, reopen supporting sources, and turn the
analysis into an audience-facing PPT-ready Markdown Deck rather than paginate
the Brief. When an editable PPTX and template are explicit, it must preserve the
template and support a real revision round trip.

## Goal-Loop Scenarios

1. **Same actions, different goals**: competitor analysis, three content items,
   and two customer follow-ups must produce different ranking and management
   meaning for “win next week's proposal” versus “reduce delivery risk.”
2. **No reliable goal source**: label the goal unknown, ask at most one question
   only when ambiguity would change selection or priority, continue when skipped,
   and never infer a confirmed Why from actions, commits, modules, or effort.
3. **Prior commitments**: account for every prior confirmed commitment and
   proposal as `met`, `advanced`, `blocked`, `replanned`, or `not_started`.
4. **Evidence-led replan**: preserve the old direction, evidence trigger,
   reason, and new direction; do not report a justified replan as simple failure.
5. **Unplanned critical repair**: expose both the repair's material value and
   the original goal it displaced.
6. **Exploration**: allow closing uncertainty or ruling out a path to be the
   objective; do not manufacture a delivery.
7. **Multiple work projects**: keep separate goal lanes when projects share a
   reporting group but no objective.
8. **Work scope with mixed vault**: personal projects must not appear anywhere
   in output, including paths and evidence refs.
9. **All scope**: work and personal receive separate judgments, goal lanes,
   portfolios, next commitments, and evidence sections.
10. **Raw entries sufficient**: raw fields drive state, meaning, and risk; matching
   git commits remain coverage/evidence.
11. **Git-only fallback**: meaningful activity remains `limited`; chore noise is
   filtered and no motivation or verified impact is invented.
12. **Artifact context**: source-of-truth references can support a bounded claim;
   general dossier context remains navigation.
13. **Dense week**: select every change needed to explain goal progress,
   variance, or a management decision; every other meaningful stream remains in
   portfolio coverage. Do not force a headline count.
14. **Conflict**: later or conflicting raw states remain visible and lower
   confidence.
15. **Explicit PPT request**: produce one PPT-ready Markdown Deck with only
    necessary main slides per group. Zero admitted pages return an empty state.
    Default Weekly remains a Brief.
16. **Quantified algorithm result**: recommend a result chart only when metric,
   unit, baseline, current value, delta, sample scope, method, and comparability
   support it.
17. **Missing effect data**: show mechanism or Before/After plus a measurement
    plan and closure criterion; never invent a result chart.
18. **Conflicting metrics**: expose invalid ordering, incompatible samples, or
    unit conflicts, lower confidence, and withhold the chart.
19. **Core runtime mechanism**: use mechanism evidence only when it materially
    advances the audience's understanding; a diagram explains causality rather
    than enumerate actors or steps.
20. **Cognitive decomposition**: only when a complex result has an uncertain
    merge/split decision, identify necessary problem reframe, design rationale,
    mechanism, validation, and decision roles internally; roles are diagnostics,
    not pages or a mandatory stage.
21. **Maintenance-only work**: retain parameter tuning, cleanup, and
    non-mechanism configuration work in the portfolio without decorative
    architecture diagrams or implementation narratives.
22. **Audience and occasion**: resolve one primary audience, prior knowledge,
    occasion, optional duration, deck job, and required audience outcome before
    page selection. With no explicit framing, default to same-department
    colleagues at a weekly meeting—not a timed manager decision brief.
23. **Goal-grounded semantic composition**: start from why the work exists,
    then present the weekly result or final choice, shortest rationale, evidence
    boundary, and next closure. Internal grouping does not become public
    authoring fields.
24. **Selected-source reopen**: reopen raw and direct sources only for selected
    results, keep source packets internal, and turn facts, relations,
    comparisons, mechanisms, numbers, boundaries, and gates into presentation
    content itself.
25. **Contract rejection probes**: reject missing audience outcome, topic-only
    titles, unsupported title claims, production guidelines in public content,
    unsafe main-deck references, false complex-result merges, mechanical
    simple-result splits, and appendix-only meaning.
26. **Qualified commit source**: when a technical claim points to a commit,
    resolve its repository, inspect the delta, and use only an immutable captured
    snapshot within the report cutoff for the resulting committed tree. An
    unresolvable commit or snapshot cannot support a current-topology visual.
27. **Truth-state separation**: distinguish recorded intent, implemented
    structure, tested behavior, observed effect, and target design. Never use a
    code or design diagram as effect evidence.
28. **Representation utility**: state the concept in plain language first, then
    add only the lightest diagram, table, trace, curve, formula, or text view
    that materially reduces the declared audience's understanding cost.
29. **Independent goal lanes**: one communication job does not create a common
    business goal. A single-goal deck starts directly with its local narrative;
    a multi-goal deck starts with a grounded goal map, keeps lane narratives
    contiguous, and groups next-week closure by lane.

## PPT-ready Markdown Deck Scenarios

1. **P1 — One goal, several actions**: merge activities that prove one audience
   conclusion instead of allocating one page per activity.
2. **P2 — Complex mechanism**: allow more than one page only when the pages
   perform independent cognitive work.
3. **P3 — Quiet maintenance week**: produce a short deck without filler cover,
   agenda, status, or summary pages.
4. **P4 — No comparable metric**: use a relationship, process, state, or
   evidence-boundary visual instead of a chart.
5. **P5 — Comparable metric**: let the chart prove the conclusion without
   repeating the same values in adjacent text or a table.
6. **P6 — Management decision**: combine risk, variance, and support into one
   decision page when they serve one judgment.
7. **P7 — Non-code work**: support proposal, content, and customer progress
   without requiring technical diagrams.
8. **P8 — All scope**: create separate work and personal mini-decks with their
   own thesis and audience decision.
9. **P9 — Evidence conflict**: lower claim strength and keep the conflict
   visible.
10. **P10 — Deletion**: reject any page whose removal changes neither deck
    thesis nor audience decision.
11. **P11 — Independent goals**: when two source-independent goals both change
    colleague understanding or action, Slide 1 carries both Whys, results,
    states, and boundaries; each lane then receives its own evidence and gate.

### P2-A — Complex Story forms a natural progression

Input contains an old approach's failure, candidate trade-offs, a governing
design constraint, the new operating path, and an unchanged boundary.

Pass only when:

- one communication job and one primary audience govern both pages;
- page-one title states the supported design judgment and its body proves the
  constraints and trade-offs;
- page-two title states the operating claim and depends on page one's premise;
- pages use different grounded source material and cognitive tasks;
- no authoring field or production guideline appears in public content;
- a fresh target reader can state both conclusions and their dependency;
- deleting either page changes the audience's understanding or decision.

### P2-B — Simple result must merge

When one Before/After, relationship, or flow can fully express root cause,
choice, and operation, emit one claim-led content page.

Fail when:

- design and mechanism are split by convention;
- page two only expands page-one detail;
- deleting either page leaves the audience outcome intact.

### P2-C — Blind Content Handoff

Give only the final Markdown Deck to an independent maker who did not perform
Weekly Analysis.

The maker may choose layout, type, color, and visual translation. They may not
browse the vault, research trade-offs, invent nodes, relations, numbers, or
risks, or re-decide the split. Pass only when PPT and Markdown carry the same
argument and the maker performs visual translation only.

### P3-A — Audience Outcome Read

Give only the public deck to a fresh member of the declared primary audience.

Pass only when the reader can state, after a short read:

- the deck thesis;
- the confidence boundary;
- the decision, action, or understanding expected of them.

Fail when they mainly recall modules, commits, process steps, or raw facts while
missing the management conclusion.

### P3-B — Standalone Claim-led Markdown

Read the Markdown without making a PPT. Pass only when a reader can reconstruct
the cumulative claim sequence, material facts, relationships, numbers, risks,
and decision without production guidance or access to internal source records.

### P3-C — Template-native Editable Delivery

When the user supplies a template and requests an actual PPTX, inspect every
source slide and map each output page to one source page. Pass only when:

- copied slides preserve source masters, layouts, typography, and spacing;
- narrative content edits inherited elements instead of overlaying a rebuild;
- all titles, numbers, charts, and key objects remain natively editable;
- copy fits at source type sizes without clipping or silent shrinkage;
- every rendered page passes overflow and template-fidelity review;
- no fixed Tracework style gallery or flattened slide image substitutes for the
  supplied template.

### P3-D — Revision Round Trip

Preserve the accepted PPTX, add later evidence or a precise user comment, and
write a new version. Pass only when affected claims, proof, and dependent
decision pages update together; unrelated page logic and template mapping do
not get re-decided; the previous version remains recoverable; and the revised
deck still passes audience, source, editability, and render checks. Preserve
stable page ids where the cognitive job survives, but allow a grounded revision
to add, remove, or reorder pages when the evidence changes the necessary claim
sequence. Whitespace-only or formatting-only differences do not count as a
revision.

### P3-E — Code-grounded Current Architecture

Input contains a raw entry whose typed commit source includes a repository
path, plus a later target-design document.

Pass only when:

- the commit diff supplies the weekly delta and an immutable captured repository
  snapshot at or before `as_of` supplies the resulting committed modules and
  relationships;
- the slide explains the concept in plain language before the diagram;
- every diagram node and edge is traceable to the source chain;
- tests are described only as exercised behavior, not quality or production
  proof;
- current implementation and target design are visibly different claims with
  different sources;
- internal source records or speaker notes preserve the qualified commit,
  captured snapshot, and design source without exposing an Evidence Appendix
  or leaking paths and hashes into the spoken slide.

If the repo path, commit, or captured snapshot cannot be resolved, pass only by
falling back to a raw-supported conceptual view and stating that the current
code topology is unavailable. Inventing a plausible architecture fails.

### P3-F — Visual Utility and Text-only Restraint

For a complex mechanism, a fresh peer viewing only the visual must be able to
explain the supported objects, relationships, and evidence boundary without
claiming an unobserved effect. The concept must already be understandable in
plain language before the visual appears.

For a simple repair that two or three sentences explain completely, pass only
with text. A diagram fails when it merely turns those sentences into boxes and
arrows, adds no relationship the audience needs, or survives deletion without
changing understanding.

## Brief Compression Scenarios

Compression is semantic, not a character or item budget. The body is the
minimum information needed to reconstruct goal state, actual change, material
variance, decision or support, next commitment, and confidence boundary.

1. **C1 — Body sufficiency**: a fresh reader can reconstruct all six management
   fields without opening the appendix.
2. **C2 — Counterfactual deletion**: every body block uniquely changes at least
   one management field, action, or confidence boundary.
3. **C3 — Appendix migration**: a material block, replan, decision request, or
   evidence conflict fails validation when it exists only in the appendix.
4. **C4 — Maintenance noise invariance**: adding routine maintenance changes
   the appendix but leaves the body unchanged.
5. **C5 — Material risk sensitivity**: adding a decision-blocking risk changes
   the body and names the risk there.
6. **C6 — Evidence expansion invariance**: adding refs for an unchanged claim
   grows evidence mapping without expanding the body; a confidence change is
   the exception.
7. **C7 — Complete accountability**: every prior item and meaningful stream is
   present in the appendix even when absent from the body.
8. **C8 — One expanded home**: appendix ledgers do not repeat a body narrative.
9. **C9 — Dense-week justification**: a dense body may contain more blocks only
   when each represents an independent management change, not more activity or
   evidence volume.

## Semantic Admission, Grounding Recovery, and Capability Failure

Semantic Admission is a routing aid, not page evidence. Its cost ledger reports
`evidence_source_input` separately and applies the efficiency gate to comparable
input that includes the mandatory Weekly skill and references on both sides.
Classifying every card is not semantic completeness: material goal lanes must
remain in the main narrative and every prior commitment must be accounted for.
The candidate ledger and required-lane/prior-obligation oracle are separate
inputs. An evaluated run must execute ledger validation; card preparation alone
cannot claim Coverage Gate success. Mandatory Weekly instructions and reopened
evidence are measured from their actual files, and a failed comparable-input
gate exits non-zero. The CLI keeps `model_input` separate from diagnostic
`metrics`; only the former counts as the admission payload sent to the model.

After Result Selection, reopen only the commit, snapshot, eval, document, or
other direct source required by retained claims. Ask the user at most once when
one or more missing sources affect necessary main-deck semantics. The combined
request states the claim, missing grounding, accepted source forms, and the
skip/degrade outcome. Appendix-only gaps do not interrupt the user. User prose
establishes recorded context only; it never proves code topology or observed
effect.

The recovery fixture, not the candidate, owns the expected material and exact
gap ids plus the source-type-to-proof-responsibility mapping. The single rendered
question must include each requested claim, missing grounding, accepted source
forms, and skip consequence. Gap and degradation actions use closed values so
equivalent wording cannot recreate precise structure after a source is skipped.

After one bounded repair, an output that still loses a material lane, exposes
implementation inventory or internal coverage bookkeeping, or requires a maker
to invent objects and relationships must return a non-slide `PPT Mode 未通过`
recovery pack. It must not emit numbered slides or silently switch mode/model.

Executable mutations must reject:

- a material Agent-native card hidden as `explicit_exclusion`;
- a prior commitment omitted from accounting;
- source-only savings presented as total-input or token savings;
- separate recovery questions for each missing source;
- requests for nonmaterial or appendix-only sources;
- user explanation promoted to committed architecture;
- exact architecture generated after the source is skipped;
- `coverage ledger`, undefined stage labels, line counts, or harness inventory
  in same-department main slides;
- a failed weak-model draft returned as numbered slides.

## Pass Criteria

- Scope partition occurs before ranking.
- Every reporting group has exactly one repeatable weekly judgment.
- Every goal states its source, confidence, closure criterion, status, and
  confirmed/proposed commitment state.
- Inferred and unknown goals never use confirmed-goal language.
- Every material change is goal-linked, explicitly unplanned, or in the
  portfolio.
- Every prior commitment is accounted for and no proposal is silently promoted.
- Replans preserve the prior direction, trigger, reason, and new direction.
- Headline and next-commitment counts are not fixed.
- Every next commitment has a pass/fail closure criterion.
- Raw entries are semantic truth; git-only work stays limited.
- Activity volume never becomes an outcome by itself.
- Main prose is readable without report-local ids.
- Claim-level evidence remains available in the appendix.
- The brief body contains no tables, source paths, commit lists, or evidence
  index.
- Every body block survives the counterfactual deletion test.
- Full prior-item accounting and meaningful-stream coverage remain in compact
  appendix ledgers.
- Adding maintenance or extra evidence without changing management meaning does
  not expand the body.
- Adding a material decision-blocking risk does change the body.
- The appendix maps body claims to evidence without retelling body prose.
- Executable fixtures map every admitted slide to an available source and an
  explicit proof responsibility; fabricated sources fail validation.
- Slides resolve one primary audience, prior knowledge, occasion, optional
  duration, deck job, audience outcome, central claim, and confidence boundary
  before selection. If framing is absent, use the same-department weekly-meeting
  default with no invented duration.
- The Markdown Deck states a compact presentation context and one required
  audience understanding, judgment, or action.
- One communication job does not force one business thesis. A single-goal deck
  has no generic overview; a multi-goal deck uses one evidence-bearing goal map
  and never derives commonality from project, group, audience, week, or generic
  “improve quality” wording.
- A produced main deck has only necessary slides; unusual length triggers
  deletion/compression review rather than a numeric cap. Zero admitted
  candidates return an empty state instead of an empty deck.
- An unusual-length fixture must also reject duplicated pages that merely use
  different ids, and an empty state must name missing evidence and a repair
  action without bypassing audience defaults or leaking deck-only fields.
- The work goal is visible and not reconstructed from actions. Cognitive roles
  are invoked only for complex merge/split diagnosis and remain internal.
- Each title states an evidence-bounded audience-facing claim, and the page body
  visibly proves it.
- Each page directly presents supported facts, relationships, comparison,
  mechanism, numbers, boundaries, or risks; it contains no production fields.
- Complementary proof objects may share one page when they serve one cognitive
  job, and each evidence item states its proof responsibility.
- The main deck defaults to the final choice and shortest rationale; complete
  rejected-path archaeology stays local unless the audience must choose now.
- Full Source Grounding Packets and unsupported-claim ledgers remain internal;
  source mappings stay in internal records or speaker notes, with no public
  Evidence Appendix. Executable fixture field `internal_evidence` is a private
  validation sidecar, never part of the audience deck.
- Complex results split only when pages use different grounded material and
  cognitive tasks, serve one local goal narrative, and form a prerequisite
  sequence.
- Simple results remain merged when one content block explains root cause,
  choice, and operation.
- Validation receives a separate page only when it changes confidence, risk, or
  the audience decision.
- Removing any slide changes the audience's decision, understanding, or
  confidence.
- The deck passes audience outcome reading, claim-to-proof review, standalone
  reading, and blind content handoff.
- Mechanism completion, effect validation, and production acceptance are
  reported separately.
- Open risks and next-week acceptance targets preserve recorded closure
  criteria; missing criteria stay explicitly unrecorded.
- The default same-department deck ends with a next-week plan page that
  distinguishes confirmed commitments from proposals. Each item preserves its
  source commitment state and any recorded closure criterion; missing criteria
  stay explicitly unrecorded. Source commitments
  and rendered plan blocks match one-to-one, while negated, omitted, swapped,
  or promoted commitments fail validation.
- A revision that changes, adds, or removes a supported claim also changes its
  internal evidence map; reusing a stale map fails validation.
- Expected effects never appear as observed outcomes, and missing numeric
  evidence never becomes a guessed baseline, target, or trend.
- Default department slides keep source paths, commit hashes, raw evidence ids,
  and internal links in internal records or speaker notes; only explicit
  technical-review decks may
  show sanitized compact references.
- A requested template-native PPTX maps every output page to a real source page,
  remains natively editable, preserves the prior version, and passes rendered
  fit, fidelity, and one revision round trip.

## Fresh-Context Brief Check

A reader without project background must be able to answer:

1. What was the original goal, or why is it unknown?
2. What actually changed?
3. What variance or replan occurred, and why?
4. What decision or support is needed now?
5. What is the next commitment and its pass/fail criterion?

Missing any answer fails Phase 1 even when the executable contract is green.

## Slide Visual Routing

| Mechanism or evidence | Expected route |
|---|---|
| Concurrency, asynchronous stages, stage collaboration | sequence or swimlane |
| Data processing, aggregation, materialized rebuild | data flow |
| Provider, model, policy, or strategy dispatch | decision tree |
| Failure handling and fallback | failure path |
| Lifecycle or state transition | state machine |
| Component responsibility change | architecture relationship |
| Feedback, retry, or iterative update | loop diagram |
| One case changing step by step | aligned example trace |
| Repeated old/new comparison | small table or matrix |
| Formula is the irreducible relationship | one minimal formula plus plain-language translation |
| Comparable algorithm or outcome data | `comparison_chart`, `distribution_chart`, `trend_chart`, `timeline_chart`, or `waterfall_chart` |
| One reliable number | `number_card` |
| Missing or conflicting outcome data | mechanism/validation summary plus measurement plan |
| Two or three sentences already explain the result | text only |

## Real-Output Check

Use the real `2026-W31` vault entries with an explicit
`as_of: 2026-07-30T23:59:59+08:00`. Do not overwrite the source report or raw
entries. Save candidates under the ignored weekly eval directory.

The frozen W31 run uses this communication job unless the user overrides it:

> By the end, the responsible manager or project owner should decide whether
> source-faithful routing is ready to merge because the implementation is
> complete but the 10-episode evidence does not establish a quality gain.

The expected main argument is three necessary claims, not a reusable page
formula:

1. source-faithful routing is code-complete, but 10-episode evidence does not
   support merging it;
2. `117 -> 115` is not a demonstrated quality gain because five episodes
   improved and five regressed under a small, high-variance sample;
3. expand to at least 30 episodes or a second series, then apply a stated
   go/no-go gate.

Duration-route history, module topology, test and branch inventory, and the
agent-native v3.1 mechanism stay in speaker notes or a separate explicit technical
review unless the audience outcome requires them. Terms such as `B0/B1`,
`CP1-CP4`, `mode_id`, `TaskSkillSnapshot`, and commit or branch inventories must
not dominate the manager deck.

The frozen candidate fails when it expands the existing W31 Markdown instead of
reopening raw sources, mixes routing and agent-native architecture into one
thesis, exceeds eight pages, hides the conclusion in topic titles, or requires
technical prior knowledge not declared in the audience contract.

For the user-selected same-department weekly meeting, change the communication
job to progress synchronization. A real technical architecture page is
admissible when it helps peers continue development or review and survives the
deletion test. It must follow a qualified commit into a captured W31 snapshot,
present actual modules and relationships, and remain separate from the
Agent-native target design. The current W31 raw commit refs omit repository
paths, contain no repository snapshot, and the project registry does not resolve
the storyboard repository, so
the local candidate must visibly degrade to a raw-supported conceptual relation
rather than fabricate the S1-S5 code topology. This degraded result verifies
failure safety but does not satisfy the code-grounded happy path in P3-E.

Then extend the same W31 run to
`as_of: 2026-07-31T23:59:59+08:00` as a revision test. The new evidence says the
cleanup v2 signal is about 13% lower errors but entirely from
`too_many_actions`; `wrong_shot_size` remains 35; attribution remains incomplete.
Write a new version, update every affected claim and decision, keep the prior
version recoverable, and preserve template mapping unless the revised claim no
longer fits honestly.

Finally use a real user-selected editable template, complete P3-C and P3-D, and
give the Markdown, versioned PPTX, and renders to the user. If the user judges
the audience, argument, clarity, template use, or editability inadequate, the
Weekly PPT Mode correction does not pass. Automated checks and independent
reader/maker validation do not replace explicit user acceptance.
