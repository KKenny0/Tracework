# Quick Start

## 1. Install

```bash
codex plugin marketplace add KKenny0/Tracework
codex plugin add tracework@tracework
```

Claude Code:

```bash
claude plugin marketplace add KKenny0/Tracework
claude plugin install tracework@tracework
```

## 2. Try a Report First

In any project with recent work, say:

```text
write the weekly report
```

or:

```text
/tracework:weekly
```

You can also close today first: `write the daily report` / `/tracework:daily`.

You can see a result in the conversation without configuring a vault. If the
current project is still unassigned, an implicit trial reports it as `local`
instead of pretending it is safe `work`. An explicit or configured `work` scope excludes
unassigned projects and explains how to fix the classification. Before Capture, reports can also use facts already visible in the current
conversation when the project, group, and work date are known. This does not
save long-term memory or read other conversations. Git-only coverage remains
`limited`; reports do not invent intent, decisions, or verified impact.

## 3. Turn On Durable Storage When You Need It

When you want multi-day memory, file writes, and strict work/personal
partitioning, run:

```text
/tracework:cold-start-interview
```

Choose the local vault, project identity, and reporting group such as `work`
or `personal`.

Assign a group to each project you want in a scoped report. Unassigned projects
are excluded from work or personal output.

Common closure commands:

```text
/tracework:daily work
/tracework:weekly work
/tracework:monthly work
```

Use `personal` for personal projects or `all` for a private combined view with
separate group sections. Weekly has three modes: say `这周做了啥` / `quick weekly`
for a conversation-only quick review; default `write the weekly report` for a
Markdown brief; say `weekly PPT` when you need a standalone PPT-ready Markdown
Deck for a department update. Without explicit framing, it serves
same-department colleagues at a weekly meeting and does not invent a duration.
The deck starts from why the work exists, presents this week's result or final
choice and shortest rationale, and ends with next-week closure. It contains only
necessary pages; zero admitted pages return an empty state. The Markdown is
independently readable; PPT is its visual translation.

## 4. Improve the Evidence with Capture

End key work with `收工` / “wrap up” or `/tracework:capture`. Capture chooses
lite, standard, or deep from the session signal and stores only durable facts.

If you prefer one end-of-day recovery pass, opt in with:

```yaml
session_scan:
  enabled: true
  retention_days: 30
```

Then run `/tracework:capture day [YYYY-MM-DD] [work|personal|all]`. The bundled
hook indexes metadata only; Capture Day partitions reporting scope before it
reads transcript content.

## 5. Use Trust and Recovery When Needed

- `/tracework:query why did we choose ...?`
- `/tracework:recall` when resuming older work
- `/tracework:roadmap` for a long-range decision review

These are lower-frequency surfaces; they do not need to become daily habits.

## 6. Update or Correct What You Saved

Daily updates preserve hand edits and return a draft if the file changed after
it was read. To correct a stored fact, ask Capture to correct the record and
identify the original record, correct fact, and reason. The original remains
stored; all six readers use the corrected view in its original work period.
Existing reports change only when you request a refresh. Once corrections exist,
keep a correction-aware plugin installed rather than downgrading to an older
reader. See [Skills](./skills) for historical knowledge cutoffs and state handling.
