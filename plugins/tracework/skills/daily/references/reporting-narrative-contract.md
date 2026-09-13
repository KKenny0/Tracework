# Reporting Narrative Contract

Daily, Weekly and Monthly explain evidence-backed progress and remaining gates.
Reports are human-facing judgments, not substitutes for raw records.

## Scope Before Selection

Before reading report material, run the bundled resolver:

```bash
python <this-skill>/scripts/tracework_raw.py resolve-scope --cwd <project-root> --purpose report
```

Pass `--scope <group-or-all>` only when the user explicitly selected it.
Use the returned `scope`, `scope_source`, and `reason`; do not substitute `work`.
Precedence is explicit user scope → configured `profile.default_reporting_group`
→ current project's group (project config, then matching registry) → unresolved.
Configuration merges project over global values as usual. An unresolved report
returns `scope=local`, `scope_source=implicit-local`: current project only,
conversation output, no files. A named group literally called `local` remains
an exact group when its source is explicit/configured/project.
For Capture Day, use `--purpose session`; unresolved scope is null and must stop
before list/collect or transcript reads. This resolver reads configuration and
registry metadata only; it does not authorize reading other projects.

Partition the resolved scope before ranking work:

- `<group>`: include only projects whose `reporting_group` exactly matches the
  requested group, commonly `work` or `personal`.
- `all`: keep every reporting group, but write a separate judgment and separate
  headline set for each group. Never force a cross-group theme.

Read `reporting_group` from the project-level
`.tracework/config.yaml` `profile.reporting_group`, then from the matching
`raw/projects.json` entry. When neither exists, classify the project as
`unassigned`. Exclude unassigned projects from `work` and `personal` output and
report the missing classification; keep them visibly separate only in `all`.
Never guess that an unassigned project is safe for a scoped report.

Explicit/configured scopes exclude unassigned projects. With no explicit or
configured default, use the current project's assigned group, otherwise only
the current project as an unassigned local lane in conversation. `all` remains
a private combined view with separate judgments and evidence per group.
Personal material must never displace or appear in a work report, even in its
appendix. The headline budget applies per group, never across the vault.

## Effective Facts and State

For each authorized project, run `python <this-skill>/scripts/tracework_state.py
--vault <vault> --slug <slug> --start YYYY-MM-DD --end YYYY-MM-DD`; pass `--as-of`
only for an explicit knowledge cutoff. Use its entries, states, correction
history and diagnostics. It applies corrections before work-period selection
and computes state through period end. Accepted risks stay separate; conflicts
and unassociated old questions stay visible. Do not use raw totals or historical
question lists as current state. Reports never rewrite raw or older reports.
For a material gap, offer Capture Day for one project/date; read sessions only
after that action is selected, through Capture's project-root filter.

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
