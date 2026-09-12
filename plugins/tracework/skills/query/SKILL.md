---
name: query
description: Query Tracework's decision replay index for why a project chose a path, what alternatives were rejected, what should be revisited, what impact a decision had, or any natural-language question about project history. Use this skill for "/tracework:query", "why did we choose this?", "为什么当时这么选", "有没有被拒绝过的方案", "revisit this decision", "auth 迁移做到哪了", "我们讨论过 rate limiting 吗", or when a coding agent needs cited decision evidence before changing architecture, contracts, prompts, schemas, or product direction.
---

# Decision Replay Query

This skill answers targeted project-history questions from Tracework's local decision
memory. It is a thin wrapper around the deterministic decision replay helper:
the script narrows evidence, and the host agent writes the final answer.

Use `query` when the current task touches an existing decision, architecture
boundary, rejected option, long-running risk, or product tradeoff. Use `recall`
for session-start orientation; use `query` for a specific follow-up question.
Git-only report fallback is not decision evidence here. If the raw record does
not support the question, return the evidence gap and suggest targeted capture
after the user clarifies the decision.

## Scope

- Intra-project by default.
- Raw entries remain the source of truth.
- `{vault}/raw/decisions/{project-slug}.json` is a derived retrieval index.
- The helper may rebuild an in-memory index from raw entries when no saved index
  exists, but this skill does not write new memory.
- Do not use git history, external docs, or model assumptions to fill missing
  decision evidence.

## Workflow

1. Identify the user's decision question.
2. Pick the mode:

| Mode | Use when the user asks |
|------|------------------------|
| `why` | why a path was chosen, why something works this way |
| `alternatives` | what was rejected, abandoned, deferred, or not chosen |
| `revisit` | what open questions or deferred choices should be reconsidered |
| `impact` | what downstream effects a decision had |
| `free` | anything that doesn't fit the other 4 modes — status checks, "did we discuss X?", "what's the history of Y?" |

Questions asking for evidence, proof, verification, or whether a claimed result
is supported use the existing modes rather than inventing an evidence mode:
try `impact` first to retrieve the claimed effect, then `why` if the impact
query is not answerable. The agent performs this routing; the helper continues
to expose only its four concrete modes.

### Free-Form Mode

When the user asks a natural-language question that doesn't clearly map to
`why` / `alternatives` / `revisit` / `impact`, use `free` mode. The agent
tries multiple modes sequentially and returns the first result with
`answerable=true`.

**Fallback order**: `why` → `revisit` → `impact`. Stop at the first
`answerable=true` result. Do not try `alternatives` in the fallback chain —
it answers a different question shape.

If all three modes return `answerable=false`, say the vault does not contain
enough evidence for this question. Suggest capturing the context with
`/tracework:capture` if the user can clarify the decision.

Free-form queries still pass a concrete `--mode` to the helper on each
attempt. The agent handles the multi-mode orchestration; the helper script is
not modified.

3. Run the helper:

```bash
python <this-skill>/scripts/decision_graph.py query "<question>" --cwd "$PWD" --mode why --limit 5
```

Use `--mode alternatives`, `--mode revisit`, `--mode impact`, or follow the
free-form fallback order when the question calls for it. If the user names a
project slug, pass `--slug <slug>`. If the user or config provides a vault
path, pass `--vault <path>`.

4. Read the JSON evidence pack.
5. Answer from the evidence pack only.

## Output Contract

Return a concise answer with:

- A direct answer when `answerable=true`.
- The matched decision node ids and source timestamps.
- `matched_terms`, `evidence_strength`, and `answerability_reason`.
- `evidence_boundary`, `impact_boundary`, and any `missing_evidence`, even
  when the recorded decision is answerable.
- `source_entry_refs` for every cited decision.
- Direct evidence fields (`evidence_refs`, `source_refs`, and
  `direct_artifact_refs` source-of-truth evidence)
  when present on a cited decision.
- Rejected alternatives when relevant.
- Open questions when relevant.
- `confidence` and `inference_notes` when a node is inferred.
- Suggested repo-local docs from `suggested_docs`, if any.

If `answerable=false`, say the current Tracework records do not contain enough
evidence. Include `missing_evidence` and suggest capturing the decision with
`/tracework:capture` after the user clarifies it. Do not invent an answer.

## Evidence Rules

- Treat `confidence=explicit` as directly recorded raw-entry evidence.
- Treat `confidence=inferred` as useful navigation, not a proven fact.
- Treat `source_entry_refs` as provenance: they prove where Tracework recorded a
  claim, not that the claim's outcome was independently verified.
- Treat `evidence_refs`, supporting typed `source_refs`, and `direct_artifact_refs`
  as references to inspect, not fresh verification. `conversation` records
  provenance; `repository_snapshot` locates a revision. Neither alone verifies
  an outcome. General `artifact_refs` are navigation hints unless the raw
  entry explicitly marked them source-of-truth. Preserve both kinds so readers
  can drill down without overstating verification.
- Treat artifact dossier fields from `{vault}/raw/artifacts/{slug}.json` as
  navigation plus recorded context. `artifact_summary.key_claims` can explain
  what a linked artifact was believed to cover, but only
  references explicitly in raw may support its declared verification boundary.
- Carry raw `reporting.evidence_boundary` and `reporting.impact_boundary`.
  Legacy explicit entries default to `recorded`; inferred entries to `limited`.
  `strong` requires a well-matched explicit decision, a valid `verified`
  boundary, and supporting references. Impact queries also require `observed`.
  A reference alone never upgrades a recorded claim. Preserve evidence gaps.
- Treat `evidence_strength=weak` as a prompt to hedge or ask for more evidence
  even when `answerable=true`.
- An explicit, well-matched raw entry without direct evidence remains
  answerable, but it must not be called `strong`; include its
  `missing_evidence` instead.
- Preserve uncertainty in the wording when `inference_notes` are present.
- Do not quote or cite a decision without its `source_entry_refs`.
- Edges and supporting nodes are context expansion, not standalone proof.

## Storage

This skill reads:

- `{vault}/raw/decisions/{project-slug}.json` when present
- `{vault}/raw/weeks/{YYYY-WNN}/{project-slug}.json` as rebuild fallback
- `{vault}/raw/artifacts/{project-slug}.json` as optional dossier navigation and recorded context

This skill writes no files.
