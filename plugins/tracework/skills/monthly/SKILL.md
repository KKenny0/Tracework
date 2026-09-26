---
name: monthly
description: >
  Generate a raw-first monthly management review, using Daily and Weekly reports
  as prior human judgments rather than semantic truth. Supports work, personal,
  and private all-project scopes. Use for "/tracework:monthly", "月报",
  "月度总结", "月度回顾", "monthly review", or monthly Daily Note archiving.
  Do not use for performance packaging or unsupported value claims.
---

# Tracework Monthly

Write a phase-level judgment: what state changed this month, which outcomes or
decisions matter, which risks repeated, and what next month should close. Raw
entries are the semantic source. Daily and Weekly are editorial context and
coverage, not stronger evidence.

## Required References

Read:

- `references/reporting-narrative-contract.md`
- `references/daily-note-format.md` only when Daily input exists or archiving is requested
- `references/worklog-summary-template.md`
- `references/project-tagging-guide.md` when Daily project labels are ambiguous
- `references/tracework-storage-convention.md` only when resolving storage/schema details

## Inputs and Outputs

Resolve `{vault}` from project then global `.tracework/config.yaml`.

Inputs:

- `{vault}/raw/weeks/` entries matching the target month: semantic source.
- `{vault}/Daily Note.md`: daily judgments, date index, and legacy coverage.
- Matching `{vault}/Work Diary/Weekly/*.md`: optional prior prioritization hints.

Outputs:

- Optional Daily archive: `{vault}/Work Diary/Monthly/{YYYY-MM}.md`
- Signals: `{vault}/raw/months/{YYYY-MM}/signals.json`
- Skeleton: `{vault}/raw/months/{YYYY-MM}/skeleton.json`
- Review: `{vault}/Work Diary/Monthly/{YYYY-MM}.summary.md`

## Workflow

### 1. Resolve Month, Scope, and Output

- Parse the requested month; default to the current month through today.
- The preparation helper uses shared `read-report --report monthly` selection.
  Pass `--cwd` for the current project; add `--scope` only for explicit user
  choice. Use returned scope and groups, not a separately inferred project list.
- Exact groups exclude unassigned projects; `all` keeps separate group sections.
- Without a vault, or in implicit local mode, return the review in conversation
  and write no files. Do not require cold-start or a Daily archive. Use scoped
  conversation evidence and lightweight git coverage; git-only remains `limited`.
- With no meaningful signal, return what was checked and the evidence gap;
  do not invent phase results, next-month targets, or empty output files.

### 2. Build Raw-First Context

Admit scoped current conversation facts using the shared contract, including
deduplication and conflict boundaries. Keep them temporary alongside helper
output; do not capture or modify raw to make them reportable.

With a vault, collect matching raw entries whether or not Daily/Weekly exist:

```bash
python <this-skill>/scripts/prepare_monthly_data.py \
  --cwd <project-root> --vault {vault} \
  --month {YYYY-MM} \
  --signals-output {temporary-directory}/signals.json \
  --skeleton-output {temporary-directory}/skeleton.json
```

The helper selects projects before reading raw and performs deterministic
extraction, not prose writing. Optional `--project-slug` only narrows scope;
Daily's repo list does not affect Monthly. Pass `--as-of` only for an explicit
knowledge cutoff and `--end YYYY-MM-DD` for a month-to-date review.
Signals contain raw_entries once, effective_views without duplicated entry bodies,
and scoped editorial_context. The skeleton indexes those arrays by project slug;
raw_work_streams use explicit work_stream fields or the project slug fallback.
The helper does not rank outcomes or infer phases from repetition. Summary mode
changes presentation only. effective_views retain period-end states, corrections,
conflicts and diagnostics, including carried states without current-month entries.
`report_context` carries selection status and write policy. Partial coverage
returns JSON to the conversation without writing either output. Use `--save-draft`
only for an explicit request to save that incomplete context; use `--overwrite`
only for an explicit update of existing outputs. No-vault/local/blocked runs
never write files, even with these flags. Apply the same policy to the review.
Raw-only input is sufficient; Daily/Weekly files are optional.

If a matching Daily archive exists, optionally pass `--input <archive.md>` for
prior judgments and legacy coverage. Managed Daily blocks require matching group,
valid body hash, and an in-period date. Project-narrowed or local runs exclude
whole-group prose. Legacy blocks require an exact selected project slug label;
display names, unknown labels and ambiguous ownership are excluded with counts
only. Editorial text never supplies verified completion, risks or next actions.
Daily-only evidence supports a limited review; compare it with raw when present
and retain disagreements as editorial conflicts. Matching Weekly reports are also optional
editorial context. Their absence does not lower a raw claim's evidence grade.

For a normal scoped vault run, save only the in-scope context to the configured
signals/skeleton paths when useful. Never overwrite another scope's existing
output without an explicit update request; use a scope-suffixed file instead.
Local/no-vault runs keep analysis temporary and return conversation output.

### 3. Archive Daily Note Only When Requested

Monthly review does not require archiving. If the user requests monthly Daily
Note archiving, run `<this-skill>/scripts/split_daily_note.py` with `--month-filter YYYY-MM`.
Preserve source text and respect the configured overwrite policy. If Daily Note
is missing, explain that no archive was created and continue the review from raw.
Do not manufacture a blank archive to satisfy the context helper.

### 4. Write the Review

Use effective raw entries for claims and effective_views.states for current
risks/questions. Separate accepted risks, retain conflicts and unassociated
questions, and preserve correction history and diagnostics. Use Daily judgments and matching Weekly reports to understand what was
previously emphasized, but never let a repeated Daily phrase override a later
raw status.

For each reporting group:

- Write one monthly judgment.
- Select supported phase-result arcs; one is enough for sparse evidence.
- Keep all remaining meaningful projects in the portfolio.
- Surface only recurring risks supported by repeated timestamps, explicit
  recurrence metadata, or an unresolved risk carried across periods.
- Write only supported next-month closure targets; do not pad.
- Put evidence and activity metadata in appendices.

`all` is a private combined review with separate complete sections per group.
Never rank work and personal projects together.

### 5. Report Execution

Return actual output paths (or conversation-only), selected scope, raw coverage, Daily-only coverage,
warnings, and whether existing files were overwritten.

## Conflict Rules

- Later raw state supersedes earlier raw state when the lifecycle/thread match
  is explicit.
- Daily/raw disagreement remains visible and lowers confidence.
- Git-only or Daily-only material is `limited`.
- Repetition across days does not prove importance or completion.
- Artifact dossiers provide navigation and recorded scope, not independent
  verification unless direct evidence is present.

## Quality Gate

- Scope partition happened before selection.
- Raw-only input works without Daily/Weekly or derived indexes.
- No-vault/local runs write nothing; empty evidence produces a short empty state.
- Work output contains no personal or unassigned material, including appendices.
- Raw entries are the semantic source whenever available.
- Every group has one monthly judgment and only supported phase arcs.
- Portfolio coverage preserves meaningful non-headline work.
- Recurring risks have actual repeated or carried evidence.
- Next-month targets name closure gates, not every task.
- Candidate Rules appear only when explicitly requested.
- Main review is roughly 40-80 lines per group, excluding appendices.
- Activity counts never substantiate outcomes.
