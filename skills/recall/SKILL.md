---
name: recall
description: >
  Recall recent project memory at the start of an agentic coding session. Use
  this skill for "/tracework:recall", when the user says "开工", "session start",
  "start session", "recall context", "继续上次", "接着做", or asks what to
  remember before implementing in the current repo. Intra-project only; does
  not do cross-project retrieval.
---

# Session Start Recall

This skill prepares a bounded project context at the start of a session so the
developer and AI do not restart from zero. It is useful when durable Tracework
memory exists; it is not required before daily, weekly, monthly, or query can
produce their best available output.

Recall is a durable-memory surface, not a report fallback. Unlike daily or
weekly reports, it must not use git history to invent missing memory.

## Effective Facts

Use the bundled helper's effective facts, correction_history, states and
diagnostics. `--as-of` selects an explicit knowledge cutoff; `--end` bounds
lifecycle state by work date. Query/Roadmap also accept `--start`. Do not restore
retracted facts or close questions from similar wording. Accepted risks remain
separate from mitigated risks. Missing captured_at limits exact as-of replay.
Old reports are not rewritten; refresh a requested report through its writer.

## Scope

- Intra-project only.
- Raw entries are the semantic source of truth.
- Artifact dossier entries are optional source navigation plus recorded context.
- Decision context entries are optional synthesized decision-replay hints from
  `{vault}/raw/decisions/{project-slug}.json`.
- If the saved decision index is missing, invalid, empty, or older than the raw
  entries, the helper refreshes the derived decision index from raw entries as a
  best-effort side effect, then uses that fresh Decision Context.
- Do not use git commits as fallback in v1.
- Do not invent history when no vault data exists.

## Workflow

### Pre-Check: Vault Health

Before running the recall helper, do a quick health check:

1. Resolve vault path from config
2. Check if `{vault}/raw/weeks/` has any `{slug}.json` files
3. If no raw entries exist at all: suggest `/tracework:capture` and stop
4. If raw entries exist but are older than 14 days: note staleness in output
5. If `recall_context.py` is missing: warn and suggest re-install

If the pre-check passes, continue to the main workflow:

1. Resolve the current project context.
2. Run the helper:

```bash
python <this-skill>/scripts/recall_context.py --cwd "$PWD" --limit 12
```

If the user explicitly names a project slug, pass `--slug <slug>`. If the user
or config provides a vault path, pass `--vault <path>`.

3. Read `references/recall-output-template.md`.
4. Produce Markdown in the conversation.

## Output Contract

The response must include:

- Recent progress
- Relevant decisions
- Decision Context, when `{vault}/raw/decisions/{project-slug}.json` exists
  or can be rebuilt in memory from raw entries
- Abandoned alternatives that may affect the current task
- Open questions
- Risks to check before implementation
- Repo-local docs worth reading
- Potentially stale intent artifacts
- Suggested entry point for the current session

If there is no vault or no raw data, say that Tracework has no durable memory for the
current project yet, suggest using `/tracework:capture` after this session, and
suggest `/tracework:cold-start-interview` if no config exists. Do not fill the gap
with git history or assumptions.

## Evidence Rules

- Cite raw entry timestamps for decisions, risks, abandoned alternatives, and
  open questions.
- Cite artifact ids for docs worth reading.
- Cite decision context `source_entry_refs` when using `decision_context`;
  preserve `confidence` and `inference_notes` instead of presenting inferred
  nodes as fact.
- Treat artifact dossiers as independently readable but not independently
  authoritative. `artifact_summary` can explain scope and recorded context;
  direct evidence still comes from raw entries, `evidence_refs`, typed
  `source_refs`, or source-of-truth artifact references.
- Include `decision_context_source` when present, especially if `rebuilt=true`,
  so the user can see whether the section came from a saved index or an
  in-memory freshness rebuild.
- Treat `intent_artifact_flags` as read-only staleness hints. Phrase them as
  "may need review" rather than facts. Do not write or propose diffs from this
  skill.
- Use "Inferred" wording when the helper returns weak or old-schema entries.
- Missing artifact dossier index is acceptable and must not block output.

## Storage

This skill reads:

- `{vault}/raw/weeks/{YYYY-WNN}/{project-slug}.json`
- `{vault}/raw/artifacts/{project-slug}.json` when present
- `{vault}/raw/decisions/{project-slug}.json` when present

This skill writes `{vault}/raw/decisions/{project-slug}.json` only when the
derived decision index is missing, invalid, empty, or older than raw entries.
Raw entries remain the source of truth.

## Artifact Discovery

The artifact dossier index at `{vault}/raw/artifacts/{slug}.json` is a
structured catalog of durable project documents plus recorded context. When
present, use it to enrich the recall output:

1. **Find related docs**: When raw entries mention `related_docs` or
   `artifact_context`, cross-reference the artifact dossier index for topic tags,
   decision threads, and `artifact_summary.scope` to find adjacent documents.
2. **Detect stale documents**: Artifacts with `status: superseded` or a
   `superseded_by` field indicate documents that have been replaced — flag these
   so the next session doesn't rely on outdated references.
3. **Navigate by topic**: Artifact `topics`, `decision_threads`, and
   `artifact_summary.key_claims` provide stable retrieval terms for finding
   documents relevant to the current session.
4. **Respect availability**: Use `source_availability`, `last_seen`, and
   `deletion_behavior` to show whether the source document can still be opened
   and whether the dossier remains useful if it cannot.

In the "Docs worth reading" section, include for each artifact:
- Why the artifact matters (from `artifact_summary.scope`, `topics`, or recorded
  raw `artifact_context.scope`)
- Whether it is still active (from `status`)
- Source availability and deletion behavior when present
- Evidence boundary for any key claim when present

Missing artifact dossier index is acceptable — the recall output must not depend on it.
When absent, derive doc references from raw entry fields alone.

## Absorbed Intent-Artifact Flagging

The old standalone intent-sync behavior is now a lightweight recall section.
When recent raw entries include `sync_suggestions`, or mention intent artifacts
and contract-like terms such as design, plan, architecture, prompt, schema,
contract, migration, or config, include a "Potentially stale intent artifacts"
section.

This section is read-only. Its job is to tell the next session what to inspect,
not to decide that a document is stale and not to modify the document.
