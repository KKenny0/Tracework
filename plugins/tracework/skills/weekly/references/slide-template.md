# Weekly Audience-facing PPT Mode Markdown Template

Use only for explicit **slides** mode, after the slides contract.

The Markdown is the audience-facing semantic presentation. It must read like
candidate slide content, not an analysis form, Storyboard, or Production Brief.
A PPT maker may choose visual translation but may not research the vault,
invent semantics, or re-decide the argument.

Keep internal semantic groups, cognitive roles, source packets, and template
mapping out of the public document.

## Deck

```markdown
# {YYYY-WNN} Weekly Review

**汇报场景：** {primary audience · occasion; duration only when supplied}
**需要形成的理解或行动：** {one audience understanding, action, or decision}

---

## Slide 1｜{evidence-bounded conclusion the audience should retain}

{The minimum grounded facts, comparison, relationship, number, risk, or gate
that visibly proves the title. Use plain audience-facing wording.}

---

## Slide 2｜{next supported claim in the cumulative argument}

{Presentation content that answers the question raised by the prior page or
creates the need for the next decision.}

---

## Slide N｜{decision or action claim, when the communication job requires one;
otherwise the last supporting claim}

{The bounded implication, and the recorded next gate when one exists.}

---

## Slide N+1｜下周计划围绕{goal or remaining gate}收口

{Confirmed commitments and proposed items, each with recorded owner, date, and
closure criterion when they exist; items without a recorded criterion or date
stay explicitly uncriterioned or undated. Required for the default
same-department weekly-meeting deck; adapt only when explicit framing changes
the communication job.}
```

For a single selected goal, use the sequence above directly and do not add an
overview. For multiple independent selected goals, replace Slide 1 with a
grounded weekly goal map:

```markdown
## Slide 1｜{evidence-bounded weekly judgment across independent lanes}

| 工作主线 | 本周变化 | 当前边界 |
|---|---|---|
| {lane A} | {result or choice} | {state and gate} |
| {lane B} | {result or choice} | {state and gate} |
```

This is not an agenda; keep lane pages contiguous and group the next-week plan
by lane.

A neutral complete page showing the layer division:

```markdown
## Slide 4｜导出文件新增来源索引，两个真实样本完成一致性核对

每条导出记录带 source_refs（来源文档号＋段落序号），由最终绑定关系生成、
去重排序；无来源记录保留空列表。

- 两个真实样本共 22 条记录、57 条来源引用，回验与导出字节一致；
- 字段值为文件内原文，例如 {"doc": 12, "para": 3}。

使用方已确认两个样本可直接用于溯源（确认来自对接人转述，验收报告未读）；
字段命名语义仍需对方数据组人工确认。

> 备注：正文保留理解变化所需的结论、证据与限制；协议全量字段与逐样本数字
> 由讲者掌握（内部记录）。
```

The body keeps the claim, must-see evidence, and misleading-if-removed limits;
the note carries supplements; sources and reconciliation stay in internal
records. Illustrative only, not a required domain.

The example shows a claim sequence, not a required page count. A produced deck
contains only pages that survive Result Selection and deletion review. Unusual
length triggers compression review rather than a numeric failure. When no
candidate survives, return an evidence-insufficient empty state instead of an
empty deck.

## Content Rules

- Use one primary audience and one communication job.
- Do not confuse one communication job with one business goal. Preserve
  independent selected goal lanes when no source supports a common objective.
- When framing is absent, write for same-department colleagues who know the
  project background but not this week's implementation and validation; do not
  substitute a manager brief or invent a duration.
- Make the work goal visible before asking the audience to interpret actions,
  and keep this week's change more prominent than system background.
- For one selected goal, start directly with its result narrative. For multiple
  independent goals, use Slide 1 as a weekly goal map with each lane's result,
  status, and remaining boundary; each lane's Why sits in the map or its first
  page. Do not reduce it to names, activities, or an agenda.
- Write each slide title as a supported claim a presenter could naturally say
  aloud. Do not use a topic, question, process, object, or cognitive-role label.
- Make the body visibly prove the title. Keep limited, conflicting, or
  expected-only boundaries beside the claim they qualify.
- Keep each slide to one narrative job and one primary claim; prefer less copy
  and higher-value evidence over implementation detail.
- Put the facts, conflicts, relationships, numbers, risks, and recorded gates
  the audience must see to understand this period's change in the slide body.
  Include mechanism detail—branches, fallbacks, invariants—only as far as
  needed to follow the change, choice, or risk on that page. Show alternatives
  only when the audience must compare or choose them now; otherwise give the
  final choice and its shortest necessary rationale.
- Allow complementary text, diagrams, numbers, tests, and traces on one page
  when they perform one cognitive job; state what each proves—proximity must
  not imply causality.
- For technical explanation, state the concept in plain audience language
  before any diagram; keep current implementation, tested behavior, observed
  effect, and target design visibly distinct in ordinary slide copy.
- Use Mermaid, Markdown tables, quote blocks, number comparisons, concise prose,
  and short lists only when they are audience content—not production
  instructions.
- Choose a visual from the grounded relationship rather than a preset, using
  the contract's representation table; use text when it already carries the
  idea at lower reading cost. When one representation clearly fits, the page
  uses it directly and the maker keeps that form; only pages without a dominant
  shape leave it open.
- Keep a complex design-to-mechanism result in one composition; use two pages
  only when both claims have independent evidence and the mechanism depends on
  the premise established first.
- Keep a simple result on one page when one Before/After, relation, or flow
  explains root cause, choice, and operation.
- Move implementation inventory, complete work-stream accounting, and
  provenance to speaker notes or internal records unless they change the
  audience decision.
- Keep one responsibility per layer: body = conclusion, necessary evidence,
  and misleading-if-removed limits; speaker notes = presenter supplements and
  source hints; sources and reconciliation stay internal; the deck carries no
  Evidence Appendix; not every fact must enter the body.
- For the default same-department weekly meeting, end with a next-week plan
  page that separates confirmed commitments from proposals. Use only recorded
  closure criteria, owners, and dates; missing ones stay explicitly marked, and
  undated items stay undated. Group a multi-goal plan by lane; no lane may
  first appear there.
- Keep source packets, unsupported-claim analysis, and claim-to-source mapping
  internal or in speaker notes; no provenance table in the deck.

## Forbidden Public Sections

Do not emit public `Story`, cognitive-role, or analysis-field scaffolding;
`Audience takeaway`, `Recommended visual form`, `Page composition`, `On-slide
copy`, `Production constraints`, or page-level `Source Grounding Packet`
sections; `intended_takeaway` or `supported_claim` field names; or layout,
typography, color, card, template-map, or drawing instructions.

## Template-native Production

An explicitly requested editable PPTX follows the contract's optional
template-native rules: keep the public Markdown unchanged, map internally to
real source slides, preserve native typography and structure, and write a
versioned copy.

## Preflight

1. Give only the Markdown to a fresh member of the target audience. They must
   state the work goal, thesis, confidence boundary, and requested action
   without additional project research.
2. Check every title against its body. Unsupported certainty, topic-only titles,
   or evidence that does not prove the title fail.
3. Remove each page in turn. If decision, understanding, and confidence
   remain unchanged, merge, move, or delete it.
4. Read the deck end to end: the cumulative argument advances without
   repetition that adds no understanding, action, or confidence; state words
   such as closed, accepted, or passed name
   their object, confirmer, and scope; worked examples are internally derivable
   from stated inputs, and illustrative-only examples are marked.
5. Remove each diagram in turn. If it only reformats prose, has an ungrounded
   node or edge, hides its boundary, or does not reduce understanding cost,
   delete it.
6. Give only the Markdown to a fresh maker: visual translation allowed; no
   research or semantic invention; fitting may shorten or remap copy without
   changing facts, evidence boundaries, or necessary limits; a needed split
   returns to content arrangement.
7. For a requested template-native PPTX, apply the contract's render/verify,
   versioning, and scoped-revision rules before acceptance.

After at most one bounded repair, do not emit a deck that still misses a
material goal lane, exposes implementation inventory or internal coverage
bookkeeping, or leaves the maker to invent core objects and relationships.
Return a non-slide `PPT Mode 未通过` result with the failure type, recoverable
facts and boundaries, and the options to provide grounding, confirm goal lanes,
choose a more capable model, or explicitly request Brief.
