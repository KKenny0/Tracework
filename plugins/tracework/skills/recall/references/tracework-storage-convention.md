# Tracework Storage Convention (v3.2)

This file defines the shared data schema and storage convention used by all skills in this monorepo. When generating change entries, follow this spec exactly so downstream consumers can reliably read them.

## Configuration

Tracework uses a YAML configuration file to determine the knowledge vault location. The vault is a git repo (typically an Obsidian vault) that stores both raw intermediate data and human-readable outputs.

**Config file locations** (higher priority wins):

| Priority | Location | Scope |
|----------|----------|-------|
| 1 | `{project-root}/.tracework/config.yaml` | Project-level override |
| 2 | `~/.tracework/config.yaml` | Global default |

**Config file format** (see `references/tracework-config-template.yaml` for full template):

```yaml
knowledge_vault: /path/to/your/knowledge-vault
project_slug: my-project  # optional, defaults to git repo directory name

profile:
  project_name: My Project
  reporting_group: work        # project-level: work | personal | another stable group
  default_reporting_group: work # global default report scope
  report_language: mixed   # zh | en | mixed
  weekly_mode: report      # tech | report; brief remains default unless PPT is explicit
  team_context: solo       # solo | team | mixed

artifact_index:
  enabled: true
```

All subsequent path references use `{vault}` as shorthand for the resolved knowledge vault path. Project `profile.reporting_group` and registry `reporting_group` partition report audiences before selection; `profile.default_reporting_group` selects the default scope. Other `profile.*` fields are optional preferences. If a skill's primary output depends on `{vault}` and no path can be resolved, tell the user to run `/tracework:cold-start-interview` or configure `knowledge_vault`. If writing a weekly change entry is only a side effect, skip that write gracefully when `{vault}` cannot be resolved.

## Storage Location

Tracework uses four storage surfaces. Store the full artifact where it is maintained,
then store enough structured metadata for future skills to find and reuse it:

- **Project repo**: code-adjacent artifacts that evolve with implementation,
  such as `DESIGN.md`, `PLAN.md`, `AGENTS.md`, prompt contracts, schema
  contracts, migration notes, and architecture notes.
- **Vault raw layer**: machine-readable memory and indexes, such as weekly raw
  entries, artifact dossier entries, decision thread indexes, open question
  indexes, and monthly signals.
- **Vault wiki layer**: human-readable synthesis outputs, such as daily notes,
  weekly outlines, monthly reviews, and decision roadmaps.
- **Conversation fallback**: zero-config immediate value when no durable storage
  exists, such as Markdown session recap output.

Tracework may also keep a local operational session index at
`~/.tracework/session-index/` when `session_scan.enabled` is explicitly true.
This index is not a fifth storage surface and is not semantic memory. It stores
only runtime, session id, transcript pointer, cwd history, observation times,
and scan watermarks. Transcript content is never copied into it. Capture Day
must partition reporting scope from this metadata before opening a transcript.

Each manifest uses `tracework.session_index.v1` and one file per runtime/session:

```json
{
  "schema_version": "tracework.session_index.v1",
  "runtime": "codex",
  "session_id": "stable-host-session-id",
  "transcript_path": "/local/host/transcript.jsonl",
  "first_seen_at": "2026-07-11T09:00:00+08:00",
  "last_seen_at": "2026-07-11T18:00:00+08:00",
  "cwd_history": [
    {
      "cwd": "/path/to/project",
      "first_seen_at": "2026-07-11T09:00:00+08:00",
      "last_seen_at": "2026-07-11T18:00:00+08:00"
    }
  ],
  "scanned_through": {
    "2026-07-11": "2026-07-11T17:58:00+08:00"
  }
}
```

The index is disposable. Deleting it disables incremental negative-result
watermarks, but positive capture watermarks can still be recovered from raw
entry conversation `source_refs`. Raw entries remain the semantic source.

The knowledge vault itself is organized in two layers following the raw/wiki
pattern:

```
{vault}/
  raw/                            # Raw layer (immutable intermediate data)
    projects.json                 # Optional project registry
    artifacts/
      my-project.json             # Array of durable artifact dossier entries
    decisions/
      my-project.json             # Derived decision replay index for agent queries
    weeks/
      2026-W15/
        my-project.json           # Array of change entries
      2026-W16/
        my-project.json
    months/
      2026-04/
        signals.json              # Monthly extracted signals
        skeleton.json             # Monthly summary skeleton
  Daily Note.md                   # Wiki layer (daily notes)
  Work Diary/                     # Wiki layer (human-readable work outputs)
    Weekly/
      2026-W15.md                 # Weekly brief outline
      2026-W16.md
    Monthly/
      2026-04.md                  # Monthly archive
      2026-04.summary.md          # Monthly summary
```

Weekly brief consumers should write their primary human-readable output to
`{vault}/Work Diary/Weekly/{YYYY-WNN}.md` unless the user or config provides an
explicit output path.

## Decision Replay Index

The decision replay index is a derived, machine-readable view over raw entries.
It exists so coding agents can query why a project chose a path, what was
rejected, and what evidence supports the answer without reading every weekly raw
entry. Raw entries remain the source of truth; the index can be rebuilt from
`{vault}/raw/weeks/` at any time.

Store one project-scoped index at:

```
{vault}/raw/decisions/{slug}.json
```

The file shape is:

```json
{
  "schema_version": "tracework.decision_replay.v1",
  "project_slug": "my-project",
  "generated_at": "2026-05-17T08:00:00+08:00",
  "source": {
    "kind": "roadmap",
    "builder_version": 3,
    "raw_entry_count": 12
  },
  "nodes": [
    {
      "id": "raw:my-project:2026-W20:0",
      "timestamp": "2026-05-17T08:00:00+08:00",
      "week": "2026-W20",
      "confidence": "explicit",
      "source_entry_refs": [
        {
          "week": "2026-W20",
          "path": "/path/to/vault/raw/weeks/2026-W20/my-project.json",
          "timestamp": "2026-05-17T08:00:00+08:00",
          "entry_index": 0,
          "entry_id": "raw:my-project:2026-W20:0"
        }
      ],
      "summary": "Chose a derived decision replay index before adding autonomous capture",
      "decision": "Use a derived decision replay index as the next product layer",
      "why": "Raw entries already contain decision evidence, but agents need a compact queryable evidence pack.",
      "chosen": "Derived index plus recall/query consumption",
      "rejected": [
        {
          "option": "Build a dashboard, sentinel, or capture agent first",
          "reason": "Expands platform surface before decision replay value is proven"
        }
      ],
      "open_questions": [],
      "impact": "Fresh coding agents can recover the reasoning behind past project direction.",
      "decision_threads": ["decision-replay"],
      "lifecycle_transition": {
        "subject": "decision:decision-replay",
        "from": "proposed",
        "to": "chosen",
        "reason": "The derived index gives agents a compact queryable evidence pack."
      },
      "topic_keys": ["decision-replay", "recall"],
      "artifact_refs": [],
      "evidence_refs": [],
      "source_refs": [
        {
          "type": "doc",
          "ref": "decision-replay-plan",
          "path": "/path/to/project/PLAN.md"
        }
      ],
      "thread_id": "thread:decision-replay",
      "inference_notes": []
    }
  ],
  "edges": [
    {
      "from": "raw:my-project:2026-W20:0",
      "to": "raw:my-project:2026-W20:1",
      "type": "same_thread",
      "confidence": "heuristic",
      "reason": "Both nodes share thread:decision-replay"
    }
  ]
}
```

`raw/decisions/` is derived and rebuildable. `source.builder_version`
identifies the deterministic builder semantics; consumers rebuild an older
derived index when this version changes without migrating or rewriting weekly
raw entries. Builder 3 uses `raw:{slug}:{week}:{entry_index}` (original zero-based
JSON-array position), never the sorted node ordinal. Raw arrays are append-only:
do not insert, reorder, or delete existing elements. Backfilling another week or
appending a same-week entry leaves existing ids unchanged. Old reports retain
`source_entry_refs`; no ambiguous mapping from old ordinal ids is fabricated.

`source.input_fingerprint` is SHA-256 over canonical JSON of loaded raw and
artifact inputs. Content edits and artifact changes invalidate the index even
when entry count and timestamps are unchanged. Rebuilds use atomic replacement.
Missing or truncated raw sources preserve the saved index and return unavailable
claims with a diagnostic; they must not overwrite history with an empty index.

### Decision Node Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Stable id within the project index |
| `timestamp` | ISO 8601 | Yes | Timestamp of the source raw entry |
| `week` | string | Yes | ISO week containing the source raw entry |
| `confidence` | enum | Yes | `explicit` when the raw entry has decision fields; `inferred` when derived from summary/context |
| `source_entry_refs` | object[] | Yes | Provenance pointers to the raw entries where the claim was recorded; not independent verification of the claim |
| `summary` | string | Yes | Original raw entry summary |
| `decision` | string | Yes | Decision phrased as a reusable agent-facing statement |
| `why` | string | No | Motivation or reconstructed reason |
| `chosen` | string | No | Chosen path when explicit or inferable |
| `rejected` | object[] | No | Rejected options with reasons, derived from `abandoned_alternatives` |
| `open_questions` | string[] | No | Unresolved questions from the source entry |
| `impact` | string | No | Downstream effect of the decision |
| `decision_threads` | string[] | No | Explicit raw-entry decision threads used before artifact hints or keyword fallback |
| `lifecycle_transition` | object | No | Raw-entry lifecycle transition when this node carries a state change |
| `topic_keys` | string[] | No | Stable retrieval terms for deterministic query helpers |
| `artifact_refs` | string[] | No | Artifact paths or ids touched by the decision |
| `direct_artifact_refs` | string[] | No | Artifact references explicitly recorded under `artifact_context.source_of_truth`; unlike general `artifact_refs`, these can support verification |
| `evidence_refs` | string[] | No | Direct commit, eval, issue, document, or source references supporting the claim |
| `source_refs` | object[] | No | Typed references; conversation and repository_snapshot are provenance, not outcome verification |
| `evidence_boundary` | enum | Yes | `verified`, `recorded`, or `limited`; copied and constrained from raw reporting |
| `impact_boundary` | enum | Yes | `observed`, `expected`, or `unknown`; copied from raw reporting |
| `evidence_gap` | string | No | Remaining verification gap from raw reporting |
| `thread_id` | string | No | Decision thread grouping key |
| `inference_notes` | string[] | No | Notes explaining any inferred decision content |

`source_entry_refs` are mandatory because agents should ground answers in raw
records. They establish provenance, not independent verification. Consumers may
summarize the decision node, but they must not present derived content as
stronger than the node's `confidence`, `inference_notes`, and direct evidence
allow. Explicit legacy entries default to `recorded`; inferred entries to
`limited`. `strong` additionally requires a valid `verified` boundary and
supporting references; impact queries require `observed`. Conversation refs and
repository snapshots alone cannot establish verification. Other references are
support to inspect, not proof that the reader reran validation. General
`artifact_refs` remain navigation hints unless explicitly marked source-of-truth.

### Decision Edges

Edges are optional navigation hints, not facts by themselves. Supported v1 edge
types:

- `same_thread` — nodes share a decision thread or stable topic key
- `supersedes` — a later decision explicitly replaces an earlier one
- `related` — nodes share a meaningful topic or retrieval term
- `touches_artifact` — nodes affect the same durable artifact

Each edge must include `confidence` (`explicit` or `heuristic`) and `reason`.
Consumers should use edges to expand context after retrieval, not as standalone
decision evidence.

## Artifact Index

Raw entries record chronological semantic work signals. Artifact index entries
record durable artifact dossiers: enough context for an agent to understand what
an artifact governed, why it mattered, and where its evidence boundary sits even
if the source document later moves or disappears. Do not overload weekly raw
entries as a document catalog, and do not turn artifact entries into shadow
copies of full documents.

Each `{vault}/raw/artifacts/{slug}.json` file contains a JSON array of artifacts:

```json
[
  {
    "id": "storyboard-pipeline:design-doc:parse-stage:v1",
    "project_slug": "storyboard-pipeline",
    "artifact_type": "design-doc",
    "title": "Parse Stage Implementation",
    "path": "/Users/dev/projects/storyboard-pipeline/docs/2026-W18/stage-parse-implementation-v1.md",
    "repo_relative_path": "docs/2026-W18/stage-parse-implementation-v1.md",
    "created_at": "2026-05-08T10:00:00+08:00",
    "updated_at": "2026-05-08T10:00:00+08:00",
    "source": "capture",
    "topics": ["parse-stage", "validation", "repair-loop"],
    "decision_threads": ["schema-validation-boundary"],
    "open_questions": ["whether repair-loop ownership should move upstream"],
    "evidence_refs": ["doc:stage-parse-implementation-v1"],
    "source_entry_refs": [
      {
        "week": "2026-W18",
        "path": "/path/to/vault/raw/weeks/2026-W18/storyboard-pipeline.json",
        "timestamp": "2026-05-08T10:00:00+08:00",
        "entry_index": 0
      }
    ],
    "artifact_summary": {
      "scope": "Validation-stage contract between parse output, repair loops, and export.",
      "non_scope": "Does not define orchestration-level retry policy.",
      "key_claims": [
        {
          "claim": "Export is a consumer of validated panels, not the repair owner.",
          "evidence_boundary": "recorded_context",
          "evidence_refs": ["doc:stage-parse-implementation-v1"]
        }
      ],
      "key_decisions": ["Keep schema repair inside validation-stage ownership."],
      "open_questions": ["whether repair-loop ownership should move upstream"]
    },
    "last_seen": {
      "at": "2026-05-08T10:00:00+08:00",
      "exists": true,
      "content_hash": "sha256:..."
    },
    "source_availability": "available",
    "deletion_behavior": "summary_remains_usable",
    "status": "active",
    "supersedes": [],
    "superseded_by": null
  }
]
```

### Artifact Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Stable unique id within the vault |
| `project_slug` | string | Yes | Same slug resolution as weekly raw entries |
| `artifact_type` | enum | Yes | `arch-doc` \| `design-doc` \| `plan-doc` \| `agents-rule` \| `prompt-contract` \| `schema-contract` \| `checklist` \| `roadmap` \| `review` \| `other` |
| `title` | string | Yes | Human-readable artifact title |
| `path` | string | Yes | Absolute path to the local artifact when available |
| `created_at` | ISO 8601 | Yes | First indexed time |
| `updated_at` | ISO 8601 | Yes | Last indexed time |
| `source` | string | Yes | Producing skill or workflow |
| `status` | enum | Yes | `active` \| `draft` \| `superseded` \| `obsolete` \| `missing` |
| `repo_relative_path` | string | No | Path relative to the project repo when the artifact lives inside the repo |
| `topics` | string[] | No | Stable recall tags, not prose summaries |
| `decision_threads` | string[] | No | Stable narrative threads used by roadmap and recall |
| `open_questions` | string[] | No | Questions preserved by the artifact |
| `risk_refs` | string[] | No | Risk ids or short risk labels |
| `evidence_refs` | string[] | No | Commit SHAs, eval ids, issue ids, or doc refs |
| `source_entry_refs` | object[] | No | Provenance pointers to raw capture entries that recorded this dossier context; not references to the artifact document itself |
| `artifact_summary` | object | No | Agent-readable dossier summary with `scope`, `non_scope`, `key_claims`, `key_decisions`, and `open_questions` |
| `last_seen` | object | No | Best-effort source file observation with `at`, `exists`, and optional `content_hash` |
| `source_availability` | enum | No | `available` \| `missing` \| `moved` \| `unknown` |
| `deletion_behavior` | enum | No | `summary_remains_usable` \| `source_required` |
| `supersedes` | string[] | No | Artifact ids this artifact replaces |
| `superseded_by` | string or null | No | Artifact id that replaces this artifact |

### Artifact Dossier Semantics

Artifact entries should be independently readable, not independently
authoritative. A future agent should be able to answer "what was this artifact
about, what did it not cover, why was it important, and what should I verify
before relying on it?" without opening the source document. The dossier must not
store full artifact content and must not become a second document repository.

Use dossier fields this way:

- `source_entry_refs` point to raw capture entries where the dossier context was
  recorded. They establish provenance, not direct verification.
- `artifact_summary.scope` and `artifact_summary.non_scope` define the boundary
  the artifact governs and what remains outside it.
- `artifact_summary.key_claims` may be strings or objects. If an object has
  `evidence_boundary`, use exactly one of `navigation_only`,
  `recorded_context`, or `direct_evidence`.
- `artifact_summary.key_decisions` and `.open_questions` preserve reusable
  agent context, but consumers must still check raw entries or direct evidence
  before presenting them as verified facts.
- `last_seen` records the last source-file observation when known. A missing or
  stale source file does not invalidate the dossier summary, but it lowers what
  consumers may claim from it.
- `source_availability` and `deletion_behavior` tell recall/query/roadmap
  whether the source can still be opened and whether the dossier remains useful
  if it cannot.

`deletion_behavior: "summary_remains_usable"` means the artifact entry can still
orient a future agent after the source document is deleted. It does not mean the
entry can reconstruct the document or verify every claim inside it.

When `scripts/tracework_raw.py` supports artifact indexing, producers should write
the artifact object to a temporary JSON file and delegate validation and upsert
behavior to the helper:

```bash
python <skill-or-repo>/scripts/tracework_raw.py upsert-artifact \
  --artifact /tmp/tracework-artifact.json \
  --cwd "$PWD"
```

Consumers must tolerate missing artifact indexes. Artifact dossier metadata
helps find source documents and preserve recorded context; it must not be
treated as a replacement for raw-entry facts or direct verification.

## ISO Week

Use `date +%Y-W%V` to calculate the current week string. Format: `YYYY-WNN` (zero-padded).

If the `raw/weeks/{week}/` or `Work Diary/Weekly/` directory does not exist,
create it before writing.

When a skill-local or repository helper script is available, prefer it over
hand-written date logic:

```bash
python <skill-or-repo>/scripts/tracework_raw.py week --date 2026-04-26
```

## Project Slug

Resolution order:
1. Check `.tracework/config.yaml` for explicit `project_slug` field
2. Look up the current project path in `{vault}/raw/projects.json` → use its `slug`
3. If not found or the file contains invalid JSON, derive from the project directory name: lowercase, replace spaces/underscores with hyphens

Helper command:

```bash
python <skill-or-repo>/scripts/tracework_raw.py project-slug --cwd "$PWD"
```

## projects.json (Optional)

```json
[
  {
    "name": "My Project",
    "slug": "my-project",
    "path": "/Users/dev/projects/my-project",
    "priority": "core",
    "reporting_group": "work"
  }
]
```

This file is maintained by the `register-project` helper. The cold-start interview calls it automatically during setup. The `capture` skill may also update it as a best-effort side effect. `reporting_group` partitions report audiences before headline selection; it is an open stable string, commonly `work` or `personal`. Skills should work correctly whether or not the registry exists, but an unassigned project must not be silently treated as safe for a work report.

Helper command:

```bash
python <skill-or-repo>/scripts/tracework_raw.py register-project --cwd "$PWD" [--name "My Project"] [--slug my-project] [--priority core] [--reporting-group work]
```

## Change Entry Schema

Each `{vault}/raw/weeks/{week}/{slug}.json` file contains a **JSON array** of entries:

```json
[
  {
    "timestamp": "2026-04-11T14:30:00+08:00",
    "capture_depth": "standard",
    "archetype": "build",
    "type": "feature",
    "summary": "Built scene composition system with auto-layout and overlap resolution",
    "context": "Replaced manual positioning with constraint solver. Resolves 3 bad cases from v2.3 batch eval.",
    "related_docs": ["/Users/dev/projects/my-project/docs/stage-composition-implementation.md"],
    "source": "session-recap",
    "status": "done",
    "work_stream": "Scene composition reliability",
    "motivation": "Manual positioning caused recurring panel overlap failures during export.",
    "impact": "Weekly outline can explain the shipped layout capability without re-reading implementation commits.",
    "reporting": {
      "outcome_candidate": {
        "kind": "outcome",
        "statement": "Scene composition can resolve known panel overlap failures before export."
      },
      "impact_boundary": "observed",
      "evidence_boundary": "verified",
      "evidence_gap": "No production usage metric recorded yet."
    },
    "evidence_refs": ["abc1234", "/Users/dev/projects/my-project/docs/stage-composition-implementation.md"],
    "decision_threads": ["composition-layout-boundary"],
    "lifecycle_transition": {
      "subject": "decision:composition-layout-boundary",
      "from": "proposed",
      "to": "chosen",
      "reason": "Auto-layout with overlap resolution replaced manual positioning."
    },
    "source_refs": [
      {
        "type": "commit",
        "ref": "abc1234",
        "path": "/Users/dev/projects/my-project",
        "note": "Implemented the composition layout change."
      },
      {
        "type": "repository_snapshot",
        "ref": "0123456789abcdef0123456789abcdef01234567",
        "path": "/Users/dev/projects/my-project",
        "note": "Committed tree observed at capture; uncommitted work is not represented."
      }
    ],
    "artifact_context": [
      {
        "artifact_path": "/Users/dev/projects/my-project/DESIGN.md",
        "scope": "Scene composition layout contract and ownership.",
        "delta": "Recorded the auto-layout boundary and overlap-resolution responsibility.",
        "open_questions": ["Whether dense panels need a separate export fallback."],
        "source_of_truth": ["src/composition/layout.ts", "tests/composition-layout.test.ts"]
      }
    ]
  }
]
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `timestamp` | ISO 8601 | Yes | When the change was made or recorded |
| `capture_depth` | enum | No | `lite` \| `standard` \| `deep`; route chosen by capture to bound token cost and retained detail |
| `archetype` | enum | Recommended for new entries | `decision` \| `build` \| `investigation` \| `repair` \| `maintenance`; describes the session shape |
| `type` | enum | Yes | `feature` \| `fix` \| `refactor` \| `decision` \| `risk` |
| `summary` | string | Yes | 1 factual sentence at the boundary actually reached; do not promote plans or partial work into shipped outcomes |
| `context` | string | Yes | 1-2 sentences explaining why and impact |
| `related_docs` | string[] | No | Absolute paths to relevant documentation files |
| `source` | enum | Yes | `session-recap` for new entries; `arch-doc` is legacy-only historical data |

### Recommended Optional Fields

Consumers must tolerate these fields being absent. Producers should add them when the signal is available without extra analysis:

| Field | Type | Description |
|-------|------|-------------|
| `project_area` | string | Product/module area affected by the change |
| `work_stream` | string | Suggested weekly-report grouping; groups activity but does not prove an outcome |
| `impact` | string | Observed user, system, or engineering effect; prospective effects must be labeled as expected or intended |
| `status` | enum | Claim boundary: `done` completed the described scope; `ongoing` is progress; `risk` is unresolved exposure; `decision` records a choice, not implementation |
| `evidence_refs` | string[] | Direct commit, eval, issue, or document references supporting the entry; their presence alone does not prove `impact` |
| `decision_threads` | string[] | Stable thread keys for decision replay. These override artifact hints and keyword fallback when deriving `thread_id` |
| `lifecycle_transition` | object | Explicit state change for an open question, risk, decision, or artifact |
| `source_refs` | object[] | Typed source references with `type` and `ref`, plus optional `path`, `url`, `note`, or `timestamp`; `repository_snapshot` uses a full Git object id and absolute repository root |
| `motivation` | string | Trigger reason and goal for the change — what problem was being solved |
| `exploration_paths` | string[] | Approaches tried during the session and their outcomes |
| `abandoned_alternatives` | string[] | Approaches explicitly rejected and why |
| `open_questions` | string[] | Unresolved questions at session end; entry points for next session |
| `root_cause` | string | Repair archetype root cause; 1-2 sentences |
| `artifact_context` | object[] | Durable artifact scope/delta/source-of-truth blocks embedded in the raw entry |
| `reporting` | object | Report-ready boundary metadata for daily, weekly, and monthly consumers |
| `sync_suggestions` | string[] | Presence-based hints that repo-local intent artifacts may need review |

### `type` vs `archetype`

`archetype` describes the shape of the session. `type` describes the reporting
category of the entry. They are independent axes:

- A `build` archetype normally produces `type: "feature"`.
- A `repair` archetype normally produces `type: "fix"`.
- A `decision` archetype normally produces `type: "decision"`, but can produce
  `type: "feature"` when the chosen approach was implemented in the same
  session.

New `session-recap` entries should include `archetype`. Historical entries
without it are valid and must be treated as legacy raw signals.

### Capture Depth

`capture_depth` records how much context the capture skill chose to preserve for
the session. It is additive; old entries without it remain valid.

| Depth | Meaning |
|---|---|
| `lite` | Report-ready atoms for routine progress, small fixes, cleanup, or low-risk recovered session material |
| `standard` | Normal session memory with motivation, impact, risks, evidence boundary, and report metadata when clear |
| `deep` | High-value decision, contract, artifact dossier, root-cause, rejected-alternative, or recurring-risk memory |

Capture chooses the lightest depth that preserves the reusable signal. Explicit
user wording such as `/tracework:capture deep` may override the route, but most
users should not need to choose a depth. Consumers must treat depth as a cost
and detail hint, not as evidence strength. Evidence strength still comes from
`reporting.evidence_boundary`, `evidence_refs`, typed `source_refs`, and source
artifacts.

### Archetype Expectations

The adaptive-depth helper logs warnings for missing archetype fields; it does
not reject the entry. Zero-config Markdown output follows the same best-effort
rule.

| Archetype | Expected fields when known |
|---|---|
| `decision` | `motivation`, `exploration_paths`; `abandoned_alternatives` when discussed |
| `build` | `motivation`, `impact` |
| `investigation` | `exploration_paths`, `open_questions` |
| `repair` | `motivation`, `root_cause` |
| `maintenance` | Core fields only |

### `artifact_context`

Use `artifact_context` when a session created or materially changed a durable
artifact such as `DESIGN.md`, `PLAN.md`, `AGENTS.md`, README, prompt contracts,
schema contracts, migration notes, or architecture notes.

Each object has this shape:

```json
{
  "artifact_path": "/absolute/path/to/artifact",
  "scope": "What this artifact governs",
  "delta": "What changed in this session",
  "open_questions": ["unresolved artifact question"],
  "source_of_truth": ["path/to/implementation", "path/to/tests"]
}
```

`artifact_path`, `scope`, `delta`, and `source_of_truth` are required when the
object is present. `artifact_path` must be absolute.

### `reporting`

Use `reporting` when the session has a report-ready boundary that should survive
into daily, weekly, or monthly outputs without forcing the consumer to infer it
from prose. This field is optional and additive; historical entries without it
remain valid.

```json
{
  "reporting": {
    "outcome_candidate": {
      "kind": "outcome | progress | activity",
      "statement": "The bounded claim a report may reuse."
    },
    "impact_boundary": "observed | expected | unknown",
    "evidence_boundary": "verified | recorded | limited",
    "evidence_gap": "What is still missing before strengthening the claim."
  }
}
```

Field semantics:

- `outcome_candidate.kind` sets the highest defensible report treatment:
  `outcome` for a recorded state change, `progress` for bounded advancement,
  and `activity` for work that should be visible but not promoted.
- `impact_boundary` says whether impact is observed, expected, or unknown.
- `evidence_boundary` says whether the claim is verified by direct evidence,
  recorded in the raw entry only, or limited by fallback/incomplete evidence.
- `evidence_gap` names what would be needed to strengthen the claim.
- New entries keep grouping in top-level `work_stream` and keep risks,
  questions, alternatives, and decision threads in their factual top-level
  fields. Do not pre-write channel-specific Daily/Weekly/Monthly prose.
- Historical rich reporting objects with `module_scope`, nested `work_stream`,
  `carry_forward`, or `hard_signals` remain valid and readable. Producers stop
  generating those fields; consumers treat them as legacy hints rather than
  current truth.

Do not store report-local `O#`, `W#`, `D#`, or `E#` identifiers in raw entries.
Weekly and monthly assign those labels after collecting the full reporting
period.

Recommended producer behavior:

- Add `status` whenever it can be inferred from the session: `done` for completed work, `ongoing` for partially completed work, `risk` for open risk entries, and `decision` for design decisions.
- Add `archetype` for new `session-recap` entries using the adaptive-depth
  classification rules from the skill.
- Add `capture_depth` for new `session-recap` entries using the capture routing
  rules from the skill.
- Add `impact` when the entry has a clear user, system, reporting, reliability, migration, or developer-workflow effect. This should be more report-ready than `context`, not a duplicate.
- Add `evidence_refs` for commit SHAs, issue IDs, eval IDs, or doc paths that are already known. Do not perform extra repository analysis only to populate this field.
- Add `decision_threads` when the entry belongs to a durable decision topic.
  Use stable slug-like terms such as `validation-repair-ownership`; these are
  preferred over artifact hints and keywords for decision replay `thread_id`.
- Add `lifecycle_transition` when the entry explicitly changes the state of an
  open question, risk, decision, or artifact. Keep it factual and tied to the
  current raw entry.
- Add `source_refs` when evidence needs a typed reference rather than a plain
  string. Each object must include `type` and `ref`; optional fields are
  `path`, `url`, `note`, and `timestamp`.
- For a code-backed session-end or checkpoint entry, add a
  `repository_snapshot` source when the current repository and committed `HEAD`
  can be resolved cheaply. Use the full object id as `ref` and the absolute
  repository root as `path`. It identifies only the committed tree observed at
  capture time; it never includes or proves uncommitted work. Do not reconstruct
  a historical snapshot during Capture Day from the repository's current state.
- Add `project_area` or `work_stream` when the natural module or narrative grouping is obvious. Leave them absent rather than guessing.
- Add `motivation` when the trigger for the change is clear — the problem being solved, the constraint that forced the change, or the goal being pursued. This is the "why now" behind the change.
- Add `exploration_paths` when the session involved trying multiple approaches. Each entry should describe the approach and its outcome (e.g. "lazy loading → marginal gain on mobile first-screen").
- Add `abandoned_alternatives` when approaches were explicitly considered and rejected. Include the rejection reason — this is valuable for future roadmap decisions.
- Add `open_questions` when the session ends with unresolved decisions or unanswered questions. These serve as entry points for the next session.
- Add `sync_suggestions` when the entry mentions a decision, prompt/schema
  contract, orchestration rule, or intent artifact that may require follow-up in
  `DESIGN.md`, `PLAN.md`, `AGENTS.md`, README, architecture docs, prompt
  contracts, or schema contracts. This is lightweight flagging only; producers
  must not claim semantic diffing or automatic doc updates.
- Add minimal `reporting` when the entry already has a clear claim and evidence
  boundary. Consumers use it for claim treatment, while factual narrative comes
  from `summary`/`context`/`status`/`impact` and the other top-level fields.

### Fruit Check

Every report-level claim should have a real "fruit": an observable change in
user, product, system, reliability, migration, or developer-workflow state.
Commits, files, tokens, logs, task counts, and documents are activity or
evidence, not outcomes by themselves.

Apply these checks without adding fields or migrating historical raw entries:

1. `summary` states what actually changed at the boundary reached.
2. `status` limits the claim; `ongoing`, `risk`, and `decision` must not be
   rewritten as completed outcomes.
3. `impact` describes an observed effect. If only a future effect is known,
   label it explicitly as expected, intended, or possible.
4. `work_stream` explains how related entries may roll up, but does not turn
   their combined activity into an outcome.
5. Evidence must support the claim. A true commit, log, or document reference
   does not make an unsupported impact statement true.

If an entry cannot pass this check, narrow it to a decision, investigation,
maintenance, or risk signal instead of manufacturing a result. Consumers must
remain backward-compatible with entries that predate v2.2 and omit optional
fields.

### Writing `summary`

One sentence that answers: **what was done + how**. Use active voice, specific technical nouns, avoid generic verbs.

Pattern: `[Action verb] [specific output/change] [with/using/replacing key approach]`

- Good: "Added retry-with-repair loop to narrative validation, replacing single-pass validation"
- Good: "Extracted character extraction into a standalone stage with fan-out parallelism"
- Avoid: "Updated documentation" / "Made improvements" / "Fixed issues"

### Writing `context`

1-2 sentences that answer: **why this was needed + what impact it has**. Capture the design intent and reasoning that git commits rarely convey.

Pattern: `[Trigger/motivation]. [Approach chosen] → [expected impact or what it resolves].`

- Good: "Single-pass validation missed 3 recurring failure patterns from v2.3 eval. Repair loop now catches and corrects these automatically, reducing manual review by ~40%."
- Good: "Character extraction was tightly coupled with parsing, blocking independent iteration. New isolation allows tuning extraction without risking parse stability."
- Avoid: Repeating the summary / describing implementation details / vague statements like "improved quality"

### Quality Levels

Use these levels when judging whether a raw entry is worth keeping:

| Level | Example | Problem / Value |
|-------|---------|-----------------|
| Bad | "Updated documentation" | Process log only; no durable work signal |
| OK | "Updated Parse Stage documentation" | Names the artifact, but not the engineering meaning |
| Good | "Clarified Parse Stage input validation and repair-loop responsibilities" | Captures the technical boundary |
| Excellent | "Separated Parse Stage input validation, repair-loop ownership, and downstream output contracts so future schema migrations can debug failures without re-reading implementation commits" | Captures change, boundary, why it matters, and future reuse value |

Prefer Good or Excellent entries. If an entry cannot rise above OK, skip it unless the user explicitly asked to preserve that process detail.

### Type Definitions

- **feature** — New capability was built
- **fix** — Bug was resolved or reliability improved
- **refactor** — Code restructured without behavior change
- **decision** — Architectural or design decision (even if not yet implemented)
- **risk** — Issue identified that could affect future work

## Lifecycle Signals

Tracework does not mutate historical raw entries. When a later skill learns that an
open question, risk, or decision changed state, it should append a new raw entry
that states the lifecycle transition explicitly.

Supported lifecycle language:

```text
open_question: open -> answered -> obsolete -> promoted_to_decision
risk: identified -> mitigated -> accepted -> obsolete
decision: proposed -> chosen -> revised -> superseded
artifact: draft -> active -> superseded -> obsolete; active -> missing
```

Use the optional `lifecycle_transition` field when a raw entry carries one of
these changes:

```json
{
  "subject": "decision:validation-repair-ownership",
  "from": "proposed",
  "to": "chosen",
  "reason": "The validation stage owns its internal repair loop."
}
```

`subject`, `from`, `to`, and `reason` are recommended when known. Consumers must
tolerate partial objects because older entries and agent-authored fallback
entries may only know the new state.

Future consumers may derive current state by reading entries in timestamp order.
Producers must not pretend lifecycle state is fully managed if they only have a
new raw signal.

## Write Behavior

- **Append** new entries under a per-file lock (read → append → atomic replace)
- Do not deduplicate or overwrite — the consumer handles merging
- **Side-effect failure**: if the project slug cannot be determined or the write fails, skip the change-entry write gracefully. The primary deliverable of each skill is never the change entry — it is always a side effect.
- **Concurrent writes**: the shared helper locks the complete read-modify-write transaction for raw entries, artifact dossiers, and the project registry, and replaces JSON atomically. Never ask consumers to recover overwritten entries. Invalid existing JSON fails without replacing the original.

`timestamp` is work time used by period consumers. Ordinary capture sets it from
the system clock. Historical capture passes `--date YYYY-MM-DD` and a source
ISO timestamp with timezone on that date; the helper preserves it and selects
the corresponding ISO week. New entries also carry `captured_at`, the actual
system-clock ingestion time. Historical entries need no migration. For an
as-of reconstruction, exclude evidence captured after the cutoff when
`captured_at` is available, even if its work timestamp is earlier.

When `scripts/tracework_raw.py` is available in the skill directory or repository,
producers should write the entry object or array to a temporary JSON file and
delegate validation and append behavior to the helper:

```bash
python <skill-or-repo>/scripts/tracework_raw.py append-entry \
  --entry /tmp/tracework-entry.json \
  --cwd "$PWD"
```

The helper accepts a single entry object or an array of entries. It validates
required fields, resolves `{vault}` and project slug, creates the target week
directory, appends to the existing project JSON array, and prints a JSON summary
containing `week`, `slug`, `path`, `entries_appended`, and `total_entries`.

## Consumers

Downstream tools read these files to get high-quality development context:

- **weekly** — reads change entries as the primary semantic source for weekly report generation. Git logs are only fallback and coverage evidence when raw entries are missing or incomplete.
- **daily** — creates scoped daily management-closure reports from raw entries and uses git only as limited fallback coverage
- **monthly** — uses matching raw entries as semantic truth and Daily/Weekly reports as prior human judgments
- **recall** — reads recent raw entries first and uses artifact dossiers as optional navigation plus recorded context
- **roadmap** — derives decision threads, accumulating risks, and
  recurring open questions from raw entries
- Any future reporting or review tool that needs structured change history

## Weekly Report Consumption

For weekly reporting, raw entries should carry the meaning of the work:

- If `reporting` is present, use its outcome, impact, evidence, and gap
  boundaries before inferring claim treatment. Use top-level factual fields for
  the narrative. Old rich reporting fields remain compatibility hints.
- `summary` should describe the engineering change at report granularity.
- `context` should explain why it mattered and what changed as a result.
- `archetype` should control treatment depth: decisions emphasize trade-offs,
  repairs emphasize root cause, investigations emphasize open questions, and
  builds emphasize impact.
- `artifact_context` is embedded technical evidence. Consumers should use its
  scope, delta, and source-of-truth fields before reading files from disk.
- `source: arch-doc` is legacy historical data. Treat it as high-confidence
  architecture evidence, but do not expect new entries from that source.
- `related_docs` are evidence and deep context; consumers should read them only
  when the raw entry is not enough to explain the technical approach.
- Artifact index entries are optional source navigation. Consumers may use them
  to find durable repo-local docs and dossier context, but must not invent
  decision facts from artifact titles or summaries alone. Treat dossier claims
  as `navigation_only` or `recorded_context` unless a claim or source-of-truth
  field provides direct evidence.
- Git commits are useful for coverage checks, but they should not override explicit raw-entry intent.

### Duplicate and Conflict Handling

Consumers should merge semantically similar signals rather than repeat them:

- Same project + same week + similar `summary` / `context` means the entries are candidates for one work stream.
- `session-recap` entries are intent-rich: they often preserve why the work happened and what trade-off was made in conversation.
- Legacy `arch-doc` entries are evidence-rich: they often preserve contract
  boundaries, source-of-truth paths, and architecture decisions.
- If a `session-recap` entry and a legacy `arch-doc` entry describe the same
  change, combine them into one work stream. Use the session entry for
  motivation and the legacy arch-doc entry for technical evidence.
- If a new `session-recap` entry includes `artifact_context`, treat it as
  equivalent signal strength to the older session-recap plus arch-doc pair.
- Fallback git commits fill coverage gaps only. They should not create a duplicate stream for work already explained by raw entries.
- If two entries conflict, preserve the conflict explicitly in the weekly outline or daily note instead of silently choosing the more positive version.

## Producer Guidance

Raw entries are weekly-report signals, not chronological diary items.

### For `session-recap`

Capture only signals that should survive into a weekly review:

- Capabilities shipped or meaningfully advanced
- Technical decisions and trade-offs
- Risks, blockers, regressions, and follow-up work
- Cross-module contracts, migrations, reliability improvements, or validation changes

Merge related implementation steps into one entry. A feature implemented through several commits, fixes, and follow-up tweaks should usually become one `feature` entry with context that mentions the important repair or trade-off. Skip process-only work such as formatting, file moves, import cleanup, generated files, and local setup unless it explains a larger report-worthy change.

### Legacy `arch-doc` Entries

Historical raw data may still contain `source: "arch-doc"`. Consumers must keep
reading those entries as architecture evidence. New producers must not write
`source: "arch-doc"`; adaptive-depth `session-recap` entries with
`artifact_context` replace that signal path.
