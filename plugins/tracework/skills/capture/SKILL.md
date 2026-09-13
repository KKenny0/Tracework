---
name: capture
description: >
  Adaptive-depth session recap and low-friction checkpoint capture for
  report-ready Tracework memory. Use this skill for "/tracework:capture" or when
  the user signals end of a work session, such as "收工", "今天到这", "done",
  "wrap up", "that's it for today", "好了", or "先这样". Also trigger on
  explicit checkpoint or logging requests like "记录变更", "log changes",
  "记一下今天做了什么", "记一下当前进展", or "checkpoint". The skill dynamically
  routes the session to lite, standard, or deep capture depth; explicit
  "/tracework:capture lite|standard|deep" wording overrides that route. Use day
  mode for "/tracework:capture day", "扫描今天的会话", "补录今天", or "capture
  today". Also use for explicit correction of a stored fact ("原记录记错了",
  "更正这条记录"). Do NOT trigger when the user is simply saying goodbye or switching
  topics.
---

# Adaptive-Depth Session Recap

Capture session-end or checkpoint signals into Tracework raw entries. The goal
is not a chronological diary. Preserve the lightest durable work signal that
can improve Daily, Weekly, and Monthly first, then support evidence drill-down,
decision replay, roadmap synthesis, and session-start recall when needed.

Tracework is reporting-first: Daily, Weekly, and Monthly can still produce
direct value without a fresh capture. Capture improves their evidence boundary
and keeps lower-frequency Query, Recall, and Roadmap available when needed.

## Progressive References

Keep this file focused on routing and workflow. Read these references only when
needed:

- `references/capture-routing.md`: choose `capture_depth` and handle explicit
  lite/standard/deep overrides. Read before finalizing entries.
- `references/capture-entry-writing.md`: write raw entries, artifact context,
  reporting metadata, Markdown fallback, and quality checks.
- `references/capture-operations.md`: resolve config, call `tracework_raw.py`,
  write artifact dossiers, and format quiet receipts.
- `references/capture-corrections.md`: explicit correction of a stored fact only.
- `references/capture-day.md`: scan indexed Codex and Claude sessions for one
  date without mixing reporting groups. Read for day mode only.
- `references/tracework-storage-convention.md`: shared schema and storage rules.

## Zero-Config Mode

This skill works with or without a configured knowledge vault:

- With a vault: write entries to
  `{vault}/raw/weeks/{ISO-week}/{project-slug}.json`; write artifact dossiers
  to `{vault}/raw/artifacts/{project-slug}.json` only when the routed capture
  depth and session signal justify it. Keep output quiet by default.
- Without a vault: return structured Markdown in the conversation. Do not write
  files or create directories. Add a one-line setup hint.

Zero-config mode is best-effort. Fill fields that are supported by the
conversation and local evidence, but do not interrogate the user just to enrich
optional fields.

## Workflow

1. **Detect mode and depth.**
   - For a mistaken stored fact, follow `references/capture-corrections.md`.
     Wording edits change reports only; later real changes use lifecycle_transition.
   - Default mode is session-end capture.
   - Use checkpoint mode for "checkpoint", "记一下当前进展", or
     `/tracework:capture checkpoint`.
   - Use day mode for `/tracework:capture day [YYYY-MM-DD] [scope]` or its
     natural-language triggers. Read `references/capture-day.md` and follow it
     instead of extracting only the current conversation.
   - Read `references/capture-routing.md`, then choose one session-level
     `capture_depth`: `lite`, `standard`, or `deep`.
   - Respect explicit depth overrides such as `/tracework:capture deep` or
     "简单记一下". If no override exists, route from the session evidence.

2. **Extract signals.**
   - Read `references/capture-entry-writing.md`.
   - Classify the primary archetype: `decision`, `repair`, `investigation`,
     `build`, or `maintenance`.
   - Extract only durable signals: goal, state change, decision/trade-off,
     rejected path, risk, evidence boundary, artifact context, and next useful
     action.
   - Group related work into 1-3 entries. Use at most 5 entries for unusually
     broad sessions.
   - For normal session-end or checkpoint capture, resolve one immutable
     committed-tree snapshot for code-backed entries as described in
     `references/capture-entry-writing.md`. Never backfill Capture Day with the
     repository's current `HEAD`.

3. **Generate raw entries.**
   - Include `capture_depth` on every new `session-recap` entry.
   - Add the minimal `reporting` object only when the report boundary is clear.
     Keep `work_stream` at the top level and do not pre-write channel-specific
     Daily/Weekly/Monthly carry-forward prose.
   - Add `artifact_context` and artifact dossier side effects only when the
     session materially changed durable artifacts or routed to `deep`.
   - For a durable design or architecture artifact, preserve a compact
     recoverable digest in existing entry and dossier fields: why it exists,
     its goal, final choice and shortest rationale, core objects and
     relationships, material path or fallback, current-versus-target boundary,
     and remaining gate. Do not copy the full document.
   - When a local design source moved to a cloud document, keep the last local
     path for provenance and add a typed `doc` source ref with the stable URL
     and document or revision id when known.
   - Do not assign report-local `O#`, `W#`, `D#`, or `E#` labels.

4. **Write or fallback.**
   - Read `references/capture-operations.md`.
   - Use `tracework_raw.py append-entry` as the canonical write path.
   - Upsert artifact dossiers when warranted and enabled.
   - Register the project as a best-effort side effect.
   - If config or helper calls fail, return the Markdown recap instead of
     blocking the user.

## Output Policy

Vault mode returns a concise confirmation plus a capture receipt from
`references/capture-operations.md`. Include:

- chosen depth and one short routing reason;
- the top durable summary;
- non-zero risk / open-question / abandoned-alternative counts only;
- one forward-looking line that connects this capture to later Daily/Weekly
  reports (for example that it can enter this week's report candidates).
- when a `source_required` artifact has no durable locator, one explicit warning
  that deleting its only local copy will prevent exact design reconstruction.

Keep the default vault reply about six lines or fewer. Do not dump transcript
bodies or long recaps unless verbose mode is requested.

Day mode returns one aggregate scan receipt. Never echo transcript bodies or
paths. List only counts, project names, and explicit skip reasons.

Verbose output is opt-in. Treat "verbose", "show recap", "展开总结", or an
explicit request to inspect the recap as permission to include the Markdown
recap after the receipt.

Zero-config mode is always verbose because the conversation output is the only
deliverable. It does not need the short vault receipt; keep the existing
one-line setup hint after the Markdown recap.

## Quality Gate

Before finalizing each entry, check:

- Does the entry explain why the work mattered, not just what files changed?
- Is `capture_depth` no heavier than the signal deserves?
- Does `status` bound the claim as done, ongoing, risk, or decision?
- Does `reporting.outcome_candidate.kind`, when present, avoid overstating the
  evidence?
- Can Daily, Weekly, and Monthly recover the state change and next gate from
  factual fields without relying on pre-written channel prose?
- Are git, files, docs, and logs treated as evidence or coverage rather than
  outcomes by themselves?
- Does every visible commit `source_refs` item include the repository root in
  `path` when that root is known?
- Does every `repository_snapshot` use the full committed `HEAD` object id and
  absolute repository root, without implying that uncommitted work is included?
- Are durable artifacts represented through `artifact_context` or dossier
  metadata only when they are material?
- If an artifact is `source_required`, is there a durable commit, path, or
  remote document locator? If not, warn that deleting the only local copy will
  prevent later reconstruction of exact architecture or design mechanics.
- For checkpoint mode, is this a durable stage signal rather than a progress
  log?

Before finalizing vault-mode user output, also check:

- Does the receipt include a top summary grounded in the written entries?
- Are zero counts omitted rather than shown as "0 个"?
- Is there exactly one forward-looking report line (candidate for weekly/daily,
  or checkpoint "已记入本周证据")?
- Is the default reply short and quiet unless verbose was requested?

## Anti-Patterns

- Do not fabricate fields to satisfy the schema.
- Do not ask confirmation questions just to enrich optional fields.
- Do not preserve process noise that would never appear in a daily or weekly
  review.
- Do not use checkpoint mode to record command-by-command progress.
- Do not scan host-wide transcript directories directly; day mode reads only
  manifests created by the opt-in Tracework hook.
- Do not read a transcript until its project and reporting group pass scope
  classification.
- Do not split one coherent feature across many entries.
- Do not write new entries with `source: "arch-doc"`; that source is
  legacy-only.
- Do not generate formal Stage/Pipeline architecture documents from this skill.
