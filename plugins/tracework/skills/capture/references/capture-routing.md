# Capture Routing

Use this reference before finalizing a capture entry. Choose one
session-level `capture_depth` unless explicit user wording overrides it.

## Explicit Overrides

Respect clear user intent:

- `lite`: "简单记一下", "brief", "quick capture", `/tracework:capture lite`
- `standard`: `/tracework:capture standard`, ordinary explicit capture
- `deep`: "深入记录", "记住这个决策", "记录这个取舍", "deep",
  `/tracework:capture deep`

When no override exists, route from evidence. Do not ask the user to choose a
depth.

## Dynamic Route

Choose the lightest depth that preserves the reusable signal.

| Depth | Use when | Normal entry count |
|---|---|---|
| `lite` | Routine progress, small fix, docs/tests/config cleanup, completed low-risk implementation, or recovered session material without durable decision evidence | 1 |
| `standard` | Normal build, repair, investigation, or decision with a clear goal, impact, risk, evidence boundary, or report-ready signal | 1-3 |
| `deep` | Architecture/product/schema/prompt contract decision, rejected alternatives, durable artifact dossier, major root-cause repair, recurring risk, or explicit "why/tradeoff" memory request | 1-5 |

If a session contains mixed signals, choose the highest justified depth and keep
minor work inside the same entry only when it supports the main signal.

## Lite Capture

Preserve report atoms and avoid expensive reconstruction.

Expected fields:

- `capture_depth: "lite"`
- core fields: `timestamp`, `type`, `summary`, `context`, `source`
- `archetype`, `status`, and `reporting` when obvious
- `evidence_refs` only when already visible

Avoid:

- artifact dossier side effects unless a durable artifact was materially
  changed
- reconstructed alternatives or root cause when the conversation did not
  establish them
- long open-question lists

## Standard Capture

Preserve the normal session memory that improves reports and later evidence checks.

Expected fields:

- `capture_depth: "standard"`
- core fields plus `archetype`, `status`, `motivation`, and `impact` when known
- `reporting` metadata when a daily/weekly/monthly boundary is clear
- risks, open questions, evidence refs, and obvious work stream hints

Use standard for most explicit `/tracework:capture` requests.

## Deep Capture

Use deep only when the session would be expensive or risky to reconstruct later.

Expected fields:

- `capture_depth: "deep"`
- decision threads, lifecycle transitions, rejected alternatives, or root cause
  when present
- typed `source_refs` and direct evidence boundaries when available
- `artifact_context`, `sync_suggestions`, and artifact dossier upserts when a
  durable artifact governs future work

Deep capture is justified by decision density or artifact/contract importance,
not by token count, file count, or how long the session felt.

## Checkpoint Mode

Checkpoint entries are usually `lite` or `standard`. Use `deep` only if the
checkpoint records a durable decision, contract boundary, major risk, or
artifact context. Prefer `status: "ongoing"` unless the checkpoint captures a
completed phase, resolved repair, or chosen decision.

## Receipt Reason

In vault mode, include one short reason after the confirmation:

```text
depth=standard: captured outcome, risk, and evidence boundary
```

Keep the reason factual. It is for tuning, not marketing.
