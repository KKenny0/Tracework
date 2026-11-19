# Daily Note Writing Rules

Read the shared reporting narrative contract first. Prefer raw factual fields,
then admitted current conversation evidence, optional artifact navigation, and
uncovered git activity. Old reporting/carry_forward metadata is a hint, not
current truth.

## Merge Within Scope

- Combine accounts of the same state transition under the same work goal.
  Keep independent key deliverables and conflicting claims identifiable, even
  when they share a project, work stream, or source.
- Distinguish the earlier same-day result from what the current review or
  recalculation actually adds. When a finding is revised or withdrawn, name
  the affected conclusion, the evidence that changed it, what still holds, and
  the comparison population and denominator where they affect the result.
  For a withdrawal, focus on the affected judgment and what the evidence can
  still support. Repeat a withdrawn figure only if it is needed to understand
  the difference, and explicitly mark it as no longer applicable. Keep
  different evaluation goals and their rankings distinct.
- Use earlier Daily material already available in scope only to recognize known
  repeats. Keep the current effective facts as the basis of the report. Never
  open earlier reports or expand dates, projects, groups, or source reads just to
  deduplicate across dates. If a repeat check adds no supported fact, omit the
  old result as news. Preserve substantive earlier work that belongs to the
  requested day when updating that same day's report.
- For each item in the requested date/group's inspected body, establish the
  selected project and support within the current report's period and as-of.
  A valid block hash proves text integrity, not project ownership or truth.
  Carry supported independent work into the replacement. Merge supported
  revisions under the same goal and keep the earlier claim only as revision
  history. Admit git-only support from the resolved project and date at its
  limited grade. The old body alone cannot support a claim.
- If replacing the block would lose an item with unknown ownership, missing
  support, or unresolved conflicting evidence, leave the block in place and
  return a scoped draft that explains why. This includes items outside a
  narrowed project selection. Do not repeat unadmitted old text in the draft.
  Partial reads normally stay in conversation. An explicit save request for a
  partial draft still requires safe reconciliation for every targeted block.
- When explicitly asked to refresh the date, an existing block whose last
  reportable item is clearly linked to a successful authoritative `retract`
  needs a brief withdrawal notice. Require matching project, exact raw
  target or logical ID, same work date, visible correction history under the
  requested cutoff, and no unresolved conflict affecting the withdrawal.
  If a correction conflict could affect the withdrawal and its diagnostic
  does not identify the target, keep the existing block and return a draft.
  State what was withdrawn and why, cite the correction entry and reason, and
  avoid reasserting the old claim. If the day still has supported work, retain
  it. Missing evidence, a failed read, or a mere follow-up cannot establish a
  retraction. Do not create a new block or empty day from absence alone.

## Short Body

Organize each main item around one work goal. Explain the action and its
specific object, what the deliverable contains or is usable for, and what the
work newly establishes or changes, with the decisive basis for that judgment.
Include only supported parts and give distinct contributions enough room to be
understood. Keep the delivery or acceptance state and limits beside the claim.
Put a supported follow-up with its item. Give a cross-item decision, escalation,
or standalone coordination need its own place when it warrants attention.

Name the concrete mechanism or proposal in the body. When a source number helps
readers cross-reference it, put the number next to the name. For first-round
priorities, keep the facts that explain the choice, including what makes a
plausible alternative less urgent or no longer viable when that affects the
ranking. Split multiple findings into short paragraphs or subitems when that
helps readers scan them. Let the evidence determine the length.

Before writing, read each item as a colleague who has never seen the underlying
review or plan. Replace every bare direction, option, or gate label with its
supported meaning. If the evidence does not name the object, omit the shorthand
unless a material unresolved fact needs an explicit qualification. One example
of a self-contained conclusion is “The migration review recommends reconnecting
the failure report. The service now rejects immediate duplicates, but the old
report that tracked duplicates across later retries was removed.”

Each group or local lane with signal needs one clear daily judgment. Make it
explicit in the lead item by default. Add a separate `今日判断` overview only when
it adds an independent conclusion about the day. The default body can be as
simple as the following:

```markdown
- **{project / work goal}**：{concrete action and object, deliverable content or
  use, supported change and basis, adjacent status limits and any recorded next step}

<details>
<summary>证据</summary>

- {project / source ref / recorded, verified, or limited, with precise check boundary}

</details>
```

Use the same content standard in conversation and vault output. An explicit
user format, including work-group formatting instructions the user supplies
through vault guidance, takes precedence over this default layout. Place the
same facts and judgment in the appropriate items or fields while preserving
claim-level attribution, audience partition, and protected writes.

One supported change is enough. Omit empty sections and cover meaningful
secondary work briefly. Missing reports, effect measurements, or root-cause
details qualify the result when material. Report a next step only when the
source supports it. Keep git-only claims limited. When stating an
eligibility rule, keep every condition and exception that changes which cases
qualify; otherwise give a bounded description, not an incomplete substitute
rule. Do not derive required order or dependencies from a list of open issues;
any suggested plan stays visibly proposed. Keep decisive scope and fallback
limits when shortening, without an implementation inventory. Re-read the body
alone before writing: one change's commit, push, or acceptance must not appear
to cover another change.
A reader should understand the day in about one minute per reporting group.
No fixed project labels or field list are required for new reports. Monthly
uses raw first and reads this prose only as prior editorial judgment.

For local/no-vault output, add `## YYYY.MM.DD · {scope}` and return in the
conversation. Label implicit local as unassigned, never work. Do not invent a
file path. An optional one-line cold-start hint may follow. For `all`, keep a
separate complete body per exact group, including a separate unassigned lane;
never rank or write a common judgment across groups.

## Protected Vault Update

Only the bundled merger writes Daily Note. It accepts prepared prose and checks
its boundaries. Before drafting for a date, inspect the groups authorized for
that write. In `all`, repeat `--group` for each selected exact group, excluding
lanes that have no eligible project. Never use `all` as a group key.

```bash
python <this-skill>/scripts/update_daily_note.py \
  --inspect --path <daily-note-path> --date YYYY-MM-DD --group <exact-group>
```

Use `bodies` as prior same-day prose and `expected_file_hash` for the writer.
An absent group has no managed body in that snapshot. An inspection conflict
returns no prior bodies. Inspect each additional date before drafting it, using
the file version after any successful writes from earlier dates in this run.
Stop the vault update on a stale snapshot and return the affected draft.

Save the reconciled bodies to a temporary UTF-8 JSON object mapping exact
reporting groups to Markdown. Conversation output can retain headings and title
levels requested by the user. In a vault body, render H1–H3 as H4 or bold
labels, including user-supplied titles. For combined output, start each body
with a visible `#### {group name}`. Leave date headings and managed markers to
the writer. A user format never overrides these boundaries.

```bash
python <this-skill>/scripts/update_daily_note.py \
  --path <daily-note-path> --date YYYY-MM-DD \
  --bodies <temporary-bodies.json> --expected-file-hash <sha256-or-missing>
```

The merger owns one marked block per date and exact group. It checks the stored
body hash before replacement, preserves other blocks and outside bytes, checks
the whole-file snapshot before atomic replacement, and serializes its own
writers. On conflict (user edits, corrupt/duplicate markers, ambiguous legacy
date content, or concurrent changes), keep the original file and deliver the
prepared body as a conversation draft with the reason. Do not bypass protection,
repair markers, rehash user edits, or retry with a fresh hash to force a write.
Legacy checkbox and field-format history remains untouched. The optimistic
whole-file check cannot lock unrelated editors; if the user reports a concurrent
edit after writing, preserve both versions and resolve explicitly.
