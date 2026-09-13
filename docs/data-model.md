# Data Model

[Back to README](../README.md)

Tracework data is organized around one source-of-truth rule: raw records stay
raw, and every synthesized view must be traceable back to them. Daily, Weekly,
and Monthly are the primary human-facing views; query, recall, and roadmap are
lower-frequency evidence and recovery views.

## Storage Surfaces

| Surface | Owns | Examples |
|---|---|---|
| Project repo | Artifacts that evolve with implementation | `AGENTS.md`, design docs, prompt contracts, schema contracts |
| Vault raw layer | Machine-readable memory and indexes | `raw/weeks/`, `raw/decisions/`, `raw/artifacts/`, `raw/months/` |
| Vault wiki layer | Human-readable synthesis | `Daily Note.md`, `Work Diary/Weekly/`, `Work Diary/Monthly/` |
| Conversation fallback | Zero-config immediate value | Structured capture recap when no vault is configured |

An opt-in local session index may exist at `~/.tracework/session-index/`. It is
operational metadata, not a vault layer: no transcript content is copied there,
and reports never consume it directly.

## Vault Layout

```text
{vault}/
  raw/
    projects.json
    artifacts/
      {slug}.json
    decisions/
      {slug}.json
    weeks/
      YYYY-WNN/
        {slug}.json
    months/
      YYYY-MM/
        signals.json
        skeleton.json
  Daily Note.md
  Work Diary/
    Weekly/
    Monthly/
```

## Core Flow

```text
/tracework:capture     -> raw/weeks/{week}/{slug}.json
/tracework:capture day -> scoped local session material -> raw/weeks/{week}/{slug}.json
/tracework:query   <- raw/decisions/{slug}.json + raw/weeks/
/tracework:recall  <- raw/weeks/ + raw/artifacts/ + raw/decisions/
/tracework:daily   <- raw/weeks/ + fallback git coverage
/tracework:weekly  <- raw/weeks/ + fallback git coverage
/tracework:monthly <- matching raw entries + Daily/Weekly editorial context
/tracework:roadmap <- raw entries + decision indexes
```

Skills are independently triggered. The shared storage convention lets their
outputs compound.

Daily, weekly, monthly, and query can be useful before capture coverage is
complete. When only git evidence is available, report skills must label the
result as `limited` and avoid inventing motivation, trade-offs, or verified
impact. Capture improves the evidence boundary; it is not a prerequisite for
every report.

## Temporary Reporting Evidence and Daily Updates

Daily, Weekly and Monthly admit already-visible conversation facts with known
project, group and work date. They deduplicate exact entry refs, repository plus
commit or message refs before state-change merging; conflicts stay visible.
Reports do not implicitly invoke Capture, write raw, register projects or update
session scan watermarks. Unsaved conversation facts are not durable memory.

New Daily prose is editorial context for Monthly; legacy field/checkbox formats
remain readable. `skills/daily/scripts/update_daily_note.py` owns one block per
date and exact group, with a body SHA-256 in its marker. It accepts a JSON map of
group bodies and the expected whole-file hash from the draft snapshot. It checks
user edits and concurrent changes before atomic replacement; other blocks and
outside text stay byte-for-byte intact. Conflicts preserve the file and return
the draft. `all` submits separate actual group bodies, never an all block.
An advisory lock serializes this writer; unrelated editors are covered by the
optimistic file check, not a universal filesystem lock.

## Corrections and Period-End State

The shared `references/tracework_state.py` reader resolves one authorized project
at a time. It applies an explicit knowledge cutoff, replacement/withdrawal
chains, and lifecycle state through the report end before selecting work-period
facts. Daily, Weekly, Monthly, Recall, Query and Roadmap use the same view.

A correction contains operation, exact target week/index/timestamp, target hash
and reason. The existing append writer checks the effective tail inside the
weekly-file lock and atomically appends. Replacement is complete, withdrawal is
not a new outcome. Work time stays in the original week; captured_at records
when the correction became known. Explicit as-of excludes later captures;
legacy missing captured_at limits exact historical replay.

Risk subjects keep their logical raw ID. Question subjects persist only when
text and index are unchanged; moved/changed questions get new IDs. Legacy free
names form exact-name chains and never resolve similar raw questions. Accepted
risks are separate, and conflicting transitions remain unresolved conflicts.
Already generated reports stay unchanged until an explicit refresh. After the
first correction, retain correction-aware readers and fix forward rather than
downgrading. No history migration or raw-array rewriting is required.

Report-driven evidence recovery uses a selected project/date and checks
`--project-root` before opening a transcript. A candidate is only a possible
source. Complete the unscanned increment before durable capture/watermark update;
temporary inspection changes neither raw nor watermarks.

## Raw Entries

Raw entries should preserve report-worthy signals:

- goal or state change
- capture depth (`lite`, `standard`, or `deep`) chosen by the capture skill
- report-ready boundary metadata in optional `reporting`
- decision and rationale
- rejected or deferred alternatives
- risk, open question, or follow-up
- artifact or source reference
- evidence boundary

Raw entries are append-only for practical purposes. If a later session changes
a decision, mitigates a risk, or invalidates an artifact, write a new entry.
Do not rewrite historical entries for a naming or positioning migration.

`reporting` is optional and additive. New entries keep it minimal: claim kind,
impact boundary, evidence boundary, and evidence gap. Work-stream grouping,
risks, questions, alternatives, and evidence remain in factual top-level fields.
Historical rich reporting objects remain readable. Final `O#`, `W#`, `D#`, and
`E#` ids are report-local and are never stored in raw entries.

`timestamp` is work time; `captured_at` records ingestion time on new entries.
Historical recovery preserves source work time using `--date`; reports group by
work time. Ordinary capture uses the system clock. Existing entries remain valid.

`capture_depth` is also optional and additive. It describes how much detail the
capture skill preserved, not how strong the evidence is.

Code-backed session-end and checkpoint entries may also carry a typed
`repository_snapshot` source reference. Its `ref` is the full immutable Git
`HEAD` object id observed at capture and its `path` is the absolute repository
root. It represents the committed tree only. Weekly may select snapshots whose
entry timestamp and `captured_at` (when present) are within its `as_of` cutoff; it must not reconstruct an older
tree from today's moving branch. Historical entries without snapshots remain
valid and degrade to their direct commit or raw claim.

Capture Day entries use typed conversation `source_refs` with a stable
`session:<runtime>:<session-id>` ref and a `timestamp` watermark. Re-running a
day processes only later material. The transcript pointer and body remain local
and are not written into raw entries.

## Artifact Dossiers

`{vault}/raw/artifacts/{slug}.json` stores durable artifact dossiers. A dossier
should be independently readable enough to tell an agent what the artifact
covered, what it did not cover, which claims or decisions matter, what remains
open, when the source was last seen, and whether the original source is still
available.

Dossiers are not independently authoritative. They preserve navigation plus
recorded context; consumers still need raw entries or direct evidence before
presenting a claim as verified. The vault does not store full artifact content
or become a shadow document repository.

## Decision Index

`{vault}/raw/decisions/{slug}.json` is a derived index for query speed and
answerability. Its schema string is `tracework.decision_replay.v1`.

The index must point back to raw evidence through `source_entry_refs`. Those
refs prove where a claim was recorded. They do not, by themselves, prove that
the outcome was independently verified.

## Report-Local Traceability

Weekly and monthly reports can derive local trace ids:

```text
raw evidence -> D# decision/tradeoff -> W# work stream -> O# outcome/progress
O# outcome/progress -> W# stream -> D# decision/tradeoff -> E# evidence
```

These ids belong to the report only. They are not written back into raw schema
and do not require historical data migration.

Evidence levels:

- `verified`: raw record plus independently checkable evidence
- `recorded`: raw record with clear provenance but no independent proof
- `limited`: fallback, inference, conflict, or insufficient support

Commit counts, line counts, task counts, active days, and token counts are
coverage metadata. They cannot become outcomes on their own.

## Reporting Scope

Project config and `raw/projects.json` may carry a `reporting_group`. Reports
partition projects before narrative ranking:

- `work` excludes all personal content, including evidence refs.
- `personal` excludes work content.
- `all` keeps each group in a separate narrative lane.

Headline budgets apply per group. Non-headline work remains in portfolio
coverage rather than disappearing.

## Independent Monthly Input

Monthly reads matching raw entries without requiring Daily Note or an archive.
Daily/Weekly judgments are optional context. Daily archiving runs only when
requested. Without a vault, Monthly returns a bounded conversation review;
implicit unassigned scope remains local, as with Daily and Weekly.
