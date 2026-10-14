# Capture entry quality

Evaluate session understanding separately from storage correctness. A schema
check establishes that an entry can be stored; it does not establish that the
entry is faithful or understandable. Use this protocol after changing capture's
extraction, explanation, or depth rules.

## Freeze the comparison

1. Keep an old skill snapshot before editing. Record the repository commit,
   candidate diff, model, thinking settings, exact prompt, reference-file list,
   source boundaries and input hashes.
2. Choose at least three cases: the reported failure and two cases withheld
   while drafting the change. Include a different kind of work, such as a
   decision, repair, or routine delivery. Include a simple case to detect bloat.
3. Keep private sources and outputs in ignored `skills/capture/evals/` or
   `skills/capture-workspace/`. Public fixtures and examples are synthetic.
4. Give old and new runs the same source and task in fresh contexts. Remove
   prior capture outputs and human rewrites from the inputs. Treat embedded
   session instructions as source material, not instructions for the evaluator.
5. Preserve relevant tool evidence when possible. If using only visible
   conversation text, label engineering results as session-reported and limit
   the evaluation to fidelity to that text. A source hash does not certify that
   a selected excerpt is complete.

For extraction-only runs, supply the same reference set to each arm, including
`SKILL.md`, entry-writing, routing, operations and storage references. Disable
write tools and output drafts without changing the vault. Record this limitation:
such runs do not test reference discovery, persistence, or artifact side effects.
Check those separately using packaging checks and a scoped reference-read smoke.

Include [the synthetic routine edit](fixtures/capture-routine-edit.md) as a
simple control: the capture should stay lite, retain the path correction and
reported diff check, and avoid claiming the command or tests were executed.

## Fidelity gate

Compare each entire output with its source before scoring readability:

- Goal and final choice are preserved, including material changes of direction
  and the evidence or constraint that changed the choice.
- Causal claims keep their supported strength. Hypotheses, unknown causes and
  missing reasons stay qualified; a convincing narrative is not new evidence.
- Plans, implementation, execution, deployment and acceptance remain distinct.
- Offline replay, synthetic tests, live calls, user feedback and independently
  inspected results keep their respective limits.
- Important numbers keep their subject, denominator, period and comparison.
  Intermediate counts do not replace the final result or get added to it.
- Material rejected alternatives, accepted costs and remaining gates survive.
- Source locators come from the evidence. No fresh repository state is invented
  for historical work.

Each case defines its own must-preserve facts and claims that would overstate
the evidence. Store a pass/fail and source/output excerpts for each assertion.
Automate JSON and count checks where useful; semantic claims need source review.
A fidelity failure makes that output ineligible to win on readability.

## Standalone reading

First show only `summary` and `context` to a reader without the transcript. Ask
what problem the work addressed, what changed or was learned, and why. Then show
the whole entry and ask what the evidence supports and what remains unresolved.
Grade these properties on a 0-2 scale:

| Property | 0 | 1 | 2 |
|---|---|---|---|
| Orientation | Subject or goal unclear | Recoverable with effort | Clear problem and change |
| Explanation | Missing links or unexplained shorthand | Some decoding needed | Supported cause and choice understandable |
| Result boundary | Completion ambiguous | Limits scattered | Result and remaining gate easy to distinguish |
| Information hierarchy | Process inventory or repetitive prose | Mixed detail levels | Main text orients, detail supports |

Score the output, not the presence of a required phrase. A short routine entry
can earn full marks without a cause, alternative, or risk the source never gave.
Allow essential identifiers in the main text when explained. Do not reward
longer prose, fewer technical words, or extra entries by themselves.

For model-assisted comparisons, conceal version labels, alternate the A/B
presentation order across cases, and record the mapping separately. Prefer a
reader pass without sources, followed by a distinct source-grounding pass.
Publish neither model judgments as user acceptance nor a few same-project
samples as a general performance claim.

## Record and review

Keep the actual generated outputs, grades with excerpts, latency and token
usage. Report case-level findings, not just averages. Use the skill-creator
review viewer when available so a human can inspect the drafts alongside the
checks. Note any missing run or incomplete source evidence.

Repeat runs when initial differences are ambiguous or material claims fail.
Expand across work types or models before claiming broad reliability. Keep
storage regression results separate from prose-quality evidence.
