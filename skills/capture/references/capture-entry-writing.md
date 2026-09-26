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

Extract in this order:

- motivation: the explicitly stated problem, goal, or constraint; preserve the
  intended state change before describing activity
- changed state: capability, fix, refactor, decision, risk, or progress
- reporting boundary: outcome, progress, or activity; impact and evidence
  boundary
- evidence: raw source refs, commits, evals, docs, source-of-truth artifacts
- decisions and trade-offs: chosen path, rejected alternatives, deferred
  choices
- open questions and risks
- artifact context: durable artifacts materially created or changed

When already stated in the session, preserve what should change in `motivation`
and the pass/fail acceptance gate in `context` or `open_questions`. Keep a next
step proposed unless the user explicitly committed to it. Do not ask for optional
fields or invent a goal from completed actions.

Skip process-only noise unless it explains a larger report-worthy signal.

## Raw Entry Shape

Follow `references/tracework-storage-convention.md`. New entries should use:

```json
{
  "timestamp": "Work time in ISO 8601; source timestamp for historical --date recovery",
  "capture_depth": "lite | standard | deep",
  "archetype": "decision | build | investigation | repair | maintenance",
  "type": "feature | fix | refactor | decision | risk",
  "summary": "1 factual sentence at the boundary reached",
  "context": "1-2 sentences explaining why and impact",
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
