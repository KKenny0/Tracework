# Reporting Narrative Contract

Daily, Weekly and Monthly explain evidence-backed progress and remaining gates.
Reports are human-facing judgments, not substitutes for raw records.

## Scope Before Selection

Read scoped facts through the shared entry:

```bash
python <this-skill>/scripts/tracework_raw.py read-report --cwd <project-root> \
  --report <daily|weekly|monthly> --start YYYY-MM-DD --end YYYY-MM-DD
```

Monthly calls the same reader. Pass `--scope <group-or-all>`
only for explicit user choice, repeat `--project-slug` to narrow projects, and
pass `--as-of` only for an explicit knowledge cutoff. Filters only narrow scope. Use returned `scope`, `scope_source`, `reason`, `groups` and failures;
do not reconstruct the selection or read excluded projects through another path.

Scope precedence: explicit user choice → configured `profile.default_reporting_group`
→ current project's group → implicit-local. Project config overrides global
settings. Implicit-local means current project only, conversation only, no files.
An explicitly named `local` group remains an exact group, not this fallback.

The reader selects from registry metadata and raw filenames, plus the current
project. Only Daily applies `daily_note.repos` when configured. Each project's
config group overrides registry group; missing classification is `unassigned`.
Exact-group reports exclude unassigned and other groups. `all` keeps groups
separate, including unassigned; never rank or write a common judgment across them.
Duplicate ownership or unreadable metadata stops the affected project's reads.
Excluded/ambiguous projects are counted without exposing names, paths or refs.
Only selected projects in `groups` may supply Git, conversation or editorial
material; skills still handle those sources and audience partition themselves.

## Effective Facts, Failures and Output

Each selected project carries a `view` from `tracework_state.py`: effective
entries, period-end states, correction history and diagnostics. Corrections
apply before period selection. Accepted risks, conflicts and unassociated old
questions stay visible; raw totals and historical questions are not current state.
A null view means no vault; continue from scoped conversation and Git evidence.
An empty view is valid absence of records, not a read failure.

`status=partial` means coverage is incomplete: use surviving projects for a
conversation draft, disclose failures, and make no whole-scope conclusion.
`write_policy=explicit_save_only` permits saving only after an explicit request
to save this incomplete draft; ordinary report generation is not that request.
Existing-file protections still apply. `conversation_only` (no vault, local or
blocked metadata) writes nothing. `status=blocked` reads no raw; explain the
metadata problem. Never bypass errors with direct raw or Git fallback for the
failed project. Complete scoped reports keep their output policy.

Reading reports never captures, registers projects, edits raw or advances scan
watermarks. For a material gap, offer Capture Day for one project/date; use its
project-root filter only after recovery is explicitly selected.

## Current Conversation Evidence

Daily, Weekly, and Monthly may report directly from facts already visible in
this task. Admit a fact only when its project, reporting group (or resolved
local lane), and work date fall within the resolved scope and period. Unknown
project/date stays outside claims; do not infer a work date from message time.
Use this temporary evidence alongside raw, before ranking and git fallback.
No Capture call, raw write, project registration, transcript search, or scan
watermark update is implied. Unsaved conversation facts are not durable memory.

Deduplicate by exact entry ref, repository plus commit, or existing message
reference first. Without an exact identifier, merge only the same state change
in the same project and period; retain distinct acceptance gates and conflicts.
Repeated assistant descriptions are one source, not independent verification.
Use actual available refs; when absent say current visible conversation and do
not invent message IDs. A clear recorded decision can support decision closure
without a commit. Self-reported completion is recorded, not verified; direct
visible test/tool evidence supports only the specific check it demonstrates.
Raw/conversation disagreement remains visible with both sources and a limited
boundary; do not silently overwrite raw or pick the more optimistic claim.
Apply audience partition to the evidence appendix as well as the body.

## Shared Narrative Spine

Every headline narrative should explain:

1. **Starting situation**: the goal, constraint, risk, or uncertainty at the
   start of the period.
2. **Decisive movement**: the action, choice, experiment, or repair that changed
   the situation.
3. **End state**: what is observably different now.
4. **Management meaning**: why the change matters to the intended reader.
5. **Closure boundary**: what is closed, what remains open, and the next gate.

Do not promote implementation volume into narrative importance. Commits, files,
line counts, tokens, and active days are evidence or coverage metadata.

## Closure Types

- `delivery`: a deliverable or usable state now exists.
- `decision`: a direction is chosen and alternatives are bounded.
- `risk`: the root cause or risk boundary is known even if remediation remains.
- `learning`: evidence ruled out or narrowed a path and changes what happens next.

Completion is not the only valid closure. Ongoing work can be report-worthy
when the uncertainty, decision, or next gate is clear.

## Selection and Coverage

For each reporting group:

- Write one period judgment.
- Use only as many headlines as the evidence supports; one meaningful change
  is enough for sparse input. Never pad or truncate material work to meet a count.
- Put every remaining meaningful stream in a portfolio or other-activity
  section. Coverage is not the same as headline prominence.
- Keep risks and unresolved decisions visible even when they do not support a
  success headline.

Rank headline candidates by end-state significance, management relevance,
evidence strength, and effect on the next planning decision. Do not rank by
entry count or commit volume.

## Evidence Boundary

Use the existing evidence grades:

- `verified`: a recorded claim plus direct independent evidence that supports
  its actual wording.
- `recorded`: a clear raw or admitted conversation record without independent proof.
- `limited`: fallback, inference, conflict, or semantically incomplete input.

Main prose should remain readable without report-local ids. Put `O#`, `W#`,
`D#`, and `E#` in a compact evidence appendix when claim-level drill-down is
useful. A source reference proves where something was recorded, not that the
recorded effect was independently verified.

## Audience Safety

- `work` output must contain no personal or unassigned project titles,
  summaries, paths, commits, artifacts, or evidence refs.
- `personal` output must contain no work-project material unless the user
  explicitly requests a combined private view.
- `all` output is private by default and must visibly separate groups.
- When scope is ambiguous and mixed groups exist, prefer the configured default;
  otherwise produce separate group sections rather than mixing them. Never use
  an unassigned project in a scoped report merely to avoid an empty result.
