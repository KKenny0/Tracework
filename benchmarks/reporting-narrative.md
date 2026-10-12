# Reporting Narrative Benchmark

Daily, Weekly, and Monthly are agent-authored, so evaluation has two layers.

## Executable Contract

`report-contract` fixtures verify:

- scope partition happens before selection;
- work output contains no configured personal terms;
- each group has its own judgment and headline budget;
- every meaningful stream appears in a headline or portfolio;
- next-period closure targets remain bounded.

These checks protect structure and audience safety. They do not claim to grade
prose quality.

## Real-Output Evaluation

For a dense real week, generate `work`, `personal`, and `all` views without
overwriting the source report. Review:

- Can the reader repeat the period judgment?
- Does each headline show starting situation, movement, end state, meaning, and
  remaining gate?
- Did personal work stay out of work output, including evidence refs?
- Did every meaningful non-headline stream remain in portfolio coverage?
- Can Daily be read in about one minute and Weekly presented in about five?
- Can every material claim drill into raw or direct evidence?

Record model, repo SHA, scope, output path, pass/fail, and short failure excerpts.
Keep private raw data and generated comparisons in ignored local eval folders or
temporary storage; do not commit them.

Before assigning an overall preference, follow
[Report Grounding Review](report-grounding-review.md): calibrate with incorrect
statements and correct controls, inspect complete outputs, and keep grounding
separate from readability. A model's assertion pass rate is not factual accuracy.
Use `node benchmarks/report-output-checks.mjs REPORT.md [EXPECTED_RAW_DAYS]` for
mechanical format/count checks; supply coverage from the evidence, not the report.
Omitting the expected count checks only internal enumerations. Neither mode
checks semantic truth. `npm --prefix cli run test:report-output` tests this checker
and is included in the full test suite.

## Instrumented Model Calls

Use `report-runner.mjs` for Claude CLI writing-stage comparisons. It takes an
explicit executable path and available model name; it does not hard-code a
route, change authentication, or install anything. Keep the same model, effort,
instructions and evidence within each comparison. A route change starts a new
comparison rather than extending the old scores.

```js
import { runReportEvaluation } from './benchmarks/report-runner.mjs';

await runReportEvaluation({
  cli: '/path/to/claude',
  model: '<available-model>',
  effort: 'medium',
  prompt, systemPrompt,
  outputDir: '<new-attempt-directory>',
  cwd: '<evaluation-workspace>',
  timeoutMs: 120_000,
  expectedRawDays: 4, // Count independently from the supplied evidence.
});
```

Each attempt directory is immutable: reuse is rejected. The runner drains and
saves stdout/stderr during execution, keeps partial text and timestamped stream
events, and preserves the final CLI envelope separately from report text. It
never extracts embedded Markdown from a JSON report to turn a format failure
into a pass. A later repair or retry belongs in a different directory.

`outcome.json` distinguishes `launch_error`, `timeout`, `api_error`,
`process_error`, `protocol_error`, `format_error`, `coverage_error`, and
`complete`. Timeouts retain whether events, thinking deltas, text, or a final
result had arrived; thinking-event times and counts do not enter the report body.
`before_content` alone does not distinguish server waiting from unstreamed model
thinking. Even a final result followed by a stuck client remains a timeout. API errors
require explicit CLI error evidence, not a guess based on missing output.
`complete` means transport and mechanical checks passed; `semantic_status`
remains `not_checked` until independent source review.

`npm --prefix cli run test:report-runner` uses local subprocess fixtures (no
model calls) to check partial-output retention, large streams, API error
classification, malformed output, UTF-8 boundaries, and report format/count
failures. It is included in the full test suite.

## Bounded Review and Repair

`report-review-cycle.mjs` composes generation, whole-report review, at most one
separate repair, and a fresh whole-report review. It is an evaluation tool, not
an installed-skill runtime or a semantic certification service.

```js
import { claudeReviewInvoker, runReviewedReport } from './benchmarks/report-review-cycle.mjs';

const invoke = claudeReviewInvoker({
  cli: '/path/to/claude', model: '<available-model>',
  effort: 'medium', timeoutMs: 240_000,
});
await runReviewedReport({
  prompt: '<writing instructions and the frozen template>',
  // Supply only already selected, scoped, effective evidence.
  sources: [
    { id: 'scope', date: null, text: 'Work scope; selected project: release.' },
    { id: 'R1', date: '2026-11-18', text: 'Deployed; production latency is unmeasured.' },
  ],
  requirements: ['Retain deployment and the unmeasured production effect.'],
  invoke, outputDir: '<new-cycle-directory>',
});
```

Dated records determine `raw_entry_count` and distinct `raw_days`; null-date
context is excluded. Invalid source configuration is rejected before creating a
cycle or invoking a model. Empty-day coverage remains unknown. These values reach the
writer before generation. The mechanical checker also accepts this `coverage`
object to check labeled entry counts and prevent an unknown empty-day count from
becoming numeric zero. It recognizes explicit count labels, not all equivalent
prose. Omitted or paraphrased statistics still need source review.

Reviewers return a judgment for every nonempty paragraph/block and every required
material fact. An empty `requirements` list checks existing claims without
asserting omission coverage. Reviewers choose source and report-block IDs; code binds those IDs to
exact original text. This avoids asking a model to copy long quotations, but does
not prove that its chosen source actually supports a claim. Unknown IDs, missing
blocks, duplicate rows, malformed JSON and incomplete requirements fail review
validation. Requirements should describe facts that must appear, not demand a
quotation to prove the absence of forbidden wording. Review JSON can have one
complete `json` fence; surrounding prose is not stripped. This framing allowance
does not apply to report output, where JSON wrapping still fails.

Initial and repaired reports, input hashes, mechanical checks, raw model responses
and reviews remain separate. The repair sees the full review, including later
sections. Its result is reviewed from scratch. A failed/malformed review stops the
cycle; a rejected or uncertain repair does not trigger another repair. Budget the
review phase explicitly: long whole-report checks may exceed a writing timeout.

`review_pass_unconfirmed` and `first_attempt_review_pass` describe automated review
only. `eligible` stays false and `independent_source_review_required` stays true,
even after a successful repair. Calibrate using retained negative reports and
accepted controls, then independently adjudicate full outputs before acceptance.
Reader approval of style cannot override this boundary. This module neither
promotes a template nor writes into the vault.

Run `npm --prefix cli run test:report-review-cycle` for behavior tests of coverage,
reference binding, incomplete reviews, error handling, one-repair limits and
preservation of originals. The full suite includes this target.

## End-to-End Admission

Run `npm --prefix cli test` and `npm --prefix cli run check-skills` first.
Report these independent boundaries instead of treating an aggregate green as
proof of usable prose:

| Layer | Pass condition |
|---|---|
| Preservation | Concurrent writes retain every entry; failed replacement retains original JSON; historical work reaches its correct period. |
| Independent consumption | Raw-only Monthly succeeds without Daily/Weekly or a derived index; absent evidence produces an honest empty state. |
| Claim support | No invented confirmed goals, expected effects as observed, vanished material risk, or silently confirmed proposals. |
| Reader value | A reader can repeat the change, remaining gate, and needed decision; material claims have source mappings. |
| Cost | Compare the same mode and evidence before/after, including every required instruction file, source reread, elapsed time, and manual correction count when actually measured. |

For semantic checks, use a small private set covering sparse evidence, late
cross-month capture, a replan, independent goals, and mixed groups. Name the
input period and scope exactly; a bounded sample is not full-week acceptance.
Assign expected material claims and unresolved gates from sources before writing
the candidate. Record exact failing sentences and revisions. Agent self-review
and actual reader acceptance are separate results; do not manufacture the latter.
Keep real inputs and outputs outside tracked public fixtures.
