# Workflow

## Primary Loop

```text
install
  -> try: write weekly / write daily
  -> when you need multi-day memory: configure vault and project groups
  -> wrap up after key sessions
  -> write daily / weekly / monthly
  -> drill down only when questioned or resuming
```

1. Install `tracework@tracework`.
2. Try `/tracework:weekly` or `/tracework:daily` first; without a vault, the
   report returns in the conversation.
3. Run `/tracework:cold-start-interview` when you want durable storage and
   strict reporting groups.
4. End key sessions with `收工` / “wrap up” or `/tracework:capture` so reports
   can explain intent, risks, trade-offs, and evidence boundaries.
5. Use `/tracework:daily`, `/tracework:weekly`, and `/tracework:monthly` for
   high-frequency management closure.
6. Optionally enable metadata-only session scanning and run
   `/tracework:capture day` once at day end to recover missed sessions.
7. Use Query, Recall, or Roadmap only when work is questioned, resumed, or
   reviewed over a long horizon.

## User Actions, Not a Command Table

| What you say | What runs |
| :--- | :--- |
| wrap up / 收工 | capture |
| write daily / weekly / monthly | daily / weekly / monthly |
| why did we choose this / continue last time | query / recall |

See [Skills](./skills) for the full command surface.

## Scope Partition

```text
work     -> work projects only
personal -> personal projects only
all      -> separate group narratives in one private view
```

Partition happens before selection. Weekly then resolves goal sources and
accounts for actual change, variance, and next commitments without forcing a
headline count. Its brief body keeps only information that changes management
judgment, action, or confidence; accountability, coverage, and provenance stay
in the appendix.

## Reuse Map

```text
Capture -> raw/weeks/{week}/{slug}.json
Capture Day -> scoped session index + local transcripts -> raw entries
Daily   <- raw entries + limited git fallback
Weekly  <- raw entries + limited git fallback
Monthly <- raw entries + Daily/Weekly editorial context
Query   <- derived decisions + raw entries
Recall  <- raw entries + artifact/decision navigation
Roadmap <- decision evidence pack
```

Raw entries remain semantic truth. Report-local evidence ids belong to the
appendix, not the raw schema or spoken narrative.

Daily, Weekly, and Monthly can also use scoped facts already visible in the
current conversation, without capturing them or scanning other sessions.
Stored entries pass through the shared corrected view before reporting;
corrections stay in the original work period, and an explicit as-of cutoff
preserves what was known then. Existing reports require an explicit refresh.
