# Weekly Slides Contract

Read only for explicit Weekly slides, after the shared analysis contract.

## Audience and Occasion Framing

**Slides only.** Resolve the communication job before selecting presentation
content. Keep this as internal analysis rather than another public page schema:

```json
{
  "primary_audience": "one role, not managers plus peers plus reviewers",
  "prior_knowledge": "what this audience can safely be assumed to know",
  "occasion": "live_brief | async_read | technical_review",
  "duration": "optional user-supplied constraint",
  "deck_job": "inform | recommend | decide | request_support | technical_review",
  "audience_outcome": "the judgment, action, or understanding required",
  "central_claim": "one evidence-bounded conclusion",
  "confidence_boundary": "what the evidence does not establish"
}
```

Express the communication job in one sentence:

> By the end, **[primary audience]** should **[audience outcome]** because
> **[central claim within its confidence boundary]**.

When framing is absent, use this product default:

- primary audience: same-department colleagues;
- prior knowledge: they know the project's basic context but not this week's
  latest implementation and validation;
- occasion: department weekly meeting;
- duration: unspecified;
- deck job: inform;
- audience outcome: understand this week's progress and implementation state,
  know material boundaries or collaboration needs, and see the next-week plan.

Explicit manager, leadership, async-read, or technical-review wording overrides
the default. A technical-review occasion may admit deeper mechanism and
provenance in slide bodies without relaxing source-truth rules or the
change-first selection below. Ask at most one combined question only when
unresolved ambiguity would materially change result selection, grouping, or
the requested action.
Never use `reporting_group` alone as the audience definition, and do not mix
distinct audience roles in one deck.

## Result Selection and Goal Narratives

**Slides only.** Select a result only when removing it would change the primary
audience's understanding, action, or confidence. Implementation inventory,
secondary work streams, provenance, and details useful only for technical
follow-up go to speaker notes or internal records.

Do not admit a result merely because it is effortful, complete, technically
interesting, or present in Weekly Analysis. The main deck answers the
communication job; accountability stays in internal records and raw sources.

Select what changed this period first; add background only as far as needed to
understand that change. Do not turn the deck into a teaching tour of the
system, and do not give a module, field, or test category a page merely
because it exists.

For one selected goal lane, build one local thesis before page writing:

```text
work goal
→ weekly result or final choice
→ shortest necessary rationale
→ evidence and current boundary
→ next closure
```

The work goal answers why the work exists; it must not be reconstructed from
actions, commits, modules, or effort. Group claims into the fewest semantic
compositions that preserve this local thesis. Do not add an overview page.

When two or more independent goal lanes survive Result Selection, keep one
communication job but do not force one business thesis. Treat lanes as
independent when no source supports a common objective and they have different
problems, results or choices, evidence, and remaining gates. Sharing a project,
reporting group, audience, week, technology, or generic wording such as
“improve quality” is not common-goal evidence.

Start a multi-goal deck with one weekly goal map. For every selected lane, the
map states its weekly result, current status, and most important remaining
boundary; each lane's Why sits in the map or its first page.
It must contain judgment, not merely names or an agenda. Keep each lane's
narrative contiguous, using only that lane's goal source and result evidence. A lane that does not change audience understanding, action, or
confidence stays in portfolio. These groups remain internal
authoring logic rather than public Story/Why/Goal fields.

## Cognitive Task Decomposition

**Slides only and on demand.** Use this temporary reasoning step only when a
complex selected result still has an uncertain merge/split decision. Do not run
it for every result, expose its role labels, or create another public schema. A
cognitive task is a diagnostic unit, not a page.

First state the audience-facing conclusion the selected result must support.
Then identify only the roles needed to test independence:

- `problem_reframe`: replace the apparent problem with the real constraint;
- `design_rationale`: explain the trade-off and why the chosen direction wins;
- `mechanism`: explain how the chosen solution causally operates, including
  material branches, fallback, and unchanged boundary;
- `validation`: change confidence using comparable results, tests, or an
  explicit evidence gap;
- `decision`: make the required judgment, support, or next gate unavoidable.

For each temporary task, record an internal `supported_claim`, its evidence
boundary, likely source locators, the facts or relationship that prove it, and
the prior understanding it needs. Discard tasks that do not advance the Deck
Thesis. A retained `supported_claim` becomes the public slide title or combines
into another; do not make the audience infer the conclusion from a topic label.

## Selected-source Reopen

Reopen the raw entries and direct artifacts behind every selected result and
retained claim. Do not construct full packets for unselected results.
Existing Weekly prose may locate evidence but cannot substitute for it. Build
an internal Source Grounding Packet containing:

- source path or raw entry identifier;
- the exact claim it supports;
- extracted facts, values, labels, and relationships usable on the page;
- available text, relationship, screenshot, code structure, or table;
- the evidence boundary;
- unverified statements that must not be presented as fact.

Do not expose full packets per page; emit no Evidence Appendix, and keep
claim-to-source mapping internal or in speaker notes.

### Recover material grounding once, not source by source

Admission cards and artifact dossiers locate evidence; they are not substitutes
for a commit, code snapshot, eval, or design document when a retained page needs
exact structure or relationships. After the first reopen pass, identify only
missing sources that satisfy all of these conditions:

- the result is selected for the main deck;
- the missing material affects the central claim, objects, relationship, visual
  expression, or confidence boundary;
- raw and dossier summaries cannot support the required precision;
- deleting or degrading the page would remove necessary understanding.

Ask the user once for all such gaps. For each one, name the affected claim, the
missing grounding, the consequence of skipping it, and acceptable forms such as
a repository path plus commit id, local document, durable document URL, export,
or screenshot. Do not interrupt for provenance completeness or optional detail.

Treat supplied material by its actual responsibility: repository plus commit
and a qualified snapshot can establish committed structure; an accessible
design document can establish target design; a screenshot establishes only
visible content; and a user explanation establishes recorded intent or context,
not code topology, tested behavior, or observed effect.

If the user skips or the source remains inaccessible, merge or omit a
nonessential page. A dossier may still support an explicitly recorded,
conceptual design boundary. If exact mechanics are necessary and no source can
establish them, fail PPT Mode rather than manufacture the page. Weekly uses
user-supplied material for the current run only; durable capture remains an
explicit later action.

### Follow the source chain only as far as the claim requires

Raw entries remain semantic truth for intent, status, and management meaning.
For a technical explanation, follow their direct locators rather than treating
the raw summary as code structure:

- a commit diff establishes the implementation delta;
- an immutable repository snapshot captured within the report cutoff establishes
  the resulting committed structure;
- tests or a harness establish only the behavior they exercise;
- eval or production data establishes observed effect within its sample;
- a plan or design document establishes target design, not current state.

Resolve a commit repository from `source_refs.path`, then the matching project
registry entry, then the current repository when it is the same project. A
commit diff establishes the delta. For the resulting structure, select the
latest relevant `repository_snapshot` from scoped raw entries whose entry
timestamp and `captured_at` (when present) are not later than `as_of`, whose absolute `path` identifies the same
repository, and whose full object id exists locally. Never derive a historical
tree from a branch name or substitute today's `HEAD`; branches move and are not
reproducible evidence.

When combining a commit delta with a later snapshot, use Git's ancestry check to
confirm that the referenced commit is an ancestor of the snapshot. If that
relationship cannot be established, keep the sources separate. A snapshot
represents committed content only; it does not establish staged, unstaged, or
untracked work.

If no qualified snapshot exists, the referenced commit tree may still support
wording such as "the structure after this commit", but not "the final structure
at the weekly cutoff". If the repository, commit, or snapshot cannot be
resolved, retain the raw-supported claim, mark the code view unavailable, and
do not manufacture module names, edges, or a current-architecture diagram.

Keep these truth types distinct in wording even when they share a page:
recorded intent, implemented structure, tested behavior, observed effect, and
target design. A commit or code diagram never proves quality improvement, and a
target-design diagram must be visibly described as not yet implemented.

## Evidence Responsibility and Final Deck Writing

Convert selected grounded material directly into presentation content:

- the work goal and why it matters now;
- the final choice and its shortest goal-serving rationale;
- facts and contradictions the audience must see;
- actual objects and relationships;
- observed numbers with sample and boundary;
- mechanism detail—main path, material branch, fallback, input, output,
  invariant—only as far as the audience needs it to follow the
  change, choice, or risk on this page;
- Before/After, Mermaid, Markdown tables, quote blocks, or concise prose;
- remaining risks and decisions, with recorded pass/fail gates.

Do not expose full candidate, constraint, or rejected-alternative inventories by
default. Keep that evidence local unless the current audience must compare or
choose among those paths.

Assign every retained evidence item one responsibility: architecture
establishes structure, tests establish exercised behavior, evals observed
effect within their sample, design artifacts target intent. One page may combine several proof objects when they
jointly support one claim. Spatial adjacency must not imply that one evidence
type proves another.

Do not specify layout, font, color, cards, regions, or drawing instructions in
the public Markdown. Markdown is the audience-facing semantic presentation,
not a Production Brief. If grounded content cannot state the needed objects,
relations, values, or risks directly, supplement evidence, merge, or omit the
candidate.

### Choose a representation from the evidence shape

First state the concept in plain audience language and, when it materially
helps, ground it with one minimal example. Then choose the lightest
representation that makes a supported relationship easier to see:

| Grounded shape | Prefer |
|---|---|
| architecture, data flow, module relation | structure or flow diagram |
| causal chain, process, state change | causal diagram, timeline, or state view |
| feedback, retry, iterative update | loop diagram |
| distribution, scale, marginal change | compact ASCII curve only with comparable evidence |
| cost/quality or speed/accuracy tension | trade-off curve only with comparable axes; otherwise a table |
| repeated old/new comparison | small table or matrix |
| one case changing step by step | aligned example trace |
| formula as the irreducible relation | one minimal formula plus a plain-language translation |
| two or three sentences already suffice | text only |

Use fenced `text` for ASCII within 80 characters; diagrams are optional and
never the first body block—state the concept first. Every node, edge, value,
and label must be traceable to the grounded packet, with its evidence boundary
immediately after the visual.
A reader seeing only the visual should recover the relevant relationship and
boundary without inferring a stronger result. If the visual only reformats the
summary, remove it.

When the grounded shape clearly implies one primary representation, use it
directly (table, tree, trace, image pair); the maker keeps that form. When no
shape dominates, the maker chooses the visual translation.

### Page independence and merge or split

A candidate becomes a page only when it carries an independent supported claim,
contains grounded presentation content, advances the communication job, and
cannot be deleted without changing the audience's decision, understanding, or
confidence.

Prefer one page. Split `design_rationale` from `mechanism` only when both
pages serve the same local goal narrative, use different source material and
cognitive tasks, and the mechanism depends on the facts and trade-offs presented
first. The first page directly presents the design problem and
choice; the second directly presents operation, branch or fallback, and
unchanged boundary.

Otherwise merge them. One grounded Before/After, relationship, or flow view is
enough when it carries the root cause, choice, and operation. Add validation as
a third page only when it independently changes confidence or the decision and
has its own packet and visual.

When a user supplies a PPTX template, the page decision is not final until the
grounded claim is mapped to a real source slide. Preserve the claim and shorten
copy, choose another source layout, or split only when the native layout cannot
carry the proof at its original typography. Never shrink text to protect an
earlier page count, and never let a template create unsupported semantics.

Reject background pages, option inventories without a decision, module or step
lists, interchangeable pages, and detail pages whose deletion changes nothing.

## PPT-ready Markdown Deck

**Slides only.** Return one public Markdown document using `slide-template.md`.
It must remain complete and readable without a `.pptx`.

Use the resolved primary audience. When framing is skipped, use the
same-department weekly-meeting default above. Duration remains unspecified.
Keep only necessary main-deck slides; use no numeric page cap. An unusual length
triggers deletion and compression review. A result may use zero, one, two, or—
only when independent validation changes understanding or action—three slides.

Public content consists of a compact deck framing line, audience-facing slide
content, and optional speaker notes. Internal
semantic groups, cognitive roles, source packets, visual feasibility,
merge/split analysis, unsupported-claim ledgers, and production guidance remain
hidden.

Give each layer one responsibility: the slide body carries the conclusion, the
evidence the audience must see, and limits that would mislead if removed;
speaker notes carry presenter supplements and source hints; sources and
reconciliation stay internal; not every fact must enter the body.

For the default same-department weekly meeting, end with one next-week plan page
that distinguishes confirmed commitments from proposals. Use only recorded
dates, owners, and closure criteria; a missing criterion, owner, or date is
shown explicitly, never invented; an unresolved target stays marked; undated
items stay undated. Group items by lane in a multi-goal deck; a lane must not
first appear on this page.

Run the preflights in `slide-template.md`, including whole-deck integrity: no
repetition that adds no understanding, action, or confidence; state words name
object, confirmer, scope; worked examples internally derivable; illustrative-
only examples marked.

Run at most one bounded repair using the admission view, reopened sources,
validator feedback, and draft. If material lanes remain missing or the
body still consists of implementation inventory instead of presentation
semantics, return a non-slide result headed `PPT Mode 未通过`. Name one of
`evidence insufficient`, `contract validation failed`, or `model capability
insufficient`, then preserve candidate lanes, usable facts, evidence boundaries,
and user options. Do not number failure content as slides or silently switch to
Brief or another model.

## Optional Template-native PPTX

**Slides only and only when explicitly requested.** Treat the user-supplied
PPTX as the visual source. Use an existing presentation capability when the
runtime provides one; otherwise stop at Markdown and state the capability
boundary.

- Inspect every source slide; map each output slide to a real one, duplicate
  it, edit inherited elements rather than rebuilding its style, and preserve
  master, layout, typography, spacing, and native editability.
- If copy does not fit, shorten, remap, or split. Do not shrink or flatten it.
- Render and inspect every final page; verify template fidelity and overflow.
- Write a versioned copy and preserve its predecessor.
- Carry the deck's speaker notes into the PPTX notes pane and spot-check them
  at delivery.
- Apply one evidence or user-comment revision to affected claims and dependent
  pages without re-deciding unrelated pages. Keep stable page ids where the
  cognitive job survives; reorder pages only when changed evidence changes the
  claim sequence. Formatting-only differences are not a revision.

Do not add a renderer, a closed style gallery, a persistent template registry,
or a custom history database to Tracework. A template path is an explicit run
input and versioned files provide rollback.


## Deck Workflow

Skip for `quick` and `brief`. Run only for `slides`:

```text
Coverage → Result Selection → Selected-source Reopen
→ Source Grounding Recovery when a necessary page remains unsupported
→ Final Deck
```

1. Resolve framing before ranking; default to the same-department weekly meeting.
2. Build one local narrative per selected lane; multiple lanes start from one
   grounded goal map and keep lane pages contiguous.
3. Reopen only selected sources; give each evidence item a proof
   responsibility; complementary proof objects may share one page.
4. Ask once for all still-missing material sources before degrading or merging
   a necessary page; never ask for provenance-only detail.
5. Use Cognitive Task Decomposition only to diagnose a complex split.
6. Delete or merge pages that do not change understanding, action, or
   confidence; unusual length gets semantic review, not a numeric cap.
7. End with confirmed/proposed next-week closure, grouped by lane.

If data is missing, incomparable, or contradictory, do not invent a chart:
use a mechanism or state-change view, lower the evidence boundary, expose the
measurement gap, and name its recorded closure criterion when one exists. The
bounded-repair and failure rules above apply as written; a template-native
PPTX follows the optional contract above with no new renderer.


## Slides Quality Gate

- One audience and outcome before selection; absent framing defaults to
  same-department colleagues, no invented duration, next-week closure.
- Multi-goal decks open with the grounded goal map; unrelated goals stay
  independent; no single-goal overview page.
- Cognitive roles stay internal and on demand; split only for independent
  evidence and prerequisite claims.
- Every diagram, number, test, trace, or design artifact keeps one proof
  responsibility; implementation structure is never effect evidence.
- Emit only necessary slides; zero candidates produce an empty state; unusual
  length gets deletion/compression review, not a numeric cap.
- Reader and maker use the Markdown without vault research, semantic
  invention, or production instructions.
- Charts stay comparable with units and sample context; truth states separate;
  provenance out of ordinary main slides unless technical review needs it.
- Template-native PPTX stays editable, rendered, versioned, revision-safe.


## Slides Anti-Patterns

- One slide per stream by default.
- Fixed “design slide + implementation slide” pairs.
- One proof-object type per page when complementary evidence is needed to prove
  one claim.
- A full candidate, constraint, or rejected-alternative inventory when the
  audience only needs the final choice and its shortest rationale.
- A public Storyboard or Production Brief beside the public Markdown Deck.
- A public Evidence Appendix, coverage ledger, or claim-to-source table in the
  deck.
- `Audience takeaway`, `Recommended visual form`, `Page composition`,
  `On-slide copy`, `Production constraints`, or page-level Source Grounding
  Packet sections in the public deck.
- Public Story, Why/Goal field, or cognitive-role scaffolding that the audience
  would not expect to see in the actual presentation.
- Topic, question, process, or object-only titles that hide the supported
  claim (for example `方案怎么跑通`).
- A design slide that only supplies background, history, or option inventory.
- A mechanism slide that is only a module, field, code, or step list.
- Two slides that do not perform independent cognitive work, or a detail slide
  whose removal changes neither thesis nor audience decision.
- Content that makes the reader or maker reopen the vault to discover the
  actual claim, node, relationship, number, or risk.
- Layout, typography, color, card, or diagram-production instructions.
- Decorative architecture diagrams with only component names and arrows.
- Ungrounded, wrong-cutoff, target-as-current, or prose-reformatting diagrams.
- Using a solution-logic diagram as proof of effectiveness.
- Bundled style galleries, flattened slides, or a custom version database when
  user templates and versioned files already suffice.
- Repeating the same audit-style disclaimer on page after page instead of
  scoping each claim once, beside the claim it qualifies.
- State words such as closed, accepted, or passed without naming the object,
  the confirmer, and the scope of the confirmation.
