# Daily Note Writing Rules

Read the shared reporting narrative contract first. Prefer raw factual fields,
then admitted current conversation evidence, optional artifact navigation, and
uncovered git activity. Old reporting/carry_forward metadata is a hint, not
current truth. Merge one work-stream state change into one account; keep
independent work and conflicting claims separate.

## Short Body

Use the same short prose in conversation and vault output:

```markdown
#### 今日判断

{Most important state change and remaining gate, in one or two sentences.}

#### 必要进展

- **{project}**：{starting situation, decisive movement, current state and meaning;
  keep expected, unverified, conflict, or limited boundaries beside this claim.}

#### 下一道门

{Concrete next acceptance gate, decision, or escalation, only if supported.}

<details>
<summary>证据</summary>

- {project / source ref / recorded, verified, or limited; precise check boundary}

</details>
```

One supported change is enough. Omit empty sections. Cover meaningful secondary
work briefly; do not invent risks or next steps. Git-only claims stay limited.
A reader should understand the day in about one minute per reporting group.
No fixed project labels or field list are required for new reports. Monthly
uses raw first and reads this prose only as prior editorial judgment.

For local/no-vault output, add `## YYYY.MM.DD · {scope}` and return in the
conversation. Label implicit local as unassigned, never work. Do not invent a
file path. An optional one-line cold-start hint may follow. For `all`, keep a
separate complete body per exact group, including a separate unassigned lane;
never rank or write a common judgment across groups.

## Protected Vault Update

Only the bundled merger writes Daily Note. It merges text; it does not generate
claims. Read the target bytes before drafting and obtain their SHA-256 (or
`missing` if absent). Save the bodies to a temporary UTF-8 JSON object mapping
exact reporting groups to Markdown. For `all`, include each actual group as a
key, never an `all` key. In combined output, start each body with a visible
`#### {group name}` heading. Do not include a date heading inside a body.

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
