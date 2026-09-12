# Reporting Narrative Contract

Use this contract for Tracework daily, weekly, and monthly reports. Reports are
human-facing management-closure views over raw evidence. They are not agent
handoffs, activity inventories, or substitutes for the raw record.

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

`profile.default_reporting_group` selects the default scope when configured.
When a scope is **explicit** (user named `work`, `personal`, or another group)
or **configured** via that default, unassigned projects stay excluded and must
never be guessed into the scoped report.

When no explicit group and no configured default are present, Daily, Weekly, and Monthly
use the current project's assigned group when available. Otherwise report
the current unassigned repository as a `local` lane, label
it clearly, and keep workplace audience safety intact. An explicit `all`
request remains the private combined view with separate group sections.

The headline budget applies per reporting group, not across the whole vault.
Personal projects must never displace work projects from a `work` report, and
must never appear anywhere in that report, including evidence appendices.

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
- Use three headline narratives by default. Two to four is acceptable when the
  material genuinely requires it; never truncate a fourth material work stream
  just to satisfy a number.
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
- `recorded`: a clear raw record with provenance but no independent proof.
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
