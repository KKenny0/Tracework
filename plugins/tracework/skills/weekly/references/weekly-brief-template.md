# Weekly Management Brief Template

Use this template for **brief** mode (`/tracework:weekly`, `写周报`, default
weekly). Do not use it for **quick** mode. For **slides**, analyze with the
brief spine first, then project through `slide-template.md`.

Read `reporting-narrative-contract.md` first. Brief mode does not require
solution-logic diagrams, implementation narratives, or chart briefs. A selected
material result may use the optional Change Explanation Card below when its
visual changes judgment, action, or confidence; compact prose remains default.

When coverage is thin or git-only, keep the main sections short, mark affected
arcs `limited`, and avoid padding with architecture detail that the evidence
does not support.

The body is the minimum information needed to reconstruct the management
judgment. Before keeping a body block, ask whether removing it would change the
reader's judgment, action, or confidence. Move accountability, coverage, and
provenance to the appendix. Do not use a fixed length or item count.

For no-vault or local first-run conversation output, prefer the compact shape
in `SKILL.md` (目标与判断 / 目标推进 / 偏差与决策 / 下周承诺 /
证据边界). Label scope `local` when the current repo is unassigned under
implicit scope; never present that lane as `work`.

```markdown
# YYYY-WNN 工作汇报

**日期：** YYYY-MM-DD ~ YYYY-MM-DD
**范围：** work | personal | all

## 本周目标与判断

{State the confirmed goal, inferred direction with its boundary, or
`目标未记录`. Then give one repeatable judgment covering actual change,
material variance, current decision, and largest remaining gate.}

## 关键推进

### {conclusion-led management change}

- **实际变化：** {observable change}
- **管理意义：** {why it changes the goal state or management judgment}
- **剩余门槛：** {what is not closed}

Show an evidence boundary here only when the claim is `limited`, conflicting,
or expected-only. Verified provenance stays in the appendix. Repeat only when
another independent change survives the counterfactual deletion test. Multiple
activities that prove one conclusion stay together.

When admitted by **Change Explanation Card Projection** in
`weekly-analysis-contract.md`, replace that result's three-line block with:

```markdown
### {conclusion-led state change}

{one primary visual: Markdown Before/After table, diff fence, Mermaid
Before/After subgraphs, aligned text trace, or no visual}

**问题：** {evidenced constraint or root cause}

**方案：** {intervention actually chosen and performed}

**形成的变化：** {current observable state and management meaning}

**证据与边界：** {verified | recorded | limited} · {remaining gate}
```

Before and After compare the same object and axis; After is actual at the
weekly cutoff. Put proposed designs outside After and label them
`target / not implemented`. Use at most one primary visual. If the card fails
the deletion test, the problem lacks evidence, or plain text is clearer, use
the compact result above. Do not turn portfolio rows into cards.

## 偏差与决策

- **{blocked | replanned | unplanned | decision | support}:** {only the
  information whose removal would change judgment, action, or confidence}

When none exists, write `本周没有需要升级的重要偏差、决策或协作事项。`

## 下周承诺

- **{commitment}:** {specific pass/fail closure criterion} ·
  {confirmed | proposed}

Do not force a count or list every task. A report proposal must remain
`proposed` until the user or another explicit source confirms it.

---

## 附录

### 目标与上期事项账本

| 事项 | 来源与性质 | 本周状态 | 收口条件或原因 |
|------|------------|----------|----------------|
| {goal or prior item} | {source} · {confirmed | inferred | unknown} · {confirmed | proposed} | {met | advanced | blocked | replanned | not_started} | {criterion or reason} |

Include every goal and every prior-period item. Omit prior rows only when no
previous Weekly item exists.

### 工作组合

| 工作主线 | 状态 | 本周形成的变化 | 与目标关系 | 需要关注 |
|----------|------|----------------|------------|----------|
| {stream} | {status} | {bounded change} | {goal / unplanned / portfolio} | {gate or none} |

Every meaningful stream must appear in the body or this ledger.

### 主张—证据与覆盖边界

| 正文主张 | 紧凑证据 | 证据边界与缺口 |
|----------|----------|----------------|
| {body claim} | {source type + stable reference} | {verified | recorded | limited; remaining gap} |

- **Scope：** {partition and excluded lanes}
- **Coverage：** {raw coverage and bounded git fallback}
```

For `all`, write two complete group sections, such as `公司工作` and
`个人项目`. Each group gets its own body and appendix so work output can be
extracted without personal references.

## Brief Quality Gate


- Every group has exactly one weekly judgment.
- Every goal states its source, confidence, status, and closure criterion.
- Inferred or unknown goals never use confirmed-goal language.
- Every prior commitment is accounted for; proposals remain proposals.
- Every material change is goal-linked, explicitly unplanned, or in the
  portfolio.
- Replanned work preserves the prior direction, evidence trigger, reason, and
  new direction.
- Every meaningful remaining stream appears in the portfolio.
- Every unresolved risk or next commitment has a concrete closure criterion.
- The body alone reconstructs goal state, actual change, material variance,
  decision or support, next commitment, and confidence boundary.
- Every body block survives counterfactual deletion; full prior-item,
  portfolio, and evidence coverage stays in the appendix.
- The body contains no tables except each admitted Change Explanation Card's
  single Before/After comparison; it contains no source paths, commit lists, or
  evidence index.
- Appendix ledgers and mappings do not repeat body narrative.
- Brief mode does not require diagrams, implementation narratives, or charts.
  It may use one lightweight visual inside an admitted Change Explanation Card;
  simple results remain text-only.
