import assert from 'node:assert/strict';
import test from 'node:test';
import fs from 'node:fs';
import { validateWeeklyPptReadyMarkdownContract } from './report-contract.mjs';
import { checkReportOutput } from './report-output-checks.mjs';

const codes = (text, context) => checkReportOutput(text, context).map(issue => issue.code);

test('rejects an empty report and JSON returned instead of Markdown', () => {
  assert.deepEqual(codes(' \n'), ['empty_report']);
  for (const text of ['{"今日判断":"尚未实现"}', '```json\n{"今日判断":"尚未实现"}\n```', '[{"status":"recorded"}]']) {
    assert.deepEqual(codes(text), ['json_instead_of_markdown']);
  }
});

test('accepts Markdown containing a JSON evidence example', () => {
  assert.deepEqual(codes('# 本月判断\n\n尚未验证。\n```json\n{"status":"recorded"}\n```'), []);
});

test('compares a printed day count with independently supplied evidence coverage', () => {
  assert.deepEqual(codes('- Raw-backed days: 6', { expectedRawDays: 7 }), ['raw_day_count_mismatch']);
  assert.deepEqual(codes('- Raw-backed days: 7', { expectedRawDays: 7 }), []);
  assert.deepEqual(codes('- 原始记录覆盖天数：0', { expectedRawDays: 0 }), []);
});

test('catches seven listed dates labeled as six without external context', () => {
  const report = '- **Raw-backed days:** 6（06-02, 06-10, 06-11, 06-18, 06-20, 06-28, 06-30）';
  const [issue] = checkReportOutput('# 报告\n' + report);
  assert.equal(issue.code, 'enumerated_day_count_mismatch');
  assert.equal(issue.line, 2);
  assert.equal(issue.expected, 7);
  assert.equal(issue.evidence, report);
});

test('counts distinct dates, not entries on the same date', () => {
  assert.deepEqual(codes('- Raw-backed days: 2（2026-06-02、2026-06-02、2026-06-10）'), []);
  assert.deepEqual(codes('- Raw-backed days: 0'), []);
});

test('does not treat ranges, examples, or mixed date formats as exhaustive lists', () => {
  for (const text of [
    '- Raw-backed days: 7（06-02 至 06-30）',
    '- Raw-backed days: 7（例如 06-02, 06-10）',
    '- Raw-backed days: 1（2026-06-02, 06-02）',
  ]) assert.deepEqual(codes(text), []);
});

test('does not claim to detect semantic mistakes by keyword matching', () => {
  assert.deepEqual(codes('线上延迟未验证，不能断言未改变。'), []);
  assert.deepEqual(codes('线上延迟未改变。'), []);
});

test('rejects invalid evidence count inputs instead of silently passing', () => {
  for (const expectedRawDays of [-1, NaN, 1.5, '7']) {
    assert.throws(() => checkReportOutput('# 报告', { expectedRawDays }), TypeError);
  }
});

// Slides keep provenance in the benchmark's internal map, not a public appendix.

const pptFixture = () => {
  const fixture = JSON.parse(fs.readFileSync(new URL('./regression-fixtures.json', import.meta.url), 'utf8'))
    .fixtures.find(item => item.id === 'weekly-ppt-a-complex-story-content-split');
  return fixture;
};

test('accepts slides with an internal evidence map and no public appendix', () => {
  const fixture = pptFixture();
  fixture.fixture.candidate_output.internal_evidence[0].note = 'Internal supported_claim annotation';
  assert.doesNotThrow(() => validateWeeklyPptReadyMarkdownContract(fixture));
});

test('rejects a public evidence appendix even when internal provenance is valid', () => {
  for (const surface of ['field', 'title', 'content']) {
    const fixture = pptFixture();
    const output = fixture.fixture.candidate_output;
    if (surface === 'field') output.evidence_appendix = structuredClone(output.internal_evidence);
    else if (surface === 'title') output.slides[0].title = 'Evidence Appendix';
    else output.slides[0].content += '\n\n## 证据附录\nClaim | Source | Boundary';
    assert.throws(() => validateWeeklyPptReadyMarkdownContract(fixture), /public deck leaks/);
  }
});

test('still rejects missing or fabricated internal provenance', () => {
  const missing = pptFixture();
  delete missing.fixture.candidate_output.internal_evidence;
  assert.throws(() => validateWeeklyPptReadyMarkdownContract(missing), /internal evidence map is missing/);
  const forged = pptFixture();
  forged.fixture.candidate_output.internal_evidence[0].source = 'invented:source';
  assert.throws(() => validateWeeklyPptReadyMarkdownContract(forged), /unavailable source/);
});

test('keeps an unrecorded closure criterion missing instead of inventing one', () => {
  const fixture = JSON.parse(fs.readFileSync(new URL('./regression-fixtures.json', import.meta.url), 'utf8'))
    .fixtures.find(item => item.id === 'weekly-ppt-default-team-sync-goal-grounded');
  const source = fixture.fixture.source_next_commitments[0];
  const output = fixture.fixture.candidate_output;
  output.slides.at(-1).content = output.slides.at(-1).content
    .replace(`通过标准是 ${source.closure_criterion}`, '通过标准未记录');
  delete source.closure_criterion;
  delete output.next_plan_items[0].closure_criterion;
  assert.doesNotThrow(() => validateWeeklyPptReadyMarkdownContract(fixture));
  output.next_plan_items[0].closure_criterion = 'Invented acceptance gate';
  assert.throws(() => validateWeeklyPptReadyMarkdownContract(fixture), /changed its closure criterion/);
});
