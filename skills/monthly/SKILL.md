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
- Run `python <this-skill>/scripts/tracework_raw.py resolve-scope --cwd <project-root> --purpose report`
  using the shared reporting contract; add `--scope` only for an explicit user
  choice. Use `scope_source=implicit-local` for conversation-only local fallback.
- For an explicit/configured group, include only matching projects; exclude
  unassigned projects and explain an empty result with a configuration hint.
- `all` remains a private view with separate complete group sections.
- Partition before ranking. Resolve project config before registry metadata,
  as required by the shared reporting contract.
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
  --vault {vault} \
  --month {YYYY-MM} --project-slug <authorized-slug> \
  --signals-output {temporary-directory}/signals.json \
  --skeleton-output {temporary-directory}/skeleton.json
```

The helper performs deterministic extraction, not selection or prose writing.
Repeat `--project-slug` for each authorized in-scope project; pass `--as-of`
only for an explicit knowledge cutoff. Its effective_views carry period-end
states, correction history and diagnostics. Partition editorial context too. It does not grant permission to publish the
unfiltered context. Raw-only input is sufficient. Missing derived indexes and
Daily/Weekly files do not block the review.

If a matching Daily archive exists, optionally pass `--input <archive.md>` for
prior judgments and legacy coverage. Matching Weekly reports are also optional
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
