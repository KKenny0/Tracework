---
name: daily
description: >
  Generate or update workplace-facing daily reports from Tracework raw entries,
  using git only as limited fallback coverage. Supports work, personal, and
  private all-project scopes without mixing audiences. Use for
  "/tracework:daily", "更新日报", "写日报", "日报", "工作日志", "补日报",
  "daily note", or a dated daily work report. Do not use for agent handoff,
  meeting notes, generic prose reports, or git operations.
---

# Tracework Daily

Write a concise daily management-closure view. Answer what changed today, why
it matters, what is now closed or bounded, and the next gate. Do not produce a
module inventory or agent handoff.

## Required References

Read both before writing:

- `references/reporting-narrative-contract.md`: scope partition, closure types,
  headline selection, evidence rules, and audience safety.
- `references/daily-note-writing.md`: source handling, merge rules, vault file
  shape, and conversation / first-run shapes.

## Configuration

Resolve configuration in this order:

1. Project `.tracework/config.yaml`
2. `~/.tracework/config.yaml`

The primary output defaults to `{vault}/Daily Note.md`, overridable through
`daily_note.path`. The shared reader selects projects; `daily_note.repos` restricts Daily only.

If no vault can be resolved, return the report in the conversation. Do not
create an unrequested vault. Do not block on cold-start. Optionally add one
soft upgrade line at the end (see First-Run and Local Fallback).

## First-Run and Local Fallback

Daily must produce value without prior setup. Cold-start is an upgrade for
durable multi-day storage and strict audience partition, not a ticket to try.

### Scope resolution

Use the shared contract's `read-report --report daily` command with the target
dates; add `--scope` only for explicit user choice. Use the returned scope and projects.
An assigned current-project group is a normal exact-group scope;
`scope_source=implicit-local` activates local first-run below.

### Partition rules

- **Explicit or configured** `work` / `personal` / named group:
  - Include only projects whose `reporting_group` exactly matches.
  - Exclude `unassigned` projects. Never treat unassigned as safe `work`.
  - If the result is empty because the current project is unassigned, say so
    clearly, explain that explicit `work` (or the configured default) will not
    invent a group, and tell the user how to fix it:
    `/tracework:cold-start-interview` or set `profile.reporting_group`.
  - Still return a short empty/excluded report rather than failing.

- **Implicit** scope (no explicit group, no configured default):
  - If the current project has a `reporting_group`, use that group.
  - If the resolver returns `scope_source=implicit-local`, enter
    **local first-run**:
    - Report only the current repository.
    - Label scope `local` (unassigned). Do not label it `work`.
    - Use git and any available raw entries for that repo only.
    - Mark evidence `limited` when git-only.
    - Add a one-line hint to set `reporting_group` before workplace-scoped
      reports.
  - If a vault registry lists other assigned projects but the user is in an
    unassigned repo under implicit scope, prefer local first-run for the
    current repo and mention that assigned vault projects were not mixed in.

### No vault

- Always allowed.
- Write nothing to disk.
- Use the conversation output shape in `daily-note-writing.md`.
- End with at most one upgrade line, for example:

  > 可选：配置 knowledge vault 后可跨天累计并写入文件。`/tracework:cold-start-interview`

- Do not imply the report is incomplete solely because vault setup is missing.

### Empty signal

If local first-run has no raw entries, admitted conversation facts, or
meaningful git activity, return a short empty-state: what was checked, that nothing reportable was found, and
that capture or more work signal will improve the next run. Do not error.

## Workflow

1. **Resolve date, scope class, and output target.**
   - Default date: today.
   - Accept a date range and write one section per date.
   - Resolve explicit / configured / implicit scope as above.
   - Choose vault file output only when a vault exists and the resolved lane is
     a normal scoped group (`work` / `personal` / named / `all` sections). Local
     first-run and no-vault runs stay in conversation even if a vault path
     exists, so unassigned content is not written into workplace Daily Note.

2. **Read scoped effective facts.**
   - Run the shared `read-report --report daily` entry for each requested date, with start=end.
   - Use its groups, project views, correction history, states and diagnostics.
   - Apply its failure and write policy before continuing. A partial read returns
     a conversation draft unless saving that incomplete draft was requested.

3. **Prepare evidence.**
   - Prefer factual top-level fields and optional `reporting` boundaries.
   - Artifact dossiers are optional navigation for selected projects only.
   - A null view means no vault; continue with scoped conversation and Git.

4. **Admit current conversation evidence, then check git coverage.**
   - Apply Current Conversation Evidence in the shared contract; scope, date,
     deduplication, and conflict rules apply before synthesis. No capture side effects.
   - Use lightweight commit subject/stat inspection only for work not already
     covered by raw entries.
   - Git-only material is `limited`; do not infer motivation, decisions,
     verified impact, or management meaning that the commit does not support.
   - Filter formatting, generated-bundle, and chore-only noise unless it is a
     recorded risk or release gate.

5. **Synthesize state transitions.**
   - Group entries and fallback commits by coherent work stream.
   - Merge feature/fix/refactor entries that describe one state transition.
   - For each reporting group or the single local lane, write one daily
     judgment and only supported advances; one is enough for sparse evidence.
     Put remaining meaningful work under Other activity. Thin first-run reports may use fewer headlines.
   - Preserve explicit risk, conflict, open question, rejected path, and
     evidence gaps.

6. **Write incrementally or in conversation.**
   - Vault mode: use only `<this-skill>/scripts/update_daily_note.py` with the
     previously read whole-file hash and per-group bodies, as described in
     `daily-note-writing.md`. A conflict returns a conversation draft, never a
     manual overwrite. Do not write an empty date section.
   - No-vault or local first-run conversation mode: use the conversation shape
     in `daily-note-writing.md`. Do not invent a Daily Note path.

## Quality Gate

Before finishing, verify:

- Scope class (explicit / configured / implicit-local) was resolved before
  headline selection.
- A `work` report contains no personal or unassigned material, including
  evidence.
- Local first-run is labeled `local` / unassigned, never presented as a safe
  workplace `work` report.
- Explicit scoped emptiness explains exclusion and repair, and does not leak
  unassigned content into `work`.
- No-vault runs return conversation output without blocking on cold-start.
- Each reporting group or local lane has one clear daily judgment when there is
  signal.
- Headline items describe starting situation, movement, end state, meaning, and
  next gate when evidence supports them; git-only stays bounded.
- Remaining meaningful work is still covered when present.
- `ongoing` and `risk` are not rewritten as completed outcomes.
- The report is readable in about one minute per reporting group.
- Source/evidence boundaries are explicit.

## References

- `references/reporting-narrative-contract.md`
- `references/daily-note-writing.md`
- `references/config-template.yaml`
