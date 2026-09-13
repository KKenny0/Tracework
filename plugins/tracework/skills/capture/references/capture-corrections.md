# Correct a Stored Fact

Use only when the user identifies a factual mistake in an existing raw record.
A prose edit updates a report; a later real event is an ordinary lifecycle entry.
No vault: return a draft. Resolve the authorized current project before reading.

1. Run `<this-skill>/scripts/tracework_state.py --vault <vault> --slug <slug>`.
   Find the exact effective chain tail and its raw source ref; do not guess by
   similar summary. If ambiguous, request the missing target identity.
2. Read that original JSON object. Compute target_hash with the bundled
   `tracework_state.entry_hash` (canonical sorted UTF-8 JSON, compact separators,
   excluding internal underscore metadata). Use exact week, zero-based array
   index and timestamp. Do not put project/path overrides inside target_ref.
3. Prepare one normal raw object with this optional correction object:

```json
{
  "operation": "replace",
  "target_ref": {"week": "2026-W35", "entry_index": 0, "timestamp": "2026-08-25T10:00:00+08:00"},
  "target_hash": "<sha256>",
  "reason": "What was inaccurate"
}
```

For replace, normal factual fields carry the full corrected record; omitted
fields are removed, not inherited. For retract, use ordinary required fields to
describe the withdrawal; consumers exclude it as an outcome. Keep target work
timestamp. If work date itself was wrong, retract and then append a new ordinary
record with the correct date; these are two explicit writes, not a transaction.
If the second fails, report the withdrawal and retain the replacement draft.

4. Use existing `tracework_raw.py append-entry --entry <json> --cwd <project>`
   with the authorized vault/slug when needed. The writer chooses the target
   week, retains work time, assigns current captured_at, and checks hash and
   effective chain tail inside the target file lock. Append one correction per
   call. On conflict or write failure, preserve the draft; never retry by
   changing the target/hash silently or modifying old array elements.
5. Read back the effective view and report the actual result. Do not refresh
   earlier reports unless requested; Daily refresh uses its protected writer.

Risk subjects retain the original logical raw ID through a correction chain.
Question subjects retain their ID only when both text and index are unchanged;
changed or moved questions get replacement raw IDs. Unmatched transitions stay
visible and require an explicit new binding.
After a correction exists, do not downgrade to readers that ignore corrections.
Stop new correction writes and fix forward if rollback is needed.
