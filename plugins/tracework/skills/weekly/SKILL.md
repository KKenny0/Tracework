---
name: weekly
description: >
  Generate a workplace-facing weekly report from Tracework raw entries, using
  git only as limited fallback coverage. Supports work, personal, and private
  all-project scopes. Three modes: quick conversation review ("这周做了啥",
  "周报简版", "quick weekly", "本周概要"), default Markdown brief ("写周报",
  "周报", "/tracework:weekly", "weekly brief", "本周总结", "weekly report"),
  and PPT-ready Markdown Deck only when weekly PPT is explicit ("weekly PPT", "周报 PPT",
  "weekly slides", "演示大纲"). Do not use for daily notes, generic slide
  decks, or single-commit analysis.
---

# Tracework Weekly

Turn a week of agent work into an objective-anchored feedback loop: direction,
actual change, variance, workplace judgment, and next commitment. Preserve
meaningful work without inventing a retrospective goal.
## Modes

Resolve mode before gathering evidence. Prefer the strongest explicit cue.

Priority when cues conflict: `slides` > `quick` > `brief`.

| Mode | Triggers (examples) | Output | Write files | Heavy slide rules |
| :--- | :--- | :--- | :--- | :--- |
| `quick` | 这周做了啥, 周报简版, quick weekly, 本周概要 | Conversation 5–7 bullets + carried-forward | No | No |
| `brief` | 写周报, 周报, /tracework:weekly, weekly brief, 本周总结, weekly report | Management brief | Yes when vault exists; else conversation | No |
| `slides` | weekly PPT, 周报 PPT, weekly slides, 演示大纲; or PPT/slides only after this skill is already selected for a weekly report | Audience-framed PPT-ready Markdown Deck; optional editable template-native PPTX when explicitly requested and supported | Same as brief; PPTX is a versioned copy | Yes |

Default to `brief` for a normal weekly report. Bare “PPT” or “slides” selects
slides only inside an already weekly-report request.

Slide mode selects for one audience, occasion, and communication job. Do not
paginate a Brief or force source-independent lanes under a shared goal. Default
to a same-department weekly meeting: colleagues know the project's basic
context, need this week's progress and implementation update, and need a final
next-week plan. Duration is optional and never supplies a default page count.
Explicit manager, leadership, async-read, or technical-review wording overrides
this default. Do not combine distinct audiences in one deck.

## Progressive References

Always:

- `references/reporting-narrative-contract.md` for scope partition, selection,
  closure, evidence, and audience safety.

For Weekly, the goal-loop rules below replace the shared contract's default
headline and next-target counts. Scope, evidence, closure, and audience-safety
rules remain unchanged.

For `brief` and `slides` only:

- `references/weekly-analysis-contract.md` for structured analysis. Use the brief
  analysis path unless mode is `slides`.
- `references/weekly-brief-template.md` for brief output only.

For `slides` only:

- `references/weekly-slides-contract.md` for selection, source recovery, and deck gates
- `references/slide-template.md`

Do not read `slide-template.md` for `quick` or `brief`.

## Inputs and Output

Resolve `{vault}` from project then global `.tracework/config.yaml`.

Defaults:

- Date range: current Monday through today.
- Scope: resolve with First-Run and Local Fallback below. Do not silently force
  unassigned projects into `work`.
- Mode: as above; default `brief`.
- Slides framing: user-supplied audience, occasion, optional duration, required
  understanding/action, and optional PPTX template path; otherwise use the
  same-department weekly-meeting default. No persistent template registry or
  style config.
- Brief/slides file output: `{vault}/Work Diary/Weekly/{YYYY-WNN}.md`, unless
  the user or config provides another path. Write that file only for normal
  scoped group output. Quick mode, no-vault runs, and local first-run stay in
  conversation so unassigned content is not written into workplace weekly files.

If the target brief/slides file exists, ask before overwriting unless the user
requested update, rewrite, or overwrite. If no vault exists, return brief or
slides content in conversation. Quick mode always stays in conversation.
Cold-start is optional upgrade copy, never a hard gate.

For an explicitly requested editable PPTX, preserve the template and write a
versioned copy. Without presentation-editing capability, deliver Markdown and
state the boundary; never imitate editability with flattened slide images.

## First-Run and Local Fallback

Weekly must produce value without prior setup.

### Scope resolution

Run `python <this-skill>/scripts/tracework_raw.py resolve-scope --cwd <project-root> --purpose report`
as defined in `references/reporting-narrative-contract.md`; add `--scope` only
for an explicit user choice. Use its `scope`, `scope_source`, and `reason`.
An assigned current-project group is a normal exact-group scope;
`scope_source=implicit-local` activates local first-run below.

### Partition rules

- **Explicit or configured** `work` / `personal` / named group:
  - Include only matching projects.
  - Exclude `unassigned`. Never promote unassigned into `work`.
  - If empty because the current project is unassigned, return a clear
    excluded/empty result with repair hint:
    `/tracework:cold-start-interview` or set `profile.reporting_group`.
  - Do not fail the skill.

- **Implicit** scope (no explicit group, no configured default):
  - If the current project has a `reporting_group`, use that group.
  - If the resolver returns `scope_source=implicit-local`, enter
    **local first-run**:
    - Report only the current repository.
    - Label scope `local` (unassigned), never `work`.
    - Use git plus any raw entries for that repo.
    - Mark git-only material `limited`.
    - Hint that workplace-scoped reports need `reporting_group`.
  - Do not mix unrelated assigned vault projects into a local first-run.

### No vault

- Always allowed for quick, brief, and slides.
- Write nothing to disk.
- Keep the narrative short; use conversation output.
- End brief/slides with at most one upgrade line:

  > 可选：配置 knowledge vault 后可跨天累计并写入文件。`/tracework:cold-start-interview`

- Do not imply the run failed because setup is missing.

### Empty signal

If local first-run has no raw entries and no meaningful git activity, return a
short empty-state and suggest capture or waiting for more work signal.

## Workflow

### 0. Resolve Mode, Range, and Scope

1. Choose `quick`, `brief`, or `slides` from the mode table.
2. Resolve week range and scope class (explicit / configured / implicit).
3. If mode is `quick`, follow **Quick Mode** and stop after its quality gate.
4. Otherwise continue with partition → evidence → goals → analysis → write.

### 1. Resolve and Partition

1. Load projects from the prompt, `raw/projects.json`, or current repo.
2. Resolve each project's `reporting_group` from project config, then registry.
3. Apply First-Run and Local Fallback with the audience-safety rules.
4. For normal scoped output, filter to the exact requested group. For `all`,
   keep groups separate throughout analysis and writing.
5. Exclude unassigned projects from scoped `work` / `personal` output and
   report the missing classification. Show them separately only in `all`.
6. For local first-run, keep a single `local` lane for the current repo.

### 2. Gather Evidence

For every in-scope project or the local lane:

1. Read matching `{vault}/raw/weeks/{week}/{slug}.json` entries when a vault
   exists.
2. Read the previous Weekly's next-period items as editorial context when it
   exists. Preserve whether each item was a confirmed commitment or only a
   report proposal; never silently promote a proposal.
3. Read explicit goal sources available in the request or project, such as a
   milestone or current `PLAN` artifact. Read only sources needed to establish
   the reporting goal.
4. Read optional artifact dossiers for navigation and recorded scope.
5. Run a lightweight git log only to detect uncovered work.
6. Merge duplicate raw/git signals before analysis.
7. Without a vault, use git coverage and conversation context only.

Raw entries are the semantic source. Git-only work remains `limited` and cannot
substantiate a completed outcome or invented trade-off.

### 3. Resolve Goals and Prior Commitments

Resolve each goal lane from the strongest available source:

1. an explicit goal in the current request;
2. a confirmed commitment or goal from the previous Weekly;
3. an explicit milestone, plan, or project-goal artifact;
4. a raw entry's recorded local objective or constraint;
5. a bounded inference from raw motivation;
6. `unknown`.

Actions, commits, modules, and effort volume are not goal sources. A previous
report proposal remains proposed rather than becoming a confirmed goal.

Record the goal statement, source, confidence, closure criterion, status, and
commitment state. Confidence is `confirmed`, `inferred`, or `unknown`; status is
`met`, `advanced`, `blocked`, `replanned`, or `not_started`; commitment state is
`confirmed` or `proposed`.

For `brief` and `slides`, ask at most one question only when goal ambiguity would
materially change selection, grouping, the overall judgment, or next priority:

> 这周原本最重要的是推进什么？

If the user skips it, continue with `目标未记录`. The Weekly may report bounded
facts but must not claim that an unknown goal advanced. Never backfill a
confirmed Why from completed activities. Quick mode does not ask this question.

`reporting_group` is an audience and privacy boundary, not proof that its
projects share one objective. Keep separate goal lanes when no common goal is
recorded.

### 4. Analyze Change and Variance (brief and slides)

Apply `references/weekly-analysis-contract.md` in the main dialog. For `brief`,
do not build slide candidates, chart briefs, or full solution-logic narratives.
A material change may use one lightweight Change Explanation Card visual when
removing it would change judgment, action, or confidence; otherwise keep the
compact text result. Slides-only visual production still waits for an explicit
upgrade.

For every prior commitment, record whether it was met, advanced, blocked,
replanned, or not started. No prior commitment may disappear.

Connect every material weekly change to a goal lane. When no honest link exists,
label it `unplanned but material` or keep it in the portfolio. Preserve the old
goal, evidence trigger, reason, and new direction for replanned work.

For `brief`, rank goal-linked and unplanned material changes inside each
reporting group by:

- observable end-state significance;
- management relevance;
- evidence strength;
- effect on the next planning decision.

Write one weekly judgment per group. For `slides`, stop before this
manager-oriented ranking and perform audience-specific Result Selection in step
6; do not create a complete Brief first. In both modes, do not force a headline
count. Multiple activities may support one change, and one goal may need
multiple changes when they carry distinct meaning. Put every remaining
meaningful stream in the portfolio table. Do not allocate prose by entry count.

### 5. Project the Brief When Requested

Skip for `quick` and `slides`. For `brief`, apply **Brief Projection** in
`references/weekly-analysis-contract.md`: keep only blocks whose removal would
change judgment, action, or confidence in the body; route accountability,
coverage, and provenance to the appendix. Use one expanded home per fact and no
fixed length or item count.

### 6. Build the PPT-ready Markdown Deck

Slides only: follow `references/weekly-slides-contract.md` and
`references/slide-template.md`. Brief and quick skip these files entirely.

### 7. Write

- `quick`: conversation only; see Quick Mode.
- `brief`: use `weekly-brief-template.md`.
- `slides`: use `slide-template.md`; emit only necessary slides, or return an
  evidence-insufficient empty state without a deck file.
- Keep claim-level evidence in the appendix. Main prose must be readable
  without report-local ids.
- Preserve risks, unresolved decisions, and evidence gaps.
- Preserve confirmed versus proposed commitments and inferred versus confirmed
  goals.
- Keep tables, full commitment accounting, portfolio coverage, and provenance
  in the brief appendix. The brief body uses prose and bullets except for each
  admitted Change Explanation Card's Before/After comparison.
- Keep `limited`, conflicting, and expected-only boundaries beside the body
  claim they qualify. Verified provenance can remain in the appendix.
- When evidence is thin or git-only, keep the main narrative short and mark
  `limited` explicitly rather than padding with architecture theater.

## Quick Mode

Triggers: `这周做了啥`, `周报简版`, `quick weekly`, `本周概要`, and clear
equivalents.

Behavior:

1. Resolve week range and scope class with First-Run and Local Fallback.
2. Partition accordingly. Explicit/configured `work` / `personal` still exclude
   unassigned. Implicit unassigned current repo uses `local`.
3. Read raw entries for in-scope projects when a vault exists. Optionally glance
   at git to detect uncovered commits.
4. Do not read `slide-template.md` or build slide candidates, diagrams, or
   implementation narratives.
5. Output 5–7 bullets in the conversation only. Prefer
   `[archetype] summary`-style lines grounded in raw fields; git-only bullets
   stay bounded and `limited`.
6. Append at most three carried-forward lines for open risks or unresolved
   decisions.
7. If no raw entries but meaningful git exists: say evidence is `limited`, list
   at most a few commit-derived bullets without inventing intent, and offer a
   full brief.
8. If no raw and no usable git: empty-state with a short hint to capture or run
   a full brief after more work signal exists.
9. If explicit scope excluded the current unassigned project, say so and point
   to reporting_group setup instead of returning a silent empty list.

Suggested shape:

```markdown
## {YYYY-WNN} 快速回顾（{scope}）

- [decision] …
- [build] …
- [repair] …

**结转**：… · …
```

Do not write vault files in quick mode. A single optional upgrade line is
allowed; do not block on cold-start.

## Coverage

Calculate project coverage as raw entries versus uncovered commits, but put
coverage badges in the appendix or portfolio—not in the headline narrative.

- High: raw explains intent and status.
- Moderate: mixed raw and git-only gaps.
- Low: mostly git-only; narrative is limited.
- None: no usable work signal.

Coverage measures source completeness, not value. Quick mode may mention
coverage in one line; it does not need badges.

## Quality Gate

### Shared (all modes that emit scoped narrative)

- Scope class (explicit / configured / implicit-local) was resolved before
  ranking or bullet selection.
- `work` contains no personal or unassigned titles, paths, commits, artifacts, or refs.
- Local first-run is labeled `local` / unassigned, never presented as safe `work`.
- Explicit scoped emptiness explains exclusion and repair without leaking
  unassigned content into `work`.
- No-vault runs return conversation output without blocking on cold-start.
- Evidence grades and uncertainty are preserved; git-only material stays `limited`.
- Activity volume is never promoted into outcomes.
### Quick only

- Conversation output only; no weekly file write.
- 5–7 bullets, plus at most three carried-forward lines.
- No slide structure, solution-logic diagrams, or implementation narratives.

### Brief only

- Every group has exactly one weekly judgment.
- Every goal states its source, confidence, status, and closure criterion.
- Inferred or unknown goals never use confirmed-goal language.
- Every prior commitment is accounted for; proposals remain proposals.
- Every material change is goal-linked, explicitly unplanned, or in the
  portfolio.
- Replanned work preserves the prior direction, evidence trigger, reason, and
  new direction.
- Every meaningful remaining stream appears in the portfolio.
- Every unresolved risk or next commitment has a concrete closure criterion.
- The body alone reconstructs goal state, actual change, material variance,
  decision or support, next commitment, and confidence boundary.
- Every body block survives counterfactual deletion; full prior-item,
  portfolio, and evidence coverage stays in the appendix.
- The body contains no tables except each admitted Change Explanation Card's
  single Before/After comparison; it contains no source paths, commit lists, or
  evidence index.
- Appendix ledgers and mappings do not repeat body narrative.
- Brief mode does not require diagrams, implementation narratives, or charts.
  It may use one lightweight visual inside an admitted Change Explanation Card;
  simple results remain text-only.

## Anti-Patterns

### All modes

- Flat project or commit list as the overview.
- Cross-group themes in `all` mode.
- Activity volume promoted into outcomes.
- Retrofitting a confirmed Why from completed actions.
- Treating a report proposal as a prior commitment.
- Hiding a prior goal when evidence caused a replan.
- Forcing unrelated projects in one reporting group under a shared goal.
- Keeping a body block whose removal changes neither judgment, action, nor
  confidence.
- Repeating the same narrative in the body and appendix.
- Hiding a blocked/replanned material item, decision request, or evidence
  conflict only in the appendix.
- Hiding work because it did not qualify as a headline (brief/slides) or
  omitting material risks from carried-forward (quick).
- Treating expected impact as an observed result.
- Treating code completion as production acceptance.
- Applying slides-only diagram or implementation-narrative gates to brief or
  quick output.

### Brief and slides

- Evidence ids dominating the spoken narrative.
