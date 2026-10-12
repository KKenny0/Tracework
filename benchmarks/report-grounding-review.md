# Report Grounding Review

Use this review separately from readability preference. Inputs are the complete
report, its scoped source facts and a source-derived list of required material
changes, unresolved gates and conflicts. Fix those expectations before generation.
Do not reveal which template or rule version produced the report.

## Calibrate Before Comparing

Test the reviewer on known incorrect statements and matched correct controls.
Include unsupported completion, missing comparison baselines, unknown versus
negative effects, and proposed versus confirmed actions or deadlines. A correct
quotation that explicitly rejects an unsupported claim must remain acceptable.
Require a source-based explanation, not keyword matches. Record missed errors
and false positives separately; a failed calibration disqualifies the automated
reviewer's pass verdicts until independently checked.

Then recheck complete prior reports containing the known failures. Passing short
controls alone does not demonstrate that a reviewer catches contradictions buried
in a long report. If this check fails, independently adjudicate every output used
for acceptance; spot checks or a high assertion score cannot rehabilitate the
reviewer's other passes. Preserve original outputs and original judgments alongside
any adjudication; do not replace a failed run with an edited success.

## Read Every Claim in Context

Review headings, body, tables, footnotes and appendices. For each distinct claim,
identify the actor/object, action or state, date, scope and degree of certainty.
Map it to actual source facts. One correct disclaimer elsewhere does not cancel
an unsupported headline or later sentence. Evidence IDs and `verified` labels do
not independently prove a claim. Quoted historical errors that are visibly
rejected are not claims the current report endorses.

Check these relationships explicitly:

- **Unknown effects:** no measurement supports "not yet verified," not "unchanged,"
  "no improvement" or "no loss." Positive and negative effects both need evidence.
- **Comparisons:** a post-change number alone proves neither a gain nor a loss.
  Require comparable before/after samples and methods for a directional claim,
  including offline effects and claims without a percentage.
- **Lifecycle:** implemented, merged, deployed, tested and accepted are different
  states. Verify the state actually claimed, even if nearby prose is cautious.
- **Commitments:** preserve proposed versus confirmed and keep action separate
  from deadline. An agreed next step is not an agreed next-week completion date.
- **Scope and causes:** preserve test/production, client population, permission
  conditions and sample limits. Do not invent root-cause confirmation, losses,
  avoided incidents, exclusivity ("only criterion"), or prior preference.
- **Coverage:** preserve every required material stream, unresolved gate and
  source conflict. Compression may remove repetition, not meaningful evidence.

For each finding, return an exact report quotation with its location, the relevant
source reference, and the unsupported inference or contradiction. Validate that
the quotation actually exists. State disputed or ambiguous cases as `uncertain`;
do not silently convert them into passes. Also return supported-claim examples
and missing required facts so review is not just a hunt for negative keywords.

## Decision Gate

Keep these independent results:

1. Mechanical checks: Markdown output and any supported count checks, using
   `report-output-checks.mjs`. A clean result means only these checks passed.
2. Grounding: `pass`, `fail`, or `uncertain`, with exact findings and omissions.
3. Readability: concrete wording, flow, unnecessary repetition, and actual reader
   preference. A shorter report is not automatically clearer.

Any confirmed material unsupported claim, contradiction or omission fails
Grounding. Uncertain or unreviewed output cannot receive an overall pass. Compare
readability for either version if useful, but an output failing Grounding cannot
be declared the overall winner; when neither passes, report "neither accepted."
A calibrated model judgment still requires spot checks and is not human acceptance.

Keep raw judge responses, calibration outcomes, adjudications and any parse errors.
Judge failures remain unresolved; never default missing or malformed verdicts to
pass. Report the same-model and small-sample limitations. Use held-out evidence
for the next iteration, not only examples that shaped the new instructions.
