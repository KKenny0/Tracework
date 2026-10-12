import assert from 'node:assert/strict';
import test from 'node:test';
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
