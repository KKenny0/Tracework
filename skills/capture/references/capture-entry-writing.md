# Capture Entry Writing

Use this reference after choosing `capture_depth`.

## Archetype

Choose one primary archetype:

1. `decision`: chose between approaches or clarified a trade-off
2. `repair`: fixed a bug, regression, or reliability issue
3. `investigation`: explored without shipping a fix or feature
4. `build`: shipped or meaningfully advanced a capability
5. `maintenance`: low-risk cleanup, docs, config, or routine support work

If multiple archetypes apply, choose the strongest durable signal. A fix after
exploration is usually `repair`; a feature that mainly records a design choice
is usually `decision`.

## Signal Extraction

Extract only facts and decisions supported by the session. First make a private
checklist of material facts: the goal, final choice and rationale, important
rejected paths, scope and quotas, results with their comparison basis, and
unresolved implementation, approval, release, or acceptance boundaries. Keep
reported evidence distinct from what was directly checked. This checklist is a
drafting aid, not an additional raw field or a user-facing step.

Then organize the work into a short explanation: the problem or goal, the key
cause or constraint, the chosen action and its reason, the observed result, and
the remaining gate.
Ask who acted on what, what the action did, and what changed. Draft those
relationships in ordinary project language before introducing internal labels.
These are drafting questions, not a required visible template.
Use the parts actually present in the source; missing reasons stay unknown.
Chronology alone does not establish causality.

Keep a material change of direction and why it happened. For example, when a
first approach fails and the session changes course, retain the evidence that
changed the choice. A checkpoint needs just enough earlier context to explain
its new result; it need not repeat the whole session.

Then distribute that explanation across the existing fields:

- `summary`: the concrete change or finding and the boundary reached
- `context`: the problem and the shortest causal explanation needed to
  understand the change
- `motivation`: why the work was needed, when that adds to `context`
- `impact`: the supported consequence, distinguishing observed from expected
- `exploration_paths` and `abandoned_alternatives`: material attempts, results,
  and choices with their reasons
- `open_questions`: the remaining decision, evidence gap, or next useful action
- evidence and artifact fields: locators and the detail needed to inspect claims

When stated in the session, preserve the intended state change and acceptance
gate. Keep a next step proposed unless the user explicitly committed to it.
Optional fields do not require invented goals or additional questioning.
Skip process-only noise unless it explains the durable signal.

## Standalone Explanation

Write for a colleague who knows the project but did not attend the session.
They should understand `summary` and `context` without opening a transcript,
following evidence links, or decoding implementation names. These fields orient
the reader; the rest of the entry supplies the decision and evidence detail.

- Describe who or what did what and what happened. Explain a necessary term on
  first use through its behavior, then use that term consistently. A validator
  name or an internal label is not an explanation of what it checks or changes.
  Replace plan-item numbers with the task they refer to when the source states
  that task; otherwise preserve the missing context as a limit.
- Put the key cause beside its consequence. Preserve conditions, uncertainty,
  and whether the explanation was observed, hypothesized, or only proposed.
- Keep the current decision or implementation status and acceptance-blocking
  limits beside the main result. When a local success leaves the overall goal
  unproven, state both together instead of hiding the limit in `open_questions`.
- Keep file counts, version strings, hashes, and error codes in evidence or
  exploration fields unless a specific identifier is needed to distinguish
  the subject. Explain such identifiers when they are needed in the main text.
  Moving detail must not erase a material scope limit, request quota,
  comparison basis, or implementation boundary.
- Let each field add information. Present detailed evidence or numerical
  comparisons once in the most suitable field. A short completion qualifier
  may recur where needed; repeating the narrative obscures the result.
- Use short sentences rather than packing several mechanisms and caveats into
  one sentence. `deep` adds supported reasoning and trade-offs, not a longer
  inventory of commands, files, and checks.

For example, a session might establish that one malformed import row caused a
whole batch to be rejected. A locally tested proposal preserves valid rows and
retries only invalid rows, but has not shipped.

Weak summary: "Validated selective repair closure; four-file plan pending."

Useful summary: "A malformed row caused valid import rows to be rejected too;
local tests support retrying only invalid rows, but the change has not shipped."

The context should explain why the whole batch was rejected and why preserving
valid rows is the proposed remedy, using only what the session established.
The test count, validator name, and patch path remain available in the detail
fields. This is an explanation pattern, not a required import workflow.

### Before Writing

Run two separate checks on the drafted entry:

1. **Standalone reading:** using only `summary` and `context`, can a colleague
   state what problem this addressed, what changed or was learned, and why?
   Using the rest of the entry, can they state what the evidence supports and
   what remains unresolved? Rewrite unexplained shorthand or missing links.
2. **Source fidelity:** compare every material fact in the source checklist
   with the whole entry. Preserve the final choice and rationale, material
   rejected alternatives, scope and quotas, numbers with their comparison
   basis, and unresolved implementation, approval, release, or acceptance
   boundaries. Moving detail must not discard it. Distinguish a plan from
   implementation, an offline replay from a new execution, and a reported
   result from an independently checked one. Check causal links back to the
   source; narrow unsupported causality instead of making the story sound
   complete.

Both checks must pass before persistence. Clear prose does not strengthen the
evidence, and a valid JSON object does not prove either quality check passed.

## Raw Entry Shape

Follow `references/tracework-storage-convention.md`. New entries should use:

```json
{
  "timestamp": "Work time in ISO 8601; source timestamp for historical --date recovery",
  "capture_depth": "lite | standard | deep",
  "archetype": "decision | build | investigation | repair | maintenance",
  "type": "feature | fix | refactor | decision | risk",
  "summary": "Concrete change or finding, with the boundary reached",
  "context": "Short problem background and the key supported causal explanation",
  "source": "session-recap",
  "status": "done | ongoing | risk | decision",
  "work_stream": "optional report grouping hint",
  "reporting": {
    "outcome_candidate": {
      "kind": "outcome | progress | activity",
      "statement": "bounded report claim"
    },
    "impact_boundary": "observed | expected | unknown",
    "evidence_boundary": "verified | recorded | limited",
    "evidence_gap": "missing evidence before strengthening the claim"
  },
  "impact": "report-ready user, system, reliability, or workflow impact",
  "evidence_refs": ["commit SHA, issue ID, eval ID, or doc path"],
  "decision_threads": ["stable-decision-thread"],
  "lifecycle_transition": {
    "subject": "decision:stable-decision-thread",
    "from": "proposed",
    "to": "chosen",
    "reason": "why this session changed the lifecycle state"
  },
  "source_refs": [
    {
      "type": "commit | repository_snapshot | issue | eval | doc | conversation | other",
      "ref": "stable source id",
      "path": "/absolute/path/when-local",
      "url": "https://example.com/when-remote",
      "note": "short evidence note"
    }
  ],
  "motivation": "why this work was needed now",
  "exploration_paths": ["approach tried -> observed outcome"],
  "abandoned_alternatives": ["approach rejected -> reason"],
  "open_questions": ["unresolved question or next-session entry point"],
  "root_cause": "repair-only cause",
  "artifact_context": [
    {
      "artifact_path": "/absolute/path/to/artifact",
      "scope": "what this artifact governs",
      "delta": "what changed",
      "open_questions": ["unresolved artifact question"],
      "source_of_truth": ["path/to/implementation", "path/to/tests"]
    }
  ],
  "sync_suggestions": ["Review DESIGN.md because the session changed a contract."]
}
```

## Field Expectations

| Archetype | Expected when known |
|---|---|
| `decision` | `motivation`, `exploration_paths`, `abandoned_alternatives` |
| `build` | `motivation`, `impact` |
| `investigation` | `exploration_paths`, `open_questions` |
| `repair` | `motivation`, `root_cause` |
| `maintenance` | core fields only |

The helper warns on missing adaptive-depth fields but should not reject entries
that lack optional evidence.

### Commit source qualification

When a visible source is a git commit, preserve it as a typed `source_refs`
item. If the repository root is known, include it in `path`; a commit hash alone
is not globally resolvable when Weekly later runs from another project. Capture
does not need to inspect the commit or summarize code to populate this locator.

If the path is unavailable, keep the commit ref without guessing a repository.
Later consumers must degrade to the raw claim instead of treating an
unresolvable commit as code-grounded evidence.

### Repository snapshot qualification

For normal session-end and checkpoint capture, observe the current committed
tree when the entry has a code-backed claim. Use Git's own immutable identifiers:

```bash
git rev-parse --show-toplevel
git rev-parse --verify 'HEAD^{commit}'
```

When both commands succeed, add one `source_refs` item to each code-backed entry:

```json
{
  "type": "repository_snapshot",
  "ref": "full HEAD object id",
  "path": "/absolute/repository/root",
  "note": "Committed tree observed at capture; uncommitted work is not represented."
}
```

Do not inspect or summarize the code merely to create this locator. Do not store
the branch as the locator: branches move, while the captured object id is
immutable. The snapshot proves only the committed tree. It excludes staged,
unstaged, and untracked work even when the session discussed those changes.

Do not add a repository snapshot during Capture Day unless the recovered source
already contains that historical snapshot. Reading today's `HEAD` would
misrepresent the earlier session. Keep the older raw claim and its direct refs
instead.

## Reporting Metadata

Add `reporting` only when the boundary is clear. It is for human
daily/weekly/monthly outputs, not agent handoff.

- `outcome`: recorded state change or deliverable exists.
- `progress`: bounded advancement exists, but completion or independent
  verification is missing.
- `activity`: work happened and should remain visible, but it is not a
  defensible outcome.

Use `impact_boundary` and `evidence_boundary` to prevent later reports from
overstating the claim. Name `evidence_gap` when verification is missing. Do not
store report-local `O#`, `W#`, `D#`, or `E#` labels.

For new entries, keep `work_stream` at the top level. Do not generate
`reporting.module_scope`, nested `reporting.work_stream`, channel-specific
`reporting.carry_forward`, or `reporting.hard_signals`. Their facts already
belong in `work_stream`, `impact`, `open_questions`, `abandoned_alternatives`,
`decision_threads`, and evidence fields. Consumers remain compatible with old
rich reporting objects.

## Fruit Check

Before accepting a report-level claim, ask what observable state changed:
user, product, system, reliability, migration, or workflow. Activity counts,
commits, files touched, tokens, logs, and documents are evidence or inputs; they
are not outcomes.

If no fruit can be stated honestly, narrow the entry to a decision,
investigation, maintenance, or risk signal.

## Artifact Context

Add `artifact_context` only when the session created or materially changed a
durable artifact, such as `DESIGN.md`, `PLAN.md`, `AGENTS.md`, README,
architecture docs, prompt contracts, schema contracts, migration notes, or
checklists.

When `artifact_context` is present and a vault is configured, also upsert an
artifact dossier through `tracework_raw.py upsert-artifact` unless
`artifact_index.enabled` is false. The dossier should include enough
`artifact_summary`, `source_entry_refs`, `last_seen`, `source_availability`,
and `deletion_behavior` for a future agent to understand the artifact boundary.
Do not copy full artifact content into the dossier.

For a design or architecture artifact that may later move or disappear, make
the existing entry and dossier fields a compact recovery aid rather than a
document backup. Preserve the goal or constraint, final choice and shortest
rationale, core objects and relationships, material input/output/path/fallback,
current-versus-target boundary, and remaining gate when known. Use
`motivation`, `summary`, `impact`, `context`, `artifact_context`, and
`artifact_summary`; do not add a second architecture schema. A dossier can
support recorded intent and conceptual boundaries after deletion, but it cannot
reconstruct exact topology or verify every document claim.

When a local document is synchronized to a durable cloud document, keep the
last local path in the dossier and add a typed raw-entry source ref when the
stable locator is known:

```json
{
  "type": "doc",
  "ref": "stable document or revision id",
  "url": "https://example.com/durable-document",
  "note": "Target design; not evidence of current implementation."
}
```

Use `deletion_behavior: "summary_remains_usable"` only when the digest is
enough for later orientation. Use `source_required` when exact architecture,
algorithm, or mechanism still depends on opening the source. If a
`source_required` artifact has no durable path, commit, or remote locator, say
so in the Capture receipt before the user deletes the only local copy.

## Sync Suggestions

Add `sync_suggestions` when decisions, contract changes, prompt/schema changes,
or durable intent artifacts may need human review. A suggestion means "may need
review", not "is stale" and not "apply this diff".

## Markdown Fallback

Use this template in zero-config mode or helper-failure fallback:

```markdown
## Session Recap - {project-dir-name} ({date})

### {type}: {summary}

{context}

**Depth**: {capture_depth}
**Archetype**: {archetype}

{if motivation present:
**动机**: {motivation}
}

{if impact present:
**影响**: {impact}
}

{if reporting present:
**汇报边界**: {outcome_candidate.kind}; impact={impact_boundary}; evidence={evidence_boundary}
}

{if root_cause present:
**根因**: {root_cause}
}

{if exploration_paths present:
**探索路径**:
- {path}
}

{if abandoned_alternatives present:
**放弃的方案**:
- {alternative}
}

{if artifact_context present:
**Artifact context**:
- {artifact_path}: {delta}
}

{if open_questions present:
**开放问题**:
- {question}
}

{if sync_suggestions present:
**需要同步检查**:
- {suggestion}
}
```

After the final entry, append one soft upgrade line (zero-config only):

```text
可选：配置 knowledge vault 后可跨天累计，并在日报、周报和月报 中复用。`/tracework:cold-start-interview`
```

Do not imply capture failed without a vault. The Markdown recap is the
deliverable.
