# Capture Day

Use day mode to recover report-ready facts from locally indexed Codex and
Claude sessions after the user explicitly asks to scan a date.

## Command Contract

```text
/tracework:capture day
/tracework:capture day 2026-07-10
/tracework:capture day 2026-07-10 work
/tracework:capture day 2026-07-10 all
```

- Date defaults to the local calendar date.
- Resolve scope with the bundled helper below: explicit user choice, then
  `profile.default_reporting_group`, then the current project's assigned group.
- If unresolved, explain the missing group and stop without reading transcripts.
- Accept an exact reporting-group name or private `all`.
- `session_scan.enabled` must be `true`; otherwise explain how to opt in and do
  not inspect host transcript directories directly.

## Safety Order

Scope classification must happen before transcript reading. The session helper
uses the hook manifest's `cwd_history` to resolve the nearest project
`.tracework/config.yaml` and its `profile.reporting_group`.

- Exact scope reads only projects in that group.
- `all` may read assigned projects, but still preserves separate project and
  reporting-group lanes.
- Unassigned sessions are skipped.
- Sessions spanning more than one project root or reporting group are skipped
  as `ambiguous_project_or_group`, including in `all`.
- Never recover excluded personal content into a work report, source ref, or
  receipt.
- Cwd classification is the pre-read gate, not permission to mix audiences. If
  normalized content clearly crosses into another project or reporting group,
  skip that material rather than writing it under the indexed project.

## Collect Normalized Material

First resolve scope without reading transcript content:

```bash
python <this-skill>/scripts/tracework_raw.py resolve-scope \
  --cwd <project-root> --purpose session
```

Add `--scope <group-or-all>` only for an explicit user choice. If `scope` is
null, do not call list/collect. Otherwise pass the returned scope explicitly
to both commands (neither has a default). Then list candidate manifests:

```bash
python <this-skill>/scripts/tracework_sessions.py list-day \
  --date YYYY-MM-DD \
  --scope <resolved-scope>
```

Then collect one bounded chunk from each returned session:

```bash
python <this-skill>/scripts/tracework_sessions.py collect-session \
  --date YYYY-MM-DD \
  --scope <resolved-scope> \
  --runtime codex \
  --session-id <id> \
  --chunk 1
```

Read `chunk_count` and request later chunks one at a time. Never request every
session or every chunk in one shell call.

The helper returns only scoped user text and the last assistant text in each
assistant run. It excludes system/developer instructions, tool results,
subagents, injected environment blocks, and unsupported records. Each response
contains at most one 64 KB chunk split at message boundaries.

Treat `missing_transcript`, `unreadable_transcript`, and unknown/empty material
as evidence gaps. Do not guess from filenames or manifest metadata.
If scanning is enabled but no manifests exist, explain that the plugin hook may
be newly enabled, untrusted, or disabled by host policy; keep manual Capture
available and do not fall back to broad home-directory discovery.

## Synthesize Entries

1. Read every returned chunk for one project sequentially before writing.
2. Group related sessions into coherent work streams.
3. Produce normally 1-3 entries per project; use at most 5 for an unusually
   broad day.
4. Apply the existing archetype, adaptive-depth, reporting-boundary, evidence,
   and Fruit Check rules.
5. Transcript claims default to `evidence_boundary: recorded`. Strengthen them
   only when direct repository evidence supports the exact claim.
6. Give every entry all contributing conversation refs:

```json
{
  "type": "conversation",
  "ref": "session:codex:<session-id>",
  "timestamp": "<captured_through timestamp>",
  "note": "Recovered by Capture Day."
}
```

The stable ref plus timestamp is the durable ingestion watermark. Do not store
the transcript path or copy transcript content into the vault.

## Write and Advance Watermarks

Append each project's entries through `tracework_raw.py append-entry` using the
returned `project_root` as `--cwd` and the requested date as `--date YYYY-MM-DD`.
Set each entry's `timestamp` from its latest contributing normalized message on
that date, including timezone. The helper validates that it matches `--date`,
keeps it as work time, and adds `captured_at` from the system clock. Do not use
today's time for historical work. Keep conversation-ref timestamps as ingestion
watermarks, not substitutes for the entry's work time.

Only after that project's append succeeds, advance every contributing session:

```bash
python <this-skill>/scripts/tracework_sessions.py mark-scanned \
  --runtime codex \
  --session-id <id> \
  --date YYYY-MM-DD \
  --through <captured_through>
```

When a reviewed session contains no durable signal, advance its watermark
without writing an empty raw entry. If append or review fails, do not advance
the affected watermark; a later run must be able to retry.

## Receipt

Return only aggregate operational facts, plus one short forward line when any
entries were written:

```text
扫描 7 个 session -> 写入 4 个项目、6 条记录
跳过：1 个已覆盖 · 1 个未分组 · 1 个格式不支持
scope=work · date=2026-07-10
→ 已补入本周证据；需要时运行 /tracework:weekly 或「写周报」
```

If nothing was written, omit the forward line and keep the skip reasons clear.

Do not echo prompts, assistant replies, transcript paths, or personal project
names excluded by scope.

## Targeted Evidence Recovery

When a report proposes recovery for one project and date, wait for the user to
select that action. Pass `--project-root <authorized-root>` to both list-day
and collect-session; collect rechecks canonical project ownership before any
transcript or raw-watermark read. Candidate metadata is only a possible source,
not proof that acceptance evidence exists.

For durable recovery, review the selected session's complete unscanned daily
increment before appending useful signals or marking reviewed/no-signal. A
partial read must not use captured_through to advance the full watermark. For
temporary evidence inspection, neither append raw nor mark-scanned. After a
successful recovery, revise only affected report claims with the report's
normal protected update behavior.
